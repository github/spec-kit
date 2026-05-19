"""Tests for the integration registry documentation generation."""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from specify_cli.catalog_docs import (
    escape_url_for_markdown_link,
    render_cell,
    list_integrations_for_docs,
    render_integrations_table,
)
from specify_cli import app


runner = CliRunner()


@contextmanager
def _get_catalog_docs_patches():
    """Context manager that applies mocked registry and doc maps for tests."""

    fake_registry = {
        "copilot": MagicMock(config={"name": "GitHub Copilot"}),
        "codex": MagicMock(config={"name": "Codex CLI"}),
    }
    fake_doc_urls = {
        "copilot": "https://code.visualstudio.com/",
        "codex": "https://github.com/openai/codex",
    }
    fake_label_overrides = {}
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


def test_integrations_docs_label_and_url_sources():
    """Test using mocked registry/doc maps to avoid test brittleness."""
    # Create a minimal fake registry with two known integrations
    fake_registry = {
        "copilot": MagicMock(config={"name": "GitHub Copilot"}),
        "codex": MagicMock(config={"name": "Codex CLI"}),
    }

    # Mock the doc maps to only contain entries for the fake registry
    fake_doc_urls = {
        "copilot": "https://code.visualstudio.com/",
        "codex": "https://github.com/openai/codex",
    }
    fake_label_overrides = {}
    fake_notes = {}

    patch_registry = patch(
        "specify_cli.catalog_docs._get_integration_registry",
        return_value=fake_registry,
    )
    patch_urls = patch(
        "specify_cli.catalog_docs.INTEGRATION_DOC_URLS", fake_doc_urls
    )
    patch_labels = patch(
        "specify_cli.catalog_docs.INTEGRATION_LABEL_OVERRIDES",
        fake_label_overrides,
    )
    patch_notes = patch(
        "specify_cli.catalog_docs.INTEGRATION_NOTES", fake_notes
    )

    with patch_registry, patch_urls, patch_labels, patch_notes:
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


def test_docs_reference_integrations_md_stays_in_sync():
    """Regression test: committed docs/reference/integrations.md stays in sync.
    
    This ensures that the integration reference docs file contains the exact
    list of integrations defined in the registry.
    If this test fails, run: specify integration search --markdown
    and update the table in docs/reference/integrations.md accordingly.
    """
    import pytest
    from pathlib import Path
    
    # Find the committed integrations.md file
    repo_root = Path(__file__).parent.parent
    docs_file = repo_root / "docs" / "reference" / "integrations.md"
    
    if not docs_file.exists():
        pytest.skip(
            f"Integration reference docs not found at {docs_file}. "
            "Skipping sync test (expected in CI, acceptable in isolated "
            "test environments)."
        )
    
    # Read the committed file with explicit UTF-8 encoding
    with open(docs_file, encoding="utf-8") as f:
        committed_content = f.read()
    
    # Extract rows from the H2 section ## Supported AI Coding Agents
    def parse_first_markdown_table(text: str) -> set[tuple[str, str, str]]:
        """Parse the first markdown table in a section, respecting escaped pipes."""
        lines = text.splitlines()
        in_target_section = False
        in_table = False
        rows = []

        def split_markdown_table_row(line: str) -> list[str]:
            parts = []
            current = ""
            backslash_run = 0
            for char in line:
                if char == "\\":
                    backslash_run += 1
                    current += char
                    continue
                if char == "|" and backslash_run % 2 == 0:
                    parts.append(current.strip())
                    current = ""
                else:
                    current += char
                backslash_run = 0
            parts.append(current.strip())
            if parts and parts[0] == "":
                parts = parts[1:]
            if parts and parts[-1] == "":
                parts = parts[:-1]
            return parts

        for line in lines:
            if line.startswith("## Supported AI Coding Agents"):
                in_target_section = True
                continue
            if in_target_section:
                if line.startswith("## "):
                    break
                if line.strip().startswith("|"):
                    in_table = True
                    parts = split_markdown_table_row(line)

                    if (
                        all(p.startswith("---") or p == "" for p in parts)
                        or parts == ["Agent", "Key", "Notes"]
                    ):
                        continue
                    
                    # Validate we have 3 columns
                    assert (
                        len(parts) == 3
                    ), f"Malformed row in integrations.md: {line!r} (expected 3 columns, got {len(parts)})"
                    
                    rows.append((parts[0], parts[1], parts[2]))
                elif in_table:
                    break
        return set(rows)

    def parse_markdown_table_rows(text: str) -> set[tuple[str, str, str]]:
        """Parse markdown table rows, respecting escaped pipes."""
        rows = []

        def split_markdown_table_row(line: str) -> list[str]:
            parts = []
            current = ""
            backslash_run = 0
            for char in line:
                if char == "\\":
                    backslash_run += 1
                    current += char
                    continue
                if char == "|" and backslash_run % 2 == 0:
                    parts.append(current.strip())
                    current = ""
                else:
                    current += char
                backslash_run = 0
            parts.append(current.strip())
            if parts and parts[0] == "":
                parts = parts[1:]
            if parts and parts[-1] == "":
                parts = parts[:-1]
            return parts

        for line in text.splitlines():
            if not line.strip().startswith("|"):
                continue

            parts = split_markdown_table_row(line)

            # Skip header and separator rows
            if (
                all(p.startswith("---") or p == "" for p in parts)
                or parts == ["Agent", "Key", "Notes"]
            ):
                continue
            
            # Validate we have the expected 3 columns
            if len(parts) != 3:
                continue
            
            rows.append((parts[0], parts[1], parts[2]))
        return set(rows)

    committed_rows = parse_first_markdown_table(committed_content)
    generated_table = render_integrations_table()
    generated_rows = parse_markdown_table_rows(generated_table)

    # Assert they are in perfect sync
    diff_missing = generated_rows - committed_rows
    diff_extra = committed_rows - generated_rows

    error_msg = (
        "The committed integrations.md table is out of sync with the registry.\n"
        f"Missing from docs: {diff_missing}\n"
        f"Extra in docs: {diff_extra}\n"
        "To update the docs table, run: specify integration search --markdown"
    )
    assert not diff_missing and not diff_extra, error_msg
