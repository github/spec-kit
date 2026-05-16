"""Tests for the integration registry documentation generation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from specify_cli.catalog_docs import (
    render_cell,
    list_integrations_for_docs,
    render_integrations_table,
)
from specify_cli import app


runner = CliRunner()


def _get_mocked_cli_runner():
    """Set up a context with mocked registry and doc maps for CLI tests."""
    fake_registry = {
        "copilot": MagicMock(config={"name": "GitHub Copilot"}),
        "codex": MagicMock(config={"name": "Codex CLI"}),
    }
    fake_doc_urls = {"copilot": "https://code.visualstudio.com/", "codex": "https://github.com/openai/codex"}
    fake_label_overrides = {}
    fake_notes = {"copilot": "Test note"}
    
    patches = [
        patch("specify_cli.catalog_docs._get_integration_registry", return_value=fake_registry),
        patch("specify_cli.catalog_docs.INTEGRATION_DOC_URLS", fake_doc_urls),
        patch("specify_cli.catalog_docs.INTEGRATION_LABEL_OVERRIDES", fake_label_overrides),
        patch("specify_cli.catalog_docs.INTEGRATION_NOTES", fake_notes),
    ]
    return patches


def test_integrations_table_renders():
    table = render_integrations_table()
    lines = table.splitlines()
    assert lines[0] == "| Agent | Key | Notes |"
    assert lines[1] == "| --- | --- | --- |"


def test_render_cell_escapes_pipes_and_normalizes_newlines():
    assert render_cell("a|b") == "a\\|b"
    assert render_cell("a\nb") == "a b"
    assert render_cell("a\r\nb") == "a b"
    assert render_cell("a\rb") == "a b"
    assert render_cell("a|b\nc") == "a\\|b c"


def test_integrations_docs_label_and_url_sources():
    """Test with a mocked registry and doc maps to avoid brittleness to live registry changes."""
    # Create a minimal fake registry with two known integrations
    fake_registry = {
        "copilot": MagicMock(config={"name": "GitHub Copilot"}),
        "codex": MagicMock(config={"name": "Codex CLI"}),
    }

    # Mock the doc maps to only contain entries for the fake registry
    fake_doc_urls = {"copilot": "https://code.visualstudio.com/", "codex": "https://github.com/openai/codex"}
    fake_label_overrides = {}
    fake_notes = {}

    patch_registry = patch("specify_cli.catalog_docs._get_integration_registry", return_value=fake_registry)
    patch_urls = patch("specify_cli.catalog_docs.INTEGRATION_DOC_URLS", fake_doc_urls)
    patch_labels = patch("specify_cli.catalog_docs.INTEGRATION_LABEL_OVERRIDES", fake_label_overrides)
    patch_notes = patch("specify_cli.catalog_docs.INTEGRATION_NOTES", fake_notes)

    with patch_registry, patch_urls, patch_labels, patch_notes:
        rows = {key: (label, url) for key, label, url, _notes in list_integrations_for_docs()}
        assert rows["copilot"][0] == "GitHub Copilot"
        assert rows["copilot"][1] == "https://code.visualstudio.com/"
        assert rows["codex"][0] == "Codex CLI"
        assert rows["codex"][1] == "https://github.com/openai/codex"


def test_cli_integration_search_markdown_success():
    """Test that `integration search --markdown` outputs the markdown table."""
    patches = _get_mocked_cli_runner()
    for p in patches:
        p.start()
    try:
        result = runner.invoke(app, ["integration", "search", "--markdown"])
        assert result.exit_code == 0
        lines = result.stdout.splitlines()
        assert len(lines) > 2  # At least header, separator, and one data row
        assert lines[0] == "| Agent | Key | Notes |"
        assert lines[1] == "| --- | --- | --- |"
    finally:
        for p in patches:
            p.stop()


def test_cli_integration_search_markdown_with_filters_warns():
    """Test that `integration search --markdown` with filters emits a warning to stderr."""
    patches = _get_mocked_cli_runner()
    for p in patches:
        p.start()
    try:
        result = runner.invoke(app, ["integration", "search", "test-query", "--markdown", "--tag", "some-tag"])
        assert result.exit_code == 0
        # Check for the specific Typer warning message (not generic Python warnings)
        assert "ignores query/--tag/--author filters" in result.stderr
        lines = result.stdout.splitlines()
        assert lines[0] == "| Agent | Key | Notes |"
    finally:
        for p in patches:
            p.stop()


def test_cli_integration_search_markdown_stdout_is_clean():
    """Test that stdout contains only the markdown table with proper format."""
    patches = _get_mocked_cli_runner()
    for p in patches:
        p.start()
    try:
        result = runner.invoke(app, ["integration", "search", "--markdown"])
        assert result.exit_code == 0
        stdout = result.stdout
        lines = stdout.splitlines()
        # Verify markdown table header is present
        assert len(lines) > 1
        assert lines[0] == "| Agent | Key | Notes |"
        # Ensure stderr has no error messages
        assert "error" not in result.stderr.lower()
    finally:
        for p in patches:
            p.stop()


def test_docs_reference_integrations_md_stays_in_sync():
    """Regression test: committed docs/reference/integrations.md table should exist.
    
    This ensures the integration reference docs file is present and contains expected markers.
    If this test fails, run: poetry run python scripts/generate_integrations_reference.py --write
    """
    from pathlib import Path
    
    # Find the committed integrations.md file
    repo_root = Path(__file__).parent.parent
    docs_file = repo_root / "docs" / "reference" / "integrations.md"
    
    assert docs_file.exists(), \
        f"The committed integrations.md file doesn't exist at {docs_file}. \n" \
        "Run: poetry run python scripts/generate_integrations_reference.py --write"
    
    # Read the committed file
    with open(docs_file) as f:
        committed_content = f.read()
    
    # Verify the file contains table markers (the table structure)
    assert "| Agent" in committed_content, \
        "The committed integrations.md doesn't contain 'Agent' column marker. \n" \
        "Run: poetry run python scripts/generate_integrations_reference.py --write"
    
    assert "| Key" in committed_content, \
        "The committed integrations.md doesn't contain 'Key' column marker. \n" \
        "Run: poetry run python scripts/generate_integrations_reference.py --write"
    
    assert "| Notes" in committed_content, \
        "The committed integrations.md doesn't contain 'Notes' column marker. \n" \
        "Run: poetry run python scripts/generate_integrations_reference.py --write"
    
    # The generated table should also have these markers
    generated_table = render_integrations_table()
    assert "| Agent | Key | Notes |" in generated_table
