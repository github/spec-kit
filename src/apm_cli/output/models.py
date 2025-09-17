"""Data models for compilation output and results."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
from enum import Enum

from ..primitives.models import Instruction


class PlacementStrategy(Enum):
    """Placement strategy types for optimization decisions."""
    SINGLE_POINT = "Single Point"
    SELECTIVE_MULTI = "Selective Multi" 
    DISTRIBUTED = "Distributed"


@dataclass
class ProjectAnalysis:
    """Analysis of the project structure and file distribution."""
    directories_scanned: int
    files_analyzed: int
    file_types_detected: Set[str]
    instruction_patterns_detected: int
    max_depth: int
    constitution_detected: bool = False
    constitution_path: Optional[str] = None
    
    def get_file_types_summary(self) -> str:
        """Get a concise summary of detected file types."""
        if not self.file_types_detected:
            return "none"
        
        # Remove leading dots and sort
        types = sorted([t.lstrip('.') for t in self.file_types_detected if t])
        if len(types) <= 3:
            return ', '.join(types)
        else:
            return f"{', '.join(types[:3])} and {len(types) - 3} more"


@dataclass 
class OptimizationDecision:
    """Details about a specific optimization decision for an instruction."""
    instruction: Instruction
    pattern: str
    matching_directories: int
    total_directories: int
    distribution_score: float
    strategy: PlacementStrategy
    placement_directories: List[Path]
    reasoning: str
    relevance_score: float = 0.0  # Coverage efficiency for primary placement directory
    
    @property
    def distribution_ratio(self) -> float:
        """Get the distribution ratio (matching/total)."""
        return self.matching_directories / self.total_directories if self.total_directories > 0 else 0.0


@dataclass
class PlacementSummary:
    """Summary of a single AGENTS.md file placement."""
    path: Path
    instruction_count: int
    source_count: int
    sources: List[str] = field(default_factory=list)
    
    def get_relative_path(self, base_dir: Path) -> Path:
        """Get path relative to base directory."""
        try:
            rel_path = self.path.relative_to(base_dir)
            return Path('.') if rel_path == Path('.') else rel_path
        except ValueError:
            return self.path


@dataclass
class OptimizationStats:
    """Performance and efficiency statistics from optimization."""
    average_context_efficiency: float
    pollution_improvement: Optional[float] = None
    baseline_efficiency: Optional[float] = None  
    placement_accuracy: Optional[float] = None
    generation_time_ms: Optional[int] = None
    total_agents_files: int = 0
    directories_analyzed: int = 0
    
    @property
    def efficiency_improvement(self) -> Optional[float]:
        """Calculate efficiency improvement percentage."""
        if self.baseline_efficiency is not None:
            return ((self.average_context_efficiency - self.baseline_efficiency) 
                   / self.baseline_efficiency * 100)
        return None
    
    @property
    def efficiency_percentage(self) -> float:
        """Get efficiency as percentage."""
        return self.average_context_efficiency * 100


@dataclass
class CompilationResults:
    """Complete results from compilation process."""
    project_analysis: ProjectAnalysis
    optimization_decisions: List[OptimizationDecision]
    placement_summaries: List[PlacementSummary]
    optimization_stats: OptimizationStats
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    is_dry_run: bool = False
    
    @property
    def total_instructions(self) -> int:
        """Get total number of instructions processed."""
        return sum(summary.instruction_count for summary in self.placement_summaries)
    
    @property
    def has_issues(self) -> bool:
        """Check if there are any warnings or errors."""
        return len(self.warnings) > 0 or len(self.errors) > 0