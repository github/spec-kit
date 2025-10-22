"""
Test utilities and helper functions for Bicep Generator tests.

This module provides common utilities used across multiple test modules.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock


def create_mock_analysis(project_name: str = "test-project") -> Dict[str, Any]:
    """
    Create a mock project analysis result.
    
    Args:
        project_name: Name of the project
        
    Returns:
        Mock analysis dictionary
    """
    return {
        "project_name": project_name,
        "language": "python",
        "framework": "fastapi",
        "resources": [
            {
                "resource_type": "Microsoft.Storage/storageAccounts",
                "name": f"{project_name}-storage",
                "api_version": "2023-01-01",
                "properties": {
                    "supportsHttpsTrafficOnly": True,
                    "minimumTlsVersion": "TLS1_2"
                },
                "sku": {"name": "Standard_LRS"},
                "location": "eastus"
            }
        ],
        "dependencies": [
            {
                "service_type": "storage",
                "confidence": 0.95,
                "evidence": ["azure-storage-blob package"]
            }
        ],
        "configuration": {
            "azure": {
                "region": "eastus",
                "environment": "dev"
            }
        }
    }


def create_mock_bicep_template(resource_type: str) -> str:
    """
    Create a mock Bicep template for a resource type.
    
    Args:
        resource_type: Azure resource type
        
    Returns:
        Bicep template string
    """
    templates = {
        "Microsoft.Storage/storageAccounts": """
param storageAccountName string
param location string = resourceGroup().location

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
  }
}

output storageAccountId string = storageAccount.id
""",
        "Microsoft.Web/sites": """
param webAppName string
param location string = resourceGroup().location

resource webApp 'Microsoft.Web/sites@2023-01-01' = {
  name: webAppName
  location: location
  properties: {
    httpsOnly: true
    siteConfig: {
      minTlsVersion: '1.2'
    }
  }
}

output webAppId string = webApp.id
"""
    }
    
    return templates.get(resource_type, "// Template not found")


def create_project_structure(base_dir: Path, project_type: str = "web") -> None:
    """
    Create a mock project directory structure.
    
    Args:
        base_dir: Base directory for the project
        project_type: Type of project (web, api, container)
    """
    if project_type == "web":
        # .NET web project
        (base_dir / "src").mkdir(parents=True, exist_ok=True)
        (base_dir / "src" / "MyWebApp").mkdir(exist_ok=True)
        
        appsettings = {
            "ConnectionStrings": {
                "DefaultConnection": "Server=myserver.database.windows.net;",
                "StorageConnection": "AccountName=mystorageaccount;"
            }
        }
        
        appsettings_file = base_dir / "src" / "MyWebApp" / "appsettings.json"
        appsettings_file.write_text(json.dumps(appsettings, indent=2))
        
    elif project_type == "api":
        # Python API project
        requirements = """
azure-identity==1.15.0
azure-storage-blob==12.19.0
fastapi==0.109.0
"""
        (base_dir / "requirements.txt").write_text(requirements)
        
    elif project_type == "container":
        # Container project
        dockerfile = """
FROM python:3.11-slim
WORKDIR /app
COPY . .
CMD ["python", "app.py"]
"""
        (base_dir / "Dockerfile").write_text(dockerfile)


def validate_bicep_syntax(template: str) -> List[str]:
    """
    Validate Bicep template syntax (mock implementation).
    
    Args:
        template: Bicep template string
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Basic syntax checks
    if "resource" not in template:
        errors.append("No resource definitions found")
    
    if "param" not in template and "var" not in template:
        errors.append("No parameters or variables defined")
    
    # Check for common issues
    if template.count("{") != template.count("}"):
        errors.append("Mismatched braces")
    
    if template.count("'") % 2 != 0:
        errors.append("Mismatched quotes")
    
    return errors


def extract_resources_from_template(template: str) -> List[Dict[str, Any]]:
    """
    Extract resource definitions from Bicep template (simplified).
    
    Args:
        template: Bicep template string
        
    Returns:
        List of resource dictionaries
    """
    resources = []
    
    # Simple pattern matching (not a full parser)
    lines = template.split('\n')
    current_resource = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("resource "):
            # Extract resource name and type
            parts = line.split("'")
            if len(parts) >= 2:
                resource_type = parts[1].split("@")[0]
                current_resource = {
                    "type": resource_type,
                    "properties": {}
                }
                resources.append(current_resource)
    
    return resources


def compare_templates(template1: str, template2: str) -> Dict[str, Any]:
    """
    Compare two Bicep templates and identify differences.
    
    Args:
        template1: First template
        template2: Second template
        
    Returns:
        Dictionary with comparison results
    """
    resources1 = extract_resources_from_template(template1)
    resources2 = extract_resources_from_template(template2)
    
    types1 = {r["type"] for r in resources1}
    types2 = {r["type"] for r in resources2}
    
    return {
        "added": list(types2 - types1),
        "removed": list(types1 - types2),
        "common": list(types1 & types2),
        "total_changes": len(types1) + len(types2) - 2 * len(types1 & types2)
    }


