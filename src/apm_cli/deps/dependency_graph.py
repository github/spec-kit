"""Data structures for dependency graph representation and resolution."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from ..models.apm_package import APMPackage, DependencyReference


@dataclass
class DependencyNode:
    """Represents a single dependency node in the dependency graph."""
    package: APMPackage
    dependency_ref: DependencyReference
    depth: int = 0
    children: List['DependencyNode'] = field(default_factory=list)
    parent: Optional['DependencyNode'] = None
    
    def get_id(self) -> str:
        """Get unique identifier for this node."""
        # Include reference to distinguish between different versions/branches of same repo
        if self.dependency_ref.reference:
            return f"{self.dependency_ref.repo_url}#{self.dependency_ref.reference}"
        return self.dependency_ref.repo_url
    
    def get_display_name(self) -> str:
        """Get display name for this dependency."""
        return self.dependency_ref.get_display_name()


@dataclass
class CircularRef:
    """Represents a circular dependency reference."""
    cycle_path: List[str]  # List of repo URLs forming the cycle
    detected_at_depth: int
    
    def _format_complete_cycle(self) -> str:
        """
        Return a string representation of the cycle, ensuring it is visually complete.
        If the cycle path does not end at the starting node, append the start to the end.
        """
        if not self.cycle_path:
            return "(empty path)"
        cycle_display = " -> ".join(self.cycle_path)
        # Ensure the cycle visually returns to the start node
        if len(self.cycle_path) > 1 and self.cycle_path[0] != self.cycle_path[-1]:
            cycle_display += f" -> {self.cycle_path[0]}"
        return cycle_display

    def __str__(self) -> str:
        """String representation of the circular dependency."""
        return f"Circular dependency detected: {self._format_complete_cycle()}"
@dataclass 
class DependencyTree:
    """Hierarchical representation of dependencies before flattening."""
    root_package: APMPackage
    nodes: Dict[str, DependencyNode] = field(default_factory=dict)
    max_depth: int = 0
    
    def add_node(self, node: DependencyNode) -> None:
        """Add a node to the tree."""
        self.nodes[node.get_id()] = node
        self.max_depth = max(self.max_depth, node.depth)
    
    def get_node(self, repo_url: str) -> Optional[DependencyNode]:
        """Get a node by its repository URL."""
        return self.nodes.get(repo_url)
    
    def get_nodes_at_depth(self, depth: int) -> List[DependencyNode]:
        """Get all nodes at a specific depth level."""
        return [node for node in self.nodes.values() if node.depth == depth]
    
    def has_dependency(self, repo_url: str) -> bool:
        """Check if a dependency exists in the tree."""
        # Check by repo URL, not by full node ID (which may include reference)
        return any(node.dependency_ref.repo_url == repo_url for node in self.nodes.values())


@dataclass
class ConflictInfo:
    """Information about a dependency conflict."""
    repo_url: str
    winner: DependencyReference  # The dependency that "wins"
    conflicts: List[DependencyReference]  # All conflicting dependencies
    reason: str  # Explanation of why winner was chosen
    
    def __str__(self) -> str:
        """String representation of the conflict."""
        conflict_refs = [str(ref) for ref in self.conflicts]
        return f"Conflict for {self.repo_url}: {str(self.winner)} wins over {', '.join(conflict_refs)} ({self.reason})"


@dataclass
class FlatDependencyMap:
    """Final flattened dependency mapping ready for installation."""
    dependencies: Dict[str, DependencyReference] = field(default_factory=dict)
    conflicts: List[ConflictInfo] = field(default_factory=list)
    install_order: List[str] = field(default_factory=list)  # Order for installation
    
    def add_dependency(self, dep_ref: DependencyReference, is_conflict: bool = False) -> None:
        """Add a dependency to the flat map."""
        repo_url = dep_ref.repo_url
        
        # If this is the first occurrence, just add it
        if repo_url not in self.dependencies:
            self.dependencies[repo_url] = dep_ref
            self.install_order.append(repo_url)
        elif is_conflict:
            # Record the conflict but keep the first one (first wins strategy)
            existing_ref = self.dependencies[repo_url]
            conflict = ConflictInfo(
                repo_url=repo_url,
                winner=existing_ref,
                conflicts=[dep_ref],
                reason="first declared dependency wins"
            )
            
            # Check if we already have a conflict for this repo
            existing_conflict = next((c for c in self.conflicts if c.repo_url == repo_url), None)
            if existing_conflict:
                existing_conflict.conflicts.append(dep_ref)
            else:
                self.conflicts.append(conflict)
    
    def get_dependency(self, repo_url: str) -> Optional[DependencyReference]:
        """Get a dependency by repository URL."""
        return self.dependencies.get(repo_url)
    
    def has_conflicts(self) -> bool:
        """Check if there are any conflicts in the flattened map."""
        return bool(self.conflicts)
    
    def total_dependencies(self) -> int:
        """Get total number of unique dependencies."""
        return len(self.dependencies)
    
    def get_installation_list(self) -> List[DependencyReference]:
        """Get dependencies in installation order."""
        return [self.dependencies[repo_url] for repo_url in self.install_order if repo_url in self.dependencies]


@dataclass
class DependencyGraph:
    """Complete resolved dependency information."""
    root_package: APMPackage
    dependency_tree: DependencyTree
    flattened_dependencies: FlatDependencyMap
    circular_dependencies: List[CircularRef] = field(default_factory=list)
    resolution_errors: List[str] = field(default_factory=list)
    
    def has_circular_dependencies(self) -> bool:
        """Check if there are any circular dependencies."""
        return bool(self.circular_dependencies)
    
    def has_conflicts(self) -> bool:
        """Check if there are any dependency conflicts."""
        return self.flattened_dependencies.has_conflicts()
    
    def has_errors(self) -> bool:
        """Check if there are any resolution errors."""
        return bool(self.resolution_errors)
    
    def is_valid(self) -> bool:
        """Check if the dependency graph is valid (no circular deps or errors)."""
        return not self.has_circular_dependencies() and not self.has_errors()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the dependency resolution."""
        return {
            "root_package": self.root_package.name,
            "total_dependencies": self.flattened_dependencies.total_dependencies(),
            "max_depth": self.dependency_tree.max_depth,
            "has_circular_dependencies": self.has_circular_dependencies(),
            "circular_count": len(self.circular_dependencies),
            "has_conflicts": self.has_conflicts(),
            "conflict_count": len(self.flattened_dependencies.conflicts),
            "has_errors": self.has_errors(),
            "error_count": len(self.resolution_errors),
            "is_valid": self.is_valid()
        }
    
    def add_error(self, error: str) -> None:
        """Add a resolution error."""
        self.resolution_errors.append(error)
    
    def add_circular_dependency(self, circular_ref: CircularRef) -> None:
        """Add a circular dependency detection."""
        self.circular_dependencies.append(circular_ref)