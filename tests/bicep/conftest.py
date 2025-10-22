"""
Pytest configuration and fixtures for Bicep Generator tests.

This module provides shared fixtures and test configuration for all Bicep Generator tests.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from rich.console import Console


# ============================================================================
# Test Configuration
# ============================================================================

@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Get the test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Get the fixtures directory."""
    return Path(__file__).parent / "fixtures"


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================

@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory for generated templates."""
    output_dir = tmp_path / "bicep_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


# ============================================================================
# Sample Project Fixtures
# ============================================================================

@pytest.fixture
def sample_web_project(temp_project_dir: Path) -> Path:
    """Create a sample web application project structure."""
    # Create directory structure
    (temp_project_dir / "src").mkdir()
    (temp_project_dir / "src" / "MyWebApp").mkdir()
    
    # Create appsettings.json with Azure dependencies
    appsettings = {
        "Logging": {
            "LogLevel": {
                "Default": "Information"
            }
        },
        "ConnectionStrings": {
            "DefaultConnection": "Server=tcp:myserver.database.windows.net,1433;Database=mydb;",
            "StorageConnection": "DefaultEndpointsProtocol=https;AccountName=mystorageaccount;"
        },
        "Azure": {
            "KeyVault": {
                "VaultUri": "https://mykeyvault.vault.azure.net/"
            }
        }
    }
    
    appsettings_path = temp_project_dir / "src" / "MyWebApp" / "appsettings.json"
    appsettings_path.write_text(json.dumps(appsettings, indent=2))
    
    # Create Program.cs with Azure SDK usage
    program_cs = """
using Microsoft.AspNetCore.Builder;
using Azure.Identity;
using Azure.Storage.Blobs;
using Azure.Security.KeyVault.Secrets;

var builder = WebApplication.CreateBuilder(args);

// Add Azure services
builder.Services.AddAzureClients(clientBuilder =>
{
    clientBuilder.AddBlobServiceClient(builder.Configuration.GetConnectionString("StorageConnection"));
    clientBuilder.AddSecretClient(new Uri(builder.Configuration["Azure:KeyVault:VaultUri"]));
});

var app = builder.Build();
app.Run();
"""
    
    program_path = temp_project_dir / "src" / "MyWebApp" / "Program.cs"
    program_path.write_text(program_cs)
    
    # Create .csproj file
    csproj = """<?xml version="1.0" encoding="utf-8"?>
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Azure.Identity" Version="1.10.0" />
    <PackageReference Include="Azure.Storage.Blobs" Version="12.18.0" />
    <PackageReference Include="Azure.Security.KeyVault.Secrets" Version="4.5.0" />
  </ItemGroup>
</Project>
"""
    
    csproj_path = temp_project_dir / "src" / "MyWebApp" / "MyWebApp.csproj"
    csproj_path.write_text(csproj)
    
    return temp_project_dir


@pytest.fixture
def sample_python_project(temp_project_dir: Path) -> Path:
    """Create a sample Python project structure."""
    # Create directory structure
    (temp_project_dir / "src").mkdir()
    
    # Create requirements.txt with Azure dependencies
    requirements = """
azure-identity==1.15.0
azure-storage-blob==12.19.0
azure-keyvault-secrets==4.7.0
azure-cosmos==4.5.1
fastapi==0.109.0
uvicorn==0.27.0
"""
    
    req_path = temp_project_dir / "requirements.txt"
    req_path.write_text(requirements)
    
    # Create main.py with Azure SDK usage
    main_py = """
from fastapi import FastAPI
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.keyvault.secrets import SecretClient
from azure.cosmos import CosmosClient

app = FastAPI()

# Initialize Azure clients
credential = DefaultAzureCredential()
blob_service = BlobServiceClient(account_url="https://mystorageaccount.blob.core.windows.net", credential=credential)
secret_client = SecretClient(vault_url="https://mykeyvault.vault.azure.net/", credential=credential)
cosmos_client = CosmosClient(url="https://mycosmosdb.documents.azure.com:443/", credential=credential)

@app.get("/")
async def root():
    return {"message": "Hello Azure"}
"""
    
    main_path = temp_project_dir / "src" / "main.py"
    main_path.write_text(main_py)
    
    return temp_project_dir


@pytest.fixture
def sample_container_project(temp_project_dir: Path) -> Path:
    """Create a sample containerized project structure."""
    # Create Dockerfile
    dockerfile = """
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
"""
    
    dockerfile_path = temp_project_dir / "Dockerfile"
    dockerfile_path.write_text(dockerfile)
    
    # Create docker-compose.yml with Azure references
    docker_compose = """
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8080:8080"
    environment:
      - AZURE_STORAGE_ACCOUNT=mystorageaccount
      - AZURE_KEY_VAULT_URL=https://mykeyvault.vault.azure.net/
