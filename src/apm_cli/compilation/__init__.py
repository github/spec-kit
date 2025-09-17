"""APM compilation module for generating AGENTS.md files."""

from .agents_compiler import AgentsCompiler, compile_agents_md, CompilationConfig, CompilationResult
from .template_builder import (
    build_conditional_sections,
    TemplateData,
    find_chatmode_by_name
)
from .link_resolver import (
    resolve_markdown_links,
    validate_link_targets
)

__all__ = [
    # Main compilation interface
    'AgentsCompiler',
    'compile_agents_md',
    'CompilationConfig',
    'CompilationResult',
    
    # Template building
    'build_conditional_sections',
    'TemplateData',
    'find_chatmode_by_name',
    
    # Link resolution
    'resolve_markdown_links',
    'validate_link_targets'
]