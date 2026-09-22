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

    def test_info_escapes_catalog_metadata(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.step.catalog import StepCatalog, StepRegistry

        metadata = dict(self.METADATA)
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(StepRegistry, "get", lambda _registry, step_id: None)
        monkeypatch.setattr(
            StepCatalog,
            "get_step_info",
            lambda _catalog, step_id: metadata,
        )

        result = CliRunner().invoke(
            app, ["workflow", "step", "info", metadata["id"]]
        )

        assert result.exit_code == 0, result.output
        for value in metadata.values():
            assert value in result.output

    def test_info_escapes_missing_step_id(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.step.catalog import StepCatalog, StepRegistry

        step_id = "[red]missing[/red]"
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(StepRegistry, "get", lambda _registry, step_id: None)
        monkeypatch.setattr(
            StepCatalog,
            "get_step_info",
            lambda _catalog, step_id: None,
        )

        result = CliRunner().invoke(
            app, ["workflow", "step", "info", step_id]
        )

        assert result.exit_code == 1, result.output
        assert step_id in result.output
