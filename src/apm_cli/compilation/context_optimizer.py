"""Context Optimizer for APM distributed compilation system.

This module implements the Context Optimization Engine that minimizes 
irrelevant context loaded by agents working in specific directories,
following the Minimal Context Principle.
"""

import fnmatch
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from functools import lru_cache
import glob

from ..primitives.models import Instruction
from ..output.models import (
    CompilationResults, ProjectAnalysis, OptimizationDecision, OptimizationStats,
    PlacementStrategy, PlacementSummary
)


@dataclass
class DirectoryAnalysis:
    """Analysis of a directory's file distribution and patterns."""
    directory: Path
    depth: int
    total_files: int
    pattern_matches: Dict[str, int] = field(default_factory=dict)  # pattern -> count
    file_types: Set[str] = field(default_factory=set)
    
    def get_relevance_score(self, pattern: str) -> float:
        """Calculate relevance score for a pattern in this directory."""
        if self.total_files == 0:
            return 0.0
        matches = self.pattern_matches.get(pattern, 0)
        return matches / self.total_files


@dataclass
class InheritanceAnalysis:
    """Analysis of context inheritance chain for a working directory."""
    working_directory: Path
    inheritance_chain: List[Path]  # From most specific to root
    total_context_load: int = 0
    relevant_context_load: int = 0
    pollution_score: float = 0.0
    
    def get_efficiency_ratio(self) -> float:
        """Calculate context efficiency ratio."""
        if self.total_context_load == 0:
            return 1.0
        return self.relevant_context_load / self.total_context_load


@dataclass
class PlacementCandidate:
    """Candidate placement for an instruction with optimization scores."""
    instruction: Instruction
    directory: Path
    direct_relevance: float
    inheritance_pollution: float
    depth_specificity: float
    total_score: float
    
    def __post_init__(self):
        """Calculate total optimization score."""
        self.total_score = (
            self.direct_relevance * 1.0 +          # Direct relevance weight
            -self.inheritance_pollution * 0.5 +     # Pollution penalty
            self.depth_specificity * 0.1            # Depth bonus
        )


