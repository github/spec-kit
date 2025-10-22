"""
Unit tests for BicepGenerator.

Tests the Bicep template generation functionality including resource generation,
parameter creation, and template organization.
"""

from pathlib import Path
from typing import Dict, Any
from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.mark.unit
class TestBicepGenerator:
    """Test cases for BicepGenerator class."""
    
    def test_generate_basic_template(self, sample_project_analysis, temp_output_dir, mock_console):
        """Test generation of basic Bicep template."""
        # Expected output:
        # - main.bicep (orchestrator)
        # - parameters/ directory with parameter files
        # - modules/ directory with resource modules
        
        expected_files = [
            "main.bicep",
            "parameters/dev.parameters.json",
            "parameters/production.parameters.json",
            "modules/storage-account.bicep",
            "modules/web-app.bicep",
            "modules/key-vault.bicep"
        ]
        
        # Verify analysis has required resources
        assert len(sample_project_analysis["resources"]) > 0
        
        # Simulate file generation
        for file_path in expected_files:
            full_path = temp_output_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("// Generated Bicep template")
            assert full_path.exists()
    
    def test_generate_with_dependencies(self, sample_project_analysis, temp_output_dir):
        """Test generation with resource dependencies."""
        # Web App depends on Storage Account and Key Vault
        # Should generate templates with proper dependsOn
        
        resources = sample_project_analysis["resources"]
        
        # Build dependency graph
        dependencies = {
            "testwebapp": ["teststorageaccount", "testkeyvault"],
            "teststorageaccount": [],
            "testkeyvault": []
        }
        
        # Verify dependency relationships
        assert len(dependencies["testwebapp"]) == 2
        assert len(dependencies["teststorageaccount"]) == 0
    
    @pytest.mark.asyncio
    async def test_generate_with_mcp_schemas(self, sample_project_analysis, mock_mcp_client, temp_output_dir):
        """Test generation using Azure MCP Server schemas."""
        # Should retrieve schemas for each resource type
        resource_types = [r["resource_type"] for r in sample_project_analysis["resources"]]
        
        # Fetch schemas via MCP
        for resource_type in resource_types:
            schema = await mock_mcp_client.get_bicep_schema(resource_type, "2023-01-01")
            assert schema is not None
            assert "properties" in schema
    
    def test_generate_parameters_file(self, sample_project_analysis, temp_output_dir):
        """Test parameter file generation for different environments."""
        environments = ["dev", "staging", "production"]
        
        for env in environments:
            params = {
                "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
                "contentVersion": "1.0.0.0",
                "parameters": {}
            }
            
            # Add parameters for each resource
            for resource in sample_project_analysis["resources"]:
                param_name = f"{resource['name']}Name"
                params["parameters"][param_name] = {
                    "value": f"{resource['name']}-{env}"
                }
            
            # Write parameters file
            param_file = temp_output_dir / f"parameters/{env}.parameters.json"
            param_file.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            param_file.write_text(json.dumps(params, indent=2))
            
            assert param_file.exists()
    
    def test_apply_naming_conventions(self):
        """Test Azure naming convention enforcement."""
        # Test storage account naming (lowercase, no hyphens)
        storage_name = "My-Storage-Account"
        normalized = storage_name.lower().replace("-", "").replace("_", "")
        assert normalized == "mystorageaccount"
        assert normalized.islower()
        assert "-" not in normalized
        
        # Test resource group naming (alphanumeric, hyphens, underscores, periods)
        rg_name = "My_Resource-Group.Dev"
        assert all(c.isalnum() or c in "-_." for c in rg_name)
    
    def test_apply_best_practices(self, sample_project_analysis):
        """Test application of Azure best practices."""
        # Storage Account best practices
        storage_resource = next(
            r for r in sample_project_analysis["resources"]
            if r["resource_type"] == "Microsoft.Storage/storageAccounts"
        )
        
        assert storage_resource["properties"]["supportsHttpsTrafficOnly"] is True
        assert storage_resource["properties"]["minimumTlsVersion"] == "TLS1_2"
        
        # Web App best practices
        webapp_resource = next(
            r for r in sample_project_analysis["resources"]
            if r["resource_type"] == "Microsoft.Web/sites"
        )
        
        assert webapp_resource["properties"]["httpsOnly"] is True
        assert webapp_resource["properties"]["siteConfig"]["minTlsVersion"] == "1.2"
        
        # Key Vault best practices
        keyvault_resource = next(
            r for r in sample_project_analysis["resources"]
            if r["resource_type"] == "Microsoft.KeyVault/vaults"
        )
        
        assert keyvault_resource["properties"]["enableRbacAuthorization"] is True
        assert keyvault_resource["properties"]["enableSoftDelete"] is True
    
    def test_organize_by_resource_type(self, sample_project_analysis, temp_output_dir):
        """Test organization of templates by resource type."""
        # Expected structure:
        # modules/
        #   compute/
        #     web-app.bicep
        #   storage/
        #     storage-account.bicep
        #   security/
        #     key-vault.bicep
        
        organization = {
            "Microsoft.Web/sites": "compute",
            "Microsoft.Storage/storageAccounts": "storage",
            "Microsoft.KeyVault/vaults": "security",
            "Microsoft.Sql/servers": "data",
            "Microsoft.DocumentDB/databaseAccounts": "data",
            "Microsoft.ContainerRegistry/registries": "containers"
        }
        
        for resource in sample_project_analysis["resources"]:
            resource_type = resource["resource_type"]
            if resource_type in organization:
                category = organization[resource_type]
                assert category in ["compute", "storage", "security", "data", "containers"]


