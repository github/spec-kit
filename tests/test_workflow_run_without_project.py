"""Tests for running workflow YAML files without a project."""

import os

import yaml


class TestWorkflowRunWithoutProject:
    """Tests that specify workflow run works with YAML files without .specify/ dir."""

    def test_workflow_run_yaml_without_project(self, tmp_path):
        """Running a .yml file should work without a .specify/ directory."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        # Create a minimal workflow YAML with a shell step
        workflow_file = tmp_path / "test-workflow.yml"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "standalone-test",
                "name": "Standalone Test",
                "version": "1.0.0",
                "description": "A workflow that runs without a project",
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
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", str(workflow_file),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"workflow run failed: {result.output}"
        assert "completed" in result.output
        assert (tmp_path / "marker.txt").exists()
        assert (tmp_path / ".specify" / "workflows" / "runs").is_dir()

    def test_workflow_run_yaml_with_tilde_and_uppercase_suffix(self, tmp_path, monkeypatch):
        """Running ~/file.YML should work without a .specify/ directory."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        home_dir = tmp_path / "home"
        home_dir.mkdir()
        monkeypatch.setenv("HOME", str(home_dir))
        monkeypatch.setenv("USERPROFILE", str(home_dir))

        workflow_file = home_dir / "test-workflow.YML"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "standalone-test-uppercase",
                "name": "Standalone Test Uppercase",
                "version": "1.0.0",
                "description": "A workflow that runs from ~/ with an uppercase suffix",
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
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", "~/test-workflow.YML",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"workflow run failed: {result.output}"
        assert "Status: completed" in result.output
        assert (tmp_path / "marker.txt").exists()

    def test_workflow_run_id_still_requires_project(self, tmp_path):
        """Running a workflow by ID should still require a .specify/ directory."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", "some-workflow-id",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Not a spec-kit project" in result.output

    def test_workflow_run_missing_yaml_file(self, tmp_path):
        """Running a non-existent .yml file should still require a project."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", "nonexistent.yml",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        # non-existent .yml files fall through to project check or file-not-found
        assert result.exit_code != 0

    def test_workflow_run_failing_yaml_without_project(self, tmp_path):
        """A failing workflow YAML should report failure status."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        workflow_file = tmp_path / "fail-workflow.yml"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "fail-test",
                "name": "Fail Test",
                "version": "1.0.0",
                "description": "A workflow that fails",
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
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", str(workflow_file),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"workflow run failed unexpectedly: {result.output}"
        assert "Status: failed" in result.output