class ContextOptimizer:
    """Context Optimization Engine for distributed AGENTS.md placement."""
    
    # Mathematical optimization parameters
    COVERAGE_EFFICIENCY_WEIGHT = 1.0
    POLLUTION_MINIMIZATION_WEIGHT = 0.8
    MAINTENANCE_LOCALITY_WEIGHT = 0.3
    DEPTH_PENALTY_FACTOR = 0.1
    DIVERSITY_FACTOR_BASE = 0.5
    
    # Distribution score thresholds for placement strategy
    LOW_DISTRIBUTION_THRESHOLD = 0.3
    HIGH_DISTRIBUTION_THRESHOLD = 0.7
    
    def __init__(self, base_dir: str = "."):
        """Initialize the context optimizer.
        
        Args:
            base_dir (str): Base directory for optimization analysis.
        """
        try:
            self.base_dir = Path(base_dir).resolve()
        except (OSError, FileNotFoundError):
            self.base_dir = Path(base_dir).absolute()
        
        self._directory_cache: Dict[Path, DirectoryAnalysis] = {}
        self._pattern_cache: Dict[str, Set[Path]] = {}
        
        # Performance optimization caches
        self._glob_cache: Dict[str, List[str]] = {}
        self._file_list_cache: Optional[List[Path]] = None
        self._timing_enabled = False
        self._phase_timings: Dict[str, float] = {}
        
        # Data collection for output formatting
        self._optimization_decisions: List[OptimizationDecision] = []
        self._warnings: List[str] = []
        self._errors: List[str] = []
        self._start_time: Optional[float] = None
    
    def enable_timing(self, verbose: bool = False):
        """Enable performance timing instrumentation."""
        self._timing_enabled = verbose
        self._phase_timings.clear()
    
    def _time_phase(self, phase_name: str, operation_func, *args, **kwargs):
        """Time a phase of optimization and optionally log it."""
        if not self._timing_enabled:
            return operation_func(*args, **kwargs)
        
        start_time = time.time()
        result = operation_func(*args, **kwargs)
        duration = time.time() - start_time
        self._phase_timings[phase_name] = duration
        
        # Only show timing in verbose mode with professional formatting
        if self._timing_enabled and hasattr(self, '_verbose') and self._verbose:
            print(f"⏱️  {phase_name}: {duration*1000:.1f}ms")
        return result
    
    def _cached_glob(self, pattern: str) -> List[str]:
        """Cache glob results to avoid repeated filesystem scans."""
        if pattern not in self._glob_cache:
            old_cwd = os.getcwd()
            try:
                os.chdir(str(self.base_dir))  # Convert Path to string for os.chdir
                self._glob_cache[pattern] = glob.glob(pattern, recursive=True)
            finally:
                os.chdir(old_cwd)
        return self._glob_cache[pattern]
    
    def _get_all_files(self) -> List[Path]:
        """Get cached list of all files in project."""
        if self._file_list_cache is None:
            self._file_list_cache = []
            for root, dirs, files in os.walk(self.base_dir):
                # Skip hidden directories for performance
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    if not file.startswith('.'):
                        self._file_list_cache.append(Path(root) / file)
        return self._file_list_cache
    
    def optimize_instruction_placement(
        self, 
        instructions: List[Instruction],
        verbose: bool = False,
        enable_timing: bool = False
    ) -> Dict[Path, List[Instruction]]:
        """Optimize placement of instructions across directories with performance timing.
        
        Args:
            instructions (List[Instruction]): Instructions to optimize.
            verbose (bool): Collect verbose analysis data.
            enable_timing (bool): Enable detailed timing measurements.
        
        Returns:
            Dict[Path, List[Instruction]]: Optimized placement mapping.
        """
        self._start_time = time.time()
        self._timing_enabled = enable_timing
        self._verbose = verbose  # Store verbose mode for timing display
        
        # Don't show the "timing enabled" message - it's not professional
        if enable_timing and verbose:
            self._compilation_start_time = time.time()
        
        self.enable_timing(verbose)
        self._optimization_decisions.clear()
        self._warnings.clear()
        self._errors.clear()
        
        # Phase 1: Analyze project structure
        self._time_phase("📊 Project Analysis", self._analyze_project_structure)
        
        # Phase 2: Analyze each instruction for optimal placement
        placement_map: Dict[Path, List[Instruction]] = defaultdict(list)
        
        def process_instructions():
            for instruction in instructions:
                if not instruction.apply_to:
                    # Instructions without patterns go to root
                    placement_map[self.base_dir].append(instruction)
                    
                    # Record global instruction decision  
                    # Global instructions have maximum relevance since they apply everywhere
                    global_relevance = 1.0
                    
                    self._optimization_decisions.append(OptimizationDecision(
                        instruction=instruction,
                        pattern="(global)",
                        matching_directories=1,
                        total_directories=len(self._directory_cache),
                        distribution_score=1.0,
                        strategy=PlacementStrategy.DISTRIBUTED,
                        placement_directories=[self.base_dir],
                        reasoning="Global instruction placed at project root",
                        relevance_score=global_relevance
                    ))
                    continue
                
                optimal_placements = self._find_optimal_placements(instruction, verbose)
                
                # Add instruction to optimal placement(s)
                for directory in optimal_placements:
                    placement_map[directory].append(instruction)
        
        self._time_phase("🎯 Instruction Processing", process_instructions)
        
        return dict(placement_map)
    
    def analyze_context_inheritance(
        self, 
        working_directory: Path,
        placement_map: Dict[Path, List[Instruction]]
    ) -> InheritanceAnalysis:
        """Analyze context inheritance chain for a working directory.
        
        Args:
            working_directory (Path): Directory where agent is working.
            placement_map (Dict[Path, List[Instruction]]): Current placement mapping.
        
        Returns:
            InheritanceAnalysis: Analysis of inheritance efficiency.
        """
        inheritance_chain = self._get_inheritance_chain(working_directory)
        
        total_context = 0
        relevant_context = 0
        
        for directory in inheritance_chain:
            if directory in placement_map:
                instructions = placement_map[directory]
                total_context += len(instructions)
                
                # Count relevant instructions for working directory
                for instruction in instructions:
                    if self._is_instruction_relevant(instruction, working_directory):
                        relevant_context += 1
        
        pollution_score = 1.0 - (relevant_context / total_context) if total_context > 0 else 0.0
        
        return InheritanceAnalysis(
            working_directory=working_directory,
            inheritance_chain=inheritance_chain,
            total_context_load=total_context,
            relevant_context_load=relevant_context,
            pollution_score=pollution_score
        )
    
    def get_optimization_stats(self, placement_map: Dict[Path, List[Instruction]]) -> OptimizationStats:
        """Calculate optimization statistics for the placement map."""
        if not placement_map:
            return OptimizationStats(
                average_context_efficiency=0.0,
                total_agents_files=0,
                directories_analyzed=len(self._directory_cache)
            )
        
        # Calculate average context efficiency across all directories with files
        all_directories = set(self._directory_cache.keys())
        efficiency_scores = []
        
        for directory in all_directories:
            if self._directory_cache[directory].total_files > 0:
                inheritance = self.analyze_context_inheritance(directory, placement_map)
                efficiency_scores.append(inheritance.get_efficiency_ratio())
        
        average_efficiency = sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0.0
        
        return OptimizationStats(
            average_context_efficiency=average_efficiency,
            total_agents_files=len(placement_map),
            directories_analyzed=len(self._directory_cache)
        )

    def get_compilation_results(
        self,
        placement_map: Dict[Path, List[Instruction]],
        is_dry_run: bool = False
    ) -> CompilationResults:
        """Generate comprehensive compilation results for output formatting.
        
        Args:
            placement_map: Final instruction placement mapping.
            is_dry_run: Whether this is a dry run.
            
        Returns:
            CompilationResults with all analysis data.
        """
        # Calculate generation time
        generation_time_ms = None
        if self._start_time is not None:
            generation_time_ms = int((time.time() - self._start_time) * 1000)
        
        # Create project analysis
        file_types = set()
        total_files = 0
        
        for analysis in self._directory_cache.values():
            file_types.update(analysis.file_types)
            total_files += analysis.total_files
        
        # Check for constitution
        from .constitution import find_constitution
        constitution_path = find_constitution(Path(self.base_dir))
        constitution_detected = constitution_path.exists()
        
        project_analysis = ProjectAnalysis(
            directories_scanned=len(self._directory_cache),
            files_analyzed=total_files,
            file_types_detected=file_types,
            instruction_patterns_detected=len(self._optimization_decisions),
            max_depth=max((a.depth for a in self._directory_cache.values()), default=0),
            constitution_detected=constitution_detected,
            constitution_path=str(constitution_path.relative_to(self.base_dir)) if constitution_detected else None
        )
        
        # Create placement summaries
        placement_summaries = []
        
        # Special case: if no instructions but constitution exists, create root placement
        if not placement_map and constitution_detected:
            # Create a root placement for constitution-only projects
            root_sources = {"constitution.md"}
            summary = PlacementSummary(
                path=Path(self.base_dir),
                instruction_count=0,
                source_count=len(root_sources),
                sources=list(root_sources)
            )
            placement_summaries.append(summary)
        else:
            # Normal case: create summaries for each placement in the map
            for directory, instructions in placement_map.items():
                # Count unique sources
                sources = set()
                for instruction in instructions:
                    if hasattr(instruction, 'source_file') and instruction.source_file:
                        sources.add(instruction.source_file)
                    elif hasattr(instruction, 'source') and instruction.source:
                        sources.add(str(instruction.source))
                
                # Add constitution as a source if it exists and will be injected
                if constitution_detected:
                    sources.add("constitution.md")
                
                summary = PlacementSummary(
                    path=directory,
                    instruction_count=len(instructions),
                    source_count=len(sources),
                    sources=list(sources)
                )
                placement_summaries.append(summary)
        
        # Get optimization statistics
        optimization_stats = self.get_optimization_stats(placement_map)
        optimization_stats.generation_time_ms = generation_time_ms
        
        return CompilationResults(
            project_analysis=project_analysis,
            optimization_decisions=self._optimization_decisions.copy(),
            placement_summaries=placement_summaries,
            optimization_stats=optimization_stats,
            warnings=self._warnings.copy(),
            errors=self._errors.copy(),
            is_dry_run=is_dry_run
        )
    
    def _analyze_project_structure(self) -> None:
        """Analyze the project structure and cache results."""
        self._directory_cache.clear()
        self._pattern_cache.clear()  # Also clear pattern cache for deterministic behavior
        
        # Track visited directories to prevent infinite loops
        visited_dirs = set()
        
        for root, dirs, files in os.walk(self.base_dir):
            current_path = Path(root)
            
            # Safety check for infinite loops
            if current_path in visited_dirs:
                continue
            visited_dirs.add(current_path)
            
            # Calculate depth for analysis
            try:
                relative_path = current_path.relative_to(self.base_dir)
                depth = len(relative_path.parts)
            except ValueError:
                depth = 0

            # Skip hidden directories and common ignore patterns
            if any(part.startswith('.') for part in current_path.parts[len(self.base_dir.parts):]):
                continue
            
            if any(ignore in str(current_path) for ignore in ['node_modules', '__pycache__', '.git', 'dist', 'build']):
                continue
            
            # Analyze files in this directory
            total_files = len([f for f in files if not f.startswith('.')])
            if total_files == 0:
                continue
            
            analysis = DirectoryAnalysis(
                directory=current_path,
                depth=depth,
                total_files=total_files
            )
            
            # Analyze file types
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = current_path / file
                analysis.file_types.add(file_path.suffix)
            
            self._directory_cache[current_path] = analysis
    
    def _find_optimal_placements(
        self,
        instruction: Instruction,
        verbose: bool = False
    ) -> List[Path]:
        """Find optimal placement(s) for an instruction using mathematical optimization.
        
        This implements constraint satisfaction optimization that guarantees every 
        instruction gets placed at its mathematically optimal location(s).
        
        Args:
            instruction (Instruction): Instruction to place.
            verbose (bool): Collect verbose analysis data.
        
        Returns:
            List[Path]: List of optimal directory placements.
        """
        return self._solve_placement_optimization(instruction, verbose)
    
    def _solve_placement_optimization(
        self,
        instruction: Instruction, 
        verbose: bool = False
    ) -> List[Path]:
        """Mathematical optimization solver for instruction placement.
        
        Implements the mathematician's objective function:
        minimize: Σ(context_pollution × directory_weight) 
        subject to: ∀instruction → ∃placement
        
        Args:
            instruction (Instruction): Instruction to optimize placement for.
            verbose (bool): Collect verbose analysis data.
        
        Returns:
            List[Path]: Mathematically optimal placement(s).
        """
        pattern = instruction.apply_to
        
        # Find all directories with matching files
        matching_directories = self._find_matching_directories(pattern)
        
        if not matching_directories:
            # Smart fallback: Try to place in semantically appropriate directory
            intended_dir = self._extract_intended_directory_from_pattern(pattern)
            
            if intended_dir:
                # Place in the intended directory (e.g., docs/ for docs/**/*.md)
                placement = intended_dir
                reasoning = f"No matching files found, placed in intended directory '{intended_dir.relative_to(self.base_dir)}'"
                self._warnings.append(f"Pattern '{pattern}' matches no files - placing in intended directory '{intended_dir.relative_to(self.base_dir)}'")
            else:
                # Fallback to root for global patterns
                placement = self.base_dir
                reasoning = "No matching files found, fallback to root placement"
                self._warnings.append(f"Pattern '{pattern}' matches no files - placing at project root")
            
            # Calculate relevance score for the fallback placement
            relevance_score = 0.0  # No matches means no relevance
            if placement in self._directory_cache:
                relevance_score = self._calculate_coverage_efficiency(placement, pattern)
            
            decision = OptimizationDecision(
                instruction=instruction,
                pattern=pattern,
                matching_directories=0,
                total_directories=len(self._directory_cache),
                distribution_score=0.0,
                strategy=PlacementStrategy.DISTRIBUTED,
                placement_directories=[placement],
                reasoning=reasoning,
                relevance_score=relevance_score
            )
            self._optimization_decisions.append(decision)
            
            return [placement]
        
        # Calculate distribution score with diversity factor
        distribution_score = self._calculate_distribution_score(matching_directories)
        
        # Apply three-tier placement strategy based on mathematical analysis
        if distribution_score < self.LOW_DISTRIBUTION_THRESHOLD:
            # Low distribution: Single Point Placement
            strategy = PlacementStrategy.SINGLE_POINT
            placements = self._optimize_single_point_placement(matching_directories, instruction, verbose)
            reasoning = "Low distribution pattern optimized for minimal pollution"
        elif distribution_score > self.HIGH_DISTRIBUTION_THRESHOLD:
            # High distribution: Distributed Placement
            strategy = PlacementStrategy.DISTRIBUTED
            placements = self._optimize_distributed_placement(matching_directories, instruction, verbose)
            reasoning = "High distribution pattern placed at root to minimize duplication"
        else:
            # Medium distribution: Selective Multi-Placement
            strategy = PlacementStrategy.SELECTIVE_MULTI
            placements = self._optimize_selective_placement(matching_directories, instruction, verbose)
            reasoning = "Medium distribution pattern with selective high-relevance placement"
        
        # Calculate relevance score for the primary placement directory
        relevance_score = 0.0
        if placements:
            primary_placement = placements[0]  # Use first placement as representative
            if primary_placement in self._directory_cache:
                relevance_score = self._calculate_coverage_efficiency(primary_placement, pattern)
        
        # Record optimization decision
        decision = OptimizationDecision(
            instruction=instruction,
            pattern=pattern,
            matching_directories=len(matching_directories),
            total_directories=len(self._directory_cache),
            distribution_score=distribution_score,
            strategy=strategy,
            placement_directories=placements,
            reasoning=reasoning,
            relevance_score=relevance_score
        )
        self._optimization_decisions.append(decision)
        
        return placements
    
    def _extract_intended_directory_from_pattern(self, pattern: str) -> Optional[Path]:
        """Extract the intended directory from a pattern like 'docs/**/*.md' -> 'docs'.
        
        Args:
            pattern (str): File pattern to analyze.
        
        Returns:
            Optional[Path]: Intended directory path, or None if pattern is global.
        """
        if not pattern or pattern.startswith('**/'):
            return None  # Global pattern
        
        if '/' in pattern:
            # Extract the first directory component
            parts = pattern.split('/')
            first_part = parts[0]
            
            # Skip if it's a wildcard
            if '*' not in first_part and first_part:
                intended_dir = self.base_dir / first_part
                if intended_dir.exists() and intended_dir.is_dir():
                    return intended_dir
        
        return None
    
    def _expand_glob_pattern(self, pattern: str) -> List[str]:
        """Expand glob pattern with brace expansion.
        
        Args:
            pattern (str): Pattern like '**/*.{css,scss}'
        
        Returns:
            List[str]: Expanded patterns like ['**/*.css', '**/*.scss']
        """
        import re
        
        # Handle brace expansion like {css,scss}
        brace_match = re.search(r'\{([^}]+)\}', pattern)
        if brace_match:
            extensions = brace_match.group(1).split(',')
            base_pattern = pattern[:brace_match.start()] + '{}' + pattern[brace_match.end():]
            return [base_pattern.format(ext) for ext in extensions]
        
        return [pattern]
    
    def _file_matches_pattern(self, file_path: Path, pattern: str) -> bool:
        """Check if a file matches a given pattern with optimized performance.
        
        Args:
            file_path (Path): File path to check
            pattern (str): Glob pattern to match against
        
        Returns:
            bool: True if file matches pattern
        """
        # Expand any brace patterns
        expanded_patterns = self._expand_glob_pattern(pattern)
        
        for expanded_pattern in expanded_patterns:
            # For patterns with **, use cached glob results
            if '**' in expanded_pattern:
                try:
                    # Resolve both paths to handle symlinks and path inconsistencies
                    resolved_file = file_path.resolve()
                    rel_path = resolved_file.relative_to(self.base_dir)
                    
                    # Use cached glob results instead of repeated glob calls
                    matches = self._cached_glob(expanded_pattern)
                    # Convert to Path objects for comparison
                    match_paths = {Path(match) for match in matches}
                    if rel_path in match_paths:
                        return True
                except (ValueError, OSError):
                    pass
            else:
                # For non-recursive patterns, use fnmatch as before
                try:
                    # Resolve both paths to handle symlinks and path inconsistencies
                    resolved_file = file_path.resolve()
                    rel_path = resolved_file.relative_to(self.base_dir)
                    if fnmatch.fnmatch(str(rel_path), expanded_pattern):
                        return True
                except ValueError:
                    pass
                
                # Only use filename match for patterns without directory structure
                # This prevents "docs/**/*.md" from matching any "*.md" file anywhere
                if '/' not in expanded_pattern:
                    if fnmatch.fnmatch(file_path.name, expanded_pattern):
                        return True
        
        return False
    
    def _find_matching_directories(self, pattern: str) -> Set[Path]:
        """Find directories that contain files matching the pattern.
        
        Args:
            pattern (str): File pattern to match.
        
        Returns:
            Set[Path]: Set of directories with matching files.
        """
        # Use cached result if available
        if pattern in self._pattern_cache:
            return self._pattern_cache[pattern]
        
        matching_dirs: Set[Path] = set()
        
        # Use the reliable approach for all patterns
        for directory, analysis in sorted(self._directory_cache.items()):
            try:
                files = [f for f in directory.iterdir() if f.is_file() and not f.name.startswith('.')]
                
                match_count = 0
                for file_path in files:
                    if self._file_matches_pattern(file_path, pattern):
                        match_count += 1
                        matching_dirs.add(directory)
                
                if match_count > 0:
                    analysis.pattern_matches[pattern] = match_count
            except (OSError, PermissionError):
                continue
        
        self._pattern_cache[pattern] = matching_dirs
        return matching_dirs
    
    def _calculate_inheritance_pollution(self, directory: Path, pattern: str) -> float:
        """Calculate inheritance pollution score for placing instruction at directory.
        
        Args:
            directory (Path): Candidate placement directory.
            pattern (str): Instruction pattern.
        
        Returns:
            float: Pollution score (higher = more pollution).
        """
        pollution_score = 0.0
        
        # Optimization: Only check direct children instead of all directories
        # This prevents O(n²) complexity with unlimited depth analysis
        try:
            direct_children = [
                child for child in directory.iterdir() 
                if child.is_dir() and child in self._directory_cache
            ]
            
            # Check only direct child directories for pollution
            for child_dir in direct_children:
                analysis = self._directory_cache[child_dir]
                
                # If child has no matching files, this creates pollution
                child_relevance = analysis.get_relevance_score(pattern)
                if child_relevance == 0.0:
                    pollution_score += 0.5  # Strong pollution penalty
                elif child_relevance < 0.1:  # Weak relevance threshold
                    pollution_score += 0.2  # Weak pollution penalty
        except (OSError, PermissionError):
            # Skip directories we can't read
            pass
        
        return pollution_score
    
    def _calculate_distribution_score(self, matching_directories: Set[Path]) -> float:
        """Calculate distribution score with diversity factor.
        
        Args:
            matching_directories: Set of directories with pattern matches.
        
        Returns:
            float: Distribution score accounting for spread and depth diversity.
        """
        total_dirs_with_files = len([d for d in self._directory_cache.values() if d.total_files > 0])
        if total_dirs_with_files == 0:
            return 0.0
        
        base_ratio = len(matching_directories) / total_dirs_with_files
        
        # Calculate diversity factor based on depth distribution
        depths = [self._directory_cache[d].depth for d in matching_directories]
        if not depths:
            return base_ratio
        
        depth_variance = sum((d - sum(depths)/len(depths))**2 for d in depths) / len(depths)
        diversity_factor = 1.0 + (depth_variance * self.DIVERSITY_FACTOR_BASE)
        
        return base_ratio * diversity_factor
    
    def _optimize_single_point_placement(
        self, 
        matching_directories: Set[Path], 
        instruction: Instruction,
        verbose: bool = False
    ) -> List[Path]:
        """Optimize placement for low distribution patterns (< 0.3 ratio).
        
        Strategy: Ensure mandatory coverage constraint first, then optimize for minimal pollution.
        Coverage guarantee takes priority over efficiency optimization.
        """
        candidates = self._generate_all_candidates(matching_directories, instruction)
        
        if not candidates:
            return [self.base_dir]
        
        # CRITICAL: Mandatory coverage constraint - filter candidates that provide complete coverage
        coverage_candidates = []
        for candidate in candidates:
            # Verify this placement can provide hierarchical coverage for ALL matching directories
            covered_directories = self._calculate_hierarchical_coverage([candidate.directory], matching_directories)
            if covered_directories == matching_directories:
                # This candidate satisfies the mandatory coverage constraint
                coverage_candidates.append(candidate)
        
        # If no single candidate provides complete coverage, find minimal coverage placement
        if not coverage_candidates:
            minimal_coverage = self._find_minimal_coverage_placement(matching_directories)
            if minimal_coverage:
                return [minimal_coverage]
            else:
                # Ultimate fallback to root to guarantee coverage
                return [self.base_dir]
        
        # Among coverage-compliant candidates, select the one with best efficiency/pollution ratio
        best_candidate = max(coverage_candidates, key=lambda c: (
            c.coverage_efficiency - c.pollution_score
        ))
        
        return [best_candidate.directory]
    
    def _optimize_distributed_placement(
        self, 
        matching_directories: Set[Path], 
        instruction: Instruction,
        verbose: bool = False
    ) -> List[Path]:
        """Optimize placement for high distribution patterns (> 0.7 ratio).
        
        Strategy: Place at root to minimize duplication while maintaining accessibility.
        """
        return [self.base_dir]
    
    def _optimize_selective_placement(
        self, 
        matching_directories: Set[Path], 
        instruction: Instruction,
        verbose: bool = False
    ) -> List[Path]:
        """Optimize placement for medium distribution patterns (0.3-0.7 ratio).
        
        Strategy: Ensure hierarchical coverage - all matching files must be able 
        to inherit the instruction through the hierarchical AGENTS.md system.
        """
        # First check if we can achieve complete coverage with a single high-level placement
        coverage_placement = self._find_minimal_coverage_placement(matching_directories)
        if coverage_placement:
            return [coverage_placement]
        
        # If single placement doesn't work, use multi-placement strategy
        candidates = self._generate_all_candidates(matching_directories, instruction)
        
        if not candidates:
            return [self.base_dir]
        
        # Filter for high-relevance candidates (top 20% or relevance > 0.8)
        high_relevance_threshold = max(0.8, 
            sorted([c.coverage_efficiency for c in candidates], reverse=True)[max(0, len(candidates)//5)])
        
        high_relevance_candidates = [
            c for c in candidates 
            if c.coverage_efficiency >= high_relevance_threshold
        ]
        
        if not high_relevance_candidates:
            # Fallback: use best candidate
            high_relevance_candidates = [max(candidates, key=lambda c: c.total_score)]
        
        optimal_placements = [c.directory for c in high_relevance_candidates]
        
        # CRITICAL: Verify hierarchical coverage
        covered_directories = self._calculate_hierarchical_coverage(optimal_placements, matching_directories)
        uncovered_directories = matching_directories - covered_directories
        
        if uncovered_directories:
            # Coverage violation! Find minimal placement that covers everything
            minimal_coverage = self._find_minimal_coverage_placement(matching_directories)
            if minimal_coverage:
                return [minimal_coverage]
            else:
                # Fallback to root to ensure no coverage gaps
                return [self.base_dir]
        
        return optimal_placements
    
    def _generate_all_candidates(self, matching_directories: Set[Path], instruction: Instruction) -> List[PlacementCandidate]:
        """Generate all placement candidates with optimization scores.
        
        This includes both matching directories AND their common ancestors to ensure
        the mandatory coverage constraint can be satisfied.
        """
        candidates = []
        pattern = instruction.apply_to
        
        # Collect all potential placement directories:
        # 1. The matching directories themselves
        # 2. Their common ancestors (for coverage guarantee)
        potential_directories = set(matching_directories)
        
        # Add common ancestor directories to ensure coverage options exist
        if len(matching_directories) > 1:
            # Find common ancestors that could provide coverage
            common_ancestor = self._find_minimal_coverage_placement(matching_directories)
            if common_ancestor:
                potential_directories.add(common_ancestor)
            
            # Also add any intermediate directories in the inheritance chains
            for directory in matching_directories:
                chain = self._get_inheritance_chain(directory)
                # Add intermediate directories that could provide coverage
                for intermediate in chain:
                    if intermediate != directory and intermediate in self._directory_cache:
                        potential_directories.add(intermediate)
        
        # Generate candidates for all potential directories
        for directory in sorted(potential_directories):
            if directory not in self._directory_cache:
                continue
                
            analysis = self._directory_cache[directory]
            
            # Calculate the three optimization objectives
            coverage_efficiency = self._calculate_coverage_efficiency(directory, pattern)
            pollution_score = self._calculate_pollution_minimization(directory, pattern)
            maintenance_locality = self._calculate_maintenance_locality(directory, pattern)
            
            # Apply depth penalty for excessive nesting
            depth_penalty = max(0, (analysis.depth - 3) * self.DEPTH_PENALTY_FACTOR)
            
            # Calculate total objective function score
            total_score = (
                coverage_efficiency * self.COVERAGE_EFFICIENCY_WEIGHT +
                (1.0 - pollution_score) * self.POLLUTION_MINIMIZATION_WEIGHT +
                maintenance_locality * self.MAINTENANCE_LOCALITY_WEIGHT -
                depth_penalty
            )
            
            candidate = PlacementCandidate(
                instruction=instruction,
                directory=directory,
                direct_relevance=coverage_efficiency,  # Legacy field
                inheritance_pollution=pollution_score,  # Legacy field
                depth_specificity=analysis.depth * 0.1,  # Legacy field
                total_score=0.0  # Temporary value, will be overwritten
            )
            
            # Add new optimization fields
            candidate.coverage_efficiency = coverage_efficiency
            candidate.pollution_score = pollution_score
            candidate.maintenance_locality = maintenance_locality
            
            # Set the mathematical optimization score (after __post_init__ has run)
            candidate.total_score = total_score
            
            candidates.append(candidate)
        
        return candidates
    
    def _find_minimal_coverage_placement(self, matching_directories: Set[Path]) -> Optional[Path]:
        """Find the highest directory that can provide hierarchical coverage for all matching directories.
        
        Args:
            matching_directories: Directories that contain files matching the pattern
            
        Returns:
            Path to the minimal covering directory, or None if no single placement works
        """
        if not matching_directories:
            return None
            
        # Convert to relative paths for easier analysis
        relative_dirs = [d.relative_to(self.base_dir) for d in matching_directories]
        
        # Find the lowest common ancestor that covers all directories
        if len(relative_dirs) == 1:
            # Single directory - we can place instruction in that directory or any parent
            return list(matching_directories)[0]
        
        # Find common path prefix for all directories
        common_parts = []
        min_depth = min(len(d.parts) for d in relative_dirs)
        
        for i in range(min_depth):
            parts_at_level = [d.parts[i] for d in relative_dirs]
            if len(set(parts_at_level)) == 1:
                # All directories share this path component
                common_parts.append(parts_at_level[0])
            else:
                break
        
        if common_parts:
            # Found common ancestor
            common_ancestor = self.base_dir / Path(*common_parts)
            return common_ancestor
        else:
            # No common ancestor beyond root - place at root
            return self.base_dir
    
    def _calculate_hierarchical_coverage(self, placements: List[Path], target_directories: Set[Path]) -> Set[Path]:
        """Calculate which target directories are covered by the given placements through hierarchical inheritance.
        
        Args:
            placements: List of directories where AGENTS.md files will be placed
            target_directories: Directories that need to be covered
            
        Returns:
            Set of target directories that are covered by the placements
        """
        covered = set()
        
        for target in target_directories:
            for placement in placements:
                if self._is_hierarchically_covered(target, placement):
                    covered.add(target)
                    break
        
        return covered
    
    def _is_hierarchically_covered(self, target_dir: Path, placement_dir: Path) -> bool:
        """Check if target_dir can inherit instructions from placement_dir through hierarchy.
        
        This is true if placement_dir is target_dir itself or any parent of target_dir.
        """
        try:
            # Check if target is the same as placement or is a subdirectory of placement
            target_dir.relative_to(placement_dir)
            return True
        except ValueError:
            # target_dir is not under placement_dir
            return False
    
    def _calculate_coverage_efficiency(self, directory: Path, pattern: str) -> float:
        """Calculate how well placement covers actual usage."""
        analysis = self._directory_cache[directory]
        return analysis.get_relevance_score(pattern)
    
    def _calculate_pollution_minimization(self, directory: Path, pattern: str) -> float:
        """Calculate pollution score (higher = more pollution)."""
        return self._calculate_inheritance_pollution(directory, pattern)
    
    def _calculate_maintenance_locality(self, directory: Path, pattern: str) -> float:
        """Calculate maintenance locality score."""
        # Simple heuristic: prefer directories with more related files
        analysis = self._directory_cache[directory]
        pattern_matches = analysis.pattern_matches.get(pattern, 0)
        
        if analysis.total_files == 0:
            return 0.0
        
        return min(1.0, pattern_matches / analysis.total_files)
    
    def _select_clean_separation_placements(
        self, 
        candidates: List[PlacementCandidate], 
        pattern: str
    ) -> List[Path]:
        """Select placements that provide clean separation of concerns.
        
        Args:
            candidates (List[PlacementCandidate]): Sorted placement candidates.
            pattern (str): Instruction pattern.
        
        Returns:
            List[Path]: List of directories for clean separation.
        """
        # Look for distinct clusters of files
        clusters = []
        
        for candidate in candidates:
            # Check if this directory is isolated (not a parent/child of others)
            is_isolated = True
            
            for other in candidates:
                if candidate.directory == other.directory:
                    continue
                
                if (self._is_child_directory(candidate.directory, other.directory) or
                    self._is_child_directory(other.directory, candidate.directory)):
                    is_isolated = False
                    break
            
            if is_isolated and candidate.direct_relevance >= 0.1:  # Use fixed threshold
                clusters.append(candidate.directory)
        
        # If we found clean clusters, use them
        if len(clusters) > 1:
            return clusters
        
        # Otherwise, return single best placement
        return []
    
    def _get_inheritance_chain(self, working_directory: Path) -> List[Path]:
        """Get inheritance chain from working directory to root.
        
        Args:
            working_directory (Path): Starting directory.
        
        Returns:
            List[Path]: Inheritance chain (most specific to root).
        """
        chain = []
        # Resolve the starting directory to ensure consistent path comparison
        try:
            current = working_directory.resolve()
        except (OSError, ValueError):
            current = working_directory.absolute()
            
        seen_paths = set()  # Track visited paths to prevent infinite loops
        
        # Build chain from working directory up to (and including) base_dir
        while current not in seen_paths:
            seen_paths.add(current)
            chain.append(current)
            
            # Stop at base_dir
            if current == self.base_dir:
                break
                
            # Stop if we can't go higher or hit filesystem root
            try:
                parent = current.parent
                if parent == current:  # We've hit filesystem root
                    break
                current = parent
            except (OSError, ValueError):
                break
        
        return chain
    
    def _is_child_directory(self, child: Path, parent: Path) -> bool:
        """Check if child is a subdirectory of parent.
        
        Args:
            child (Path): Potential child directory.
            parent (Path): Potential parent directory.
        
        Returns:
            bool: True if child is subdirectory of parent.
        """
        try:
            child.relative_to(parent)
            return child != parent
        except ValueError:
            return False
    
    def _is_instruction_relevant(self, instruction: Instruction, working_directory: Path) -> bool:
        """Check if instruction is relevant for the working directory.
        
        Args:
            instruction (Instruction): Instruction to check.
            working_directory (Path): Directory where agent is working.
        
        Returns:
            bool: True if instruction is relevant.
        """
        if not instruction.apply_to:
            return True  # Global instructions are always relevant
        
        pattern = instruction.apply_to
        
        # Resolve working directory to handle path inconsistencies
        try:
            resolved_working_dir = working_directory.resolve()
        except (OSError, ValueError):
            resolved_working_dir = working_directory.absolute()
        
        # Check if working directory has files matching the pattern
        analysis = self._directory_cache.get(resolved_working_dir)
        if not analysis:
            return False
        
        # If pattern already analyzed, use cached result
        if pattern in analysis.pattern_matches:
            return analysis.pattern_matches[pattern] > 0
        
        # Otherwise, analyze this specific directory for the pattern
        # Only check direct files in this directory (not subdirectories for simplicity)
        matching_files = 0
        
        try:
            for file in os.listdir(resolved_working_dir):
                if file.startswith('.'):
                    continue
                    
                file_path = resolved_working_dir / file
                if file_path.is_file():
                    if self._file_matches_pattern(file_path, pattern):
                        matching_files += 1
        except (OSError, PermissionError):
            # Handle case where directory doesn't exist or can't be read
            pass
        
        # Cache the result
        analysis.pattern_matches[pattern] = matching_files
        
        return matching_files > 0
    
    # Debug print methods removed - replaced by structured data collection
    # for professional output formatting via CompilationResults