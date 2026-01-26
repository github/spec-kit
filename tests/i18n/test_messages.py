"""
Tests for CLI message translation.

Tests that CLI messages are properly marked for translation and translated correctly.
"""

import os
import pytest
from specify_cli.i18n.core import setup_i18n


class TestMessageTranslation:
    """Test CLI message translation functionality."""
    
    def test_simple_message_translation(self, monkeypatch):
        """Test that simple messages can be translated."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        gettext_func, _ = setup_i18n()
        
        # Test with English (should return as-is)
        message = gettext_func("Project ready.")
        assert isinstance(message, str)
        assert message == "Project ready."
    
    def test_message_with_variables(self, monkeypatch):
        """Test that messages with variables preserve placeholders."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        gettext_func, _ = setup_i18n()
        
        # Message template with named variable
        template = gettext_func("Initialized project '{name}'")
        assert "{name}" in template or "name" in template
        
        # Format with actual value
        result = template.format(name="test-project")
        assert "test-project" in result
    
    def test_plural_message_translation(self, monkeypatch):
        """Test that plural messages work correctly."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        _, ngettext_func = setup_i18n()
        
        # Test singular (n=1)
        singular = ngettext_func("{count} file created", "{count} files created", 1)
        formatted_singular = singular.format(count=1)
        assert "1" in formatted_singular
        assert "file" in formatted_singular
        
        # Test plural (n=2)
        plural = ngettext_func("{count} file created", "{count} files created", 2)
        formatted_plural = plural.format(count=2)
        assert "2" in formatted_plural
    
    def test_chinese_locale_setup(self, monkeypatch):
        """Test that Chinese locale can be set up without errors."""
        monkeypatch.setenv("SPECIFY_LANG", "zh_CN")
        
        # Should not raise exception even if translations don't exist yet
        gettext_func, ngettext_func = setup_i18n()
        
        assert callable(gettext_func)
        assert callable(ngettext_func)
        
        # Should return original message if translation missing
        message = gettext_func("Test message")
        assert message == "Test message"
    
    def test_fallback_to_english_for_missing_translation(self, monkeypatch):
        """Test that missing translations fall back to English."""
        monkeypatch.setenv("SPECIFY_LANG", "zh_CN")
        gettext_func, _ = setup_i18n()
        
        # For untranslated messages, should return original English
        original = "This message is not translated"
        result = gettext_func(original)
        assert result == original


class TestRichMarkupPreservation:
    """Test that Rich console markup is preserved in translations."""
    
    def test_rich_markup_in_message(self, monkeypatch):
        """Test that Rich markup tags are preserved."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        gettext_func, _ = setup_i18n()
        
        # Message with Rich markup
        message = gettext_func("[green]Success:[/green] Project created")
        
        # Rich markup should be preserved
        assert "[green]" in message
        assert "[/green]" in message
    
    def test_rich_markup_with_variables(self, monkeypatch):
        """Test Rich markup with variable substitution."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        gettext_func, _ = setup_i18n()
        
        template = gettext_func("[cyan]Downloading:[/cyan] {filename}")
        result = template.format(filename="template.zip")
        
        assert "[cyan]" in result
        assert "[/cyan]" in result
        assert "template.zip" in result


class TestErrorMessageTranslation:
    """Test that error messages are translatable."""
    
    def test_error_message_format(self, monkeypatch):
        """Test error message translation and formatting."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        gettext_func, _ = setup_i18n()
        
        error_template = gettext_func("[red]Error:[/red] {message}")
        result = error_template.format(message="File not found")
        
        assert "[red]" in result
        assert "File not found" in result
    
    def test_warning_message_format(self, monkeypatch):
        """Test warning message translation and formatting."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        gettext_func, _ = setup_i18n()
        
        warning_template = gettext_func("[yellow]Warning:[/yellow] {message}")
        result = warning_template.format(message="Directory not empty")
        
        assert "[yellow]" in result
        assert "Directory not empty" in result


class TestMessageConsistency:
    """Test that message terminology is consistent."""
    
    def test_consistent_project_terminology(self, monkeypatch):
        """Test that 'project' terminology is used consistently."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        gettext_func, _ = setup_i18n()
        
        # These should all use "project" consistently
        msg1 = gettext_func("Project ready.")
        msg2 = gettext_func("Initialized project '{name}'")
        
        assert "project" in msg1.lower() or "Project" in msg1
        assert "project" in msg2.lower() or "Project" in msg2
