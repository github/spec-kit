"""
Test cases for localization functionality.
"""

# import pytest  # Not needed for basic tests
import tempfile
from pathlib import Path
import yaml

from specify_cli.locale import LocaleManager, get_text, set_locale, translate_template


class TestLocaleManager:
    """Test LocaleManager functionality."""

    def test_init_with_default_path(self):
        """Test LocaleManager initialization with default path."""
        lm = LocaleManager()
        assert lm.current_locale == "en"
        assert lm.locale_dir.name == "locales"

    def test_init_with_custom_path(self):
        """Test LocaleManager initialization with custom path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir)
            lm = LocaleManager(custom_path)
            assert lm.locale_dir == custom_path

    def test_get_available_locales(self):
        """Test getting available locales."""
        lm = LocaleManager()
        locales = lm.get_available_locales()
        assert "en" in locales
        assert "ko" in locales

    def test_set_locale_valid(self):
        """Test setting a valid locale."""
        lm = LocaleManager()
        assert lm.set_locale("ko") is True
        assert lm.current_locale == "ko"

    def test_set_locale_invalid(self):
        """Test setting an invalid locale."""
        lm = LocaleManager()
        assert lm.set_locale("invalid") is False
        assert lm.current_locale == "en"  # Should remain unchanged

    def test_get_text_english(self):
        """Test getting English text."""
        lm = LocaleManager()
        lm.set_locale("en")
        title = lm.get_text("templates.spec.title")
        assert title == "Feature Specification"

    def test_get_text_korean(self):
        """Test getting Korean text."""
        lm = LocaleManager()
        lm.set_locale("ko")
        title = lm.get_text("templates.spec.title")
        assert title == "기능 명세서"

    def test_get_text_with_formatting(self):
        """Test getting text with string formatting."""
        lm = LocaleManager()
        lm.set_locale("en")
        # Test with a path that exists in the YAML and supports formatting
        error_msg = lm.get_text("messages.errors.no_spec", path="/test/path")
        assert "/test/path" in error_msg

    def test_get_text_fallback_to_english(self):
        """Test fallback to English when key not found in other locale."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a minimal Korean file with missing keys
            korean_file = Path(temp_dir) / "ko.yaml"
            with open(korean_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump({"partial": {"key": "값"}}, f)

            # Create English fallback
            english_file = Path(temp_dir) / "en.yaml"
            with open(english_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump({"templates": {"spec": {"title": "Feature Specification"}}}, f)

            lm = LocaleManager(Path(temp_dir))
            lm.set_locale("ko")
            title = lm.get_text("templates.spec.title")
            assert title == "Feature Specification"  # Should fallback to English

    def test_get_text_missing_key(self):
        """Test getting text for missing key."""
        lm = LocaleManager()
        result = lm.get_text("nonexistent.key.path")
        assert result == "[nonexistent.key.path]"

    def test_translate_template(self):
        """Test template translation."""
        lm = LocaleManager()
        lm.set_locale("ko")

        template = "# {{locale:templates.spec.title}}: Test Feature"
        translated = lm.translate_template(template)
        assert translated == "# 기능 명세서: Test Feature"

    def test_translate_template_multiple_markers(self):
        """Test template translation with multiple markers."""
        lm = LocaleManager()
        lm.set_locale("ko")

        template = """
# {{locale:templates.spec.title}}: [FEATURE NAME]

## {{locale:templates.spec.sections.requirements}}
"""
        translated = lm.translate_template(template)
        assert "기능 명세서" in translated
        assert "요구사항" in translated


class TestGlobalFunctions:
    """Test global locale functions."""

    def test_set_locale_global(self):
        """Test global set_locale function."""
        assert set_locale("ko") is True
        assert set_locale("invalid") is False

    def test_get_text_global(self):
        """Test global get_text function."""
        set_locale("en")
        title = get_text("templates.spec.title")
        assert title == "Feature Specification"

    def test_translate_template_global(self):
        """Test global translate_template function."""
        set_locale("ko")
        template = "# {{locale:templates.spec.title}}: Test"
        translated = translate_template(template)
        assert translated == "# 기능 명세서: Test"


if __name__ == "__main__":
    # Run basic functionality test
    print("Running basic locale tests...")

    # Test English
    set_locale("en")
    print(f"English title: {get_text('templates.spec.title')}")

    # Test Korean
    set_locale("ko")
    print(f"Korean title: {get_text('templates.spec.title')}")

    # Test template translation
    template = "# {{locale:templates.spec.title}}: Test Feature"
    translated = translate_template(template)
    print(f"Translated template: {translated}")

    print("Basic tests completed successfully!")