"""Bicep template data model.

This module defines the data structures for representing generated Bicep templates
and their metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import json


class TemplateType(Enum):
    """Types of Bicep templates."""
    MAIN = "main"                    # Main deployment template
    MODULE = "module"                # Reusable module
    NESTED = "nested"                # Nested template
    PARAMETER = "parameter"          # Parameter file (.bicepparam)
    VARIABLES = "variables"          # Variables file
    CONFIGURATION = "configuration"   # Configuration template


class ValidationStatus(Enum):
    """Validation status for templates."""
    NOT_VALIDATED = "not_validated"
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    VALIDATING = "validating"


@dataclass
class BicepParameter:
    """Represents a Bicep template parameter."""
    name: str
    parameter_type: str  # string, int, bool, object, array
    description: str
    default_value: Optional[Any] = None
    allowed_values: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    decorators: List[str] = field(default_factory=list)  # @secure, @description, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_bicep(self) -> str:
        """Generate Bicep parameter definition."""
        lines = []
        
        # Add decorators
        for decorator in self.decorators:
            lines.append(decorator)
        
        # Add description decorator if not already present
        if self.description and not any('@description' in d for d in self.decorators):
            lines.append(f"@description('{self.description}')")
        
        # Add validation decorators
        if self.allowed_values:
            values_str = json.dumps(self.allowed_values)
            lines.append(f"@allowed({values_str})")
        
        if self.min_value is not None:
            lines.append(f"@minValue({self.min_value})")
        
        if self.max_value is not None:
            lines.append(f"@maxValue({self.max_value})")
        
        if self.min_length is not None:
            lines.append(f"@minLength({self.min_length})")
        
        if self.max_length is not None:
            lines.append(f"@maxLength({self.max_length})")
        
        # Parameter declaration
        param_line = f"param {self.name} {self.parameter_type}"
        if self.default_value is not None:
            if isinstance(self.default_value, str):
                param_line += f" = '{self.default_value}'"
            else:
                param_line += f" = {json.dumps(self.default_value)}"
        
        lines.append(param_line)
        return '\n'.join(lines)


@dataclass
class BicepVariable:
    """Represents a Bicep template variable."""
    name: str
    expression: str
    description: Optional[str] = None
    
    def to_bicep(self) -> str:
        """Generate Bicep variable definition."""
        lines = []
        if self.description:
            lines.append(f"// {self.description}")
        lines.append(f"var {self.name} = {self.expression}")
        return '\n'.join(lines)


@dataclass
class BicepResource:
    """Represents a Bicep resource definition."""
    symbolic_name: str
    resource_type: str
    api_version: str
    name_expression: str
    properties: Dict[str, Any] = field(default_factory=dict)
    location_expression: str = "location"
    tags_expression: str = "tags"
    depends_on: List[str] = field(default_factory=list)
    condition_expression: Optional[str] = None
    scope_expression: Optional[str] = None
    identity: Optional[Dict[str, Any]] = None
    
    def to_bicep(self) -> str:
        """Generate Bicep resource definition."""
        lines = []
        
        # Resource declaration
        resource_line = f"resource {self.symbolic_name} '{self.resource_type}@{self.api_version}' = "
        
        # Add condition if present
        if self.condition_expression:
            resource_line += f"if ({self.condition_expression}) "
        
        resource_line += "{"
        lines.append(resource_line)
        
        # Resource properties
        lines.append(f"  name: {self.name_expression}")
        lines.append(f"  location: {self.location_expression}")
        
        if self.tags_expression != "{}":
            lines.append(f"  tags: {self.tags_expression}")
        
        if self.scope_expression:
            lines.append(f"  scope: {self.scope_expression}")
        
        if self.identity:
            lines.append(f"  identity: {json.dumps(self.identity, indent=2).replace('\\n', '\\n  ')}")
        
        if self.properties:
            lines.append(f"  properties: {json.dumps(self.properties, indent=2).replace('\\n', '\\n  ')}")
        
        lines.append("}")
        
        return '\n'.join(lines)


@dataclass
class BicepOutput:
    """Represents a Bicep template output."""
    name: str
    output_type: str
    value_expression: str
    description: Optional[str] = None
    is_sensitive: bool = False
    
    def to_bicep(self) -> str:
        """Generate Bicep output definition."""
        lines = []
        
        if self.description:
            lines.append(f"@description('{self.description}')")
        
        if self.is_sensitive:
            lines.append("@secure()")
        
        lines.append(f"output {self.name} {self.output_type} = {self.value_expression}")
        
        return '\n'.join(lines)


@dataclass
class BicepModule:
    """Represents a Bicep module reference."""
    symbolic_name: str
    module_path: str
    name_expression: str
    parameters: Dict[str, str] = field(default_factory=dict)  # param_name -> expression
    depends_on: List[str] = field(default_factory=list)
    condition_expression: Optional[str] = None
    scope_expression: Optional[str] = None
    
    def to_bicep(self) -> str:
        """Generate Bicep module reference."""
        lines = []
        
        # Module declaration
        module_line = f"module {self.symbolic_name} '{self.module_path}' = "
        
        if self.condition_expression:
            module_line += f"if ({self.condition_expression}) "
        
        module_line += "{"
        lines.append(module_line)
        
        lines.append(f"  name: {self.name_expression}")
        
        if self.scope_expression:
            lines.append(f"  scope: {self.scope_expression}")
        
        if self.parameters:
            lines.append("  params: {")
            for param_name, param_value in self.parameters.items():
                lines.append(f"    {param_name}: {param_value}")
            lines.append("  }")
        
        lines.append("}")
        
        return '\n'.join(lines)


@dataclass
class ValidationIssue:
    """Represents a validation issue with a template."""
    severity: str  # "error", "warning", "info"
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    code: Optional[str] = None  # Error code
    suggestion: Optional[str] = None


@dataclass
class BicepTemplate:
    """Represents a complete Bicep template."""
    # Basic Information
    template_name: str
    template_type: TemplateType
    description: str
    version: str = "1.0.0"
    
    # Template Content
    parameters: List[BicepParameter] = field(default_factory=list)
    variables: List[BicepVariable] = field(default_factory=list)
    resources: List[BicepResource] = field(default_factory=list)
    modules: List[BicepModule] = field(default_factory=list)
    outputs: List[BicepOutput] = field(default_factory=list)
    
    # File Information
    file_path: Optional[Path] = None
    relative_path: Optional[str] = None
    
    # Validation
    validation_status: ValidationStatus = ValidationStatus.NOT_VALIDATED
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    
    # Metadata
    target_scope: str = "resourceGroup"  # resourceGroup, subscription, managementGroup
    schema_version: str = "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#"
    created_timestamp: datetime = field(default_factory=datetime.now)
    modified_timestamp: datetime = field(default_factory=datetime.now)
    author: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)  # Other templates this depends on
    
    def add_parameter(self, parameter: BicepParameter) -> None:
        """Add a parameter to the template."""
        # Check for duplicates
        existing_names = {p.name for p in self.parameters}
        if parameter.name in existing_names:
            raise ValueError(f"Parameter '{parameter.name}' already exists")
        
        self.parameters.append(parameter)
        self._update_modified_timestamp()
    
    def add_variable(self, variable: BicepVariable) -> None:
        """Add a variable to the template."""
        # Check for duplicates
        existing_names = {v.name for v in self.variables}
        if variable.name in existing_names:
            raise ValueError(f"Variable '{variable.name}' already exists")
        
        self.variables.append(variable)
        self._update_modified_timestamp()
    
    def add_resource(self, resource: BicepResource) -> None:
        """Add a resource to the template."""
        # Check for duplicates
        existing_names = {r.symbolic_name for r in self.resources}
        if resource.symbolic_name in existing_names:
            raise ValueError(f"Resource '{resource.symbolic_name}' already exists")
        
        self.resources.append(resource)
        self._update_modified_timestamp()
    
    def add_module(self, module: BicepModule) -> None:
        """Add a module reference to the template."""
        # Check for duplicates
        existing_names = {m.symbolic_name for m in self.modules}
        if module.symbolic_name in existing_names:
            raise ValueError(f"Module '{module.symbolic_name}' already exists")
        
        self.modules.append(module)
        self._update_modified_timestamp()
    
    def add_output(self, output: BicepOutput) -> None:
        """Add an output to the template."""
        # Check for duplicates
        existing_names = {o.name for o in self.outputs}
        if output.name in existing_names:
            raise ValueError(f"Output '{output.name}' already exists")
        
        self.outputs.append(output)
        self._update_modified_timestamp()
    
    def _update_modified_timestamp(self) -> None:
        """Update the modified timestamp."""
        self.modified_timestamp = datetime.now()
    
    def to_bicep(self) -> str:
        """Generate the complete Bicep template content."""
        sections = []
        
        # Header comment
        header = f"""// {self.description}
