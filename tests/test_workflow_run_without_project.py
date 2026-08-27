"""Tests for running workflow YAML files without a project."""

import os

import pytest
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
        assert "Not a Spec Kit project" in result.output

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
        # A failed workflow now maps to a non-zero process exit code so
        # scripts and CI can rely on $? (the CLI itself still ran fine).
        assert result.exit_code == 1, f"expected exit 1 on failed run: {result.output}"
        assert "Status: failed" in result.output

    def test_workflow_run_yaml_rejects_symlinked_specify_dir(self, tmp_path):
        """Running local YAML should fail when .specify is a symlink."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        workflow_file = tmp_path / "test-workflow.yml"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "symlink-test",
                "name": "Symlink Test",
                "version": "1.0.0",
                "description": "A workflow for symlink guard testing",
            },
            "steps": [{"id": "noop", "type": "shell", "run": "echo done"}],
        }
        workflow_file.write_text(yaml.dump(workflow_content), encoding="utf-8")

        target_dir = tmp_path / "real-specify-dir"
        target_dir.mkdir()
        try:
            (tmp_path / ".specify").symlink_to(target_dir, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks are not available in this environment")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", str(workflow_file),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        assert "Refusing to use symlinked .specify path" in result.output

    def test_workflow_run_yaml_rejects_symlinked_workflows_dir(self, tmp_path):
        """Running local YAML should fail when .specify/workflows is a symlink."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        workflow_file = tmp_path / "test-workflow.yml"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "symlink-workflows-test",
                "name": "Symlink Workflows Test",
                "version": "1.0.0",
                "description": "A workflow for symlink guard testing",
            },
            "steps": [{"id": "noop", "type": "shell", "run": "echo done"}],
        }
        workflow_file.write_text(yaml.dump(workflow_content), encoding="utf-8")

        (tmp_path / ".specify").mkdir()
        target_dir = tmp_path / "real-workflows-dir"
        target_dir.mkdir()
        try:
            (tmp_path / ".specify" / "workflows").symlink_to(
                target_dir, target_is_directory=True
            )
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks are not available in this environment")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", str(workflow_file),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        assert "Refusing to use symlinked .specify/workflows path" in result.output

    def test_workflow_run_yaml_rejects_symlinked_runs_dir(self, tmp_path):
        """Running local YAML should fail when .specify/workflows/runs is a symlink."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        workflow_file = tmp_path / "test-workflow.yml"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "symlink-runs-test",
                "name": "Symlink Runs Test",
                "version": "1.0.0",
                "description": "A workflow for symlink guard testing",
            },
            "steps": [{"id": "noop", "type": "shell", "run": "echo done"}],
        }
        workflow_file.write_text(yaml.dump(workflow_content), encoding="utf-8")

        (tmp_path / ".specify" / "workflows").mkdir(parents=True)
        target_dir = tmp_path / "real-runs-dir"
        target_dir.mkdir()
        try:
            (tmp_path / ".specify" / "workflows" / "runs").symlink_to(
                target_dir, target_is_directory=True
            )
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks are not available in this environment")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", str(workflow_file),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        assert "Refusing to use symlinked .specify/workflows/runs path" in result.output

    def test_workflow_run_yaml_rejects_non_directory_specify_path(self, tmp_path):
        """Running local YAML should fail when .specify is not a directory."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()

        workflow_file = tmp_path / "test-workflow.yml"
        workflow_content = {
            "schema_version": "1.0",
            "workflow": {
                "id": "nondir-test",
                "name": "Non-directory Test",
                "version": "1.0.0",
                "description": "A workflow for non-directory guard testing",
            },
            "steps": [{"id": "noop", "type": "shell", "run": "echo done"}],
        }
        workflow_file.write_text(yaml.dump(workflow_content), encoding="utf-8")
        (tmp_path / ".specify").write_text("not a directory", encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "workflow", "run", str(workflow_file),
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        assert ".specify path exists but is not a directory" in result.output


class TestWorkflowRunJsonErrorStream:
    """Under --json, error text must go to stderr so stdout stays parseable."""

    def _bad_workflow(self, tmp_path):
        wf = tmp_path / "bad.yml"
        wf.write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "workflow": {
                        "id": "bad-wf",
                        "name": "Bad",
                        "version": "1.0.0",
                        "description": "fails validation",
                    },
                    # shell step missing required 'run' -> validation error
                    "steps": [{"id": "s", "type": "shell"}],
                }
            ),
            encoding="utf-8",
        )
        return wf

    def test_run_json_validation_error_not_on_stdout(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        wf = self._bad_workflow(tmp_path)
        runner = CliRunner()
        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app, ["workflow", "run", str(wf), "--json"], catch_exceptions=False
            )
        finally:
            os.chdir(old)

        assert result.exit_code == 1
        # stdout must carry only JSON (here: nothing) — never human error text.
        assert "validation failed" not in result.stdout
        assert "Error" not in result.stdout
        # The message is routed to stderr instead.
        assert "validation failed" in result.stderr

    def test_run_json_invalid_input_not_on_stdout(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        # A valid single-shell workflow so we get past load/validate to
        # _parse_input_values, which rejects the malformed --input.
        wf = tmp_path / "ok.yml"
        wf.write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "workflow": {
                        "id": "ok-wf",
                        "name": "OK",
                        "version": "1.0.0",
                        "description": "x",
                    },
                    "steps": [{"id": "s", "type": "shell", "run": "echo hi"}],
                }
            ),
            encoding="utf-8",
        )
        runner = CliRunner()
        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                ["workflow", "run", str(wf), "--json", "--input", "no-equals"],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old)

        assert result.exit_code == 1
        assert "Invalid input format" not in result.stdout
        assert "Invalid input format" in result.stderr
