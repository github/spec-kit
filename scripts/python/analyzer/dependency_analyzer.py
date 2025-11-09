"""
Dependency analyzer for reverse engineering analysis.

Integrates with npm audit (Node.js), pip-audit (Python), and other package
security tools to analyze project dependencies for security vulnerabilities,
outdated packages, and deprecation warnings.
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

# Handle both relative and absolute imports
try:
    from .config import DEFAULT_CONFIG
    from .security import validate_project_path, SecurityError
except ImportError:
    from config import DEFAULT_CONFIG
    from security import validate_project_path, SecurityError

logger = logging.getLogger(__name__)


@dataclass
class DependencyIssue:
    """Container for a single dependency issue."""

    package_name: str
    current_version: str
    latest_version: Optional[str] = None
    severity: str = "info"  # info, low, medium, high, critical
    issue_type: str = "outdated"  # outdated, vulnerable, deprecated
    cve: Optional[str] = None
    description: Optional[str] = None
    fix_available: bool = False


@dataclass
class DependencyReport:
    """Container for dependency analysis results."""

    ecosystem: str  # npm, pip, maven, nuget, etc.
    total_dependencies: int
    outdated_count: int
    vulnerable_count: int
    deprecated_count: int
    issues: List[DependencyIssue]
    tool_available: bool = True
    analysis_successful: bool = True
    error_message: Optional[str] = None


class DependencyAnalyzer:
    """
    Analyze project dependencies for security and maintenance issues.

    Supports multiple package ecosystems with graceful degradation if tools unavailable.
    """

    def __init__(self, project_path: Path):
        """
        Initialize dependency analyzer.

        Args:
            project_path: Path to project root directory

        Raises:
            SecurityError: If path is unsafe
            FileNotFoundError: If path doesn't exist
        """
        # Validate path for security
        try:
            self.project_path = validate_project_path(Path(project_path))
            logger.info(f"Initialized dependency analyzer for: {self.project_path}")
        except (SecurityError, FileNotFoundError, PermissionError) as e:
            logger.error(f"Cannot initialize dependency analyzer: {e}")
            raise

    def analyze_dependencies(self) -> List[DependencyReport]:
        """
        Analyze all dependency files in the project.

        Returns:
            List of DependencyReport for each detected ecosystem
        """
        reports = []

        # Check for Node.js/npm
        if (self.project_path / "package.json").exists():
            npm_report = self.analyze_npm_dependencies()
            reports.append(npm_report)

        # Check for Python
        requirements_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements.in",
            "Pipfile",
            "pyproject.toml",
        ]
        for req_file in requirements_files:
            if (self.project_path / req_file).exists():
                python_report = self.analyze_python_dependencies()
                reports.append(python_report)
                break  # Only analyze once for Python

        # Check for Java/Maven
        if (self.project_path / "pom.xml").exists():
            maven_report = self._create_unsupported_report("maven")
            reports.append(maven_report)

        # Check for .NET/NuGet
        csproj_files = list(self.project_path.glob("*.csproj"))
        if csproj_files:
            nuget_report = self._create_unsupported_report("nuget")
            reports.append(nuget_report)

        # Check for Ruby/Bundler
        if (self.project_path / "Gemfile").exists():
            ruby_report = self._create_unsupported_report("ruby")
            reports.append(ruby_report)

        # Check for PHP/Composer
        if (self.project_path / "composer.json").exists():
            php_report = self._create_unsupported_report("php")
            reports.append(php_report)

        return reports

    def analyze_npm_dependencies(self) -> DependencyReport:
        """
        Analyze Node.js dependencies using npm audit and npm outdated.

        Returns:
            DependencyReport for npm ecosystem
        """
        package_json_path = self.project_path / "package.json"

        if not package_json_path.exists():
            return DependencyReport(
                ecosystem="npm",
                total_dependencies=0,
                outdated_count=0,
                vulnerable_count=0,
                deprecated_count=0,
                issues=[],
                tool_available=False,
                analysis_successful=False,
                error_message="package.json not found",
            )

        # Load package.json to count dependencies
        try:
            with open(package_json_path, "r") as f:
                package_data = json.load(f)
                deps = package_data.get("dependencies", {})
                dev_deps = package_data.get("devDependencies", {})
                total_deps = len(deps) + len(dev_deps)
        except Exception as e:
            total_deps = 0

        issues = []

        # Check if npm is available
        npm_available = self._check_tool_available("npm")

        if not npm_available:
            return DependencyReport(
                ecosystem="npm",
                total_dependencies=total_deps,
                outdated_count=0,
                vulnerable_count=0,
                deprecated_count=0,
                issues=[],
                tool_available=False,
                analysis_successful=False,
                error_message="npm not installed",
            )

        # Run npm audit
        vulnerable_issues = self._run_npm_audit()
        issues.extend(vulnerable_issues)

        # Run npm outdated
        outdated_issues = self._run_npm_outdated()
        issues.extend(outdated_issues)

        # Count by type
        outdated_count = len([i for i in issues if i.issue_type == "outdated"])
        vulnerable_count = len([i for i in issues if i.issue_type == "vulnerable"])
        deprecated_count = len([i for i in issues if i.issue_type == "deprecated"])

        return DependencyReport(
            ecosystem="npm",
            total_dependencies=total_deps,
            outdated_count=outdated_count,
            vulnerable_count=vulnerable_count,
            deprecated_count=deprecated_count,
            issues=issues,
            tool_available=True,
            analysis_successful=True,
        )

    def analyze_python_dependencies(self) -> DependencyReport:
        """
        Analyze Python dependencies using pip-audit and pip list --outdated.

        Returns:
            DependencyReport for Python ecosystem
        """
        # Find requirements file
        requirements_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements.in",
        ]

        req_file = None
        for rf in requirements_files:
            if (self.project_path / rf).exists():
                req_file = self.project_path / rf
                break

        if not req_file and not (self.project_path / "pyproject.toml").exists():
            return DependencyReport(
                ecosystem="pip",
                total_dependencies=0,
                outdated_count=0,
                vulnerable_count=0,
                deprecated_count=0,
                issues=[],
                tool_available=False,
                analysis_successful=False,
                error_message="No Python dependency file found",
            )

        # Count dependencies
        total_deps = 0
        if req_file:
            try:
                with open(req_file, "r") as f:
                    lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                    total_deps = len(lines)
            except Exception:
                total_deps = 0

        issues = []

        # Check if pip is available
        pip_available = self._check_tool_available("pip") or self._check_tool_available("pip3")

        if not pip_available:
            return DependencyReport(
                ecosystem="pip",
                total_dependencies=total_deps,
                outdated_count=0,
                vulnerable_count=0,
                deprecated_count=0,
                issues=[],
                tool_available=False,
                analysis_successful=False,
                error_message="pip not installed",
            )

        # Run pip-audit if available
        pip_audit_available = self._check_tool_available("pip-audit")
        if pip_audit_available:
            vulnerable_issues = self._run_pip_audit(req_file)
            issues.extend(vulnerable_issues)

        # Run pip list --outdated
        outdated_issues = self._run_pip_outdated()
        issues.extend(outdated_issues)

        # Count by type
        outdated_count = len([i for i in issues if i.issue_type == "outdated"])
        vulnerable_count = len([i for i in issues if i.issue_type == "vulnerable"])
        deprecated_count = len([i for i in issues if i.issue_type == "deprecated"])

        return DependencyReport(
            ecosystem="pip",
            total_dependencies=total_deps,
            outdated_count=outdated_count,
            vulnerable_count=vulnerable_count,
            deprecated_count=deprecated_count,
            issues=issues,
            tool_available=True,
            analysis_successful=True,
        )

    # Private helper methods

    def _check_tool_available(self, tool_name: str) -> bool:
        """Check if a command-line tool is available."""
        try:
            result = subprocess.run(
                ["which", tool_name],
                capture_output=True,
                text=True,
                cwd=self.project_path,
                timeout=DEFAULT_CONFIG.security.subprocess_timeout_quick,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout checking for tool: {tool_name}")
            return False
        except Exception as e:
            logger.debug(f"Error checking for tool {tool_name}: {e}")
            return False

    def _run_npm_audit(self) -> List[DependencyIssue]:
        """Run npm audit and parse results."""
        issues = []

        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                cwd=self.project_path,
                timeout=DEFAULT_CONFIG.security.subprocess_timeout_default,
            )

            if result.stdout:
                audit_data = json.loads(result.stdout)

                # npm audit v7+ format
                if "vulnerabilities" in audit_data:
                    for pkg_name, vuln_data in audit_data.get("vulnerabilities", {}).items():
                        issue = DependencyIssue(
                            package_name=pkg_name,
                            current_version=vuln_data.get("range", "unknown"),
                            severity=vuln_data.get("severity", "unknown"),
                            issue_type="vulnerable",
                            description=vuln_data.get("via", [{}])[0].get("title") if isinstance(vuln_data.get("via"), list) else None,
                            fix_available=vuln_data.get("fixAvailable", False),
                        )
                        issues.append(issue)

                logger.info(f"npm audit found {len(issues)} vulnerabilities")

        except subprocess.TimeoutExpired:
            logger.warning(f"npm audit timed out after {DEFAULT_CONFIG.security.subprocess_timeout_default}s")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse npm audit output: {e}")
        except Exception as e:
            logger.warning(f"npm audit failed: {e}")

        return issues

    def _run_npm_outdated(self) -> List[DependencyIssue]:
        """Run npm outdated and parse results."""
        issues = []

        try:
            result = subprocess.run(
                ["npm", "outdated", "--json"],
                capture_output=True,
                text=True,
                cwd=self.project_path,
                timeout=60,
            )

            if result.stdout:
                outdated_data = json.loads(result.stdout)

                for pkg_name, pkg_info in outdated_data.items():
                    issue = DependencyIssue(
                        package_name=pkg_name,
                        current_version=pkg_info.get("current", "unknown"),
                        latest_version=pkg_info.get("latest", "unknown"),
                        severity="info",
                        issue_type="outdated",
                    )
                    issues.append(issue)

        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass

        return issues

    def _run_pip_audit(self, requirements_file: Optional[Path]) -> List[DependencyIssue]:
        """Run pip-audit and parse results."""
        issues = []

        try:
            cmd = ["pip-audit", "--format=json"]
            if requirements_file:
                cmd.extend(["-r", str(requirements_file)])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_path,
                timeout=120,
            )

            if result.stdout:
                audit_data = json.loads(result.stdout)

                for vuln in audit_data.get("dependencies", []):
                    for vuln_detail in vuln.get("vulns", []):
                        issue = DependencyIssue(
                            package_name=vuln.get("name", "unknown"),
                            current_version=vuln.get("version", "unknown"),
                            severity=self._cvss_to_severity(vuln_detail.get("cvss", 0)),
                            issue_type="vulnerable",
                            cve=vuln_detail.get("id"),
                            description=vuln_detail.get("description"),
                            fix_available=bool(vuln_detail.get("fix_versions")),
                        )
                        issues.append(issue)

        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass

        return issues

    def _run_pip_outdated(self) -> List[DependencyIssue]:
        """Run pip list --outdated and parse results."""
        issues = []

        try:
            pip_cmd = "pip3" if self._check_tool_available("pip3") else "pip"

            result = subprocess.run(
                [pip_cmd, "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                cwd=self.project_path,
                timeout=60,
            )

            if result.stdout:
                outdated_data = json.loads(result.stdout)

                for pkg_info in outdated_data:
                    issue = DependencyIssue(
                        package_name=pkg_info.get("name", "unknown"),
                        current_version=pkg_info.get("version", "unknown"),
                        latest_version=pkg_info.get("latest_version", "unknown"),
                        severity="info",
                        issue_type="outdated",
                    )
                    issues.append(issue)

        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass

        return issues

    def _cvss_to_severity(self, cvss_score: float) -> str:
        """Convert CVSS score to severity level."""
        if cvss_score >= 9.0:
            return "critical"
        elif cvss_score >= 7.0:
            return "high"
        elif cvss_score >= 4.0:
            return "medium"
        elif cvss_score > 0:
            return "low"
        else:
            return "info"

    def _create_unsupported_report(self, ecosystem: str) -> DependencyReport:
        """Create a report for ecosystems not yet fully supported."""
        return DependencyReport(
            ecosystem=ecosystem,
            total_dependencies=0,
            outdated_count=0,
            vulnerable_count=0,
            deprecated_count=0,
            issues=[],
            tool_available=False,
            analysis_successful=False,
            error_message=f"{ecosystem} analysis not yet implemented",
        )


def main():
    """Example usage of DependencyAnalyzer."""
    import sys

    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path.cwd()

    print(f"Analyzing dependencies in: {project_path}")

    analyzer = DependencyAnalyzer(project_path)
    reports = analyzer.analyze_dependencies()

    for report in reports:
        print(f"\n=== {report.ecosystem.upper()} Dependencies ===")
        print(f"Total: {report.total_dependencies}")
        print(f"Outdated: {report.outdated_count}")
        print(f"Vulnerable: {report.vulnerable_count}")
        print(f"Deprecated: {report.deprecated_count}")
        print(f"Tool Available: {report.tool_available}")
        print(f"Analysis Successful: {report.analysis_successful}")

        if report.error_message:
            print(f"Error: {report.error_message}")

        if report.issues:
            print(f"\nTop {min(5, len(report.issues))} Issues:")
            for issue in report.issues[:5]:
                print(f"  - {issue.package_name} ({issue.current_version})")
                print(f"    Type: {issue.issue_type}, Severity: {issue.severity}")
                if issue.latest_version:
                    print(f"    Latest: {issue.latest_version}")
                if issue.cve:
                    print(f"    CVE: {issue.cve}")


if __name__ == "__main__":
    main()
