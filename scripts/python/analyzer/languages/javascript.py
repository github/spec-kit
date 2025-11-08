"""
JavaScript/Node.js specific analyzer.

Deep analysis for JavaScript and TypeScript projects including framework
detection, build tool analysis, and Node.js version management.
"""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class JavaScriptAnalysis:
    """Container for JavaScript-specific analysis results."""

    framework: Optional[str] = None
    framework_version: Optional[str] = None
    build_tool: Optional[str] = None
    package_manager: str = "npm"
    node_version: Optional[str] = None
    node_version_source: Optional[str] = None
    typescript: bool = False
    typescript_version: Optional[str] = None
    linting: List[str] = field(default_factory=list)
    testing_frameworks: List[str] = field(default_factory=list)
    bundler: Optional[str] = None
    ui_library: Optional[str] = None
    state_management: Optional[str] = None
    css_framework: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


class JavaScriptAnalyzer:
    """
    Analyze JavaScript/Node.js projects in depth.

    Detects frameworks, build tools, package managers, versions, and provides
    specific recommendations for modernization.
    """

    FRAMEWORKS = {
        "react": ["react", "@types/react"],
        "vue": ["vue", "@vue/cli"],
        "angular": ["@angular/core"],
        "svelte": ["svelte"],
        "next.js": ["next"],
        "nuxt": ["nuxt"],
        "gatsby": ["gatsby"],
        "express": ["express"],
        "nestjs": ["@nestjs/core"],
        "fastify": ["fastify"],
        "koa": ["koa"],
        "hapi": ["@hapi/hapi"],
    }

    BUILD_TOOLS = {
        "webpack": ["webpack"],
        "vite": ["vite"],
        "rollup": ["rollup"],
        "esbuild": ["esbuild"],
        "parcel": ["parcel"],
        "turbopack": ["turbopack"],
    }

    LINTERS = {
        "eslint": ["eslint"],
        "prettier": ["prettier"],
        "tslint": ["tslint"],  # Deprecated
    }

    TESTING = {
        "jest": ["jest"],
        "mocha": ["mocha"],
        "jasmine": ["jasmine"],
        "vitest": ["vitest"],
        "cypress": ["cypress"],
        "playwright": ["@playwright/test"],
        "testing-library": ["@testing-library/react", "@testing-library/vue"],
    }

    UI_LIBRARIES = {
        "material-ui": ["@mui/material", "@material-ui/core"],
        "ant-design": ["antd"],
        "chakra-ui": ["@chakra-ui/react"],
        "tailwind": ["tailwindcss"],
        "bootstrap": ["bootstrap", "react-bootstrap"],
        "semantic-ui": ["semantic-ui-react"],
    }

    STATE_MANAGEMENT = {
        "redux": ["redux", "@reduxjs/toolkit"],
        "mobx": ["mobx"],
        "zustand": ["zustand"],
        "recoil": ["recoil"],
        "jotai": ["jotai"],
        "vuex": ["vuex"],
        "pinia": ["pinia"],
    }

    def __init__(self, project_path: Path):
        """
        Initialize JavaScript analyzer.

        Args:
            project_path: Path to project root
        """
        self.project_path = Path(project_path)
        self.package_json_path = self.project_path / "package.json"
        self.package_json: Optional[Dict] = None

    def analyze(self) -> JavaScriptAnalysis:
        """
        Perform comprehensive JavaScript/Node.js analysis.

        Returns:
            JavaScriptAnalysis with detailed findings
        """
        if not self.package_json_path.exists():
            return JavaScriptAnalysis()

        # Load package.json
        try:
            with open(self.package_json_path, "r") as f:
                self.package_json = json.load(f)
        except Exception:
            return JavaScriptAnalysis()

        analysis = JavaScriptAnalysis()

        # Get all dependencies
        all_deps = self._get_all_dependencies()

        # Detect components
        analysis.framework, analysis.framework_version = self._detect_framework(all_deps)
        analysis.build_tool = self._detect_build_tool(all_deps)
        analysis.package_manager = self._detect_package_manager()
        analysis.node_version, analysis.node_version_source = self._detect_node_version()
        analysis.typescript = self._detect_typescript(all_deps)
        analysis.typescript_version = self._get_dependency_version(all_deps, "typescript")
        analysis.linting = self._detect_linting(all_deps)
        analysis.testing_frameworks = self._detect_testing(all_deps)
        analysis.bundler = self._detect_bundler(all_deps)
        analysis.ui_library = self._detect_ui_library(all_deps)
        analysis.state_management = self._detect_state_management(all_deps)
        analysis.css_framework = self._detect_css_framework(all_deps)

        # Generate recommendations
        analysis.recommendations = self._generate_recommendations(analysis, all_deps)

        return analysis

    def _get_all_dependencies(self) -> Dict[str, str]:
        """Get all dependencies (production + dev)."""
        if not self.package_json:
            return {}

        deps = {}
        deps.update(self.package_json.get("dependencies", {}))
        deps.update(self.package_json.get("devDependencies", {}))
        return deps

    def _detect_framework(self, deps: Dict[str, str]) -> tuple[Optional[str], Optional[str]]:
        """Detect JavaScript framework."""
        for framework, indicators in self.FRAMEWORKS.items():
            for indicator in indicators:
                if indicator in deps:
                    version = deps.get(indicator, "unknown")
                    return framework, version
        return None, None

    def _detect_build_tool(self, deps: Dict[str, str]) -> Optional[str]:
        """Detect build tool."""
        for tool, indicators in self.BUILD_TOOLS.items():
            for indicator in indicators:
                if indicator in deps:
                    return tool
        return None

    def _detect_package_manager(self) -> str:
        """Detect package manager from lock files."""
        if (self.project_path / "pnpm-lock.yaml").exists():
            return "pnpm"
        elif (self.project_path / "yarn.lock").exists():
            return "yarn"
        elif (self.project_path / "package-lock.json").exists():
            return "npm"
        elif (self.project_path / "bun.lockb").exists():
            return "bun"
        return "npm"  # Default

    def _detect_node_version(self) -> tuple[Optional[str], Optional[str]]:
        """Detect Node.js version from various sources."""
        # Check .nvmrc
        nvmrc = self.project_path / ".nvmrc"
        if nvmrc.exists():
            try:
                version = nvmrc.read_text().strip()
                return version, ".nvmrc"
            except Exception:
                pass

        # Check .node-version
        node_version_file = self.project_path / ".node-version"
        if node_version_file.exists():
            try:
                version = node_version_file.read_text().strip()
                return version, ".node-version"
            except Exception:
                pass

        # Check package.json engines
        if self.package_json:
            engines = self.package_json.get("engines", {})
            node_version = engines.get("node")
            if node_version:
                return node_version, "package.json engines"

        return None, None

    def _detect_typescript(self, deps: Dict[str, str]) -> bool:
        """Check if TypeScript is used."""
        return "typescript" in deps or (self.project_path / "tsconfig.json").exists()

    def _get_dependency_version(self, deps: Dict[str, str], package: str) -> Optional[str]:
        """Get version of a specific dependency."""
        return deps.get(package)

    def _detect_linting(self, deps: Dict[str, str]) -> List[str]:
        """Detect linting tools."""
        linters = []
        for linter, indicators in self.LINTERS.items():
            for indicator in indicators:
                if indicator in deps:
                    linters.append(linter)
                    break
        return linters

    def _detect_testing(self, deps: Dict[str, str]) -> List[str]:
        """Detect testing frameworks."""
        frameworks = []
        for framework, indicators in self.TESTING.items():
            for indicator in indicators:
                if indicator in deps:
                    frameworks.append(framework)
                    break
        return frameworks

    def _detect_bundler(self, deps: Dict[str, str]) -> Optional[str]:
        """Detect bundler (alias for build_tool)."""
        return self._detect_build_tool(deps)

    def _detect_ui_library(self, deps: Dict[str, str]) -> Optional[str]:
        """Detect UI component library."""
        for library, indicators in self.UI_LIBRARIES.items():
            for indicator in indicators:
                if indicator in deps:
                    return library
        return None

    def _detect_state_management(self, deps: Dict[str, str]) -> Optional[str]:
        """Detect state management library."""
        for library, indicators in self.STATE_MANAGEMENT.items():
            for indicator in indicators:
                if indicator in deps:
                    return library
        return None

    def _detect_css_framework(self, deps: Dict[str, str]) -> Optional[str]:
        """Detect CSS framework."""
        css_frameworks = {
            "tailwindcss": ["tailwindcss"],
            "sass": ["sass", "node-sass"],
            "less": ["less"],
            "styled-components": ["styled-components"],
            "emotion": ["@emotion/react"],
            "css-modules": [],  # Detected differently
        }

        for framework, indicators in css_frameworks.items():
            for indicator in indicators:
                if indicator in deps:
                    return framework

        # Check for CSS modules in package.json scripts
        if self.package_json:
            scripts = self.package_json.get("scripts", {})
            for script in scripts.values():
                if "css-modules" in script or "modules.css" in script:
                    return "css-modules"

        return None

    def _generate_recommendations(self, analysis: JavaScriptAnalysis, deps: Dict[str, str]) -> List[str]:
        """Generate modernization recommendations."""
        recommendations = []

        # Node.js version recommendations
        if analysis.node_version:
            try:
                # Extract major version
                version_str = analysis.node_version.replace("v", "").replace("^", "").replace("~", "")
                major_version = int(version_str.split(".")[0]) if version_str[0].isdigit() else None

                if major_version and major_version < 18:
                    recommendations.append(
                        f"Upgrade Node.js from v{major_version} to v18 LTS or v20 LTS"
                    )
            except Exception:
                pass

        # TypeScript recommendations
        if not analysis.typescript:
            recommendations.append("Consider migrating to TypeScript for better type safety")
        elif analysis.typescript_version:
            try:
                ts_major = int(analysis.typescript_version.replace("^", "").replace("~", "").split(".")[0])
                if ts_major < 5:
                    recommendations.append(f"Upgrade TypeScript from v{ts_major} to v5.x")
            except Exception:
                pass

        # Linting recommendations
        if "tslint" in analysis.linting:
            recommendations.append("Migrate from TSLint (deprecated) to ESLint")

        if not analysis.linting:
            recommendations.append("Add ESLint for code quality enforcement")

        if "prettier" not in analysis.linting:
            recommendations.append("Add Prettier for consistent code formatting")

        # Testing recommendations
        if not analysis.testing_frameworks:
            recommendations.append("Add testing framework (Jest or Vitest recommended)")

        # Build tool recommendations
        if analysis.build_tool == "webpack":
            recommendations.append("Consider migrating from Webpack to Vite for faster dev experience")

        if not analysis.build_tool:
            recommendations.append("Add build tool (Vite recommended for modern projects)")

        # Framework-specific recommendations
        if analysis.framework == "react":
            if analysis.framework_version:
                try:
                    react_major = int(analysis.framework_version.replace("^", "").replace("~", "").split(".")[0])
                    if react_major < 18:
                        recommendations.append(f"Upgrade React from v{react_major} to v18 for concurrent features")
                except Exception:
                    pass

            if not analysis.state_management:
                recommendations.append("Consider adding state management (Zustand or Redux Toolkit)")

        # Package manager recommendations
        if analysis.package_manager == "npm":
            recommendations.append("Consider migrating to pnpm for faster installs and better disk usage")

        return recommendations


