"""Documentation generator for Azure Bicep templates.

This module generates comprehensive documentation for the generated Bicep templates,
including architecture diagrams, resource descriptions, and deployment guides.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .models.project_analysis import ProjectAnalysisResult, ProjectType
from .models.resource_requirement import ResourceRequirement, ResourceType
from .models.bicep_template import BicepTemplate
from .models.deployment_config import DeploymentConfiguration

logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """Generates comprehensive documentation for Bicep templates."""
    
    def __init__(self, 
                 analysis_result: ProjectAnalysisResult,
                 deployment_config: DeploymentConfiguration,
                 resource_requirements: List[ResourceRequirement]):
        """Initialize the documentation generator."""
        self.analysis_result = analysis_result
        self.deployment_config = deployment_config
        self.resource_requirements = resource_requirements
        
    def generate_architecture_document(self) -> str:
        """Generate architecture documentation in Markdown format."""
        
        content = []
        
        # Header
        content.append(f"# {self.analysis_result.project_path.name} - Architecture Documentation")
        content.append("")
        content.append(f"**Generated on:** {datetime.now().isoformat()}")
        content.append(f"**Generator:** Specify CLI Bicep Generator")
        content.append("")
        
        # Table of Contents
        content.append("## Table of Contents")
        content.append("")
        content.append("1. [Project Overview](#project-overview)")
        content.append("2. [Architecture Overview](#architecture-overview)")
        content.append("3. [Azure Resources](#azure-resources)")
        content.append("4. [Environment Configuration](#environment-configuration)")
        content.append("5. [Security Configuration](#security-configuration)")
        content.append("6. [Monitoring and Observability](#monitoring-and-observability)")
        content.append("7. [Cost Estimation](#cost-estimation)")
        content.append("8. [Deployment Guide](#deployment-guide)")
        content.append("")
        
        # Project Overview
        content.extend(self._generate_project_overview())
        
        # Architecture Overview
        content.extend(self._generate_architecture_overview())
        
        # Azure Resources
        content.extend(self._generate_resources_documentation())
        
        # Environment Configuration
        content.extend(self._generate_environment_documentation())
        
        # Security Configuration
        content.extend(self._generate_security_documentation())
        
        # Monitoring and Observability
        content.extend(self._generate_monitoring_documentation())
        
        # Cost Estimation
        content.extend(self._generate_cost_documentation())
        
        # Deployment Guide
        content.extend(self._generate_deployment_guide())
        
        return "\n".join(content)
    
    def _generate_project_overview(self) -> List[str]:
        """Generate project overview section."""
        content = []
        
        content.append("## Project Overview")
        content.append("")
        content.append(f"**Project Name:** {self.analysis_result.project_path.name}")
        content.append(f"**Project Type:** {self.analysis_result.project_type.value}")
        content.append(f"**Detected Frameworks:** {', '.join([f.value for f in self.analysis_result.detected_frameworks])}")
        content.append(f"**Confidence Score:** {self.analysis_result.confidence_score:.1%}")
        content.append(f"**Total Files Analyzed:** {self.analysis_result.total_files}")
        content.append("")
        
        # Project characteristics
        if self.analysis_result.security_analysis:
            security_issues = len(self.analysis_result.security_analysis.security_issues)
            content.append(f"**Security Issues Detected:** {security_issues}")
        
        if self.analysis_result.performance_analysis:
            bottlenecks = len(self.analysis_result.performance_analysis.potential_bottlenecks)
            content.append(f"**Performance Considerations:** {bottlenecks} identified")
        
        content.append("")
        
        return content
    
    def _generate_architecture_overview(self) -> List[str]:
        """Generate architecture overview section."""
        content = []
        
        content.append("## Architecture Overview")
        content.append("")
        
        # Architecture description based on project type
        if self.analysis_result.project_type == ProjectType.WEB_APPLICATION:
            content.append("This is a **web application** architecture designed to host dynamic web content with backend services.")
        elif self.analysis_result.project_type == ProjectType.STATIC_WEBSITE:
            content.append("This is a **static website** architecture optimized for serving static content with global distribution.")
        elif self.analysis_result.project_type == ProjectType.API_SERVICE:
            content.append("This is an **API service** architecture designed to host RESTful APIs and microservices.")
        elif self.analysis_result.project_type == ProjectType.FULL_STACK_APPLICATION:
            content.append("This is a **full-stack application** architecture with both frontend and backend components.")
        else:
            content.append("This architecture is designed to support the application's specific requirements.")
        
        content.append("")
        
        # Architecture patterns
        content.append("### Architecture Patterns")
        content.append("")
        
        patterns = self._identify_architecture_patterns()
        for pattern in patterns:
            content.append(f"- **{pattern['name']}**: {pattern['description']}")
        
        content.append("")
        
        # Resource flow
        content.append("### Resource Flow")
        content.append("")
        content.append("```")
        content.append(self._generate_ascii_architecture())
        content.append("```")
        content.append("")
        
        return content
    
    def _identify_architecture_patterns(self) -> List[Dict[str, str]]:
        """Identify architecture patterns in the solution."""
        patterns = []
        
        # Check for common patterns
        resource_types = {req.resource_type for req in self.resource_requirements}
        
        if ResourceType.APP_SERVICE in resource_types:
            patterns.append({
                "name": "App Service Pattern",
                "description": "Uses Azure App Service for hosting web applications with built-in scaling and management"
            })
        
        if ResourceType.STATIC_WEB_APP in resource_types:
            patterns.append({
                "name": "Static Web App Pattern", 
                "description": "Leverages Azure Static Web Apps for hosting static content with global CDN"
            })
        
        if ResourceType.APPLICATION_INSIGHTS in resource_types:
            patterns.append({
                "name": "Observability Pattern",
                "description": "Implements comprehensive monitoring with Application Insights and Log Analytics"
            })
        
        if ResourceType.KEY_VAULT in resource_types:
            patterns.append({
                "name": "Secrets Management Pattern",
                "description": "Uses Azure Key Vault for secure storage and management of secrets and certificates"
            })
        
        if any(db_type in resource_types for db_type in [ResourceType.SQL_DATABASE, ResourceType.POSTGRESQL, ResourceType.MYSQL, ResourceType.COSMOS_DB]):
            patterns.append({
                "name": "Data Persistence Pattern",
                "description": "Implements managed database services for reliable data storage and retrieval"
            })
        
        if ResourceType.REDIS_CACHE in resource_types:
            patterns.append({
                "name": "Caching Pattern",
                "description": "Uses Redis Cache to improve application performance and reduce database load"
            })
        
        return patterns
    
    def _generate_ascii_architecture(self) -> str:
        """Generate ASCII architecture diagram."""
        lines = []
        
        # Simple flow diagram based on resources
        lines.append("Internet")
        lines.append("    |")
        lines.append("    v")
        
        if any(req.resource_type == ResourceType.APP_SERVICE for req in self.resource_requirements):
            lines.append("[App Service]")
            lines.append("    |")
        elif any(req.resource_type == ResourceType.STATIC_WEB_APP for req in self.resource_requirements):
            lines.append("[Static Web App]")
            lines.append("    |")
        
        # Database connection
        db_types = [req for req in self.resource_requirements if req.resource_type in [
            ResourceType.SQL_DATABASE, ResourceType.POSTGRESQL, ResourceType.MYSQL, ResourceType.COSMOS_DB
        ]]
        if db_types:
            lines.append("    |-- [Database]")
        
        # Cache connection
        if any(req.resource_type == ResourceType.REDIS_CACHE for req in self.resource_requirements):
            lines.append("    |-- [Redis Cache]")
        
        # Storage connection
        if any(req.resource_type == ResourceType.STORAGE_ACCOUNT for req in self.resource_requirements):
            lines.append("    |-- [Storage Account]")
        
        # Key Vault connection
        if any(req.resource_type == ResourceType.KEY_VAULT for req in self.resource_requirements):
            lines.append("    |-- [Key Vault]")
        
        # Monitoring
        if any(req.resource_type == ResourceType.APPLICATION_INSIGHTS for req in self.resource_requirements):
            lines.append("    |")
            lines.append("    v")
            lines.append("[Application Insights]")
        
        return "\n".join(lines)
    
    def _generate_resources_documentation(self) -> List[str]:
        """Generate Azure resources documentation."""
        content = []
        
        content.append("## Azure Resources")
        content.append("")
        content.append("The following Azure resources will be deployed:")
        content.append("")
        
        # Group resources by type
        resource_groups = {}
        for req in self.resource_requirements:
            category = self._get_resource_category(req.resource_type)
            if category not in resource_groups:
                resource_groups[category] = []
            resource_groups[category].append(req)
        
        for category, resources in resource_groups.items():
            content.append(f"### {category}")
            content.append("")
            
            for req in resources:
                content.append(f"#### {req.resource_type.value.replace('_', ' ').title()}")
                content.append("")
                content.append(f"**Purpose:** {req.justification}")
                content.append(f"**Priority:** {req.priority.value.title()}")
                content.append(f"**Estimated Monthly Cost:** ${req.estimated_cost_monthly:.2f}")
                
                # Add resource-specific documentation
                resource_docs = self._get_resource_specific_docs(req.resource_type)
                if resource_docs:
                    content.extend(resource_docs)
                
                content.append("")
        
        return content
    
    def _get_resource_category(self, resource_type: ResourceType) -> str:
        """Get category for a resource type."""
        category_map = {
            ResourceType.APP_SERVICE: "Compute Services",
            ResourceType.STATIC_WEB_APP: "Compute Services",
            ResourceType.FUNCTION_APP: "Compute Services",
            ResourceType.CONTAINER_INSTANCES: "Compute Services",
            ResourceType.KUBERNETES_SERVICE: "Compute Services",
            
            ResourceType.SQL_DATABASE: "Database Services",
            ResourceType.POSTGRESQL: "Database Services", 
            ResourceType.MYSQL: "Database Services",
            ResourceType.COSMOS_DB: "Database Services",
            
            ResourceType.STORAGE_ACCOUNT: "Storage Services",
            ResourceType.CDN: "Storage Services",
            
            ResourceType.KEY_VAULT: "Security Services",
            
            ResourceType.APPLICATION_INSIGHTS: "Monitoring Services",
            ResourceType.LOG_ANALYTICS: "Monitoring Services",
            
            ResourceType.REDIS_CACHE: "Performance Services",
            ResourceType.SERVICE_BUS: "Messaging Services",
            ResourceType.EVENT_HUB: "Messaging Services"
        }
        
        return category_map.get(resource_type, "Other Services")
    
    def _get_resource_specific_docs(self, resource_type: ResourceType) -> List[str]:
        """Get resource-specific documentation."""
        docs_map = {
            ResourceType.APP_SERVICE: [
                "**Features:**",
                "- Automatic scaling based on demand",
                "- Built-in load balancing", 
                "- Continuous deployment support",
                "- Custom domain and SSL certificate support"
            ],
            ResourceType.SQL_DATABASE: [
                "**Features:**",
                "- Automatic backups and point-in-time recovery",
                "- Built-in security and compliance",
                "- Automatic tuning and performance insights",
                "- High availability options"
            ],
            ResourceType.KEY_VAULT: [
                "**Features:**",
                "- Hardware security module (HSM) protection",
                "- Access policies and RBAC integration",
                "- Audit logging and monitoring",
                "- Integration with Azure services"
            ],
            ResourceType.APPLICATION_INSIGHTS: [
                "**Features:**",
                "- Application performance monitoring",
                "- Custom telemetry and metrics",
                "- Intelligent alerts and diagnostics",
                "- Integration with Azure Monitor"
            ]
        }
        
        return docs_map.get(resource_type, [])
    
    def _generate_environment_documentation(self) -> List[str]:
        """Generate environment configuration documentation."""
        content = []
        
        content.append("## Environment Configuration")
        content.append("")
        
        for env_name, env_config in self.deployment_config.environments.items():
            content.append(f"### {env_config.display_name} Environment")
            content.append("")
            content.append(f"**Region:** {env_config.location}")
            content.append(f"**Auto Scaling:** {'Enabled' if env_config.enable_auto_scaling else 'Disabled'}")
            content.append(f"**Monitoring:** {'Enabled' if env_config.enable_monitoring else 'Disabled'}")
            content.append(f"**Backup:** {'Enabled' if env_config.enable_backup else 'Disabled'}")
            
            if env_config.compliance_frameworks:
                content.append(f"**Compliance Frameworks:** {', '.join(env_config.compliance_frameworks)}")
            
            content.append("")
            
            # Environment-specific tags
            if env_config.default_tags:
                content.append("**Default Tags:**")
                for key, value in env_config.default_tags.items():
                    content.append(f"- `{key}`: {value}")
                content.append("")
        
        return content
    
    def _generate_security_documentation(self) -> List[str]:
        """Generate security configuration documentation."""
        content = []
        
        content.append("## Security Configuration")
        content.append("")
        
        # Security features
        content.append("### Security Features")
        content.append("")
        content.append("- **HTTPS Enforcement**: All web traffic uses HTTPS")
        content.append("- **Minimum TLS Version**: 1.2")
        content.append("- **Managed Identity**: Used for service-to-service authentication")
        content.append("- **RBAC**: Role-based access control enabled")
        content.append("- **Key Vault Integration**: Secrets stored securely in Azure Key Vault")
        content.append("")
        
        # Security analysis results
        if self.analysis_result.security_analysis:
            content.append("### Security Analysis Results")
            content.append("")
            
            if self.analysis_result.security_analysis.security_issues:
                content.append("**Security Issues Detected:**")
                for issue in self.analysis_result.security_analysis.security_issues:
                    content.append(f"- {issue}")
                content.append("")
            
            if self.analysis_result.security_analysis.recommendations:
                content.append("**Security Recommendations:**")
                for rec in self.analysis_result.security_analysis.recommendations:
                    content.append(f"- {rec}")
                content.append("")
        
        return content
    
    def _generate_monitoring_documentation(self) -> List[str]:
        """Generate monitoring and observability documentation."""
        content = []
        
        content.append("## Monitoring and Observability")
        content.append("")
        
        if any(req.resource_type == ResourceType.APPLICATION_INSIGHTS for req in self.resource_requirements):
            content.append("### Application Insights")
            content.append("")
            content.append("Application Insights provides:")
            content.append("- **Application Performance Monitoring (APM)**")
            content.append("- **Custom metrics and telemetry**")
            content.append("- **Intelligent alerting**")
            content.append("- **Dependency tracking**")
            content.append("- **User behavior analytics**")
            content.append("")
            
            content.append("### Key Metrics to Monitor")
            content.append("")
            content.append("- **Response Time**: Application response latency")
            content.append("- **Throughput**: Requests per second")
            content.append("- **Error Rate**: Percentage of failed requests")
            content.append("- **Availability**: Application uptime percentage")
            content.append("- **Resource Utilization**: CPU, memory, and storage usage")
            content.append("")
        
        return content
    
    def _generate_cost_documentation(self) -> List[str]:
        """Generate cost estimation documentation."""
        content = []
        
        content.append("## Cost Estimation")
        content.append("")
        
        total_cost = sum(req.estimated_cost_monthly for req in self.resource_requirements)
        
        content.append(f"**Estimated Total Monthly Cost:** ${total_cost:.2f}")
        content.append("")
        content.append("*Note: These are rough estimates. Actual costs may vary based on usage patterns, data transfer, and Azure pricing changes.*")
        content.append("")
        
        content.append("### Cost Breakdown by Service")
        content.append("")
        
        # Sort by cost descending
        sorted_requirements = sorted(self.resource_requirements, 
                                   key=lambda x: x.estimated_cost_monthly, 
                                   reverse=True)
        
        for req in sorted_requirements:
            percentage = (req.estimated_cost_monthly / total_cost * 100) if total_cost > 0 else 0
            service_name = req.resource_type.value.replace('_', ' ').title()
            content.append(f"- **{service_name}**: ${req.estimated_cost_monthly:.2f}/month ({percentage:.1f}%)")
        
        content.append("")
        
        content.append("### Cost Optimization Recommendations")
        content.append("")
        content.append("- **Right-size resources**: Start with smaller SKUs and scale up as needed")
        content.append("- **Use reserved instances**: For predictable workloads, consider reserved capacity")
        content.append("- **Monitor usage**: Set up cost alerts and regularly review Azure Cost Management")
        content.append("- **Implement auto-scaling**: Automatically scale resources based on demand")
        content.append("- **Review storage tiers**: Use appropriate storage tiers for different data access patterns")
        content.append("")
        
        return content
    
    def _generate_deployment_guide(self) -> List[str]:
        """Generate deployment guide."""
        content = []
        
        content.append("## Deployment Guide")
        content.append("")
        
        content.append("### Prerequisites")
        content.append("")
        content.append("1. **Azure CLI**: Install and configure Azure CLI")
        content.append("2. **Bicep CLI**: Install Bicep extension for Azure CLI")
        content.append("3. **Azure Subscription**: Valid Azure subscription with appropriate permissions")
        content.append("4. **Resource Groups**: Create resource groups for each environment")
        content.append("")
        
        content.append("### Step-by-Step Deployment")
        content.append("")
        
        environments = list(self.deployment_config.environments.keys())
        
        content.append("#### 1. Authenticate to Azure")
        content.append("")
        content.append("```bash")
        content.append("az login")
        content.append("az account set --subscription <your-subscription-id>")
        content.append("```")
        content.append("")
        
        content.append("#### 2. Create Resource Groups")
        content.append("")
        for env in environments:
            location = self.deployment_config.environments[env].location
            content.append("```bash")
            content.append(f"az group create --name \"rg-{self.analysis_result.project_path.name}-{env}\" --location \"{location}\"")
            content.append("```")
        content.append("")
        
        content.append("#### 3. Deploy Infrastructure")
        content.append("")
        content.append("**Using the deployment script (recommended):**")
        content.append("")
        for env in environments:
            content.append("```bash")
            content.append(f"./deploy.sh -e {env} -g \"rg-{self.analysis_result.project_path.name}-{env}\"")
            content.append("```")
        content.append("")
        
        content.append("**Using Azure CLI directly:**")
        content.append("")
        for env in environments:
            content.append("```bash")
            content.append("az deployment group create \\")
            content.append(f"  --resource-group \"rg-{self.analysis_result.project_path.name}-{env}\" \\")
            content.append("  --template-file main.bicep \\")
            content.append(f"  --parameters main.{env}.bicepparam")
            content.append("```")
        content.append("")
        
        content.append("#### 4. Verify Deployment")
        content.append("")
        content.append("After deployment, verify that all resources are created successfully:")
        content.append("")
        content.append("```bash")
        content.append("az resource list --resource-group \"rg-{project-name}-{env}\" --output table")
        content.append("```")
        content.append("")
        
        content.append("### Post-Deployment Configuration")
        content.append("")
        content.append("1. **Configure Application Settings**: Update application configuration in App Service")
        content.append("2. **Set Up Secrets**: Store sensitive configuration in Key Vault")
        content.append("3. **Configure Custom Domains**: Set up custom domain names and SSL certificates")
        content.append("4. **Set Up Monitoring**: Configure Application Insights dashboards and alerts")
        content.append("5. **Configure Backup**: Set up backup policies for databases and storage")
        content.append("")
        
        return content
    
    def generate_resource_summary(self) -> Dict[str, Any]:
        """Generate a summary of resources for quick reference."""
        summary = {
            "project_name": self.analysis_result.project_path.name,
            "project_type": self.analysis_result.project_type.value,
            "total_resources": len(self.resource_requirements),
            "estimated_monthly_cost": sum(req.estimated_cost_monthly for req in self.resource_requirements),
            "environments": list(self.deployment_config.environments.keys()),
            "resources_by_category": {},
            "security_features": [],
            "monitoring_enabled": any(req.resource_type == ResourceType.APPLICATION_INSIGHTS for req in self.resource_requirements)
        }
        
        # Group resources by category
        for req in self.resource_requirements:
            category = self._get_resource_category(req.resource_type)
            if category not in summary["resources_by_category"]:
                summary["resources_by_category"][category] = []
            
            summary["resources_by_category"][category].append({
                "name": req.resource_type.value,
                "cost": req.estimated_cost_monthly,
                "priority": req.priority.value
            })
        
        # Security features
        summary["security_features"] = [
            "HTTPS Enforcement",
            "Managed Identity",
            "Key Vault Integration", 
            "RBAC Authorization",
            "Network Security"
        ]
        
        return summary


# Export the main class
__all__ = ["DocumentationGenerator"]