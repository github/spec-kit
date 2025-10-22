"""Orchestration module for coordinating all Bicep generation components.

This module provides high-level orchestration functions that coordinate
project analysis, template generation, and deployment configuration.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

from .analyzer import ProjectAnalyzer
from .generator import BicepGenerator
from .questionnaire import UserRequirementsQuestionnaire
from .template_manager import TemplateManager
from .arm_validator import ARMValidator
from .models.project_analysis import ProjectAnalysisResult
from .models.deployment_config import DeploymentConfiguration
from .models.bicep_template import BicepTemplate
from .mcp_client import MCPClient
from ..utils.file_scanner import FileScanner

logger = logging.getLogger(__name__)


class BicepOrchestrator:
    """High-level orchestrator for the complete Bicep generation workflow."""
    
    def __init__(self, 
                 project_path: Path,
                 output_path: Optional[Path] = None,
                 enable_mcp: bool = True,
                 enable_validation: bool = True):
        """Initialize the orchestrator."""
        self.project_path = project_path
        self.output_path = output_path or (project_path / "infrastructure")
        self.enable_mcp = enable_mcp
        self.enable_validation = enable_validation
        
        # Components
        self.file_scanner = FileScanner()
        self.mcp_client: Optional[MCPClient] = None
        self.project_analyzer: Optional[ProjectAnalyzer] = None
        self.template_manager = TemplateManager()
        self.arm_validator = ARMValidator()
        
        # Results
        self.analysis_result: Optional[ProjectAnalysisResult] = None
        self.deployment_config: Optional[DeploymentConfiguration] = None
        self.generated_files: Dict[str, Path] = {}
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def initialize(self) -> None:
        """Initialize all components."""
        logger.info("Initializing Bicep orchestrator...")
        
        # Initialize MCP client if enabled
        if self.enable_mcp:
            try:
                self.mcp_client = MCPClient()
                await self.mcp_client.connect()
                logger.info("Azure MCP client connected")
            except Exception as e:
                logger.warning(f"Failed to connect to MCP server: {e}")
                self.mcp_client = None
        
        # Initialize analyzer
        self.project_analyzer = ProjectAnalyzer(self.file_scanner, self.mcp_client)
        
        logger.info("Orchestrator initialization complete")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.mcp_client:
            await self.mcp_client.disconnect()
            logger.info("MCP client disconnected")
    
    async def run_complete_workflow(self, 
                                  interactive: bool = True,
                                  user_requirements: Optional[Dict[str, Any]] = None,
                                  validate_output: bool = True) -> Dict[str, Path]:
        """Run the complete Bicep generation workflow."""
        logger.info("Starting complete Bicep generation workflow")
        
        try:
            # Phase 1: Project Analysis
            await self._phase_1_analyze_project()
            
            # Phase 2: Requirements Collection
            requirements = await self._phase_2_collect_requirements(interactive, user_requirements)
            
            # Phase 3: Configuration Creation
            await self._phase_3_create_configuration(requirements)
            
            # Phase 4: Template Generation
            await self._phase_4_generate_templates()
            
            # Phase 5: Validation (optional)
            if validate_output and self.enable_validation:
                await self._phase_5_validate_templates()
            
            # Phase 6: File Writing
            output_files = await self._phase_6_write_files()
            
            logger.info(f"Workflow completed successfully. Generated {len(output_files)} files.")
            return output_files
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            raise
    
    async def _phase_1_analyze_project(self) -> None:
        """Phase 1: Analyze project structure and requirements."""
        logger.info("Phase 1: Analyzing project structure...")
        
        if not self.project_analyzer:
            raise RuntimeError("Project analyzer not initialized")
        
        self.analysis_result = await self.project_analyzer.analyze_project(
            self.project_path,
            deep_scan=True
        )
        
        logger.info(f"Project analysis complete: {self.analysis_result.project_type.value}, "
                   f"confidence: {self.analysis_result.confidence_score:.1%}")
    
    async def _phase_2_collect_requirements(self, 
                                          interactive: bool,
                                          user_requirements: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Phase 2: Collect user requirements and preferences."""
        logger.info("Phase 2: Collecting user requirements...")
        
        if not self.analysis_result:
            raise RuntimeError("Project analysis must be completed first")
        
        if interactive:
            questionnaire = UserRequirementsQuestionnaire(self.analysis_result)
            requirements = await questionnaire.run_interactive_questionnaire()
        elif user_requirements:
            requirements = user_requirements
        else:
            # Use defaults
            requirements = self._get_default_requirements()
        
        logger.info("Requirements collection complete")
        return requirements
    
    def _get_default_requirements(self) -> Dict[str, Any]:
        """Get default requirements for non-interactive mode."""
        return {
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
    
    async def _phase_3_create_configuration(self, requirements: Dict[str, Any]) -> None:
        """Phase 3: Create deployment configuration."""
        logger.info("Phase 3: Creating deployment configuration...")
        
        if not self.analysis_result:
            raise RuntimeError("Project analysis must be completed first")
        
        questionnaire = UserRequirementsQuestionnaire(self.analysis_result)
        questionnaire.answers = requirements
        
        self.deployment_config = questionnaire.create_deployment_configuration()
        
        # Set file paths
        self.deployment_config.main_template_path = self.output_path / "main.bicep"
        for env_name in self.deployment_config.environments:
            param_file = self.output_path / f"main.{env_name}.bicepparam"
            self.deployment_config.set_parameter_file_path(env_name, param_file)
        
        logger.info(f"Configuration created for {len(self.deployment_config.environments)} environments")
    
    async def _phase_4_generate_templates(self) -> None:
        """Phase 4: Generate Bicep templates."""
        logger.info("Phase 4: Generating Bicep templates...")
        
        if not self.analysis_result or not self.deployment_config:
            raise RuntimeError("Analysis and configuration must be completed first")
        
        generator = BicepGenerator(
            project_path=self.project_path,
            output_path=self.output_path,
            mcp_client=self.mcp_client
        )
        
        # Set the analysis result and config
        generator.analysis_result = self.analysis_result
        generator.deployment_config = self.deployment_config
        
        # Generate templates without running full workflow
        await generator._generate_bicep_templates()
        
        # Store generated templates
        self.generated_templates = generator.generated_templates
        
        logger.info(f"Generated {len(self.generated_templates)} templates")
    
    async def _phase_5_validate_templates(self) -> None:
        """Phase 5: Validate generated templates."""
        logger.info("Phase 5: Validating templates...")
        
        if not hasattr(self, 'generated_templates'):
            raise RuntimeError("Templates must be generated first")
        
        validation_results = []
        
        for template_name, template in self.generated_templates.items():
            try:
                # Convert to ARM for validation
                arm_template = template.to_arm_template()
                
                # Validate with ARM validator
                result = await self.arm_validator.validate_template(arm_template)
                validation_results.append((template_name, result))
                
                if result.is_valid:
                    logger.info(f"Template '{template_name}' validation passed")
                else:
                    logger.warning(f"Template '{template_name}' validation issues: {result.errors}")
                    
            except Exception as e:
                logger.error(f"Failed to validate template '{template_name}': {e}")
        
        logger.info(f"Validation completed for {len(validation_results)} templates")
    
    async def _phase_6_write_files(self) -> Dict[str, Path]:
        """Phase 6: Write all files to disk."""
        logger.info("Phase 6: Writing files to disk...")
        
        # Ensure output directory exists
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        output_files = {}
        
        # Write Bicep templates
        if hasattr(self, 'generated_templates'):
            for template_name, template in self.generated_templates.items():
                bicep_content = template.to_bicep()
                
                if template_name == "main":
                    file_path = self.output_path / "main.bicep"
                else:
                    file_path = self.output_path / f"{template_name}.bicep"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(bicep_content)
                
                output_files[f"template-{template_name}"] = file_path
        
        # Write parameter files
        if self.deployment_config:
            for env_name, env_config in self.deployment_config.environments.items():
                param_content = self._generate_parameter_file_content(env_config)
                param_file = self.output_path / f"main.{env_name}.bicepparam"
                
                with open(param_file, 'w', encoding='utf-8') as f:
                    f.write(param_content)
                
                output_files[f"params-{env_name}"] = param_file
        
        # Write deployment scripts
        script_files = await self._write_deployment_scripts()
        output_files.update(script_files)
        
        # Write README
        readme_content = self._generate_readme_content()
        readme_file = self.output_path / "README.md"
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        output_files["readme"] = readme_file
        
        logger.info(f"Wrote {len(output_files)} files to {self.output_path}")
        return output_files
    
    def _generate_parameter_file_content(self, env_config) -> str:
        """Generate parameter file content for an environment."""
        if not self.analysis_result:
            raise RuntimeError("Analysis result required")
        
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
        
        return "\n".join(lines)
    
    async def _write_deployment_scripts(self) -> Dict[str, Path]:
        """Write deployment scripts."""
        script_files = {}
        
        if not self.deployment_config or not self.analysis_result:
            return script_files
        
        # PowerShell script
        ps_content = self._generate_powershell_script()
        ps_file = self.output_path / "deploy.ps1"
        
        with open(ps_file, 'w', encoding='utf-8') as f:
            f.write(ps_content)
        
        script_files["deploy-powershell"] = ps_file
        
        # Bash script
        bash_content = self._generate_bash_script()
        bash_file = self.output_path / "deploy.sh"
        
        with open(bash_file, 'w', encoding='utf-8') as f:
            f.write(bash_content)
        
        script_files["deploy-bash"] = bash_file
        
        return script_files
    
    def _generate_powershell_script(self) -> str:
        """Generate PowerShell deployment script."""
        if not self.deployment_config or not self.analysis_result:
            return ""
        
        environments = list(self.deployment_config.environments.keys())
        default_location = next(iter(self.deployment_config.environments.values())).location
        
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
    [string]$Location = "{default_location}",
    
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

$deploymentParams = @{{
    ResourceGroupName = $ResourceGroupName
    TemplateFile = $templateFile
    TemplateParameterFile = $parametersFile
    Name = "{self.analysis_result.project_path.name}-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
}}

if ($WhatIf) {{
    Write-Host "Running deployment validation..." -ForegroundColor Yellow
    New-AzResourceGroupDeployment @deploymentParams -WhatIf
}} else {{
    Write-Host "Starting deployment..." -ForegroundColor Green
    $deployment = New-AzResourceGroupDeployment @deploymentParams
    
    if ($deployment.ProvisioningState -eq "Succeeded") {{
        Write-Host "Deployment completed successfully!" -ForegroundColor Green
    }} else {{
        Write-Error "Deployment failed with state: $($deployment.ProvisioningState)"
    }}
}}
'''
    
    def _generate_bash_script(self) -> str:
        """Generate Bash deployment script."""
        if not self.deployment_config or not self.analysis_result:
            return ""
        
        environments = list(self.deployment_config.environments.keys())
        default_location = next(iter(self.deployment_config.environments.values())).location
        
        return f'''#!/bin/bash
# Azure Bicep Deployment Script for {self.analysis_result.project_path.name}
# Generated by Specify CLI on {datetime.now().isoformat()}

set -e

# Function to display usage
usage() {{
    echo "Usage: $0 -e <environment> -g <resource-group> [-l <location>] [-w]"
    echo "  -e: Environment ({', '.join(environments)})"
    echo "  -g: Resource group name"
    echo "  -l: Azure location (default: {default_location})"
    echo "  -w: What-if mode"
    exit 1
}}

# Default values
LOCATION="{default_location}"
WHAT_IF=""

# Parse arguments
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

echo "Deploying {self.analysis_result.project_path.name} to $ENVIRONMENT environment..."

# Check Azure CLI login
if ! az account show >/dev/null 2>&1; then
    echo "Please log in to Azure..."
    az login
fi

# Create resource group if needed
if ! az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
    echo "Creating resource group: $RESOURCE_GROUP"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
fi

# Deploy template
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
DEPLOYMENT_NAME="{self.analysis_result.project_path.name}-$(date +%Y%m%d-%H%M%S)"

az deployment group create \\
    --resource-group "$RESOURCE_GROUP" \\
    --template-file "$SCRIPT_DIR/main.bicep" \\
    --parameters "$SCRIPT_DIR/main.$ENVIRONMENT.bicepparam" \\
    --name "$DEPLOYMENT_NAME" \\
    $WHAT_IF

echo "Deployment completed!"
'''
    
    def _generate_readme_content(self) -> str:
        """Generate README content."""
        if not self.analysis_result or not self.deployment_config:
            return "# Infrastructure Templates\n\nGenerated by Specify CLI"
        
        environments = list(self.deployment_config.environments.keys())
        
        return f'''# {self.analysis_result.project_path.name} - Infrastructure

Azure infrastructure templates generated by Specify CLI.

## Project Information

- **Type**: {self.analysis_result.project_type.value}
- **Frameworks**: {', '.join([f.value for f in self.analysis_result.detected_frameworks])}
- **Generated**: {datetime.now().isoformat()}

## Files

- `main.bicep` - Main infrastructure template
{chr(10).join([f'- `main.{env}.bicepparam` - {env.title()} environment parameters' for env in environments])}
- `deploy.ps1` - PowerShell deployment script
- `deploy.sh` - Bash deployment script

## Quick Start

### Deploy to Development

```bash
# Using Azure CLI
./deploy.sh -e dev -g "rg-{self.analysis_result.project_path.name}-dev"

# Using PowerShell
./deploy.ps1 -Environment dev -ResourceGroupName "rg-{self.analysis_result.project_path.name}-dev"
```

### Deploy to Production

```bash
# Using Azure CLI
./deploy.sh -e prod -g "rg-{self.analysis_result.project_path.name}-prod"

# Using PowerShell  
./deploy.ps1 -Environment prod -ResourceGroupName "rg-{self.analysis_result.project_path.name}-prod"
```

## Environment Configuration

{chr(10).join([f'### {env.title()}' + chr(10) + f'- Location: {self.deployment_config.environments[env].location}' for env in environments])}

## Next Steps

1. Review and customize parameter files
2. Set up secure parameters in Azure Key Vault
3. Test deployment in development environment
4. Configure CI/CD pipeline for automated deployments

Generated by [Specify CLI](https://github.com/microsoft/spec-kit)
'''
    
    # Convenience methods for common workflows
    
    async def quick_generate(self, 
                           interactive: bool = False,
                           environments: Optional[List[str]] = None,
                           location: Optional[str] = None) -> Dict[str, Path]:
        """Quick generation with minimal configuration."""
        
        user_requirements = {}
        if environments:
            user_requirements["environments"] = environments
        if location:
            user_requirements["primary_location"] = location
        
        # Set non-interactive defaults
        user_requirements.update({
            "project_confirmation": True,
            "enable_monitoring": True,
            "security_level": "enhanced",
            "final_confirmation": True
        })
        
        return await self.run_complete_workflow(
            interactive=interactive,
            user_requirements=user_requirements,
            validate_output=True
        )
    
    async def analyze_only(self) -> ProjectAnalysisResult:
        """Run only project analysis."""
        await self._phase_1_analyze_project()
        if not self.analysis_result:
            raise RuntimeError("Analysis failed")
        return self.analysis_result
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get a summary of the project analysis."""
        if not self.analysis_result:
            return {}
        
        return {
            "project_type": self.analysis_result.project_type.value,
            "frameworks": [f.value for f in self.analysis_result.detected_frameworks],
            "confidence": self.analysis_result.confidence_score,
            "total_files": self.analysis_result.total_files,
            "resource_requirements": len(self.analysis_result.resource_requirements),
            "security_issues": len(self.analysis_result.security_analysis.security_issues) if self.analysis_result.security_analysis else 0
        }


# Convenience functions for common use cases

async def generate_bicep_templates(project_path: Path, 
                                 output_path: Optional[Path] = None,
                                 interactive: bool = True,
                                 environments: Optional[List[str]] = None,
                                 location: str = "eastus") -> Dict[str, Path]:
    """Convenience function to generate Bicep templates."""
    async with BicepOrchestrator(project_path, output_path) as orchestrator:
        return await orchestrator.quick_generate(
            interactive=interactive,
            environments=environments,
            location=location
        )


async def analyze_project(project_path: Path) -> ProjectAnalysisResult:
    """Convenience function to analyze a project."""
    async with BicepOrchestrator(project_path, enable_validation=False) as orchestrator:
        return await orchestrator.analyze_only()


# Export main classes and functions
__all__ = [
    "BicepOrchestrator",
    "generate_bicep_templates", 
    "analyze_project"
]