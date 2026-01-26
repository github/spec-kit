"""
Internationalization (i18n) module for Specify CLI.

This module provides translation support for CLI messages, templates, and documentation
using Python's gettext framework with Babel for extraction and compilation.

Usage:
    from specify_cli.i18n import _, ngettext, setup_i18n, get_template_path
    
    # Initialize i18n at application startup
    setup_i18n()
    
    # Use in code
    print(_("Project ready."))
    print(_("Initialized project '{name}'").format(name=project_name))
    print(ngettext("{count} file", "{count} files", count).format(count=count))
    
    # Get localized template
    template_path = get_template_path("spec-template.md")
"""

from .core import (
    setup_i18n,
    get_active_locale,
    get_template_path,
    SUPPORTED_LANGUAGES,
)

# Global translation functions - initialized by setup_i18n()
_ = lambda x: x  # Placeholder until setup_i18n() is called
ngettext = lambda s, p, n: s if n == 1 else p  # Placeholder

__all__ = [
    "setup_i18n",
    "get_active_locale",
    "get_template_path",
    "SUPPORTED_LANGUAGES",
    "_",
    "ngettext",
]
