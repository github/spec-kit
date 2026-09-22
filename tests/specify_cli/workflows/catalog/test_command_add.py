"""Tests for ``specify workflow catalog add``."""

from typer.testing import CliRunner

from specify_cli import app
from specify_cli.workflows.catalog import WorkflowCatalog


def test_workflow_catalog_add_persists_named_source(project_dir, monkeypatch):
    monkeypatch.chdir(project_dir)

    result = CliRunner().invoke(
        app,
        [
            "workflow",
            "catalog",
            "add",
            "https://example.com/workflows.json",
            "--name",
            "local",
        ],
    )

    assert result.exit_code == 0, result.output
    configs = WorkflowCatalog(project_dir).get_catalog_configs()
    assert any(
        config["name"] == "local"
        and config["url"] == "https://example.com/workflows.json"
        for config in configs
    )
