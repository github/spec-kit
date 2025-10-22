"""Deployment configuration data model.

This module defines the data structures for representing deployment configurations
and environment-specific settings.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import json


class DeploymentTarget(Enum):
    """Deployment target types."""
    RESOURCE_GROUP = "resourceGroup"
    SUBSCRIPTION = "subscription"
    MANAGEMENT_GROUP = "managementGroup"
    TENANT = "tenant"


class DeploymentMode(Enum):
    """ARM deployment modes."""
    INCREMENTAL = "Incremental"
    COMPLETE = "Complete"


class DeploymentStatus(Enum):
    """Deployment status values."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VALIDATING = "validating"


@dataclass
class AzureLocation:
    """Represents an Azure region/location."""
    name: str  # e.g., "East US"
    display_name: str  # e.g., "East US"
    regional_display_name: str  # e.g., "(US) East US"
    
    @classmethod
    def get_common_locations(cls) -> List['AzureLocation']:
        """Get list of commonly used Azure locations."""
        return [
            cls("eastus", "East US", "(US) East US"),
            cls("eastus2", "East US 2", "(US) East US 2"),
            cls("westus", "West US", "(US) West US"),
            cls("westus2", "West US 2", "(US) West US 2"),
            cls("westus3", "West US 3", "(US) West US 3"),
            cls("centralus", "Central US", "(US) Central US"),
            cls("northeurope", "North Europe", "(Europe) North Europe"),
            cls("westeurope", "West Europe", "(Europe) West Europe"),
            cls("southeastasia", "Southeast Asia", "(Asia Pacific) Southeast Asia"),
            cls("eastasia", "East Asia", "(Asia Pacific) East Asia"),
        ]


@dataclass
class ResourceGroupConfig:
    """Configuration for resource groups."""
    name: str
    location: str
    tags: Dict[str, str] = field(default_factory=dict)
    managed_by: Optional[str] = None


@dataclass
class ParameterValue:
    """Represents a parameter value for deployment."""
    name: str
    value: Any
    description: Optional[str] = None
    is_secure: bool = False
    source: str = "user"  # "user", "keyvault", "environment", "generated"
    
    def to_arm_parameter(self) -> Dict[str, Any]:
        """Convert to ARM template parameter format."""
        if self.is_secure:
            return {
                "reference": {
                    "keyVault": {
                        "id": f"/subscriptions/{{subscription-id}}/resourceGroups/{{rg}}/providers/Microsoft.KeyVault/vaults/{{vault-name}}"
                    },
                    "secretName": self.name
                }
            }
        else:
            return {"value": self.value}


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment."""
    name: str  # dev, staging, prod
    display_name: str
    
    # Azure Configuration
    subscription_id: Optional[str] = None
    tenant_id: Optional[str] = None
    location: str = "eastus"
    
    # Resource Groups
    resource_groups: List[ResourceGroupConfig] = field(default_factory=list)
    
    # Parameters
    parameters: Dict[str, ParameterValue] = field(default_factory=dict)
    
    # Tags
    default_tags: Dict[str, str] = field(default_factory=dict)
    
    # Environment-specific settings
    enable_monitoring: bool = True
    enable_diagnostics: bool = True
    enable_backup: bool = False
    enable_auto_scaling: bool = False
    
    # Security settings
    require_https: bool = True
    minimum_tls_version: str = "1.2"
    enable_rbac: bool = True
    
    # Compliance
    compliance_frameworks: List[str] = field(default_factory=list)
    
    def get_parameter_value(self, name: str) -> Any:
        """Get a parameter value."""
        if name in self.parameters:
            return self.parameters[name].value
        return None
    
    def set_parameter(self, name: str, value: Any, is_secure: bool = False, description: Optional[str] = None) -> None:
        """Set a parameter value."""
        self.parameters[name] = ParameterValue(
            name=name,
            value=value,
            is_secure=is_secure,
            description=description
        )
    
    def get_effective_tags(self, resource_tags: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get effective tags combining defaults with resource-specific tags."""
        effective_tags = self.default_tags.copy()
        if resource_tags:
            effective_tags.update(resource_tags)
        return effective_tags


@dataclass
class DeploymentValidation:
    """Deployment validation configuration and results."""
    validate_template: bool = True
    validate_parameters: bool = True
    validate_dependencies: bool = True
    validate_policies: bool = True
    
    # Validation results
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    validation_timestamp: Optional[datetime] = None
    
    def add_error(self, message: str) -> None:
        """Add a validation error."""
        self.validation_errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """Add a validation warning."""
        self.validation_warnings.append(message)


@dataclass
class DeploymentHooks:
    """Pre and post deployment hooks."""
    pre_deployment_scripts: List[str] = field(default_factory=list)
    post_deployment_scripts: List[str] = field(default_factory=list)
    validation_scripts: List[str] = field(default_factory=list)
    
    # Azure CLI commands
    pre_deployment_commands: List[str] = field(default_factory=list)
    post_deployment_commands: List[str] = field(default_factory=list)
    
    # PowerShell scripts
    pre_deployment_powershell: List[str] = field(default_factory=list)
    post_deployment_powershell: List[str] = field(default_factory=list)


