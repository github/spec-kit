"""
Tests for core i18n functionality.

Tests language detection (CLI args + env vars), catalog loading, fallback behavior, and template selection.
"""

import os
import pytest
from pathlib import Path
from specify_cli.i18n.core import (
    get_active_locale,
    setup_i18n,
    get_template_path,
    SUPPORTED_LANGUAGES,
    detect_terminal_encoding,
)


class TestLanguageDetection:
    """Test language detection from CLI argument and environment variable."""
    
    def test_default_locale_when_unset(self, monkeypatch):
        """Should return en_US when no CLI arg and SPECIFY_LANG not set."""
        monkeypatch.delenv("SPECIFY_LANG", raising=False)
        assert get_active_locale() == "en_US"
    
    def test_cli_arg_takes_precedence_over_env(self, monkeypatch):
        """CLI --lang argument should override SPECIFY_LANG environment variable."""
        monkeypatch.setenv("SPECIFY_LANG", "en_US")
        assert get_active_locale(cli_lang="zh_CN") == "zh_CN"
    
    def test_env_var_used_when_no_cli_arg(self, monkeypatch):
        """Should use SPECIFY_LANG when CLI argument not provided."""
        monkeypatch.setenv("SPECIFY_LANG", "zh_CN")
        assert get_active_locale() == "zh_CN"
    
    def test_valid_chinese_locale_from_cli(self, monkeypatch):
        """Should return zh_CN when CLI --lang=zh_CN."""
        assert get_active_locale(cli_lang="zh_CN") == "zh_CN"
    
    def test_valid_english_locale_from_cli(self, monkeypatch):
        """Should return en_US when CLI --lang=en_US."""
        assert get_active_locale(cli_lang="en_US") == "en_US"
    
    def test_invalid_locale_falls_back_to_english(self, monkeypatch, capsys):
        """Should fallback to en_US for invalid locale with warning."""
        locale = get_active_locale(cli_lang="invalid_XX")
        assert locale == "en_US"
        
        # Check that warning was printed
        captured = capsys.readouterr()
        assert "Warning" in captured.out or "Warning" in captured.err
        assert "invalid_XX" in captured.out or "invalid_XX" in captured.err


class TestTranslationSetup:
    """Test translation catalog loading and setup with CLI arguments."""
    
    def test_setup_returns_callable_functions(self, monkeypatch):
        """Should return callable gettext and ngettext functions."""
        monkeypatch.delenv("SPECIFY_LANG", raising=False)
        gettext_func, ngettext_func = setup_i18n()
        
        assert callable(gettext_func)
        assert callable(ngettext_func)
    
    def test_setup_with_cli_lang_argument(self, monkeypatch):
        """Should initialize translations with CLI --lang argument."""
        gettext_func, ngettext_func = setup_i18n(cli_lang="zh_CN")
        
        assert callable(gettext_func)
        assert callable(ngettext_func)
    
    def test_gettext_returns_string(self, monkeypatch):
        """Gettext function should return strings."""
        gettext_func, _ = setup_i18n(cli_lang="en_US")
        
        result = gettext_func("Test message")
        assert isinstance(result, str)
    
    def test_ngettext_handles_plurals(self, monkeypatch):
        """Ngettext function should handle singular/plural forms."""
        _, ngettext_func = setup_i18n(cli_lang="en_US")
        
        singular = ngettext_func("file", "files", 1)
        plural = ngettext_func("file", "files", 2)
        
        assert isinstance(singular, str)
        assert isinstance(plural, str)
    
    def test_chinese_locale_initialization(self, monkeypatch):
        """Should initialize with zh_CN without errors (even if catalog missing)."""
        gettext_func, ngettext_func = setup_i18n(cli_lang="zh_CN")
        
        assert callable(gettext_func)
        assert callable(ngettext_func)
        
        # Should return original message if translation missing (fallback)
        result = gettext_func("Untranslated message")
        assert result == "Untranslated message"


class TestTemplateLocalization:
    """Test localized template selection with CLI arguments."""
    
    def test_english_template_path(self, monkeypatch):
        """Should return English template path for en_US locale."""
        path = get_template_path("spec-template.md", cli_lang="en_US")
        
        assert isinstance(path, Path)
        assert "spec-template.md" in str(path)
        # Should be in base templates/ directory, not i18n subdirectory
        assert "i18n" not in str(path) or path.parent.name != "i18n"
    
    def test_chinese_template_path_fallback(self, monkeypatch):
        """Should fallback to English if Chinese template doesn't exist."""
        path = get_template_path("spec-template.md", cli_lang="zh_CN")
        
        assert isinstance(path, Path)
        assert "spec-template.md" in str(path)
        # May be in i18n/zh_CN/ if exists, otherwise base templates/
    
    def test_explicit_locale_overrides_cli_lang(self, monkeypatch):
        """Explicit locale parameter should override CLI --lang argument."""
        # Pass zh_CN as cli_lang but en_US as locale
        path = get_template_path("spec-template.md", locale="en_US", cli_lang="zh_CN")
        
        assert isinstance(path, Path)
        # Should use en_US (explicit locale), not zh_CN (cli_lang)
        assert "i18n" not in str(path) or "en_US" not in str(path)
    
    def test_template_path_with_subdirectory(self, monkeypatch):
        """Should handle template paths with subdirectories (e.g., commands/)."""
        path = get_template_path("commands/specify.md", cli_lang="en_US")
        
        assert isinstance(path, Path)
        assert "specify.md" in str(path)


class TestTerminalEncoding:
    """Test terminal encoding detection."""
    
    def test_detect_encoding_returns_tuple(self):
        """Should return (encoding, supports_unicode) tuple."""
        encoding, supports_unicode = detect_terminal_encoding()
        
        assert isinstance(encoding, str)
        assert isinstance(supports_unicode, bool)
    
    def test_utf8_encoding_is_supported(self):
        """UTF-8 encoding should be marked as unicode-supporting."""
        encoding, supports_unicode = detect_terminal_encoding()
        
        # If terminal is UTF-8, should be marked as supporting unicode
        if "utf" in encoding.lower():
            assert supports_unicode is True


class TestSupportedLanguages:
    """Test SUPPORTED_LANGUAGES configuration."""
    
    def test_english_is_supported(self):
        """English (en_US) should be in supported languages."""
        assert "en_US" in SUPPORTED_LANGUAGES
        
        lang = SUPPORTED_LANGUAGES["en_US"]
        assert lang.code == "en_US"
        assert lang.display_name == "English (US)"
        assert lang.fallback is None  # English has no fallback
    
    def test_chinese_is_supported(self):
        """Chinese (zh_CN) should be in supported languages."""
        assert "zh_CN" in SUPPORTED_LANGUAGES
        
        lang = SUPPORTED_LANGUAGES["zh_CN"]
        assert lang.code == "zh_CN"
        assert lang.display_name == "简体中文"
        assert lang.fallback == "en_US"  # Chinese falls back to English
    
    def test_all_languages_have_required_attributes(self):
        """All supported languages should have required metadata."""
        for code, lang in SUPPORTED_LANGUAGES.items():
            assert lang.code == code
            assert isinstance(lang.display_name, str)
            assert len(lang.display_name) > 0
            assert isinstance(lang.plural_forms, str)
            assert "nplurals" in lang.plural_forms
