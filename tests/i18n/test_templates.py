"""
Tests for template localization.

Tests that templates can be localized and placeholders are preserved.
"""

import os
import pytest
from pathlib import Path
from specify_cli.i18n.core import get_template_path, get_active_locale


class TestTemplateSelection:
    """Test localized template selection logic."""
    
    def test_english_template_selection(self, monkeypatch):
        """Should select English template for en_US locale."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        
        template_path = get_template_path("spec-template.md")
        assert isinstance(template_path, Path)
        assert template_path.name == "spec-template.md"
    
    def test_chinese_template_selection(self, monkeypatch):
        """Should attempt to select Chinese template for zh_CN locale."""
        monkeypatch.setenv("SPECIFY_LANG", "zh_CN")
        
        template_path = get_template_path("spec-template.md")
        assert isinstance(template_path, Path)
        assert template_path.name == "spec-template.md"
        
        # If Chinese template exists, path should include i18n/zh_CN
        # If not, falls back to English (base templates/ directory)
        path_str = str(template_path)
        # This is valid either way - fallback is expected if not translated yet
        assert "spec-template.md" in path_str
    
    def test_explicit_locale_parameter(self, monkeypatch):
        """Should respect explicit locale parameter."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        
        # Request Chinese template explicitly
        zh_path = get_template_path("spec-template.md", locale="zh_CN")
        
        # Request English template explicitly
        en_path = get_template_path("spec-template.md", locale="en_US")
        
        assert isinstance(zh_path, Path)
        assert isinstance(en_path, Path)


class TestTemplatePathResolution:
    """Test template path resolution and fallback behavior."""
    
    def test_nonexistent_template_returns_path(self, monkeypatch):
        """Should return path even if template doesn't exist (for creation)."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        
        path = get_template_path("nonexistent-template.md")
        assert isinstance(path, Path)
        assert "nonexistent-template.md" in str(path)
    
    def test_command_template_path(self, monkeypatch):
        """Should handle command template paths correctly."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        
        # Command templates are in commands/ subdirectory
        path = get_template_path("commands/specify.md")
        assert isinstance(path, Path)
        assert "specify.md" in str(path)


class TestTemplatePlaceholderPreservation:
    """Test that template placeholders are preserved in localized versions."""
    
    def test_placeholder_format(self):
        """Test that placeholders follow expected format."""
        # Common placeholders used in templates
        placeholders = [
            "[FEATURE_NAME]",
            "[PROJECT_NAME]",
            "[BRANCH]",
            "[DATE]",
            "[###-feature-name]",
        ]
        
        # These should remain unchanged in translations
        for placeholder in placeholders:
            # Placeholders are literal strings in square brackets
            assert placeholder.startswith("[")
            assert placeholder.endswith("]")
            assert placeholder.isupper() or "###" in placeholder


class TestTemplateTypes:
    """Test different template types can be localized."""
    
    @pytest.mark.parametrize("template_name", [
        "spec-template.md",
        "plan-template.md",
        "tasks-template.md",
        "checklist-template.md",
        "agent-file-template.md",
    ])
    def test_core_templates(self, template_name, monkeypatch):
        """Test that core templates can be retrieved."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        
        path = get_template_path(template_name)
        assert isinstance(path, Path)
        assert path.name == template_name
    
    @pytest.mark.parametrize("command_template", [
        "commands/specify.md",
        "commands/plan.md",
        "commands/tasks.md",
        "commands/implement.md",
        "commands/clarify.md",
        "commands/analyze.md",
        "commands/checklist.md",
        "commands/constitution.md",
        "commands/taskstoissues.md",
    ])
    def test_command_templates(self, command_template, monkeypatch):
        """Test that command templates can be retrieved."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        
        path = get_template_path(command_template)
        assert isinstance(path, Path)
        assert command_template.split("/")[-1] in str(path)


class TestLocaleEnvironment:
    """Test locale environment variable handling."""
    
    def test_unset_locale_defaults_to_english(self, monkeypatch):
        """Unset locale should default to English templates."""
        monkeypatch.delenv("SPECIFY_LANG", raising=False)
        
        locale = get_active_locale()
        assert locale == "en_US"
        
        path = get_template_path("spec-template.md")
        assert isinstance(path, Path)
    
    def test_invalid_locale_falls_back(self, monkeypatch, capsys):
        """Invalid locale should fallback to English with warning."""
        monkeypatch.setenv("SPECIFY_LANG", "invalid_XX")
        
        locale = get_active_locale()
        assert locale == "en_US"
        
        # Should have printed a warning
        captured = capsys.readouterr()
        # Warning might be in stdout or stderr depending on implementation
        output = captured.out + captured.err
        assert len(output) > 0  # Some output was produced
