"""Tests for the integration registry documentation generation."""

from __future__ import annotations

from specify_cli.catalog_docs import render_cell, list_integrations_for_docs, render_integrations_table


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
    rows = {key: (label, url) for key, label, url, _notes in list_integrations_for_docs()}
    assert rows["copilot"][0] == "GitHub Copilot"
    assert rows["copilot"][1] == "https://code.visualstudio.com/"
    assert rows["codex"][0] == "Codex CLI"
    assert rows["codex"][1] == "https://github.com/openai/codex"