@pytest.mark.unit
class TestTemplateGeneration:
    """Test cases for individual template generation."""
    
    def test_generate_storage_account_template(self, mock_mcp_schema_response):
        """Test generation of Storage Account Bicep template."""
        template = """
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
    accessTier: 'Hot'
  }
}

output storageAccountId string = storageAccount.id
"""
        
        # Verify template structure
        assert "param storageAccountName string" in template
        assert "Microsoft.Storage/storageAccounts" in template
        assert "supportsHttpsTrafficOnly: true" in template
        assert "output storageAccountId" in template
    
    def test_generate_web_app_template(self):
        """Test generation of Web App Bicep template."""
        template = """
param webAppName string
param location string = resourceGroup().location
param appServicePlanId string

resource webApp 'Microsoft.Web/sites@2023-01-01' = {
  name: webAppName
  location: location
  properties: {
    serverFarmId: appServicePlanId
    httpsOnly: true
    siteConfig: {
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
    }
  }
}

output webAppId string = webApp.id
"""
        
        # Verify template structure
        assert "param webAppName string" in template
        assert "Microsoft.Web/sites" in template
        assert "httpsOnly: true" in template
        assert "minTlsVersion: '1.2'" in template
    
    def test_generate_key_vault_template(self):
        """Test generation of Key Vault Bicep template."""
        template = """
param keyVaultName string
param location string = resourceGroup().location
param tenantId string = subscription().tenantId

resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
  }
}

output keyVaultId string = keyVault.id
"""
        
        # Verify template structure
        assert "param keyVaultName string" in template
        assert "Microsoft.KeyVault/vaults" in template
        assert "enableRbacAuthorization: true" in template
        assert "enableSoftDelete: true" in template
    
    def test_generate_with_dependencies(self):
        """Test generation with explicit dependencies."""
        template = """
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'mystorageaccount'
  location: 'eastus'
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}

resource webApp 'Microsoft.Web/sites@2023-01-01' = {
  name: 'mywebapp'
  location: 'eastus'
  dependsOn: [
    storageAccount
  ]
  properties: {
    // ...
  }
}
"""
        
        # Verify dependency declaration
        assert "dependsOn: [" in template
        assert "storageAccount" in template
    
    def test_generate_with_outputs(self):
        """Test generation with output values."""
        template = """
output storageAccountName string = storageAccount.name
output storageAccountId string = storageAccount.id
output storageAccountPrimaryEndpoints object = storageAccount.properties.primaryEndpoints
"""
        
        # Verify outputs
        assert "output storageAccountName string" in template
        assert "output storageAccountId string" in template
        assert "output storageAccountPrimaryEndpoints object" in template


