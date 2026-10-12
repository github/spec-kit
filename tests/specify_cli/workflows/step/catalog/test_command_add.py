"""Tests for ``specify workflow step catalog add``."""

from typer.testing import CliRunner

from specify_cli import app
from specify_cli.workflows.step.catalog import StepCatalog


def test_workflow_step_catalog_add_persists_named_source(project_dir, monkeypatch):
    monkeypatch.chdir(project_dir)

    result = CliRunner().invoke(
        app,
        [
            "workflow",
            "step",
            "catalog",
            "add",
            "https://example.com/steps.json",
            "--name",
            "local",
        ],
    )

    assert result.exit_code == 0, result.output
    configs = StepCatalog(project_dir).get_catalog_configs()
    assert any(
        config["name"] == "local"
        and config["url"] == "https://example.com/steps.json"
        for config in configs
    )


def test_workflow_step_catalog_add_reports_unchanged(project_dir, monkeypatch):
    monkeypatch.chdir(project_dir)
    args = [
        "workflow",
        "step",
        "catalog",
        "add",
        "https://example.com/steps.json",
        "--name",
        "local",
    ]

    runner = CliRunner()
    assert runner.invoke(app, args).exit_code == 0
    unchanged = runner.invoke(app, args)

    assert unchanged.exit_code == 0, unchanged.output
    assert "already configured" in unchanged.output
