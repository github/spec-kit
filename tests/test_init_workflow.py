"""Tests for --workflow flag on specify init."""

import os

import yaml


class TestInitWorkflowFlag:
    """Tests for the --workflow option on specify init."""

    def test_workflow_flag_missing_file_errors(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        project = tmp_path / "wf-test"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "init", "--here", "--integration", "copilot",
                "--script", "sh", "--no-git",
                "--workflow", str(tmp_path / "nonexistent.yml"),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Workflow file not found" in result.output

    def test_workflow_flag_runs_workflow_after_init(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        project = tmp_path / "wf-run-test"
        project.mkdir()

        # Create a minimal workflow YAML that runs a simple shell step
        workflow_file = tmp_path / "post-init.yml"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "post-init-test",
                "name": "Post Init Test",
                "version": "1.0.0",
                "description": "A test post-init workflow",
            },
            "steps": [
                {
                    "id": "create-marker",
                    "type": "shell",
                    "run": "echo done > marker.txt",
                },
            ],
        }
        workflow_file.write_text(yaml.dump(workflow_content), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "init", "--here", "--integration", "copilot",
                "--script", "sh", "--no-git",
                "--workflow", str(workflow_file),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        assert "Running post-init workflow" in result.output
        assert "Workflow status: completed" in result.output
        # The shell step should have created the marker file
        assert (project / "marker.txt").exists()

    def test_workflow_flag_failing_workflow_exits_nonzero(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        project = tmp_path / "wf-fail-test"
        project.mkdir()

        # Create a workflow that fails
        workflow_file = tmp_path / "bad-workflow.yml"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "bad-wf",
                "name": "Bad Workflow",
                "version": "1.0.0",
                "description": "A failing workflow",
            },
            "steps": [
                {
                    "id": "fail-step",
                    "type": "shell",
                    "run": "exit 1",
                },
            ],
        }
        workflow_file.write_text(yaml.dump(workflow_content), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "init", "--here", "--integration", "copilot",
                "--script", "sh", "--no-git",
                "--workflow", str(workflow_file),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0

    def test_init_without_workflow_flag_works_normally(self, tmp_path):
        """Ensure that omitting --workflow does not change existing behavior."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        project = tmp_path / "no-wf-test"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "init", "--here", "--integration", "copilot",
                "--script", "sh", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        assert "Running post-init workflow" not in result.output