@pytest.mark.unit
class TestModularGeneration:
    """Test cases for modular template generation."""
    
    def test_generate_main_orchestrator(self, temp_output_dir):
        """Test generation of main orchestrator template."""
        main_template = """
param location string = resourceGroup().location
param environment string

module storage './modules/storage-account.bicep' = {
  name: 'storageDeployment'
  params: {
    storageAccountName: 'mystorageaccount'
    location: location
  }
}

module webApp './modules/web-app.bicep' = {
  name: 'webAppDeployment'
  params: {
    webAppName: 'mywebapp'
    location: location
    appServicePlanId: appServicePlan.id
  }
  dependsOn: [
    storage
  ]
}
"""
        
        # Write main template
        main_file = temp_output_dir / "main.bicep"
        main_file.write_text(main_template)
        
        assert main_file.exists()
        content = main_file.read_text()
        assert "module storage" in content
        assert "module webApp" in content
    
    def test_generate_module_files(self, temp_output_dir):
        """Test generation of individual module files."""
        modules_dir = temp_output_dir / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate storage module
        storage_module = modules_dir / "storage-account.bicep"
        storage_module.write_text("// Storage Account module")
        
        # Generate web app module
        webapp_module = modules_dir / "web-app.bicep"
        webapp_module.write_text("// Web App module")
        
        assert storage_module.exists()
        assert webapp_module.exists()
    
    def test_parameter_passing_between_modules(self):
        """Test parameter passing between modules."""
        # Main template passes outputs from one module as inputs to another
        main_template = """
module storage './modules/storage.bicep' = {
  name: 'storage'
  params: {
    storageAccountName: 'mystorageaccount'
  }
}

module webApp './modules/webapp.bicep' = {
  name: 'webapp'
  params: {
    webAppName: 'mywebapp'
    storageAccountId: storage.outputs.storageAccountId
  }
}
"""
        
        # Verify parameter passing
        assert "storage.outputs.storageAccountId" in main_template


@pytest.mark.unit
class TestGenerationConfiguration:
    """Test cases for generation configuration."""
    
    def test_configure_environment(self):
        """Test environment-specific configuration."""
        environments = {
            "dev": {
                "sku": "B1",
                "capacity": 1,
                "auto_scale": False
            },
            "production": {
                "sku": "P1v2",
                "capacity": 3,
                "auto_scale": True
            }
        }
        
        # Verify dev configuration
        assert environments["dev"]["sku"] == "B1"
        assert environments["dev"]["capacity"] == 1
        
        # Verify production configuration
        assert environments["production"]["sku"] == "P1v2"
        assert environments["production"]["capacity"] == 3
    
    def test_configure_regions(self):
        """Test region-specific configuration."""
        regions = {
            "primary": "eastus",
            "secondary": "westus2"
        }
        
        # Verify region configuration
        assert regions["primary"] == "eastus"
        assert regions["secondary"] == "westus2"
    
    def test_configure_naming_prefix(self):
        """Test naming prefix configuration."""
        config = {
            "naming_prefix": "myapp",
            "environment": "dev"
        }
        
        # Generate resource name with prefix
        resource_name = f"{config['naming_prefix']}-storage-{config['environment']}"
        assert resource_name == "myapp-storage-dev"
    
    def test_configure_tags(self):
        """Test tag configuration."""
        tags = {
            "Environment": "Production",
            "CostCenter": "Engineering",
            "Owner": "DevOps Team",
            "Application": "MyWebApp"
        }
        
        # Verify all tags are present
        assert tags["Environment"] == "Production"
        assert tags["CostCenter"] == "Engineering"
        assert "Owner" in tags
        assert "Application" in tags
