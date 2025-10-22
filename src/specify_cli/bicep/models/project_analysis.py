"""Project analysis data model.

This module defines the data structures for representing project analysis results
and Azure service recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import json


class ProjectType(Enum):
    """Types of projects that can be analyzed."""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    MICROSERVICE = "microservice"
    DATA_APPLICATION = "data_application"
    CONTAINER_APPLICATION = "container_application"
    STATIC_WEBSITE = "static_website"
    FUNCTION_APP = "function_app"
    DESKTOP_APPLICATION = "desktop_application"
    MOBILE_BACKEND = "mobile_backend"
    IOT_APPLICATION = "iot_application"
    MACHINE_LEARNING = "machine_learning"
    UNKNOWN = "unknown"


class FrameworkType(Enum):
    """Supported application frameworks."""
    # Web Frameworks
    ASPNET_CORE = "aspnet_core"
    EXPRESS_JS = "express_js"
    FASTAPI = "fastapi"
    DJANGO = "django"
    FLASK = "flask"
    SPRING_BOOT = "spring_boot"
    LARAVEL = "laravel"
    RUBY_ON_RAILS = "ruby_on_rails"
    
    # Frontend Frameworks
    REACT = "react"
    ANGULAR = "angular"
    VUE_JS = "vue_js"
    NEXT_JS = "next_js"
    NUXT_JS = "nuxt_js"
    BLAZOR = "blazor"
    
    # Mobile Frameworks
    XAMARIN = "xamarin"
    REACT_NATIVE = "react_native"
    FLUTTER = "flutter"
    
    # Other
    ELECTRON = "electron"
    UNKNOWN = "unknown"


class ConfidenceLevel(Enum):
    """Confidence levels for analysis results."""
    VERY_HIGH = "very_high"  # 90-100%
    HIGH = "high"           # 75-89%
    MEDIUM = "medium"       # 50-74%
    LOW = "low"            # 25-49%
    VERY_LOW = "very_low"  # 0-24%


@dataclass
class FileAnalysisResult:
    """Analysis result for a single file."""
    file_path: Path
    file_type: str
    size_bytes: int
    last_modified: datetime
    detected_frameworks: Set[FrameworkType] = field(default_factory=set)
    detected_languages: Set[str] = field(default_factory=set)
    azure_service_indicators: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    confidence_score: float = 0.0
    analysis_notes: List[str] = field(default_factory=list)


@dataclass
class ServiceIndicator:
    """Indicator for an Azure service requirement."""
    service_type: str
    confidence: float
    evidence: List[str]
    file_sources: List[Path]
    recommended_tier: Optional[str] = None
    estimated_monthly_cost: Optional[str] = None


@dataclass
class ProjectStructureAnalysis:
    """Analysis of project structure and organization."""
    total_files: int
    analyzed_files: int
    project_size_mb: float
    directory_structure: Dict[str, int]  # directory -> file count
    main_languages: List[str]
    detected_frameworks: Set[FrameworkType]
    build_systems: Set[str]  # npm, maven, msbuild, etc.
    configuration_files: List[Path]
    documentation_files: List[Path]
    test_directories: List[Path]


@dataclass
class SecurityAnalysis:
    """Security-related analysis results."""
    secrets_detected: List[str]  # Types of secrets found
    security_vulnerabilities: List[str]
    compliance_issues: List[str]
    recommended_security_services: List[str]
    security_score: float  # 0-100


@dataclass
class PerformanceAnalysis:
    """Performance-related analysis results."""
    estimated_traffic_patterns: Dict[str, Any]
    scalability_requirements: List[str]
    performance_bottlenecks: List[str]
    recommended_performance_services: List[str]
    performance_score: float  # 0-100


@dataclass
class CostEstimation:
    """Cost estimation for the project."""
    monthly_estimate_usd: float
    cost_breakdown: Dict[str, float]  # service -> cost
    cost_optimization_suggestions: List[str]
    pricing_tier_recommendations: Dict[str, str]  # service -> tier


@dataclass
class ProjectAnalysisResult:
    """Complete analysis result for a project."""
    # Basic Information
    project_path: Path
    project_name: str
    analysis_timestamp: datetime
    analysis_duration_seconds: float
    
    # Project Classification
    project_type: ProjectType
    primary_framework: FrameworkType
    confidence_level: ConfidenceLevel
    
    # File Analysis
    file_analysis: List[FileAnalysisResult]
    structure_analysis: ProjectStructureAnalysis
    
    # Service Requirements
    detected_services: Dict[str, ServiceIndicator]  # service_type -> indicator
    recommended_services: List[str]
    service_dependencies: Dict[str, List[str]]  # service -> dependencies
    
    # Specialized Analysis
    security_analysis: SecurityAnalysis
    performance_analysis: PerformanceAnalysis
    cost_estimation: CostEstimation
    
    # Metadata
    analysis_version: str = "1.0.0"
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        def convert_enum(obj):
            if isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, set):
                return list(obj)
            elif isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        # Custom serialization logic
        result = {}
        for key, value in self.__dict__.items():
            if hasattr(value, '__dict__'):
                # Handle dataclass objects
                result[key] = {k: convert_enum(v) for k, v in value.__dict__.items()}
            elif isinstance(value, (list, tuple)):
                result[key] = [convert_enum(item) for item in value]
            elif isinstance(value, dict):
                result[key] = {k: convert_enum(v) for k, v in value.items()}
            else:
                result[key] = convert_enum(value)
        
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectAnalysisResult':
        """Create from dictionary (for deserialization)."""
        # This would need custom logic to reconstruct enums and dataclasses
        # Implementation depends on specific serialization needs
        raise NotImplementedError("Deserialization not yet implemented")
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the analysis."""
        return f"""
Project Analysis Summary
========================
Project: {self.project_name}
Type: {self.project_type.value}
Framework: {self.primary_framework.value}
Confidence: {self.confidence_level.value}

Files Analyzed: {len(self.file_analysis)}/{self.structure_analysis.total_files}
Detected Services: {len(self.detected_services)}
Recommended Services: {len(self.recommended_services)}

Estimated Monthly Cost: ${self.cost_estimation.monthly_estimate_usd:.2f}
Security Score: {self.security_analysis.security_score:.1f}/100
Performance Score: {self.performance_analysis.performance_score:.1f}/100

Analysis completed in {self.analysis_duration_seconds:.2f} seconds
"""
    
    def get_service_summary(self) -> List[str]:
        """Get a list of recommended services with confidence levels."""
        services = []
        for service_type, indicator in self.detected_services.items():
            confidence_pct = int(indicator.confidence * 100)
            services.append(f"{service_type} ({confidence_pct}% confidence)")
        return services
    
    def has_critical_issues(self) -> bool:
        """Check if there are critical issues that need attention."""
        return (
            len(self.errors) > 0 or 
            self.security_analysis.security_score < 50 or
            len(self.security_analysis.secrets_detected) > 0
        )
    
    def get_deployment_complexity(self) -> str:
        """Estimate deployment complexity based on services and dependencies."""
        service_count = len(self.detected_services)
        dependency_count = sum(len(deps) for deps in self.service_dependencies.values())
        
        complexity_score = service_count + (dependency_count * 0.5)
        
        if complexity_score <= 3:
            return "Simple"
        elif complexity_score <= 8:
            return "Moderate" 
        elif complexity_score <= 15:
            return "Complex"
        else:
            return "Enterprise"
    
    def get_recommended_resource_groups(self) -> List[str]:
        """Get recommended resource group organization."""
        complexity = self.get_deployment_complexity()
        
        if complexity == "Simple":
            return ["rg-{project}-{environment}"]
        elif complexity == "Moderate":
            return [
                "rg-{project}-app-{environment}",
                "rg-{project}-data-{environment}"
            ]
        else:
            return [
                "rg-{project}-app-{environment}",
                "rg-{project}-data-{environment}",
                "rg-{project}-network-{environment}",
                "rg-{project}-security-{environment}"
            ]