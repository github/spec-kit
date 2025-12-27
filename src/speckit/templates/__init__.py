"""
Jinja2 prompt templates for LLM interactions.

This module provides template loading and rendering utilities for
generating prompts used in workflow phases.
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Template directory
TEMPLATE_DIR = Path(__file__).parent

# Jinja2 environment
_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def get_template(name: str):
    """Load a template by name."""
    return _env.get_template(name)


def render_template(name: str, **kwargs) -> str:
    """Render a template with the given context."""
    template = get_template(name)
    return template.render(**kwargs)


__all__ = [
    "TEMPLATE_DIR",
    "get_template",
    "render_template",
]
