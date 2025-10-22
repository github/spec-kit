"""Resource requirement data model.

This module defines the data structures for representing Azure resource
requirements and their specifications.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import json


class ResourceType(Enum):
    """Azure resource types supported by the generator."""
    # Compute
    APP_SERVICE = "Microsoft.Web/sites"
    APP_SERVICE_PLAN = "Microsoft.Web/serverfarms"
    FUNCTION_APP = "Microsoft.Web/sites"
    CONTAINER_INSTANCE = "Microsoft.ContainerInstance/containerGroups"
    VIRTUAL_MACHINE = "Microsoft.Compute/virtualMachines"
    
    # Storage
    STORAGE_ACCOUNT = "Microsoft.Storage/storageAccounts"
    COSMOS_DB = "Microsoft.DocumentDB/databaseAccounts"
    SQL_DATABASE = "Microsoft.Sql/databases"
    SQL_SERVER = "Microsoft.Sql/servers"
    
    # Networking
    VIRTUAL_NETWORK = "Microsoft.Network/virtualNetworks"
    LOAD_BALANCER = "Microsoft.Network/loadBalancers"
    APPLICATION_GATEWAY = "Microsoft.Network/applicationGateways"
    CDN_PROFILE = "Microsoft.Cdn/profiles"
    
    # Security
    KEY_VAULT = "Microsoft.KeyVault/vaults"
    
    # Monitoring
    APPLICATION_INSIGHTS = "Microsoft.Insights/components"
    LOG_ANALYTICS_WORKSPACE = "Microsoft.OperationalInsights/workspaces"
    
    # Integration
    SERVICE_BUS = "Microsoft.ServiceBus/namespaces"
    EVENT_HUB = "Microsoft.EventHub/namespaces"
    API_MANAGEMENT = "Microsoft.ApiManagement/service"
    
    # Containers
    CONTAINER_REGISTRY = "Microsoft.ContainerRegistry/registries"
    KUBERNETES_SERVICE = "Microsoft.ContainerService/managedClusters"


class PriorityLevel(Enum):
    """Priority levels for resource requirements."""
    CRITICAL = "critical"      # Must have - application won't work without it
    HIGH = "high"             # Should have - important for proper operation
    MEDIUM = "medium"         # Could have - nice to have but not essential
    LOW = "low"              # Won't have this time - future consideration
    OPTIONAL = "optional"     # Optional - user can decide


class EnvironmentType(Enum):
    """Environment types for resource sizing."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class PricingTier(Enum):
    """Common Azure pricing tiers."""
    FREE = "Free"
    BASIC = "Basic"
    STANDARD = "Standard"
    PREMIUM = "Premium"
    PREMIUM_V2 = "PremiumV2"
    PREMIUM_V3 = "PremiumV3"


@dataclass
class ResourceDependency:
    """Represents a dependency between Azure resources."""
    dependent_resource: ResourceType
    dependency_resource: ResourceType
    dependency_type: str  # "requires", "enhances", "integrates_with"
    is_mandatory: bool
    configuration_notes: List[str] = field(default_factory=list)


@dataclass
class ParameterSpecification:
    """Specification for a Bicep template parameter."""
    name: str
    parameter_type: str  # string, int, bool, object, array
    description: str
    default_value: Optional[Any] = None
    allowed_values: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    is_required: bool = True
    is_secure: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OutputSpecification:
    """Specification for a Bicep template output."""
    name: str
    output_type: str
    description: str
    value_expression: str  # Bicep expression for the value
    is_sensitive: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceConfiguration:
    """Configuration settings for an Azure resource."""
    # Basic Configuration
    name_template: str  # Template for resource name (e.g., "{prefix}-{environment}-app")
    location_expression: str = "resourceGroup().location"
    
    # SKU and Pricing
    default_sku: Optional[str] = None
    environment_skus: Dict[EnvironmentType, str] = field(default_factory=dict)
    pricing_tier: Optional[PricingTier] = None
    
    # Properties
    properties: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Security and Compliance
    enable_https_only: bool = True
    minimum_tls_version: str = "1.2"
    enable_rbac: bool = True
    network_access_rules: Dict[str, Any] = field(default_factory=dict)
    
    # Monitoring and Diagnostics
    enable_monitoring: bool = True
    enable_diagnostics: bool = True
    log_retention_days: int = 30
    
    # Tags
    default_tags: Dict[str, str] = field(default_factory=dict)
    
    # Advanced Configuration
    custom_properties: Dict[str, Any] = field(default_factory=dict)
    conditional_properties: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class CostEstimate:
    """Cost estimation for a resource requirement."""
    monthly_cost_usd: float
    cost_breakdown: Dict[str, float]  # component -> cost
    pricing_model: str  # "consumption", "reserved", "spot", etc.
    cost_factors: List[str]  # Factors affecting cost
    optimization_suggestions: List[str] = field(default_factory=list)


