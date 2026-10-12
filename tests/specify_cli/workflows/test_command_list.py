"""Command-focused workflow tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest



class TestWorkflowAddSymlinkGuard:
    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_list_refuses_symlinked_runs_dir(self, temp_dir, monkeypatch):
        """workflow commands using the project shim must refuse symlinked run storage."""
        from typer.testing import CliRunner
        from specify_cli import app

        (temp_dir / ".specify" / "workflows").mkdir(parents=True)
        outside = temp_dir.parent / "outside-runs-target"
        outside.mkdir(parents=True, exist_ok=True)
        (temp_dir / ".specify" / "workflows" / "runs").symlink_to(
            outside, target_is_directory=True
        )

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "list"])

        assert result.exit_code != 0
        assert "symlinked .specify/workflows/runs" in result.output



class TestWorkflowCliAlignment:
    """CLI alignment with extension/preset commands (#2342)."""

    WORKFLOW_YAML = """
schema_version: "1.0"
workflow:
  id: "align-wf"
  name: "Align Workflow"
  version: "{version}"
  description: "CLI alignment test workflow"
steps:
  - id: step-one
    type: shell
    run: "echo hello"
"""

    def _write_workflow_dir(self, base, version="1.0.0"):
        d = base / "wf-src"
        d.mkdir(parents=True, exist_ok=True)
        (d / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version=version), encoding="utf-8"
        )
        return d

    def _install_dev(self, runner, app, project_dir):
        src = self._write_workflow_dir(project_dir)
        result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])
        assert result.exit_code == 0, result.output
        return src

    def test_list_skips_corrupted_registry_entry(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        registry_path = WorkflowRegistry(project_dir).registry_path
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "workflows": {
                        "broken": "not-a-dict",
                        "ok": {"name": "OK Workflow", "version": "1.0.0"},
                    },
                }
            ),
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "list"])
        assert result.exit_code == 0, result.output
        assert "corrupted" in result.output
        assert "OK Workflow" in result.output

    def test_list_unreadable_registry_fails_closed_with_clean_error(
        self, project_dir, monkeypatch
    ):
        """An unreadable registry file must produce a clean CLI error, not a
        raw traceback and not a silent "nothing installed" list -- the latter
        is exactly the fail-open state a caller could otherwise mistake for
        "safe to (re)install", overwriting real files. Covers the read/query
        boundary fix required at every WorkflowRegistry call site."""
        import builtins
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)

        registry_path = WorkflowRegistry(project_dir).registry_path.resolve()
        real_open = builtins.open

        def _raising_open(file, mode="r", *args, **kwargs):
            if Path(file).resolve() == registry_path and "r" in mode:
                raise OSError("simulated read failure")
            return real_open(file, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _raising_open)
        result = runner.invoke(app, ["workflow", "list"])
        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Error" in result.output

    def test_list_escapes_rich_markup_in_registry_fields(self, project_dir, monkeypatch):
        """User-editable name/description/id fields must not be parsed as Rich markup."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        registry_path = WorkflowRegistry(project_dir).registry_path
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "workflows": {
                        "ok": {
                            "name": "Bracket [Test]",
                            "version": "1.0.0",
                            "description": "desc [with] brackets",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "list"])
        assert result.exit_code == 0, result.output
        assert "Bracket [Test]" in result.output
        assert "desc [with] brackets" in result.output
