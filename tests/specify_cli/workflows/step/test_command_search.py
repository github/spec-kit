"""Command-focused workflow tests."""

from typing import ClassVar

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.workflows.step.catalog import StepCatalog, StepCatalogError


class TestWorkflowStepRichMarkup:
    """Step discovery commands render metadata as literal text."""

    METADATA: ClassVar[dict[str, str]] = {
        "id": "[magenta]step-id[/magenta]",
        "name": "[red]Step Name[/red]",
        "version": "[green]1.0.0[/green]",
        "author": "[yellow]Author[/yellow]",
        "description": "[blue]Description[/blue]",
    }

    def test_search_escapes_catalog_metadata(self, project_dir, monkeypatch):
        metadata = dict(self.METADATA)
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            StepCatalog, "search", lambda _catalog, query=None: [metadata]
        )

        result = CliRunner().invoke(app, ["workflow", "step", "search"])

        assert result.exit_code == 0, result.output
        assert metadata["name"] in result.output
        assert metadata["id"] in result.output
        assert metadata["version"] in result.output
        assert metadata["description"] in result.output


@pytest.mark.parametrize("query", ["[/x]", "a[red]b"])
def test_workflow_step_search_displays_query_markup_literally(
    project_dir, monkeypatch, query
):
    monkeypatch.chdir(project_dir)

    result = CliRunner().invoke(app, ["workflow", "step", "search", query])

    assert result.exit_code == 0, result.output
    assert f"No step types found matching '{query}'." in result.output


def test_workflow_step_search_escapes_catalog_error_markup(project_dir, monkeypatch):
    monkeypatch.chdir(project_dir)

    def raise_catalog_error(self, query=None):
        raise StepCatalogError("Invalid step id [/x]")

    monkeypatch.setattr(StepCatalog, "search", raise_catalog_error)
    result = CliRunner().invoke(app, ["workflow", "step", "search"])

    assert result.exit_code == 1
    assert "Invalid step id [/x]" in result.output
    assert "MarkupError" not in result.output
