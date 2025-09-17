"""Professional CLI output formatters for APM compilation."""

import time
from pathlib import Path
from typing import List, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.tree import Tree
    from rich.text import Text
    from rich.panel import Panel
    from rich import box
    from io import StringIO
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .models import CompilationResults, OptimizationDecision, PlacementStrategy


class CompilationFormatter:
    """Professional formatter for compilation output with fallback for no-rich environments."""
    
    def __init__(self, use_color: bool = True):
        """Initialize formatter.
        
        Args:
            use_color: Whether to use colors and rich formatting.
        """
        self.use_color = use_color and RICH_AVAILABLE
        self.console = Console() if self.use_color else None
    
    def format_default(self, results: CompilationResults) -> str:
        """Format default compilation output.
        
        Args:
            results: Compilation results to format.
            
        Returns:
            Formatted output string.
        """
        lines = []
        
        # Phase 1: Project Discovery
        lines.extend(self._format_project_discovery(results.project_analysis))
        lines.append("")
        
        # Phase 2: Optimization Progress
        lines.extend(self._format_optimization_progress(results.optimization_decisions, results.project_analysis))
        lines.append("")
        
        # Phase 3: Results Summary
        lines.extend(self._format_results_summary(results))
        
        # Issues (warnings/errors)
        if results.has_issues:
            lines.append("")
            lines.extend(self._format_issues(results.warnings, results.errors))
        
        return "\n".join(lines)
    
    def format_verbose(self, results: CompilationResults) -> str:
        """Format verbose compilation output with mathematical details.
        
        Args:
            results: Compilation results to format.
            
        Returns:
            Formatted verbose output string.
        """
        lines = []
        
        # Phase 1: Project Discovery
        lines.extend(self._format_project_discovery(results.project_analysis))
        lines.append("")
        
        # Phase 2: Optimization Progress
        lines.extend(self._format_optimization_progress(results.optimization_decisions, results.project_analysis))
        lines.append("")
        
        # Phase 3: Mathematical Analysis Section (verbose only)
        lines.extend(self._format_mathematical_analysis(results.optimization_decisions))
        lines.append("")
        
        # Phase 4: Coverage vs. Efficiency Explanation (verbose only)
        lines.extend(self._format_coverage_explanation(results.optimization_stats))
        lines.append("")
        
        # Phase 5: Detailed Performance Metrics (verbose only)
        lines.extend(self._format_detailed_metrics(results.optimization_stats))
        lines.append("")
        
        # Phase 6: Final Summary (Generated X files + placement distribution)
        lines.extend(self._format_final_summary(results))
        
        # Issues (warnings/errors)
        if results.has_issues:
            lines.append("")
            lines.extend(self._format_issues(results.warnings, results.errors))
        
        return "\n".join(lines)
    
    def _format_final_summary(self, results: CompilationResults) -> List[str]:
        """Format final summary for verbose mode: Generated files + placement distribution."""
        lines = []
        
        # Main result
        file_count = len(results.placement_summaries)
        summary_line = f"Generated {file_count} AGENTS.md file{'s' if file_count != 1 else ''}"
        
        if results.is_dry_run:
            summary_line = f"[DRY RUN] Would generate {file_count} AGENTS.md file{'s' if file_count != 1 else ''}"
        
        if self.use_color:
            color = "yellow" if results.is_dry_run else "green"
            lines.append(self._styled(summary_line, f"{color} bold"))
        else:
            lines.append(summary_line)
        
        # Efficiency metrics with improved formatting
        stats = results.optimization_stats
        efficiency_pct = f"{stats.efficiency_percentage:.1f}%"
        
        # Build metrics with baselines and improvements when available
        metrics_lines = [
            f"┌─ Context efficiency:    {efficiency_pct}"
        ]
        
        if stats.efficiency_improvement is not None:
            improvement = f"(baseline: {stats.baseline_efficiency * 100:.1f}%, improvement: +{stats.efficiency_improvement:.0f}%)" if stats.efficiency_improvement > 0 else f"(baseline: {stats.baseline_efficiency * 100:.1f}%, change: {stats.efficiency_improvement:.0f}%)"
            metrics_lines[0] += f" {improvement}"
        
        if stats.pollution_improvement is not None:
            pollution_pct = f"{(1.0 - stats.pollution_improvement) * 100:.1f}%"
            improvement_pct = f"-{stats.pollution_improvement * 100:.0f}%" if stats.pollution_improvement > 0 else f"+{abs(stats.pollution_improvement) * 100:.0f}%"
            metrics_lines.append(f"├─ Average pollution:     {pollution_pct} (improvement: {improvement_pct})")
        
        if stats.placement_accuracy is not None:
            accuracy_pct = f"{stats.placement_accuracy * 100:.1f}%"
            metrics_lines.append(f"├─ Placement accuracy:    {accuracy_pct} (mathematical optimum)")
        
        if stats.generation_time_ms is not None:
            metrics_lines.append(f"└─ Generation time:       {stats.generation_time_ms}ms")
        else:
            # Change last ├─ to └─
            if len(metrics_lines) > 1:
                metrics_lines[-1] = metrics_lines[-1].replace("├─", "└─")
        
        for line in metrics_lines:
            if self.use_color:
                lines.append(self._styled(line, "dim"))
            else:
                lines.append(line)
        
        # Add placement distribution summary
        lines.append("")
        if self.use_color:
            lines.append(self._styled("Placement Distribution", "cyan bold"))
        else:
            lines.append("Placement Distribution")
        
        # Show distribution of AGENTS.md files
        for summary in results.placement_summaries:
            rel_path = str(summary.get_relative_path(Path.cwd()))
            content_text = self._get_placement_description(summary)
            source_text = f"{summary.source_count} source{'s' if summary.source_count != 1 else ''}"
            
            # Use proper tree formatting
            prefix = "├─" if summary != results.placement_summaries[-1] else "└─"
            line = f"{prefix} {rel_path:<30} {content_text} from {source_text}"
            
            if self.use_color:
                lines.append(self._styled(line, "dim"))
            else:
                lines.append(line)
        
        return lines

    def format_dry_run(self, results: CompilationResults) -> str:
        """Format dry run output.
        
        Args:
            results: Compilation results to format.
            
        Returns:
            Formatted dry run output string.
        """
        lines = []
        
        # Standard analysis
        lines.extend(self._format_project_discovery(results.project_analysis))
        lines.append("")
        lines.extend(self._format_optimization_progress(results.optimization_decisions, results.project_analysis))
        lines.append("")
        
        # Dry run specific output
        lines.extend(self._format_dry_run_summary(results))
        
        # Issues (warnings/errors) - important for dry run too!
        if results.has_issues:
            lines.append("")
            lines.extend(self._format_issues(results.warnings, results.errors))
        
        return "\n".join(lines)
    
    def _format_project_discovery(self, analysis) -> List[str]:
        """Format project discovery phase output."""
        lines = []
        
        if self.use_color:
            lines.append(self._styled("Analyzing project structure...", "cyan bold"))
        else:
            lines.append("Analyzing project structure...")
        
        # Constitution detection (first priority)
        if analysis.constitution_detected:
            constitution_line = f"├─ Constitution detected: {analysis.constitution_path}"
            if self.use_color:
                lines.append(self._styled(constitution_line, "dim"))
            else:
                lines.append(constitution_line)
        
        # Structure tree with more detailed information
        file_types_summary = analysis.get_file_types_summary() if hasattr(analysis, 'get_file_types_summary') else "various"
        tree_lines = [
            f"├─ {analysis.directories_scanned} directories scanned (max depth: {analysis.max_depth})",
            f"├─ {analysis.files_analyzed} files analyzed across {len(analysis.file_types_detected)} file types ({file_types_summary})",
            f"└─ {analysis.instruction_patterns_detected} instruction patterns detected"
        ]
        
        for line in tree_lines:
            if self.use_color:
                lines.append(self._styled(line, "dim"))
            else:
                lines.append(line)
        
        return lines
    
    def _format_optimization_progress(self, decisions: List[OptimizationDecision], analysis=None) -> List[str]:
        """Format optimization progress display using Rich table for better readability."""
        lines = []
        
        if self.use_color:
            lines.append(self._styled("Optimizing placements...", "cyan bold"))
        else:
            lines.append("Optimizing placements...")
        
        if self.use_color and RICH_AVAILABLE:
            # Create a Rich table for professional display
            table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE_HEAD)
            table.add_column("Pattern", style="white", width=25)
            table.add_column("Source", style="yellow", width=20)
            table.add_column("Coverage", style="dim", width=10)
            table.add_column("Placement", style="green", width=25)
            table.add_column("Metrics", style="dim", width=20)
            
            # Add constitution row first if detected
            if analysis and analysis.constitution_detected:
                table.add_row(
                    "**",
                    "constitution.md",
                    "ALL",
                    "./AGENTS.md",
                    "rel: 100%"
                )
            
            for decision in decisions:
                pattern_display = decision.pattern if decision.pattern else "(global)"
                
                # Extract source information from the instruction
                source_display = "unknown"
                if decision.instruction and hasattr(decision.instruction, 'file_path'):
                    try:
                        # Get relative path from base directory if possible
                        rel_path = decision.instruction.file_path.name  # Just filename for brevity
                        source_display = rel_path
                    except:
                        source_display = str(decision.instruction.file_path)[-20:]  # Last 20 chars
                
                ratio_display = f"{decision.matching_directories}/{decision.total_directories}"
                
                if len(decision.placement_directories) == 1:
                    placement = self._get_relative_display_path(decision.placement_directories[0])
                    # Add efficiency details for single placement
                    relevance = getattr(decision, 'relevance_score', 0.0) if hasattr(decision, 'relevance_score') else 1.0
                    pollution = getattr(decision, 'pollution_score', 0.0) if hasattr(decision, 'pollution_score') else 0.0
                    metrics = f"rel: {relevance*100:.0f}%"
                else:
                    placement_count = len(decision.placement_directories)
                    placement = f"{placement_count} locations"
                    metrics = "distributed"
                
                # Color code the placement by strategy
                placement_style = self._get_strategy_color(decision.strategy)
                placement_text = Text(placement, style=placement_style)
                
                table.add_row(pattern_display, source_display, ratio_display, placement_text, metrics)
            
            # Render table to lines
            if self.console:
                with self.console.capture() as capture:
                    self.console.print(table)
                table_output = capture.get()
                if table_output.strip():
                    lines.extend(table_output.split('\n'))
        else:
            # Fallback to simplified text display for non-Rich environments
            # Add constitution first if detected
            if analysis and analysis.constitution_detected:
                lines.append("**                        constitution.md     ALL        → ./AGENTS.md                (rel: 100%)")
            
            for decision in decisions:
                pattern_display = decision.pattern if decision.pattern else "(global)"
                
                # Extract source information
                source_display = "unknown"
                if decision.instruction and hasattr(decision.instruction, 'file_path'):
                    try:
                        source_display = decision.instruction.file_path.name
                    except:
                        source_display = "unknown"
                
                ratio_display = f"{decision.matching_directories}/{decision.total_directories} dirs"
                
                if len(decision.placement_directories) == 1:
                    placement = self._get_relative_display_path(decision.placement_directories[0])
                    relevance = getattr(decision, 'relevance_score', 0.0) if hasattr(decision, 'relevance_score') else 1.0
                    pollution = getattr(decision, 'pollution_score', 0.0) if hasattr(decision, 'pollution_score') else 0.0
                    line = f"{pattern_display:<25} {source_display:<15} {ratio_display:<10} → {placement:<25} (rel: {relevance*100:.0f}%)"
                else:
                    placement_count = len(decision.placement_directories)
                    line = f"{pattern_display:<25} {source_display:<15} {ratio_display:<10} → {placement_count} locations"
                
                lines.append(line)
        
        return lines
    
    def _format_results_summary(self, results: CompilationResults) -> List[str]:
        """Format final results summary."""
        lines = []
        
        # Main result
        file_count = len(results.placement_summaries)
        summary_line = f"Generated {file_count} AGENTS.md file{'s' if file_count != 1 else ''}"
        
        if results.is_dry_run:
            summary_line = f"[DRY RUN] Would generate {file_count} AGENTS.md file{'s' if file_count != 1 else ''}"
        
        if self.use_color:
            color = "yellow" if results.is_dry_run else "green"
            lines.append(self._styled(summary_line, f"{color} bold"))
        else:
            lines.append(summary_line)
        
        # Efficiency metrics with improved formatting
        stats = results.optimization_stats
        efficiency_pct = f"{stats.efficiency_percentage:.1f}%"
        
        # Build metrics with baselines and improvements when available
        metrics_lines = [
            f"┌─ Context efficiency:    {efficiency_pct}"
        ]
        
        if stats.efficiency_improvement is not None:
            improvement = f"(baseline: {stats.baseline_efficiency * 100:.1f}%, improvement: +{stats.efficiency_improvement:.0f}%)" if stats.efficiency_improvement > 0 else f"(baseline: {stats.baseline_efficiency * 100:.1f}%, change: {stats.efficiency_improvement:.0f}%)"
            metrics_lines[0] += f" {improvement}"
        
        if stats.pollution_improvement is not None:
            pollution_pct = f"{(1.0 - stats.pollution_improvement) * 100:.1f}%"
            improvement_pct = f"-{stats.pollution_improvement * 100:.0f}%" if stats.pollution_improvement > 0 else f"+{abs(stats.pollution_improvement) * 100:.0f}%"
            metrics_lines.append(f"├─ Average pollution:     {pollution_pct} (improvement: {improvement_pct})")
        
        if stats.placement_accuracy is not None:
            accuracy_pct = f"{stats.placement_accuracy * 100:.1f}%"
            metrics_lines.append(f"├─ Placement accuracy:    {accuracy_pct} (mathematical optimum)")
        
        if stats.generation_time_ms is not None:
            metrics_lines.append(f"└─ Generation time:       {stats.generation_time_ms}ms")
        else:
            # Change last ├─ to └─
            if len(metrics_lines) > 1:
                metrics_lines[-1] = metrics_lines[-1].replace("├─", "└─")
        
        for line in metrics_lines:
            if self.use_color:
                lines.append(self._styled(line, "dim"))
            else:
                lines.append(line)
        
        # Add placement distribution summary
        lines.append("")
        if self.use_color:
            lines.append(self._styled("Placement Distribution", "cyan bold"))
        else:
            lines.append("Placement Distribution")
        
        # Show distribution of AGENTS.md files
        for summary in results.placement_summaries:
            rel_path = str(summary.get_relative_path(Path.cwd()))
            content_text = self._get_placement_description(summary)
            source_text = f"{summary.source_count} source{'s' if summary.source_count != 1 else ''}"
            
            # Use proper tree formatting
            prefix = "├─" if summary != results.placement_summaries[-1] else "└─"
            line = f"{prefix} {rel_path:<30} {content_text} from {source_text}"
            
            if self.use_color:
                lines.append(self._styled(line, "dim"))
            else:
                lines.append(line)
        
        return lines
    
    def _format_dry_run_summary(self, results: CompilationResults) -> List[str]:
        """Format dry run specific summary."""
        lines = []
        
        if self.use_color:
            lines.append(self._styled("[DRY RUN] File generation preview:", "yellow bold"))
        else:
            lines.append("[DRY RUN] File generation preview:")
        
        # List files that would be generated
        for summary in results.placement_summaries:
            rel_path = str(summary.get_relative_path(Path.cwd()))
            instruction_text = f"{summary.instruction_count} instruction{'s' if summary.instruction_count != 1 else ''}"
            source_text = f"{summary.source_count} source{'s' if summary.source_count != 1 else ''}"
            
            line = f"├─ {rel_path:<30} {instruction_text}, {source_text}"
            
            if self.use_color:
                lines.append(self._styled(line, "dim"))
            else:
                lines.append(line)
        
        # Change last ├─ to └─
        if lines and len(lines) > 1:
            lines[-1] = lines[-1].replace("├─", "└─")
        
        lines.append("")
        
        # Call to action
        if self.use_color:
            lines.append(self._styled("[DRY RUN] No files written. Run 'apm compile' to apply changes.", "yellow"))
        else:
            lines.append("[DRY RUN] No files written. Run 'apm compile' to apply changes.")
        
        return lines
    
    def _format_mathematical_analysis(self, decisions: List[OptimizationDecision]) -> List[str]:
        """Format mathematical analysis for verbose mode with coverage-first principles."""
        lines = []
        
        if self.use_color:
            lines.append(self._styled("Mathematical Optimization Analysis", "cyan bold"))
        else:
            lines.append("Mathematical Optimization Analysis")
        
        lines.append("")
        
        if self.use_color and RICH_AVAILABLE:
            # Coverage-First Strategy Table
            strategy_table = Table(title="Three-Tier Coverage-First Strategy", show_header=True, header_style="bold cyan", box=box.SIMPLE_HEAD)
            strategy_table.add_column("Pattern", style="white", width=25)
            strategy_table.add_column("Source", style="yellow", width=15)
            strategy_table.add_column("Distribution", style="yellow", width=12)
            strategy_table.add_column("Strategy", style="green", width=15)
            strategy_table.add_column("Coverage Guarantee", style="blue", width=20)
            
            for decision in decisions:
                pattern = decision.pattern if decision.pattern else "(global)"
                
                # Extract source information
                source_display = "unknown"
                if decision.instruction and hasattr(decision.instruction, 'file_path'):
                    try:
                        source_display = decision.instruction.file_path.name
                    except:
                        source_display = "unknown"
                
                # Distribution score with threshold classification
                score = decision.distribution_score
                if score < 0.3:
                    dist_display = f"{score:.3f} (Low)"
                    strategy_name = "Single Point"
                    coverage_status = "✅ Perfect"
                elif score > 0.7:
                    dist_display = f"{score:.3f} (High)"
                    strategy_name = "Distributed"
                    coverage_status = "✅ Universal"
                else:
                    dist_display = f"{score:.3f} (Medium)"
                    strategy_name = "Selective Multi"
                    # Check if root placement was used (indicates coverage fallback)
                    if any("." == str(p) or p.name == "" for p in decision.placement_directories):
                        coverage_status = "⚠️  Root Fallback"
                    else:
                        coverage_status = "✅ Verified"
                
                strategy_table.add_row(pattern, source_display, dist_display, strategy_name, coverage_status)
            
            # Render strategy table
            if self.console:
                with self.console.capture() as capture:
                    self.console.print(strategy_table)
                table_output = capture.get()
                if table_output.strip():
                    lines.extend(table_output.split('\n'))
            
            lines.append("")
            
            # Hierarchical Coverage Analysis Table
            coverage_table = Table(title="Hierarchical Coverage Analysis", show_header=True, header_style="bold cyan", box=box.SIMPLE_HEAD)
            coverage_table.add_column("Pattern", style="white", width=25)
            coverage_table.add_column("Matching Files", style="yellow", width=15)
            coverage_table.add_column("Placement", style="green", width=20)
            coverage_table.add_column("Coverage Result", style="blue", width=25)
            
            for decision in decisions:
                pattern = decision.pattern if decision.pattern else "(global)"
                matching_files = f"{decision.matching_directories} dirs"
                
                if len(decision.placement_directories) == 1:
                    placement = self._get_relative_display_path(decision.placement_directories[0])
                    
                    # Analyze coverage outcome
                    if str(decision.placement_directories[0]).endswith('.'):
                        coverage_result = "Root → All files inherit"
                    elif decision.distribution_score < 0.3:
                        coverage_result = "Local → Perfect efficiency"
                    else:
                        coverage_result = "Selective → Coverage verified"
                else:
                    placement = f"{len(decision.placement_directories)} locations"
                    coverage_result = "Multi-point → Full coverage"
                
                coverage_table.add_row(pattern, matching_files, placement, coverage_result)
            
            # Render coverage table
            if self.console:
                with self.console.capture() as capture:
                    self.console.print(coverage_table)
                table_output = capture.get()
                if table_output.strip():
                    lines.extend(table_output.split('\n'))
            
            lines.append("")
            
            # Updated Mathematical Foundation Panel
            foundation_text = """Objective: minimize Σ(context_pollution × directory_weight)
Constraints: ∀file_matching_pattern → can_inherit_instruction
Variables: placement_matrix ∈ {0,1}
Algorithm: Three-tier strategy with hierarchical coverage verification

Coverage Guarantee: Every file can access applicable instructions through
hierarchical inheritance. Coverage takes priority over efficiency."""
            
            if self.console:
                from rich.panel import Panel
                try:
                    panel = Panel(foundation_text, title="Coverage-Constrained Optimization", border_style="cyan")
                    with self.console.capture() as capture:
                        self.console.print(panel)
                    panel_output = capture.get()
                    if panel_output.strip():
                        lines.extend(panel_output.split('\n'))
                except:
                    # Fallback to simple text
                    lines.append("Coverage-Constrained Optimization:")
                    for line in foundation_text.split('\n'):
                        lines.append(f"  {line}")
            
        else:
            # Fallback for non-Rich environments
            lines.append("Coverage-First Strategy Analysis:")
            for decision in decisions:
                pattern = decision.pattern if decision.pattern else "(global)"
                score = f"{decision.distribution_score:.3f}"
                strategy = decision.strategy.value
                coverage = "✅ Verified" if decision.distribution_score < 0.7 else "⚠️ Root Fallback"
                lines.append(f"  {pattern:<30} {score:<8} {strategy:<15} {coverage}")
            
            lines.append("")
            lines.append("Mathematical Foundation:")
            lines.append("  Objective: minimize Σ(context_pollution × directory_weight)")
            lines.append("  Constraints: ∀file_matching_pattern → can_inherit_instruction")
            lines.append("  Algorithm: Three-tier strategy with coverage verification")
            lines.append("  Principle: Coverage guarantee takes priority over efficiency")
        
        return lines
    
    def _format_detailed_metrics(self, stats) -> List[str]:
        """Format detailed performance metrics table with interpretations."""
        lines = []
        
        if self.use_color:
            lines.append(self._styled("Performance Metrics", "cyan bold"))
        else:
            lines.append("Performance Metrics")
        
        # Create metrics table
        if self.use_color and RICH_AVAILABLE:
            table = Table(box=box.SIMPLE)
            table.add_column("Metric", style="white", width=20)
            table.add_column("Value", style="white", width=12)
            table.add_column("Assessment", style="blue", width=35)
            
            # Context Efficiency with coverage-first interpretation
            efficiency = stats.efficiency_percentage
            if efficiency >= 80:
                assessment = "Excellent - perfect pattern locality"
                assessment_color = "bright_green"
                value_color = "bright_green"
            elif efficiency >= 60:
                assessment = "Good - well-optimized with minimal coverage conflicts"
                assessment_color = "green"
                value_color = "green"
            elif efficiency >= 40:
                assessment = "Fair - moderate coverage-driven pollution"
                assessment_color = "yellow"
                value_color = "yellow"
            elif efficiency >= 20:
                assessment = "Poor - significant coverage constraints"
                assessment_color = "orange1"
                value_color = "orange1"
            else:
                assessment = "Very Poor - may be mathematically optimal given coverage"
                assessment_color = "red"
                value_color = "red"
            
            table.add_row(
                "Context Efficiency",
                Text(f"{efficiency:.1f}%", style=value_color),
                Text(assessment, style=assessment_color)
            )
            
            # Calculate pollution level with coverage-aware interpretation
            pollution_level = 100 - efficiency
            if pollution_level <= 20:
                pollution_assessment = "Excellent - perfect pattern locality"
                pollution_color = "bright_green"
            elif pollution_level <= 40:
                pollution_assessment = "Good - minimal coverage conflicts"
                pollution_color = "green"
            elif pollution_level <= 60:
                pollution_assessment = "Fair - acceptable coverage-driven pollution"
                pollution_color = "yellow"
            elif pollution_level <= 80:
                pollution_assessment = "Poor - high coverage constraints"
                pollution_color = "orange1"
            else:
                pollution_assessment = "Very Poor - but may guarantee coverage"
                pollution_color = "red"
                
            table.add_row(
                "Pollution Level", 
                Text(f"{pollution_level:.1f}%", style=pollution_color),
                Text(pollution_assessment, style=pollution_color)
            )
            
            if stats.placement_accuracy:
                accuracy = stats.placement_accuracy * 100
                if accuracy >= 95:
                    accuracy_assessment = "Excellent - mathematically optimal"
                    accuracy_color = "bright_green"
                elif accuracy >= 85:
                    accuracy_assessment = "Good - near optimal"
                    accuracy_color = "green"
                elif accuracy >= 70:
                    accuracy_assessment = "Fair - reasonably placed"
                    accuracy_color = "yellow"
                else:
                    accuracy_assessment = "Poor - suboptimal placement"
                    accuracy_color = "orange1"
                    
                table.add_row(
                    "Placement Accuracy",
                    Text(f"{accuracy:.1f}%", style=accuracy_color),
                    Text(accuracy_assessment, style=accuracy_color)
                )
            
            # Render table
            if self.console:
                with self.console.capture() as capture:
                    self.console.print(table)
                table_output = capture.get()
                if table_output.strip():
                    lines.extend(table_output.split('\n'))
            
            lines.append("")
            
            # Add interpretation guide
            if self.console:
                try:
                    interpretation_text = """📊 How These Metrics Are Calculated

Context Efficiency = Average across all directories of (Relevant Instructions / Total Instructions)
• For each directory, APM analyzes what instructions agents would inherit from AGENTS.md files
• Calculates ratio of instructions that apply to files in that directory vs total instructions loaded
• Takes weighted average across all project directories with files

Pollution Level = 100% - Context Efficiency (inverse relationship)
• High pollution = agents load many irrelevant instructions when working in specific directories
• Low pollution = agents see mostly relevant instructions for their current context

🎯 Interpretation Benchmarks

Context Efficiency:
• 80-100%: Excellent - Instructions perfectly targeted to usage context
• 60-80%: Good - Well-optimized with minimal wasted context  
• 40-60%: Fair - Some optimization opportunities exist
• 20-40%: Poor - Significant context pollution, consider restructuring
• 0-20%: Very Poor - High pollution, instructions poorly distributed

Pollution Level:
• 0-10%: Excellent - Agents see highly relevant instructions only
• 10-25%: Good - Low noise, mostly relevant context
• 25-50%: Fair - Moderate noise, some irrelevant instructions  
• 50%+: Poor - High noise, agents see many irrelevant instructions

💡 Example: 36.7% efficiency means agents working in specific directories see only 36.7% relevant instructions and 63.3% irrelevant context pollution."""
                    
                    panel = Panel(interpretation_text, title="Metrics Guide", border_style="dim", title_align="left")
                    with self.console.capture() as capture:
                        self.console.print(panel)
                    panel_output = capture.get()
                    if panel_output.strip():
                        lines.extend(panel_output.split('\n'))
                except:
                    # Fallback to simple text
                    lines.extend([
                        "Metrics Guide:",
                        "• Context Efficiency 80-100%: Excellent | 60-80%: Good | 40-60%: Fair | <40%: Poor",
                        "• Pollution 0-10%: Excellent | 10-25%: Good | 25-50%: Fair | >50%: Poor"
                    ])
        else:
            # Fallback for non-Rich environments
            efficiency = stats.efficiency_percentage
            pollution = 100 - efficiency
            
            if efficiency >= 80:
                efficiency_assessment = "Excellent"
            elif efficiency >= 60:
                efficiency_assessment = "Good"
            elif efficiency >= 40:
                efficiency_assessment = "Fair"
            elif efficiency >= 20:
                efficiency_assessment = "Poor"
            else:
                efficiency_assessment = "Very Poor"
                
            if pollution <= 10:
                pollution_assessment = "Excellent"
            elif pollution <= 25:
                pollution_assessment = "Good"
            elif pollution <= 50:
                pollution_assessment = "Fair"
            else:
                pollution_assessment = "Poor"
                
            lines.extend([
                f"Context Efficiency: {efficiency:.1f}% ({efficiency_assessment})",
                f"Pollution Level: {pollution:.1f}% ({pollution_assessment})",
                "Guide: 80-100% Excellent | 60-80% Good | 40-60% Fair | 20-40% Poor | <20% Very Poor"
            ])
        
        return lines
    
    def _format_issues(self, warnings: List[str], errors: List[str]) -> List[str]:
        """Format warnings and errors as professional blocks."""
        lines = []
        
        # Errors first
        for error in errors:
            if self.use_color:
                lines.append(self._styled(f"✗ Error: {error}", "red"))
            else:
                lines.append(f"✗ Error: {error}")
        
        # Then warnings - handle multi-line warnings as cohesive blocks
        for warning in warnings:
            if '\n' in warning:
                # Multi-line warning - format as a professional block
                warning_lines = warning.split('\n')
                # First line gets the warning symbol and styling
                if self.use_color:
                    lines.append(self._styled(f"⚠ Warning: {warning_lines[0]}", "yellow"))
                else:
                    lines.append(f"⚠ Warning: {warning_lines[0]}")
                
                # Subsequent lines are indented and styled consistently
                for line in warning_lines[1:]:
                    if line.strip():  # Skip empty lines
                        if self.use_color:
                            lines.append(self._styled(f"           {line}", "yellow"))
                        else:
                            lines.append(f"           {line}")
            else:
                # Single-line warning - standard format
                if self.use_color:
                    lines.append(self._styled(f"⚠ Warning: {warning}", "yellow"))
                else:
                    lines.append(f"⚠ Warning: {warning}")
        
        return lines
    
    def _get_strategy_symbol(self, strategy: PlacementStrategy) -> str:
        """Get symbol for placement strategy."""
        symbols = {
            PlacementStrategy.SINGLE_POINT: "●",
            PlacementStrategy.SELECTIVE_MULTI: "◆", 
            PlacementStrategy.DISTRIBUTED: "◇"
        }
        return symbols.get(strategy, "•")
    
    def _get_strategy_color(self, strategy: PlacementStrategy) -> str:
        """Get color for placement strategy."""
        colors = {
            PlacementStrategy.SINGLE_POINT: "green",
            PlacementStrategy.SELECTIVE_MULTI: "yellow",
            PlacementStrategy.DISTRIBUTED: "blue"
        }
        return colors.get(strategy, "white")
    
    def _get_relative_display_path(self, path: Path) -> str:
        """Get display-friendly relative path."""
        try:
            rel_path = path.relative_to(Path.cwd())
            if rel_path == Path('.'):
                return "./AGENTS.md"
            return str(rel_path / "AGENTS.md")
        except ValueError:
            return str(path / "AGENTS.md")
    
    def _format_coverage_explanation(self, stats) -> List[str]:
        """Explain the coverage vs. efficiency trade-off."""
        lines = []
        
        if self.use_color:
            lines.append(self._styled("Coverage vs. Efficiency Analysis", "cyan bold"))
        else:
            lines.append("Coverage vs. Efficiency Analysis")
        
        lines.append("")
        
        efficiency = stats.efficiency_percentage
        
        if efficiency < 30:
            lines.append("⚠️  Low Efficiency Detected:")
            lines.append("   • Coverage guarantee requires some instructions at root level")
            lines.append("   • This creates pollution for specialized directories")
            lines.append("   • Trade-off: Guaranteed coverage vs. optimal efficiency")
            lines.append("   • Alternative: Higher efficiency with coverage violations (data loss)")
            lines.append("")
            lines.append("💡 This may be mathematically optimal given coverage constraints")
        elif efficiency < 60:
            lines.append("✅ Moderate Efficiency:")
            lines.append("   • Good balance between coverage and efficiency")
            lines.append("   • Some coverage-driven pollution is acceptable")
            lines.append("   • Most patterns are well-localized")
        else:
            lines.append("🎯 High Efficiency:")
            lines.append("   • Excellent pattern locality achieved")
            lines.append("   • Minimal coverage conflicts")
            lines.append("   • Instructions are optimally placed")
        
        lines.append("")
        lines.append("📚 Why Coverage Takes Priority:")
        lines.append("   • Every file must access applicable instructions")
        lines.append("   • Hierarchical inheritance prevents data loss")
        lines.append("   • Better low efficiency than missing instructions")
        
        return lines

    def _get_placement_description(self, summary) -> str:
        """Get description of what's included in a placement summary.
        
        Args:
            summary: PlacementSummary object
            
        Returns:
            str: Description like "Constitution and 1 instruction" or "Constitution"
        """
        # Check if constitution is included
        has_constitution = any("constitution.md" in source for source in summary.sources)
        
        # Build the description based on what's included
        parts = []
        if has_constitution:
            parts.append("Constitution")
        
        if summary.instruction_count > 0:
            instruction_text = f"{summary.instruction_count} instruction{'s' if summary.instruction_count != 1 else ''}"
            parts.append(instruction_text)
        
        if parts:
            return " and ".join(parts)
        else:
            return "content"

    def _styled(self, text: str, style: str) -> str:
        """Apply styling to text with rich fallback."""
        if self.use_color and RICH_AVAILABLE:
            styled_text = Text(text)
            styled_text.style = style
            with self.console.capture() as capture:
                self.console.print(styled_text, end="")
            return capture.get()
        else:
            return text