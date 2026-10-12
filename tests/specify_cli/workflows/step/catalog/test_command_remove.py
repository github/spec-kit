"""Tests for ``specify workflow step catalog remove``."""

from typer.testing import CliRunner
import yaml

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


def test_workflow_step_catalog_remove_uses_listed_index(project_dir, monkeypatch):
    monkeypatch.chdir(project_dir)
    monkeypatch.delenv("SPECKIT_STEP_CATALOG_URL", raising=False)
    config = project_dir / ".specify" / "step-catalogs.yml"
    data = {"notes": "keep", "catalogs": [
        {"name": "team", "url": "https://example.com/team.json", "priority": 10},
        {"name": "review", "url": "https://example.com/review.json", "priority": 1},
    ]}
    config.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    runner = CliRunner()
    listed = runner.invoke(app, ["workflow", "step", "catalog", "list"])
    assert listed.exit_code == 0, listed.output
    assert "[0] review" in listed.output

    result = runner.invoke(app, ["workflow", "step", "catalog", "remove", "0"])

    assert result.exit_code == 0, result.output
    assert "'review' removed" in result.output
    data["catalogs"].pop(1)
    assert yaml.safe_load(config.read_text(encoding="utf-8")) == data


def test_workflow_step_catalog_remove_refuses_environment_source(project_dir, monkeypatch):
    monkeypatch.chdir(project_dir)
    config = project_dir / ".specify" / "step-catalogs.yml"
    config.write_text(
        "# keep\ncatalogs:\n  - name: project\n"
        "    url: https://example.com/project.json\n", encoding="utf-8",
    )
    before = config.read_bytes()
    monkeypatch.setenv("SPECKIT_STEP_CATALOG_URL", "https://example.com/override.json")
    runner = CliRunner()
    listed = runner.invoke(app, ["workflow", "step", "catalog", "list"])
    assert listed.exit_code == 0, listed.output
    assert "[0] env-override" in listed.output

    result = runner.invoke(app, ["workflow", "step", "catalog", "remove", "0"])

    assert result.exit_code == 1, result.output
    assert "SPECKIT_STEP_CATALOG_URL" in result.output
    assert "Unset" in result.output
    assert config.read_bytes() == before
