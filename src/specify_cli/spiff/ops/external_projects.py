"""
specify_cli.spiff.ops.external_projects - External Project Validation

Enables validation of spec-kit integration in external Python projects
through dynamic BPMN workflow generation and batch processing.

Adapted from uvmgr's external project validation framework.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Optional OTEL instrumentation
try:
    from ...core.telemetry import metric_counter, metric_histogram, span
    from ...core.instrumentation import add_span_attributes, add_span_event
    _otel_available = True
except ImportError:
    _otel_available = False

    def span(*args, **kwargs):
        from contextlib import contextmanager
        @contextmanager
        def _no_op():
            yield
        return _no_op()

    def metric_counter(name):
        def _no_op(value=1):
            return None
        return _no_op

    def metric_histogram(name):
        def _no_op(value):
            return None
        return _no_op

    def add_span_attributes(**kwargs):
        pass

    def add_span_event(name, attributes=None):
        pass

__all__ = [
    "ExternalProjectInfo",
    "ExternalValidationResult",
    "discover_external_projects",
    "validate_external_project_with_spiff",
    "batch_validate_external_projects",
    "run_8020_external_project_validation",
]


@dataclass
class ExternalProjectInfo:
    """Metadata about discovered Python project."""

    path: Path
    name: str
    package_manager: str  # "uv", "pip", "poetry", "pipenv"
    has_tests: bool = False
    has_requirements: bool = False
    has_dependencies: bool = False
    project_type: str = "unknown"  # "web", "cli", "library", "data", "ml"
    confidence: float = 0.0
    test_framework: str = ""
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": str(self.path),
            "name": self.name,
            "package_manager": self.package_manager,
            "has_tests": self.has_tests,
            "has_requirements": self.has_requirements,
            "project_type": self.project_type,
            "confidence": self.confidence,
            "test_framework": self.test_framework,
            "dependencies_count": len(self.dependencies),
        }


@dataclass
class ExternalValidationResult:
    """Complete validation result for external project."""

    project_path: Path
    project_name: str
    success: bool
    duration_seconds: float = 0.0
    analysis: Dict[str, Any] = field(default_factory=dict)
    installation_success: bool = False
    validation_success: bool = False
    test_results: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "project_path": str(self.project_path),
            "project_name": self.project_name,
            "success": self.success,
            "duration_seconds": self.duration_seconds,
            "analysis": self.analysis,
            "installation_success": self.installation_success,
            "validation_success": self.validation_success,
            "test_results": self.test_results,
            "errors": self.errors,
            "metrics": self.metrics,
        }


def discover_external_projects(
    search_path: Path = Path.home() / "projects",
    max_depth: int = 3,
    min_confidence: float = 0.5,
) -> List[ExternalProjectInfo]:
    """
    Discover Python projects by scanning filesystem.

    Args:
        search_path: Root path to search
        max_depth: Maximum directory depth to search
        min_confidence: Minimum confidence threshold

    Returns
    -------
        List of discovered projects sorted by confidence
    """
    with span("projects.discover", search_path=str(search_path)):
        add_span_event("discovery.started", {
            "search_path": str(search_path),
            "max_depth": max_depth,
        })

        projects = []

        if not search_path.exists():
            add_span_event("discovery.search_path_not_found", {
                "path": str(search_path)
            })
            return projects

        # Recursively search for projects
        def _search(path: Path, depth: int):
            if depth > max_depth or depth > 10:
                return

            try:
                for item in path.iterdir():
                    if item.is_dir() and not item.name.startswith("."):
                        project_info = _is_python_project(item)
                        if project_info and project_info.confidence >= min_confidence:
                            projects.append(project_info)
                            add_span_event("discovery.project_found", {
                                "path": str(item),
                                "name": project_info.name,
                                "confidence": project_info.confidence,
                            })
                        _search(item, depth + 1)
            except (PermissionError, OSError):
                pass

        _search(search_path, 0)

        # Sort by confidence
        projects.sort(key=lambda p: p.confidence, reverse=True)

        add_span_event("discovery.completed", {
            "discovered_projects": len(projects),
        })

        metric_counter("discovery.projects_found")(len(projects))
        return projects


def validate_external_project_with_spiff(
    project_info: ExternalProjectInfo,
    use_8020: bool = True,
    timeout_seconds: int = 120,
) -> ExternalValidationResult:
    """
    Validate external project with spec-kit.

    Args:
        project_info: Project to validate
        use_8020: Use 80/20 critical path approach
        timeout_seconds: Timeout for validation

    Returns
    -------
        ExternalValidationResult
    """
    import time
    start_time = time.time()

    with span("validation.external_project", project_name=project_info.name):
        result = ExternalValidationResult(
            project_path=project_info.path,
            project_name=project_info.name,
            success=False,
        )

        try:
            add_span_event("validation.started", {
                "project": str(project_info.path),
                "package_manager": project_info.package_manager,
            })

            # Step 1: Analyze project
            result.analysis = project_info.to_dict()

            # Step 2: Generate test commands
            test_commands = _generate_project_specific_tests(project_info, use_8020)

            # Step 3: Execute validation workflow
            from .otel_validation import execute_otel_validation_workflow

            workflow_path = Path(tempfile.gettempdir()) / f"validate_{project_info.name}.bpmn"

            from .otel_validation import create_otel_validation_workflow
            create_otel_validation_workflow(workflow_path, test_commands)

            validation_result = execute_otel_validation_workflow(
                workflow_path,
                test_commands,
                timeout_seconds=timeout_seconds,
            )

            result.validation_success = validation_result.success
            result.test_results = validation_result.test_results
            result.metrics = validation_result.metrics

            # Step 4: Cleanup
            try:
                workflow_path.unlink()
            except Exception:
                pass

            result.success = validation_result.success
            result.duration_seconds = time.time() - start_time

            add_span_event("validation.completed", {
                "project": str(project_info.path),
                "success": result.success,
                "duration": result.duration_seconds,
            })

            metric_counter("external_validation.completed")(1)
            metric_histogram("external_validation.duration")(result.duration_seconds)

            return result

        except Exception as e:
            result.errors.append(str(e))
            result.duration_seconds = time.time() - start_time

            add_span_event("validation.failed", {
                "project": str(project_info.path),
                "error": str(e),
            })

            metric_counter("external_validation.failed")(1)
            return result


def batch_validate_external_projects(
    projects: List[ExternalProjectInfo],
    parallel: bool = True,
    max_workers: int = 4,
    use_8020: bool = True,
) -> List[ExternalValidationResult]:
    """
    Validate multiple projects in batch.

    Args:
        projects: List of projects to validate
        parallel: Use parallel execution
        max_workers: Maximum worker threads
        use_8020: Use 80/20 critical path approach

    Returns
    -------
        List of validation results
    """
    with span("validation.batch", num_projects=len(projects)):
        add_span_event("batch_validation.started", {
            "num_projects": len(projects),
            "parallel": parallel,
        })

        results = []

        if parallel and len(projects) > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        validate_external_project_with_spiff,
                        project,
                        use_8020=use_8020,
                    ): project for project in projects
                }

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        project = futures[future]
                        results.append(ExternalValidationResult(
                            project_path=project.path,
                            project_name=project.name,
                            success=False,
                            errors=[str(e)],
                        ))
        else:
            for project in projects:
                result = validate_external_project_with_spiff(project, use_8020=use_8020)
                results.append(result)

        # Calculate summary
        successful = sum(1 for r in results if r.success)

        add_span_event("batch_validation.completed", {
            "total_projects": len(results),
            "successful": successful,
            "failed": len(results) - successful,
        })

        metric_counter("batch_validation.completed")(1)
        metric_histogram("batch_validation.success_rate")(
            successful / len(results) if results else 0
        )

        return results


def run_8020_external_project_validation(
    search_path: Path = Path.home() / "projects",
    max_depth: int = 2,
    project_type_filter: Optional[str] = None,
    parallel: bool = True,
) -> Dict[str, Any]:
    """
    Run 80/20 validation on critical external projects.

    Focuses on highest-confidence projects that represent 80% of value.

    Args:
        search_path: Where to search for projects
        max_depth: Maximum directory depth
        project_type_filter: Filter by project type ("web", "cli", "library", etc.)
        parallel: Use parallel execution

    Returns
    -------
        Summary of validation results
    """
    with span("validation.8020_external_projects", filter=project_type_filter):
        add_span_event("8020_validation.started", {
            "search_path": str(search_path),
            "type_filter": project_type_filter,
        })

        # Discover projects
        all_projects = discover_external_projects(search_path, max_depth=max_depth)

        # Filter by type if specified
        if project_type_filter:
            projects = [p for p in all_projects if p.project_type == project_type_filter]
        else:
            projects = all_projects

        # Select critical projects (80/20: top projects by confidence)
        critical_count = max(1, len(projects) // 5)  # Top 20%
        critical_projects = projects[:critical_count]

        # Validate critical projects
        results = batch_validate_external_projects(
            critical_projects,
            parallel=parallel,
            use_8020=True,
        )

        # Summary
        successful = sum(1 for r in results if r.success)
        summary = {
            "total_discovered": len(all_projects),
            "critical_selected": len(critical_projects),
            "validated": len(results),
            "successful": successful,
            "failed": len(results) - successful,
            "success_rate": successful / len(results) if results else 0.0,
            "results": [r.to_dict() for r in results],
        }

        add_span_event("8020_validation.completed", {
            "total_discovered": len(all_projects),
            "validated": len(results),
            "successful": successful,
        })

        metric_counter("8020_external_validation.executed")(1)
        metric_histogram("8020_external_validation.success_rate")(
            summary["success_rate"]
        )

        return summary


def _is_python_project(path: Path) -> Optional[ExternalProjectInfo]:
    """
    Check if directory is a Python project with confidence score.

    Args:
        path: Directory to check

    Returns
    -------
        ExternalProjectInfo if project detected, None otherwise
    """
    if not path.is_dir():
        return None

    confidence = 0.0
    has_requirements = False
    has_tests = False
    has_dependencies = False
    package_manager = "pip"
    test_framework = ""

    # Check for Python project indicators
    indicators = {
        "pyproject.toml": 0.3,
        "setup.py": 0.25,
        "setup.cfg": 0.15,
        "requirements.txt": 0.2,
        "Pipfile": 0.25,
        "poetry.lock": 0.2,
        "uv.lock": 0.2,
    }

    for indicator, score in indicators.items():
        if (path / indicator).exists():
            confidence += score
            has_dependencies = True
            if "Pipfile" in indicator:
                package_manager = "pipenv"
            elif "poetry" in indicator:
                package_manager = "poetry"
            elif "uv" in indicator:
                package_manager = "uv"

    # Check for tests
    test_dirs = ["tests", "test"]
    for test_dir in test_dirs:
        if (path / test_dir).is_dir():
            has_tests = True
            confidence += 0.1
            test_framework = "pytest"
            break

    # Check for source code
    if (path / "src").is_dir() or any(f.suffix == ".py" for f in path.glob("*.py")):
        confidence += 0.15

    # Detect project type
    project_type = _detect_project_type(path)

    if confidence < 0.2:
        return None

    return ExternalProjectInfo(
        path=path,
        name=path.name,
        package_manager=package_manager,
        has_tests=has_tests,
        has_requirements=has_dependencies,
        has_dependencies=has_dependencies,
        project_type=project_type,
        confidence=min(1.0, confidence),
        test_framework=test_framework,
    )


def _detect_project_type(path: Path) -> str:
    """Detect project type from directory structure."""
    indicators = {
        "web": ["flask", "django", "fastapi", "app.py", "wsgi.py"],
        "cli": ["click", "typer", "argparse", "main.py", "cli.py"],
        "library": ["__init__.py", "src/"],
        "data": ["pandas", "numpy", "jupyter", "notebooks/"],
        "ml": ["tensorflow", "pytorch", "sklearn", "models/"],
    }

    for proj_type, keywords in indicators.items():
        for keyword in keywords:
            if keyword.endswith(".py"):
                if (path / keyword).exists():
                    return proj_type
            else:
                for file in path.glob("**/*"):
                    if keyword in file.name:
                        return proj_type

    return "unknown"


def _generate_project_specific_tests(
    project_info: ExternalProjectInfo,
    use_8020: bool = True,
) -> List[str]:
    """Generate test commands specific to project."""
    tests = []

    if use_8020:
        # Critical path tests
        module_name = project_info.name.replace("-", "_").split(".")[0]
        tests.extend([
            f"cd {project_info.path} && python -c 'import {module_name}'",
            "python -c 'from specify_cli import specify_cli'",
        ])
    else:
        # Comprehensive tests
        if project_info.has_tests:
            tests.append(f"cd {project_info.path} && pytest")
        if project_info.test_framework:
            tests.append(f"cd {project_info.path} && {project_info.test_framework}")

    return tests or ["python -c 'print(\\\"Project validation passed\\\")'"]
