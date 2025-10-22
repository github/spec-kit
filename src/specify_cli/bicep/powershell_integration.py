"""Final PowerShell orchestration and command integration.

This module provides the final integration between PowerShell commands
and the Python-based Bicep generation system.
"""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from .orchestrator import GenerationOrchestrator, GenerationResult
from .analyzer import ProjectAnalyzer
from .questionnaire import InteractiveQuestionnaire
from .generator import BicepGenerator
from .arm_validator import ARMTemplateValidator
from .best_practices_validator import BestPracticesValidator
from ..utils.file_scanner import FileScanner
from .mcp_client import AzureMCPClient

logger = logging.getLogger(__name__)


@dataclass
class PowerShellIntegrationResult:
    """Result of PowerShell integration operation."""
    success: bool
    message: str
    generated_files: List[str] = None
    validation_results: Dict[str, Any] = None
    duration_seconds: float = 0.0
    errors: List[str] = None
    
    def to_json(self) -> str:
        """Convert result to JSON for PowerShell consumption."""
        return json.dumps(asdict(self), indent=2, default=str)


class PowerShellBicepOrchestrator:
    """Main orchestrator for PowerShell command integration."""
    
    def __init__(self):
        """Initialize the PowerShell orchestrator."""
        self.start_time = None
        
    async def generate_bicep_templates_from_powershell(
        self,
        project_path: str,
        output_path: str,
        project_name: str,
        options: Dict[str, Any]
    ) -> PowerShellIntegrationResult:
        """Main entry point for PowerShell-initiated template generation.
        
        Args:
            project_path: Path to the project to analyze
            output_path: Path where templates should be generated
            project_name: Name of the project
            options: Dictionary of generation options from PowerShell
            
        Returns:
            PowerShellIntegrationResult with generation results
        """
        self.start_time = datetime.now()
        
        try:
            logger.info(f"Starting PowerShell-initiated generation for project: {project_name}")
            logger.info(f"Project path: {project_path}")
            logger.info(f"Output path: {output_path}")
            
            # Convert paths
            project_path_obj = Path(project_path).resolve()
            output_path_obj = Path(output_path).resolve()
            
            # Validate inputs
            if not project_path_obj.exists():
                return PowerShellIntegrationResult(
                    success=False,
                    message=f"Project path does not exist: {project_path}",
                    errors=[f"Invalid project path: {project_path}"]
                )
            
            # Initialize components
            file_scanner = FileScanner()
            mcp_client = AzureMCPClient()
            
            analyzer = ProjectAnalyzer(file_scanner)
            questionnaire = InteractiveQuestionnaire()
            generator = BicepGenerator(mcp_client=mcp_client)
            
            orchestrator = GenerationOrchestrator(
                analyzer=analyzer,
                questionnaire=questionnaire,
                generator=generator
            )
            
            # Setup MCP client if available
            try:
                await mcp_client.connect()
                logger.info("Connected to Azure MCP server successfully")
            except Exception as e:
                logger.warning(f"Could not connect to Azure MCP server: {e}")
            
            # Process options
            generation_options = self._process_powershell_options(options)
            
            # Run generation
            logger.info("Starting template generation workflow")
            result = await orchestrator.generate_bicep_templates(
                project_path=project_path_obj,
                output_path=output_path_obj,
                project_name=project_name,
                options=generation_options
            )
            
            # Run validation if requested
            validation_results = None
            if generation_options.get('validate_templates', True):
                validation_results = await self._run_validation(
                    output_path_obj, generation_options
                )
            
            # Calculate duration
            duration = (datetime.now() - self.start_time).total_seconds()
            
            # Build result
            if result.success:
                generated_files = [info['path'] for info in result.generated_templates]
                
                return PowerShellIntegrationResult(
                    success=True,
                    message=f"Successfully generated {len(generated_files)} template files",
                    generated_files=generated_files,
                    validation_results=validation_results,
                    duration_seconds=duration
                )
            else:
                return PowerShellIntegrationResult(
                    success=False,
                    message="Template generation failed",
                    errors=result.errors,
                    duration_seconds=duration
                )
                
        except Exception as e:
            logger.error(f"PowerShell generation failed: {e}", exc_info=True)
            duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0.0
            
            return PowerShellIntegrationResult(
                success=False,
                message=f"Generation failed: {str(e)}",
                errors=[str(e)],
                duration_seconds=duration
            )
        
        finally:
            # Cleanup MCP client
            try:
                if 'mcp_client' in locals():
                    await mcp_client.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting MCP client: {e}")
    
    def _process_powershell_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate options from PowerShell.
        
        Args:
            options: Raw options from PowerShell
            
        Returns:
            Processed options dictionary
        """
        processed = {\n            'validate_templates': options.get('ValidateTemplates', True),\n            'enable_best_practices': options.get('EnableBestPractices', True),\n            'use_architecture_patterns': options.get('UseArchitecturePatterns', True),\n            'force_pattern': options.get('ForcePattern'),\n            'environments': options.get('Environments', ['dev']),\n            'primary_region': options.get('PrimaryRegion', 'East US'),\n            'interactive_mode': options.get('InteractiveMode', False),\n            'backup_existing': options.get('BackupExisting', True),\n            'dry_run': options.get('DryRun', False)\n        }\n        \n        # Ensure environments is a list\n        if isinstance(processed['environments'], str):\n            processed['environments'] = [processed['environments']]\n        \n        logger.info(f\"Processed PowerShell options: {processed}\")\n        return processed\n    \n    async def _run_validation(\n        self,\n        output_path: Path,\n        options: Dict[str, Any]\n    ) -> Dict[str, Any]:\n        \"\"\"Run validation on generated templates.\n        \n        Args:\n            output_path: Path containing generated templates\n            options: Generation options\n            \n        Returns:\n            Validation results dictionary\n        \"\"\"\n        validation_results = {\n            'overall_success': True,\n            'validated_files': [],\n            'validation_summary': {\n                'total_files': 0,\n                'passed': 0,\n                'failed': 0,\n                'warnings': 0\n            },\n            'best_practices_scores': {},\n            'errors': []\n        }\n        \n        try:\n            logger.info(\"Running template validation\")\n            \n            # Find all Bicep files\n            bicep_files = list(output_path.glob('*.bicep'))\n            validation_results['validation_summary']['total_files'] = len(bicep_files)\n            \n            if not bicep_files:\n                validation_results['errors'].append(\"No Bicep files found to validate\")\n                validation_results['overall_success'] = False\n                return validation_results\n            \n            # Initialize validators\n            arm_validator = ARMTemplateValidator()\n            best_practices_validator = BestPracticesValidator(arm_validator)\n            \n            # Validate each file\n            for bicep_file in bicep_files:\n                try:\n                    logger.info(f\"Validating file: {bicep_file.name}\")\n                    \n                    # Run comprehensive validation\n                    file_results = await arm_validator.validate_template_comprehensive(\n                        bicep_file,\n                        enable_best_practices=options.get('enable_best_practices', True)\n                    )\n                    \n                    validation_results['validated_files'].append({\n                        'file': str(bicep_file.name),\n                        'success': file_results['overall_success'],\n                        'issues': file_results['arm_validation']['issues'] if file_results.get('arm_validation') else [],\n                        'best_practices_score': file_results.get('best_practices_assessment', {}).get('overall_score', 0.0)\n                    })\n                    \n                    # Update summary\n                    if file_results['overall_success']:\n                        validation_results['validation_summary']['passed'] += 1\n                    else:\n                        validation_results['validation_summary']['failed'] += 1\n                    \n                    # Count warnings\n                    if file_results.get('arm_validation'):\n                        warnings = len([i for i in file_results['arm_validation']['issues'] if i['severity'] == 'warning'])\n                        validation_results['validation_summary']['warnings'] += warnings\n                    \n                    # Store best practices scores\n                    if file_results.get('best_practices_assessment'):\n                        validation_results['best_practices_scores'][bicep_file.name] = {\n                            'overall': file_results['best_practices_assessment']['overall_score'],\n                            'pillars': file_results['best_practices_assessment']['pillar_scores']\n                        }\n                    \n                except Exception as e:\n                    logger.error(f\"Error validating {bicep_file.name}: {e}\")\n                    validation_results['errors'].append(f\"Validation failed for {bicep_file.name}: {str(e)}\")\n                    validation_results['validation_summary']['failed'] += 1\n            \n            # Update overall success\n            validation_results['overall_success'] = validation_results['validation_summary']['failed'] == 0\n            \n            logger.info(f\"Validation complete: {validation_results['validation_summary']}\")\n            \n        except Exception as e:\n            logger.error(f\"Validation process failed: {e}\")\n            validation_results['errors'].append(f\"Validation process error: {str(e)}\")\n            validation_results['overall_success'] = False\n        \n        return validation_results\n    \n    def validate_bicep_file_sync(\n        self,\n        template_path: str,\n        enable_best_practices: bool = True\n    ) -> Dict[str, Any]:\n        \"\"\"Synchronous validation for individual Bicep files (PowerShell callable).\n        \n        Args:\n            template_path: Path to Bicep template file\n            enable_best_practices: Whether to run best practices validation\n            \n        Returns:\n            Validation results dictionary\n        \"\"\"\n        try:\n            # Run async validation in sync context\n            return asyncio.run(self._validate_single_file(\n                Path(template_path), enable_best_practices\n            ))\n        except Exception as e:\n            return {\n                'success': False,\n                'error': str(e),\n                'message': f\"Validation failed for {template_path}\"\n            }\n    \n    async def _validate_single_file(\n        self,\n        template_path: Path,\n        enable_best_practices: bool\n    ) -> Dict[str, Any]:\n        \"\"\"Validate a single Bicep file.\n        \n        Args:\n            template_path: Path to template file\n            enable_best_practices: Whether to run best practices\n            \n        Returns:\n            Validation results\n        \"\"\"\n        try:\n            arm_validator = ARMTemplateValidator()\n            \n            result = await arm_validator.validate_template_comprehensive(\n                template_path,\n                enable_best_practices=enable_best_practices\n            )\n            \n            return {\n                'success': result['overall_success'],\n                'file': str(template_path.name),\n                'validation_time': result['validation_time'],\n                'issues': result.get('arm_validation', {}).get('issues', []),\n                'best_practices': result.get('best_practices_assessment', {}),\n                'summary': result.get('summary', {})\n            }\n            \n        except Exception as e:\n            logger.error(f\"Single file validation failed: {e}\")\n            return {\n                'success': False,\n                'error': str(e),\n                'file': str(template_path.name)\n            }\n\n\ndef create_powershell_orchestrator() -> PowerShellBicepOrchestrator:\n    \"\"\"Factory function for PowerShell integration.\n    \n    Returns:\n        Configured PowerShellBicepOrchestrator instance\n    \"\"\"\n    return PowerShellBicepOrchestrator()\n\n\n# PowerShell integration functions\ndef run_bicep_generation_from_powershell(\n    project_path: str,\n    output_path: str,\n    project_name: str,\n    options_json: str\n) -> str:\n    \"\"\"Main entry point for PowerShell bicep generation.\n    \n    Args:\n        project_path: Path to project\n        output_path: Output directory\n        project_name: Project name\n        options_json: JSON string with options\n        \n    Returns:\n        JSON string with results\n    \"\"\"\n    try:\n        # Parse options\n        options = json.loads(options_json) if options_json else {}\n        \n        # Create orchestrator\n        orchestrator = create_powershell_orchestrator()\n        \n        # Run generation\n        result = asyncio.run(\n            orchestrator.generate_bicep_templates_from_powershell(\n                project_path, output_path, project_name, options\n            )\n        )\n        \n        return result.to_json()\n        \n    except Exception as e:\n        error_result = PowerShellIntegrationResult(\n            success=False,\n            message=f\"PowerShell integration error: {str(e)}\",\n            errors=[str(e)]\n        )\n        return error_result.to_json()\n\n\ndef validate_bicep_file_from_powershell(\n    template_path: str,\n    enable_best_practices: bool = True\n) -> str:\n    \"\"\"Validate a single Bicep file from PowerShell.\n    \n    Args:\n        template_path: Path to Bicep file\n        enable_best_practices: Enable best practices validation\n        \n    Returns:\n        JSON string with validation results\n    \"\"\"\n    try:\n        orchestrator = create_powershell_orchestrator()\n        result = orchestrator.validate_bicep_file_sync(\n            template_path, enable_best_practices\n        )\n        return json.dumps(result, indent=2, default=str)\n        \n    except Exception as e:\n        error_result = {\n            'success': False,\n            'error': str(e),\n            'message': f\"Validation error: {str(e)}\"\n        }\n        return json.dumps(error_result, indent=2)\n\n\n# CLI entry point for testing\nif __name__ == \"__main__\":\n    import argparse\n    \n    parser = argparse.ArgumentParser(description=\"PowerShell Bicep Orchestrator\")\n    parser.add_argument(\"command\", choices=[\"generate\", \"validate\"])\n    parser.add_argument(\"--project-path\", required=True)\n    parser.add_argument(\"--output-path\")\n    parser.add_argument(\"--project-name\")\n    parser.add_argument(\"--options\", default=\"{}\")\n    parser.add_argument(\"--template-path\")\n    \n    args = parser.parse_args()\n    \n    if args.command == \"generate\":\n        result = run_bicep_generation_from_powershell(\n            args.project_path,\n            args.output_path or f\"{args.project_path}/infrastructure\",\n            args.project_name or Path(args.project_path).name,\n            args.options\n        )\n        print(result)\n        \n    elif args.command == \"validate\":\n        result = validate_bicep_file_from_powershell(\n            args.template_path or args.project_path\n        )\n        print(result)