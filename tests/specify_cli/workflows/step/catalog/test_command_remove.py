"""Tests for ``specify workflow step catalog remove``."""

from typer.testing import CliRunner

from specify_cli import app
from specify_cli.workflows.step.catalog import StepCatalog


def test_workflow_step_catalog_remove_deletes_selected_source(
    project_dir, monkeypatch
):
    monkeypatch.chdir(project_dir)
    catalog = StepCatalog(project_dir)
    catalog.add_catalog("https://example.com/steps.json", "local")

    result = CliRunner().invoke(
        app, ["workflow", "step", "catalog", "remove", "0"]
    )

    assert result.exit_code == 0, result.output
    assert all(
        config["name"] != "local" for config in catalog.get_catalog_configs()
    )
