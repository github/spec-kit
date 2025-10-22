"""Main Bicep template generator.

This module orchestrates the complete Bicep template generation process,
combining project analysis, user requirements, and template generation.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .analyzer import ProjectAnalyzer
from .questionnaire import UserRequirementsQuestionnaire
from .template_manager import TemplateManager
from .models.project_analysis import ProjectAnalysisResult, ProjectType, FrameworkType
from .models.resource_requirement import ResourceRequirement, ResourceType, PriorityLevel
from .models.bicep_template import BicepTemplate, BicepResource, BicepParameter, BicepOutput
from .models.deployment_config import DeploymentConfiguration, EnvironmentConfig
from ..utils.file_scanner import FileScanner
from .mcp_client import MCPClient

logger = logging.getLogger(__name__)


class BicepGenerator:
    """Main orchestrator for Bicep template generation."""
    
    def __init__(self, 
                 project_path: Path,
                 output_path: Optional[Path] = None,
                 mcp_client: Optional[MCPClient] = None):
        """Initialize the Bicep generator."""
        self.project_path = project_path
        self.output_path = output_path or (project_path / "infrastructure")
        self.mcp_client = mcp_client
        
        # Initialize components
        self.file_scanner = FileScanner()
        self.project_analyzer = ProjectAnalyzer(self.file_scanner, mcp_client)
        self.template_manager = TemplateManager()
        
        # State
        self.analysis_result: Optional[ProjectAnalysisResult] = None
        self.user_requirements: Dict[str, Any] = {}
        self.deployment_config: Optional[DeploymentConfiguration] = None
        self.generated_templates: Dict[str, BicepTemplate] = {}
    
    async def generate_templates(self, 
                               interactive: bool = True,
                               user_requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Path]:
        """Generate complete Bicep templates for the project."""
        logger.info(f"Starting Bicep template generation for: {self.project_path}")
        
        try:
            # Step 1: Analyze project
            await self._analyze_project()
            
            # Step 2: Collect user requirements
            if interactive:
                await self._collect_user_requirements_interactive()
            elif user_requirements:
                self.user_requirements = user_requirements
            else:
                # Use defaults based on analysis
                self.user_requirements = self._get_default_requirements()
            
            # Step 3: Create deployment configuration
            self._create_deployment_configuration()
            
            # Step 4: Generate templates
            await self._generate_bicep_templates()
            
            # Step 5: Write templates to disk
            output_files = await self._write_templates()
            
            # Step 6: Generate parameter files
            param_files = await self._generate_parameter_files()
            output_files.update(param_files)
            
            # Step 7: Generate deployment scripts
            script_files = await self._generate_deployment_scripts()
            output_files.update(script_files)
            
            logger.info(f"Bicep template generation completed. Generated {len(output_files)} files.")
            return output_files
            
        except Exception as e:
            logger.error(f"Error generating Bicep templates: {e}")
            raise
    
    async def _analyze_project(self) -> None:
        """Analyze the project to determine requirements."""
        logger.info("Analyzing project structure and dependencies...")
        
        self.analysis_result = await self.project_analyzer.analyze_project(
            self.project_path, 
            deep_scan=True
        )
        
        logger.info(f"Project analysis complete: {self.analysis_result.project_type.value}, "
                   f"confidence: {self.analysis_result.confidence_score:.1%}")
    
    async def _collect_user_requirements_interactive(self) -> None:
        """Collect user requirements through interactive questionnaire."""
        logger.info("Starting interactive requirements collection...")
        
        questionnaire = UserRequirementsQuestionnaire(self.analysis_result)
        self.user_requirements = await questionnaire.run_interactive_questionnaire()
        
        logger.info("User requirements collection completed")
    
    def _get_default_requirements(self) -> Dict[str, Any]:
        """Get default requirements based on project analysis."""
        defaults = {
            "project_confirmation": True,
            "environments": ["dev", "prod"],
            "primary_location": "eastus",
            "multi_region": False,
            "enable_caching": True,
            "enable_monitoring": True,
            "security_level": "enhanced",
            "ssl_configuration": "managed",
            "auto_scaling": True,
            "backup_retention": "30",
            "cost_optimization": "balanced",
            "compliance_frameworks": ["none"],
            "final_confirmation": True
        }
        
        # Add database defaults based on project type
        if self.analysis_result.project_type in [
            ProjectType.WEB_APPLICATION, 
            ProjectType.FULL_STACK_APPLICATION, 
            ProjectType.API_SERVICE
        ]:
            defaults["database_type"] = "sql"
        
        return defaults
    
    def _create_deployment_configuration(self) -> None:
        """Create deployment configuration from analysis and requirements."""
        questionnaire = UserRequirementsQuestionnaire(self.analysis_result)
        questionnaire.answers = self.user_requirements
        
        self.deployment_config = questionnaire.create_deployment_configuration()
        
        # Set output paths
        self.deployment_config.main_template_path = self.output_path / "main.bicep"
        
        for env_name in self.deployment_config.environments:
            param_file = self.output_path / f"main.{env_name}.bicepparam"
            self.deployment_config.set_parameter_file_path(env_name, param_file)
    
    async def _generate_bicep_templates(self) -> None:
        """Generate the main Bicep templates."""
        logger.info("Generating Bicep templates...")
        
        # Determine final resource requirements
        base_requirements = self.analysis_result.resource_requirements
        user_requirements_override = self._get_user_resource_requirements()
        
        # Merge and deduplicate requirements
        final_requirements = self._merge_resource_requirements(
            base_requirements, user_requirements_override
        )
        
        # Generate main template
        main_template = await self._generate_main_template(final_requirements)
        self.generated_templates["main"] = main_template
        
        # Generate module templates for complex resources
        module_templates = await self._generate_module_templates(final_requirements)
        self.generated_templates.update(module_templates)
        
        logger.info(f"Generated {len(self.generated_templates)} templates")
    
    def _get_user_resource_requirements(self) -> List[ResourceRequirement]:
        """Get resource requirements based on user selections."""
        questionnaire = UserRequirementsQuestionnaire(self.analysis_result)
        questionnaire.answers = self.user_requirements
        return questionnaire.get_resource_requirements_override()
    
    def _merge_resource_requirements(self, 
                                   base_requirements: List[ResourceRequirement],
                                   user_requirements: List[ResourceRequirement]) -> List[ResourceRequirement]:
        """Merge base and user requirements, prioritizing user choices."""
        # Create lookup for user requirements
        user_by_type = {req.resource_type: req for req in user_requirements}
        
        # Start with user requirements
        final_requirements = list(user_requirements)
        
        # Add base requirements that aren't overridden
        for base_req in base_requirements:
            if base_req.resource_type not in user_by_type:
                final_requirements.append(base_req)
        
        # Sort by priority
        final_requirements.sort(key=lambda req: req.priority.value, reverse=True)
        
        return final_requirements
    
    async def _generate_main_template(self, requirements: List[ResourceRequirement]) -> BicepTemplate:
        """Generate the main Bicep template."""
        template = BicepTemplate(
            name="main",
            description=f"Main infrastructure template for {self.analysis_result.project_path.name}",
            version="1.0.0"
        )
        
        # Add metadata
        template.metadata = {
            "generator": "Specify CLI Bicep Generator",
            "project": self.analysis_result.project_path.name,
            "project_type": self.analysis_result.project_type.value,
            "generated_at": datetime.now().isoformat(),
            "frameworks": [f.value for f in self.analysis_result.detected_frameworks]
        }
        
        # Add common parameters
        await self._add_common_parameters(template)
        
        # Add resources based on requirements
        await self._add_resources_to_template(template, requirements)
        
        # Add outputs
        await self._add_common_outputs(template)
        
        return template
    
    async def _add_common_parameters(self, template: BicepTemplate) -> None:
        """Add common parameters to the template."""
        # Environment parameter
        template.add_parameter(BicepParameter(
            name="environment",
            type="string",
            default_value="dev",
            allowed_values=list(self.deployment_config.environments.keys()),
            description="The deployment environment"
        ))
        
        # Location parameter
        template.add_parameter(BicepParameter(
            name="location",
            type="string",
            default_value="[resourceGroup().location]",
            description="The Azure region for resources"
        ))
        
        # Application name parameter
        template.add_parameter(BicepParameter(
            name="applicationName",
            type="string",
            default_value=self.analysis_result.project_path.name.lower(),
            description="The name of the application"
        ))
        
        # Tags parameter
        template.add_parameter(BicepParameter(
            name="tags",
            type="object",
            default_value={
                "project": self.analysis_result.project_path.name,
                "environment": "[parameters('environment')]",
                "generated-by": "specify-cli"
            },
            description="Resource tags"
        ))
    
    async def _add_resources_to_template(self, 
                                       template: BicepTemplate, 
                                       requirements: List[ResourceRequirement]) -> None:
        """Add resources to the template based on requirements."""
        
        for requirement in requirements:
            try:
                if requirement.resource_type == ResourceType.APP_SERVICE:
                    await self._add_app_service_resources(template, requirement)
                
                elif requirement.resource_type == ResourceType.STATIC_WEB_APP:
                    await self._add_static_web_app_resources(template, requirement)
                
                elif requirement.resource_type == ResourceType.SQL_DATABASE:
                    await self._add_sql_database_resources(template, requirement)
                
                elif requirement.resource_type == ResourceType.POSTGRESQL:
                    await self._add_postgresql_resources(template, requirement)
                
                elif requirement.resource_type == ResourceType.REDIS_CACHE:
                    await self._add_redis_cache_resources(template, requirement)
                
                elif requirement.resource_type == ResourceType.APPLICATION_INSIGHTS:
                    await self._add_application_insights_resources(template, requirement)
                
                elif requirement.resource_type == ResourceType.KEY_VAULT:
                    await self._add_key_vault_resources(template, requirement)
                
                elif requirement.resource_type == ResourceType.STORAGE_ACCOUNT:
                    await self._add_storage_account_resources(template, requirement)
                
                # Add more resource types as needed
                
            except Exception as e:
                logger.warning(f"Failed to add {requirement.resource_type.value} resource: {e}")
    
    async def _add_app_service_resources(self, template: BicepTemplate, requirement: ResourceRequirement) -> None:
        """Add App Service resources."""
        # App Service Plan
        plan_resource = BicepResource(
            type="Microsoft.Web/serverfarms",
            api_version="2023-01-01",
            name="[format('{0}-plan', parameters('applicationName'))]",
            location="[parameters('location')]",
            properties={
                "reserved": True if self._uses_linux_stack() else False
            },
            sku={
                "name": self._get_app_service_sku(),
                "capacity": 1
            },
            tags="[parameters('tags')]"
        )
        template.add_resource(plan_resource)
        
        # App Service
        app_resource = BicepResource(
            type="Microsoft.Web/sites",
            api_version="2023-01-01",
            name="[parameters('applicationName')]",
            location="[parameters('location')]",
            properties={
                "serverFarmId": "[resourceId('Microsoft.Web/serverfarms', format('{0}-plan', parameters('applicationName')))]",
                "httpsOnly": True,
                "siteConfig": self._get_app_service_config()
            },
            tags="[parameters('tags')]",
            depends_on=["[resourceId('Microsoft.Web/serverfarms', format('{0}-plan', parameters('applicationName')))]"]
        )
        template.add_resource(app_resource)
    
    def _uses_linux_stack(self) -> bool:
        """Determine if the project uses a Linux stack."""
        linux_frameworks = [
            FrameworkType.DJANGO, FrameworkType.FLASK, FrameworkType.FASTAPI,
            FrameworkType.EXPRESS_JS, FrameworkType.REACT, FrameworkType.ANGULAR, FrameworkType.VUE
        ]
        return any(fw in self.analysis_result.detected_frameworks for fw in linux_frameworks)
    
    def _get_app_service_sku(self) -> str:
        """Get appropriate App Service SKU based on cost optimization."""
        cost_pref = self.user_requirements.get("cost_optimization", "balanced")
        
        if cost_pref == "low_cost":
            return "B1"  # Basic tier
        elif cost_pref == "performance":
            return "P1V3"  # Premium tier
        else:
            return "S1"  # Standard tier
    
    def _get_app_service_config(self) -> Dict[str, Any]:
        """Get App Service configuration based on detected frameworks."""
        config = {
            "minTlsVersion": "1.2",
            "ftpsState": "Disabled",
            "httpLoggingEnabled": True,
            "detailedErrorLoggingEnabled": True,
            "requestTracingEnabled": True
        }
        
        # Framework-specific configuration
        if FrameworkType.ASP_NET_CORE in self.analysis_result.detected_frameworks:
            config.update({
                "netFrameworkVersion": "v8.0",
                "metadata": [
                    {
                        "name": "CURRENT_STACK",
                        "value": "dotnetcore"
                    }
                ]
            })
        
        elif any(fw in self.analysis_result.detected_frameworks for fw in [
            FrameworkType.EXPRESS_JS, FrameworkType.REACT, FrameworkType.ANGULAR, FrameworkType.VUE
        ]):
            config.update({
                "linuxFxVersion": "NODE|18-lts",
                "appCommandLine": "npm start"
            })
        
        elif any(fw in self.analysis_result.detected_frameworks for fw in [
            FrameworkType.DJANGO, FrameworkType.FLASK, FrameworkType.FASTAPI
        ]):
            config.update({
                "linuxFxVersion": "PYTHON|3.11",
                "appCommandLine": "gunicorn --bind=0.0.0.0 --workers=4 startup:app"
            })
        
        return config
    
    async def _add_static_web_app_resources(self, template: BicepTemplate, requirement: ResourceRequirement) -> None:
        """Add Static Web App resources."""
        swa_resource = BicepResource(
            type="Microsoft.Web/staticSites",
            api_version="2023-01-01",
            name="[parameters('applicationName')]",
            location="[parameters('location')]",
            properties={
                "buildProperties": {
                    "appLocation": "/",
                    "outputLocation": self._get_static_output_location()
                }
            },
            sku={
                "name": "Free",
                "tier": "Free"
            },
            tags="[parameters('tags')]"
        )
        template.add_resource(swa_resource)
    
    def _get_static_output_location(self) -> str:
        """Get the output location for static web apps based on framework."""
        if FrameworkType.REACT in self.analysis_result.detected_frameworks:
            return "build"
        elif FrameworkType.ANGULAR in self.analysis_result.detected_frameworks:
            return "dist"
        elif FrameworkType.VUE in self.analysis_result.detected_frameworks:
            return "dist"
        else:
            return "dist"
    
    async def _add_sql_database_resources(self, template: BicepTemplate, requirement: ResourceRequirement) -> None:
        """Add SQL Database resources."""
        # SQL Server
        server_resource = BicepResource(
            type="Microsoft.Sql/servers",
            api_version="2023-05-01-preview",
            name="[format('{0}-sql', parameters('applicationName'))]",
            location="[parameters('location')]",
            properties={
                "administratorLogin": "sqladmin",
                "administratorLoginPassword": "[parameters('sqlPassword')]",
                "version": "12.0",
                "minimalTlsVersion": "1.2",
                "publicNetworkAccess": "Enabled"
            },
            tags="[parameters('tags')]"
        )
        template.add_resource(server_resource)
        
        # Add SQL password parameter
        template.add_parameter(BicepParameter(
            name="sqlPassword",
            type="securestring",
            description="SQL Server administrator password"
        ))
        
        # SQL Database
        db_resource = BicepResource(
            type="Microsoft.Sql/servers/databases",
            api_version="2023-05-01-preview",
            name="[format('{0}-sql/{1}', parameters('applicationName'), parameters('applicationName'))]",
            location="[parameters('location')]",
            properties={
                "collation": "SQL_Latin1_General_CP1_CI_AS",
                "maxSizeBytes": 2147483648,  # 2GB
                "sampleName": None
            },
            sku={
                "name": "Basic",
                "tier": "Basic",
                "capacity": 5
            },
            tags="[parameters('tags')]",
            depends_on=["[resourceId('Microsoft.Sql/servers', format('{0}-sql', parameters('applicationName')))]"]
        )
        template.add_resource(db_resource)
        
        # Firewall rule for Azure services
        firewall_resource = BicepResource(
            type="Microsoft.Sql/servers/firewallRules",
            api_version="2023-05-01-preview",
            name="[format('{0}-sql/AllowAzureServices', parameters('applicationName'))]",
            properties={
                "startIpAddress": "0.0.0.0",
                "endIpAddress": "0.0.0.0"
            },
            depends_on=["[resourceId('Microsoft.Sql/servers', format('{0}-sql', parameters('applicationName')))]"]
        )
        template.add_resource(firewall_resource)
    
    async def _add_postgresql_resources(self, template: BicepTemplate, requirement: ResourceRequirement) -> None:
        """Add PostgreSQL resources."""
        pg_resource = BicepResource(
            type="Microsoft.DBforPostgreSQL/flexibleServers",
            api_version="2023-06-01-preview",
            name="[format('{0}-pg', parameters('applicationName'))]",
            location="[parameters('location')]",
            properties={
                "administratorLogin": "pgadmin",
                "administratorLoginPassword": "[parameters('pgPassword')]",
                "version": "15",
                "storage": {
                    "storageSizeGB": 32
                },
                "backup": {
                    "backupRetentionDays": int(self.user_requirements.get("backup_retention", "30")),
                    "geoRedundantBackup": "Disabled"
                },
                "highAvailability": {
                    "mode": "Disabled"
                }
            },
            sku={
                "name": "Standard_B1ms",
                "tier": "Burstable"
            },
            tags="[parameters('tags')]"
        )
        template.add_resource(pg_resource)
        
        # Add PostgreSQL password parameter
        template.add_parameter(BicepParameter(
            name="pgPassword",
            type="securestring",
            description="PostgreSQL administrator password"
        ))
    
    async def _add_redis_cache_resources(self, template: BicepTemplate, requirement: ResourceRequirement) -> None:
        """Add Redis Cache resources."""
        redis_resource = BicepResource(
            type="Microsoft.Cache/redis",
            api_version="2023-08-01",
            name="[format('{0}-redis', parameters('applicationName'))]",
            location="[parameters('location')]",
            properties={
                "sku": {
                    "name": "Basic",
                    "family": "C",
                    "capacity": 0
                },
                "enableNonSslPort": False,
                "minimumTlsVersion": "1.2"
            },
            tags="[parameters('tags')]"
        )
        template.add_resource(redis_resource)
    
    async def _add_application_insights_resources(self, template: BicepTemplate, requirement: ResourceRequirement) -> None:
        """Add Application Insights resources."""
        # Log Analytics Workspace (required for Application Insights)
        workspace_resource = BicepResource(
            type="Microsoft.OperationalInsights/workspaces",
            api_version="2023-09-01",
            name="[format('{0}-law', parameters('applicationName'))]",
            location="[parameters('location')]",
            properties={
                "sku": {
                    "name": "PerGB2018"
                },
                "retentionInDays": 90
            },
            tags="[parameters('tags')]"
        )
        template.add_resource(workspace_resource)
        
        # Application Insights
        insights_resource = BicepResource(
            type="Microsoft.Insights/components",
            api_version="2020-02-02",
            name="[format('{0}-ai', parameters('applicationName'))]",
            location="[parameters('location')]",
            kind="web",
            properties={
                "Application_Type": "web",
                "WorkspaceResourceId": "[resourceId('Microsoft.OperationalInsights/workspaces', format('{0}-law', parameters('applicationName')))]"
            },
            tags="[parameters('tags')]",
            depends_on=["[resourceId('Microsoft.OperationalInsights/workspaces', format('{0}-law', parameters('applicationName')))]"]
        )
        template.add_resource(insights_resource)
    
    async def _add_key_vault_resources(self, template: BicepTemplate, requirement: ResourceRequirement) -> None:
        """Add Key Vault resources."""
        kv_resource = BicepResource(
            type="Microsoft.KeyVault/vaults",
            api_version="2023-07-01",
            name="[format('{0}-kv-{1}', parameters('applicationName'), uniqueString(resourceGroup().id))]",
            location="[parameters('location')]",
            properties={
                "tenantId": "[subscription().tenantId]",
                "sku": {
                    "name": "standard",
                    "family": "A"
                },
                "enabledForDeployment": True,
                "enabledForTemplateDeployment": True,
                "enabledForDiskEncryption": False,
                "enableRbacAuthorization": True,
                "enableSoftDelete": True,
                "softDeleteRetentionInDays": 7,
                "enablePurgeProtection": False,
                "networkAcls": {
                    "defaultAction": "Allow",
                    "bypass": "AzureServices"
                }
            },
            tags="[parameters('tags')]"
        )
        template.add_resource(kv_resource)
    
    async def _add_storage_account_resources(self, template: BicepTemplate, requirement: ResourceRequirement) -> None:
        """Add Storage Account resources."""
        storage_resource = BicepResource(
            type="Microsoft.Storage/storageAccounts",
            api_version="2023-01-01",
            name="[format('{0}st{1}', parameters('applicationName'), uniqueString(resourceGroup().id))]",
            location="[parameters('location')]",
            kind="StorageV2",
            properties={
                "supportsHttpsTrafficOnly": True,
                "minimumTlsVersion": "TLS1_2",
                "allowBlobPublicAccess": False,
                "allowSharedKeyAccess": True,
                "defaultToOAuthAuthentication": False
            },
            sku={
                "name": "Standard_LRS"
            },
            tags="[parameters('tags')]"
        )
        template.add_resource(storage_resource)
    
    async def _add_common_outputs(self, template: BicepTemplate) -> None:
        """Add common outputs to the template."""
        # Resource group name
        template.add_output(BicepOutput(
            name="resourceGroupName",
            type="string",
            value="[resourceGroup().name]",
            description="The name of the resource group"
        ))
        
        # Application name
        template.add_output(BicepOutput(
            name="applicationName",
            type="string",
            value="[parameters('applicationName')]",
            description="The name of the application"
        ))
        
        # Environment
        template.add_output(BicepOutput(
            name="environment",
            type="string",
            value="[parameters('environment')]",
            description="The deployment environment"
        ))
    
    async def _generate_module_templates(self, requirements: List[ResourceRequirement]) -> Dict[str, BicepTemplate]:
        """Generate module templates for complex resources."""
        modules = {}
        
        # For now, we'll generate everything in the main template
        # Future enhancement: create separate modules for complex resources
        
        return modules
    
    async def _write_templates(self) -> Dict[str, Path]:
        """Write generated templates to disk."""
        logger.info(f"Writing templates to: {self.output_path}")
        
        # Ensure output directory exists
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        output_files = {}
        
        for template_name, template in self.generated_templates.items():
            # Generate Bicep content
            bicep_content = template.to_bicep()
            
            # Write to file
            if template_name == "main":
                file_path = self.output_path / "main.bicep"
            else:
                file_path = self.output_path / f"{template_name}.bicep"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(bicep_content)
            
            output_files[template_name] = file_path
            logger.info(f"Generated template: {file_path}")
        
        return output_files
    
    async def _generate_parameter_files(self) -> Dict[str, Path]:
        """Generate parameter files for each environment."""
        param_files = {}
        
        for env_name, env_config in self.deployment_config.environments.items():
            # Create parameter file content
            param_content = self._generate_bicep_param_content(env_config)
            
            # Write parameter file
            param_file = self.output_path / f"main.{env_name}.bicepparam"
            
            with open(param_file, 'w', encoding='utf-8') as f:
                f.write(param_content)
            
            param_files[f"params-{env_name}"] = param_file
            logger.info(f"Generated parameter file: {param_file}")
        
        return param_files
    
    def _generate_bicep_param_content(self, env_config: EnvironmentConfig) -> str:
        """Generate Bicep parameter file content."""
        lines = [
            f"// Parameter file for {env_config.display_name} environment",
            f"// Generated by Specify CLI on {datetime.now().isoformat()}",
            "",
            "using 'main.bicep'",
            "",
            f"param environment = '{env_config.name}'",
            f"param location = '{env_config.location}'",
            f"param applicationName = '{self.analysis_result.project_path.name.lower()}'",
            "",
            "param tags = {",
            f"  environment: '{env_config.name}'",
            f"  project: '{self.analysis_result.project_path.name}'",
            "  'generated-by': 'specify-cli'",
        ]
        
        # Add environment-specific tags
        for key, value in env_config.get_effective_tags().items():
            if key not in ['environment', 'project', 'generated-by']:
                lines.append(f"  '{key}': '{value}'")
        
        lines.append("}")
        
        # Add secure parameters (to be filled by user)
        if self.user_requirements.get("database_type") == "sql":
            lines.extend([
                "",
                "// TODO: Set secure parameters",
                "// param sqlPassword = '' // Set in deployment"
            ])
        
        if self.user_requirements.get("database_type") == "postgresql":
            lines.extend([
                "",
                "// TODO: Set secure parameters", 
                "// param pgPassword = '' // Set in deployment"
            ])
        
        return "\n".join(lines)
    
    async def _generate_deployment_scripts(self) -> Dict[str, Path]:
        """Generate deployment scripts."""
        script_files = {}
        
        # PowerShell deployment script
        ps_script = self._generate_powershell_script()
        ps_file = self.output_path / "deploy.ps1"
        
        with open(ps_file, 'w', encoding='utf-8') as f:
            f.write(ps_script)
        
        script_files["deploy-powershell"] = ps_file
        
        # Bash deployment script
        bash_script = self._generate_bash_script()
        bash_file = self.output_path / "deploy.sh"
        
        with open(bash_file, 'w', encoding='utf-8') as f:
            f.write(bash_script)
        
        script_files["deploy-bash"] = bash_file
        
        # README file
        readme_content = self._generate_readme()
        readme_file = self.output_path / "README.md"
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        script_files["readme"] = readme_file
        
        logger.info("Generated deployment scripts and documentation")
        return script_files
    
    def _generate_powershell_script(self) -> str:
        """Generate PowerShell deployment script."""
        environments = list(self.deployment_config.environments.keys())
        
        return f'''#!/usr/bin/env pwsh
# Azure Bicep Deployment Script for {self.analysis_result.project_path.name}
# Generated by Specify CLI on {datetime.now().isoformat()}

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet({', '.join([f'"{env}"' for env in environments])})]
    [string]$Environment,
    
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "{self.user_requirements.get('primary_location', 'eastus')}",
    
    [Parameter(Mandatory=$false)]
    [switch]$WhatIf
)

# Set error handling
$ErrorActionPreference = "Stop"

# Authenticate to Azure (if not already authenticated)
if (-not (Get-AzContext)) {{
    Write-Host "Please log in to Azure..." -ForegroundColor Yellow
    Connect-AzAccount
}}

# Create resource group if it doesn't exist
$rg = Get-AzResourceGroup -Name $ResourceGroupName -ErrorAction SilentlyContinue
if (-not $rg) {{
    Write-Host "Creating resource group: $ResourceGroupName" -ForegroundColor Green
    New-AzResourceGroup -Name $ResourceGroupName -Location $Location
}}

# Deploy Bicep template
$templateFile = Join-Path $PSScriptRoot "main.bicep"
$parametersFile = Join-Path $PSScriptRoot "main.$Environment.bicepparam"

Write-Host "Deploying to environment: $Environment" -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Green
Write-Host "Template: $templateFile" -ForegroundColor Green
Write-Host "Parameters: $parametersFile" -ForegroundColor Green

$deploymentParams = @{{
    ResourceGroupName = $ResourceGroupName
    TemplateFile = $templateFile
    TemplateParameterFile = $parametersFile
    Name = "{self.analysis_result.project_path.name}-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
}}

if ($WhatIf) {{
    Write-Host "Running deployment validation (WhatIf)..." -ForegroundColor Yellow
    New-AzResourceGroupDeployment @deploymentParams -WhatIf
}} else {{
    Write-Host "Starting deployment..." -ForegroundColor Green
    $deployment = New-AzResourceGroupDeployment @deploymentParams
    
    if ($deployment.ProvisioningState -eq "Succeeded") {{
        Write-Host "Deployment completed successfully!" -ForegroundColor Green
        Write-Host "Outputs:" -ForegroundColor Cyan
        $deployment.Outputs | ConvertTo-Json -Depth 3
    }} else {{
        Write-Error "Deployment failed with state: $($deployment.ProvisioningState)"
    }}
}}
'''
    
    def _generate_bash_script(self) -> str:
        """Generate Bash deployment script."""
        environments = list(self.deployment_config.environments.keys())
        
        return f'''#!/bin/bash
# Azure Bicep Deployment Script for {self.analysis_result.project_path.name}
# Generated by Specify CLI on {datetime.now().isoformat()}

set -e  # Exit on error

# Function to display usage
usage() {{
    echo "Usage: $0 -e <environment> -g <resource-group> [-l <location>] [-w]"
    echo "  -e: Environment ({', '.join(environments)})"
    echo "  -g: Resource group name"
    echo "  -l: Azure location (default: {self.user_requirements.get('primary_location', 'eastus')})"
    echo "  -w: What-if mode (validate only)"
    exit 1
}}

# Default values
LOCATION="{self.user_requirements.get('primary_location', 'eastus')}"
WHAT_IF=""

# Parse command line arguments
while getopts "e:g:l:wh" opt; do
    case $opt in
        e) ENVIRONMENT="$OPTARG" ;;
        g) RESOURCE_GROUP="$OPTARG" ;;
        l) LOCATION="$OPTARG" ;;
        w) WHAT_IF="--what-if" ;;
        h) usage ;;
        *) usage ;;
    esac
done

# Validate required parameters
if [[ -z "$ENVIRONMENT" ]] || [[ -z "$RESOURCE_GROUP" ]]; then
    echo "Error: Environment and resource group are required"
    usage
fi

# Validate environment
case "$ENVIRONMENT" in
    {' | '.join(environments)})
        ;;
    *)
        echo "Error: Invalid environment. Must be one of: {', '.join(environments)}"
        exit 1
        ;;
esac

echo "========================================="
echo "Azure Bicep Deployment"
echo "========================================="
echo "Environment: $ENVIRONMENT"
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "What-If Mode: ${{WHAT_IF:+Yes}}"
echo "========================================="

# Check if logged in to Azure
if ! az account show >/dev/null 2>&1; then
    echo "Please log in to Azure..."
    az login
fi

# Create resource group if it doesn't exist
if ! az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
    echo "Creating resource group: $RESOURCE_GROUP"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
fi

# Deploy Bicep template
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
TEMPLATE_FILE="$SCRIPT_DIR/main.bicep"
PARAMETERS_FILE="$SCRIPT_DIR/main.$ENVIRONMENT.bicepparam"
DEPLOYMENT_NAME="{self.analysis_result.project_path.name}-$(date +%Y%m%d-%H%M%S)"

echo "Deploying template..."
az deployment group create \\
    --resource-group "$RESOURCE_GROUP" \\
    --template-file "$TEMPLATE_FILE" \\
    --parameters "$PARAMETERS_FILE" \\
    --name "$DEPLOYMENT_NAME" \\
    $WHAT_IF

if [[ -z "$WHAT_IF" ]]; then
    echo "Deployment completed successfully!"
    echo "Getting deployment outputs..."
    az deployment group show \\
        --resource-group "$RESOURCE_GROUP" \\
        --name "$DEPLOYMENT_NAME" \\
        --query "properties.outputs" \\
        --output table
fi
'''
    
    def _generate_readme(self) -> str:
        """Generate README documentation."""
        environments = list(self.deployment_config.environments.keys())
        
        return f'''# {self.analysis_result.project_path.name} - Azure Infrastructure

This directory contains the Azure infrastructure templates and deployment scripts for the {self.analysis_result.project_path.name} project.

## Generated Information

- **Project Type**: {self.analysis_result.project_type.value}
- **Detected Frameworks**: {', '.join([f.value for f in self.analysis_result.detected_frameworks])}
- **Generated On**: {datetime.now().isoformat()}
- **Generator**: Specify CLI Bicep Generator

## Files

- `main.bicep` - Main Bicep template
{chr(10).join([f'- `main.{env}.bicepparam` - Parameters for {env} environment' for env in environments])}
- `deploy.ps1` - PowerShell deployment script
- `deploy.sh` - Bash deployment script
- `README.md` - This file

## Prerequisites

1. **Azure CLI** - Install from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
2. **Bicep CLI** - Install with `az bicep install`
3. **Azure PowerShell** (for PowerShell scripts) - Install from https://docs.microsoft.com/en-us/powershell/azure/install-az-ps

## Deployment

### Using PowerShell

```powershell
# Login to Azure
Connect-AzAccount

# Deploy to development environment
./deploy.ps1 -Environment dev -ResourceGroupName "rg-{self.analysis_result.project_path.name}-dev"

# Deploy to production environment  
./deploy.ps1 -Environment prod -ResourceGroupName "rg-{self.analysis_result.project_path.name}-prod"

# Validate deployment (what-if)
./deploy.ps1 -Environment dev -ResourceGroupName "rg-{self.analysis_result.project_path.name}-dev" -WhatIf
```

### Using Bash/Azure CLI

```bash
# Login to Azure
az login

# Deploy to development environment
./deploy.sh -e dev -g "rg-{self.analysis_result.project_path.name}-dev"

# Deploy to production environment
./deploy.sh -e prod -g "rg-{self.analysis_result.project_path.name}-prod"

# Validate deployment (what-if)
./deploy.sh -e dev -g "rg-{self.analysis_result.project_path.name}-dev" -w
```

## Configuration

### Environment-Specific Parameters

Each environment has its own parameter file that you can customize:

{chr(10).join([f'''#### {env.title()} Environment (`main.{env}.bicepparam`)
- **Location**: {self.deployment_config.environments[env].location}
- **Environment**: {env}''' for env in environments])}

### Security Configuration

- **HTTPS Only**: Enabled
- **Minimum TLS Version**: 1.2
- **Key Vault**: Included for secrets management
- **RBAC**: {"Enabled" if self.user_requirements.get("security_level") != "basic" else "Basic"}

### Monitoring

- **Application Insights**: {"Enabled" if self.user_requirements.get("enable_monitoring") else "Disabled"}
- **Log Analytics**: {"Enabled" if self.user_requirements.get("enable_monitoring") else "Disabled"}

## Resource Overview

The template deploys the following Azure resources:

{chr(10).join([f'- **{req.resource_type.value.replace("_", " ").title()}**: {req.justification}' for req in self._get_all_resource_requirements()])}

## Cost Estimation

- **Optimization Level**: {self.user_requirements.get("cost_optimization", "balanced").replace("_", " ").title()}
- **Estimated Monthly Cost**: ${sum(req.estimated_cost_monthly for req in self._get_all_resource_requirements()):.0f} (approximate)

*Note: Actual costs may vary based on usage, region, and Azure pricing changes.*

## Security Notes

1. **Secrets Management**: Use Azure Key Vault for all secrets and connection strings
2. **Network Security**: Review and configure appropriate network access rules
3. **Identity and Access**: Configure appropriate RBAC permissions
4. **Compliance**: {"Configured for: " + ", ".join(self.user_requirements.get("compliance_frameworks", [])) if self.user_requirements.get("compliance_frameworks") != ["none"] else "Standard configuration"}

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure you're logged in with `az login` or `Connect-AzAccount`
2. **Permission Errors**: Ensure your account has Contributor access to the subscription/resource group
3. **Resource Name Conflicts**: Resource names must be globally unique for some services
4. **Location Constraints**: Some services may not be available in all regions

### Validation

Before deploying, you can validate the template:

```bash
# Validate with Azure CLI
az deployment group validate \\
    --resource-group "your-resource-group" \\
    --template-file main.bicep \\
    --parameters main.dev.bicepparam
```

```powershell
# Validate with PowerShell
Test-AzResourceGroupDeployment \\
    -ResourceGroupName "your-resource-group" \\
    -TemplateFile "main.bicep" \\
    -TemplateParameterFile "main.dev.bicepparam"
```

## Next Steps

1. **Review Parameters**: Customize the parameter files for your environments
2. **Set Secrets**: Configure secure parameters (passwords, connection strings) in Key Vault
3. **Test Deployment**: Start with a development environment
4. **Configure CI/CD**: Set up automated deployments using GitHub Actions or Azure DevOps
5. **Monitor Resources**: Set up alerts and monitoring dashboards

## Support

For issues with the generated templates:

1. Check the Azure Activity Log for deployment errors
2. Review the Bicep template syntax
3. Consult the Azure Bicep documentation: https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/

Generated by [Specify CLI](https://github.com/microsoft/spec-kit) Bicep Generator v{self.deployment_config.version}
'''
    
    def _get_all_resource_requirements(self) -> List[ResourceRequirement]:
        """Get all resource requirements for documentation."""
        base_requirements = self.analysis_result.resource_requirements
        user_requirements = self._get_user_resource_requirements()
        return self._merge_resource_requirements(base_requirements, user_requirements)


# Export the main class
__all__ = ["BicepGenerator"]