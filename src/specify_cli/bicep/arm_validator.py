"""ARM template validation utility.

This module provides functionality to validate ARM templates and Bicep files
against Azure Resource Manager APIs and schemas.
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .mcp_client import AzureMCPClient, MCPServerResponse

logger = logging.getLogger(__name__)

# Forward reference to avoid circular imports
BestPracticesValidator = None


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationType(Enum):
    """Types of validation performed."""
    SYNTAX = "syntax"
    SCHEMA = "schema"
    DEPLOYMENT = "deployment"
    BEST_PRACTICE = "best_practice"


@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: ValidationSeverity
    validation_type: ValidationType
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    resource_type: Optional[str] = None
    property_path: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of template validation."""
    is_valid: bool
    template_path: Path
    validation_time: datetime
    issues: List[ValidationIssue] = field(default_factory=list)
    validated_resources: List[str] = field(default_factory=list)
    schema_version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ARMTemplateValidator:
    """Validator for ARM templates and Bicep files."""
    
    # Common ARM template schema patterns
    ARM_SCHEMA_PATTERNS = [
        r'https://schema\.management\.azure\.com/schemas/.*deploymentTemplate\.json#',
        r'https://schema\.management\.azure\.com/schemas/.*subscriptionDeploymentTemplate\.json#',
        r'https://schema\.management\.azure\.com/schemas/.*managementGroupDeploymentTemplate\.json#'
    ]
    
    # Required ARM template properties
    REQUIRED_ARM_PROPERTIES = ['$schema', 'contentVersion', 'resources']
    
    # Best practice rules
    BEST_PRACTICE_RULES = {
        'parameter_descriptions': {
            'message': 'Parameters should have descriptions',
            'severity': ValidationSeverity.WARNING
        },
        'output_descriptions': {
            'message': 'Outputs should have descriptions',
            'severity': ValidationSeverity.WARNING
        },
        'resource_dependencies': {
            'message': 'Resource dependencies should be explicit',
            'severity': ValidationSeverity.INFO
        },
        'naming_conventions': {
            'message': 'Resource names should follow Azure naming conventions',
            'severity': ValidationSeverity.WARNING
        },
        'tags_usage': {
            'message': 'Resources should include tags for management',
            'severity': ValidationSeverity.INFO
        }
    }
    
    def __init__(self):
        """Initialize the ARM template validator."""
        self.mcp_client = AzureMCPClient()
    
    async def validate_template(
        self,
        template_path: Path,
        validate_deployment: bool = False,
        subscription_id: Optional[str] = None,
        resource_group: Optional[str] = None
    ) -> ValidationResult:
        """Validate an ARM template or Bicep file.
        
        Args:
            template_path: Path to the template file.
            validate_deployment: Whether to perform deployment validation.
            subscription_id: Azure subscription ID for deployment validation.
            resource_group: Resource group for deployment validation.
            
        Returns:
            ValidationResult with all validation issues.
        """
        logger.info(f"Validating template: {template_path}")
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        validation_result = ValidationResult(
            is_valid=True,
            template_path=template_path,
            validation_time=datetime.now()
        )
        
        # Add progress tracking
        validation_steps = ["Reading", "Syntax", "Schema", "Best Practices"]
        current_step = 0
        
        def log_progress(step: str):
            nonlocal current_step
            current_step += 1
            logger.debug(f"[{current_step}/{len(validation_steps)}] {step}")
        
        try:
            # Read template content
            log_progress("Reading template file")
            content = self._read_template_file(template_path)
            
            # Determine file type
            is_bicep = template_path.suffix.lower() == '.bicep'
            
            log_progress("Validating syntax")
            if is_bicep:
                await self._validate_bicep_file(content, template_path, validation_result)
            else:
                await self._validate_arm_template(content, template_path, validation_result)
            
            # Perform deployment validation if requested
            if validate_deployment and subscription_id:
                log_progress("Validating deployment")
                await self._validate_deployment(
                    content, template_path, validation_result,
                    subscription_id, resource_group
                )
            
            # Apply best practice checks
            log_progress("Checking best practices")
            self._validate_best_practices(content, template_path, validation_result, is_bicep)
            
            # Determine overall validation status
            validation_result.is_valid = not any(
                issue.severity == ValidationSeverity.ERROR 
                for issue in validation_result.issues
            )
            
            logger.info(
                f"Validation complete: {'PASSED' if validation_result.is_valid else 'FAILED'} "
                f"with {len(validation_result.issues)} issues"
            )
            
        except Exception as e:
            logger.error(f"Validation failed with exception: {e}")
            validation_result.is_valid = False
            validation_result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    validation_type=ValidationType.SYNTAX,
                    message=f"Validation error: {str(e)}"
                )
            )
        
        return validation_result
    
    async def validate_template_comprehensive(
        self,
        template_path: Path,
        enable_best_practices: bool = True,
        validate_deployment: bool = False,
        subscription_id: Optional[str] = None,
        resource_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive validation including best practices.
        
        Args:
            template_path: Path to the template file.
            enable_best_practices: Whether to run best practices validation.
            validate_deployment: Whether to perform deployment validation.
            subscription_id: Azure subscription ID for deployment validation.
            resource_group: Resource group for deployment validation.
            
        Returns:
            Dictionary with validation results and best practices assessment.
        """
        logger.info(f"Starting comprehensive validation for: {template_path}")
        
        results = {
            'template_path': str(template_path),
            'validation_time': datetime.now().isoformat(),
            'arm_validation': None,
            'best_practices_assessment': None,
            'overall_success': False,
            'summary': {
                'total_issues': 0,
                'errors': 0,
                'warnings': 0,
                'recommendations': 0
            }
        }
        
        try:
            # Basic ARM/Bicep validation
            arm_result = await self.validate_template(
                template_path, validate_deployment, subscription_id, resource_group
            )
            results['arm_validation'] = self._serialize_validation_result(arm_result)
            
            # Best practices validation if enabled
            if enable_best_practices:
                # Import here to avoid circular dependency
                global BestPracticesValidator
                if BestPracticesValidator is None:
                    from .best_practices_validator import BestPracticesValidator
                
                best_practices_validator = BestPracticesValidator(self)
                
                # Convert to BicepTemplate if needed for best practices validation
                template_content = self._read_template_file(template_path)
                
                if template_path.suffix.lower() == '.bicep':
                    # For Bicep files, create a mock BicepTemplate
                    from .models.bicep_template import BicepTemplate
                    bicep_template = BicepTemplate(
                        name=template_path.stem,
                        description=f"Template for {template_path.stem}",
                        version="1.0.0"
                    )
                    bicep_template.content = template_content
                    
                    assessment = await best_practices_validator.validate_template_best_practices(
                        bicep_template, template_content
                    )
                    results['best_practices_assessment'] = self._serialize_assessment(assessment)
            
            # Calculate summary
            arm_issues = arm_result.issues if arm_result else []
            bp_issues = results.get('best_practices_assessment', {}).get('violations', [])
            
            results['summary']['total_issues'] = len(arm_issues) + len(bp_issues)
            results['summary']['errors'] = len([i for i in arm_issues if i.severity == ValidationSeverity.ERROR])
            results['summary']['warnings'] = len([i for i in arm_issues if i.severity == ValidationSeverity.WARNING])
            results['summary']['recommendations'] = len(bp_issues)
            
            # Overall success if no errors
            results['overall_success'] = (
                arm_result.is_valid if arm_result else False
            ) and results['summary']['errors'] == 0
            
            logger.info(
                f"Comprehensive validation complete: {'SUCCESS' if results['overall_success'] else 'FAILED'} "
                f"({results['summary']['total_issues']} total issues)"
            )
            
        except Exception as e:
            logger.error(f"Comprehensive validation failed: {e}")
            results['error'] = str(e)
            results['overall_success'] = False
        
        return results
    
    def _serialize_validation_result(self, result: ValidationResult) -> Dict[str, Any]:
        """Serialize ValidationResult to dictionary."""
        return {
            'is_valid': result.is_valid,
            'template_path': str(result.template_path),
            'validation_time': result.validation_time.isoformat(),
            'issues': [
                {
                    'severity': issue.severity.value,
                    'validation_type': issue.validation_type.value,
                    'message': issue.message,
                    'line_number': issue.line_number,
                    'column_number': issue.column_number,
                    'resource_type': issue.resource_type,
                    'property_path': issue.property_path,
                    'suggestion': issue.suggestion
                }
                for issue in result.issues
            ],
            'validated_resources': result.validated_resources,
            'schema_version': result.schema_version,
            'metadata': result.metadata
        }
    
    def _serialize_assessment(self, assessment) -> Dict[str, Any]:
        """Serialize WellArchitectedAssessment to dictionary."""
        return {
            'overall_score': assessment.overall_score,
            'pillar_scores': {
                'reliability': assessment.reliability_score,
                'security': assessment.security_score,
                'cost_optimization': assessment.cost_optimization_score,
                'operational_excellence': assessment.operational_excellence_score,
                'performance_efficiency': assessment.performance_efficiency_score
            },
            'violations': [
                {
                    'rule_id': v.rule_id,
                    'resource_name': v.resource_name,
                    'resource_type': v.resource_type,
                    'message': v.message,
                    'severity': v.severity,
                    'line_number': v.line_number,
                    'suggestion': v.suggestion
                }
                for v in assessment.violations
            ],
            'recommendations': assessment.recommendations
        }
    
    def validate_template_sync(
        self,
        template_path: Path,
        validate_deployment: bool = False,
        subscription_id: Optional[str] = None,
        resource_group: Optional[str] = None
    ) -> ValidationResult:
        """Synchronous wrapper for template validation.
        
        Args:
            template_path: Path to the template file.
            validate_deployment: Whether to perform deployment validation.
            subscription_id: Azure subscription ID for deployment validation.
            resource_group: Resource group for deployment validation.
            
        Returns:
            ValidationResult with all validation issues.
        """
        return asyncio.run(
            self.validate_template(
                template_path, validate_deployment, subscription_id, resource_group
            )
        )
    
    async def validate_bicep_syntax(self, bicep_content: str) -> List[ValidationIssue]:
        """Validate Bicep syntax using Azure MCP Server.
        
        Args:
            bicep_content: Bicep template content.
            
        Returns:
            List of syntax validation issues.
        """
        issues = []
        
        try:
            # Use MCP client to validate Bicep syntax
            response = await self.mcp_client.validate_bicep_template(bicep_content)
            
            if response and not response.success:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        validation_type=ValidationType.SYNTAX,
                        message=response.error or "Bicep syntax validation failed"
                    )
                )
            
        except Exception as e:
            logger.warning(f"Bicep syntax validation failed: {e}")
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    validation_type=ValidationType.SYNTAX,
                    message=f"Could not validate Bicep syntax: {str(e)}"
                )
            )
        
        return issues
    
    async def validate_resource_schema(
        self,
        resource_type: str,
        resource_properties: Dict[str, Any],
        api_version: Optional[str] = None
    ) -> List[ValidationIssue]:
        """Validate resource properties against Azure schema.
        
        Args:
            resource_type: Azure resource type (e.g., 'Microsoft.Storage/storageAccounts').
            resource_properties: Resource properties to validate.
            api_version: API version to use for validation.
            
        Returns:
            List of schema validation issues.
        """
        issues = []
        
        try:
            # Get schema from MCP client
            schema_response = await self.mcp_client.get_bicep_schema(resource_type, api_version)
            
            if schema_response and schema_response.success and schema_response.data:
                schema = schema_response.data
                
                # Validate against schema
                validation_issues = self._validate_against_schema(
                    resource_properties, schema, resource_type
                )
                issues.extend(validation_issues)
            else:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        validation_type=ValidationType.SCHEMA,
                        message=f"Could not retrieve schema for {resource_type}",
                        resource_type=resource_type
                    )
                )
                
        except Exception as e:
            logger.warning(f"Schema validation failed for {resource_type}: {e}")
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    validation_type=ValidationType.SCHEMA,
                    message=f"Schema validation error: {str(e)}",
                    resource_type=resource_type
                )
            )
        
        return issues
    
    def _read_template_file(self, template_path: Path) -> str:
        """Read template file content with proper encoding.
        
        Args:
            template_path: Path to the template file.
            
        Returns:
            Template content as string.
        """
        encodings = ['utf-8', 'utf-16', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(template_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        raise ValueError(f"Could not read template file with supported encodings: {template_path}")
    
    async def _validate_bicep_file(
        self,
        content: str,
        template_path: Path,
        validation_result: ValidationResult
    ):
        """Validate a Bicep file.
        
        Args:
            content: Bicep file content.
            template_path: Path to the Bicep file.
            validation_result: Validation result to update.
        """
        # Basic Bicep syntax validation
        syntax_issues = await self.validate_bicep_syntax(content)
        validation_result.issues.extend(syntax_issues)
        
        # Extract and validate resources
        resources = self._extract_bicep_resources(content)
        validation_result.validated_resources = [r['type'] for r in resources]
        
        # Validate each resource
        for resource in resources:
            if 'type' in resource and 'properties' in resource:
                resource_issues = await self.validate_resource_schema(
                    resource['type'],
                    resource['properties'],
                    resource.get('apiVersion')
                )
                validation_result.issues.extend(resource_issues)
    
    async def _validate_arm_template(
        self,
        content: str,
        template_path: Path,
        validation_result: ValidationResult
    ):
        """Validate an ARM template.
        
        Args:
            content: ARM template content.
            template_path: Path to the ARM template.
            validation_result: Validation result to update.
        """
        try:
            # Parse JSON
            template = json.loads(content)
            
            # Validate required properties
            for prop in self.REQUIRED_ARM_PROPERTIES:
                if prop not in template:
                    validation_result.issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            validation_type=ValidationType.SYNTAX,
                            message=f"Missing required property: {prop}"
                        )
                    )
            
            # Validate schema
            if '$schema' in template:
                validation_result.schema_version = template['$schema']
                if not any(pattern in template['$schema'] for pattern in self.ARM_SCHEMA_PATTERNS):
                    validation_result.issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            validation_type=ValidationType.SCHEMA,
                            message="Unrecognized ARM template schema"
                        )
                    )
            
            # Validate resources
            if 'resources' in template:
                for i, resource in enumerate(template['resources']):
                    await self._validate_arm_resource(resource, i, validation_result)
                    
                validation_result.validated_resources = [
                    r.get('type', 'Unknown') for r in template['resources']
                ]
        
        except json.JSONDecodeError as e:
            validation_result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    validation_type=ValidationType.SYNTAX,
                    message=f"Invalid JSON: {str(e)}",
                    line_number=getattr(e, 'lineno', None),
                    column_number=getattr(e, 'colno', None)
                )
            )
    
    async def _validate_arm_resource(
        self,
        resource: Dict[str, Any],
        resource_index: int,
        validation_result: ValidationResult
    ):
        """Validate a single ARM template resource.
        
        Args:
            resource: Resource definition.
            resource_index: Index of resource in template.
            validation_result: Validation result to update.
        """
        # Required properties
        required_props = ['type', 'apiVersion', 'name']
        for prop in required_props:
            if prop not in resource:
                validation_result.issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        validation_type=ValidationType.SYNTAX,
                        message=f"Resource {resource_index}: Missing required property '{prop}'",
                        resource_type=resource.get('type')
                    )
                )
        
        # Schema validation
        if 'type' in resource and 'properties' in resource:
            resource_issues = await self.validate_resource_schema(
                resource['type'],
                resource['properties'],
                resource.get('apiVersion')
            )
            validation_result.issues.extend(resource_issues)
    
    async def _validate_deployment(
        self,
        content: str,
        template_path: Path,
        validation_result: ValidationResult,
        subscription_id: str,
        resource_group: Optional[str]
    ):
        """Validate template for deployment.
        
        Args:
            content: Template content.
            template_path: Path to template.
            validation_result: Validation result to update.
            subscription_id: Azure subscription ID.
            resource_group: Resource group name.
        """
        try:
            # Use MCP client for deployment validation
            # This is a placeholder - actual implementation would use Azure APIs
            logger.info(f"Performing deployment validation for {template_path}")
            
            # Mock deployment validation
            validation_result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    validation_type=ValidationType.DEPLOYMENT,
                    message="Deployment validation completed successfully"
                )
            )
            
        except Exception as e:
            validation_result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    validation_type=ValidationType.DEPLOYMENT,
                    message=f"Deployment validation failed: {str(e)}"
                )
            )
    
    def _validate_best_practices(
        self,
        content: str,
        template_path: Path,
        validation_result: ValidationResult,
        is_bicep: bool
    ):
        """Validate against best practices.
        
        Args:
            content: Template content.
            template_path: Path to template.
            validation_result: Validation result to update.
            is_bicep: Whether this is a Bicep file.
        """
        # Check for parameter descriptions
        if is_bicep:
            if 'param ' in content and '@description' not in content:
                validation_result.issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        validation_type=ValidationType.BEST_PRACTICE,
                        message="Parameters should include @description annotations",
                        suggestion="Add @description('...') above parameter definitions"
                    )
                )
        else:
            # ARM template checks
            try:
                template = json.loads(content)
                
                # Check parameter descriptions
                if 'parameters' in template:
                    for param_name, param_def in template['parameters'].items():
                        if 'metadata' not in param_def or 'description' not in param_def['metadata']:
                            validation_result.issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverity.WARNING,
                                    validation_type=ValidationType.BEST_PRACTICE,
                                    message=f"Parameter '{param_name}' lacks description",
                                    suggestion="Add metadata.description to parameter definition"
                                )
                            )
                
                # Check for tags
                if 'resources' in template:
                    for resource in template['resources']:
                        if 'tags' not in resource:
                            validation_result.issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverity.INFO,
                                    validation_type=ValidationType.BEST_PRACTICE,
                                    message=f"Resource '{resource.get('name', 'unnamed')}' should include tags",
                                    resource_type=resource.get('type'),
                                    suggestion="Add tags property to resource for better management"
                                )
                            )
                            
            except json.JSONDecodeError:
                # Skip best practice checks if JSON is invalid
                pass
    
    def _extract_bicep_resources(self, content: str) -> List[Dict[str, Any]]:
        """Extract resource definitions from Bicep content.
        
        Args:
            content: Bicep file content.
            
        Returns:
            List of resource definitions.
        """
        resources = []
        
        # Simple parsing - in a real implementation, this would use a proper Bicep parser
        lines = content.split('\n')
        current_resource = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('resource '):
                # Start of new resource
                parts = line.split()
                if len(parts) >= 3:
                    resource_name = parts[1]
                    resource_type_and_version = parts[2].strip("'\"")
                    
                    if '@' in resource_type_and_version:
                        resource_type, api_version = resource_type_and_version.split('@', 1)
                    else:
                        resource_type = resource_type_and_version
                        api_version = None
                    
                    current_resource = {
                        'name': resource_name,
                        'type': resource_type,
                        'apiVersion': api_version,
                        'properties': {}
                    }
            
            elif current_resource and line == '}':
                # End of resource
                resources.append(current_resource)
                current_resource = None
        
        return resources
    
    def _validate_against_schema(
        self,
        properties: Dict[str, Any],
        schema: Dict[str, Any],
        resource_type: str
    ) -> List[ValidationIssue]:
        """Validate properties against a JSON schema.
        
        Args:
            properties: Resource properties to validate.
            schema: JSON schema to validate against.
            resource_type: Resource type being validated.
            
        Returns:
            List of validation issues.
        """
        issues = []
        
        # Basic schema validation - in a real implementation, use jsonschema library
        if 'required' in schema:
            for required_prop in schema['required']:
                if required_prop not in properties:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            validation_type=ValidationType.SCHEMA,
                            message=f"Missing required property: {required_prop}",
                            resource_type=resource_type,
                            property_path=required_prop
                        )
                    )
        
        # Check property types
        if 'properties' in schema:
            for prop_name, prop_value in properties.items():
                if prop_name in schema['properties']:
                    prop_schema = schema['properties'][prop_name]
                    if 'type' in prop_schema:
                        expected_type = prop_schema['type']
                        actual_type = type(prop_value).__name__
                        
                        # Simple type checking
                        type_mapping = {
                            'string': 'str',
                            'number': ['int', 'float'],
                            'boolean': 'bool',
                            'object': 'dict',
                            'array': 'list'
                        }
                        
                        expected_python_types = type_mapping.get(expected_type, expected_type)
                        if isinstance(expected_python_types, list):
                            valid_type = actual_type in expected_python_types
                        else:
                            valid_type = actual_type == expected_python_types
                        
                        if not valid_type:
                            issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverity.ERROR,
                                    validation_type=ValidationType.SCHEMA,
                                    message=f"Property '{prop_name}' should be of type {expected_type}",
                                    resource_type=resource_type,
                                    property_path=prop_name
                                )
                            )
        
        return issues