"""Tests for the integration registry documentation generation."""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
import re
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from specify_cli.catalog_docs import (
    escape_url_for_markdown_link,
    escape_markdown_link_text,
    INTEGRATIONS_REFERENCE_PATH,
    render_cell,
    render_code_span,
    list_integrations_for_docs,
    render_integrations_table,
)
from specify_cli import app


runner = CliRunner()


@contextmanager
def _get_catalog_docs_patches(
    *,
    fake_registry=None,
    fake_doc_urls=None,
    fake_label_overrides=None,
    fake_notes=None,
):
    """Context manager that applies mocked registry and doc maps for tests."""

    if fake_registry is None:
        fake_registry = {
            "copilot": MagicMock(config={"name": "GitHub Copilot"}),
            "codex": MagicMock(config={"name": "Codex CLI"}),
        }
    if fake_doc_urls is None:
        fake_doc_urls = {
            "copilot": "https://code.visualstudio.com/",
            "codex": "https://github.com/openai/codex",
        }
    if fake_label_overrides is None:
        fake_label_overrides = {}
    if fake_notes is None:
        fake_notes = {"copilot": "Test note"}

    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "specify_cli.catalog_docs._get_integration_registry",
                return_value=fake_registry,
            )
        )
        stack.enter_context(
            patch("specify_cli.catalog_docs.INTEGRATION_DOC_URLS", fake_doc_urls)
        )
        stack.enter_context(
            patch(
                "specify_cli.catalog_docs.INTEGRATION_LABEL_OVERRIDES",
                fake_label_overrides,
            )
        )
        stack.enter_context(
            patch("specify_cli.catalog_docs.INTEGRATION_NOTES", fake_notes)
        )
        yield


def test_integrations_table_renders():
    table = render_integrations_table()
    lines = table.splitlines()
    assert lines[0] == "| Agent | Key | Notes |"
    assert lines[1] == "| --- | --- | --- |"


def test_integrations_reference_doc_matches_renderer():
    if not INTEGRATIONS_REFERENCE_PATH.exists():
        pytest.skip(
            f"Integrations reference not found at {INTEGRATIONS_REFERENCE_PATH}. "
            "Skipping (expected when running from sdist/wheel)."
        )
    doc_text = INTEGRATIONS_REFERENCE_PATH.read_text(encoding="utf-8")
    start_marker = "## Supported AI Coding Agents\n\n"
    end_marker = "\n## List Available Integrations\n"
    start = doc_text.index(start_marker) + len(start_marker)
    end = doc_text.index(end_marker)
    committed_table = doc_text[start:end].rstrip("\n")
    rendered_table = render_integrations_table().rstrip("\n")

    def parse_table(table: str) -> list[list[str]]:
        rows: list[list[str]] = []
        for line in table.splitlines():
            if not line.startswith("| "):
                continue
            parts = [part.strip() for part in re.split(r"(?<!\\)\|", line.strip("|"))]
            if parts and set(parts[0]) == {"-"}:
                continue
            if len(parts) == 3:
                rows.append(parts)
        return rows

    committed_rows = parse_table(committed_table)
    rendered_rows = parse_table(rendered_table)
    committed_rows.sort(key=lambda row: row[1])
    rendered_rows.sort(key=lambda row: row[1])

    assert committed_rows == rendered_rows


def test_render_cell_escapes_pipes_and_normalizes_newlines():
    assert render_cell("a|b") == "a\\|b"
    assert render_cell("a\nb") == "a b"
    assert render_cell("a\r\nb") == "a b"
    assert render_cell("a\rb") == "a b"
    assert render_cell("a|b\nc") == "a\\|b c"


def test_escape_url_for_markdown_link():
    """Test that URLs with special characters are properly escaped for Markdown links."""
    # URLs containing ) and | should be escaped
    assert escape_url_for_markdown_link("https://example.com/path)") == (
        "https://example.com/path\\)"
    )
    assert escape_url_for_markdown_link("https://example.com/path|query") == (
        "https://example.com/path\\|query"
    )
    assert escape_url_for_markdown_link("https://example.com/path)|query") == (
        "https://example.com/path\\)\\|query"
    )
    # URLs without special characters should be unchanged
    assert escape_url_for_markdown_link("https://example.com/path") == (
        "https://example.com/path"
    )


def test_escape_markdown_link_text():
    assert escape_markdown_link_text("Code [Buddy]") == "Code \\[Buddy\\]"

def test_render_code_span_preserves_backticks():
    assert render_code_span("alpha`beta") == "``alpha`beta``"


def test_integrations_docs_label_and_url_sources():
    """Test using mocked registry/doc maps to avoid test brittleness."""
    with _get_catalog_docs_patches(fake_notes={}):
        rows = {
            key: (label, url)
            for key, label, url, _notes in list_integrations_for_docs()
        }
        assert rows["copilot"][0] == "GitHub Copilot"
        assert rows["copilot"][1] == "https://code.visualstudio.com/"
        assert rows["codex"][0] == "Codex CLI"
        assert rows["codex"][1] == "https://github.com/openai/codex"


def test_cli_integration_search_markdown_success():
    """Test that `integration search --markdown` outputs the markdown table."""
    with _get_catalog_docs_patches():
        result = runner.invoke(app, ["integration", "search", "--markdown"])
        assert result.exit_code == 0
        lines = result.stdout.splitlines()
        assert len(lines) > 2  # At least header, separator, and one data row
        assert lines[0] == "| Agent | Key | Notes |"
        assert lines[1] == "| --- | --- | --- |"


def test_render_integrations_table_escapes_link_text():
    fake_registry = {
        "bracket": MagicMock(config={"name": "Code [Buddy]"}),
    }
    fake_doc_urls = {
        "bracket": "https://example.com/docs",
    }

    with _get_catalog_docs_patches(
        fake_registry=fake_registry,
        fake_doc_urls=fake_doc_urls,
        fake_notes={},
    ):
        table = render_integrations_table()

    assert "[Code \\[Buddy\\]](https://example.com/docs)" in table


def test_cli_integration_search_markdown_with_filters_warns():
    """Test that `integration search --markdown` with filters warns."""
    with _get_catalog_docs_patches():
        result = runner.invoke(
            app,
            [
                "integration",
                "search",
                "test-query",
                "--markdown",
                "--tag",
                "some-tag",
            ],
        )
        assert result.exit_code == 0
        # Check for the specific Typer warning message
        assert "ignores query/--tag/--author filters" in result.stderr
        lines = result.stdout.splitlines()
        assert lines[0] == "| Agent | Key | Notes |"


def test_cli_integration_search_markdown_stdout_is_clean():
    """Test that stdout contains only the markdown table with proper format."""
    with _get_catalog_docs_patches():
        result = runner.invoke(app, ["integration", "search", "--markdown"])
        assert result.exit_code == 0
        stdout = result.stdout
        lines = stdout.splitlines()
        # Verify markdown table header is present
        assert len(lines) > 1
        assert lines[0] == "| Agent | Key | Notes |"
        # Ensure stderr has no error messages
        assert "error" not in result.stderr.lower()