"""
    
    compose_path = temp_project_dir / "docker-compose.yml"
    compose_path.write_text(docker_compose)
    
    return temp_project_dir


# ============================================================================
# Mock Azure MCP Server Fixtures
# ============================================================================

@pytest.fixture
def mock_mcp_schema_response() -> Dict[str, Any]:
    """Provide a mock Azure resource schema response."""
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Resource name"
            },
            "location": {
                "type": "string",
                "description": "Resource location"
            },
            "sku": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "tier": {"type": "string"}
                }
            },
            "properties": {
                "type": "object",
                "properties": {
                    "publicNetworkAccess": {
                        "type": "string",
                        "enum": ["Enabled", "Disabled"]
                    }
                }
            }
        },
        "required": ["name", "location", "sku"]
    }


@pytest.fixture
def mock_mcp_client(mock_mcp_schema_response: Dict[str, Any]):
    """Provide a mock MCP client for testing."""
    mock_client = AsyncMock()
    
    # Mock schema retrieval
    async def mock_get_schema(resource_type: str, api_version: str):
        return mock_mcp_schema_response
    
    mock_client.get_bicep_schema = mock_get_schema
    
    # Mock best practices
    async def mock_get_best_practices(resource_type: str):
        return [
            "Enable HTTPS only",
            "Use managed identity",
            "Enable diagnostic logging"
        ]
    
    mock_client.get_best_practices = mock_get_best_practices
    
    # Mock resource providers
    async def mock_get_providers():
        return [
            "Microsoft.Storage",
            "Microsoft.Web",
            "Microsoft.KeyVault",
            "Microsoft.Sql",
            "Microsoft.DocumentDB"
        ]
    
    mock_client.get_resource_providers = mock_get_providers
    
    return mock_client


# ============================================================================
# Mock Azure CLI Fixtures
# ============================================================================

@pytest.fixture
def mock_azure_cli():
    """Provide mock Azure CLI responses."""
    mock_cli = Mock()
    
    # Mock successful deployment
    mock_cli.deployment_create = Mock(return_value={
        "id": "/subscriptions/xxx/resourceGroups/test-rg/providers/Microsoft.Resources/deployments/test",
        "name": "test",
        "properties": {
            "provisioningState": "Succeeded",
            "outputs": {}
        }
    })
    
    # Mock validation
    mock_cli.deployment_validate = Mock(return_value={
        "error": None,
        "properties": {
            "provisioningState": "Succeeded"
        }
    })
    
    # Mock resource group
    mock_cli.resource_group_show = Mock(return_value={
        "id": "/subscriptions/xxx/resourceGroups/test-rg",
        "name": "test-rg",
        "location": "eastus"
    })
    
    return mock_cli


# ============================================================================
# Analysis Fixtures
# ============================================================================

@pytest.fixture
def sample_project_analysis() -> Dict[str, Any]:
    """Provide a sample project analysis result."""
    return {
        "project_name": "test-project",
        "language": "python",
        "framework": "fastapi",
        "resources": [
            {
                "resource_type": "Microsoft.Storage/storageAccounts",
                "name": "teststorageaccount",
                "api_version": "2023-01-01",
                "properties": {
                    "supportsHttpsTrafficOnly": True,
                    "minimumTlsVersion": "TLS1_2"
                },
                "sku": {
                    "name": "Standard_LRS"
                },
                "location": "eastus"
            },
            {
                "resource_type": "Microsoft.Web/sites",
                "name": "testwebapp",
                "api_version": "2023-01-01",
                "properties": {
                    "httpsOnly": True,
                    "siteConfig": {
                        "minTlsVersion": "1.2"
                    }
                },
                "location": "eastus"
            },
            {
                "resource_type": "Microsoft.KeyVault/vaults",
                "name": "testkeyvault",
                "api_version": "2023-02-01",
                "properties": {
                    "enableRbacAuthorization": True,
                    "enableSoftDelete": True
                },
                "location": "eastus"
            }
        ],
        "dependencies": [
            {
                "service_type": "storage",
                "confidence": 0.95,
                "evidence": ["Azure.Storage.Blobs package", "BlobServiceClient usage"]
            },
            {
                "service_type": "webapp",
                "confidence": 0.90,
                "evidence": ["FastAPI framework", "HTTP endpoints"]
            },
            {
                "service_type": "keyvault",
                "confidence": 0.85,
                "evidence": ["Azure.KeyVault.Secrets package", "SecretClient usage"]
            }
        ],
        "configuration": {
            "azure": {
                "region": "eastus",
                "environment": "dev"
            }
        }
    }


# ============================================================================
# Template Fixtures
# ============================================================================

@pytest.fixture
def sample_bicep_template() -> str:
    """Provide a sample Bicep template."""
    return """
param location string = resourceGroup().location
param storageAccountName string

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
output storageAccountName string = storageAccount.name
"""


@pytest.fixture
def sample_parameters_file() -> Dict[str, Any]:
    """Provide a sample parameters file."""
    return {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {
            "location": {
                "value": "eastus"
            },
            "storageAccountName": {
                "value": "teststorageaccount123"
            }
        }
    }


# ============================================================================
# Console Fixture
# ============================================================================

@pytest.fixture
def mock_console() -> Console:
    """Provide a mock Rich console for testing."""
    # Create console without color output for testing
    return Console(force_terminal=False, color_system=None, width=80)


# ============================================================================
# Async Utilities
# ============================================================================

@pytest.fixture
def event_loop_policy():
    """Set event loop policy for async tests."""
    import asyncio
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# ============================================================================
# Test Markers
# ============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that may require external services"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take a long time to run"
    )
    config.addinivalue_line(
        "markers", "azure: Tests that require Azure credentials"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests of complete workflows"
    )
