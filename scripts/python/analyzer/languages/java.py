"""
Java specific analyzer.

Deep analysis for Java projects including framework detection,
build tool analysis, and dependency management.
"""

import re
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class JavaAnalysis:
    """Container for Java-specific analysis results."""

    framework: Optional[str] = None
    framework_version: Optional[str] = None
    java_version: Optional[str] = None
    java_version_source: Optional[str] = None
    build_tool: Optional[str] = None
    dependency_management: Optional[str] = None
    testing_frameworks: List[str] = field(default_factory=list)
    logging_framework: Optional[str] = None
    orm: Optional[str] = None
    web_server: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


class JavaAnalyzer:
    """
    Analyze Java projects in depth.

    Detects frameworks, build tools, Java version, and provides
    specific recommendations for modernization.
    """

    FRAMEWORKS = {
        "spring-boot": ["org.springframework.boot"],
        "spring": ["org.springframework"],
        "quarkus": ["io.quarkus"],
        "micronaut": ["io.micronaut"],
        "jakarta-ee": ["jakarta.servlet", "jakarta.persistence"],
        "java-ee": ["javax.servlet", "javax.persistence"],
        "dropwizard": ["io.dropwizard"],
        "vert.x": ["io.vertx"],
    }

    TESTING = {
        "junit5": ["org.junit.jupiter"],
        "junit4": ["junit:junit"],
        "testng": ["org.testng"],
        "mockito": ["org.mockito"],
        "assertj": ["org.assertj"],
        "rest-assured": ["io.rest-assured"],
    }

    LOGGING = {
        "slf4j": ["org.slf4j"],
        "logback": ["ch.qos.logback"],
        "log4j2": ["org.apache.logging.log4j"],
        "log4j": ["log4j:log4j"],  # Deprecated/vulnerable
    }

    ORMS = {
        "hibernate": ["org.hibernate"],
        "jpa": ["javax.persistence", "jakarta.persistence"],
        "mybatis": ["org.mybatis"],
        "jooq": ["org.jooq"],
        "eclipselink": ["org.eclipse.persistence"],
    }

    def __init__(self, project_path: Path):
        """
        Initialize Java analyzer.

        Args:
            project_path: Path to project root
        """
        self.project_path = Path(project_path)
        self.pom_xml_path = self.project_path / "pom.xml"
        self.build_gradle_path = self.project_path / "build.gradle"
        self.build_gradle_kts_path = self.project_path / "build.gradle.kts"

    def analyze(self) -> JavaAnalysis:
        """
        Perform comprehensive Java analysis.

        Returns:
            JavaAnalysis with detailed findings
        """
        analysis = JavaAnalysis()

        # Detect build tool
        if self.pom_xml_path.exists():
            analysis.build_tool = "maven"
            self._analyze_maven(analysis)
        elif self.build_gradle_path.exists() or self.build_gradle_kts_path.exists():
            analysis.build_tool = "gradle"
            self._analyze_gradle(analysis)

        # Generate recommendations
        if analysis.build_tool:
            analysis.recommendations = self._generate_recommendations(analysis)

        return analysis

    def _analyze_maven(self, analysis: JavaAnalysis) -> None:
        """Analyze Maven project (pom.xml)."""
        try:
            tree = ET.parse(self.pom_xml_path)
            root = tree.getroot()

            # Define namespace
            ns = {"mvn": "http://maven.apache.org/POM/4.0.0"}
            if not root.tag.startswith("{"):
                ns = {}  # No namespace

            # Get Java version
            java_version = self._get_maven_java_version(root, ns)
            if java_version:
                analysis.java_version = java_version
                analysis.java_version_source = "pom.xml"

            # Get dependencies
            dependencies = self._get_maven_dependencies(root, ns)

            # Detect components
            analysis.framework, analysis.framework_version = self._detect_framework_from_deps(dependencies)
            analysis.testing_frameworks = self._detect_testing_from_deps(dependencies)
            analysis.logging_framework = self._detect_logging_from_deps(dependencies)
            analysis.orm = self._detect_orm_from_deps(dependencies)

            # Dependency management
            analysis.dependency_management = "maven"

        except Exception as e:
            # Failed to parse pom.xml
            pass

    def _analyze_gradle(self, analysis: JavaAnalysis) -> None:
        """Analyze Gradle project."""
        gradle_file = self.build_gradle_kts_path if self.build_gradle_kts_path.exists() else self.build_gradle_path

        try:
            with open(gradle_file, "r") as f:
                content = f.read()

            # Get Java version
            java_version = self._get_gradle_java_version(content)
            if java_version:
                analysis.java_version = java_version
                analysis.java_version_source = gradle_file.name

            # Get dependencies (simple string matching)
            dependencies = self._get_gradle_dependencies(content)

            # Detect components
            analysis.framework, analysis.framework_version = self._detect_framework_from_deps(dependencies)
            analysis.testing_frameworks = self._detect_testing_from_deps(dependencies)
            analysis.logging_framework = self._detect_logging_from_deps(dependencies)
            analysis.orm = self._detect_orm_from_deps(dependencies)

            # Dependency management
            analysis.dependency_management = "gradle"

        except Exception:
            pass

    def _get_maven_java_version(self, root, ns: Dict) -> Optional[str]:
        """Extract Java version from pom.xml."""
        # Try maven.compiler.source
        for prop in root.findall(".//mvn:properties/mvn:maven.compiler.source", ns):
            return prop.text

        # Try maven.compiler.target
        for prop in root.findall(".//mvn:properties/mvn:maven.compiler.target", ns):
            return prop.text

        # Try java.version
        for prop in root.findall(".//mvn:properties/mvn:java.version", ns):
            return prop.text

        # Try source in compiler plugin
        for config in root.findall(".//mvn:plugin[mvn:artifactId='maven-compiler-plugin']/mvn:configuration/mvn:source", ns):
            return config.text

        return None

    def _get_maven_dependencies(self, root, ns: Dict) -> Dict[str, str]:
        """Extract dependencies from pom.xml."""
        deps = {}

        for dep in root.findall(".//mvn:dependency", ns):
            group_id_elem = dep.find("mvn:groupId", ns)
            artifact_id_elem = dep.find("mvn:artifactId", ns)
            version_elem = dep.find("mvn:version", ns)

            if group_id_elem is not None and artifact_id_elem is not None:
                group_id = group_id_elem.text
                artifact_id = artifact_id_elem.text
                version = version_elem.text if version_elem is not None else "unknown"

                # Store as "groupId:artifactId"
                key = f"{group_id}:{artifact_id}" if group_id and artifact_id else None
                if key:
                    deps[key] = version

                # Also store just groupId for framework detection
                if group_id:
                    deps[group_id] = version

        return deps

    def _get_gradle_java_version(self, content: str) -> Optional[str]:
        """Extract Java version from Gradle file."""
        # sourceCompatibility
        match = re.search(r'sourceCompatibility\s*=\s*["\']?(\d+(?:\.\d+)?)["\']?', content)
        if match:
            return match.group(1)

        # targetCompatibility
        match = re.search(r'targetCompatibility\s*=\s*["\']?(\d+(?:\.\d+)?)["\']?', content)
        if match:
            return match.group(1)

        # JavaVersion enum
        match = re.search(r'JavaVersion\.VERSION_(\d+)', content)
        if match:
            return match.group(1)

        return None

    def _get_gradle_dependencies(self, content: str) -> Dict[str, str]:
        """Extract dependencies from Gradle file (simple string matching)."""
        deps = {}

        # Match implementation/compile/testImplementation lines
        for match in re.finditer(r'["\']([a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+):([^"\']+)["\']', content):
            group_artifact = match.group(1)
            version = match.group(2)
            deps[group_artifact] = version

            # Also store just the group
            group = group_artifact.split(":")[0]
            deps[group] = version

        return deps

    def _detect_framework_from_deps(self, deps: Dict[str, str]) -> tuple[Optional[str], Optional[str]]:
        """Detect Java framework from dependencies."""
        for framework, indicators in self.FRAMEWORKS.items():
            for indicator in indicators:
                for dep_key in deps.keys():
                    if indicator in dep_key:
                        version = deps.get(dep_key, "unknown")
                        return framework, version
        return None, None

    def _detect_testing_from_deps(self, deps: Dict[str, str]) -> List[str]:
        """Detect testing frameworks."""
        frameworks = []
        for framework, indicators in self.TESTING.items():
            for indicator in indicators:
                for dep_key in deps.keys():
                    if indicator in dep_key:
                        frameworks.append(framework)
                        break
        return list(set(frameworks))

    def _detect_logging_from_deps(self, deps: Dict[str, str]) -> Optional[str]:
        """Detect logging framework."""
        for framework, indicators in self.LOGGING.items():
            for indicator in indicators:
                for dep_key in deps.keys():
                    if indicator in dep_key:
                        return framework
        return None

    def _detect_orm_from_deps(self, deps: Dict[str, str]) -> Optional[str]:
        """Detect ORM."""
        for orm, indicators in self.ORMS.items():
            for indicator in indicators:
                for dep_key in deps.keys():
                    if indicator in dep_key:
                        return orm
        return None

    def _generate_recommendations(self, analysis: JavaAnalysis) -> List[str]:
        """Generate modernization recommendations."""
        recommendations = []

        # Java version recommendations
        if analysis.java_version:
            try:
                java_major = int(analysis.java_version.split(".")[0])

                if java_major < 11:
                    recommendations.append(
                        f"Upgrade Java from {java_major} to Java 17 LTS or Java 21 LTS (Java {java_major} is EOL)"
                    )
                elif java_major == 11:
                    recommendations.append(
                        "Consider upgrading from Java 11 LTS to Java 17 LTS or Java 21 LTS for better performance"
                    )
                elif java_major < 17:
                    recommendations.append(
                        f"Upgrade Java from {java_major} to Java 17 LTS or Java 21 LTS"
                    )
            except Exception:
                pass

        # Framework recommendations
        if analysis.framework == "spring":
            recommendations.append("Consider migrating to Spring Boot for modern Spring development")

        elif analysis.framework == "spring-boot":
            if analysis.framework_version:
                try:
                    version_match = re.match(r"(\d+)\.(\d+)", analysis.framework_version)
                    if version_match:
                        major = int(version_match.group(1))
                        if major < 3:
                            recommendations.append(
                                f"Upgrade Spring Boot from {major}.x to 3.x for Java 17+ support and modern features"
                            )
                except Exception:
                    pass

        elif analysis.framework == "java-ee":
            recommendations.append("Migrate from Java EE to Jakarta EE (Java EE is deprecated)")

        # Logging recommendations
        if analysis.logging_framework == "log4j":
            recommendations.append(
                "CRITICAL: Migrate from Log4j 1.x to Log4j 2 or Logback (Log4j 1.x has severe vulnerabilities)"
            )

        if not analysis.logging_framework:
            recommendations.append("Add logging framework (SLF4J + Logback recommended)")

        # Testing recommendations
        if not analysis.testing_frameworks:
            recommendations.append("Add testing framework (JUnit 5 + Mockito recommended)")

        if "junit4" in analysis.testing_frameworks and "junit5" not in analysis.testing_frameworks:
            recommendations.append("Migrate from JUnit 4 to JUnit 5 for modern testing features")

        # Build tool recommendations
        if analysis.build_tool == "maven":
            recommendations.append("Consider Gradle for faster builds (optional)")

        # ORM recommendations
        if not analysis.orm and analysis.framework in ["spring-boot", "spring"]:
            recommendations.append("Consider adding Spring Data JPA for database operations")

        return recommendations


def main():
    """Example usage of JavaAnalyzer."""
    import sys

    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path.cwd()

    print(f"Analyzing Java project: {project_path}\n")

    analyzer = JavaAnalyzer(project_path)
    analysis = analyzer.analyze()

    print("=== Java Analysis ===")
    print(f"Build Tool: {analysis.build_tool or 'None detected'}")
    print(f"Framework: {analysis.framework or 'None detected'}")
    if analysis.framework_version:
        print(f"Framework Version: {analysis.framework_version}")
    print(f"Java Version: {analysis.java_version or 'Not specified'}")
    if analysis.java_version_source:
        print(f"  Source: {analysis.java_version_source}")
    print(f"Dependency Management: {analysis.dependency_management or 'None'}")
    print(f"Testing: {', '.join(analysis.testing_frameworks) if analysis.testing_frameworks else 'None'}")
    print(f"Logging: {analysis.logging_framework or 'None'}")
    print(f"ORM: {analysis.orm or 'None'}")

    if analysis.recommendations:
        print("\n=== Recommendations ===")
        for i, rec in enumerate(analysis.recommendations, 1):
            print(f"{i}. {rec}")


if __name__ == "__main__":
    main()
