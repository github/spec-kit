"""Command-focused workflow tests."""

from __future__ import annotations

import json

import pytest



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

    def test_enable_failed_save_leaves_workflow_disabled(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)
        result = runner.invoke(app, ["workflow", "disable", "align-wf"])
        assert result.exit_code == 0, result.output

        def boom(self):
            raise OSError("disk full")

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(WorkflowRegistry, "save", boom)
            result = runner.invoke(app, ["workflow", "enable", "align-wf"])
            assert result.exit_code != 0

        assert WorkflowRegistry(project_dir).get("align-wf")["enabled"] is False
        result = runner.invoke(app, ["workflow", "enable", "align-wf"])
        assert result.exit_code == 0, result.output
        assert WorkflowRegistry(project_dir).get("align-wf")["enabled"] is True

    @pytest.mark.parametrize("command", ["enable", "disable"])
    def test_enable_disable_save_failure_gives_clean_output(
        self, project_dir, monkeypatch, command
    ):
        """A save() failure in enable/disable must produce a clean escaped CLI
        error, not surface the raw OSError as an unhandled exception. Shared
        root behavior: both call registry.add() with a fresh mapping and must
        catch its deliberate OSError the same way."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)
        # disable starts from the enabled default; enable needs a prior disable.
        starting_enabled = command == "disable"
        if command == "enable":
            pre = runner.invoke(app, ["workflow", "disable", "align-wf"])
            assert pre.exit_code == 0, pre.output

        def boom(self):
            raise OSError("disk full")

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(WorkflowRegistry, "save", boom)
            result = runner.invoke(app, ["workflow", command, "align-wf"])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert result.output.strip() != ""
        assert (
            WorkflowRegistry(project_dir).get("align-wf").get("enabled", True)
            is starting_enabled
        )

    def test_enable_disable_corrupted_registry_entry_errors(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        registry_path = WorkflowRegistry(project_dir).registry_path
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps({"schema_version": "1.0", "workflows": {"broken": "not-a-dict"}}),
            encoding="utf-8",
        )
        runner = CliRunner()
        for cmd in ("enable", "disable"):
            result = runner.invoke(app, ["workflow", cmd, "broken"])
            assert result.exit_code != 0
            assert "corrupted" in result.output

    def test_enable_disable_not_installed_errors(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        for cmd in ("enable", "disable"):
            result = runner.invoke(app, ["workflow", cmd, "ghost"])
            assert result.exit_code != 0
            assert "not installed" in result.output

    def test_enable_disable_idempotent_warnings(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)

        result = runner.invoke(app, ["workflow", "enable", "align-wf"])
        assert result.exit_code == 0
        assert "already enabled" in result.output

        runner.invoke(app, ["workflow", "disable", "align-wf"])
        result = runner.invoke(app, ["workflow", "disable", "align-wf"])
        assert result.exit_code == 0
        assert "already disabled" in result.output
