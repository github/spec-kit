"""Command-focused workflow tests."""

from __future__ import annotations

import os

import pytest



class TestWorkflowStepRemoveCLI:
    """Test the 'specify workflow step remove' CLI command edge cases."""

    def test_remove_orphaned_directory(self, project_dir, monkeypatch):
        """step remove works when directory exists but registry entry is missing.

        This covers the case where the registry was reset due to corruption.
        """
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)

        # Create an orphaned step directory (no registry entry)
        step_dir = project_dir / ".specify" / "workflows" / "steps" / "orphan-step"
        step_dir.mkdir(parents=True)
        (step_dir / "step.yml").write_text(
            "step:\n  type_key: orphan-step\n", encoding="utf-8"
        )
        (step_dir / "__init__.py").write_text("", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "remove", "orphan-step"])

        assert result.exit_code == 0, result.output
        assert not step_dir.exists()
        # Warning should be printed about missing registry entry
        assert "Warning" in result.output or "warning" in result.output.lower()

    def test_remove_not_installed(self, project_dir, monkeypatch):
        """step remove fails cleanly when neither directory nor registry entry exist."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "remove", "ghost-step"])

        assert result.exit_code != 0
        assert "not installed" in result.output

    def test_remove_registered_step(self, project_dir, monkeypatch):
        """step remove works normally when both directory and registry entry exist."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.step.catalog import StepRegistry

        monkeypatch.chdir(project_dir)

        # Set up a registered step with a directory
        registry = StepRegistry(project_dir)
        registry.add("my-step", {"name": "My Step", "type_key": "my-step", "version": "1.0.0"})
        step_dir = project_dir / ".specify" / "workflows" / "steps" / "my-step"
        step_dir.mkdir(parents=True)
        (step_dir / "step.yml").write_text(
            "step:\n  type_key: my-step\n", encoding="utf-8"
        )
        (step_dir / "__init__.py").write_text("", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "remove", "my-step"])

        assert result.exit_code == 0, result.output
        assert not step_dir.exists()
        registry2 = StepRegistry(project_dir)
        assert not registry2.is_installed("my-step")

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_remove_rejects_symlinked_steps_base_dir(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        outside = project_dir.parent / "outside-steps"
        outside.mkdir(parents=True, exist_ok=True)
        steps_link = project_dir / ".specify" / "workflows" / "steps"
        steps_link.symlink_to(outside, target_is_directory=True)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "remove", "my-step"])

        assert result.exit_code != 0
        assert "Refusing to use symlinked step directory" in result.output
