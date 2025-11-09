"""
Project scanner for reverse engineering analysis.

Detects tech stack, calculates code metrics, and discovers project structure.
"""

import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

# Handle both relative and absolute imports
try:
    from .config import DEFAULT_CONFIG
    from .security import validate_project_path, SecurityError
except ImportError:
    from config import DEFAULT_CONFIG
    from security import validate_project_path, SecurityError

logger = logging.getLogger(__name__)


@dataclass
class TechStack:
    """Container for detected technology stack."""

    primary_language: str
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    build_tools: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    runtime_version: Optional[str] = None
    package_manager: Optional[str] = None


@dataclass
class CodeMetrics:
    """Container for code metrics."""

    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    file_count: int = 0
    directory_count: int = 0
    languages_breakdown: Dict[str, int] = field(default_factory=dict)


@dataclass
class ProjectStructure:
    """Container for project structure information."""

    root_path: Path
    source_dirs: List[str] = field(default_factory=list)
    test_dirs: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    doc_files: List[str] = field(default_factory=list)
    has_ci_cd: bool = False
    has_tests: bool = False
    has_documentation: bool = False


@dataclass
class ScanResult:
    """Container for complete scan results."""

    tech_stack: TechStack
    metrics: CodeMetrics
    structure: ProjectStructure
    scan_successful: bool = True
    error_message: Optional[str] = None


