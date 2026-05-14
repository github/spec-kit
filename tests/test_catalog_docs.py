"""Tests for catalog-backed documentation generation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from specify_cli.catalog_docs import _iter_integrations_for_docs, render_integrations_reference


def test_integrations_reference_matches_generator():
    doc_path = Path("docs/reference/integrations.md")
    assert doc_path.read_text(encoding="utf-8") == render_integrations_reference()


def test_integrations_reference_generator_check_mode():
    result = subprocess.run(
        [sys.executable, "scripts/generate_integrations_reference.py", "--check"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_integrations_reference_rows_follow_registry_metadata():
    rows = dict((key, (label, url)) for key, label, url, _notes in _iter_integrations_for_docs())
    assert rows["copilot"][0] == "GitHub Copilot"
    assert rows["copilot"][1] == "https://code.visualstudio.com/"
    assert rows["codex"][0] == "Codex CLI"
    assert rows["codex"][1] == "https://github.com/openai/codex"
