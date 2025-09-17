"""APM dependency resolution engine with recursive resolution and conflict detection."""

from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import deque

from ..models.apm_package import APMPackage, DependencyReference
from .dependency_graph import (
    DependencyGraph, DependencyTree, DependencyNode, FlatDependencyMap,
    CircularRef, ConflictInfo
)


class APMDependencyResolver:
    """Handles recursive APM dependency resolution similar to NPM."""
    
    def __init__(self, max_depth: int = 50):
        """Initialize the resolver with maximum recursion depth."""
        self.max_depth = max_depth
        self._resolution_path = []  # For test compatibility
    
    def resolve_dependencies(self, project_root: Path) -> DependencyGraph:
        """
        Resolve all APM dependencies recursively.
        
        Args:
            project_root: Path to the project root containing apm.yml
            
        Returns:
            DependencyGraph: Complete resolved dependency graph
        """
        # Load the root package
        apm_yml_path = project_root / "apm.yml"
        if not apm_yml_path.exists():
            # Create empty dependency graph for projects without apm.yml
            empty_package = APMPackage(name="unknown", version="0.0.0", package_path=project_root)
            empty_tree = DependencyTree(root_package=empty_package)
            empty_flat = FlatDependencyMap()
            return DependencyGraph(
                root_package=empty_package,
                dependency_tree=empty_tree,
                flattened_dependencies=empty_flat
            )
        
        try:
            root_package = APMPackage.from_apm_yml(apm_yml_path)
        except (ValueError, FileNotFoundError) as e:
            # Create error graph
            empty_package = APMPackage(name="error", version="0.0.0", package_path=project_root)
            empty_tree = DependencyTree(root_package=empty_package)
            empty_flat = FlatDependencyMap()
            graph = DependencyGraph(
                root_package=empty_package,
                dependency_tree=empty_tree,
                flattened_dependencies=empty_flat
            )
            graph.add_error(f"Failed to load root apm.yml: {e}")
            return graph
        
        # Build the complete dependency tree
        dependency_tree = self.build_dependency_tree(apm_yml_path)
        
        # Detect circular dependencies
        circular_deps = self.detect_circular_dependencies(dependency_tree)
        
        # Flatten dependencies for installation
        flattened_deps = self.flatten_dependencies(dependency_tree)
        
        # Create and return the complete graph
        graph = DependencyGraph(
            root_package=root_package,
            dependency_tree=dependency_tree,
            flattened_dependencies=flattened_deps,
            circular_dependencies=circular_deps
        )
        
        return graph
    
    def build_dependency_tree(self, root_apm_yml: Path) -> DependencyTree:
        """
        Build complete tree of all dependencies and sub-dependencies.
        
        Uses breadth-first traversal to build the dependency tree level by level.
        This allows for early conflict detection and clearer error reporting.
        
        Args:
            root_apm_yml: Path to the root apm.yml file
            
        Returns:
            DependencyTree: Hierarchical dependency tree
        """
        # Load root package
        try:
            root_package = APMPackage.from_apm_yml(root_apm_yml)
        except (ValueError, FileNotFoundError) as e:
            # Return empty tree with error
            empty_package = APMPackage(name="error", version="0.0.0")
            tree = DependencyTree(root_package=empty_package)
            return tree
        
        # Initialize the tree
        tree = DependencyTree(root_package=root_package)
        
        # Queue for breadth-first traversal: (dependency_ref, depth, parent_node)
        processing_queue: deque[Tuple[DependencyReference, int, Optional[DependencyNode]]] = deque()
        
        # Set to track queued repo URLs for O(1) lookup instead of O(n) list comprehension
        queued_repo_urls: Set[str] = set()
        
        # Add root dependencies to queue
        root_deps = root_package.get_apm_dependencies()
        for dep_ref in root_deps:
            processing_queue.append((dep_ref, 1, None))
            queued_repo_urls.add(dep_ref.repo_url)
        
        # Process dependencies breadth-first
        while processing_queue:
            dep_ref, depth, parent_node = processing_queue.popleft()
            
            # Remove from queued set since we're now processing this dependency
            queued_repo_urls.discard(dep_ref.repo_url)
            
            # Check maximum depth to prevent infinite recursion
            if depth > self.max_depth:
                continue
            
            # Check if we already processed this dependency at this level or higher
            existing_node = tree.get_node(dep_ref.repo_url)
            if existing_node and existing_node.depth <= depth:
                # We've already processed this dependency at a shallower or equal depth
                # Create parent-child relationship if parent exists
                if parent_node and existing_node not in parent_node.children:
                    parent_node.children.append(existing_node)
                continue
            
            # Create a new node for this dependency
            # Note: In a real implementation, we would load the actual package here
            # For now, create a placeholder package
            placeholder_package = APMPackage(
                name=dep_ref.get_display_name(),
                version="unknown",
                source=dep_ref.repo_url
            )
            
            node = DependencyNode(
                package=placeholder_package,
                dependency_ref=dep_ref,
                depth=depth,
                parent=parent_node
            )
            
            # Add to tree
            tree.add_node(node)
            
            # Create parent-child relationship
            if parent_node:
                parent_node.children.append(node)
            
            # Try to load the dependency package and its dependencies
            # For Task 3, this focuses on the resolution algorithm structure
            # Package loading integration will be completed in Tasks 2 & 4
            try:
                # Attempt to load package - currently returns None (placeholder implementation)
                # This will integrate with Task 2 (GitHub downloader) and Task 4 (apm_modules scanning)
                loaded_package = self._try_load_dependency_package(dep_ref)
                if loaded_package:
                    # Update the node with the actual loaded package
                    node.package = loaded_package
                    
                    # Get sub-dependencies and add them to the processing queue
                    sub_dependencies = loaded_package.get_apm_dependencies()
                    for sub_dep in sub_dependencies:
                        # Avoid infinite recursion by checking if we're already processing this dep
                        # Use O(1) set lookup instead of O(n) list comprehension
                        if sub_dep.repo_url not in queued_repo_urls:
                            processing_queue.append((sub_dep, depth + 1, node))
                            queued_repo_urls.add(sub_dep.repo_url)
            except (ValueError, FileNotFoundError) as e:
                # Could not load dependency package - this is expected for remote dependencies
                # The node already has a placeholder package, so continue with that
                pass
        
        return tree
    
    def detect_circular_dependencies(self, tree: DependencyTree) -> List[CircularRef]:
        """
        Detect and report circular dependency chains.
        
        Uses depth-first search to detect cycles in the dependency graph.
        A cycle is detected when we encounter the same repository URL
        in our current traversal path.
        
        Args:
            tree: The dependency tree to analyze
            
        Returns:
            List[CircularRef]: List of detected circular dependencies
        """
        circular_deps = []
        visited: Set[str] = set()
        current_path: List[str] = []
        
        def dfs_detect_cycles(node: DependencyNode) -> None:
            """Recursive DFS function to detect cycles."""
            node_id = node.get_id()
            repo_url = node.dependency_ref.repo_url
            
            # Check if this repo URL is already in our current path (cycle detected)
            if repo_url in current_path:
                # Found a cycle - create the cycle path
                cycle_start_index = current_path.index(repo_url)
                cycle_path = current_path[cycle_start_index:] + [repo_url]
                
                circular_ref = CircularRef(
                    cycle_path=cycle_path,
                    detected_at_depth=node.depth
                )
                circular_deps.append(circular_ref)
                return
            
            # Mark current node as visited and add repo URL to path
            visited.add(node_id)
            current_path.append(repo_url)
            
            # Check all children
            for child in node.children:
                child_id = child.get_id()
                
                # Only recurse if we haven't processed this subtree completely
                if child_id not in visited or child.dependency_ref.repo_url in current_path:
                    dfs_detect_cycles(child)
            
            # Remove from path when backtracking (but keep in visited)
            current_path.pop()
        
        # Start DFS from all root level dependencies (depth 1)
        root_deps = tree.get_nodes_at_depth(1)
        for root_dep in root_deps:
            if root_dep.get_id() not in visited:
                current_path = []  # Reset path for each root
                dfs_detect_cycles(root_dep)
        
        return circular_deps
    
    def flatten_dependencies(self, tree: DependencyTree) -> FlatDependencyMap:
        """
        Flatten tree to avoid duplicate installations (NPM hoisting).
        
        Implements "first wins" conflict resolution strategy where the first
        declared dependency takes precedence over later conflicting dependencies.
        
        Args:
            tree: The dependency tree to flatten
            
        Returns:
            FlatDependencyMap: Flattened dependencies ready for installation
        """
        flat_map = FlatDependencyMap()
        seen_repos: Set[str] = set()
        
        # Process dependencies level by level (breadth-first)
        # This ensures that dependencies declared earlier in the tree get priority
        for depth in range(1, tree.max_depth + 1):
            nodes_at_depth = tree.get_nodes_at_depth(depth)
            
            # Sort nodes by their position in the tree to ensure deterministic ordering
            # In a real implementation, this would be based on declaration order
            nodes_at_depth.sort(key=lambda node: node.get_id())
            
            for node in nodes_at_depth:
                repo_url = node.dependency_ref.repo_url
                
                if repo_url not in seen_repos:
                    # First occurrence - add without conflict
                    flat_map.add_dependency(node.dependency_ref, is_conflict=False)
                    seen_repos.add(repo_url)
                else:
                    # Conflict - record it but keep the first one
                    flat_map.add_dependency(node.dependency_ref, is_conflict=True)
        
        return flat_map
    
    def _validate_dependency_reference(self, dep_ref: DependencyReference) -> bool:
        """
        Validate that a dependency reference is well-formed.
        
        Args:
            dep_ref: The dependency reference to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not dep_ref.repo_url:
            return False
        
        # Basic validation - in real implementation would be more thorough
        if '/' not in dep_ref.repo_url:
            return False
        
        return True
    
    def _try_load_dependency_package(self, dep_ref: DependencyReference) -> Optional[APMPackage]:
        """
        Try to load a dependency package from local paths.
        
        This is a placeholder implementation for Task 3 (dependency resolution algorithm).
        The actual package loading from apm_modules/ will be implemented in Task 4 
        (Enhanced Primitive Discovery System) and Task 2 (GitHub Package Downloader).
        
        Args:
            dep_ref: Reference to the dependency to load
            
        Returns:
            APMPackage: Loaded package if found, None otherwise
            
        Raises:
            ValueError: If package exists but has invalid format
            FileNotFoundError: If package cannot be found
        """
        # For Task 3 (dependency resolution), we focus on the algorithm logic
        # without implementing specific file system scanning which belongs to Task 4
        # 
        # In the final implementation:
        # - Task 2 will handle downloading packages from GitHub repositories  
        # - Task 4 will handle scanning apm_modules/ directory structure
        # - This method will integrate with both systems
        
        # For now, return None to indicate package not found locally
        # This allows the resolution algorithm to create placeholder nodes
        # and continue with dependency graph construction
        return None
    
    def _create_resolution_summary(self, graph: DependencyGraph) -> str:
        """
        Create a human-readable summary of the resolution results.
        
        Args:
            graph: The resolved dependency graph
            
        Returns:
            str: Summary string
        """
        summary = graph.get_summary()
        lines = [
            f"Dependency Resolution Summary:",
            f"  Root package: {summary['root_package']}",
            f"  Total dependencies: {summary['total_dependencies']}",
            f"  Maximum depth: {summary['max_depth']}",
        ]
        
        if summary['has_conflicts']:
            lines.append(f"  Conflicts detected: {summary['conflict_count']}")
        
        if summary['has_circular_dependencies']:
            lines.append(f"  Circular dependencies: {summary['circular_count']}")
        
        if summary['has_errors']:
            lines.append(f"  Resolution errors: {summary['error_count']}")
        
        lines.append(f"  Status: {'✅ Valid' if summary['is_valid'] else '❌ Invalid'}")
        
        return "\n".join(lines)