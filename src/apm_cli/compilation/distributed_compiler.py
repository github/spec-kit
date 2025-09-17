"""Distributed AGENTS.md compilation system following the Minimal Context Principle.

This module implements hierarchical directory-based distribution to generate multiple 
AGENTS.md files across a project's directory structure, following the AGENTS.md standard 
for nested agent context files.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

from ..primitives.models import Instruction, PrimitiveCollection
from ..version import get_version
from .template_builder import TemplateData, find_chatmode_by_name
from .constants import BUILD_ID_PLACEHOLDER
from .context_optimizer import ContextOptimizer
from ..output.formatters import CompilationFormatter
from ..output.models import CompilationResults


@dataclass
class DirectoryMap:
    """Mapping of directory structure analysis."""
    directories: Dict[Path, Set[str]]  # directory -> set of applicable file patterns
    depth_map: Dict[Path, int]  # directory -> depth level
    parent_map: Dict[Path, Optional[Path]]  # directory -> parent directory
    
    def get_max_depth(self) -> int:
        """Get maximum depth in the directory structure."""
        return max(self.depth_map.values()) if self.depth_map else 0


@dataclass 
class PlacementResult:
    """Result of AGENTS.md placement analysis."""
    agents_path: Path
    instructions: List[Instruction]
    inherited_instructions: List[Instruction] = field(default_factory=list)
    coverage_patterns: Set[str] = field(default_factory=set)
    source_attribution: Dict[str, str] = field(default_factory=dict)  # instruction_id -> source


@dataclass
class CompilationResult:
    """Result of distributed AGENTS.md compilation."""
    success: bool
    placements: List[PlacementResult]
    content_map: Dict[Path, str]  # agents_path -> content
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    stats: Dict[str, float] = field(default_factory=dict)  # Support optimization metrics


class DistributedAgentsCompiler:
    """Main compiler for generating distributed AGENTS.md files."""
    
    def __init__(self, base_dir: str = "."):
        """Initialize the distributed AGENTS.md compiler.
        
        Args:
            base_dir (str): Base directory for compilation.
        """
        try:
            self.base_dir = Path(base_dir).resolve()
        except (OSError, FileNotFoundError):
            self.base_dir = Path(base_dir).absolute()
        
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.total_files_written = 0
        self.context_optimizer = ContextOptimizer(str(self.base_dir))
        self.output_formatter = CompilationFormatter()
        self._placement_map = None
    
    def compile_distributed(
        self, 
        primitives: PrimitiveCollection,
        config: Optional[dict] = None
    ) -> CompilationResult:
        """Compile primitives into distributed AGENTS.md files.
        
        Args:
            primitives (PrimitiveCollection): Collection of primitives to compile.
            config (Optional[dict]): Configuration for distributed compilation.
                - clean_orphaned (bool): Remove orphaned AGENTS.md files. Default: False
                - dry_run (bool): Preview mode, don't write files. Default: False
        
        Returns:
            CompilationResult: Result of the distributed compilation.
        """
        self.warnings.clear()
        self.errors.clear()
        
        try:
            # Configuration with defaults aligned to Minimal Context Principle
            config = config or {}
            min_instructions = config.get('min_instructions_per_file', 1)  # Default to 1 for minimal context
            source_attribution = config.get('source_attribution', True)
            debug = config.get('debug', False)
            clean_orphaned = config.get('clean_orphaned', False)
            dry_run = config.get('dry_run', False)
            
            # Phase 1: Directory structure analysis
            directory_map = self.analyze_directory_structure(primitives.instructions)
            
            # Phase 2: Determine optimal AGENTS.md placement
            placement_map = self.determine_agents_placement(
                primitives.instructions, 
                directory_map,
                min_instructions=min_instructions,
                debug=debug
            )
            
            # Phase 3: Generate distributed AGENTS.md files
            placements = self.generate_distributed_agents_files(
                placement_map,
                primitives,
                source_attribution=source_attribution
            )
            
            # Phase 4: Handle orphaned file cleanup
            generated_paths = [p.agents_path for p in placements]
            orphaned_files = self._find_orphaned_agents_files(generated_paths)
            
            if orphaned_files:
                # Always show warnings about orphaned files
                warning_messages = self._generate_orphan_warnings(orphaned_files)
                if warning_messages:
                    self.warnings.extend(warning_messages)
                
                # Only perform actual cleanup if not dry_run and clean_orphaned is True
                if not dry_run and clean_orphaned:
                    cleanup_messages = self._cleanup_orphaned_files(orphaned_files, dry_run=False)
                    if cleanup_messages:
                        self.warnings.extend(cleanup_messages)
            
            # Phase 5: Validate coverage
            coverage_validation = self._validate_coverage(placements, primitives.instructions)
            if coverage_validation:
                self.warnings.extend(coverage_validation)
            
            # Compile statistics
            stats = self._compile_distributed_stats(placements, primitives)
            
            return CompilationResult(
                success=len(self.errors) == 0,
                placements=placements,
                content_map={p.agents_path: self._generate_agents_content(p, primitives) for p in placements},
                warnings=self.warnings.copy(),
                errors=self.errors.copy(),
                stats=stats
            )
            
        except Exception as e:
            self.errors.append(f"Distributed compilation failed: {str(e)}")
            return CompilationResult(
                success=False,
                placements=[],
                content_map={},
                warnings=self.warnings.copy(),
                errors=self.errors.copy(),
                stats={}
            )
    
    def analyze_directory_structure(self, instructions: List[Instruction]) -> DirectoryMap:
        """Analyze project directory structure based on instruction patterns.
        
        Args:
            instructions (List[Instruction]): List of instructions to analyze.
        
        Returns:
            DirectoryMap: Analysis of the directory structure.
        """
        directories: Dict[Path, Set[str]] = defaultdict(set)
        depth_map: Dict[Path, int] = {}
        parent_map: Dict[Path, Optional[Path]] = {}
        
        # Analyze each instruction's applyTo pattern
        for instruction in instructions:
            if not instruction.apply_to:
                continue
            
            pattern = instruction.apply_to
            
            # Extract directory paths from pattern
            dirs = self._extract_directories_from_pattern(pattern)
            
            for dir_path in dirs:
                abs_dir = self.base_dir / dir_path
                directories[abs_dir].add(pattern)
                
                # Calculate depth and parent relationships
                depth = len(abs_dir.relative_to(self.base_dir).parts)
                depth_map[abs_dir] = depth
                
                if depth > 0:
                    parent_dir = abs_dir.parent
                    parent_map[abs_dir] = parent_dir
                    # Ensure parent is also tracked
                    if parent_dir not in directories:
                        directories[parent_dir] = set()
                else:
                    parent_map[abs_dir] = None
        
        # Add base directory
        directories[self.base_dir].update(instruction.apply_to for instruction in instructions if instruction.apply_to)
        depth_map[self.base_dir] = 0
        parent_map[self.base_dir] = None
        
        return DirectoryMap(
            directories=dict(directories),
            depth_map=depth_map,
            parent_map=parent_map
        )
    
    def determine_agents_placement(
        self, 
        instructions: List[Instruction],
        directory_map: DirectoryMap,
        min_instructions: int = 1,
        debug: bool = False
    ) -> Dict[Path, List[Instruction]]:
        """Determine optimal AGENTS.md file placement using Context Optimization Engine.
        
        Following the Minimal Context Principle and Context Optimization, creates 
        focused AGENTS.md files that minimize context pollution while maximizing 
        relevance for agents working in specific directories.
        
        Args:
            instructions (List[Instruction]): List of instructions to place.
            directory_map (DirectoryMap): Directory structure analysis.
            min_instructions (int): Minimum instructions (default 1 for minimal context).
            max_depth (int): Maximum depth for placement.
        
        Returns:
            Dict[Path, List[Instruction]]: Optimized mapping of directory paths to instructions.
        """
        # Use the Context Optimization Engine for intelligent placement
        optimized_placement = self.context_optimizer.optimize_instruction_placement(
            instructions, 
            verbose=debug,
            enable_timing=debug  # Enable timing when debug mode is on
        )
        
        # Special case: if no instructions but constitution exists, create root placement
        if not optimized_placement:
            from .constitution import find_constitution
            constitution_path = find_constitution(Path(self.base_dir))
            if constitution_path.exists():
                # Create an empty placement for the root directory to enable verbose output
                optimized_placement = {Path(self.base_dir): []}
        
        # Store optimization results for output formatting later
        # Update with proper dry run status in the final result 
        self._placement_map = optimized_placement
        
        # Remove the verbose warning log - we'll show this in professional output instead
        
        # Filter out directories with too few instructions if specified
        if min_instructions > 1:
            filtered_placement = {}
            for dir_path, dir_instructions in optimized_placement.items():
                if len(dir_instructions) >= min_instructions or dir_path == self.base_dir:
                    filtered_placement[dir_path] = dir_instructions
                else:
                    # Move instructions to parent directory
                    parent_dir = dir_path.parent if dir_path != self.base_dir else self.base_dir
                    if parent_dir not in filtered_placement:
                        filtered_placement[parent_dir] = []
                    filtered_placement[parent_dir].extend(dir_instructions)
            
            return filtered_placement
        
        return optimized_placement
    
    def generate_distributed_agents_files(
        self,
        placement_map: Dict[Path, List[Instruction]],
        primitives: PrimitiveCollection,
        source_attribution: bool = True
    ) -> List[PlacementResult]:
        """Generate distributed AGENTS.md file contents.
        
        Args:
            placement_map (Dict[Path, List[Instruction]]): Directory to instructions mapping.
            primitives (PrimitiveCollection): Full primitive collection.
            source_attribution (bool): Whether to include source attribution.
        
        Returns:
            List[PlacementResult]: List of placement results with content.
        """
        placements = []
        
        # Special case: if no instructions but constitution exists, create root placement
        if not placement_map:
            from .constitution import find_constitution
            constitution_path = find_constitution(Path(self.base_dir))
            if constitution_path.exists():
                # Create a root placement for constitution-only projects
                root_path = Path(self.base_dir)
                agents_path = root_path / "AGENTS.md"
                
                placement = PlacementResult(
                    agents_path=agents_path,
                    instructions=[],  # No instructions, just constitution
                    coverage_patterns=set(),  # No patterns since no instructions
                    source_attribution={"constitution": "constitution.md"} if source_attribution else {}
                )
                
                placements.append(placement)
        else:
            # Normal case: create placements for each entry in placement_map
            for dir_path, instructions in placement_map.items():
                agents_path = dir_path / "AGENTS.md"
                
                # Build source attribution map if enabled
                source_map = {}
                if source_attribution:
                    for instruction in instructions:
                        source_info = getattr(instruction, 'source', 'local')
                        source_map[str(instruction.file_path)] = source_info
                
                # Extract coverage patterns
                patterns = set()
                for instruction in instructions:
                    if instruction.apply_to:
                        patterns.add(instruction.apply_to)
                
                placement = PlacementResult(
                    agents_path=agents_path,
                    instructions=instructions,
                    coverage_patterns=patterns,
                    source_attribution=source_map
                )
                
                placements.append(placement)
        
        return placements
    
    def get_compilation_results_for_display(self, is_dry_run: bool = False) -> Optional[CompilationResults]:
        """Get compilation results for CLI display integration.
        
        Args:
            is_dry_run: Whether this is a dry run.
            
        Returns:
            CompilationResults if available, None otherwise.
        """
        if self._placement_map:
            # Generate fresh compilation results with correct dry run status
            compilation_results = self.context_optimizer.get_compilation_results(
                self._placement_map, 
                is_dry_run=is_dry_run
            )
            
            # Merge distributed compiler's warnings (like orphan warnings) with optimizer warnings
            all_warnings = compilation_results.warnings + self.warnings
            
            # Create new compilation results with merged warnings
            from ..output.models import CompilationResults
            return CompilationResults(
                project_analysis=compilation_results.project_analysis,
                optimization_decisions=compilation_results.optimization_decisions,
                placement_summaries=compilation_results.placement_summaries,
                optimization_stats=compilation_results.optimization_stats,
                warnings=all_warnings,
                errors=compilation_results.errors + self.errors,
                is_dry_run=is_dry_run
            )
        return None
    
    def _extract_directories_from_pattern(self, pattern: str) -> List[Path]:
        """Extract potential directory paths from a file pattern.
        
        Args:
            pattern (str): File pattern like "src/**/*.py" or "docs/*.md"
        
        Returns:
            List[Path]: List of directory paths that could contain matching files.
        """
        directories = []
        
        # Remove filename part and wildcards to get directory structure
        # Examples:
        # "src/**/*.py" -> ["src"] 
        # "docs/*.md" -> ["docs"]
        # "**/*.py" -> ["."] (current directory)
        # "*.py" -> ["."] (current directory)
        
        if pattern.startswith("**/"):
            # Global pattern - applies to all directories
            directories.append(Path("."))
        elif "/" in pattern:
            # Extract directory part
            dir_part = pattern.split("/")[0]
            if not dir_part.startswith("*"):
                directories.append(Path(dir_part))
            else:
                directories.append(Path("."))
        else:
            # No directory part - applies to current directory
            directories.append(Path("."))
        
        return directories
    
    def _find_best_directory(
        self, 
        instruction: Instruction, 
        directory_map: DirectoryMap,
        max_depth: int
    ) -> Path:
        """Find the best directory for placing an instruction.
        
        Args:
            instruction (Instruction): Instruction to place.
            directory_map (DirectoryMap): Directory structure analysis.
            max_depth (int): Maximum allowed depth.
        
        Returns:
            Path: Best directory path for the instruction.
        """
        if not instruction.apply_to:
            return self.base_dir
        
        pattern = instruction.apply_to
        best_dir = self.base_dir
        best_specificity = 0
        
        for dir_path in directory_map.directories:
            # Skip directories that are too deep
            if directory_map.depth_map.get(dir_path, 0) > max_depth:
                continue
            
            # Check if this directory could contain files matching the pattern
            if pattern in directory_map.directories[dir_path]:
                # Prefer more specific (deeper) directories
                specificity = directory_map.depth_map.get(dir_path, 0)
                if specificity > best_specificity:
                    best_specificity = specificity
                    best_dir = dir_path
        
        return best_dir
    
    def _generate_agents_content(
        self, 
        placement: PlacementResult, 
        primitives: PrimitiveCollection
    ) -> str:
        """Generate AGENTS.md content for a specific placement.
        
        Args:
            placement (PlacementResult): Placement result with instructions.
            primitives (PrimitiveCollection): Full primitive collection.
        
        Returns:
            str: Generated AGENTS.md content.
        """
        sections = []
        
        # Header with source attribution
        sections.append("# AGENTS.md")
        sections.append("<!-- Generated by APM CLI from distributed .apm/ primitives -->")
        sections.append(BUILD_ID_PLACEHOLDER)
        sections.append(f"<!-- APM Version: {get_version()} -->")
        
        # Add source attribution summary if enabled
        if placement.source_attribution:
            sources = set(placement.source_attribution.values())
            if len(sources) > 1:
                sections.append(f"<!-- Sources: {', '.join(sorted(sources))} -->")
            else:
                sections.append(f"<!-- Source: {list(sources)[0] if sources else 'local'} -->")
        
        sections.append("")
        
        # Group instructions by pattern
        pattern_groups: Dict[str, List[Instruction]] = defaultdict(list)
        for instruction in placement.instructions:
            if instruction.apply_to:
                pattern_groups[instruction.apply_to].append(instruction)
        
        # Generate sections for each pattern
        for pattern, pattern_instructions in sorted(pattern_groups.items()):
            sections.append(f"## Files matching `{pattern}`")
            sections.append("")
            
            for instruction in pattern_instructions:
                content = instruction.content.strip()
                if content:
                    # Add source attribution for individual instructions
                    if placement.source_attribution:
                        source = placement.source_attribution.get(str(instruction.file_path), 'local')
                        try:
                            rel_path = instruction.file_path.relative_to(self.base_dir)
                        except ValueError:
                            rel_path = instruction.file_path
                        
                        sections.append(f"<!-- Source: {source} {rel_path} -->")
                    
                    sections.append(content)
                    sections.append("")
        
        # Footer
        sections.append("---")
        sections.append("*This file was generated by APM CLI. Do not edit manually.*")
        sections.append("*To regenerate: `specify apm compile`*")
        sections.append("")
        
        return "\n".join(sections)
    
    def _validate_coverage(
        self, 
        placements: List[PlacementResult], 
        all_instructions: List[Instruction]
    ) -> List[str]:
        """Validate that all instructions are covered by placements.
        
        Args:
            placements (List[PlacementResult]): Generated placements.
            all_instructions (List[Instruction]): All available instructions.
        
        Returns:
            List[str]: List of coverage warnings.
        """
        warnings = []
        placed_instructions = set()
        
        for placement in placements:
            placed_instructions.update(str(inst.file_path) for inst in placement.instructions)
        
        all_instruction_paths = set(str(inst.file_path) for inst in all_instructions)
        
        missing_instructions = all_instruction_paths - placed_instructions
        if missing_instructions:
            warnings.append(f"Instructions not placed in any AGENTS.md: {', '.join(missing_instructions)}")
        
        return warnings
    
    def _find_orphaned_agents_files(self, generated_paths: List[Path]) -> List[Path]:
        """Find existing AGENTS.md files that weren't generated in the current compilation.
        
        Args:
            generated_paths (List[Path]): List of AGENTS.md files generated in current run.
        
        Returns:
            List[Path]: List of orphaned AGENTS.md files that should be cleaned up.
        """
        orphaned_files = []
        generated_set = set(generated_paths)
        
        # Find all existing AGENTS.md files in the project
        for agents_file in self.base_dir.rglob("AGENTS.md"):
            # Skip files that are outside our project or in special directories
            try:
                relative_path = agents_file.relative_to(self.base_dir)
                
                # Skip files in certain directories that shouldn't be cleaned
                skip_dirs = {".git", ".apm", "node_modules", "__pycache__", ".pytest_cache", "apm_modules"}
                if any(part in skip_dirs for part in relative_path.parts):
                    continue
                    
                # If this existing file wasn't generated in current run, it's orphaned
                if agents_file not in generated_set:
                    orphaned_files.append(agents_file)
                    
            except ValueError:
                # File is outside base_dir, skip it
                continue
        
        return orphaned_files

    def _generate_orphan_warnings(self, orphaned_files: List[Path]) -> List[str]:
        """Generate warning messages for orphaned AGENTS.md files.
        
        Args:
            orphaned_files (List[Path]): List of orphaned files to warn about.
        
        Returns:
            List[str]: List of warning messages.
        """
        warning_messages = []
        
        if not orphaned_files:
            return warning_messages
        
        # Professional warning format with readable list for multiple files
        if len(orphaned_files) == 1:
            rel_path = orphaned_files[0].relative_to(self.base_dir)
            warning_messages.append(f"Orphaned AGENTS.md found: {rel_path} - run 'apm compile --clean' to remove")
        else:
            # For multiple files, create a single multi-line warning message
            file_list = []
            for file_path in orphaned_files[:5]:  # Show first 5
                rel_path = file_path.relative_to(self.base_dir)
                file_list.append(f"  • {rel_path}")
            if len(orphaned_files) > 5:
                file_list.append(f"  • ...and {len(orphaned_files) - 5} more")
            
            # Create one cohesive warning message
            files_text = "\n".join(file_list)
            warning_messages.append(f"Found {len(orphaned_files)} orphaned AGENTS.md files:\n{files_text}\n  Run 'apm compile --clean' to remove orphaned files")
        
        return warning_messages

    def _cleanup_orphaned_files(self, orphaned_files: List[Path], dry_run: bool = False) -> List[str]:
        """Actually remove orphaned AGENTS.md files.
        
        Args:
            orphaned_files (List[Path]): List of orphaned files to remove.
            dry_run (bool): If True, don't actually remove files, just report what would be removed.
        
        Returns:
            List[str]: List of cleanup status messages.
        """
        cleanup_messages = []
        
        if not orphaned_files:
            return cleanup_messages
        
        if dry_run:
            # In dry-run mode, just report what would be cleaned
            cleanup_messages.append(f"🧹 Would clean up {len(orphaned_files)} orphaned AGENTS.md files")
            for file_path in orphaned_files:
                rel_path = file_path.relative_to(self.base_dir)
                cleanup_messages.append(f"  • {rel_path}")
        else:
            # Actually perform the cleanup
            cleanup_messages.append(f"🧹 Cleaning up {len(orphaned_files)} orphaned AGENTS.md files")
            for file_path in orphaned_files:
                try:
                    rel_path = file_path.relative_to(self.base_dir)
                    file_path.unlink()
                    cleanup_messages.append(f"  ✓ Removed {rel_path}")
                except Exception as e:
                    cleanup_messages.append(f"  ✗ Failed to remove {rel_path}: {str(e)}")
        
        return cleanup_messages

    def _compile_distributed_stats(
        self, 
        placements: List[PlacementResult], 
        primitives: PrimitiveCollection
    ) -> Dict[str, float]:
        """Compile statistics about the distributed compilation with optimization metrics.
        
        Args:
            placements (List[PlacementResult]): Generated placements.
            primitives (PrimitiveCollection): Full primitive collection.
        
        Returns:
            Dict[str, float]: Compilation statistics including optimization metrics.
        """
        total_instructions = sum(len(p.instructions) for p in placements)
        total_patterns = sum(len(p.coverage_patterns) for p in placements)
        
        # Get optimization metrics
        placement_map = {Path(p.agents_path.parent): p.instructions for p in placements}
        optimization_stats = self.context_optimizer.get_optimization_stats(placement_map)
        
        # Combine traditional stats with optimization metrics
        stats = {
            "agents_files_generated": len(placements),
            "total_instructions_placed": total_instructions,
            "total_patterns_covered": total_patterns,
            "primitives_found": primitives.count(),
            "chatmodes": len(primitives.chatmodes),
            "instructions": len(primitives.instructions),
            "contexts": len(primitives.contexts)
        }
        
        # Add optimization metrics from OptimizationStats object
        if optimization_stats:
            stats.update({
                "average_context_efficiency": optimization_stats.average_context_efficiency,
                "pollution_improvement": optimization_stats.pollution_improvement,
                "baseline_efficiency": optimization_stats.baseline_efficiency,
                "placement_accuracy": optimization_stats.placement_accuracy,
                "generation_time_ms": optimization_stats.generation_time_ms,
                "total_agents_files": optimization_stats.total_agents_files,
                "directories_analyzed": optimization_stats.directories_analyzed
            })
        
        return stats