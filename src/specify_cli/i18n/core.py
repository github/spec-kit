"""
Core internationalization logic for Specify CLI.

Handles language detection, translation catalog loading, and localized template selection.
"""

import gettext
import os
from pathlib import Path
from typing import Callable, Optional

# Language metadata
class Language:
    """Represents a supported language with metadata."""
    
    def __init__(
        self,
        code: str,
        display_name: str,
        fallback: Optional[str] = None,
        plural_forms: str = "nplurals=2; plural=(n != 1);",
    ):
        self.code = code
        self.display_name = display_name
        self.fallback = fallback
        self.plural_forms = plural_forms
        self.catalog_path = Path(__file__).parent / code
        self.template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "i18n" / code


# Supported languages configuration
SUPPORTED_LANGUAGES = {
    "en_US": Language(
        code="en_US",
        display_name="English (US)",
        fallback=None,
        plural_forms="nplurals=2; plural=(n != 1);",
    ),
    "zh_CN": Language(
        code="zh_CN",
        display_name="简体中文",
        fallback="en_US",
        plural_forms="nplurals=1; plural=0;",
    ),
}


def get_active_locale(cli_lang: Optional[str] = None) -> str:
    """
    Detect active locale from CLI argument or SPECIFY_LANG environment variable.
    
    Args:
        cli_lang: Optional language code from CLI --lang argument (takes precedence)
    
    Returns:
        str: Active locale code (e.g., "zh_CN", "en_US")
        
    Priority:
        1. CLI --lang argument (highest priority)
        2. SPECIFY_LANG environment variable
        3. "en_US" default
        
    Note:
        Falls back to "en_US" if locale is unset or invalid.
    """
    # Priority: CLI arg > environment variable > default
    locale = cli_lang or os.getenv("SPECIFY_LANG", "en_US")
    
    # Validate against supported languages
    if locale not in SUPPORTED_LANGUAGES:
        # Import console here to avoid circular dependency
        try:
            from rich.console import Console
            console = Console()
            console.print(
                f"[yellow]Warning:[/yellow] Unsupported locale '{locale}', "
                "using English. "
                f"Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}"
            )
        except ImportError:
            # Fallback if rich not available
            print(f"Warning: Unsupported locale '{locale}', using English")
        
        return "en_US"
    
    return locale


def setup_i18n(cli_lang: Optional[str] = None) -> tuple[Callable[[str], str], Callable[[str, str, int], str]]:
    """
    Initialize internationalization and return translation functions.
    
    Args:
        cli_lang: Optional language code from CLI --lang argument
    
    Returns:
        tuple: (gettext function, ngettext function)
        
    Example:
        >>> _, ngettext = setup_i18n(cli_lang='zh_CN')
        >>> print(_("Project ready."))
        >>> print(ngettext("{count} file", "{count} files", 2).format(count=2))
    """
    locale = get_active_locale(cli_lang)
    lang = SUPPORTED_LANGUAGES[locale]
    
    # Get the directory containing all locale catalogs
    locale_dir = Path(__file__).parent
    
    try:
        # Build fallback chain
        languages = [locale]
        if lang.fallback:
            languages.append(lang.fallback)
        
        # Load translation catalog with fallback
        translation = gettext.translation(
            "specify",
            localedir=str(locale_dir),
            languages=languages,
            fallback=True,
        )
        
        return translation.gettext, translation.ngettext
        
    except Exception as e:
        # Import console here to avoid circular dependency
        try:
            from rich.console import Console
            console = Console()
            console.print(
                f"[yellow]Warning:[/yellow] Failed to load translations for '{locale}': {e}"
            )
            console.print("[yellow]Falling back to English[/yellow]")
        except ImportError:
            print(f"Warning: Failed to load translations: {e}")
        
        # Return NullTranslations (identity functions)
        null_translation = gettext.NullTranslations()
        return null_translation.gettext, null_translation.ngettext


def get_template_path(template_name: str, locale: Optional[str] = None, cli_lang: Optional[str] = None) -> Path:
    """
    Get localized template path with fallback to English.
    
    Args:
        template_name: Name of the template file (e.g., "spec-template.md")
        locale: Language code (overrides active locale)
        cli_lang: Language from CLI --lang argument (used if locale not provided)
        
    Returns:
        Path: Path to the localized template file, or English template if not found
        
    Example:
        >>> path = get_template_path("spec-template.md", cli_lang='zh_CN')
        >>> # Returns templates/i18n/zh_CN/spec-template.md if exists
        >>> # Otherwise returns templates/spec-template.md
    """
    if locale is None:
        locale = get_active_locale(cli_lang)
    
    # Try localized template first
    if locale in SUPPORTED_LANGUAGES:
        lang = SUPPORTED_LANGUAGES[locale]
        if lang.template_dir:
            localized_path = lang.template_dir / template_name
            if localized_path.exists():
                return localized_path
    
    # Fallback to English template
    base_templates_dir = Path(__file__).parent.parent.parent.parent / "templates"
    english_path = base_templates_dir / template_name
    
    return english_path


def detect_terminal_encoding() -> tuple[str, bool]:
    """
    Detect terminal encoding and check if it supports UTF-8/Chinese characters.
    
    Returns:
        tuple: (encoding name, supports_unicode)
        
    Note:
        Used to warn users if their terminal may not display Chinese characters correctly.
    """
    import sys
    
    encoding = sys.stdout.encoding or "utf-8"
    supports_unicode = encoding.lower() in ["utf-8", "utf8", "utf_8"]
    
    return encoding, supports_unicode