def main():
    """Example usage of JavaScriptAnalyzer."""
    import sys

    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path.cwd()

    print(f"Analyzing JavaScript project: {project_path}\n")

    analyzer = JavaScriptAnalyzer(project_path)
    analysis = analyzer.analyze()

    print("=== JavaScript/Node.js Analysis ===")
    print(f"Framework: {analysis.framework or 'None detected'}")
    if analysis.framework_version:
        print(f"Framework Version: {analysis.framework_version}")
    print(f"Build Tool: {analysis.build_tool or 'None'}")
    print(f"Package Manager: {analysis.package_manager}")
    print(f"Node.js Version: {analysis.node_version or 'Not specified'}")
    if analysis.node_version_source:
        print(f"  Source: {analysis.node_version_source}")
    print(f"TypeScript: {analysis.typescript}")
    if analysis.typescript_version:
        print(f"  Version: {analysis.typescript_version}")
    print(f"Linting: {', '.join(analysis.linting) if analysis.linting else 'None'}")
    print(f"Testing: {', '.join(analysis.testing_frameworks) if analysis.testing_frameworks else 'None'}")
    print(f"UI Library: {analysis.ui_library or 'None'}")
    print(f"State Management: {analysis.state_management or 'None'}")
    print(f"CSS Framework: {analysis.css_framework or 'None'}")

    if analysis.recommendations:
        print("\n=== Recommendations ===")
        for i, rec in enumerate(analysis.recommendations, 1):
            print(f"{i}. {rec}")


if __name__ == "__main__":
    main()
