"""
Dependency resolution system for Bicep templates and Azure resources.

This module provides intelligent dependency analysis, conflict resolution,
and deployment ordering for complex Azure resource templates.
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import json
import re

from .models.template_update import DependencyInfo, TemplateUpdateManifest
from .models.resource_requirement import ResourceRequirement, ResourceType

logger = logging.getLogger(__name__)


@dataclass
class ResourceDependency:
    """Represents a dependency between Azure resources."""
    
    source_resource: str
    target_resource: str
    dependency_type: str  # 'hard', 'soft', 'conditional'
    reason: str
    is_cross_template: bool = False
    template_name: Optional[str] = None
    
    def __hash__(self):
        return hash((self.source_resource, self.target_resource, self.dependency_type))


@dataclass 
class DependencyGraph:
    """Graph representation of resource dependencies."""
    
    nodes: Set[str] = field(default_factory=set)
    edges: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    reverse_edges: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    metadata: Dict[str, ResourceDependency] = field(default_factory=dict)
    
    def add_dependency(self, dependency: ResourceDependency):
        """Add a dependency to the graph."""
        source = dependency.source_resource
        target = dependency.target_resource
        
        self.nodes.add(source)
        self.nodes.add(target)
        self.edges[source].add(target)
        self.reverse_edges[target].add(source)
        
        # Store metadata
        key = f"{source}->{target}"
        self.metadata[key] = dependency
    
    def remove_dependency(self, source: str, target: str):
        """Remove a dependency from the graph."""
        if target in self.edges.get(source, set()):
            self.edges[source].remove(target)
            self.reverse_edges[target].remove(source)
            
            key = f"{source}->{target}"
            self.metadata.pop(key, None)
    
    def get_dependencies(self, resource: str) -> Set[str]:
        """Get direct dependencies of a resource."""
        return self.edges.get(resource, set())
    
    def get_dependents(self, resource: str) -> Set[str]:
        """Get resources that depend on this resource."""
        return self.reverse_edges.get(resource, set())


class DependencyResolver:
    """
    Analyzes and resolves dependencies between Azure resources and templates.
    
    This resolver provides intelligent dependency analysis, cycle detection,
    and optimal deployment ordering for complex Azure infrastructures.
    """
    
    def __init__(self):
        # Azure resource dependency rules
        self.resource_rules = self._initialize_resource_rules()
        
        # Template dependency patterns
        self.template_patterns = self._initialize_template_patterns()
        
        # Performance optimization
        self.cache_enabled = True
        self._dependency_cache = {}
    
    def analyze_dependencies(
        self, 
        resources: List[ResourceRequirement],
        templates: Optional[Dict[str, Any]] = None
    ) -> DependencyGraph:
        """
        Analyze dependencies between resources and build dependency graph.
        
        Args:
            resources: List of resource requirements
            templates: Optional template definitions
            
        Returns:
            Complete dependency graph
        """
        logger.info(f"Analyzing dependencies for {len(resources)} resources")
        
        graph = DependencyGraph()
        
        # Add all resources as nodes
        for resource in resources:
            graph.nodes.add(resource.name)
        
        # Analyze resource-to-resource dependencies
        self._analyze_resource_dependencies(resources, graph)
        
        # Analyze template dependencies if provided
        if templates:
            self._analyze_template_dependencies(templates, graph)
        
        # Detect implicit dependencies
        self._detect_implicit_dependencies(resources, graph)
        
        logger.info(f"Built dependency graph with {len(graph.nodes)} nodes and {sum(len(deps) for deps in graph.edges.values())} edges")
        
        return graph
    
    def detect_cycles(self, graph: DependencyGraph) -> List[List[str]]:
        """
        Detect circular dependencies in the graph.
        
        Args:
            graph: Dependency graph to analyze
            
        Returns:
            List of cycles (each cycle is a list of resource names)
        """
        cycles = []
        visited = set()
        rec_stack = set()
        
        def _dfs_cycle_detection(node: str, path: List[str]) -> Optional[List[str]]:
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]
            
            if node in visited:
                return None
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get_dependencies(node):
                cycle = _dfs_cycle_detection(neighbor, path.copy())
                if cycle:
                    cycles.append(cycle)
            
            rec_stack.remove(node)
            return None
        
        for node in graph.nodes:
            if node not in visited:
                _dfs_cycle_detection(node, [])
        
        return cycles
    
    def resolve_cycles(
        self, 
        graph: DependencyGraph, 
        cycles: List[List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Provide resolution strategies for circular dependencies.
        
        Args:
            graph: Dependency graph
            cycles: List of detected cycles
            
        Returns:
            List of resolution strategies
        """
        resolutions = []
        
        for cycle in cycles:
            resolution = {
                'cycle': cycle,
                'strategies': [],
                'recommended_action': None
            }
            
            # Analyze cycle to determine best resolution
            cycle_analysis = self._analyze_cycle(graph, cycle)
            
            # Strategy 1: Remove soft dependencies
            soft_deps = [dep for dep in cycle_analysis['dependencies'] 
                        if dep.dependency_type == 'soft']
            if soft_deps:
                resolution['strategies'].append({
                    'type': 'remove_soft_dependencies',
                    'description': 'Remove optional dependencies to break cycle',
                    'dependencies_to_remove': [(d.source_resource, d.target_resource) for d in soft_deps],
                    'risk': 'low'
                })
            
            # Strategy 2: Conditional dependencies
            conditional_deps = [dep for dep in cycle_analysis['dependencies'] 
                              if dep.dependency_type == 'conditional']
            if conditional_deps:
                resolution['strategies'].append({
                    'type': 'make_conditional',
                    'description': 'Convert dependencies to conditional deployment',
                    'dependencies': [(d.source_resource, d.target_resource) for d in conditional_deps],
                    'risk': 'medium'
                })
            
            # Strategy 3: Template separation
            cross_template_deps = [dep for dep in cycle_analysis['dependencies'] 
                                 if dep.is_cross_template]
            if cross_template_deps:
                resolution['strategies'].append({
                    'type': 'separate_templates',
                    'description': 'Move resources to separate templates with parameter passing',
                    'templates_to_separate': list(set(d.template_name for d in cross_template_deps if d.template_name)),
                    'risk': 'medium'
                })
            
            # Strategy 4: Resource extraction
            if len(cycle) > 2:
                resolution['strategies'].append({
                    'type': 'extract_shared_resource',
                    'description': 'Extract shared functionality to separate module',
                    'shared_resources': self._identify_shared_resources(cycle),
                    'risk': 'high'
                })
            
            # Select recommended action
            if resolution['strategies']:
                # Prefer low-risk solutions
                low_risk_strategies = [s for s in resolution['strategies'] if s.get('risk') == 'low']
                if low_risk_strategies:
                    resolution['recommended_action'] = low_risk_strategies[0]
                else:
                    resolution['recommended_action'] = resolution['strategies'][0]
            
            resolutions.append(resolution)
        
        return resolutions
    
    def calculate_deployment_order(
        self, 
        graph: DependencyGraph,
        parallel_groups: bool = True
    ) -> List[List[str]]:
        """
        Calculate optimal deployment order using topological sorting.
        
        Args:
            graph: Dependency graph
            parallel_groups: Whether to group resources that can be deployed in parallel
            
        Returns:
            Ordered list of deployment groups (resources in same group can be deployed in parallel)
        """
        # Check for cycles first
        cycles = self.detect_cycles(graph)
        if cycles:
            logger.warning(f"Found {len(cycles)} cycles in dependency graph. Deployment order may be suboptimal.")
        
        # Kahn's algorithm for topological sorting
        in_degree = {node: 0 for node in graph.nodes}
        for node in graph.nodes:
            for dependency in graph.get_dependencies(node):
                in_degree[dependency] += 1
        
        # Initialize queue with nodes having no dependencies
        queue = deque([node for node in graph.nodes if in_degree[node] == 0])
        deployment_order = []
        
        while queue:
            if parallel_groups:
                # Process all nodes with no remaining dependencies in parallel
                current_group = []
                next_queue = deque()
                
                while queue:
                    node = queue.popleft()
                    current_group.append(node)
                    
                    # Reduce in-degree for dependent nodes
                    for dependent in graph.get_dependencies(node):
                        in_degree[dependent] -= 1
                        if in_degree[dependent] == 0:
                            next_queue.append(dependent)
                
                if current_group:
                    deployment_order.append(current_group)
                
                queue = next_queue
            else:
                # Process one node at a time
                node = queue.popleft()
                deployment_order.append([node])
                
                for dependent in graph.get_dependencies(node):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        # Check if all nodes were processed (cycle detection)
        processed_nodes = set()
        for group in deployment_order:
            processed_nodes.update(group)
        
        if processed_nodes != graph.nodes:
            unprocessed = graph.nodes - processed_nodes
            logger.error(f"Could not determine deployment order for nodes: {unprocessed}")
            # Add unprocessed nodes to final group as fallback
            if unprocessed:
                deployment_order.append(list(unprocessed))
        
        return deployment_order
    
    def validate_dependencies(
        self, 
        graph: DependencyGraph,
        resource_definitions: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Validate that all dependencies are satisfied and consistent.
        
        Args:
            graph: Dependency graph
            resource_definitions: Resource definitions with properties
            
        Returns:
            Dictionary of validation issues by resource name
        """
        issues = defaultdict(list)
        
        for resource_name in graph.nodes:
            resource_def = resource_definitions.get(resource_name, {})
            dependencies = graph.get_dependencies(resource_name)
            
            # Check missing dependencies
            for dep_name in dependencies:
                if dep_name not in resource_definitions:
                    issues[resource_name].append(f"Missing dependency: {dep_name}")
            
            # Check resource-specific validation rules
            resource_type = resource_def.get('type', 'unknown')
            validation_rules = self.resource_rules.get(resource_type, {}).get('validation', [])
            
            for rule in validation_rules:
                if not self._validate_rule(resource_def, dependencies, resource_definitions, rule):
                    issues[resource_name].append(f"Validation failed: {rule['description']}")
        
        return dict(issues)
    
    def optimize_dependencies(
        self, 
        graph: DependencyGraph
    ) -> Tuple[DependencyGraph, List[str]]:
        """
        Optimize dependency graph by removing redundant dependencies.
        
        Args:
            graph: Original dependency graph
            
        Returns:
            Tuple of (optimized_graph, optimization_actions)
        """
        optimized_graph = DependencyGraph()
        optimized_graph.nodes = graph.nodes.copy()
        optimizations = []
        
        # Copy all dependencies initially
        for source in graph.edges:
            for target in graph.edges[source]:
                key = f"{source}->{target}"
                if key in graph.metadata:
                    optimized_graph.add_dependency(graph.metadata[key])
        
        # Remove transitive dependencies
        transitive_removed = self._remove_transitive_dependencies(optimized_graph)
        if transitive_removed:
            optimizations.append(f"Removed {transitive_removed} transitive dependencies")
        
        # Remove redundant soft dependencies
        soft_removed = self._remove_redundant_soft_dependencies(optimized_graph)
        if soft_removed:
            optimizations.append(f"Removed {soft_removed} redundant soft dependencies")
        
        # Consolidate parallel dependencies
        consolidated = self._consolidate_parallel_dependencies(optimized_graph)
        if consolidated:
            optimizations.append(f"Consolidated {consolidated} parallel dependency groups")
        
        return optimized_graph, optimizations
    
    def _initialize_resource_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize Azure resource dependency rules."""
        return {
            'Microsoft.Web/sites': {
                'hard_dependencies': ['Microsoft.Web/serverfarms'],
                'soft_dependencies': ['Microsoft.Storage/storageAccounts', 'Microsoft.KeyVault/vaults'],
                'validation': [
                    {
                        'type': 'requires_app_service_plan',
                        'description': 'Web app must reference an App Service Plan'
                    }
                ]
            },
            'Microsoft.Web/serverfarms': {
                'hard_dependencies': [],
                'soft_dependencies': ['Microsoft.Network/virtualNetworks'],
                'validation': []
            },
            'Microsoft.Storage/storageAccounts': {
                'hard_dependencies': [],
                'soft_dependencies': ['Microsoft.Network/virtualNetworks', 'Microsoft.KeyVault/vaults'],
                'validation': [
                    {
                        'type': 'unique_name',
                        'description': 'Storage account name must be globally unique'
                    }
                ]
            },
            'Microsoft.KeyVault/vaults': {
                'hard_dependencies': [],
                'soft_dependencies': ['Microsoft.Network/virtualNetworks'],
                'validation': [
                    {
                        'type': 'access_policies',
                        'description': 'Key Vault should have access policies configured'
                    }
                ]
            },
            'Microsoft.Sql/servers': {
                'hard_dependencies': [],
                'soft_dependencies': ['Microsoft.Network/virtualNetworks', 'Microsoft.KeyVault/vaults'],
                'validation': [
                    {
                        'type': 'firewall_rules',
                        'description': 'SQL Server should have firewall rules configured'
                    }
                ]
            },
            'Microsoft.Sql/servers/databases': {
                'hard_dependencies': ['Microsoft.Sql/servers'],
                'soft_dependencies': [],
                'validation': []
            },
            'Microsoft.Network/virtualNetworks': {
                'hard_dependencies': [],
                'soft_dependencies': [],
                'validation': [
                    {
                        'type': 'address_space',
                        'description': 'Virtual network must have valid address space'
                    }
                ]
            },
            'Microsoft.Network/networkSecurityGroups': {
                'hard_dependencies': [],
                'soft_dependencies': [],
                'validation': [
                    {
                        'type': 'security_rules',
                        'description': 'NSG should have appropriate security rules'
                    }
                ]
            },
            'Microsoft.Insights/components': {
                'hard_dependencies': [],
                'soft_dependencies': ['Microsoft.Web/sites'],
                'validation': []
            }
        }
    
    def _initialize_template_patterns(self) -> Dict[str, List[str]]:
        """Initialize template dependency patterns."""
        return {
            'parameter_reference': [
                r'parameters\([\'"]([^\'"]+)[\'"]\)',
                r'\$\{([^}]+)\}'
            ],
            'variable_reference': [
                r'variables\([\'"]([^\'"]+)[\'"]\)'
            ],
            'resource_reference': [
                r'resourceId\([^)]+[\'"]([^/\'\"]+/[^\'\"]+)[\'"][^)]*\)',
                r'reference\([\'"]([^\'"]+)[\'"]\)'
            ]
        }
    
    def _analyze_resource_dependencies(
        self, 
        resources: List[ResourceRequirement], 
        graph: DependencyGraph
    ):
        """Analyze dependencies between individual resources."""
        resource_by_name = {r.name: r for r in resources}
        
        for resource in resources:
            resource_type = resource.resource_type.value
            rules = self.resource_rules.get(resource_type, {})
            
            # Add hard dependencies
            for dep_type in rules.get('hard_dependencies', []):
                dependent_resources = [r for r in resources if r.resource_type.value == dep_type]
                for dep_resource in dependent_resources:
                    dependency = ResourceDependency(
                        source_resource=resource.name,
                        target_resource=dep_resource.name,
                        dependency_type='hard',
                        reason=f"Required dependency: {resource_type} -> {dep_type}"
                    )
                    graph.add_dependency(dependency)
            
            # Add soft dependencies
            for dep_type in rules.get('soft_dependencies', []):
                dependent_resources = [r for r in resources if r.resource_type.value == dep_type]
                for dep_resource in dependent_resources:
                    dependency = ResourceDependency(
                        source_resource=resource.name,
                        target_resource=dep_resource.name,
                        dependency_type='soft',
                        reason=f"Optional dependency: {resource_type} -> {dep_type}"
                    )
                    graph.add_dependency(dependency)
    
    def _analyze_template_dependencies(
        self, 
        templates: Dict[str, Any], 
        graph: DependencyGraph
    ):
        """Analyze dependencies between templates."""
        for template_name, template_content in templates.items():
            if isinstance(template_content, str):
                # Parse template content for references
                self._parse_template_references(template_name, template_content, graph)
    
    def _parse_template_references(
        self, 
        template_name: str, 
        content: str, 
        graph: DependencyGraph
    ):
        """Parse template content for dependency references."""
        # Look for parameter references
        for pattern in self.template_patterns['parameter_reference']:
            matches = re.findall(pattern, content)
            for match in matches:
                # Parameter dependencies are usually external
                dependency = ResourceDependency(
                    source_resource=template_name,
                    target_resource=f"parameter:{match}",
                    dependency_type='conditional',
                    reason=f"Parameter reference: {match}",
                    is_cross_template=True,
                    template_name=template_name
                )
                graph.add_dependency(dependency)
        
        # Look for resource references
        for pattern in self.template_patterns['resource_reference']:
            matches = re.findall(pattern, content)
            for match in matches:
                dependency = ResourceDependency(
                    source_resource=template_name,
                    target_resource=match,
                    dependency_type='hard',
                    reason=f"Resource reference: {match}",
                    is_cross_template=True,
                    template_name=template_name
                )
                graph.add_dependency(dependency)
    
    def _detect_implicit_dependencies(
        self, 
        resources: List[ResourceRequirement], 
        graph: DependencyGraph
    ):
        """Detect implicit dependencies based on resource configurations."""
        # Naming-based dependencies
        for resource in resources:
            for other_resource in resources:
                if resource.name != other_resource.name:
                    # Check if resource name suggests dependency
                    if (other_resource.name.lower() in resource.name.lower() or
                        resource.name.lower() in other_resource.name.lower()):
                        
                        dependency = ResourceDependency(
                            source_resource=resource.name,
                            target_resource=other_resource.name,
                            dependency_type='soft',
                            reason="Implicit naming-based dependency"
                        )
                        graph.add_dependency(dependency)
    
    def _analyze_cycle(
        self, 
        graph: DependencyGraph, 
        cycle: List[str]
    ) -> Dict[str, Any]:
        """Analyze a cycle to determine resolution strategies."""
        cycle_dependencies = []
        
        for i in range(len(cycle) - 1):
            source = cycle[i]
            target = cycle[i + 1]
            key = f"{source}->{target}"
            
            if key in graph.metadata:
                cycle_dependencies.append(graph.metadata[key])
        
        return {
            'cycle_length': len(cycle) - 1,
            'dependencies': cycle_dependencies,
            'has_soft_dependencies': any(d.dependency_type == 'soft' for d in cycle_dependencies),
            'has_cross_template': any(d.is_cross_template for d in cycle_dependencies)
        }
    
    def _identify_shared_resources(self, cycle: List[str]) -> List[str]:
        """Identify resources that could be extracted to break cycles."""
        # Simple heuristic: resources that appear in multiple dependency chains
        resource_counts = {}
        for resource in cycle:
            resource_counts[resource] = resource_counts.get(resource, 0) + 1
        
        # Return resources that appear most frequently
        max_count = max(resource_counts.values()) if resource_counts else 0
        return [r for r, count in resource_counts.items() if count == max_count]
    
    def _remove_transitive_dependencies(self, graph: DependencyGraph) -> int:
        """Remove transitive dependencies (A -> B -> C, remove A -> C)."""
        removed_count = 0
        
        for node in list(graph.nodes):
            dependencies = list(graph.get_dependencies(node))
            
            for direct_dep in dependencies:
                indirect_deps = graph.get_dependencies(direct_dep)
                
                for indirect_dep in indirect_deps:
                    if indirect_dep in dependencies:
                        # This is a transitive dependency, remove it
                        graph.remove_dependency(node, indirect_dep)
                        removed_count += 1
        
        return removed_count
    
    def _remove_redundant_soft_dependencies(self, graph: DependencyGraph) -> int:
        """Remove soft dependencies that are already covered by hard dependencies."""
        removed_count = 0
        
        for key, dependency in list(graph.metadata.items()):
            if dependency.dependency_type == 'soft':
                source = dependency.source_resource
                target = dependency.target_resource
                
                # Check if there's already a hard dependency path
                if self._has_hard_dependency_path(graph, source, target):
                    graph.remove_dependency(source, target)
                    removed_count += 1
        
        return removed_count
    
    def _consolidate_parallel_dependencies(self, graph: DependencyGraph) -> int:
        """Consolidate multiple parallel dependencies into single relationships."""
        # This is a placeholder for more complex consolidation logic
        return 0
    
    def _has_hard_dependency_path(
        self, 
        graph: DependencyGraph, 
        source: str, 
        target: str, 
        visited: Optional[Set[str]] = None
    ) -> bool:
        """Check if there's a hard dependency path from source to target."""
        if visited is None:
            visited = set()
        
        if source == target:
            return True
        
        if source in visited:
            return False
        
        visited.add(source)
        
        for dep in graph.get_dependencies(source):
            key = f"{source}->{dep}"
            dependency = graph.metadata.get(key)
            
            if dependency and dependency.dependency_type == 'hard':
                if self._has_hard_dependency_path(graph, dep, target, visited.copy()):
                    return True
        
        return False
    
    def _validate_rule(
        self,
        resource_def: Dict[str, Any],
        dependencies: Set[str],
        all_resources: Dict[str, Any],
        rule: Dict[str, str]
    ) -> bool:
        """Validate a specific dependency rule."""
        rule_type = rule.get('type')
        
        if rule_type == 'requires_app_service_plan':
            # Check if web app has app service plan dependency
            return any('serverfarms' in dep for dep in dependencies)
        
        elif rule_type == 'unique_name':
            # This would require global validation, simplified for now
            return True
        
        elif rule_type == 'access_policies':
            # Check if Key Vault has access policies
            return 'accessPolicies' in resource_def.get('properties', {})
        
        elif rule_type == 'firewall_rules':
            # Check if SQL Server has firewall rules
            return 'firewallRules' in resource_def.get('properties', {})
        
        elif rule_type == 'address_space':
            # Check if VNet has address space
            return 'addressSpace' in resource_def.get('properties', {})
        
        elif rule_type == 'security_rules':
            # Check if NSG has security rules
            return 'securityRules' in resource_def.get('properties', {})
        
        # Default to valid if rule type not recognized
        return True