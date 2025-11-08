"""
.NET specific analyzer.

Deep analysis for .NET projects including framework detection,
NuGet packages, and project type analysis.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DotNetAnalysis:
    """Container for .NET-specific analysis results."""

    framework: Optional[str] = None
    framework_version: Optional[str] = None
    dotnet_version: Optional[str] = None
    project_type: Optional[str] = None  # web, console, library, etc.
    testing_frameworks: List[str] = field(default_factory=list)
    orm: Optional[str] = None
    web_framework: Optional[str] = None
    logging_framework: Optional[str] = None
    api_framework: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


class DotNetAnalyzer:
    """
    Analyze .NET projects in depth.

    Detects frameworks, target frameworks, NuGet packages, and provides
    specific recommendations for modernization.
    """

    FRAMEWORKS = {
        "asp.net-core": ["Microsoft.AspNetCore"],
        "asp.net-mvc": ["Microsoft.AspNet.Mvc"],
        "blazor": ["Microsoft.AspNetCore.Components"],
        "wpf": ["System.Windows"],
        "winforms": ["System.Windows.Forms"],
        "xamarin": ["Xamarin"],
        "maui": ["Microsoft.Maui"],
    }

    TESTING = {
        "xunit": ["xunit"],
        "nunit": ["NUnit"],
        "mstest": ["MSTest"],
        "moq": ["Moq"],
        "nsubstitute": ["NSubstitute"],
    }

    ORMS = {
        "entity-framework-core": ["Microsoft.EntityFrameworkCore"],
        "entity-framework": ["EntityFramework"],
        "dapper": ["Dapper"],
        "nhibernate": ["NHibernate"],
    }

    LOGGING = {
        "serilog": ["Serilog"],
        "nlog": ["NLog"],
        "log4net": ["log4net"],
    }

    def __init__(self, project_path: Path):
        """
        Initialize .NET analyzer.

        Args:
            project_path: Path to project root
        """
        self.project_path = Path(project_path)
        self.csproj_files = list(self.project_path.glob("*.csproj"))

    def analyze(self) -> DotNetAnalysis:
        """
        Perform comprehensive .NET analysis.

        Returns:
            DotNetAnalysis with detailed findings
        """
        analysis = DotNetAnalysis()

        if not self.csproj_files:
            return analysis

        # Analyze first .csproj file (or could analyze all)
        primary_csproj = self.csproj_files[0]
        self._analyze_csproj(primary_csproj, analysis)

        # Generate recommendations
        analysis.recommendations = self._generate_recommendations(analysis)

        return analysis

    def _analyze_csproj(self, csproj_path: Path, analysis: DotNetAnalysis) -> None:
        """Analyze .csproj file."""
        try:
            tree = ET.parse(csproj_path)
            root = tree.getroot()

            # Get target framework
            target_framework = self._get_target_framework(root)
            if target_framework:
                analysis.framework, analysis.dotnet_version = self._parse_target_framework(target_framework)
                analysis.framework_version = analysis.dotnet_version

            # Get project type from SDK or OutputType
            analysis.project_type = self._get_project_type(root)

            # Get package references
            packages = self._get_package_references(root)

            # Detect components
            analysis.web_framework = self._detect_web_framework(packages)
            analysis.testing_frameworks = self._detect_testing(packages)
            analysis.orm = self._detect_orm(packages)
            analysis.logging_framework = self._detect_logging(packages)
            analysis.api_framework = self._detect_api_framework(packages)

        except Exception:
            pass

    def _get_target_framework(self, root) -> Optional[str]:
        """Extract target framework from .csproj."""
        # <TargetFramework>
        for tf in root.findall(".//TargetFramework"):
            return tf.text

        # <TargetFrameworks> (multi-targeting)
        for tfs in root.findall(".//TargetFrameworks"):
            frameworks = tfs.text
            if frameworks:
                # Return first framework
                return frameworks.split(";")[0]

        return None

    def _parse_target_framework(self, target_framework: str) -> tuple[Optional[str], Optional[str]]:
        """Parse target framework moniker (TFM)."""
        # Examples: net8.0, net7.0, net6.0, netstandard2.1, netcoreapp3.1, net48

        # .NET 5+
        match = re.match(r"net(\d+)\.(\d+)", target_framework)
        if match:
            major = match.group(1)
            minor = match.group(2)
            return ".NET", f"{major}.{minor}"

        # .NET Core
        if "netcoreapp" in target_framework:
            match = re.search(r"(\d+)\.(\d+)", target_framework)
            if match:
                return ".NET Core", f"{match.group(1)}.{match.group(2)}"

        # .NET Standard
        if "netstandard" in target_framework:
            match = re.search(r"(\d+)\.(\d+)", target_framework)
            if match:
                return ".NET Standard", f"{match.group(1)}.{match.group(2)}"

        # .NET Framework
        if target_framework.startswith("net") and target_framework[3:].replace(".", "").isdigit():
            # net48, net472, net462, etc.
            version_str = target_framework[3:]
            if len(version_str) == 2:
                # net48 -> 4.8
                return ".NET Framework", f"{version_str[0]}.{version_str[1]}"
            elif len(version_str) == 3:
                # net472 -> 4.7.2
                return ".NET Framework", f"{version_str[0]}.{version_str[1]}.{version_str[2]}"

        return None, target_framework

    def _get_project_type(self, root) -> Optional[str]:
        """Determine project type."""
        # Check SDK attribute
        sdk = root.get("Sdk")
        if sdk:
            if "Microsoft.NET.Sdk.Web" in sdk:
                return "web"
            elif "Microsoft.NET.Sdk.Razor" in sdk:
                return "razor"
            elif "Microsoft.NET.Sdk.BlazorWebAssembly" in sdk:
                return "blazor-wasm"
            elif "Microsoft.NET.Sdk" in sdk:
                # Check OutputType
                for output_type in root.findall(".//OutputType"):
                    otype = output_type.text
                    if otype == "Exe":
                        return "console"
                    elif otype == "Library":
                        return "library"
                return "library"  # Default for SDK projects

        # Legacy .NET Framework projects
        # Check for Project element
        if root.tag == "Project":
            return "legacy"

        return None

    def _get_package_references(self, root) -> Dict[str, str]:
        """Extract NuGet package references."""
        packages = {}

        for pkg in root.findall(".//PackageReference"):
            include = pkg.get("Include")
            version = pkg.get("Version")

            if include:
                packages[include] = version if version else "unknown"

        return packages

    def _detect_web_framework(self, packages: Dict[str, str]) -> Optional[str]:
        """Detect web framework from packages."""
        for framework, indicators in self.FRAMEWORKS.items():
            for indicator in indicators:
                for pkg_name in packages.keys():
                    if indicator in pkg_name:
                        return framework
        return None

    def _detect_testing(self, packages: Dict[str, str]) -> List[str]:
        """Detect testing frameworks."""
        frameworks = []
        for framework, indicators in self.TESTING.items():
            for indicator in indicators:
                for pkg_name in packages.keys():
                    if indicator in pkg_name:
                        frameworks.append(framework)
                        break
        return list(set(frameworks))

    def _detect_orm(self, packages: Dict[str, str]) -> Optional[str]:
        """Detect ORM."""
        for orm, indicators in self.ORMS.items():
            for indicator in indicators:
                for pkg_name in packages.keys():
                    if indicator in pkg_name:
                        return orm
        return None

    def _detect_logging(self, packages: Dict[str, str]) -> Optional[str]:
        """Detect logging framework."""
        for framework, indicators in self.LOGGING.items():
            for indicator in indicators:
                for pkg_name in packages.keys():
                    if indicator in pkg_name:
                        return framework
        return None

    def _detect_api_framework(self, packages: Dict[str, str]) -> Optional[str]:
        """Detect API framework."""
        if "Swashbuckle.AspNetCore" in packages or "NSwag" in packages:
            return "OpenAPI/Swagger"
        if "Microsoft.AspNetCore.OData" in packages:
            return "OData"
        if "GraphQL" in packages or "HotChocolate" in packages:
            return "GraphQL"
        return None

    def _generate_recommendations(self, analysis: DotNetAnalysis) -> List[str]:
        """Generate modernization recommendations."""
        recommendations = []

        # .NET version recommendations
        if analysis.framework == ".NET Framework":
            recommendations.append(
                f"Migrate from .NET Framework {analysis.dotnet_version} to .NET 8 or .NET 9 "
                "(.NET Framework is in maintenance mode)"
            )

        elif analysis.framework == ".NET Core":
            recommendations.append(
                f"Upgrade from .NET Core {analysis.dotnet_version} to .NET 8 or .NET 9 "
                "(.NET Core is superseded by .NET 5+)"
            )

        elif analysis.framework == ".NET":
            try:
                major = int(analysis.dotnet_version.split(".")[0])
                if major < 6:
                    recommendations.append(
                        f"Upgrade from .NET {major} to .NET 8 LTS or .NET 9 (.NET {major} is EOL)"
                    )
                elif major == 6:
                    recommendations.append(
                        "Consider upgrading from .NET 6 LTS to .NET 8 LTS for latest features"
                    )
                elif major == 7:
                    recommendations.append(
                        "Upgrade from .NET 7 to .NET 8 LTS (.NET 7 is EOL)"
                    )
            except Exception:
                pass

        elif analysis.framework == ".NET Standard":
            recommendations.append(
                "Consider targeting .NET 8+ instead of .NET Standard for better performance"
            )

        # ORM recommendations
        if analysis.orm == "entity-framework":
            recommendations.append(
                "Migrate from Entity Framework to Entity Framework Core for modern .NET"
            )

        if not analysis.orm and analysis.project_type in ["web", "console"]:
            recommendations.append(
                "Consider adding Entity Framework Core for database operations"
            )

        # Testing recommendations
        if not analysis.testing_frameworks:
            recommendations.append("Add testing framework (xUnit recommended for .NET)")

        # Web framework recommendations
        if analysis.web_framework == "asp.net-mvc":
            recommendations.append(
                "Migrate from ASP.NET MVC to ASP.NET Core for modern web development"
            )

        # Logging recommendations
        if not analysis.logging_framework:
            recommendations.append(
                "Add structured logging (Serilog recommended)"
            )

        # API recommendations
        if analysis.project_type == "web" and not analysis.api_framework:
            recommendations.append(
                "Consider adding OpenAPI/Swagger for API documentation"
            )

        return recommendations


def main():
    """Example usage of DotNetAnalyzer."""
    import sys

    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path.cwd()

    print(f"Analyzing .NET project: {project_path}\n")

    analyzer = DotNetAnalyzer(project_path)
    analysis = analyzer.analyze()

    print("=== .NET Analysis ===")
    print(f"Framework: {analysis.framework or 'None detected'}")
    print(f"Version: {analysis.dotnet_version or 'Not specified'}")
    print(f"Project Type: {analysis.project_type or 'Unknown'}")
    print(f"Web Framework: {analysis.web_framework or 'None'}")
    print(f"Testing: {', '.join(analysis.testing_frameworks) if analysis.testing_frameworks else 'None'}")
    print(f"ORM: {analysis.orm or 'None'}")
    print(f"Logging: {analysis.logging_framework or 'None'}")
    print(f"API Framework: {analysis.api_framework or 'None'}")

    if analysis.recommendations:
        print("\n=== Recommendations ===")
        for i, rec in enumerate(analysis.recommendations, 1):
            print(f"{i}. {rec}")


if __name__ == "__main__":
    main()
