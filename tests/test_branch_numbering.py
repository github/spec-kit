"""
Unit tests verifying --branch-numbering removal (v0.10.0).

Branch numbering is now managed entirely by the git extension's config.
The --branch-numbering flag was removed from `specify init`.
"""

from pathlib import Path


class TestBranchNumberingFlagRemoved:
    """--branch-numbering flag was removed in v0.10.0."""

    def test_branch_numbering_flag_is_rejected(self, tmp_path: Path):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        result = runner.invoke(app, [
            "init", str(tmp_path / "proj"), "--integration", "claude",
            "--branch-numbering", "sequential", "--ignore-agent-tools",
        ])
        assert result.exit_code != 0, "--branch-numbering should be rejected"
        assert "No such option" in result.output or "no such option" in result.output.lower()
