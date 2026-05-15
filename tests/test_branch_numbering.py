"""
Unit tests for branch numbering options (sequential vs timestamp).

Tests cover:
- Persisting branch_numbering in init-options.json
- Default value when branch_numbering is None
- Validation of branch_numbering values
"""

import json
from pathlib import Path

from specify_cli import save_init_options


class TestSaveBranchNumbering:
    """Tests for save_init_options with branch_numbering."""

    def test_save_branch_numbering_timestamp(self, tmp_path: Path):
        opts = {"branch_numbering": "timestamp", "ai": "claude"}
        save_init_options(tmp_path, opts)

        saved = json.loads((tmp_path / ".specify/init-options.json").read_text())
        assert saved["branch_numbering"] == "timestamp"

    def test_save_branch_numbering_sequential(self, tmp_path: Path):
        opts = {"branch_numbering": "sequential", "ai": "claude"}
        save_init_options(tmp_path, opts)

        saved = json.loads((tmp_path / ".specify/init-options.json").read_text())
        assert saved["branch_numbering"] == "sequential"

    def test_branch_numbering_defaults_to_sequential(self, tmp_path: Path):
        from typer.testing import CliRunner
        from specify_cli import app

        project_dir = tmp_path / "proj"
        runner = CliRunner()
        result = runner.invoke(app, ["init", str(project_dir), "--ai", "claude", "--ignore-agent-tools", "--no-git", "--script", "sh"])
        assert result.exit_code == 0

        saved = json.loads((project_dir / ".specify/init-options.json").read_text())
        assert saved["branch_numbering"] == "sequential"


class TestBranchNumberingValidation:
    """Tests for branch_numbering CLI validation via CliRunner."""

    def test_invalid_branch_numbering_rejected(self, tmp_path: Path):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["init", str(tmp_path / "proj"), "--ai", "claude", "--branch-numbering", "foobar", "--ignore-agent-tools"])
        assert result.exit_code == 1
        assert "Invalid --branch-numbering" in result.output

    def test_valid_branch_numbering_sequential(self, tmp_path: Path):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["init", str(tmp_path / "proj"), "--ai", "claude", "--branch-numbering", "sequential", "--ignore-agent-tools", "--no-git", "--script", "sh"])
        assert result.exit_code == 0
        assert "Invalid --branch-numbering" not in (result.output or "")

    def test_valid_branch_numbering_timestamp(self, tmp_path: Path):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["init", str(tmp_path / "proj"), "--ai", "claude", "--branch-numbering", "timestamp", "--ignore-agent-tools", "--no-git", "--script", "sh"])
        assert result.exit_code == 0
        assert "Invalid --branch-numbering" not in (result.output or "")
