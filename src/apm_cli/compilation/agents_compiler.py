"""Main compilation orchestration for AGENTS.md generation.

Timestamp generation removed in favor of deterministic Build ID handled after
full content assembly. This keeps repeated compiles byte-identical when source
primitives & constitution are unchanged.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
from ..primitives.models import PrimitiveCollection
from ..primitives.discovery import discover_primitives
from ..version import get_version
from .template_builder import (
    build_conditional_sections,
    generate_agents_md_template,
    TemplateData,
    find_chatmode_by_name
)
from .link_resolver import resolve_markdown_links, validate_link_targets


@dataclass
class CompilationConfig:
    """Configuration for AGENTS.md compilation."""
    output_path: str = "AGENTS.md"
    chatmode: Optional[str] = None
    resolve_links: bool = True
    dry_run: bool = False
    with_constitution: bool = True  # Phase 0 feature flag
    
    # Distributed compilation settings (Task 7)
    strategy: str = "distributed"  # "distributed" or "single-file"
    single_agents: bool = False  # Force single-file mode
    trace: bool = False  # Show source attribution and conflicts
    local_only: bool = False  # Ignore dependencies, compile only local primitives
    debug: bool = False  # Show context optimizer analysis and metrics
    min_instructions_per_file: int = 1  # Minimum instructions per AGENTS.md file (Minimal Context Principle)
    source_attribution: bool = True  # Include source file comments
    clean_orphaned: bool = False  # Remove orphaned AGENTS.md files
    
    def __post_init__(self):
        """Handle CLI flag precedence after initialization."""
        if self.single_agents:
            self.strategy = "single-file"
    
    @classmethod
    def from_apm_yml(cls, **overrides) -> 'CompilationConfig':
        """Create configuration from apm.yml with command-line overrides.
        
        Args:
            **overrides: Command-line arguments that override config file values.
            
        Returns:
            CompilationConfig: Configuration with apm.yml values and overrides applied.
        """
        config = cls()
        
        # Try to load from apm.yml
        try:
            from pathlib import Path
            import yaml
            
            if Path('apm.yml').exists():
                with open('apm.yml', 'r') as f:
                    apm_config = yaml.safe_load(f) or {}
                
                # Look for compilation section
                compilation_config = apm_config.get('compilation', {})
                
                # Apply config file values
                if 'output' in compilation_config:
                    config.output_path = compilation_config['output']
                if 'chatmode' in compilation_config:
                    config.chatmode = compilation_config['chatmode']
                if 'resolve_links' in compilation_config:
                    config.resolve_links = compilation_config['resolve_links']
                
                # Distributed compilation settings (Task 7)
                if 'strategy' in compilation_config:
                    config.strategy = compilation_config['strategy']
                if 'single_file' in compilation_config:
                    # Legacy config support - if single_file is True, override strategy
                    if compilation_config['single_file']:
                        config.strategy = "single-file"
                        config.single_agents = True
                
                # Placement settings
                placement_config = compilation_config.get('placement', {})
                if 'min_instructions_per_file' in placement_config:
                    config.min_instructions_per_file = placement_config['min_instructions_per_file']
                
                # Source attribution
                if 'source_attribution' in compilation_config:
                    config.source_attribution = compilation_config['source_attribution']
                
        except Exception:
            # If config loading fails, use defaults
            pass
        
        # Apply command-line overrides (highest priority)
        for key, value in overrides.items():
            if value is not None:  # Only override if explicitly provided
                setattr(config, key, value)
        
        # Handle CLI flag precedence
        if config.single_agents:
            config.strategy = "single-file"
        
        return config


@dataclass
class CompilationResult:
    """Result of AGENTS.md compilation."""
    success: bool
    output_path: str
    content: str
    warnings: List[str]
    errors: List[str]
    stats: Dict[str, Any]


class AgentsCompiler:
    """Main compiler for generating AGENTS.md files."""
    
    def __init__(self, base_dir: str = "."):
        """Initialize the compiler.
        
        Args:
            base_dir (str): Base directory for compilation. Defaults to current directory.
        """
        self.base_dir = Path(base_dir)
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def compile(self, config: CompilationConfig, primitives: Optional[PrimitiveCollection] = None) -> CompilationResult:
        """Compile AGENTS.md with the given configuration.
        
        Args:
            config (CompilationConfig): Compilation configuration.
            primitives (Optional[PrimitiveCollection]): Primitives to use, or None to discover.
        
        Returns:
            CompilationResult: Result of the compilation.
        """
        self.warnings.clear()
        self.errors.clear()
        
        try:
            # Use provided primitives or discover them (with dependency support)
            if primitives is None:
                if config.local_only:
                    # Use basic discovery for local-only mode
                    primitives = discover_primitives(str(self.base_dir))
                else:
                    # Use enhanced discovery with dependencies (Task 4 integration)
                    from ..primitives.discovery import discover_primitives_with_dependencies
                    primitives = discover_primitives_with_dependencies(str(self.base_dir))
            
            # Handle distributed compilation (Task 7 - new default behavior)
            if config.strategy == "distributed" and not config.single_agents:
                return self._compile_distributed(config, primitives)
            else:
                # Traditional single-file compilation (backward compatibility)
                return self._compile_single_file(config, primitives)
                
        except Exception as e:
            self.errors.append(f"Compilation failed: {str(e)}")
            return CompilationResult(
                success=False,
                output_path="",
                content="",
                warnings=self.warnings.copy(),
                errors=self.errors.copy(),
                stats={}
            )
    
    def _compile_distributed(self, config: CompilationConfig, primitives: PrimitiveCollection) -> CompilationResult:
        """Compile using distributed AGENTS.md approach (Task 7).
        
        Args:
            config (CompilationConfig): Compilation configuration.
            primitives (PrimitiveCollection): Primitives to compile.
        
        Returns:
            CompilationResult: Result of distributed compilation.
        """
        from .distributed_compiler import DistributedAgentsCompiler
        
        # Create distributed compiler
        distributed_compiler = DistributedAgentsCompiler(str(self.base_dir))
        
        # Prepare configuration for distributed compilation
        distributed_config = {
            'min_instructions_per_file': config.min_instructions_per_file,
            # max_depth removed - full project analysis
            'source_attribution': config.source_attribution,
            'debug': config.debug,
            'clean_orphaned': config.clean_orphaned,
            'dry_run': config.dry_run
        }
        
        # Compile distributed
        distributed_result = distributed_compiler.compile_distributed(primitives, distributed_config)
        
        # Display professional compilation output (always show, not just in debug)
        compilation_results = distributed_compiler.get_compilation_results_for_display(config.dry_run)
        if compilation_results:
            if config.debug or config.trace:
                # Verbose mode with mathematical analysis
                output = distributed_compiler.output_formatter.format_verbose(compilation_results)
            elif config.dry_run:
                # Dry run mode with placement preview
                output = distributed_compiler.output_formatter.format_dry_run(compilation_results)
            else:
                # Default mode with essential information
                output = distributed_compiler.output_formatter.format_default(compilation_results)
            
            # Display the professional output
            print(output)
        
        if not distributed_result.success:
            self.warnings.extend(distributed_result.warnings)
            self.errors.extend(distributed_result.errors)
            return CompilationResult(
                success=False,
                output_path="",
                content="",
                warnings=self.warnings.copy(),
                errors=self.errors.copy(),
                stats=distributed_result.stats
            )
        
        # Handle dry-run mode (preview placement without writing files)
        if config.dry_run:
            # Count files that would be written (directories that exist)
            successful_writes = 0
            for agents_path in distributed_result.content_map.keys():
                if agents_path.parent.exists():
                    successful_writes += 1
            
            # Update stats with actual files that would be written
            if distributed_result.stats:
                distributed_result.stats["agents_files_generated"] = successful_writes
            
            # Don't write files in preview mode - output already shown above
            return CompilationResult(
                success=True,
                output_path="Preview mode - no files written",
                content=self._generate_placement_summary(distributed_result),
                warnings=distributed_result.warnings,
                errors=distributed_result.errors,
                stats=distributed_result.stats
            )
        
        # Write distributed AGENTS.md files
        successful_writes = 0
        total_content_entries = len(distributed_result.content_map)
        
        for agents_path, content in distributed_result.content_map.items():
            try:
                self._write_distributed_file(agents_path, content, config)
                successful_writes += 1
            except OSError as e:
                self.errors.append(f"Failed to write {agents_path}: {str(e)}")
        
        # Update stats with actual files written
        if distributed_result.stats:
            distributed_result.stats["agents_files_generated"] = successful_writes
        
        # Merge warnings and errors
        self.warnings.extend(distributed_result.warnings)
        self.errors.extend(distributed_result.errors)
        
        # Create summary for backward compatibility
        summary_content = self._generate_distributed_summary(distributed_result, config)
        
        return CompilationResult(
            success=len(self.errors) == 0,
            output_path=f"Distributed: {len(distributed_result.placements)} AGENTS.md files",
            content=summary_content,
            warnings=self.warnings.copy(),
            errors=self.errors.copy(),
            stats=distributed_result.stats
        )
    
    def _compile_single_file(self, config: CompilationConfig, primitives: PrimitiveCollection) -> CompilationResult:
        """Compile using traditional single-file approach (backward compatibility).
        
        Args:
            config (CompilationConfig): Compilation configuration.
            primitives (PrimitiveCollection): Primitives to compile.
        
        Returns:
            CompilationResult: Result of single-file compilation.
        """
        # Validate primitives
        validation_errors = self.validate_primitives(primitives)
        if validation_errors:
            self.errors.extend(validation_errors)
        
        # Generate template data
        template_data = self._generate_template_data(primitives, config)
        
        # Generate final output
        content = self.generate_output(template_data, config)
        
        # Write output file (constitution injection handled externally in CLI)
        output_path = str(self.base_dir / config.output_path)
        if not config.dry_run:
            self._write_output_file(output_path, content)
        
        # Compile statistics
        stats = self._compile_stats(primitives, template_data)
        
        return CompilationResult(
            success=len(self.errors) == 0,
            output_path=output_path,
            content=content,
            warnings=self.warnings.copy(),
            errors=self.errors.copy(),
            stats=stats
        )
    
    def validate_primitives(self, primitives: PrimitiveCollection) -> List[str]:
        """Validate primitives for compilation.
        
        Args:
            primitives (PrimitiveCollection): Collection of primitives to validate.
        
        Returns:
            List[str]: List of validation errors.
        """
        errors = []
        
        # Validate each primitive
        for primitive in primitives.all_primitives():
            primitive_errors = primitive.validate()
            if primitive_errors:
                try:
                    # Try to get relative path, but fall back to absolute if it fails
                    file_path = str(primitive.file_path.relative_to(self.base_dir))
                except ValueError:
                    # File is outside base_dir, use absolute path
                    file_path = str(primitive.file_path)
                
                for error in primitive_errors:
                    # Treat validation errors as warnings instead of hard errors
                    # This allows compilation to continue with incomplete primitives
                    self.warnings.append(f"{file_path}: {error}")
            
            # Validate markdown links in each primitive's content using its own directory as base
            if hasattr(primitive, 'content') and primitive.content:
                primitive_dir = primitive.file_path.parent
                link_errors = validate_link_targets(primitive.content, primitive_dir)
                if link_errors:
                    try:
                        file_path = str(primitive.file_path.relative_to(self.base_dir))
                    except ValueError:
                        file_path = str(primitive.file_path)
                    
                    for link_error in link_errors:
                        self.warnings.append(f"{file_path}: {link_error}")
        
        return errors
    
    def generate_output(self, template_data: TemplateData, config: CompilationConfig) -> str:
        """Generate the final AGENTS.md output.
        
        Args:
            template_data (TemplateData): Data for template generation.
            config (CompilationConfig): Compilation configuration.
        
        Returns:
            str: Generated AGENTS.md content.
        """
        content = generate_agents_md_template(template_data)
        
        # Resolve markdown links if enabled
        if config.resolve_links:
            content = resolve_markdown_links(content, self.base_dir)
        
        return content
    
    def _generate_template_data(self, primitives: PrimitiveCollection, config: CompilationConfig) -> TemplateData:
        """Generate template data from primitives and configuration.
        
        Args:
            primitives (PrimitiveCollection): Discovered primitives.
            config (CompilationConfig): Compilation configuration.
        
        Returns:
            TemplateData: Template data for generation.
        """
        # Build instructions content
        instructions_content = build_conditional_sections(primitives.instructions)

        # Metadata (version only; timestamp intentionally omitted for determinism)
        version = get_version()

        # Handle chatmode content
        chatmode_content = None
        if config.chatmode:
            chatmode = find_chatmode_by_name(primitives.chatmodes, config.chatmode)
            if chatmode:
                chatmode_content = chatmode.content
            else:
                self.warnings.append(f"Chatmode '{config.chatmode}' not found")

        return TemplateData(
            instructions_content=instructions_content,
            version=version,
            chatmode_content=chatmode_content
        )
    
    def _write_output_file(self, output_path: str, content: str) -> None:
        """Write the generated content to the output file.
        
        Args:
            output_path (str): Path to write the output.
            content (str): Content to write.
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except OSError as e:
            self.errors.append(f"Failed to write output file {output_path}: {str(e)}")
    
    def _compile_stats(self, primitives: PrimitiveCollection, template_data: TemplateData) -> Dict[str, Any]:
        """Compile statistics about the compilation.
        
        Args:
            primitives (PrimitiveCollection): Discovered primitives.
            template_data (TemplateData): Generated template data.
        
        Returns:
            Dict[str, Any]: Compilation statistics.
        """
        return {
            "primitives_found": primitives.count(),
            "chatmodes": len(primitives.chatmodes),
            "instructions": len(primitives.instructions),
            "contexts": len(primitives.contexts),
            "content_length": len(template_data.instructions_content),
            # timestamp removed
            "version": template_data.version
        }


    def _write_distributed_file(self, agents_path: Path, content: str, config: CompilationConfig) -> None:
        """Write a distributed AGENTS.md file with constitution injection support.
        
        Args:
            agents_path (Path): Path to write the AGENTS.md file.
            content (str): Content to write.
            config (CompilationConfig): Compilation configuration.
        """
        try:
            # Handle constitution injection for distributed files
            final_content = content
            
            if config.with_constitution:
                # Try to inject constitution if available
                try:
                    from .injector import ConstitutionInjector
                    injector = ConstitutionInjector(str(agents_path.parent))
                    final_content, c_status, c_hash = injector.inject(
                        content, 
                        with_constitution=True, 
                        output_path=agents_path
                    )
                except Exception:
                    # If constitution injection fails, use original content
                    pass
            
            # Create directory if it doesn't exist
            agents_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            with open(agents_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
                
        except OSError as e:
            raise OSError(f"Failed to write distributed AGENTS.md file {agents_path}: {str(e)}")
    
    def _display_placement_preview(self, distributed_result) -> None:
        """Display placement preview for --show-placement mode.
        
        Args:
            distributed_result: Result from distributed compilation.
        """
        print("🔍 Distributed AGENTS.md Placement Preview:")
        print()
        
        for placement in distributed_result.placements:
            try:
                rel_path = placement.agents_path.relative_to(self.base_dir.resolve())
            except ValueError:
                # Fallback for path resolution issues
                rel_path = placement.agents_path
            print(f"📄 {rel_path}")
            print(f"   Instructions: {len(placement.instructions)}")
            print(f"   Patterns: {', '.join(sorted(placement.coverage_patterns))}")
            if placement.source_attribution:
                sources = set(placement.source_attribution.values())
                print(f"   Sources: {', '.join(sorted(sources))}")
            print()
    
    def _display_trace_info(self, distributed_result, primitives: PrimitiveCollection) -> None:
        """Display detailed trace information for --trace mode.
        
        Args:
            distributed_result: Result from distributed compilation.
            primitives (PrimitiveCollection): Full primitive collection.
        """
        print("🔍 Distributed Compilation Trace:")
        print()
        
        for placement in distributed_result.placements:
            try:
                rel_path = placement.agents_path.relative_to(self.base_dir.resolve())
            except ValueError:
                rel_path = placement.agents_path
            print(f"📄 {rel_path}")
            
            for instruction in placement.instructions:
                source = getattr(instruction, 'source', 'local')
                try:
                    inst_path = instruction.file_path.relative_to(self.base_dir.resolve())
                except ValueError:
                    inst_path = instruction.file_path
                
                print(f"   • {instruction.apply_to or 'no pattern'} <- {source} {inst_path}")
            print()
    
    def _generate_placement_summary(self, distributed_result) -> str:
        """Generate a text summary of placement results.
        
        Args:
            distributed_result: Result from distributed compilation.
        
        Returns:
            str: Text summary of placements.
        """
        lines = ["Distributed AGENTS.md Placement Summary:", ""]
        
        for placement in distributed_result.placements:
            try:
                rel_path = placement.agents_path.relative_to(self.base_dir.resolve())
            except ValueError:
                rel_path = placement.agents_path
            lines.append(f"📄 {rel_path}")
            lines.append(f"   Instructions: {len(placement.instructions)}")
            lines.append(f"   Patterns: {', '.join(sorted(placement.coverage_patterns))}")
            lines.append("")
        
        lines.append(f"Total AGENTS.md files: {len(distributed_result.placements)}")
        return "\n".join(lines)
    
    def _generate_distributed_summary(self, distributed_result, config: CompilationConfig) -> str:
        """Generate a summary of distributed compilation results.
        
        Args:
            distributed_result: Result from distributed compilation.
            config (CompilationConfig): Compilation configuration.
        
        Returns:
            str: Summary content.
        """
        lines = [
            "# Distributed AGENTS.md Compilation Summary",
            "",
            f"Generated {len(distributed_result.placements)} AGENTS.md files:",
            ""
        ]
        
        for placement in distributed_result.placements:
            try:
                rel_path = placement.agents_path.relative_to(self.base_dir.resolve())
            except ValueError:
                rel_path = placement.agents_path
            lines.append(f"- {rel_path} ({len(placement.instructions)} instructions)")
        
        lines.extend([
            "",
            f"Total instructions: {distributed_result.stats.get('total_instructions_placed', 0)}",
            f"Total patterns: {distributed_result.stats.get('total_patterns_covered', 0)}",
            "",
            "Use 'apm compile --single-agents' for traditional single-file compilation."
        ])
        
        return "\n".join(lines)


def compile_agents_md(
    primitives: Optional[PrimitiveCollection] = None,
    output_path: str = "AGENTS.md",
    chatmode: Optional[str] = None,
    dry_run: bool = False,
    base_dir: str = "."
) -> str:
    """Generate AGENTS.md with conditional sections.
    
    Args:
        primitives (Optional[PrimitiveCollection]): Primitives to use, or None to discover.
        output_path (str): Output file path. Defaults to "AGENTS.md".
        chatmode (str): Specific chatmode to use, or None for default.
        dry_run (bool): If True, don't write output file. Defaults to False.
        base_dir (str): Base directory for compilation. Defaults to current directory.
    
    Returns:
        str: Generated AGENTS.md content.
    """
    # Create configuration - use single-file mode for backward compatibility
    config = CompilationConfig(
        output_path=output_path,
        chatmode=chatmode,
        dry_run=dry_run,
        strategy="single-file"  # Force single-file mode for backward compatibility
    )
    
    # Create compiler and compile
    compiler = AgentsCompiler(base_dir)
    result = compiler.compile(config, primitives)
    
    if not result.success:
        raise RuntimeError(f"Compilation failed: {'; '.join(result.errors)}")
    
    return result.content