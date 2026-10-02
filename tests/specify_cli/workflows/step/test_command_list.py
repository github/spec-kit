"""Command-focused workflow tests."""

from __future__ import annotations





class TestWorkflowStepRichMarkup:
    """Step discovery commands render metadata as literal text."""

    METADATA = {
        "id": "[magenta]step-id[/magenta]",
        "name": "[red]Step Name[/red]",
        "version": "[green]1.0.0[/green]",
        "author": "[yellow]Author[/yellow]",
        "description": "[blue]Description[/blue]",
    }

    def test_list_escapes_installed_metadata(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.step.catalog import StepRegistry

        metadata = dict(self.METADATA)
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            StepRegistry,
            "list",
            lambda _registry: {metadata["id"]: metadata},
        )

        result = CliRunner().invoke(app, ["workflow", "step", "list"])

        assert result.exit_code == 0, result.output
        assert metadata["name"] in result.output
        assert metadata["id"] in result.output
        assert metadata["version"] in result.output