def calculate_template_complexity(template: str) -> int:
    """
    Calculate complexity score for a Bicep template.
    
    Args:
        template: Bicep template string
        
    Returns:
        Complexity score (higher = more complex)
    """
    complexity = 0
    
    # Count resources
    complexity += template.count("resource ") * 10
    
    # Count parameters
    complexity += template.count("param ") * 2
    
    # Count modules
    complexity += template.count("module ") * 15
    
    # Count conditional statements
    complexity += template.count("if ") * 5
    
    # Count loops
    complexity += template.count("for ") * 10
    
    return complexity


def generate_parameter_file(resources: List[Dict[str, Any]], environment: str) -> Dict[str, Any]:
    """
    Generate a parameter file for resources.
    
    Args:
        resources: List of resource specifications
        environment: Target environment (dev, staging, production)
        
    Returns:
        Parameter file dictionary
    """
    parameters = {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {}
    }
    
    for resource in resources:
        # Add name parameter
        param_name = f"{resource['name']}Name"
        parameters["parameters"][param_name] = {
            "value": f"{resource['name']}-{environment}"
        }
        
        # Add location parameter
        parameters["parameters"]["location"] = {
            "value": "eastus"
        }
    
    return parameters


def mock_azure_cli_response(command: str, success: bool = True) -> Dict[str, Any]:
    """
    Generate mock Azure CLI response.
    
    Args:
        command: CLI command
        success: Whether the command succeeded
        
    Returns:
        Mock response dictionary
    """
    if "deployment group create" in command:
        if success:
            return {
                "id": "/subscriptions/xxx/resourceGroups/test-rg/providers/Microsoft.Resources/deployments/test",
                "name": "test",
                "properties": {
                    "provisioningState": "Succeeded",
                    "outputs": {}
                }
            }
        else:
            return {
                "error": {
                    "code": "DeploymentFailed",
                    "message": "Deployment failed"
                }
            }
    
    elif "deployment group validate" in command:
        if success:
            return {
                "properties": {
                    "provisioningState": "Succeeded"
                }
            }
        else:
            return {
                "error": {
                    "code": "ValidationFailed",
                    "message": "Template validation failed"
                }
            }
    
    return {}


def create_test_fixtures(output_dir: Path) -> None:
    """
    Create test fixture files.
    
    Args:
        output_dir: Output directory for fixtures
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample templates
    templates_dir = output_dir / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    (templates_dir / "storage.bicep").write_text(
        create_mock_bicep_template("Microsoft.Storage/storageAccounts")
    )
    
    (templates_dir / "webapp.bicep").write_text(
        create_mock_bicep_template("Microsoft.Web/sites")
    )
    
    # Create sample parameters
    params_dir = output_dir / "parameters"
    params_dir.mkdir(exist_ok=True)
    
    for env in ["dev", "staging", "production"]:
        params = {
            "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
            "contentVersion": "1.0.0.0",
            "parameters": {
                "environment": {"value": env},
                "location": {"value": "eastus"}
            }
        }
        
        param_file = params_dir / f"{env}.parameters.json"
        param_file.write_text(json.dumps(params, indent=2))
    
    # Create sample analysis
    analysis = create_mock_analysis()
    analysis_file = output_dir / "analysis.json"
    analysis_file.write_text(json.dumps(analysis, indent=2))


def assert_valid_bicep_template(template: str) -> None:
    """
    Assert that a template is valid Bicep.
    
    Args:
        template: Bicep template string
        
    Raises:
        AssertionError: If template is invalid
    """
    errors = validate_bicep_syntax(template)
    assert len(errors) == 0, f"Template has syntax errors: {errors}"


def assert_resource_exists(template: str, resource_type: str) -> None:
    """
    Assert that a resource type exists in template.
    
    Args:
        template: Bicep template string
        resource_type: Azure resource type to check for
        
    Raises:
        AssertionError: If resource not found
    """
    resources = extract_resources_from_template(template)
    types = [r["type"] for r in resources]
    assert resource_type in types, f"Resource type {resource_type} not found in template"


def assert_has_parameter(template: str, parameter_name: str) -> None:
    """
    Assert that a parameter exists in template.
    
    Args:
        template: Bicep template string
        parameter_name: Parameter name to check for
        
    Raises:
        AssertionError: If parameter not found
    """
    assert f"param {parameter_name}" in template, f"Parameter {parameter_name} not found in template"


def assert_has_output(template: str, output_name: str) -> None:
    """
    Assert that an output exists in template.
    
    Args:
        template: Bicep template string
        output_name: Output name to check for
        
    Raises:
        AssertionError: If output not found
    """
    assert f"output {output_name}" in template, f"Output {output_name} not found in template"


def get_test_data_path(filename: str) -> Path:
    """
    Get path to test data file.
    
    Args:
        filename: Name of test data file
        
    Returns:
        Path to test data file
    """
    return Path(__file__).parent / "test_data" / filename


def load_test_data(filename: str) -> Dict[str, Any]:
    """
    Load test data from JSON file.
    
    Args:
        filename: Name of test data file
        
    Returns:
        Loaded test data
    """
    file_path = get_test_data_path(filename)
    if file_path.exists():
        return json.loads(file_path.read_text())
    return {}
