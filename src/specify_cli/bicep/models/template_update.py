"""
Data models for tracking template updates and changes in the Bicep generator.

This module provides comprehensive tracking of template modifications, dependency
changes, and update manifests to support intelligent template regeneration and
synchronization across environments.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field, validator


class ChangeType(str, Enum):
    """Types of changes that can trigger template updates."""
    
    RESOURCE_ADDED = "resource_added"
    RESOURCE_REMOVED = "resource_removed"
    RESOURCE_MODIFIED = "resource_modified"
    DEPENDENCY_ADDED = "dependency_added"
    DEPENDENCY_REMOVED = "dependency_removed"
    CONFIGURATION_CHANGED = "configuration_changed"
    PARAMETER_ADDED = "parameter_added"
    PARAMETER_REMOVED = "parameter_removed"
    PARAMETER_MODIFIED = "parameter_modified"
    OUTPUT_ADDED = "output_added"
    OUTPUT_REMOVED = "output_removed"
    SECURITY_POLICY_CHANGED = "security_policy_changed"
    SCALING_CONFIG_CHANGED = "scaling_config_changed"


class ChangeSeverity(str, Enum):
    """Severity levels for template changes."""
    
    LOW = "low"         # Cosmetic changes, documentation updates
    MEDIUM = "medium"   # Configuration changes, parameter updates
    HIGH = "high"       # Resource additions/removals, dependency changes
    CRITICAL = "critical"  # Security policy changes, breaking changes


class ChangeImpact(str, Enum):
    """Impact scope of template changes."""
    
    LOCAL = "local"           # Affects single template
    REGIONAL = "regional"     # Affects templates in same region/environment
    GLOBAL = "global"         # Affects all environments
    DEPENDENT = "dependent"   # Affects dependent resources/templates


class FileChange(BaseModel):
    """Represents a change to a project file that may affect templates."""
    
    file_path: Path = Field(..., description="Path to the changed file")
    change_type: str = Field(..., description="Type of file change (added, modified, deleted)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the change occurred")
    hash_before: Optional[str] = Field(None, description="File hash before change")
    hash_after: Optional[str] = Field(None, description="File hash after change")
    lines_added: int = Field(0, description="Number of lines added")
    lines_removed: int = Field(0, description="Number of lines removed")
    affected_functions: List[str] = Field(default_factory=list, description="Functions/methods affected")
    affected_dependencies: List[str] = Field(default_factory=list, description="Dependencies affected")
    
    class Config:
        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat()
        }


class ResourceChange(BaseModel):
    """Represents a change to an Azure resource configuration."""
    
    resource_type: str = Field(..., description="Azure resource type (e.g., Microsoft.Web/sites)")
    resource_name: str = Field(..., description="Name of the resource")
    change_type: ChangeType = Field(..., description="Type of change applied")
    severity: ChangeSeverity = Field(..., description="Severity of the change")
    impact: ChangeImpact = Field(..., description="Scope of impact")
    
    # Change details
    property_path: Optional[str] = Field(None, description="JSON path to changed property")
    old_value: Optional[Union[str, int, float, bool, Dict, List]] = Field(None, description="Previous value")
    new_value: Optional[Union[str, int, float, bool, Dict, List]] = Field(None, description="New value")
    
    # Dependencies
    affects_resources: Set[str] = Field(default_factory=set, description="Other resources affected by this change")
    requires_resources: Set[str] = Field(default_factory=set, description="Resources this change depends on")
    
    # Validation and deployment impact
    requires_validation: bool = Field(True, description="Whether change requires ARM validation")
    requires_redeployment: bool = Field(False, description="Whether change requires resource redeployment")
    downtime_expected: bool = Field(False, description="Whether change may cause service downtime")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When change was detected")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TemplateVersion(BaseModel):
    """Version information for a Bicep template."""
    
    version: str = Field(..., description="Semantic version (e.g., 1.2.3)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When version was created")
    commit_hash: Optional[str] = Field(None, description="Git commit hash if available")
    author: Optional[str] = Field(None, description="Author of the changes")
    description: str = Field("", description="Description of changes in this version")
    change_summary: Dict[ChangeType, int] = Field(default_factory=dict, description="Count of changes by type")
    
    # Compatibility information
    breaking_changes: List[str] = Field(default_factory=list, description="List of breaking changes")
    migration_notes: List[str] = Field(default_factory=list, description="Notes for migrating from previous version")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EnvironmentStatus(BaseModel):
    """Status of template deployment in a specific environment."""
    
    environment_name: str = Field(..., description="Name of the environment (dev, staging, prod)")
    current_version: str = Field(..., description="Currently deployed template version")
    target_version: Optional[str] = Field(None, description="Target version for next deployment")
    
    # Deployment status
    last_deployed: Optional[datetime] = Field(None, description="Last successful deployment time")
    deployment_status: str = Field("unknown", description="Status: deployed, pending, failed, unknown")
    deployment_id: Optional[str] = Field(None, description="Azure deployment operation ID")
    
    # Validation status
    validation_status: str = Field("unknown", description="ARM validation status")
    validation_errors: List[str] = Field(default_factory=list, description="Validation error messages")
    validation_warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    
    # Change tracking
    pending_changes: List[ResourceChange] = Field(default_factory=list, description="Changes waiting to be deployed")
    requires_update: bool = Field(False, description="Whether environment needs template update")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DependencyInfo(BaseModel):
    """Information about template dependencies."""
    
    template_name: str = Field(..., description="Name of the dependent template")
    dependency_type: str = Field(..., description="Type of dependency (resource, module, parameter)")
    dependency_path: str = Field(..., description="Path or reference to the dependency")
    is_optional: bool = Field(False, description="Whether dependency is optional")
    version_constraint: Optional[str] = Field(None, description="Version constraint for dependency")
    
    # Circular dependency detection
    circular_dependencies: List[str] = Field(default_factory=list, description="Circular dependency chain if detected")
    
    class Config:
        json_encoders = {}


class TemplateUpdateManifest(BaseModel):
    """
    Comprehensive manifest for tracking template updates and changes.
    
    This model serves as the central tracking mechanism for all template
    modifications, enabling intelligent update detection and deployment
    orchestration across multiple environments.
    """
    
    # Basic identification
    project_path: Path = Field(..., description="Root path of the project")
    project_name: str = Field(..., description="Name of the project")
    manifest_version: str = Field("1.0.0", description="Version of the manifest format")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When manifest was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    # Template tracking
    templates: Dict[str, TemplateVersion] = Field(default_factory=dict, description="Template versions by name")
    current_template_version: str = Field("1.0.0", description="Current active template version")
    
    # Change tracking
    file_changes: List[FileChange] = Field(default_factory=list, description="Recent file changes")
    resource_changes: List[ResourceChange] = Field(default_factory=list, description="Resource configuration changes")
    pending_changes: List[ResourceChange] = Field(default_factory=list, description="Changes not yet applied to templates")
    
    # Environment status
    environments: Dict[str, EnvironmentStatus] = Field(default_factory=dict, description="Status by environment")
    
    # Dependencies
    dependencies: List[DependencyInfo] = Field(default_factory=list, description="Template dependencies")
    dependency_graph: Dict[str, List[str]] = Field(default_factory=dict, description="Dependency relationships")
    
    # Update configuration
    auto_update_enabled: bool = Field(True, description="Whether automatic updates are enabled")
    update_strategy: str = Field("incremental", description="Update strategy: incremental, full, manual")
    environments_sync: bool = Field(False, description="Whether to sync all environments")
    
    # Metadata
    last_analysis_run: Optional[datetime] = Field(None, description="Last project analysis timestamp")
    next_scheduled_update: Optional[datetime] = Field(None, description="Next scheduled update check")
    update_frequency_hours: int = Field(24, description="Hours between automatic update checks")
    
    class Config:
        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat()
        }
    
    @validator('project_path')
    def validate_project_path(cls, v):
        """Ensure project path exists."""
        if isinstance(v, str):
            v = Path(v)
        if not v.exists():
            raise ValueError(f"Project path does not exist: {v}")
        return v
    
    @validator('manifest_version')
    def validate_manifest_version(cls, v):
        """Ensure manifest version follows semantic versioning."""
        if not v or not isinstance(v, str):
            raise ValueError("Manifest version must be a non-empty string")
        
        parts = v.split('.')
        if len(parts) != 3:
            raise ValueError("Manifest version must follow semantic versioning (x.y.z)")
        
        try:
            [int(part) for part in parts]
        except ValueError:
            raise ValueError("Manifest version parts must be integers")
        
        return v
    
    def add_file_change(self, file_change: FileChange) -> None:
        """Add a new file change to the manifest."""
        self.file_changes.append(file_change)
        self.updated_at = datetime.utcnow()
    
    def add_resource_change(self, resource_change: ResourceChange) -> None:
        """Add a new resource change to the manifest."""
        self.resource_changes.append(resource_change)
        if resource_change.severity in [ChangeSeverity.HIGH, ChangeSeverity.CRITICAL]:
            self.pending_changes.append(resource_change)
        self.updated_at = datetime.utcnow()
    
    def get_changes_since(self, timestamp: datetime) -> List[Union[FileChange, ResourceChange]]:
        """Get all changes since a specific timestamp."""
        changes = []
        
        for file_change in self.file_changes:
            if file_change.timestamp > timestamp:
                changes.append(file_change)
        
        for resource_change in self.resource_changes:
            if resource_change.timestamp > timestamp:
                changes.append(resource_change)
        
        return sorted(changes, key=lambda x: x.timestamp, reverse=True)
    
    def get_environment_status(self, environment_name: str) -> Optional[EnvironmentStatus]:
        """Get status for a specific environment."""
        return self.environments.get(environment_name)
    
    def requires_template_update(self) -> bool:
        """Check if any pending changes require template regeneration."""
        return len(self.pending_changes) > 0
    
    def get_dependency_chain(self, template_name: str) -> List[str]:
        """Get the full dependency chain for a template."""
        visited = set()
        chain = []
        
        def _build_chain(name: str):
            if name in visited:
                return
            visited.add(name)
            chain.append(name)
            
            for dep in self.dependency_graph.get(name, []):
                _build_chain(dep)
        
        _build_chain(template_name)
        return chain
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in the dependency graph."""
        def _has_cycle(node: str, visited: Set[str], rec_stack: Set[str], path: List[str]) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependency_graph.get(node, []):
                if neighbor not in visited:
                    cycle = _has_cycle(neighbor, visited, rec_stack, path.copy())
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
            
            rec_stack.remove(node)
            return None
        
        cycles = []
        visited = set()
        
        for node in self.dependency_graph:
            if node not in visited:
                cycle = _has_cycle(node, visited, set(), [])
                if cycle and cycle not in cycles:
                    cycles.append(cycle)
        
        return cycles
    
    def update_environment_status(self, environment_name: str, status: EnvironmentStatus) -> None:
        """Update status for a specific environment."""
        self.environments[environment_name] = status
        self.updated_at = datetime.utcnow()
    
    def increment_version(self, version_type: str = "patch") -> str:
        """Increment the template version based on type (major, minor, patch)."""
        parts = [int(x) for x in self.current_template_version.split('.')]
        
        if version_type == "major":
            parts[0] += 1
            parts[1] = 0
            parts[2] = 0
        elif version_type == "minor":
            parts[1] += 1
            parts[2] = 0
        else:  # patch
            parts[2] += 1
        
        new_version = '.'.join(str(x) for x in parts)
        self.current_template_version = new_version
        self.updated_at = datetime.utcnow()
        
        return new_version
    
    def cleanup_old_changes(self, days_to_keep: int = 30) -> int:
        """Remove old changes to keep manifest size manageable."""
        cutoff = datetime.utcnow().replace(day=datetime.utcnow().day - days_to_keep)
        
        original_file_count = len(self.file_changes)
        original_resource_count = len(self.resource_changes)
        
        self.file_changes = [fc for fc in self.file_changes if fc.timestamp > cutoff]
        self.resource_changes = [rc for rc in self.resource_changes if rc.timestamp > cutoff]
        
        removed_count = (original_file_count - len(self.file_changes)) + (original_resource_count - len(self.resource_changes))
        
        if removed_count > 0:
            self.updated_at = datetime.utcnow()
        
        return removed_count