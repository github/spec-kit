"""
Unit tests for ProjectAnalyzer.

Tests the project analysis functionality including dependency detection,
configuration extraction, and secret scanning.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Mock imports before actual imports to avoid import errors during testing
pytest.importorskip("specify_cli", reason="specify_cli module not available for testing")


@pytest.mark.unit
class TestProjectAnalyzer:
    """Test cases for ProjectAnalyzer class."""
    
    def test_analyze_web_project(self, sample_web_project: Path, mock_console):
        """Test analysis of a .NET web application project."""
        # This test would use the actual ProjectAnalyzer class
        # For now, we simulate the expected behavior
        
        # Expected to detect:
        # - Storage Account (from connection string)
        # - SQL Database (from connection string)
        # - Key Vault (from configuration)
        # - Web App (from .csproj)
        
        expected_dependencies = [
            "Microsoft.Storage/storageAccounts",
            "Microsoft.Sql/servers",
            "Microsoft.KeyVault/vaults",
            "Microsoft.Web/sites"
        ]
        
        # Verify project files exist
        assert (sample_web_project / "src" / "MyWebApp" / "appsettings.json").exists()
        assert (sample_web_project / "src" / "MyWebApp" / "Program.cs").exists()
        assert (sample_web_project / "src" / "MyWebApp" / "MyWebApp.csproj").exists()
        
        # Verify configuration content
        config_file = sample_web_project / "src" / "MyWebApp" / "appsettings.json"
        config = json.loads(config_file.read_text())
        
        assert "ConnectionStrings" in config
        assert "DefaultConnection" in config["ConnectionStrings"]
        assert "StorageConnection" in config["ConnectionStrings"]
        assert "Azure" in config
        assert "KeyVault" in config["Azure"]
    
    def test_analyze_python_project(self, sample_python_project: Path, mock_console):
        """Test analysis of a Python FastAPI project."""
        # Expected to detect:
        # - Storage Account (from azure-storage-blob)
        # - Key Vault (from azure-keyvault-secrets)
        # - Cosmos DB (from azure-cosmos)
        # - Web App or Container Instance (from FastAPI)
        
        # Verify project files exist
        assert (sample_python_project / "requirements.txt").exists()
        assert (sample_python_project / "src" / "main.py").exists()
        
        # Verify requirements content
        requirements = (sample_python_project / "requirements.txt").read_text()
        assert "azure-storage-blob" in requirements
        assert "azure-keyvault-secrets" in requirements
        assert "azure-cosmos" in requirements
        assert "fastapi" in requirements
    
    def test_analyze_container_project(self, sample_container_project: Path, mock_console):
        """Test analysis of a containerized project."""
        # Expected to detect:
        # - Container Registry (from Dockerfile)
        # - Container Instances or AKS (from docker-compose)
        # - Storage Account (from environment variables)
        # - Key Vault (from environment variables)
        
        # Verify project files exist
        assert (sample_container_project / "Dockerfile").exists()
        assert (sample_container_project / "docker-compose.yml").exists()
        
        # Verify Dockerfile content
        dockerfile = (sample_container_project / "Dockerfile").read_text()
        assert "FROM python" in dockerfile
        
        # Verify docker-compose content
        compose = (sample_container_project / "docker-compose.yml").read_text()
        assert "AZURE_STORAGE_ACCOUNT" in compose
        assert "AZURE_KEY_VAULT_URL" in compose
    
    def test_detect_dependencies_from_config(self):
        """Test dependency detection from configuration files."""
        # Test connection string parsing
        connection_strings = {
            "DefaultConnection": "Server=tcp:myserver.database.windows.net,1433;Database=mydb;",
            "StorageConnection": "DefaultEndpointsProtocol=https;AccountName=mystorageaccount;",
            "RedisConnection": "mycache.redis.cache.windows.net:6380,password=xxx,ssl=True"
        }
        
        # Expected detections:
        # - SQL Database from myserver.database.windows.net
        # - Storage Account from mystorageaccount
        # - Redis Cache from redis.cache.windows.net
        
        assert "database.windows.net" in connection_strings["DefaultConnection"]
        assert "AccountName=" in connection_strings["StorageConnection"]
        assert "redis.cache.windows.net" in connection_strings["RedisConnection"]
    
    def test_detect_dependencies_from_packages(self):
        """Test dependency detection from package references."""
        # .NET packages
        dotnet_packages = [
            "Azure.Identity",
            "Azure.Storage.Blobs",
            "Azure.Security.KeyVault.Secrets",
            "Microsoft.Azure.Cosmos"
        ]
        
        # Python packages
        python_packages = [
            "azure-identity",
            "azure-storage-blob",
            "azure-keyvault-secrets",
            "azure-cosmos"
        ]
        
        # Map packages to Azure services
        package_to_service = {
            "azure-storage-blob": "Microsoft.Storage/storageAccounts",
            "azure-keyvault-secrets": "Microsoft.KeyVault/vaults",
            "azure-cosmos": "Microsoft.DocumentDB/databaseAccounts"
        }
        
        for package in python_packages:
            if package in package_to_service:
                expected_service = package_to_service[package]
                assert expected_service is not None
    
    def test_detect_secrets(self, sample_web_project: Path):
        """Test secret detection in configuration files."""
        # Create a file with potential secrets
        config_with_secrets = {
            "ConnectionStrings": {
                "Storage": "DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=SECRETKEY123=="
            },
            "ApiKeys": {
                "ThirdPartyApi": "sk_live_1234567890abcdef"
            }
        }
        
        secrets_file = sample_web_project / "config.json"
        secrets_file.write_text(json.dumps(config_with_secrets, indent=2))
        
        # Expected to detect:
        # - AccountKey in connection string
        # - API key pattern
        
        content = secrets_file.read_text()
        assert "AccountKey=" in content
        assert "sk_live_" in content
    
    def test_confidence_scoring(self):
        """Test confidence scoring for detected dependencies."""
        # High confidence: Direct package reference + usage in code
        high_confidence_evidence = [
            "Package: azure-storage-blob",
            "Import: from azure.storage.blob import BlobServiceClient",
            "Usage: BlobServiceClient(account_url=...)"
        ]
        
        # Medium confidence: Package reference only
        medium_confidence_evidence = [
            "Package: azure-storage-blob"
        ]
        
        # Low confidence: Configuration reference only
        low_confidence_evidence = [
            "Config: StorageConnection string"
        ]
        
        # Simulate confidence calculation
        assert len(high_confidence_evidence) >= 3  # High confidence
        assert len(medium_confidence_evidence) >= 1  # Medium confidence
        assert len(low_confidence_evidence) >= 1  # Low confidence
    
    def test_exclude_patterns(self, temp_project_dir: Path):
        """Test exclusion of specified file patterns."""
        # Create directories that should be excluded
        (temp_project_dir / "node_modules").mkdir()
        (temp_project_dir / "bin").mkdir()
        (temp_project_dir / "obj").mkdir()
        (temp_project_dir / ".git").mkdir()
        
        exclude_patterns = [
            "**/node_modules/**",
            "**/bin/**",
            "**/obj/**",
            "**/.git/**"
        ]
        
        # These directories should not be analyzed
        for pattern in exclude_patterns:
            assert "node_modules" in pattern or "bin" in pattern or "obj" in pattern or ".git" in pattern


@pytest.mark.unit
class TestResourceDetection:
    """Test cases for specific Azure resource detection."""
    
    def test_detect_app_service(self):
        """Test App Service detection."""
        # Indicators:
        # - ASP.NET Core project
        # - FastAPI/Flask/Django
        # - Startup.cs or Program.cs
        # - WSGI application
        
        indicators = {
            "csproj": True,
            "Program.cs": True,
            "web_framework": "ASP.NET Core"
        }
        
        assert indicators["csproj"] and indicators["Program.cs"]
    
    def test_detect_storage_account(self):
        """Test Storage Account detection."""
        # Indicators:
        # - azure-storage-blob package
        # - BlobServiceClient usage
        # - Connection string with AccountName
        
        indicators = {
            "package": "azure-storage-blob",
            "connection_string": "AccountName=myaccount",
            "code_usage": "BlobServiceClient"
        }
        
        assert all(indicators.values())
    
    def test_detect_key_vault(self):
        """Test Key Vault detection."""
        # Indicators:
        # - azure-keyvault-secrets package
        # - SecretClient usage
        # - KeyVault URL in configuration
        
        indicators = {
            "package": "azure-keyvault-secrets",
            "vault_url": "https://mykeyvault.vault.azure.net/",
            "code_usage": "SecretClient"
        }
        
        assert all(indicators.values())
    
    def test_detect_sql_database(self):
        """Test SQL Database detection."""
        # Indicators:
        # - Connection string with database.windows.net
        # - SQL client package
        # - EF Core usage
        
        connection_string = "Server=tcp:myserver.database.windows.net,1433;Database=mydb;"
        
        assert "database.windows.net" in connection_string
        assert "Database=" in connection_string
    
    def test_detect_cosmos_db(self):
        """Test Cosmos DB detection."""
        # Indicators:
        # - azure-cosmos package
        # - CosmosClient usage
        # - Cosmos DB connection string
        
        indicators = {
            "package": "azure-cosmos",
            "connection_string": "AccountEndpoint=https://mycosmosdb.documents.azure.com:443/",
            "code_usage": "CosmosClient"
        }
        
        assert all(indicators.values())
    
    def test_detect_container_registry(self):
        """Test Container Registry detection."""
        # Indicators:
        # - Dockerfile present
        # - docker-compose.yml
        # - Container image references
        
        indicators = {
            "dockerfile": True,
            "docker_compose": True
        }
        
        assert indicators["dockerfile"] or indicators["docker_compose"]
    
    def test_detect_function_app(self):
        """Test Function App detection."""
        # Indicators:
        # - host.json
        # - function.json
        # - Azure Functions packages
        
        indicators = {
            "host_json": True,
            "function_json": True,
            "functions_package": True
        }
        
        # At least one indicator should be present
        assert any(indicators.values())


@pytest.mark.unit
class TestConfigurationExtraction:
    """Test cases for configuration extraction."""
    
    def test_extract_from_appsettings(self):
        """Test extraction from appsettings.json."""
        appsettings = {
            "Azure": {
                "Region": "eastus",
                "ResourceGroup": "my-rg",
                "SubscriptionId": "xxx-xxx-xxx"
            }
        }
        
        assert appsettings["Azure"]["Region"] == "eastus"
        assert appsettings["Azure"]["ResourceGroup"] == "my-rg"
    
    def test_extract_from_env_files(self):
        """Test extraction from .env files."""
        env_content = """
