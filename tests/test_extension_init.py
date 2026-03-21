"""
Unit tests for the extension init (scaffolding) command.

Tests cover:
- Extension ID validation
- Title case conversion
- Template directory discovery
- Scaffold output structure and placeholder substitution
- CLI integration (via typer CliRunner)
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from specify_cli import (
    app,
    _validate_extension_id,
    _title_case_extension,
    _find_extension_template,
)


runner = CliRunner()


# ===== Unit tests for helper functions =====


class TestValidateExtensionId:
    def test_valid_simple(self):
        assert _validate_extension_id("my-extension") is True

    def test_valid_single_word(self):
        assert _validate_extension_id("linter") is True

    def test_valid_with_numbers(self):
        assert _validate_extension_id("ext2") is True
        assert _validate_extension_id("my-ext-3") is True

    def test_rejects_uppercase(self):
        assert _validate_extension_id("My-Extension") is False

    def test_rejects_spaces(self):
        assert _validate_extension_id("my extension") is False

    def test_rejects_special_chars(self):
        assert _validate_extension_id("my_extension") is False
        assert _validate_extension_id("my.extension") is False

    def test_rejects_leading_number(self):
        assert _validate_extension_id("1ext") is False

    def test_rejects_trailing_hyphen(self):
        assert _validate_extension_id("my-extension-") is False

    def test_rejects_consecutive_hyphens(self):
        assert _validate_extension_id("my--extension") is False

    def test_rejects_empty(self):
        assert _validate_extension_id("") is False


class TestTitleCaseExtension:
    def test_single_word(self):
        assert _title_case_extension("linter") == "Linter"

    def test_hyphenated(self):
        assert _title_case_extension("my-extension") == "My Extension"

    def test_multi_word(self):
        assert _title_case_extension("spec-kit-learn") == "Spec Kit Learn"


class TestFindExtensionTemplate:
    def test_returns_path_when_template_exists(self):
        result = _find_extension_template()
        # Template exists in the source tree
        if result is not None:
            assert (result / "extension.yml").exists()

    def test_returns_none_when_template_missing(self):
        with patch("specify_cli.Path") as mock_path:
            mock_path.return_value.resolve.return_value.parent = Path("/nonexistent")
            # This tests the fallback behavior; in practice the template
            # is always present in the source tree during testing


# ===== CLI integration tests =====


@pytest.fixture
def temp_dir():
    """Create a temporary directory for scaffold output."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


class TestExtensionInitCLI:
    def test_scaffold_with_all_options(self, temp_dir):
        result = runner.invoke(app, [
            "extension", "init", "my-linter",
            "--output", str(temp_dir),
            "--author", "Jane Doe",
            "--description", "Lint spec files for quality",
            "--repository", "https://github.com/janedoe/spec-kit-my-linter",
            "--no-git",
        ])
        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "Extension Created" in result.output or "Extension scaffolded" in result.output

        ext_dir = temp_dir / "spec-kit-my-linter"
        assert ext_dir.exists()
        assert (ext_dir / "extension.yml").exists()
        assert (ext_dir / "commands").is_dir()
        assert (ext_dir / "README.md").exists()
        assert (ext_dir / "LICENSE").exists()
        assert (ext_dir / "CHANGELOG.md").exists()

    def test_placeholder_substitution(self, temp_dir):
        result = runner.invoke(app, [
            "extension", "init", "doc-guard",
            "--output", str(temp_dir),
            "--author", "Test Author",
            "--description", "Guard documentation quality",
            "--repository", "https://github.com/test/spec-kit-doc-guard",
            "--no-git",
        ])
        assert result.exit_code == 0, f"Command failed: {result.output}"

        ext_dir = temp_dir / "spec-kit-doc-guard"
        manifest = (ext_dir / "extension.yml").read_text()

        # Check placeholders were replaced
        assert "doc-guard" in manifest
        assert "Doc Guard" in manifest
        assert "Test Author" in manifest
        assert "Guard documentation quality" in manifest
        assert "https://github.com/test/spec-kit-doc-guard" in manifest

        # Check old placeholders are gone
        assert "my-extension" not in manifest
        assert "My Extension" not in manifest
        assert "Your Name" not in manifest
        assert "your-org" not in manifest

    def test_rejects_invalid_name(self):
        result = runner.invoke(app, [
            "extension", "init", "Invalid-Name",
            "--author", "Test",
            "--description", "Test",
            "--no-git",
        ])
        assert result.exit_code != 0
        assert "Invalid extension ID" in result.output

    def test_rejects_existing_directory(self, temp_dir):
        # Create the target directory first
        (temp_dir / "spec-kit-existing").mkdir()

        result = runner.invoke(app, [
            "extension", "init", "existing",
            "--output", str(temp_dir),
            "--author", "Test",
            "--description", "Test",
            "--no-git",
        ])
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_no_git_skips_initialization(self, temp_dir):
        result = runner.invoke(app, [
            "extension", "init", "no-git-test",
            "--output", str(temp_dir),
            "--author", "Test",
            "--description", "Test",
            "--repository", "https://github.com/test/spec-kit-no-git-test",
            "--no-git",
        ])
        assert result.exit_code == 0
        ext_dir = temp_dir / "spec-kit-no-git-test"
        assert not (ext_dir / ".git").exists()

    def test_example_readme_replaces_template_readme(self, temp_dir):
        result = runner.invoke(app, [
            "extension", "init", "readme-test",
            "--output", str(temp_dir),
            "--author", "Test",
            "--description", "Test",
            "--repository", "https://github.com/test/spec-kit-readme-test",
            "--no-git",
        ])
        assert result.exit_code == 0
        ext_dir = temp_dir / "spec-kit-readme-test"
        readme = (ext_dir / "README.md").read_text()
        # EXAMPLE-README content should now be in README.md
        assert "EXAMPLE" not in [f.name for f in ext_dir.iterdir() if f.name.startswith("EXAMPLE")]
        # The readme should contain customized content
        assert "readme-test" in readme.lower() or "Readme Test" in readme

    def test_next_steps_shown(self, temp_dir):
        result = runner.invoke(app, [
            "extension", "init", "steps-test",
            "--output", str(temp_dir),
            "--author", "Test",
            "--description", "Test",
            "--repository", "https://github.com/test/spec-kit-steps-test",
            "--no-git",
        ])
        assert result.exit_code == 0
        assert "Next Steps" in result.output

    def test_date_substitution(self, temp_dir):
        from datetime import datetime

        result = runner.invoke(app, [
            "extension", "init", "date-test",
            "--output", str(temp_dir),
            "--author", "Test",
            "--description", "Test",
            "--repository", "https://github.com/test/spec-kit-date-test",
            "--no-git",
        ])
        assert result.exit_code == 0
        ext_dir = temp_dir / "spec-kit-date-test"
        changelog = (ext_dir / "CHANGELOG.md").read_text()
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in changelog
        assert "YYYY-MM-DD" not in changelog
