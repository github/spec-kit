"""
Localization support for Spec Kit templates and messages.
"""

from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class LocaleManager:
    """Manages localization for templates and messages."""

    def __init__(self, locale_dir: Path = None):
        self.locale_dir = locale_dir or Path(__file__).parent.parent.parent / "locales"
        self.current_locale = "en"  # Default to English
        self._cache: Dict[str, Dict[str, Any]] = {}

    def set_locale(self, locale: str) -> bool:
        """Set the current locale. Returns True if successful."""
        locale_file = self.locale_dir / f"{locale}.yaml"
        if locale_file.exists():
            self.current_locale = locale
            return True
        return False

    def get_available_locales(self) -> list[str]:
        """Get list of available locales."""
        if not self.locale_dir.exists():
            return ["en"]

        locales = []
        for file in self.locale_dir.glob("*.yaml"):
            locales.append(file.stem)
        return sorted(locales)

    def _load_locale(self, locale: str) -> Dict[str, Any]:
        """Load locale data from YAML file."""
        if locale in self._cache:
            return self._cache[locale]

        locale_file = self.locale_dir / f"{locale}.yaml"
        if not locale_file.exists():
            # Fallback to English
            locale_file = self.locale_dir / "en.yaml"
            if not locale_file.exists():
                return {}

        try:
            with open(locale_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                self._cache[locale] = data
                return data
        except Exception as e:
            # Use console from rich if available, otherwise fallback to print
            try:
                from rich.console import Console
                console = Console()
                console.print(f"[yellow]Warning: Failed to load locale {locale}: {e}[/yellow]")
            except ImportError:
                print(f"Warning: Failed to load locale {locale}: {e}")
            return {}

    def get_text(self, key_path: str, **kwargs) -> str:
        """
        Get localized text by key path (e.g., 'templates.spec.title').
        Supports string formatting with kwargs.
        """
        data = self._load_locale(self.current_locale)

        # Navigate through nested keys
        keys = key_path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                # Fallback to English if key not found
                if self.current_locale != "en":
                    return self.get_text_from_locale("en", key_path, **kwargs)
                return f"[{key_path}]"  # Missing translation indicator

        if isinstance(current, str):
            try:
                return current.format(**kwargs) if kwargs else current
            except KeyError:
                return current

        return f"[{key_path}]"

    def get_text_from_locale(self, locale: str, key_path: str, **kwargs) -> str:
        """Get text from specific locale."""
        original_locale = self.current_locale
        self.current_locale = locale
        result = self.get_text(key_path, **kwargs)
        self.current_locale = original_locale
        return result

    def translate_template(self, template_content: str, template_type: str = "spec") -> str:
        """
        Replace translation markers in template content with localized text.
        Markers format: {{locale:key.path}}
        """
        import re

        def replace_marker(match):
            key_path = match.group(1)
            return self.get_text(key_path)

        # Replace {{locale:key.path}} markers
        pattern = r'\{\{locale:([^}]+)\}\}'
        return re.sub(pattern, replace_marker, template_content)


# Global instance
_locale_manager = None

def get_locale_manager() -> LocaleManager:
    """Get the global locale manager instance."""
    global _locale_manager
    if _locale_manager is None:
        _locale_manager = LocaleManager()
    return _locale_manager

def set_locale(locale: str) -> bool:
    """Set the global locale."""
    return get_locale_manager().set_locale(locale)

def get_text(key_path: str, **kwargs) -> str:
    """Get localized text using the global locale manager."""
    return get_locale_manager().get_text(key_path, **kwargs)

def translate_template(template_content: str, template_type: str = "spec") -> str:
    """Translate template using the global locale manager."""
    return get_locale_manager().translate_template(template_content, template_type)

def inject_language_instructions(template_content: str, command: str = "specify", locale: str = None) -> str:
    """
    Inject language-specific instructions into command templates.
    Completely YAML-driven approach - no hardcoding for any language.

    Args:
        template_content: The template content to modify
        command: The command name (specify, plan, tasks, etc.)
        locale: Target locale (defaults to current locale)

    Returns:
        Template with language instructions injected
    """
    if locale is None:
        locale = get_locale_manager().current_locale

    lm = get_locale_manager()

    # Get AI instructions from YAML
    general_instruction = lm.get_text("ai_instructions.general")
    command_instruction = lm.get_text(f"ai_instructions.commands.{command}")
    guidelines = lm.get_text("ai_instructions.guidelines")
    guidelines_header = lm.get_text("ai_instructions.guidelines_header")
    footer_reminder = lm.get_text("ai_instructions.footer_reminder")

    # Build instruction text
    instruction_parts = []

    if general_instruction:
        instruction_parts.append(general_instruction)

    if command_instruction:
        instruction_parts.append(command_instruction)

    if guidelines and isinstance(guidelines, list) and guidelines_header:
        guidelines_text = "\n".join(f"- {guideline}" for guideline in guidelines)
        instruction_parts.append(f"\n{guidelines_header}\n{guidelines_text}")

    # Combine instructions
    language_instruction = "\n\n".join(instruction_parts) if instruction_parts else ""

    # For backward compatibility, also support command-specific content instruction
    content_instruction = command_instruction if command_instruction else ""

    # Replace placeholders
    result = template_content.replace("{{LANGUAGE_INSTRUCTION}}", language_instruction)
    result = result.replace("{{LANGUAGE_CONTENT_INSTRUCTION}}", content_instruction)

    # Add footer reminder at the end of the template if it exists
    if footer_reminder and footer_reminder.strip():
        result = result + "\n" + footer_reminder

    return result

def get_ai_instruction(command: str = "specify", locale: str = None) -> str:
    """
    Get AI instruction for a specific command and locale.
    Utility function for getting instructions without template injection.
    """
    if locale is None:
        locale = get_locale_manager().current_locale

    lm = get_locale_manager()
    general = lm.get_text("ai_instructions.general")
    specific = lm.get_text(f"ai_instructions.commands.{command}")

    parts = [part for part in [general, specific] if part]
    return "\n\n".join(parts)