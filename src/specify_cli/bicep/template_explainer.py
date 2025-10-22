"""
Template explanation and documentation generator for Bicep templates.

This module provides detailed explanations of Bicep templates, resource relationships,
best practices documentation, and educational content generation.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
import json
import re
from dataclasses import dataclass, field
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.tree import Tree

from .mcp_client import MCPClient
from .cost_estimator import CostEstimator
from .security_analyzer import SecurityAnalyzer

logger = logging.getLogger(__name__)
console = Console()


class ExplanationLevel(str, Enum):
    """Levels of explanation detail."""
    
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class DocumentationFormat(str, Enum):
    """Documentation output formats."""
    
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    RICH_TEXT = "rich_text"


@dataclass
class ResourceExplanation:
    """Explanation of a single Azure resource."""
    
    resource_name: str
    resource_type: str
    
    # Basic information
    display_name: str
    description: str
    purpose: str
    
    # Technical details
    api_version: str
    location: str
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    
    # Configuration analysis
    key_properties: Dict[str, Any] = field(default_factory=dict)
    security_considerations: List[str] = field(default_factory=list)
    cost_factors: List[str] = field(default_factory=list)
    
    # Best practices
    recommendations: List[str] = field(default_factory=list)
    common_issues: List[str] = field(default_factory=list)
    
    # Documentation links
    documentation_urls: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TemplateExplanation:
    """Complete explanation of a Bicep template."""
    
    template_name: str
    template_path: str
    
    # Overview
    title: str
    description: str
    purpose: str
    target_audience: str
    
    # Template structure
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, ResourceExplanation] = field(default_factory=dict)
    outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Architecture analysis
    architecture_overview: str = ""
    resource_relationships: List[Tuple[str, str, str]] = field(default_factory=list)  # (from, to, type)
    deployment_order: List[str] = field(default_factory=list)
    
    # Analysis results
    estimated_cost: Optional[float] = None
    security_score: Optional[float] = None
    complexity_score: int = 0  # 1-10
    
    # Educational content
    learning_objectives: List[str] = field(default_factory=list)
    key_concepts: List[str] = field(default_factory=list)
    troubleshooting_tips: List[str] = field(default_factory=list)
    
    # Metadata
    explanation_level: ExplanationLevel = ExplanationLevel.INTERMEDIATE
    generated_at: datetime = field(default_factory=datetime.utcnow)


class TemplateExplainer:
    """
    Template explanation and documentation generator for Bicep templates.
    
    Provides detailed explanations, resource analysis, and educational
    content generation for Azure infrastructure templates.
    """
    
    def __init__(self):
        self.mcp_client = MCPClient()
        self.cost_estimator = CostEstimator()
        self.security_analyzer = SecurityAnalyzer()
        
        # Knowledge base
        self.resource_knowledge = self._initialize_resource_knowledge()
        self.concept_definitions = self._initialize_concept_definitions()
        self.best_practices = self._initialize_best_practices()
    
    async def explain_template(
        self,
        template_path: Path,
        level: ExplanationLevel = ExplanationLevel.INTERMEDIATE,
        include_cost_analysis: bool = True,
        include_security_analysis: bool = True
    ) -> TemplateExplanation:
        """
        Generate comprehensive explanation of a Bicep template.
        
        Args:
            template_path: Path to the Bicep template file
            level: Level of explanation detail
            include_cost_analysis: Whether to include cost analysis
            include_security_analysis: Whether to include security analysis
            
        Returns:
            Complete template explanation
        """
        logger.info(f"Generating explanation for template: {template_path}")
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        # Load and parse template
        template_content = template_path.read_text(encoding='utf-8')
        
        try:
            # Assume JSON format (ARM template) for now
            template_data = json.loads(template_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse template as JSON: {e}")
            # In real implementation, would handle Bicep parsing
            raise ValueError(f"Unable to parse template: {e}")
        
        # Create base explanation
        explanation = TemplateExplanation(
            template_name=template_path.stem,
            template_path=str(template_path),
            title=self._generate_template_title(template_data),
            description=self._extract_template_description(template_data),
            purpose=self._infer_template_purpose(template_data),
            target_audience=self._determine_target_audience(level),
            explanation_level=level
        )
        
        # Analyze template structure
        await self._analyze_parameters(template_data, explanation)
        await self._analyze_variables(template_data, explanation)
        await self._analyze_resources(template_data, explanation)
        await self._analyze_outputs(template_data, explanation)
        
        # Generate architecture analysis
        await self._analyze_architecture(template_data, explanation)
        
        # Run cost analysis if requested
        if include_cost_analysis:
            await self._add_cost_analysis(template_data, explanation)
        
        # Run security analysis if requested
        if include_security_analysis:
            await self._add_security_analysis(template_data, explanation)
        
        # Generate educational content
        await self._generate_educational_content(explanation, level)
        
        logger.info(f"Explanation generated with {len(explanation.resources)} resources analyzed")
        
        return explanation
    
    async def display_explanation(
        self,
        explanation: TemplateExplanation,
        format: DocumentationFormat = DocumentationFormat.RICH_TEXT
    ):
        """Display template explanation in specified format."""
        
        if format == DocumentationFormat.RICH_TEXT:
            await self._display_rich_explanation(explanation)
        elif format == DocumentationFormat.MARKDOWN:
            markdown_content = await self._generate_markdown_explanation(explanation)
            console.print(Markdown(markdown_content))
        else:
            console.print(f"[yellow]Format {format} not yet implemented[/yellow]")
    
    async def _display_rich_explanation(self, explanation: TemplateExplanation):
        """Display explanation using Rich formatting."""
        
        # Template overview
        overview_content = f"[bold]{explanation.title}[/bold]\n\n"
        overview_content += f"{explanation.description}\n\n"
        overview_content += f"[blue]Purpose:[/blue] {explanation.purpose}\n"
        overview_content += f"[blue]Target Audience:[/blue] {explanation.target_audience}\n"
        
        if explanation.estimated_cost:
            overview_content += f"[blue]Estimated Monthly Cost:[/blue] ${explanation.estimated_cost:.2f}\n"
        
        if explanation.security_score:
            overview_content += f"[blue]Security Score:[/blue] {explanation.security_score:.1f}/100\n"
        
        overview_content += f"[blue]Complexity:[/blue] {explanation.complexity_score}/10"
        
        console.print(Panel(overview_content, title="📄 Template Overview", border_style="blue"))
        
        # Parameters section
        if explanation.parameters:
            await self._display_parameters_section(explanation.parameters)
        
        # Resources section
        if explanation.resources:
            await self._display_resources_section(explanation.resources)
        
        # Architecture section
        if explanation.resource_relationships:
            await self._display_architecture_section(explanation)
        
        # Learning section
        if explanation.learning_objectives:
            await self._display_learning_section(explanation)
    
    async def _display_parameters_section(self, parameters: Dict[str, Dict[str, Any]]):
        """Display parameters section."""
        
        console.print("\n[bold blue]📋 Parameters[/bold blue]")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Name", style="white", no_wrap=True)
        table.add_column("Type", style="green")
        table.add_column("Description", style="white")
        table.add_column("Required", style="yellow")
        
        for param_name, param_info in parameters.items():
            param_type = param_info.get('type', 'unknown')
            description = param_info.get('metadata', {}).get('description', 'No description')
            default_value = param_info.get('defaultValue')
            required = "No" if default_value is not None else "Yes"
            
            table.add_row(param_name, param_type, description, required)
        
        console.print(table)
    
    async def _display_resources_section(self, resources: Dict[str, ResourceExplanation]):
        """Display resources section."""
        
        console.print("\n[bold blue]🏗️  Resources[/bold blue]")
        
        for resource_name, resource_explanation in resources.items():
            # Resource overview
            resource_content = f"[bold cyan]{resource_explanation.display_name}[/bold cyan]\n"
            resource_content += f"[dim]Type: {resource_explanation.resource_type}[/dim]\n\n"
            resource_content += f"{resource_explanation.description}\n\n"
            resource_content += f"[blue]Purpose:[/blue] {resource_explanation.purpose}\n"
            
            if resource_explanation.dependencies:
                deps = ", ".join(resource_explanation.dependencies)
                resource_content += f"[blue]Dependencies:[/blue] {deps}\n"
            
            if resource_explanation.key_properties:
                resource_content += f"\n[blue]Key Configuration:[/blue]\n"
                for prop, value in resource_explanation.key_properties.items():
                    resource_content += f"  • {prop}: {value}\n"
            
            if resource_explanation.security_considerations:
                resource_content += f"\n[yellow]Security Considerations:[/yellow]\n"
                for consideration in resource_explanation.security_considerations:
                    resource_content += f"  ⚠️  {consideration}\n"
            
            if resource_explanation.recommendations:
                resource_content += f"\n[green]Recommendations:[/green]\n"
                for recommendation in resource_explanation.recommendations:
                    resource_content += f"  💡 {recommendation}\n"
            
            console.print(Panel(
                resource_content, 
                title=f"Resource: {resource_name}",
                border_style="cyan",
                expand=False
            ))
    
    async def _display_architecture_section(self, explanation: TemplateExplanation):
        """Display architecture analysis section."""
        
        console.print("\n[bold blue]🏛️  Architecture Overview[/bold blue]")
        
        if explanation.architecture_overview:
            console.print(Panel(explanation.architecture_overview, border_style="blue"))
        
        # Resource dependency tree
        if explanation.resource_relationships:
            console.print("\n[bold]Resource Dependencies:[/bold]")
            tree = self._build_dependency_tree(explanation.resource_relationships)
            console.print(tree)
        
        # Deployment order
        if explanation.deployment_order:
            console.print("\n[bold]Deployment Order:[/bold]")
            for i, resource in enumerate(explanation.deployment_order, 1):
                console.print(f"  {i}. {resource}")
    
    async def _display_learning_section(self, explanation: TemplateExplanation):
        """Display learning and educational section."""
        
        console.print("\n[bold blue]📚 Learning Guide[/bold blue]")
        
        # Learning objectives
        if explanation.learning_objectives:
            console.print("\n[bold]Learning Objectives:[/bold]")
            for objective in explanation.learning_objectives:
                console.print(f"  🎯 {objective}")
        
        # Key concepts
        if explanation.key_concepts:
            console.print("\n[bold]Key Concepts:[/bold]")
            for concept in explanation.key_concepts:
                console.print(f"  📝 {concept}")
        
        # Troubleshooting tips
        if explanation.troubleshooting_tips:
            console.print("\n[bold]Troubleshooting Tips:[/bold]")
            for tip in explanation.troubleshooting_tips:
                console.print(f"  🔧 {tip}")
    
    def _build_dependency_tree(self, relationships: List[Tuple[str, str, str]]) -> Tree:
        """Build Rich tree from resource relationships."""
        
        # Find root resources (no dependencies)
        all_resources = set()
        dependent_resources = set()
        
        for from_res, to_res, rel_type in relationships:
            all_resources.add(from_res)
            all_resources.add(to_res)
            dependent_resources.add(to_res)
        
        root_resources = all_resources - dependent_resources
        
        if not root_resources:
            # Handle circular dependencies - just pick first resource
            root_resources = {list(all_resources)[0]} if all_resources else set()
        
        tree = Tree("🏗️ Resources")
        
        # Build tree recursively
        added_nodes = {}
        
        for root in root_resources:
            root_node = tree.add(f"[bold cyan]{root}[/bold cyan]")
            added_nodes[root] = root_node
            self._add_dependencies_to_tree(root, root_node, relationships, added_nodes)
        
        return tree
    
    def _add_dependencies_to_tree(
        self, 
        resource: str, 
        node: Any, 
        relationships: List[Tuple[str, str, str]], 
        added_nodes: Dict[str, Any]
    ):
        """Recursively add dependencies to tree."""
        
        # Find resources that depend on this resource
        dependents = [
            (to_res, rel_type) for from_res, to_res, rel_type in relationships 
            if from_res == resource
        ]
        
        for dependent, rel_type in dependents:
            if dependent not in added_nodes:
                dep_node = node.add(f"[cyan]{dependent}[/cyan] [dim]({rel_type})[/dim]")
                added_nodes[dependent] = dep_node
                self._add_dependencies_to_tree(dependent, dep_node, relationships, added_nodes)
    
    def _generate_template_title(self, template_data: Dict[str, Any]) -> str:
        """Generate descriptive title for template."""
        
        metadata = template_data.get('metadata', {})
        if 'description' in metadata:
            return metadata['description']
        
        # Infer from resources
        resources = template_data.get('resources', [])
        if not resources:
            return "Empty Azure Template"
        
        resource_types = set()
        for resource in resources:
            resource_type = resource.get('type', '').split('/')[-1]
            resource_types.add(resource_type)
        
        if len(resource_types) == 1:
            return f"Azure {list(resource_types)[0]} Deployment"
        elif len(resource_types) <= 3:
            return f"Azure {', '.join(sorted(resource_types))} Deployment"
        else:
            return f"Multi-Service Azure Deployment ({len(resource_types)} services)"
    
    def _extract_template_description(self, template_data: Dict[str, Any]) -> str:
        """Extract or generate template description."""
        
        metadata = template_data.get('metadata', {})
        
        # Check for existing description
        if 'description' in metadata:
            return metadata['description']
        
        # Generate description based on resources
        resources = template_data.get('resources', [])
        
        if not resources:
            return "This template does not deploy any Azure resources."
        
        resource_counts = {}
        for resource in resources:
            resource_type = resource.get('type', 'Unknown')
            resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1
        
        description_parts = []
        for resource_type, count in resource_counts.items():
            service_name = resource_type.split('/')[-1] if '/' in resource_type else resource_type
            if count == 1:
                description_parts.append(f"1 {service_name}")
            else:
                description_parts.append(f"{count} {service_name} instances")
        
        if len(description_parts) == 1:
            return f"This template deploys {description_parts[0]} to Azure."
        else:
            return f"This template deploys {', '.join(description_parts[:-1])} and {description_parts[-1]} to Azure."
    
    def _infer_template_purpose(self, template_data: Dict[str, Any]) -> str:
        """Infer the business purpose of the template."""
        
        resources = template_data.get('resources', [])
        resource_types = [resource.get('type', '') for resource in resources]
        
        # Common patterns
        if any('Microsoft.Web/sites' in rt for rt in resource_types):
            if any('Microsoft.Sql' in rt for rt in resource_types):
                return "Web application with database backend"
            else:
                return "Web application hosting"
        
        elif any('Microsoft.Storage' in rt for rt in resource_types):
            if any('Microsoft.Web' in rt for rt in resource_types):
                return "Web application with storage"
            else:
                return "Data storage solution"
        
        elif any('Microsoft.Compute/virtualMachines' in rt for rt in resource_types):
            return "Virtual machine infrastructure"
        
        elif any('Microsoft.KeyVault' in rt for rt in resource_types):
            return "Secure secrets and key management"
        
        else:
            return "Azure infrastructure deployment"
    
    def _determine_target_audience(self, level: ExplanationLevel) -> str:
        """Determine target audience based on explanation level."""
        
        audiences = {
            ExplanationLevel.BEGINNER: "Azure beginners and students learning cloud concepts",
            ExplanationLevel.INTERMEDIATE: "Developers and IT professionals with basic Azure knowledge",
            ExplanationLevel.ADVANCED: "Cloud architects and experienced Azure practitioners",
            ExplanationLevel.EXPERT: "Azure specialists and infrastructure experts"
        }
        
        return audiences.get(level, audiences[ExplanationLevel.INTERMEDIATE])
    
    async def _analyze_parameters(self, template_data: Dict[str, Any], explanation: TemplateExplanation):
        """Analyze template parameters."""
        
        parameters = template_data.get('parameters', {})
        explanation.parameters = parameters
    
    async def _analyze_variables(self, template_data: Dict[str, Any], explanation: TemplateExplanation):
        """Analyze template variables."""
        
        variables = template_data.get('variables', {})
        explanation.variables = variables
    
    async def _analyze_resources(self, template_data: Dict[str, Any], explanation: TemplateExplanation):
        """Analyze template resources."""
        
        resources = template_data.get('resources', [])
        
        for resource in resources:
            resource_name = resource.get('name', 'unnamed')
            resource_type = resource.get('type', 'unknown')
            
            # Get resource explanation
            resource_explanation = await self._explain_resource(resource)
            explanation.resources[resource_name] = resource_explanation
    
    async def _explain_resource(self, resource: Dict[str, Any]) -> ResourceExplanation:
        """Generate explanation for a single resource."""
        
        resource_name = resource.get('name', 'unnamed')
        resource_type = resource.get('type', 'unknown')
        properties = resource.get('properties', {})
        
        # Get knowledge base info
        knowledge = self.resource_knowledge.get(resource_type, {})
        
        explanation = ResourceExplanation(
            resource_name=resource_name,
            resource_type=resource_type,
            display_name=knowledge.get('display_name', resource_type.split('/')[-1]),
            description=knowledge.get('description', f"Azure {resource_type} resource"),
            purpose=knowledge.get('purpose', 'Provides cloud functionality'),
            api_version=resource.get('apiVersion', 'unknown'),
            location=resource.get('location', 'dynamic'),
            security_considerations=knowledge.get('security_considerations', []),
            cost_factors=knowledge.get('cost_factors', []),
            recommendations=knowledge.get('recommendations', []),
            common_issues=knowledge.get('common_issues', []),
            documentation_urls=knowledge.get('documentation_urls', [])
        )
        
        # Analyze key properties
        explanation.key_properties = self._extract_key_properties(resource_type, properties)
        
        return explanation
    
    def _extract_key_properties(self, resource_type: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key properties for explanation."""
        
        # Define important properties for each resource type
        key_property_map = {
            'Microsoft.Web/sites': ['httpsOnly', 'siteConfig.alwaysOn', 'siteConfig.minTlsVersion'],
            'Microsoft.Storage/storageAccounts': ['supportsHttpsTrafficOnly', 'allowBlobPublicAccess', 'kind'],
            'Microsoft.KeyVault/vaults': ['enabledForDeployment', 'enableSoftDelete', 'publicNetworkAccess'],
            'Microsoft.Sql/servers': ['administrators', 'publicNetworkAccess', 'minimalTlsVersion'],
            'Microsoft.Compute/virtualMachines': ['hardwareProfile.vmSize', 'storageProfile.osDisk.createOption']
        }
        
        key_props = {}
        relevant_properties = key_property_map.get(resource_type, [])
        
        for prop_path in relevant_properties:
            value = self._get_nested_property(properties, prop_path)
            if value is not None:
                key_props[prop_path] = value
        
        return key_props
    
    def _get_nested_property(self, properties: Dict[str, Any], prop_path: str) -> Any:
        """Get nested property value using dot notation."""
        
        keys = prop_path.split('.')
        current = properties
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    async def _analyze_architecture(self, template_data: Dict[str, Any], explanation: TemplateExplanation):
        """Analyze template architecture and relationships."""
        
        resources = template_data.get('resources', [])
        
        # Analyze resource relationships
        relationships = []
        
        for resource in resources:
            resource_name = resource.get('name', 'unnamed')
            depends_on = resource.get('dependsOn', [])
            
            for dependency in depends_on:
                relationships.append((resource_name, dependency, 'depends_on'))
        
        explanation.resource_relationships = relationships
        
        # Determine deployment order (topological sort)
        explanation.deployment_order = self._calculate_deployment_order(resources)
        
        # Generate architecture overview
        explanation.architecture_overview = self._generate_architecture_overview(resources, relationships)
    
    def _calculate_deployment_order(self, resources: List[Dict[str, Any]]) -> List[str]:
        """Calculate optimal deployment order based on dependencies."""
        
        # Simple topological sort
        resource_deps = {}
        all_resources = set()
        
        for resource in resources:
            name = resource.get('name', 'unnamed')
            all_resources.add(name)
            resource_deps[name] = resource.get('dependsOn', [])
        
        ordered = []
        remaining = all_resources.copy()
        
        while remaining:
            # Find resources with no remaining dependencies
            ready = []
            for resource in remaining:
                deps = resource_deps.get(resource, [])
                if not any(dep in remaining for dep in deps):
                    ready.append(resource)
            
            if not ready:
                # Circular dependency or other issue - just add remaining
                ready = list(remaining)
            
            # Add ready resources in alphabetical order
            ready.sort()
            ordered.extend(ready)
            
            for resource in ready:
                remaining.remove(resource)
        
        return ordered
    
    def _generate_architecture_overview(
        self, 
        resources: List[Dict[str, Any]], 
        relationships: List[Tuple[str, str, str]]
    ) -> str:
        """Generate architecture overview text."""
        
        if not resources:
            return "This template does not define any resources."
        
        resource_types = {}
        for resource in resources:
            rtype = resource.get('type', 'unknown')
            service_name = rtype.split('/')[-1] if '/' in rtype else rtype
            resource_types[service_name] = resource_types.get(service_name, 0) + 1
        
        overview = f"This template creates an Azure architecture with {len(resources)} resources "
        overview += f"across {len(resource_types)} different services.\n\n"
        
        if relationships:
            overview += f"The deployment includes {len(relationships)} resource dependencies "
            overview += "that ensure proper sequencing during deployment.\n\n"
        
        overview += "Key services deployed:\n"
        for service, count in sorted(resource_types.items()):
            overview += f"• {count} {service} instance{'s' if count > 1 else ''}\n"
        
        return overview
    
    async def _add_cost_analysis(self, template_data: Dict[str, Any], explanation: TemplateExplanation):
        """Add cost analysis to explanation."""
        
        try:
            resources = template_data.get('resources', [])
            cost_estimate = await self.cost_estimator.estimate_deployment_cost(resources)
            explanation.estimated_cost = cost_estimate.total_monthly_cost
        except Exception as e:
            logger.warning(f"Failed to add cost analysis: {e}")
    
    async def _add_security_analysis(self, template_data: Dict[str, Any], explanation: TemplateExplanation):
        """Add security analysis to explanation."""
        
        try:
            resources = template_data.get('resources', [])
            security_assessment = await self.security_analyzer.analyze_deployment_security(resources)
            explanation.security_score = 100 - security_assessment.overall_risk_score
        except Exception as e:
            logger.warning(f"Failed to add security analysis: {e}")
    
    async def _generate_educational_content(self, explanation: TemplateExplanation, level: ExplanationLevel):
        """Generate educational content based on explanation level."""
        
        # Learning objectives
        if level == ExplanationLevel.BEGINNER:
            explanation.learning_objectives = [
                "Understand Azure resource deployment concepts",
                "Learn about infrastructure as code with ARM templates",
                "Recognize common Azure services and their purposes"
            ]
        elif level == ExplanationLevel.INTERMEDIATE:
            explanation.learning_objectives = [
                "Master Azure resource configuration and dependencies",
                "Implement best practices for cloud architecture",
                "Optimize deployments for cost and performance"
            ]
        elif level in [ExplanationLevel.ADVANCED, ExplanationLevel.EXPERT]:
            explanation.learning_objectives = [
                "Design enterprise-grade cloud architectures",
                "Implement advanced security and compliance patterns",
                "Optimize for scalability and operational excellence"
            ]
        
        # Key concepts based on resources
        explanation.key_concepts = self._generate_key_concepts(explanation.resources, level)
        
        # Troubleshooting tips
        explanation.troubleshooting_tips = [
            "Check Azure subscription limits and quotas before deployment",
            "Verify resource naming conventions and uniqueness requirements",
            "Ensure proper permissions are assigned for deployment",
            "Monitor deployment logs for detailed error information"
        ]
    
    def _generate_key_concepts(
        self, 
        resources: Dict[str, ResourceExplanation], 
        level: ExplanationLevel
    ) -> List[str]:
        """Generate key concepts based on template resources."""
        
        concepts = []
        resource_types = [res.resource_type for res in resources.values()]
        
        # Add concepts based on resource types present
        if any('Microsoft.Web' in rt for rt in resource_types):
            concepts.append("App Service plans provide compute resources for web applications")
            if level in [ExplanationLevel.ADVANCED, ExplanationLevel.EXPERT]:
                concepts.append("Web apps can be scaled horizontally and vertically based on demand")
        
        if any('Microsoft.Storage' in rt for rt in resource_types):
            concepts.append("Storage accounts provide various data storage options (blobs, files, tables, queues)")
            if level != ExplanationLevel.BEGINNER:
                concepts.append("Storage replication options affect both availability and cost")
        
        if any('Microsoft.KeyVault' in rt for rt in resource_types):
            concepts.append("Key Vault securely stores secrets, keys, and certificates")
            concepts.append("Applications should use managed identities to access Key Vault")
        
        if any('Microsoft.Sql' in rt for rt in resource_types):
            concepts.append("Azure SQL provides managed relational database services")
            if level in [ExplanationLevel.ADVANCED, ExplanationLevel.EXPERT]:
                concepts.append("SQL Database offers multiple service tiers with different performance characteristics")
        
        return concepts
    
    async def _generate_markdown_explanation(self, explanation: TemplateExplanation) -> str:
        """Generate markdown documentation."""
        
        md = f"# {explanation.title}\n\n"
        md += f"{explanation.description}\n\n"
        md += f"**Purpose:** {explanation.purpose}\n\n"
        md += f"**Target Audience:** {explanation.target_audience}\n\n"
        
        if explanation.estimated_cost:
            md += f"**Estimated Monthly Cost:** ${explanation.estimated_cost:.2f}\n\n"
        
        # Parameters
        if explanation.parameters:
            md += "## Parameters\n\n"
            md += "| Name | Type | Description | Required |\n"
            md += "|------|------|-------------|----------|\n"
            
            for param_name, param_info in explanation.parameters.items():
                param_type = param_info.get('type', 'unknown')
                description = param_info.get('metadata', {}).get('description', 'No description')
                default_value = param_info.get('defaultValue')
                required = "No" if default_value is not None else "Yes"
                md += f"| {param_name} | {param_type} | {description} | {required} |\n"
            
            md += "\n"
        
        # Resources
        if explanation.resources:
            md += "## Resources\n\n"
            
            for resource_name, resource_explanation in explanation.resources.items():
                md += f"### {resource_explanation.display_name}\n\n"
                md += f"**Type:** `{resource_explanation.resource_type}`\n\n"
                md += f"{resource_explanation.description}\n\n"
                md += f"**Purpose:** {resource_explanation.purpose}\n\n"
                
                if resource_explanation.key_properties:
                    md += "**Key Configuration:**\n\n"
                    for prop, value in resource_explanation.key_properties.items():
                        md += f"- `{prop}`: {value}\n"
                    md += "\n"
                
                if resource_explanation.security_considerations:
                    md += "**Security Considerations:**\n\n"
                    for consideration in resource_explanation.security_considerations:
                        md += f"- ⚠️  {consideration}\n"
                    md += "\n"
        
        # Learning objectives
        if explanation.learning_objectives:
            md += "## Learning Objectives\n\n"
            for objective in explanation.learning_objectives:
                md += f"- 🎯 {objective}\n"
            md += "\n"
        
        return md
    
    def _initialize_resource_knowledge(self) -> Dict[str, Dict[str, Any]]:
        """Initialize resource knowledge base."""
        
        return {
            'Microsoft.Web/sites': {
                'display_name': 'Web App',
                'description': 'Azure App Service web application for hosting web apps, REST APIs, and mobile backends',
                'purpose': 'Host web applications with built-in scaling, security, and deployment features',
                'security_considerations': [
                    'Enable HTTPS Only to encrypt traffic in transit',
                    'Configure minimum TLS version 1.2 or higher',
                    'Use managed identity for accessing other Azure services',
                    'Implement proper authentication and authorization'
                ],
                'cost_factors': [
                    'App Service plan tier and size',
                    'Number of instances (scale out)',
                    'Storage usage',
                    'Outbound data transfer'
                ],
                'recommendations': [
                    'Use deployment slots for staging deployments',
                    'Enable Application Insights for monitoring',
                    'Configure auto-scaling based on metrics',
                    'Implement health check endpoints'
                ],
                'documentation_urls': [
                    'https://docs.microsoft.com/en-us/azure/app-service/'
                ]
            },
            'Microsoft.Storage/storageAccounts': {
                'display_name': 'Storage Account',
                'description': 'Scalable cloud storage for data objects, file shares, NoSQL data, and message queues',
                'purpose': 'Provide highly available and secure storage for various data types',
                'security_considerations': [
                    'Enable secure transfer (HTTPS) for all requests',
                    'Disable public blob access unless specifically needed',
                    'Use private endpoints for VNet connectivity',
                    'Enable encryption for data at rest'
                ],
                'cost_factors': [
                    'Storage type (Standard vs Premium)',
                    'Replication level (LRS, ZRS, GRS, RA-GRS)',
                    'Data access patterns (Hot, Cool, Archive)',
                    'Transaction volume'
                ]
            },
            'Microsoft.KeyVault/vaults': {
                'display_name': 'Key Vault',
                'description': 'Secure storage and management of secrets, keys, and certificates',
                'purpose': 'Centrally manage cryptographic keys and secrets with hardware security',
                'security_considerations': [
                    'Use access policies or RBAC for granular permissions',
                    'Enable soft delete and purge protection',
                    'Restrict network access using firewalls or private endpoints',
                    'Monitor access with diagnostic logging'
                ],
                'cost_factors': [
                    'Number of operations (gets, sets, deletes)',
                    'Premium tier for HSM-backed keys',
                    'Certificate operations'
                ]
            }
        }
    
    def _initialize_concept_definitions(self) -> Dict[str, str]:
        """Initialize concept definitions."""
        
        return {
            'Resource Group': 'A logical container that holds related Azure resources for an application',
            'ARM Template': 'JSON-based Infrastructure as Code template for deploying Azure resources',
            'Managed Identity': 'Azure-managed identity that eliminates the need to store credentials in code',
            'Virtual Network': 'Isolated network environment for Azure resources with customizable IP addressing',
            'Resource Dependencies': 'Relationships between resources that define deployment order'
        }
    
    def _initialize_best_practices(self) -> Dict[str, List[str]]:
        """Initialize best practices by category."""
        
        return {
            'Security': [
                'Use managed identities instead of service principals where possible',
                'Enable diagnostic logging for security monitoring',
                'Implement least privilege access principles',
                'Use Key Vault for secrets management'
            ],
            'Cost Optimization': [
                'Right-size resources based on actual usage',
                'Use reserved instances for predictable workloads',
                'Implement auto-scaling to optimize costs',
                'Choose appropriate storage tiers'
            ],
            'Reliability': [
                'Deploy across multiple availability zones',
                'Implement health checks and monitoring',
                'Use managed services to reduce operational overhead',
                'Plan for disaster recovery'
            ]
        }