class ProjectScanner:
    """
    Scan project to detect tech stack, calculate metrics, and analyze structure.
    """

    # File indicators for technology detection
    TECH_INDICATORS = {
        "javascript": ["package.json", "yarn.lock", "pnpm-lock.yaml"],
        "typescript": ["tsconfig.json", "package.json"],
        "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
        "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "csharp": ["*.csproj", "*.sln", "project.json"],
        "ruby": ["Gemfile", "Rakefile", ".ruby-version"],
        "php": ["composer.json", "composer.lock"],
        "go": ["go.mod", "go.sum"],
        "rust": ["Cargo.toml", "Cargo.lock"],
    }

    FRAMEWORK_INDICATORS = {
        "react": ["react"],
        "vue": ["vue"],
        "angular": ["@angular/core"],
        "django": ["django"],
        "flask": ["flask"],
        "fastapi": ["fastapi"],
        "spring-boot": ["org.springframework.boot"],
        "express": ["express"],
        "nestjs": ["@nestjs/core"],
        "rails": ["rails"],
        "laravel": ["laravel/framework"],
        "asp.net": ["Microsoft.AspNetCore"],
    }

    def __init__(self, project_path: Path):
        """
        Initialize project scanner.

        Args:
            project_path: Path to project root directory

        Raises:
            SecurityError: If path is unsafe
            FileNotFoundError: If path doesn't exist
        """
        # Validate path for security
        try:
            self.project_path = validate_project_path(Path(project_path))
            logger.info(f"Initialized scanner for: {self.project_path}")
        except (SecurityError, FileNotFoundError, PermissionError) as e:
            logger.error(f"Cannot initialize scanner: {e}")
            raise

    def scan_project(self) -> ScanResult:
        """
        Perform complete project scan.

        Returns:
            ScanResult with tech stack, metrics, and structure
        """
        logger.info("Starting project scan...")

        try:
            tech_stack = self._detect_tech_stack()
            logger.info(f"Detected tech stack: {tech_stack.primary_language}")

            metrics = self._calculate_metrics()
            logger.info(f"Calculated metrics: {metrics.code_lines} lines of code")

            structure = self._analyze_structure()
            logger.info("Project structure analysis complete")

            return ScanResult(
                tech_stack=tech_stack,
                metrics=metrics,
                structure=structure,
                scan_successful=True,
            )

        except PermissionError as e:
            error_msg = f"Permission denied while scanning project: {e}"
            logger.error(error_msg)
            return ScanResult(
                tech_stack=TechStack(primary_language="unknown"),
                metrics=CodeMetrics(),
                structure=ProjectStructure(root_path=self.project_path),
                scan_successful=False,
                error_message=error_msg,
            )

        except OSError as e:
            error_msg = f"File system error during scan: {e}"
            logger.error(error_msg)
            return ScanResult(
                tech_stack=TechStack(primary_language="unknown"),
                metrics=CodeMetrics(),
                structure=ProjectStructure(root_path=self.project_path),
                scan_successful=False,
                error_message=error_msg,
            )

        except Exception as e:
            error_msg = f"Unexpected error during scan: {e}"
            logger.exception(error_msg)  # Includes stack trace
            return ScanResult(
                tech_stack=TechStack(primary_language="unknown"),
                metrics=CodeMetrics(),
                structure=ProjectStructure(root_path=self.project_path),
                scan_successful=False,
                error_message=error_msg,
            )

    def _detect_tech_stack(self) -> TechStack:
        """Detect technology stack from project files."""
        detected_languages = []
        detected_frameworks = []
        build_tools = []
        runtime_version = None
        package_manager = None

        # Detect languages from indicator files
        for language, indicators in self.TECH_INDICATORS.items():
            for indicator in indicators:
                if "*" in indicator:  # Glob pattern
                    if list(self.project_path.glob(indicator)):
                        detected_languages.append(language)
                        break
                else:
                    if (self.project_path / indicator).exists():
                        detected_languages.append(language)
                        break

        # Detect frameworks from dependencies
        detected_frameworks = self._detect_frameworks()

        # Detect build tools
        if (self.project_path / "package.json").exists():
            package_manager = self._detect_node_package_manager()
            build_tools.extend(self._detect_node_build_tools())
            runtime_version = self._detect_node_version()

        elif (self.project_path / "pom.xml").exists():
            build_tools.append("maven")
            runtime_version = self._detect_java_version()

        elif (self.project_path / "build.gradle").exists() or (self.project_path / "build.gradle.kts").exists():
            build_tools.append("gradle")
            runtime_version = self._detect_java_version()

        elif (self.project_path / "Cargo.toml").exists():
            build_tools.append("cargo")
            runtime_version = self._detect_rust_version()

        elif (self.project_path / "go.mod").exists():
            build_tools.append("go")
            runtime_version = self._detect_go_version()

        # Determine primary language
        primary_language = detected_languages[0] if detected_languages else "unknown"

        return TechStack(
            primary_language=primary_language,
            languages=detected_languages,
            frameworks=detected_frameworks,
            build_tools=build_tools,
            runtime_version=runtime_version,
            package_manager=package_manager,
        )

    def _detect_frameworks(self) -> List[str]:
        """Detect frameworks from dependency files."""
        frameworks = []

        # Node.js frameworks from package.json
        package_json = self.project_path / "package.json"
        if package_json.exists():
            import json
            try:
                with open(package_json, "r") as f:
                    data = json.load(f)
                    all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

                    for framework, indicators in self.FRAMEWORK_INDICATORS.items():
                        for indicator in indicators:
                            if indicator in all_deps:
                                frameworks.append(framework)
                                break
            except Exception:
                pass

        # Python frameworks from requirements.txt
        requirements_files = ["requirements.txt", "requirements-dev.txt", "pyproject.toml"]
        for req_file in requirements_files:
            req_path = self.project_path / req_file
            if req_path.exists():
                try:
                    with open(req_path, "r") as f:
                        content = f.read().lower()
                        for framework, indicators in self.FRAMEWORK_INDICATORS.items():
                            for indicator in indicators:
                                if indicator.lower() in content:
                                    frameworks.append(framework)
                                    break
                except Exception:
                    pass
                break  # Only check one requirements file

        # Java frameworks from pom.xml
        pom_xml = self.project_path / "pom.xml"
        if pom_xml.exists():
            try:
                with open(pom_xml, "r") as f:
                    content = f.read()
                    for framework, indicators in self.FRAMEWORK_INDICATORS.items():
                        for indicator in indicators:
                            if indicator in content:
                                frameworks.append(framework)
                                break
            except Exception:
                pass

        return list(set(frameworks))  # Remove duplicates

    def _detect_node_package_manager(self) -> Optional[str]:
        """Detect Node.js package manager."""
        if (self.project_path / "pnpm-lock.yaml").exists():
            return "pnpm"
        elif (self.project_path / "yarn.lock").exists():
            return "yarn"
        elif (self.project_path / "package-lock.json").exists():
            return "npm"
        return "npm"  # Default

    def _detect_node_build_tools(self) -> List[str]:
        """Detect Node.js build tools."""
        build_tools = []
        package_json = self.project_path / "package.json"

        if package_json.exists():
            import json
            try:
                with open(package_json, "r") as f:
                    data = json.load(f)
                    all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

                    build_tool_indicators = {
                        "webpack": ["webpack"],
                        "vite": ["vite"],
                        "rollup": ["rollup"],
                        "esbuild": ["esbuild"],
                        "parcel": ["parcel"],
                    }

                    for tool, indicators in build_tool_indicators.items():
                        for indicator in indicators:
                            if indicator in all_deps:
                                build_tools.append(tool)
                                break
            except Exception:
                pass

        return build_tools

    def _detect_node_version(self) -> Optional[str]:
        """Detect Node.js version from .nvmrc or package.json."""
        # Check .nvmrc
        nvmrc = self.project_path / ".nvmrc"
        if nvmrc.exists():
            try:
                return nvmrc.read_text().strip()
            except Exception:
                pass

        # Check package.json engines
        package_json = self.project_path / "package.json"
        if package_json.exists():
            import json
            try:
                with open(package_json, "r") as f:
                    data = json.load(f)
                    return data.get("engines", {}).get("node")
            except Exception:
                pass

        return None

    def _detect_java_version(self) -> Optional[str]:
        """Detect Java version from pom.xml or build.gradle."""
        pom_xml = self.project_path / "pom.xml"
        if pom_xml.exists():
            try:
                with open(pom_xml, "r") as f:
                    content = f.read()
                    # Simple regex to find maven.compiler.source or target
                    import re
                    match = re.search(r"<maven\.compiler\.(source|target)>(\d+(?:\.\d+)?)</maven\.compiler\.\1>", content)
                    if match:
                        return match.group(2)
            except Exception:
                pass

        return None

    def _detect_rust_version(self) -> Optional[str]:
        """Detect Rust version from rust-toolchain."""
        rust_toolchain = self.project_path / "rust-toolchain"
        if rust_toolchain.exists():
            try:
                return rust_toolchain.read_text().strip()
            except Exception:
                pass

        return None

    def _detect_go_version(self) -> Optional[str]:
        """Detect Go version from go.mod."""
        go_mod = self.project_path / "go.mod"
        if go_mod.exists():
            try:
                with open(go_mod, "r") as f:
                    for line in f:
                        if line.startswith("go "):
                            return line.split()[1]
            except Exception:
                pass

        return None

    def _calculate_metrics(self) -> CodeMetrics:
        """Calculate code metrics using cloc or tokei if available."""
        # Try cloc first
        if self._check_tool_available("cloc"):
            return self._calculate_metrics_cloc()

        # Try tokei
        if self._check_tool_available("tokei"):
            return self._calculate_metrics_tokei()

        # Fallback: manual count (less accurate)
        return self._calculate_metrics_manual()

    def _calculate_metrics_cloc(self) -> CodeMetrics:
        """Calculate metrics using cloc."""
        try:
            result = subprocess.run(
                ["cloc", ".", "--json", "--exclude-dir=node_modules,vendor,.git,venv,__pycache__,build,dist"],
                capture_output=True,
                text=True,
                cwd=self.project_path,
                timeout=DEFAULT_CONFIG.security.subprocess_timeout_long,
            )

            if result.returncode == 0 and result.stdout:
                import json
                data = json.loads(result.stdout)
                summary = data.get("SUM", {})

                languages_breakdown = {}
                for lang, stats in data.items():
                    if lang not in ["header", "SUM"]:
                        languages_breakdown[lang] = stats.get("code", 0)

                logger.info(f"cloc analysis complete: {summary.get('code', 0)} lines of code")
                return CodeMetrics(
                    total_lines=summary.get("blank", 0) + summary.get("comment", 0) + summary.get("code", 0),
                    code_lines=summary.get("code", 0),
                    comment_lines=summary.get("comment", 0),
                    blank_lines=summary.get("blank", 0),
                    file_count=summary.get("nFiles", 0),
                    languages_breakdown=languages_breakdown,
                )
        except subprocess.TimeoutExpired:
            logger.warning(f"cloc analysis timed out after {DEFAULT_CONFIG.security.subprocess_timeout_long}s")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse cloc output: {e}")
        except Exception as e:
            logger.warning(f"cloc analysis failed: {e}")

        return CodeMetrics()

    def _calculate_metrics_tokei(self) -> CodeMetrics:
        """Calculate metrics using tokei."""
        try:
            result = subprocess.run(
                ["tokei", ".", "--output", "json"],
                capture_output=True,
                text=True,
                cwd=self.project_path,
                timeout=DEFAULT_CONFIG.security.subprocess_timeout_long,
            )

            if result.returncode == 0 and result.stdout:
                import json
                data = json.loads(result.stdout)

                total_code = 0
                total_comments = 0
                total_blanks = 0
                languages_breakdown = {}

                for lang, stats in data.items():
                    if lang != "Total":
                        code = stats.get("code", 0)
                        total_code += code
                        total_comments += stats.get("comments", 0)
                        total_blanks += stats.get("blanks", 0)
                        languages_breakdown[lang] = code

                logger.info(f"tokei analysis complete: {total_code} lines of code")
                return CodeMetrics(
                    total_lines=total_code + total_comments + total_blanks,
                    code_lines=total_code,
                    comment_lines=total_comments,
                    blank_lines=total_blanks,
                    file_count=len(list(self.project_path.rglob("*.*"))),
                    languages_breakdown=languages_breakdown,
                )
        except subprocess.TimeoutExpired:
            logger.warning(f"tokei analysis timed out after {DEFAULT_CONFIG.security.subprocess_timeout_long}s")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tokei output: {e}")
        except Exception as e:
            logger.warning(f"tokei analysis failed: {e}")

        return CodeMetrics()

    def _calculate_metrics_manual(self) -> CodeMetrics:
        """Manual metric calculation (fallback). Optimized for performance."""
        exclude_dirs = {"node_modules", "vendor", ".git", "venv", "__pycache__", "build", "dist", ".next", "target"}
        file_extensions = {".py", ".js", ".ts", ".java", ".go", ".rs", ".rb", ".php", ".cs"}

        file_count = 0
        total_lines = 0

        logger.info("Using manual file counting (cloc/tokei not available)")

        # Use rglob for better performance than os.walk
        for file_path in self.project_path.rglob("*"):
            # Skip if not a file
            if not file_path.is_file():
                continue

            # Skip if in excluded directory
            if any(part in exclude_dirs for part in file_path.parts):
                continue

            # Skip if not a code file
            if file_path.suffix not in file_extensions:
                continue

            file_count += 1

            # Stream file line by line instead of loading all into memory
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    total_lines += sum(1 for _ in f)
            except PermissionError:
                logger.debug(f"Permission denied reading file: {file_path}")
            except Exception as e:
                logger.debug(f"Error reading file {file_path}: {e}")

        logger.info(f"Manual count complete: {file_count} files, ~{total_lines} lines")

        return CodeMetrics(
            total_lines=total_lines,
            code_lines=int(total_lines * 0.7),  # Rough estimate
            comment_lines=int(total_lines * 0.1),
            blank_lines=int(total_lines * 0.2),
            file_count=file_count,
        )

    def _analyze_structure(self) -> ProjectStructure:
        """Analyze project structure."""
        source_dirs = []
        test_dirs = []
        config_files = []
        doc_files = []

        # Common patterns
        source_patterns = ["src", "lib", "app", "source"]
        test_patterns = ["test", "tests", "__tests__", "spec", "specs"]
        config_patterns = ["*.config.js", "*.config.ts", "config.json", "tsconfig.json", "babel.config.js"]
        doc_patterns = ["README.md", "CONTRIBUTING.md", "docs", "documentation"]

        # Find source directories
        for pattern in source_patterns:
            if (self.project_path / pattern).is_dir():
                source_dirs.append(pattern)

        # Find test directories
        for pattern in test_patterns:
            if (self.project_path / pattern).is_dir():
                test_dirs.append(pattern)

        # Find config files
        for pattern in config_patterns:
            if "*" in pattern:
                config_files.extend([str(f.relative_to(self.project_path)) for f in self.project_path.glob(pattern)])
            else:
                if (self.project_path / pattern).exists():
                    config_files.append(pattern)

        # Find doc files
        for pattern in doc_patterns:
            if (self.project_path / pattern).exists():
                doc_files.append(pattern)

        # Check for CI/CD
        has_ci_cd = (
            (self.project_path / ".github" / "workflows").is_dir() or
            (self.project_path / ".gitlab-ci.yml").exists() or
            (self.project_path / "Jenkinsfile").exists()
        )

        return ProjectStructure(
            root_path=self.project_path,
            source_dirs=source_dirs,
            test_dirs=test_dirs,
            config_files=config_files,
            doc_files=doc_files,
            has_ci_cd=has_ci_cd,
            has_tests=len(test_dirs) > 0,
            has_documentation=len(doc_files) > 0,
        )

    def _check_tool_available(self, tool_name: str) -> bool:
        """Check if a command-line tool is available."""
        try:
            result = subprocess.run(
                ["which", tool_name],
                capture_output=True,
                text=True,
                timeout=DEFAULT_CONFIG.security.subprocess_timeout_quick,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout checking for tool: {tool_name}")
            return False
        except Exception as e:
            logger.warning(f"Error checking for tool {tool_name}: {e}")
            return False


def main():
    """Example usage of ProjectScanner."""
    import sys

    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path.cwd()

    print(f"Scanning project: {project_path}\n")

    scanner = ProjectScanner(project_path)
    result = scanner.scan_project()

    if not result.scan_successful:
        print(f"Error: {result.error_message}")
        return

    print("=== Tech Stack ===")
    print(f"Primary Language: {result.tech_stack.primary_language}")
    print(f"Languages: {', '.join(result.tech_stack.languages)}")
    print(f"Frameworks: {', '.join(result.tech_stack.frameworks) or 'None detected'}")
    print(f"Build Tools: {', '.join(result.tech_stack.build_tools) or 'None detected'}")
    print(f"Package Manager: {result.tech_stack.package_manager or 'N/A'}")
    print(f"Runtime Version: {result.tech_stack.runtime_version or 'Not detected'}")

    print("\n=== Code Metrics ===")
    print(f"Total Lines: {result.metrics.total_lines:,}")
    print(f"Code Lines: {result.metrics.code_lines:,}")
    print(f"Comment Lines: {result.metrics.comment_lines:,}")
    print(f"Blank Lines: {result.metrics.blank_lines:,}")
    print(f"File Count: {result.metrics.file_count}")

    if result.metrics.languages_breakdown:
        print("\nLanguages Breakdown:")
        for lang, lines in sorted(result.metrics.languages_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {lang}: {lines:,} lines")

    print("\n=== Project Structure ===")
    print(f"Source Directories: {', '.join(result.structure.source_dirs) or 'None found'}")
    print(f"Test Directories: {', '.join(result.structure.test_dirs) or 'None found'}")
    print(f"Has CI/CD: {result.structure.has_ci_cd}")
    print(f"Has Tests: {result.structure.has_tests}")
    print(f"Has Documentation: {result.structure.has_documentation}")


if __name__ == "__main__":
    main()