@dataclass
class ComplianceRequirement:
    """Compliance requirements for a resource."""
    framework: str  # "WAF", "SOC2", "GDPR", "HIPAA", etc.
    requirement_id: str
    description: str
    implementation_notes: List[str]
    is_mandatory: bool
    compliance_score: float  # 0-1 indicating compliance level


@dataclass
class ResourceRequirement:
    """Represents a requirement for an Azure resource."""
    # Basic Information
    resource_type: ResourceType
    logical_name: str  # Logical name in the template (e.g., "mainDatabase")
    display_name: str  # Human-readable name
    description: str
    
    # Requirement Details
    priority: PriorityLevel
    confidence_score: float  # 0-1 confidence in this requirement
    evidence: List[str]  # Evidence that led to this requirement
    
    # Resource Configuration
    configuration: ResourceConfiguration
    
    # Dependencies
    dependencies: List[ResourceDependency] = field(default_factory=list)
    dependents: List[ResourceType] = field(default_factory=list)  # Resources that depend on this one
    
    # Template Specifications
    parameters: List[ParameterSpecification] = field(default_factory=list)
    outputs: List[OutputSpecification] = field(default_factory=list)
    
    # Cost and Compliance
    cost_estimate: Optional[CostEstimate] = None
    compliance_requirements: List[ComplianceRequirement] = field(default_factory=list)
    
    # Metadata
    created_timestamp: datetime = field(default_factory=datetime.now)
    source_analysis: str = ""  # What analysis led to this requirement
    notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def get_environment_sku(self, environment: EnvironmentType) -> str:
        """Get the appropriate SKU for an environment."""
        if environment in self.configuration.environment_skus:
            return self.configuration.environment_skus[environment]
        elif self.configuration.default_sku:
            return self.configuration.default_sku
        else:
            # Return reasonable defaults based on resource type and environment
            return self._get_default_sku_for_environment(environment)
    
    def _get_default_sku_for_environment(self, environment: EnvironmentType) -> str:
        """Get default SKU based on resource type and environment."""
        if self.resource_type == ResourceType.APP_SERVICE_PLAN:
            if environment == EnvironmentType.DEVELOPMENT:
                return "F1"  # Free tier for development
            elif environment == EnvironmentType.PRODUCTION:
                return "P1V2"  # Production tier
            else:
                return "B1"  # Basic tier for staging/testing
        
        elif self.resource_type == ResourceType.STORAGE_ACCOUNT:
            if environment == EnvironmentType.PRODUCTION:
                return "Standard_GRS"  # Geo-redundant for production
            else:
                return "Standard_LRS"  # Locally redundant for non-prod
        
        elif self.resource_type == ResourceType.KEY_VAULT:
            return "standard"  # Key Vault only has standard and premium
        
        # Default fallback
        return "Standard"
    
    def get_estimated_monthly_cost(self, environment: EnvironmentType) -> float:
        """Get estimated monthly cost for the specified environment."""
        if self.cost_estimate:
            # Adjust base cost based on environment
            base_cost = self.cost_estimate.monthly_cost_usd
            
            if environment == EnvironmentType.DEVELOPMENT:
                return base_cost * 0.2  # Development typically uses less resources
            elif environment == EnvironmentType.TESTING:
                return base_cost * 0.3
            elif environment == EnvironmentType.STAGING:
                return base_cost * 0.5
            else:  # Production
                return base_cost
        
        return 0.0
    
    def is_compatible_with(self, other: 'ResourceRequirement') -> bool:
        """Check if this resource is compatible with another resource."""
        # Check for known incompatibilities
        # This could be expanded with more sophisticated compatibility rules
        
        # Basic compatibility check - if they have dependencies, they're likely compatible
        for dep in self.dependencies:
            if dep.dependency_resource == other.resource_type:
                return True
        
        return True
    
    def get_deployment_order_priority(self) -> int:
        """Get deployment order priority (lower number = deploy first)."""
        # Base priority on resource type and dependencies
        base_priorities = {
            ResourceType.LOG_ANALYTICS_WORKSPACE: 1,
            ResourceType.KEY_VAULT: 2,
            ResourceType.STORAGE_ACCOUNT: 3,
            ResourceType.VIRTUAL_NETWORK: 4,
            ResourceType.APP_SERVICE_PLAN: 5,
            ResourceType.SQL_SERVER: 6,
            ResourceType.APPLICATION_INSIGHTS: 7,
            ResourceType.APP_SERVICE: 8,
            ResourceType.SQL_DATABASE: 9,
            ResourceType.FUNCTION_APP: 10,
        }
        
        base_priority = base_priorities.get(self.resource_type, 50)
        
        # Adjust based on dependencies (resources with more dependencies deploy later)
        dependency_penalty = len(self.dependencies) * 5
        
        return base_priority + dependency_penalty
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        def convert_value(value):
            if isinstance(value, Enum):
                return value.value
            elif isinstance(value, datetime):
                return value.isoformat()
            elif hasattr(value, '__dict__'):
                return {k: convert_value(v) for k, v in value.__dict__.items()}
            elif isinstance(value, (list, tuple)):
                return [convert_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            return value
        
        return {key: convert_value(value) for key, value in self.__dict__.items()}


@dataclass
class ResourceRequirementSet:
    """A collection of resource requirements for a project."""
    requirements: List[ResourceRequirement]
    project_name: str
    environment: EnvironmentType
    created_timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_by_type(self, resource_type: ResourceType) -> List[ResourceRequirement]:
        """Get all requirements of a specific type."""
        return [req for req in self.requirements if req.resource_type == resource_type]
    
    def get_by_priority(self, priority: PriorityLevel) -> List[ResourceRequirement]:
        """Get all requirements of a specific priority."""
        return [req for req in self.requirements if req.priority == priority]
    
    def get_deployment_order(self) -> List[ResourceRequirement]:
        """Get requirements sorted by deployment order."""
        return sorted(self.requirements, key=lambda req: req.get_deployment_order_priority())
    
    def get_total_estimated_cost(self) -> float:
        """Get total estimated monthly cost for all requirements."""
        total = 0.0
        for req in self.requirements:
            total += req.get_estimated_monthly_cost(self.environment)
        return total
    
    def get_critical_requirements(self) -> List[ResourceRequirement]:
        """Get only critical requirements."""
        return self.get_by_priority(PriorityLevel.CRITICAL)
    
    def validate_dependencies(self) -> List[str]:
        """Validate that all dependencies are satisfied."""
        errors = []
        requirement_types = {req.resource_type for req in self.requirements}
        
        for req in self.requirements:
            for dep in req.dependencies:
                if dep.is_mandatory and dep.dependency_resource not in requirement_types:
                    errors.append(
                        f"{req.logical_name} requires {dep.dependency_resource.value} "
                        f"but it's not included in the requirements"
                    )
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'requirements': [req.to_dict() for req in self.requirements],
            'project_name': self.project_name,
            'environment': self.environment.value,
            'created_timestamp': self.created_timestamp.isoformat(),
            'metadata': self.metadata
        }