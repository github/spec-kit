"""Project analysis utility for Azure service requirements detection.

This module analyzes project structure and code to recommend
appropriate Azure services and Bicep templates.
"""

import logging
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from ..utils.file_scanner import ProjectFileScanner, ProjectAnalysisResult, FileAnalysis

logger = logging.getLogger(__name__)


class ServicePriority(Enum):
    """Priority levels for service recommendations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"
    OPTIONAL = "optional"


class DeploymentComplexity(Enum):
    """Complexity levels for deployments."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


@dataclass
class ServiceRecommendation:
    """Recommendation for an Azure service."""
    service_type: str
    service_name: str
    priority: ServicePriority
    confidence: float
    reasons: List[str]
    dependencies: List[str] = field(default_factory=list)
    estimated_cost: Optional[str] = None
    deployment_notes: List[str] = field(default_factory=list)


@dataclass
class ProjectRecommendations:
    """Complete project analysis and recommendations."""
    project_path: Path
    project_type: str
    deployment_complexity: DeploymentComplexity
    recommended_services: List[ServiceRecommendation]
    resource_groups: List[str]
    estimated_resources: int
    deployment_order: List[str]
    warnings: List[str] = field(default_factory=list)
    analysis_confidence: float = 0.0


class ProjectAnalyzer:
    """Analyzes projects to recommend Azure services and deployment strategies."""
    
    # Service dependency mapping
    SERVICE_DEPENDENCIES = {
        'Microsoft.Web/sites': ['Microsoft.Web/serverfarms'],
        'Microsoft.Sql/databases': ['Microsoft.Sql/servers'],
        'Microsoft.Storage/storageAccounts': [],
        'Microsoft.KeyVault/vaults': [],
        'Microsoft.Insights/components': [],
        'Microsoft.ContainerRegistry/registries': [],
        'Microsoft.ContainerInstance/containerGroups': ['Microsoft.ContainerRegistry/registries'],
        'Microsoft.Network/virtualNetworks': [],
        'Microsoft.Network/loadBalancers': ['Microsoft.Network/virtualNetworks'],
    }
    
    # Cost estimates (USD per month for basic tiers)
    COST_ESTIMATES = {
        'Microsoft.Web/sites': '$10-50',
        'Microsoft.Web/serverfarms': '$10-50',
        'Microsoft.Sql/servers': '$5-500', 
        'Microsoft.Sql/databases': '$5-500',
        'Microsoft.Storage/storageAccounts': '$1-20',
        'Microsoft.KeyVault/vaults': '$0-10',
        'Microsoft.Insights/components': '$0-50',
        'Microsoft.ContainerRegistry/registries': '$5-20',
        'Microsoft.ContainerInstance/containerGroups': '$10-100',
        'Microsoft.Network/virtualNetworks': 'Free',
        'Microsoft.Network/loadBalancers': '$20-100',
    }
    
    # Service priority rules based on project characteristics
    PRIORITY_RULES = {
        'web_application': {
            'Microsoft.Web/sites': ServicePriority.CRITICAL,
            'Microsoft.Storage/storageAccounts': ServicePriority.HIGH,
            'Microsoft.KeyVault/vaults': ServicePriority.HIGH,
            'Microsoft.Insights/components': ServicePriority.MEDIUM,
        },
        'api_service': {
            'Microsoft.Web/sites': ServicePriority.CRITICAL,
            'Microsoft.KeyVault/vaults': ServicePriority.HIGH,
            'Microsoft.Insights/components': ServicePriority.HIGH,
            'Microsoft.Storage/storageAccounts': ServicePriority.MEDIUM,
        },
        'data_application': {
            'Microsoft.Sql/servers': ServicePriority.CRITICAL,
            'Microsoft.Storage/storageAccounts': ServicePriority.HIGH,
            'Microsoft.KeyVault/vaults': ServicePriority.HIGH,
            'Microsoft.Insights/components': ServicePriority.MEDIUM,
        },
        'container_application': {
            'Microsoft.ContainerRegistry/registries': ServicePriority.CRITICAL,
            'Microsoft.ContainerInstance/containerGroups': ServicePriority.HIGH,
            'Microsoft.Storage/storageAccounts': ServicePriority.HIGH,
            'Microsoft.KeyVault/vaults': ServicePriority.MEDIUM,
        }
    }
    
    def __init__(self):
        """Initialize the project analyzer."""
        self.file_scanner = ProjectFileScanner()
    
    def analyze_project(self, project_path: Path) -> ProjectRecommendations:
        """Analyze a project and generate Azure service recommendations.
        
        Args:
            project_path: Path to the project root directory.
            
        Returns:
            ProjectRecommendations with analysis and recommendations.
        """
        logger.info(f"Analyzing project at {project_path}")
        
        if not project_path.exists() or not project_path.is_dir():
            raise ValueError(f"Project path does not exist or is not a directory: {project_path}")
        
        # Scan project files
        scan_result = self.file_scanner.scan_project(project_path)
        
        # Determine project type
        project_type = self._determine_project_type(scan_result)
        
        # Generate service recommendations
        recommendations = self._generate_service_recommendations(scan_result, project_type)
        
        # Determine deployment complexity
        complexity = self._assess_deployment_complexity(recommendations, scan_result)
        
        # Generate resource groups
        resource_groups = self._recommend_resource_groups(recommendations, project_type)
        
        # Determine deployment order
        deployment_order = self._calculate_deployment_order(recommendations)
        
        # Calculate overall confidence
        analysis_confidence = self._calculate_analysis_confidence(scan_result, recommendations)
        
        # Generate warnings
        warnings = self._generate_warnings(scan_result, recommendations)
        
        logger.info(f"Analysis complete: {project_type} project with {len(recommendations)} recommendations")
        
        return ProjectRecommendations(
            project_path=project_path,
            project_type=project_type,
            deployment_complexity=complexity,
            recommended_services=recommendations,
            resource_groups=resource_groups,
            estimated_resources=len(recommendations),
            deployment_order=deployment_order,
            warnings=warnings,
            analysis_confidence=analysis_confidence
        )
    
    def _determine_project_type(self, scan_result: ProjectAnalysisResult) -> str:
        """Determine the type of project based on scan results.
        
        Args:
            scan_result: Project scan results.
            
        Returns:
            Project type string.
        """
        frameworks = scan_result.detected_frameworks
        services = scan_result.detected_services
        
        # Web application patterns
        web_frameworks = {'ASP.NET Core', 'Express.js', 'Django', 'Flask', 'Spring Boot'}
        if any(fw in frameworks for fw in web_frameworks):
            return 'web_application'
        
        # API service patterns
        if any(service in services for service in ['Microsoft.Web/sites']):
            return 'api_service'
        
        # Container application patterns
        if any(service in services for service in ['Microsoft.ContainerRegistry/registries']):
            return 'container_application'
        
        # Data application patterns
        if any(service in services for service in ['Microsoft.Sql/servers']):
            return 'data_application'
        
        # Default to web application for most cases
        return 'web_application'
    
    def _generate_service_recommendations(
        self,
        scan_result: ProjectAnalysisResult,
        project_type: str
    ) -> List[ServiceRecommendation]:
        """Generate service recommendations based on project analysis.
        
        Args:
            scan_result: Project scan results.
            project_type: Determined project type.
            
        Returns:
            List of service recommendations.
        """
        recommendations = []
        
        # Get base recommendations for project type
        base_priorities = self.PRIORITY_RULES.get(project_type, {})
        
        # Add detected services with high confidence
        for service in scan_result.detected_services:
            priority = base_priorities.get(service, ServicePriority.MEDIUM)
            confidence = 0.9  # High confidence for detected services
            
            recommendation = ServiceRecommendation(
                service_type=service,
                service_name=self._get_service_display_name(service),
                priority=priority,
                confidence=confidence,
                reasons=[f"Detected in project code analysis"],
                dependencies=self.SERVICE_DEPENDENCIES.get(service, []),
                estimated_cost=self.COST_ESTIMATES.get(service),
                deployment_notes=self._get_deployment_notes(service)
            )
            recommendations.append(recommendation)
        
        # Add recommended services based on project type
        for service, priority in base_priorities.items():
            # Skip if already added from detection
            if any(rec.service_type == service for rec in recommendations):
                continue
            
            # Calculate confidence based on project characteristics
            confidence = self._calculate_recommendation_confidence(service, scan_result, project_type)
            
            if confidence > 0.3:  # Only add if reasonable confidence
                reasons = self._get_recommendation_reasons(service, scan_result, project_type)
                
                recommendation = ServiceRecommendation(
                    service_type=service,
                    service_name=self._get_service_display_name(service),
                    priority=priority,
                    confidence=confidence,
                    reasons=reasons,
                    dependencies=self.SERVICE_DEPENDENCIES.get(service, []),
                    estimated_cost=self.COST_ESTIMATES.get(service),
                    deployment_notes=self._get_deployment_notes(service)
                )
                recommendations.append(recommendation)
        
        # Sort by priority and confidence
        recommendations.sort(key=lambda r: (r.priority.value, -r.confidence))
        
        return recommendations
    
    def _assess_deployment_complexity(
        self,
        recommendations: List[ServiceRecommendation],
        scan_result: ProjectAnalysisResult
    ) -> DeploymentComplexity:
        """Assess the complexity of the deployment.
        
        Args:
            recommendations: Service recommendations.
            scan_result: Project scan results.
            
        Returns:
            Deployment complexity level.
        """
        num_services = len(recommendations)
        num_dependencies = sum(len(rec.dependencies) for rec in recommendations)
        num_files = scan_result.analyzed_files
        
        # Calculate complexity score
        complexity_score = 0
        complexity_score += num_services * 2
        complexity_score += num_dependencies * 3
        complexity_score += min(num_files / 50, 10)  # Cap file contribution
        
        if complexity_score <= 5:
            return DeploymentComplexity.SIMPLE
        elif complexity_score <= 15:
            return DeploymentComplexity.MODERATE
        elif complexity_score <= 30:
            return DeploymentComplexity.COMPLEX
        else:
            return DeploymentComplexity.ENTERPRISE
    
    def _recommend_resource_groups(
        self,
        recommendations: List[ServiceRecommendation],
        project_type: str
    ) -> List[str]:
        """Recommend resource group organization.
        
        Args:
            recommendations: Service recommendations.
            project_type: Project type.
            
        Returns:
            List of recommended resource group names.
        """
        num_services = len(recommendations)
        
        # Simple projects: single resource group
        if num_services <= 3:
            return ['rg-{project}-{environment}']
        
        # Moderate projects: functional separation
        elif num_services <= 8:
            groups = ['rg-{project}-app-{environment}']
            
            # Add data group if database services present
            if any('Sql' in rec.service_type for rec in recommendations):
                groups.append('rg-{project}-data-{environment}')
            
            # Add network group if networking services present
            if any('Network' in rec.service_type for rec in recommendations):
                groups.append('rg-{project}-network-{environment}')
            
            return groups
        
        # Complex projects: full separation
        else:
            return [
                'rg-{project}-app-{environment}',
                'rg-{project}-data-{environment}',
                'rg-{project}-network-{environment}',
                'rg-{project}-security-{environment}',
                'rg-{project}-monitoring-{environment}'
            ]
    
    def _calculate_deployment_order(self, recommendations: List[ServiceRecommendation]) -> List[str]:
        """Calculate the order in which services should be deployed.
        
        Args:
            recommendations: Service recommendations.
            
        Returns:
            Ordered list of service types for deployment.
        """
        # Create dependency graph
        services = {rec.service_type for rec in recommendations}
        dependencies = {rec.service_type: set(rec.dependencies) & services for rec in recommendations}
        
        # Topological sort
        deployed = set()
        deployment_order = []
        
        while len(deployed) < len(services):
            # Find services with no undeployed dependencies
            ready_services = [
                service for service in services
                if service not in deployed and dependencies[service].issubset(deployed)
            ]
            
            if not ready_services:
                # Handle circular dependencies or add remaining services
                remaining = services - deployed
                ready_services = list(remaining)
            
            # Sort by priority (critical first)
            service_priorities = {rec.service_type: rec.priority for rec in recommendations}
            ready_services.sort(key=lambda s: service_priorities.get(s, ServicePriority.LOW).value)
            
            # Add first ready service
            next_service = ready_services[0]
            deployment_order.append(next_service)
            deployed.add(next_service)
        
        return deployment_order
    
    def _calculate_analysis_confidence(
        self,
        scan_result: ProjectAnalysisResult,
        recommendations: List[ServiceRecommendation]
    ) -> float:
        """Calculate overall confidence in the analysis.
        
        Args:
            scan_result: Project scan results.
            recommendations: Service recommendations.
            
        Returns:
            Confidence score between 0.0 and 1.0.
        """
        # Base confidence from file scanning
        base_confidence = scan_result.confidence_score
        
        # Boost confidence based on detections
        detection_boost = min(0.3, len(scan_result.detected_services) * 0.1)
        
        # Average recommendation confidence
        if recommendations:
            avg_rec_confidence = sum(rec.confidence for rec in recommendations) / len(recommendations)
        else:
            avg_rec_confidence = 0.0
        
        # Combine scores
        total_confidence = (base_confidence + detection_boost + avg_rec_confidence) / 3
        return round(min(1.0, total_confidence), 2)
    
    def _generate_warnings(
        self,
        scan_result: ProjectAnalysisResult,
        recommendations: List[ServiceRecommendation]
    ) -> List[str]:
        """Generate warnings about the analysis or recommendations.
        
        Args:
            scan_result: Project scan results.
            recommendations: Service recommendations.
            
        Returns:
            List of warning messages.
        """
        warnings = []
        
        # Low file analysis rate
        if scan_result.analyzed_files < scan_result.total_files * 0.5:
            warnings.append(
                f"Only {scan_result.analyzed_files}/{scan_result.total_files} files analyzed. "
                "Recommendations may be incomplete."
            )
        
        # No services detected
        if not scan_result.detected_services:
            warnings.append(
                "No Azure services detected in code. Recommendations are based on project type only."
            )
        
        # High complexity
        if len(recommendations) > 10:
            warnings.append(
                "Large number of recommended services. Consider phased deployment approach."
            )
        
        # Missing critical services
        critical_recs = [rec for rec in recommendations if rec.priority == ServicePriority.CRITICAL]
        if not critical_recs:
            warnings.append(
                "No critical services identified. Manual review recommended."
            )
        
        return warnings
    
    def _get_service_display_name(self, service_type: str) -> str:
        """Get human-readable name for a service type.
        
        Args:
            service_type: Azure service type.
            
        Returns:
            Display name for the service.
        """
        display_names = {
            'Microsoft.Storage/storageAccounts': 'Storage Account',
            'Microsoft.Web/sites': 'Web App',
            'Microsoft.Web/serverfarms': 'App Service Plan',
            'Microsoft.KeyVault/vaults': 'Key Vault',
            'Microsoft.Sql/servers': 'SQL Server',
            'Microsoft.Sql/databases': 'SQL Database',
            'Microsoft.Insights/components': 'Application Insights',
            'Microsoft.ContainerRegistry/registries': 'Container Registry',
            'Microsoft.ContainerInstance/containerGroups': 'Container Instances',
            'Microsoft.Network/virtualNetworks': 'Virtual Network',
            'Microsoft.Network/loadBalancers': 'Load Balancer',
        }
        
        return display_names.get(service_type, service_type)
    
    def _calculate_recommendation_confidence(
        self,
        service: str,
        scan_result: ProjectAnalysisResult,
        project_type: str
    ) -> float:
        """Calculate confidence for a service recommendation.
        
        Args:
            service: Service type.
            scan_result: Project scan results.
            project_type: Project type.
            
        Returns:
            Confidence score between 0.0 and 1.0.
        """
        base_confidence = 0.5  # Default confidence
        
        # Boost for detected frameworks
        web_services = {'Microsoft.Web/sites', 'Microsoft.Web/serverfarms'}
        if service in web_services and scan_result.detected_frameworks:
            base_confidence += 0.3
        
        # Boost for project type alignment
        if project_type == 'web_application' and service in web_services:
            base_confidence += 0.2
        
        # Security services always recommended
        if 'KeyVault' in service or 'Insights' in service:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _get_recommendation_reasons(
        self,
        service: str,
        scan_result: ProjectAnalysisResult,
        project_type: str
    ) -> List[str]:
        """Get reasons for recommending a service.
        
        Args:
            service: Service type.
            scan_result: Project scan results.
            project_type: Project type.
            
        Returns:
            List of reasons for the recommendation.
        """
        reasons = []
        
        # Project type reasons
        if project_type == 'web_application':
            if 'Web' in service:
                reasons.append("Required for web application hosting")
            elif 'Storage' in service:
                reasons.append("Recommended for static content and file storage")
            elif 'KeyVault' in service:
                reasons.append("Best practice for secrets management")
        
        # Framework-based reasons
        if scan_result.detected_frameworks:
            frameworks_str = ', '.join(scan_result.detected_frameworks)
            if 'Web' in service:
                reasons.append(f"Detected web framework: {frameworks_str}")
        
        # Security reasons
        if 'KeyVault' in service:
            reasons.append("Security best practice for credential storage")
        
        # Monitoring reasons
        if 'Insights' in service:
            reasons.append("Recommended for application monitoring and diagnostics")
        
        # Default reason
        if not reasons:
            reasons.append(f"Common requirement for {project_type} projects")
        
        return reasons
    
    def _get_deployment_notes(self, service: str) -> List[str]:
        """Get deployment notes for a service.
        
        Args:
            service: Service type.
            
        Returns:
            List of deployment notes.
        """
        notes = {
            'Microsoft.Web/sites': [
                "Requires App Service Plan to be created first",
                "Configure custom domain and SSL after deployment",
                "Set up deployment slots for staging"
            ],
            'Microsoft.Storage/storageAccounts': [
                "Enable secure transfer required",
                "Configure network access rules as needed",
                "Set up lifecycle management policies"
            ],
            'Microsoft.KeyVault/vaults': [
                "Configure access policies for applications",
                "Enable soft delete and purge protection",
                "Set up key rotation policies"
            ],
            'Microsoft.Sql/servers': [
                "Configure firewall rules for client access",
                "Enable threat detection and auditing",
                "Set up backup retention policies"
            ]
        }
        
        return notes.get(service, [])