@dataclass
class RollbackConfig:
    """Rollback configuration for deployments."""
    enable_rollback: bool = False
    rollback_on_failure: bool = False
    keep_backup_count: int = 3
    rollback_timeout_minutes: int = 30
    
    # Conditions for automatic rollback
    rollback_conditions: List[str] = field(default_factory=list)


@dataclass
class DeploymentMonitoring:
    """Deployment monitoring configuration."""
    enable_monitoring: bool = True
    notification_endpoints: List[str] = field(default_factory=list)
    
    # Health checks
    health_check_url: Optional[str] = None
    health_check_timeout_seconds: int = 30
    health_check_retries: int = 3
    
    # Metrics
    track_deployment_time: bool = True
    track_resource_creation: bool = True
    track_cost_changes: bool = True


@dataclass
class DeploymentConfiguration:
    """Complete deployment configuration."""
    # Basic Information
    configuration_name: str
    project_name: str
    version: str = "1.0.0"
    
    # Target Configuration
    target: DeploymentTarget
    deployment_mode: DeploymentMode = DeploymentMode.INCREMENTAL
    
    # Environment Configuration
    environments: Dict[str, EnvironmentConfig] = field(default_factory=dict)
    default_environment: str = "dev"
    
    # Template Configuration
    main_template_path: Path
    parameter_file_paths: Dict[str, Path] = field(default_factory=dict)  # environment -> path
    
    # Deployment Settings
    timeout_minutes: int = 60
    retry_count: int = 3
    parallel_deployments: bool = False
    
    # Validation
    validation: DeploymentValidation = field(default_factory=DeploymentValidation)
    
    # Hooks and Scripts
    hooks: DeploymentHooks = field(default_factory=DeploymentHooks)
    
    # Rollback
    rollback: RollbackConfig = field(default_factory=RollbackConfig)
    
    # Monitoring
    monitoring: DeploymentMonitoring = field(default_factory=DeploymentMonitoring)
    
    # Metadata
    created_timestamp: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    description: Optional[str] = None
    
    def add_environment(self, env_config: EnvironmentConfig) -> None:
        """Add an environment configuration."""
        self.environments[env_config.name] = env_config
    
    def get_environment(self, name: str) -> Optional[EnvironmentConfig]:
        """Get an environment configuration."""
        return self.environments.get(name)
    
    def get_default_environment(self) -> Optional[EnvironmentConfig]:
        """Get the default environment configuration."""
        return self.environments.get(self.default_environment)
    
    def validate_configuration(self) -> List[str]:
        """Validate the deployment configuration."""
        errors = []
        
        # Check required fields
        if not self.configuration_name:
            errors.append("Configuration name is required")
        
        if not self.project_name:
            errors.append("Project name is required")
        
        if not self.main_template_path:
            errors.append("Main template path is required")
        
        # Check template file exists
        if self.main_template_path and not self.main_template_path.exists():
            errors.append(f"Main template file not found: {self.main_template_path}")
        
        # Check environments
        if not self.environments:
            errors.append("At least one environment must be configured")
        
        if self.default_environment not in self.environments:
            errors.append(f"Default environment '{self.default_environment}' not found in environments")
        
        # Validate each environment
        for env_name, env_config in self.environments.items():
            if not env_config.location:
                errors.append(f"Environment '{env_name}' must have a location")
        
        return errors
    
    def get_parameter_file_path(self, environment: str) -> Optional[Path]:
        """Get parameter file path for an environment."""
        return self.parameter_file_paths.get(environment)
    
    def set_parameter_file_path(self, environment: str, path: Path) -> None:
        """Set parameter file path for an environment."""
        self.parameter_file_paths[environment] = path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        def convert_value(value):
            if isinstance(value, Enum):
                return value.value
            elif isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, Path):
                return str(value)
            elif hasattr(value, '__dict__'):
                return {k: convert_value(v) for k, v in value.__dict__.items()}
            elif isinstance(value, (list, tuple)):
                return [convert_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            return value
        
        return {key: convert_value(value) for key, value in self.__dict__.items()}
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""
    deployment_name: str
    environment: str
    status: DeploymentStatus
    
    # Timing
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Results
    deployed_resources: List[str] = field(default_factory=list)
    failed_resources: List[str] = field(default_factory=list)
    deployment_outputs: Dict[str, Any] = field(default_factory=dict)
    
    # Error Information
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    detailed_errors: List[str] = field(default_factory=list)
    
    # Metadata
    deployment_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def is_successful(self) -> bool:
        """Check if deployment was successful."""
        return self.status == DeploymentStatus.SUCCEEDED
    
    def get_duration(self) -> Optional[float]:
        """Get deployment duration in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None