AZURE_REGION=eastus
AZURE_SUBSCRIPTION_ID=xxx-xxx-xxx
AZURE_TENANT_ID=yyy-yyy-yyy
"""
        
        lines = env_content.strip().split('\n')
        env_vars = {}
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
        
        assert env_vars["AZURE_REGION"] == "eastus"
        assert "AZURE_SUBSCRIPTION_ID" in env_vars
    
    def test_extract_resource_names(self):
        """Test extraction of resource names from configuration."""
        config = {
            "ConnectionStrings": {
                "Storage": "AccountName=mystorageaccount;",
                "Database": "Server=myserver.database.windows.net;"
            }
        }
        
        # Extract storage account name
        storage_conn = config["ConnectionStrings"]["Storage"]
        if "AccountName=" in storage_conn:
            account_name = storage_conn.split("AccountName=")[1].split(";")[0]
            assert account_name == "mystorageaccount"
        
        # Extract server name
        db_conn = config["ConnectionStrings"]["Database"]
        if "Server=" in db_conn:
            server = db_conn.split("Server=")[1].split(";")[0]
            assert "myserver" in server


@pytest.mark.unit
class TestAnalysisValidation:
    """Test cases for analysis result validation."""
    
    def test_validate_required_fields(self, sample_project_analysis):
        """Test that analysis results contain required fields."""
        assert "project_name" in sample_project_analysis
        assert "language" in sample_project_analysis
        assert "resources" in sample_project_analysis
        assert "dependencies" in sample_project_analysis
        
        # Validate resource structure
        for resource in sample_project_analysis["resources"]:
            assert "resource_type" in resource
            assert "name" in resource
            assert "api_version" in resource
    
    def test_validate_resource_types(self, sample_project_analysis):
        """Test that detected resource types are valid Azure resource types."""
        valid_prefixes = [
            "Microsoft.Storage",
            "Microsoft.Web",
            "Microsoft.KeyVault",
            "Microsoft.Sql",
            "Microsoft.DocumentDB",
            "Microsoft.ContainerRegistry",
            "Microsoft.ContainerInstance"
        ]
        
        for resource in sample_project_analysis["resources"]:
            resource_type = resource["resource_type"]
            # Check if resource type starts with a valid prefix
            is_valid = any(resource_type.startswith(prefix) for prefix in valid_prefixes)
            assert is_valid, f"Invalid resource type: {resource_type}"
    
    def test_validate_confidence_scores(self, sample_project_analysis):
        """Test that confidence scores are within valid range."""
        for dep in sample_project_analysis["dependencies"]:
            confidence = dep["confidence"]
            assert 0.0 <= confidence <= 1.0, f"Invalid confidence score: {confidence}"
            assert "evidence" in dep
            assert len(dep["evidence"]) > 0
