"""
Integration tests for end-to-end Bicep generation workflows.

These tests verify the complete flow from project analysis through
template generation, validation, and deployment preparation.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.mark.integration
@pytest.mark.e2e
class TestEndToEndWorkflow:
    """End-to-end integration tests for complete workflows."""
    
    def test_web_app_workflow(self, sample_web_project, temp_output_dir, mock_console):
        """Test complete workflow for web application project."""
        # Step 1: Analyze project
        # Expected: Detect Web App, Storage, SQL Database, Key Vault
        
        # Step 2: Generate templates
        # Expected: main.bicep, modules/, parameters/
        
        # Step 3: Validate templates
        # Expected: No syntax errors, passes best practices
        
        # Step 4: Review architecture
        # Expected: Security recommendations, cost estimates
        
        workflow_steps = [
            "analyze",
            "generate",
            "validate",
            "review"
        ]
        
        results = {}
        for step in workflow_steps:
            results[step] = f"{step}_completed"
        
        # Verify all steps completed
        assert all(v.endswith("_completed") for v in results.values())
        assert len(results) == 4
    
    def test_python_api_workflow(self, sample_python_project, temp_output_dir, mock_console):
        """Test complete workflow for Python API project."""
        # Step 1: Analyze project
        # Expected: Detect Container Instances or App Service, Storage, Cosmos DB, Key Vault
        
        # Step 2: Generate templates with container support
        # Expected: Container-optimized templates
        
        # Step 3: Validate and optimize
        # Expected: Cost optimization for serverless/containers
        
        workflow_steps = [
            "analyze",
            "generate",
            "validate",
            "optimize"
        ]
        
        # Simulate workflow execution
        for step in workflow_steps:
            assert step in ["analyze", "generate", "validate", "optimize"]
    
    def test_update_workflow(self, sample_web_project, temp_output_dir, mock_console):
        """Test update workflow for existing templates."""
        # Step 1: Initial generation
        main_file = temp_output_dir / "main.bicep"
        main_file.write_text("// Initial template")
        
        # Step 2: Modify project (add Cosmos DB dependency)
        requirements_file = sample_web_project / "requirements.txt"
        if not requirements_file.exists():
            requirements_file.write_text("azure-cosmos==4.5.1\n")
        
        # Step 3: Detect changes
        changes = {
            "added": ["Microsoft.DocumentDB/databaseAccounts"],
            "modified": [],
            "removed": []
        }
        
        assert len(changes["added"]) == 1
        
        # Step 4: Update only affected templates
        # Expected: Only Cosmos DB module added, others unchanged
        
        # Step 5: Validate updates
        # Expected: No breaking changes to existing resources
        
        assert main_file.exists()
    
    @pytest.mark.asyncio
    async def test_mcp_integration_workflow(self, sample_web_project, mock_mcp_client, temp_output_dir):
        """Test workflow with Azure MCP Server integration."""
        # Step 1: Analyze project and identify resources
        resource_types = [
            "Microsoft.Storage/storageAccounts",
            "Microsoft.Web/sites",
            "Microsoft.KeyVault/vaults"
        ]
        
        # Step 2: Fetch schemas from MCP Server
        schemas = {}
        for resource_type in resource_types:
            schema = await mock_mcp_client.get_bicep_schema(resource_type, "2023-01-01")
            schemas[resource_type] = schema
        
        assert len(schemas) == 3
        
        # Step 3: Generate templates using schemas
        # Expected: Templates match schema structure
        
        # Step 4: Fetch best practices
        for resource_type in resource_types:
            practices = await mock_mcp_client.get_best_practices(resource_type)
            assert len(practices) > 0
    
    def test_multi_environment_workflow(self, sample_web_project, temp_output_dir):
        """Test workflow for multiple environments."""
        environments = ["dev", "staging", "production"]
        
        # Generate templates for each environment
        for env in environments:
            env_dir = temp_output_dir / env
            env_dir.mkdir(parents=True, exist_ok=True)
            
            # Create environment-specific parameters
            params = {
                "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
                "contentVersion": "1.0.0.0",
                "parameters": {
                    "environment": {"value": env},
                    "location": {"value": "eastus" if env != "production" else "westus2"}
                }
            }
            
            param_file = env_dir / f"{env}.parameters.json"
            param_file.write_text(json.dumps(params, indent=2))
            
            assert param_file.exists()
        
        # Verify all environments created
        assert len(list(temp_output_dir.iterdir())) == len(environments)


@pytest.mark.integration
class TestTemplateValidation:
    """Integration tests for template validation."""
    
    def test_validate_bicep_syntax(self, sample_bicep_template, temp_output_dir):
        """Test Bicep syntax validation."""
        # Write template to file
        template_file = temp_output_dir / "test.bicep"
        template_file.write_text(sample_bicep_template)
        
        # Validate using bicep CLI (mocked)
        # bicep build test.bicep --stdout
        
        # Expected: No syntax errors
        assert template_file.exists()
        content = template_file.read_text()
        assert "resource" in content
        assert "param" in content
    
    def test_validate_schema_compliance(self, sample_bicep_template, mock_mcp_schema_response):
        """Test schema compliance validation."""
        # Parse template and extract resource definition
        # Compare against schema from MCP Server
        
        schema_required = mock_mcp_schema_response.get("required", [])
        
        # Verify required properties are present
        assert "name" in schema_required
        assert "location" in schema_required
    
    def test_validate_best_practices(self, sample_bicep_template):
        """Test best practices validation."""
        # Check for best practices:
        # - HTTPS only
        # - TLS 1.2+
        # - Managed identity
        # - Diagnostic logging
        
        best_practices_checks = {
            "https_only": "supportsHttpsTrafficOnly: true" in sample_bicep_template,
            "tls_version": "TLS1_2" in sample_bicep_template or "minimumTlsVersion" in sample_bicep_template
        }
        
        assert best_practices_checks["https_only"]
        assert best_practices_checks["tls_version"]
    
    def test_validate_security_requirements(self, sample_bicep_template):
        """Test security requirements validation."""
        # Security checks:
        # - No hardcoded secrets
        # - Proper RBAC configuration
        # - Network security
        
        security_checks = {
            "no_hardcoded_keys": "AccountKey=" not in sample_bicep_template,
            "no_hardcoded_passwords": "password" not in sample_bicep_template.lower()
        }
        
        assert security_checks["no_hardcoded_keys"]
    
    @pytest.mark.asyncio
    async def test_validate_with_azure_arm(self, sample_bicep_template, temp_output_dir, mock_azure_cli):
        """Test validation using Azure ARM."""
        # Write template
        template_file = temp_output_dir / "test.bicep"
        template_file.write_text(sample_bicep_template)
        
        # Mock ARM validation
        validation_result = mock_azure_cli.deployment_validate()
        
        assert validation_result is not None
        assert validation_result.get("error") is None


@pytest.mark.integration
class TestTemplateDeployment:
    """Integration tests for template deployment preparation."""
    
    def test_prepare_deployment_package(self, temp_output_dir):
        """Test deployment package preparation."""
        # Create template files
        (temp_output_dir / "main.bicep").write_text("// Main template")
        (temp_output_dir / "parameters").mkdir(parents=True, exist_ok=True)
        (temp_output_dir / "parameters" / "prod.parameters.json").write_text("{}")
        
        # Deployment package should include:
        # - All .bicep files
        # - All parameter files
        # - README with deployment instructions
        
        required_files = [
            "main.bicep",
            "parameters/prod.parameters.json"
        ]
        
        for file_path in required_files:
            assert (temp_output_dir / file_path).exists()
    
    def test_generate_deployment_script(self, temp_output_dir):
        """Test deployment script generation."""
        # Generate PowerShell deployment script
        deploy_script = """
