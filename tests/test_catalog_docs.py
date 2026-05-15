"""Tests for the integration registry documentation generation."""

from __future__ import annotations

from specify_cli.catalog_docs import list_integrations_for_docs, render_integrations_table


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
