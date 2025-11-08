"""
Python specific analyzer.

Deep analysis for Python projects including framework detection,
virtual environment management, and package analysis.
"""

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class PythonAnalysis:
    """Container for Python-specific analysis results."""

    framework: Optional[str] = None
    framework_version: Optional[str] = None
    python_version: Optional[str] = None
    python_version_source: Optional[str] = None
    package_manager: str = "pip"
    virtual_env_tool: Optional[str] = None
    linting: List[str] = field(default_factory=list)
    testing_frameworks: List[str] = field(default_factory=list)
    type_checking: bool = False
    async_framework: bool = False
    orm: Optional[str] = None
    api_framework: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


class PythonAnalyzer:
    """
    Analyze Python projects in depth.

    Detects frameworks, package managers, virtual environments, and provides
    specific recommendations for modernization.
    """

    FRAMEWORKS = {
        "django": ["django", "Django"],
        "flask": ["flask", "Flask"],
        "fastapi": ["fastapi", "FastAPI"],
        "pyramid": ["pyramid"],
        "tornado": ["tornado"],
        "bottle": ["bottle"],
        "sanic": ["sanic"],
        "starlette": ["starlette"],
        "aiohttp": ["aiohttp"],
    }

    TESTING = {
        "pytest": ["pytest"],
        "unittest": [],  # Built-in, detect from imports
        "nose": ["nose", "nose2"],
        "doctest": [],  # Built-in
    }

    LINTERS = {
        "pylint": ["pylint"],
        "flake8": ["flake8"],
        "black": ["black"],
        "ruff": ["ruff"],
        "mypy": ["mypy"],
        "bandit": ["bandit"],
    }

    ORMS = {
        "sqlalchemy": ["sqlalchemy", "SQLAlchemy"],
        "django-orm": ["django"],  # Django has built-in ORM
        "peewee": ["peewee"],
        "tortoise-orm": ["tortoise-orm"],
        "pony": ["pony"],
    }

    def __init__(self, project_path: Path):
        """
        Initialize Python analyzer.

        Args:
            project_path: Path to project root
        """
        self.project_path = Path(project_path)

    def analyze(self) -> PythonAnalysis:
        """
        Perform comprehensive Python analysis.

        Returns:
            PythonAnalysis with detailed findings
        """
        analysis = PythonAnalysis()

        # Get all dependencies
        all_deps = self._get_all_dependencies()

        # Detect components
        analysis.framework, analysis.framework_version = self._detect_framework(all_deps)
        analysis.python_version, analysis.python_version_source = self._detect_python_version()
        analysis.package_manager = self._detect_package_manager()
        analysis.virtual_env_tool = self._detect_virtual_env()
        analysis.linting = self._detect_linting(all_deps)
        analysis.testing_frameworks = self._detect_testing(all_deps)
        analysis.type_checking = self._detect_type_checking(all_deps)
        analysis.async_framework = self._detect_async_framework(all_deps)
        analysis.orm = self._detect_orm(all_deps)
        analysis.api_framework = self._detect_api_framework(all_deps)

        # Generate recommendations
        analysis.recommendations = self._generate_recommendations(analysis, all_deps)

        return analysis

    def _get_all_dependencies(self) -> Dict[str, Optional[str]]:
        """Get all dependencies from requirements files."""
        deps = {}

        # Try various requirements files
        requirements_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements.in",
            "dev-requirements.txt",
        ]

        for req_file in requirements_files:
            req_path = self.project_path / req_file
            if req_path.exists():
                try:
                    with open(req_path, "r") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                # Parse package name and version
                                match = re.match(r"^([a-zA-Z0-9_-]+)([>=<~!]+.*)?$", line)
                                if match:
                                    package = match.group(1).lower()
                                    version = match.group(2) if match.group(2) else None
                                    deps[package] = version
                except Exception:
                    pass

        # Try pyproject.toml (Poetry/PEP 621)
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject, "r") as f:
                    content = f.read()
                    # Simple regex to extract dependencies
                    for match in re.finditer(r'"([^"]+)"\s*=', content):
                        package = match.group(1).lower()
                        if package not in ["python", "name", "version", "description"]:
                            deps[package] = None
            except Exception:
                pass

        # Try Pipfile
        pipfile = self.project_path / "Pipfile"
        if pipfile.exists():
            try:
                with open(pipfile, "r") as f:
                    content = f.read()
                    # Simple regex to extract packages
                    for match in re.finditer(r'([a-zA-Z0-9_-]+)\s*=\s*"([^"]*)"', content):
                        package = match.group(1).lower()
                        version = match.group(2)
                        deps[package] = version if version else None
            except Exception:
                pass

        return deps

    def _detect_framework(self, deps: Dict[str, Optional[str]]) -> tuple[Optional[str], Optional[str]]:
        """Detect Python web framework."""
        for framework, indicators in self.FRAMEWORKS.items():
            for indicator in indicators:
                if indicator.lower() in deps:
                    version = deps.get(indicator.lower())
                    return framework, version
        return None, None

    def _detect_python_version(self) -> tuple[Optional[str], Optional[str]]:
        """Detect Python version from various sources."""
        # Check .python-version (pyenv)
        python_version_file = self.project_path / ".python-version"
        if python_version_file.exists():
            try:
                version = python_version_file.read_text().strip()
                return version, ".python-version"
            except Exception:
                pass

        # Check runtime.txt (Heroku)
        runtime_txt = self.project_path / "runtime.txt"
        if runtime_txt.exists():
            try:
                content = runtime_txt.read_text().strip()
                match = re.search(r"python-(\d+\.\d+\.?\d*)", content)
                if match:
                    return match.group(1), "runtime.txt"
            except Exception:
                pass

        # Check pyproject.toml
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject, "r") as f:
                    content = f.read()
                    match = re.search(r'python\s*=\s*"([^"]+)"', content)
                    if match:
                        return match.group(1), "pyproject.toml"
            except Exception:
                pass

        # Check setup.py
        setup_py = self.project_path / "setup.py"
        if setup_py.exists():
            try:
                with open(setup_py, "r") as f:
                    content = f.read()
                    match = re.search(r'python_requires\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        return match.group(1), "setup.py"
            except Exception:
                pass

        return None, None

    def _detect_package_manager(self) -> str:
        """Detect package manager from project files."""
        if (self.project_path / "poetry.lock").exists():
            return "poetry"
        elif (self.project_path / "Pipfile.lock").exists():
            return "pipenv"
        elif (self.project_path / "pdm.lock").exists():
            return "pdm"
        elif (self.project_path / "pyproject.toml").exists():
            # Could be Poetry, PDM, or PEP 621
            try:
                with open(self.project_path / "pyproject.toml", "r") as f:
                    content = f.read()
                    if "[tool.poetry]" in content:
                        return "poetry"
                    elif "[tool.pdm]" in content:
                        return "pdm"
            except Exception:
                pass

        return "pip"  # Default

    def _detect_virtual_env(self) -> Optional[str]:
        """Detect virtual environment tool."""
        if (self.project_path / ".venv").exists():
            return "venv"
        elif (self.project_path / "venv").exists():
            return "venv"
        elif (self.project_path / ".python-version").exists():
            return "pyenv"
        elif (self.project_path / "Pipfile").exists():
            return "pipenv"
        elif (self.project_path / "poetry.lock").exists():
            return "poetry"

        return None

    def _detect_linting(self, deps: Dict[str, Optional[str]]) -> List[str]:
        """Detect linting tools."""
        linters = []
        for linter, indicators in self.LINTERS.items():
            for indicator in indicators:
                if indicator.lower() in deps:
                    linters.append(linter)
                    break
        return linters

    def _detect_testing(self, deps: Dict[str, Optional[str]]) -> List[str]:
        """Detect testing frameworks."""
        frameworks = []
        for framework, indicators in self.TESTING.items():
            if not indicators:  # Built-in (unittest, doctest)
                # Would need to scan imports
                continue
            for indicator in indicators:
                if indicator.lower() in deps:
                    frameworks.append(framework)
                    break
        return frameworks

    def _detect_type_checking(self, deps: Dict[str, Optional[str]]) -> bool:
        """Check if type checking is used."""
        return "mypy" in deps or "pyright" in deps or "pyre-check" in deps

    def _detect_async_framework(self, deps: Dict[str, Optional[str]]) -> bool:
        """Check if async framework is used."""
        async_indicators = ["asyncio", "aiohttp", "fastapi", "starlette", "sanic"]
        return any(indicator in deps for indicator in async_indicators)

    def _detect_orm(self, deps: Dict[str, Optional[str]]) -> Optional[str]:
        """Detect ORM."""
        for orm, indicators in self.ORMS.items():
            for indicator in indicators:
                if indicator.lower() in deps:
                    return orm
        return None

    def _detect_api_framework(self, deps: Dict[str, Optional[str]]) -> Optional[str]:
        """Detect API framework."""
        api_frameworks = {
            "django-rest-framework": ["djangorestframework", "django-rest-framework"],
            "flask-restful": ["flask-restful"],
            "fastapi": ["fastapi"],
            "graphene": ["graphene"],
        }

        for framework, indicators in api_frameworks.items():
            for indicator in indicators:
                if indicator.lower() in deps:
                    return framework

        return None

    def _generate_recommendations(self, analysis: PythonAnalysis, deps: Dict[str, Optional[str]]) -> List[str]:
        """Generate modernization recommendations."""
        recommendations = []

        # Python version recommendations
        if analysis.python_version:
            try:
                # Extract major.minor version
                version_match = re.match(r"(\d+)\.(\d+)", analysis.python_version)
                if version_match:
                    major = int(version_match.group(1))
                    minor = int(version_match.group(2))

                    if major == 3 and minor < 11:
                        recommendations.append(
                            f"Upgrade Python from 3.{minor} to 3.11 or 3.12 for better performance"
                        )
                    elif major == 2:
                        recommendations.append(
                            "Upgrade Python from 2.x to 3.12 (Python 2 is EOL since 2020)"
                        )
            except Exception:
                pass

        # Type checking recommendations
        if not analysis.type_checking:
            recommendations.append("Add MyPy or Pyright for static type checking")

        # Linting recommendations
        if not analysis.linting:
            recommendations.append("Add linting tools (Ruff recommended for fast linting)")
        elif "pylint" in analysis.linting and "ruff" not in analysis.linting:
            recommendations.append("Consider migrating from Pylint to Ruff for faster linting")

        if "black" not in analysis.linting and "ruff" not in analysis.linting:
            recommendations.append("Add Black or Ruff for code formatting")

        # Testing recommendations
        if not analysis.testing_frameworks:
            recommendations.append("Add testing framework (pytest recommended)")

        # Package manager recommendations
        if analysis.package_manager == "pip":
            recommendations.append("Consider using Poetry or PDM for better dependency management")

        # Framework-specific recommendations
        if analysis.framework == "django":
            if analysis.framework_version:
                try:
                    version_match = re.match(r"(\d+)\.(\d+)", analysis.framework_version)
                    if version_match:
                        major = int(version_match.group(1))
                        if major < 4:
                            recommendations.append(f"Upgrade Django from {major}.x to 4.2 LTS or 5.0")
                except Exception:
                    pass

            if not analysis.api_framework:
                recommendations.append("Consider adding Django REST Framework for API development")

        elif analysis.framework == "flask":
            if not analysis.async_framework:
                recommendations.append("Consider migrating to FastAPI for modern async Python web development")

        elif analysis.framework == "fastapi":
            # FastAPI is modern, fewer recommendations
            if not analysis.orm:
                recommendations.append("Consider adding SQLAlchemy for database operations")

        # Async recommendations
        if not analysis.async_framework and analysis.framework in ["flask", "django"]:
            recommendations.append("Consider using async/await patterns for improved performance")

        # Security recommendations
        if "bandit" not in analysis.linting:
            recommendations.append("Add Bandit for security vulnerability scanning")

        return recommendations


def main():
    """Example usage of PythonAnalyzer."""
    import sys

    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path.cwd()

    print(f"Analyzing Python project: {project_path}\n")

    analyzer = PythonAnalyzer(project_path)
    analysis = analyzer.analyze()

    print("=== Python Analysis ===")
    print(f"Framework: {analysis.framework or 'None detected'}")
    if analysis.framework_version:
        print(f"Framework Version: {analysis.framework_version}")
    print(f"Python Version: {analysis.python_version or 'Not specified'}")
    if analysis.python_version_source:
        print(f"  Source: {analysis.python_version_source}")
    print(f"Package Manager: {analysis.package_manager}")
    print(f"Virtual Env Tool: {analysis.virtual_env_tool or 'None detected'}")
    print(f"Linting: {', '.join(analysis.linting) if analysis.linting else 'None'}")
    print(f"Testing: {', '.join(analysis.testing_frameworks) if analysis.testing_frameworks else 'None'}")
    print(f"Type Checking: {analysis.type_checking}")
    print(f"Async Framework: {analysis.async_framework}")
    print(f"ORM: {analysis.orm or 'None'}")
    print(f"API Framework: {analysis.api_framework or 'None'}")

    if analysis.recommendations:
        print("\n=== Recommendations ===")
        for i, rec in enumerate(analysis.recommendations, 1):
            print(f"{i}. {rec}")


if __name__ == "__main__":
    main()
