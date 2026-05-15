"""Tests for the integration registry documentation generation."""

from __future__ import annotations

from specify_cli.catalog_docs import (
    INTEGRATIONS_REFERENCE_PATH,
    list_integrations_for_docs,
    render_integrations_table,
)


def test_integrations_table_renders():
    table = render_integrations_table()
    assert "| Agent" in table
    assert "| Key" in table
    assert "| Notes" in table


def test_integrations_reference_label_derives_from_registry_url_from_doc_map():
    rows = {key: (label, url) for key, label, url, _notes in list_integrations_for_docs()}
    assert rows["copilot"][0] == "GitHub Copilot"
    assert rows["copilot"][1] == "https://code.visualstudio.com/"
    assert rows["codex"][0] == "Codex CLI"
    assert rows["codex"][1] == "https://github.com/openai/codex"


def test_integrations_reference_doc_is_in_sync():
    """Committed docs/reference/integrations.md must contain the rendered table."""
    expected_table = render_integrations_table()
    content = INTEGRATIONS_REFERENCE_PATH.read_text(encoding="utf-8")
    assert expected_table in content, (
        "docs/reference/integrations.md is out of sync with the integration registry. "
        "Re-run `specify integration search --markdown` and update the file."
    )
