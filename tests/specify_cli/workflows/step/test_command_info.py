"""Command-focused workflow tests."""

from typing import ClassVar


class TestWorkflowStepRichMarkup:
    """Step discovery commands render metadata as literal text."""

    METADATA: ClassVar[dict[str, str]] = {
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

    def test_info_prints_local_source(self, project_dir, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.workflows.step.catalog import StepRegistry

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            StepRegistry,
            "get",
            lambda _registry, step_id: {
                "name": "Local Step",
                "version": "1.0.0",
                "source": "local",
            },
        )

        result = CliRunner().invoke(app, ["workflow", "step", "info", "local-step"])

        assert result.exit_code == 0, result.output
        assert "Source:" in result.output
        assert "local" in result.output

    def test_info_prints_catalog_source_with_name(self, project_dir, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.workflows.step.catalog import StepRegistry

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            StepRegistry,
            "get",
            lambda _registry, step_id: {
                "name": "Catalog Step",
                "version": "1.0.0",
                "source": "catalog",
                "catalog_name": "default",
            },
        )

        result = CliRunner().invoke(app, ["workflow", "step", "info", "catalog-step"])

        assert result.exit_code == 0, result.output
        assert "catalog (default)" in result.output


def test_info_versions_shows_current_and_history_from_discovery_catalog(
    project_dir, monkeypatch
):
    from typer.testing import CliRunner

    from specify_cli import app
    from specify_cli.workflows.step.catalog import StepCatalog

    monkeypatch.chdir(project_dir)
    monkeypatch.setattr(
        StepCatalog, "_get_merged_steps",
        lambda self, *, step_id=None: {
            "deploy": {
                "id": "deploy", "name": "Deploy", "version": "2.0",
                "_install_allowed": False,
                "releases": {
                    "1.0": {
                        "url": "https://example.com/1.0/step.yml",
                        "sha256": {
                            "step.yml": "0" * 64,
                            "__init__.py": "1" * 64,
                        },
                    },
                },
            }
        },
    )
    result = CliRunner().invoke(
        app, ["workflow", "step", "info", "deploy", "--versions"]
    )
    assert result.exit_code == 0, result.output
    assert "2.0 (current)" in result.output
    assert "1.0" in result.output
    assert "discovery only; not installable" in result.output
