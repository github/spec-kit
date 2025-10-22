"""
Template update orchestrator for managing intelligent template regeneration.

This module coordinates template updates based on detected project changes,
manages dependencies, and ensures consistent deployment across environments.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import json
from concurrent.futures import ThreadPoolExecutor

from .models.template_update import (
    TemplateUpdateManifest, ResourceChange, ChangeType, ChangeSeverity, 
    ChangeImpact, TemplateVersion, EnvironmentStatus, DependencyInfo
)
from .models.project_analysis import ProjectAnalysisResult
from .models.bicep_template import BicepTemplate
from .analyzer import ProjectAnalyzer
from .generator import BicepGenerator
from .arm_validator import ARMValidator
from .best_practices_validator import BestPracticesValidator
from .template_manager import TemplateManager

logger = logging.getLogger(__name__)


class UpdateStrategy:
    """Strategy for handling template updates."""
    
    CONSERVATIVE = "conservative"  # Only update on critical changes
    INCREMENTAL = "incremental"   # Update on medium+ severity changes
    AGGRESSIVE = "aggressive"     # Update on any detected changes


class TemplateUpdateOrchestrator:
    """
    Orchestrates intelligent template updates based on project changes.
    
    This orchestrator analyzes project changes, determines update requirements,
    manages dependencies, and coordinates template regeneration across environments.
    """
    
    def __init__(
        self,
        template_manager: TemplateManager,
        project_analyzer: ProjectAnalyzer,
        bicep_generator: BicepGenerator,
        arm_validator: ARMValidator,
        best_practices_validator: BestPracticesValidator
    ):
        self.template_manager = template_manager
        self.project_analyzer = project_analyzer
        self.bicep_generator = bicep_generator
        self.arm_validator = arm_validator
        self.best_practices_validator = best_practices_validator
        
        # Update configuration
        self.update_strategy = UpdateStrategy.INCREMENTAL
        self.max_concurrent_updates = 3
        self.validation_timeout_seconds = 300
        self.backup_enabled = True
        
    async def orchestrate_update(
        self,
        project_path: Path,
        manifest_path: Optional[Path] = None,
        force_update: bool = False,
        target_environments: Optional[List[str]] = None
    ) -> Tuple[TemplateUpdateManifest, List[str]]:
        """
        Orchestrate a complete template update cycle.
        
        Args:
            project_path: Root path of the project
            manifest_path: Path to existing manifest file
            force_update: Force update regardless of change severity
            target_environments: Specific environments to update (None for all)
            
        Returns:
            Tuple of (updated_manifest, status_messages)
        """
        logger.info(f"Starting template update orchestration for {project_path}")
        status_messages = []
        
        try:
            # Load existing manifest or create new one
            manifest = await self._load_or_create_manifest(project_path, manifest_path)
            
            # Analyze project for changes
            status_messages.append("🔍 Analyzing project changes...")
            updated_manifest = self.project_analyzer.analyze_project_changes(
                project_path, manifest
            )
            
            # Determine if update is needed
            if not force_update and not self._should_update_templates(updated_manifest):
                status_messages.append("✅ No template updates required")
                return updated_manifest, status_messages
            
            # Plan update execution
            status_messages.append("📋 Planning template updates...")
            update_plan = self._create_update_plan(updated_manifest, target_environments)
            
            # Execute updates
            status_messages.append("🔄 Executing template updates...")
            execution_results = await self._execute_update_plan(
                project_path, updated_manifest, update_plan
            )
            
            # Update manifest with results
            self._update_manifest_with_results(updated_manifest, execution_results)
            
            # Save updated manifest
            if manifest_path:
                await self._save_manifest(updated_manifest, manifest_path)
            
            status_messages.extend(execution_results.get('messages', []))
            status_messages.append("✅ Template update orchestration completed")
            
            return updated_manifest, status_messages
            
        except Exception as e:
            error_msg = f"❌ Template update orchestration failed: {e}"
            logger.error(error_msg)
            status_messages.append(error_msg)
            
            # Return original manifest if available
            if 'manifest' in locals():
                return manifest, status_messages
            else:
                # Create minimal manifest for error state
                error_manifest = TemplateUpdateManifest(
                    project_path=project_path,
                    project_name=project_path.name
                )
                return error_manifest, status_messages
    
    async def _load_or_create_manifest(
        self, 
        project_path: Path, 
        manifest_path: Optional[Path]
    ) -> TemplateUpdateManifest:
        """Load existing manifest or create new one."""
        if manifest_path and manifest_path.exists():
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)
                return TemplateUpdateManifest(**manifest_data)
            except Exception as e:
                logger.warning(f"Failed to load manifest from {manifest_path}: {e}")
        
        # Create new manifest
        return TemplateUpdateManifest(
            project_path=project_path,
            project_name=project_path.name
        )
    
    def _should_update_templates(self, manifest: TemplateUpdateManifest) -> bool:
        """Determine if templates should be updated based on strategy and changes."""
        if not manifest.pending_changes:
            return False
        
        if self.update_strategy == UpdateStrategy.AGGRESSIVE:
            return True
        
        # Check change severity thresholds
        severity_threshold = {
            UpdateStrategy.CONSERVATIVE: ChangeSeverity.CRITICAL,
            UpdateStrategy.INCREMENTAL: ChangeSeverity.MEDIUM
        }.get(self.update_strategy, ChangeSeverity.MEDIUM)
        
        for change in manifest.pending_changes:
            if self._severity_meets_threshold(change.severity, severity_threshold):
                return True
        
        return False
    
    def _severity_meets_threshold(
        self, 
        change_severity: ChangeSeverity, 
        threshold: ChangeSeverity
    ) -> bool:
        """Check if change severity meets update threshold."""
        severity_order = [
            ChangeSeverity.LOW,
            ChangeSeverity.MEDIUM,
            ChangeSeverity.HIGH,
            ChangeSeverity.CRITICAL
        ]
        
        return severity_order.index(change_severity) >= severity_order.index(threshold)
    
    def _create_update_plan(
        self,
        manifest: TemplateUpdateManifest,
        target_environments: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Create execution plan for template updates."""
        plan = {
            'environments': target_environments or list(manifest.environments.keys()) or ['dev'],
            'changes_to_apply': [],
            'dependency_order': [],
            'validation_required': False,
            'backup_required': False
        }
        
        # Categorize changes by severity and impact
        critical_changes = []
        high_changes = []
        medium_changes = []
        
        for change in manifest.pending_changes:
            if change.severity == ChangeSeverity.CRITICAL:
                critical_changes.append(change)
            elif change.severity == ChangeSeverity.HIGH:
                high_changes.append(change)
            elif change.severity == ChangeSeverity.MEDIUM:
                medium_changes.append(change)
        
        # Order changes by dependency and severity
        plan['changes_to_apply'] = critical_changes + high_changes + medium_changes
        
        # Determine validation requirements
        plan['validation_required'] = any(
            change.requires_validation for change in plan['changes_to_apply']
        )
        
        # Determine backup requirements
        plan['backup_required'] = (
            self.backup_enabled and 
            any(change.severity in [ChangeSeverity.HIGH, ChangeSeverity.CRITICAL] 
                for change in plan['changes_to_apply'])
        )
        
        # Build dependency order
        plan['dependency_order'] = self._resolve_update_dependencies(manifest, plan['changes_to_apply'])
        
        return plan
    
    def _resolve_update_dependencies(
        self,
        manifest: TemplateUpdateManifest,
        changes: List[ResourceChange]
    ) -> List[str]:
        """Resolve dependency order for template updates."""
        # Simple dependency resolution based on resource types
        dependency_priority = {
            'Microsoft.Network/virtualNetworks': 1,
            'Microsoft.Network/networkSecurityGroups': 2,
            'Microsoft.Storage/storageAccounts': 3,
            'Microsoft.KeyVault/vaults': 4,
            'Microsoft.Sql/servers': 5,
            'Microsoft.Web/serverfarms': 6,
            'Microsoft.Web/sites': 7,
            'Microsoft.Insights/components': 8,
        }
        
        # Group changes by resource type and sort by priority
        resource_order = []
        for change in changes:
            if change.resource_type not in resource_order:
                resource_order.append(change.resource_type)
        
        resource_order.sort(key=lambda x: dependency_priority.get(x, 999))
        
        return resource_order
    
    async def _execute_update_plan(
        self,
        project_path: Path,
        manifest: TemplateUpdateManifest,
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the template update plan."""
        results = {
            'success': False,
            'messages': [],
            'updated_templates': [],
            'validation_results': {},
            'deployment_status': {}
        }
        
        try:
            # Create backup if required
            if plan['backup_required']:
                results['messages'].append("💾 Creating backup of existing templates...")
                await self._create_backup(project_path, manifest)
            
            # Generate updated templates
            results['messages'].append("🏗️ Generating updated Bicep templates...")
            template_results = await self._generate_updated_templates(
                project_path, manifest, plan
            )
            results['updated_templates'] = template_results
            
            # Validate templates if required
            if plan['validation_required']:
                results['messages'].append("✅ Validating updated templates...")
                validation_results = await self._validate_updated_templates(
                    template_results, plan
                )
                results['validation_results'] = validation_results
                
                # Check for validation failures
                if any(not result.get('valid', False) for result in validation_results.values()):
                    results['messages'].append("❌ Template validation failed")
                    return results
            
            # Update version information
            new_version = manifest.increment_version(
                "major" if any(c.severity == ChangeSeverity.CRITICAL for c in plan['changes_to_apply'])
                else "minor" if any(c.severity == ChangeSeverity.HIGH for c in plan['changes_to_apply'])
                else "patch"
            )
            
            # Update environment status
            for env_name in plan['environments']:
                self._update_environment_status(manifest, env_name, new_version)
            
            # Clear pending changes
            manifest.pending_changes = []
            
            results['success'] = True
            results['messages'].append(f"🎉 Templates updated successfully to version {new_version}")
            
        except Exception as e:
            results['messages'].append(f"❌ Update execution failed: {e}")
            logger.error(f"Template update execution failed: {e}")
        
        return results
    
    async def _create_backup(self, project_path: Path, manifest: TemplateUpdateManifest) -> None:
        """Create backup of existing templates."""
        backup_dir = project_path / 'bicep-backups' / datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Find existing Bicep files
        bicep_files = list(project_path.rglob('*.bicep'))
        
        for bicep_file in bicep_files:
            if 'backup' not in str(bicep_file):  # Don't backup backups
                relative_path = bicep_file.relative_to(project_path)
                backup_file = backup_dir / relative_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                backup_file.write_text(bicep_file.read_text(encoding='utf-8'), encoding='utf-8')
        
        logger.info(f"Created backup in {backup_dir}")
    
    async def _generate_updated_templates(
        self,
        project_path: Path,
        manifest: TemplateUpdateManifest,
        plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate updated Bicep templates based on changes."""
        templates = []
        
        try:
            # Re-analyze project to get current state
            analysis_result = await self.project_analyzer.analyze_project(project_path)
            
            # Generate templates with updated configuration
            bicep_templates = await self.bicep_generator.generate_templates(
                analysis_result,
                output_dir=project_path / 'infrastructure'
            )
            
            for template in bicep_templates:
                templates.append({
                    'name': template.name,
                    'path': template.output_path,
                    'content': template.content,
                    'parameters': template.parameters,
                    'outputs': template.outputs
                })
            
        except Exception as e:
            logger.error(f"Failed to generate updated templates: {e}")
            raise
        
        return templates
    
    async def _validate_updated_templates(
        self,
        templates: List[Dict[str, Any]],
        plan: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Validate updated templates."""
        validation_results = {}
        
        for template in templates:
            template_name = template['name']
            
            try:
                # ARM validation
                arm_result = await self.arm_validator.validate_template_async(
                    template['content'],
                    template.get('parameters', {}),
                    timeout_seconds=self.validation_timeout_seconds
                )
                
                # Best practices validation
                bp_result = await self.best_practices_validator.validate_template(
                    template['content'],
                    template.get('parameters', {})
                )
                
                validation_results[template_name] = {
                    'valid': arm_result.is_valid and bp_result.overall_score >= 0.7,
                    'arm_validation': arm_result.dict(),
                    'best_practices': bp_result.dict(),
                    'errors': arm_result.errors + bp_result.get_critical_issues(),
                    'warnings': arm_result.warnings + bp_result.get_warnings()
                }
                
            except Exception as e:
                validation_results[template_name] = {
                    'valid': False,
                    'errors': [f"Validation failed: {e}"],
                    'warnings': []
                }
        
        return validation_results
    
    def _update_environment_status(
        self,
        manifest: TemplateUpdateManifest,
        environment_name: str,
        new_version: str
    ) -> None:
        """Update environment status with new version."""
        if environment_name not in manifest.environments:
            manifest.environments[environment_name] = EnvironmentStatus(
                environment_name=environment_name,
                current_version=new_version
            )
        else:
            env_status = manifest.environments[environment_name]
            env_status.target_version = new_version
            env_status.requires_update = True
            env_status.pending_changes = []
    
    async def _save_manifest(
        self, 
        manifest: TemplateUpdateManifest, 
        manifest_path: Path
    ) -> None:
        """Save manifest to file."""
        try:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest.dict(), f, indent=2, default=str)
            
            logger.info(f"Saved manifest to {manifest_path}")
            
        except Exception as e:
            logger.error(f"Failed to save manifest: {e}")
            raise
    
    # ==================== DEPENDENCY MANAGEMENT ====================
    
    def analyze_template_dependencies(
        self, 
        manifest: TemplateUpdateManifest
    ) -> List[DependencyInfo]:
        """Analyze dependencies between templates."""
        dependencies = []
        
        # Detect circular dependencies
        cycles = manifest.detect_circular_dependencies()
        
        for cycle in cycles:
            for i, template in enumerate(cycle[:-1]):
                next_template = cycle[i + 1]
                
                dependencies.append(DependencyInfo(
                    template_name=template,
                    dependency_type='circular',
                    dependency_path=next_template,
                    is_optional=False,
                    circular_dependencies=cycle
                ))
        
        return dependencies
    
    def resolve_dependency_conflicts(
        self,
        manifest: TemplateUpdateManifest,
        dependencies: List[DependencyInfo]
    ) -> List[str]:
        """Resolve dependency conflicts and return resolution steps."""
        resolution_steps = []
        
        # Handle circular dependencies
        circular_deps = [dep for dep in dependencies if dep.circular_dependencies]
        
        if circular_deps:
            resolution_steps.append("⚠️  Circular dependencies detected:")
            
            for dep in circular_deps:
                cycle_str = " -> ".join(dep.circular_dependencies)
                resolution_steps.append(f"   {cycle_str}")
            
            resolution_steps.append("🔧 Recommended actions:")
            resolution_steps.append("   1. Extract shared resources to separate module")
            resolution_steps.append("   2. Use parameters instead of direct references")
            resolution_steps.append("   3. Restructure template hierarchy")
        
        return resolution_steps
    
    # ==================== ENVIRONMENT SYNCHRONIZATION ====================
    
    async def synchronize_environments(
        self,
        manifest: TemplateUpdateManifest,
        source_environment: str,
        target_environments: List[str]
    ) -> Dict[str, bool]:
        """Synchronize template versions across environments."""
        sync_results = {}
        
        source_env = manifest.environments.get(source_environment)
        if not source_env:
            logger.error(f"Source environment {source_environment} not found")
            return {env: False for env in target_environments}
        
        source_version = source_env.current_version
        
        for target_env_name in target_environments:
            try:
                if target_env_name not in manifest.environments:
                    manifest.environments[target_env_name] = EnvironmentStatus(
                        environment_name=target_env_name,
                        current_version="0.0.0"
                    )
                
                target_env = manifest.environments[target_env_name]
                target_env.target_version = source_version
                target_env.requires_update = True
                
                sync_results[target_env_name] = True
                logger.info(f"Scheduled {target_env_name} for sync to version {source_version}")
                
            except Exception as e:
                logger.error(f"Failed to sync environment {target_env_name}: {e}")
                sync_results[target_env_name] = False
        
        return sync_results
    
    # ==================== VERSION MANAGEMENT ====================
    
    def create_template_version(
        self,
        manifest: TemplateUpdateManifest,
        version: str,
        description: str,
        changes: List[ResourceChange]
    ) -> TemplateVersion:
        """Create a new template version."""
        # Count changes by type
        change_summary = {}
        for change in changes:
            change_summary[change.change_type] = change_summary.get(change.change_type, 0) + 1
        
        # Identify breaking changes
        breaking_changes = []
        for change in changes:
            if change.severity == ChangeSeverity.CRITICAL and change.requires_redeployment:
                breaking_changes.append(f"{change.resource_name}: {change.change_type.value}")
        
        template_version = TemplateVersion(
            version=version,
            description=description,
            change_summary=change_summary,
            breaking_changes=breaking_changes
        )
        
        manifest.templates[version] = template_version
        return template_version
    
    def get_version_history(
        self, 
        manifest: TemplateUpdateManifest, 
        limit: int = 10
    ) -> List[TemplateVersion]:
        """Get version history sorted by timestamp."""
        versions = list(manifest.templates.values())
        versions.sort(key=lambda v: v.timestamp, reverse=True)
        return versions[:limit]
    
    def compare_versions(
        self,
        manifest: TemplateUpdateManifest,
        version_a: str,
        version_b: str
    ) -> Dict[str, Any]:
        """Compare two template versions."""
        v_a = manifest.templates.get(version_a)
        v_b = manifest.templates.get(version_b)
        
        if not v_a or not v_b:
            return {'error': 'One or both versions not found'}
        
        comparison = {
            'version_a': version_a,
            'version_b': version_b,
            'time_diff': (v_b.timestamp - v_a.timestamp).total_seconds(),
            'change_diff': {},
            'breaking_changes': {
                'added': set(v_b.breaking_changes) - set(v_a.breaking_changes),
                'removed': set(v_a.breaking_changes) - set(v_b.breaking_changes)
            }
        }
        
        # Compare change summaries
        all_change_types = set(v_a.change_summary.keys()) | set(v_b.change_summary.keys())
        
        for change_type in all_change_types:
            count_a = v_a.change_summary.get(change_type, 0)
            count_b = v_b.change_summary.get(change_type, 0)
            comparison['change_diff'][change_type] = count_b - count_a
        
        return comparison