"""Tests for the integration registry documentation generation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from specify_cli.catalog_docs import (
    render_cell,
    list_integrations_for_docs,
    render_integrations_table,
)


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

    with (
        patch("specify_cli.catalog_docs._get_integration_registry", return_value=fake_registry),
        patch("specify_cli.catalog_docs.INTEGRATION_DOC_URLS", fake_doc_urls),
        patch("specify_cli.catalog_docs.INTEGRATION_LABEL_OVERRIDES", fake_label_overrides),
        patch("specify_cli.catalog_docs.INTEGRATION_NOTES", fake_notes),
    ):
        rows = {key: (label, url) for key, label, url, _notes in list_integrations_for_docs()}
        assert rows["copilot"][0] == "GitHub Copilot"
        assert rows["copilot"][1] == "https://code.visualstudio.com/"
        assert rows["codex"][0] == "Codex CLI"
        assert rows["codex"][1] == "https://github.com/openai/codex"