// Generated: {self.created_timestamp.strftime('%Y-%m-%d %H:%M:%S')}
// Version: {self.version}
"""
        sections.append(header)
        
        # Target scope (if not default)
        if self.target_scope != "resourceGroup":
            sections.append(f"targetScope = '{self.target_scope}'")
            sections.append("")
        
        # Parameters
        if self.parameters:
            sections.append("// Parameters")
            for param in self.parameters:
                sections.append(param.to_bicep())
                sections.append("")
        
        # Variables
        if self.variables:
            sections.append("// Variables")
            for var in self.variables:
                sections.append(var.to_bicep())
            sections.append("")
        
        # Resources
        if self.resources:
            sections.append("// Resources")
            for resource in self.resources:
                sections.append(resource.to_bicep())
                sections.append("")
        
        # Modules
        if self.modules:
            sections.append("// Modules")
            for module in self.modules:
                sections.append(module.to_bicep())
                sections.append("")
        
        # Outputs
        if self.outputs:
            sections.append("// Outputs")
            for output in self.outputs:
                sections.append(output.to_bicep())
                sections.append("")
        
        return '\n'.join(sections)
    
    def get_parameter_names(self) -> List[str]:
        """Get list of parameter names."""
        return [p.name for p in self.parameters]
    
    def get_resource_names(self) -> List[str]:
        """Get list of resource symbolic names."""
        return [r.symbolic_name for r in self.resources]
    
    def get_output_names(self) -> List[str]:
        """Get list of output names."""
        return [o.name for o in self.outputs]
    
    def has_errors(self) -> bool:
        """Check if template has validation errors."""
        return any(issue.severity == "error" for issue in self.validation_issues)
    
    def has_warnings(self) -> bool:
        """Check if template has validation warnings."""
        return any(issue.severity == "warning" for issue in self.validation_issues)
    
    def get_estimated_size(self) -> int:
        """Get estimated template size in characters."""
        return len(self.to_bicep())
    
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


@dataclass
class BicepTemplateSet:
    """Represents a collection of related Bicep templates."""
    main_template: BicepTemplate
    modules: List[BicepTemplate] = field(default_factory=list)
    parameter_files: List[BicepTemplate] = field(default_factory=list)
    
    project_name: str = ""
    environment: str = "dev"
    output_directory: Optional[Path] = None
    
    created_timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_module(self, module: BicepTemplate) -> None:
        """Add a module template."""
        if module.template_type != TemplateType.MODULE:
            raise ValueError("Template must be of type MODULE")
        
        self.modules.append(module)
    
    def add_parameter_file(self, param_file: BicepTemplate) -> None:
        """Add a parameter file."""
        if param_file.template_type != TemplateType.PARAMETER:
            raise ValueError("Template must be of type PARAMETER")
        
        self.parameter_files.append(param_file)
    
    def get_all_templates(self) -> List[BicepTemplate]:
        """Get all templates in the set."""
        return [self.main_template] + self.modules + self.parameter_files
    
    def validate_references(self) -> List[str]:
        """Validate that all module references are satisfied."""
        errors = []
        
        # Get all module paths referenced in main template
        referenced_modules = {module.module_path for module in self.main_template.modules}
        
        # Get all actual module files
        actual_modules = {str(module.relative_path) for module in self.modules if module.relative_path}
        
        # Check for missing modules
        for ref_module in referenced_modules:
            if ref_module not in actual_modules:
                errors.append(f"Referenced module not found: {ref_module}")
        
        return errors
    
    def get_deployment_order(self) -> List[BicepTemplate]:
        """Get templates in deployment order (modules first, then main)."""
        return self.modules + [self.main_template]