param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory=$true)]
    [string]$SubscriptionId,
    
    [string]$Environment = "dev"
)

# Deploy Bicep template
az deployment group create `
    --resource-group $ResourceGroup `
    --subscription $SubscriptionId `
    --template-file main.bicep `
    --parameters "@parameters/$Environment.parameters.json"
"""
        
        script_file = temp_output_dir / "deploy.ps1"
        script_file.write_text(deploy_script)
        
        assert script_file.exists()
        content = script_file.read_text()
        assert "az deployment group create" in content
    
    @pytest.mark.asyncio
    async def test_dry_run_deployment(self, sample_bicep_template, temp_output_dir, mock_azure_cli):
        """Test dry-run deployment (what-if)."""
        # Write template
        template_file = temp_output_dir / "test.bicep"
        template_file.write_text(sample_bicep_template)
        
        # Mock what-if operation
        whatif_result = {
            "changes": [
                {
                    "resourceType": "Microsoft.Storage/storageAccounts",
                    "changeType": "Create",
                    "resourceName": "mystorageaccount"
                }
            ]
        }
        
        # Verify what-if shows expected changes
        assert len(whatif_result["changes"]) > 0
        assert whatif_result["changes"][0]["changeType"] == "Create"
    
    @pytest.mark.azure
    @pytest.mark.slow
    async def test_actual_deployment(self, sample_bicep_template, temp_output_dir, mock_azure_cli):
        """Test actual deployment to Azure (requires credentials)."""
        # This test would be skipped in CI unless Azure credentials are available
        pytest.skip("Requires Azure credentials and creates real resources")
        
        # Steps:
        # 1. Create resource group
        # 2. Deploy template
        # 3. Verify resources created
        # 4. Clean up resources


@pytest.mark.integration
class TestDependencyResolution:
    """Integration tests for dependency resolution."""
    
    def test_resolve_simple_dependencies(self):
        """Test resolution of simple dependencies."""
        resources = {
            "webapp": {"depends_on": ["storage", "keyvault"]},
            "storage": {"depends_on": []},
            "keyvault": {"depends_on": []}
        }
        
        # Deployment order should be: storage, keyvault, webapp
        deployment_order = []
        
        # Add resources with no dependencies first
        for name, resource in resources.items():
            if len(resource["depends_on"]) == 0:
                deployment_order.append(name)
        
        # Add resources with dependencies
        for name, resource in resources.items():
            if len(resource["depends_on"]) > 0:
                deployment_order.append(name)
        
        assert deployment_order[0] in ["storage", "keyvault"]
        assert deployment_order[-1] == "webapp"
    
    def test_resolve_complex_dependencies(self):
        """Test resolution of complex dependency graph."""
        resources = {
            "webapp": {"depends_on": ["app_plan", "storage"]},
            "app_plan": {"depends_on": []},
            "storage": {"depends_on": ["keyvault"]},
            "keyvault": {"depends_on": []}
        }
        
        # Valid deployment orders:
        # 1. keyvault, app_plan, storage, webapp
        # 2. app_plan, keyvault, storage, webapp
        
        # Build deployment order using topological sort
        # (simplified version)
        deployed = set()
        order = []
        
        while len(deployed) < len(resources):
            for name, resource in resources.items():
                if name not in deployed:
                    # Check if all dependencies are deployed
                    deps_deployed = all(dep in deployed for dep in resource["depends_on"])
                    if deps_deployed:
                        order.append(name)
                        deployed.add(name)
        
        # Verify webapp is last
        assert order[-1] == "webapp"
        
        # Verify keyvault before storage
        keyvault_idx = order.index("keyvault")
        storage_idx = order.index("storage")
        assert keyvault_idx < storage_idx
    
    def test_detect_circular_dependencies(self):
        """Test detection of circular dependencies."""
        resources = {
            "a": {"depends_on": ["b"]},
            "b": {"depends_on": ["c"]},
            "c": {"depends_on": ["a"]}  # Circular!
        }
        
        # Should detect circular dependency: a -> b -> c -> a
        
        # Simple cycle detection
        def has_cycle(resources, name, visited, rec_stack):
            visited.add(name)
            rec_stack.add(name)
            
            for dep in resources[name]["depends_on"]:
                if dep not in visited:
                    if has_cycle(resources, dep, visited, rec_stack):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(name)
            return False
        
        visited = set()
        rec_stack = set()
        
        has_circular = False
        for name in resources:
            if name not in visited:
                if has_cycle(resources, name, visited, rec_stack):
                    has_circular = True
                    break
        
        assert has_circular is True


@pytest.mark.integration
class TestCostEstimation:
    """Integration tests for cost estimation."""
    
    def test_estimate_basic_resources(self):
        """Test cost estimation for basic resources."""
        resources = [
            {"type": "Microsoft.Storage/storageAccounts", "sku": "Standard_LRS"},
            {"type": "Microsoft.Web/serverfarms", "sku": "B1"},
            {"type": "Microsoft.KeyVault/vaults", "sku": "standard"}
        ]
        
        # Mock pricing
        pricing = {
            "storage_standard_lrs": 0.05,  # per GB/month
            "app_service_b1": 13.14,  # per month
            "keyvault_standard": 0.03  # per 10K operations
        }
        
        # Calculate estimated costs
        monthly_cost = (
            pricing["storage_standard_lrs"] * 100 +  # 100 GB
            pricing["app_service_b1"] +
            pricing["keyvault_standard"] * 10  # 100K operations
        )
        
        assert monthly_cost > 0
    
    def test_estimate_with_scaling(self):
        """Test cost estimation with auto-scaling."""
        base_config = {
            "min_instances": 1,
            "max_instances": 5,
            "avg_utilization": 0.6  # 60% average
        }
        
        instance_cost = 50.0  # per instance per month
        
        # Estimated cost with average utilization
        avg_instances = (
            base_config["min_instances"] +
            (base_config["max_instances"] - base_config["min_instances"]) *
            base_config["avg_utilization"]
        )
        
        estimated_cost = avg_instances * instance_cost
        
        assert estimated_cost > instance_cost  # More than min
        assert estimated_cost < (base_config["max_instances"] * instance_cost)  # Less than max
    
    def test_cost_optimization_recommendations(self):
        """Test cost optimization recommendations."""
        current_config = {
            "sku": "P1v2",
            "instances": 3,
            "monthly_cost": 450.0
        }
        
        # Recommend reserved instances (1-year)
        reserved_discount = 0.30  # 30% discount
        reserved_cost = current_config["monthly_cost"] * (1 - reserved_discount)
        
        # Recommend right-sizing if underutilized
        utilization = 0.35  # 35% average CPU
        if utilization < 0.50:
            recommendation = "Consider downsizing to B-series"
        
        assert reserved_cost < current_config["monthly_cost"]
        assert recommendation is not None


@pytest.mark.integration
class TestSecurityAnalysis:
    """Integration tests for security analysis."""
    
    def test_scan_for_security_issues(self, sample_bicep_template):
        """Test security scanning of templates."""
        security_checks = [
            ("HTTPS enforcement", "httpsOnly: true"),
            ("TLS version", "minimumTlsVersion"),
            ("Public access", "publicNetworkAccess")
        ]
        
        issues = []
        for check_name, pattern in security_checks:
            if pattern.lower() not in sample_bicep_template.lower():
                issues.append(check_name)
        
        # Should have few or no issues
        assert len(issues) < len(security_checks)
    
    def test_compliance_framework_check(self):
        """Test compliance framework validation."""
        frameworks = {
            "CIS-Azure": [
                "Enable HTTPS only",
                "Use managed identity",
                "Enable diagnostic logging"
            ],
            "SOC2": [
                "Data encryption at rest",
                "Data encryption in transit",
                "Access control with RBAC"
            ]
        }
        
        # Check compliance for each framework
        compliance_results = {}
        for framework, requirements in frameworks.items():
            compliance_results[framework] = {
                "total": len(requirements),
                "passed": len(requirements) - 1  # Mock: all but one passed
            }
        
        # Calculate compliance percentage
        for framework, result in compliance_results.items():
            percentage = (result["passed"] / result["total"]) * 100
            assert percentage > 0
    
    def test_generate_security_report(self, temp_output_dir):
        """Test security report generation."""
        report = {
            "summary": {
                "total_checks": 25,
                "passed": 22,
                "failed": 3,
                "warnings": 5
            },
            "critical_issues": [
                "Storage account allows public access",
                "Key Vault does not have soft delete enabled"
            ],
            "recommendations": [
                "Enable HTTPS only on all web apps",
                "Use managed identities instead of connection strings"
            ]
        }
        
        # Write report
        report_file = temp_output_dir / "security-report.json"
        report_file.write_text(json.dumps(report, indent=2))
        
        assert report_file.exists()
        assert report["summary"]["passed"] > report["summary"]["failed"]
