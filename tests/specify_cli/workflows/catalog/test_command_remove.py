"""Tests for ``specify workflow catalog remove``."""

from typer.testing import CliRunner

from specify_cli import app
from specify_cli.workflows.catalog import WorkflowCatalog


def test_workflow_catalog_remove_deletes_selected_source(project_dir, monkeypatch):
    monkeypatch.chdir(project_dir)
    catalog = WorkflowCatalog(project_dir)
    catalog.add_catalog("https://example.com/workflows.json", "local")

    result = CliRunner().invoke(app, ["workflow", "catalog", "remove", "0"])

    assert result.exit_code == 0, result.output
    assert all(
        config["name"] != "local" for config in catalog.get_catalog_configs()
    )
