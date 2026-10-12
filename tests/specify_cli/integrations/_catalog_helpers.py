"""Shared fixtures for integration discovery command tests."""

import os

from tests.conftest import strip_ansi


def _normalize_cli_output(output: str) -> str:
    output = strip_ansi(output)
    output = " ".join(output.split())
    return output.strip()


class IntegrationCatalogCliTestBase:
    """End-to-end CLI tests for `integration search`, `info`, and `catalog …`.

    All tests patch `IntegrationCatalog._get_merged_integrations` so no network
    or on-disk cache is touched. Adds #2344 coverage without affecting any
    existing integration install/switch/uninstall/upgrade behavior.
    """

    FAKE_INTEGRATIONS = [
        {
            "id": "acme-coder",
            "name": "Acme Coder",
            "version": "2.0.0",
            "description": "Community integration for Acme Coder",
            "author": "acme-org",
            "tags": ["cli", "acme"],
            "_catalog_name": "community",
            "_install_allowed": False,
        },
        {
            "id": "stellar-agent",
            "name": "Stellar Agent",
            "version": "1.3.0",
            "description": "First-party Stellar agent integration",
            "author": "stellar-labs",
            "tags": ["ide"],
            "_catalog_name": "default",
            "_install_allowed": True,
        },
    ]
    MARKUP_INTEGRATION = {
        "id": "[red]markup-id[/red]",
        "name": "[green]Markup Name[/green]",
        "version": "[blue]1.0.0[/blue]",
        "description": "[yellow]Markup Description[/yellow]",
        "author": "[magenta]Markup Author[/magenta]",
        "license": "[cyan]Markup License[/cyan]",
        "repository": "[bold]Markup Repository[/bold]",
        "tags": ["[italic]markup-tag[/italic]"],
        "_catalog_name": "[underline]markup-catalog[/underline]",
        "_install_allowed": False,
    }

    def _make_project(self, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        return project

    def _patch_catalog(self, monkeypatch, integrations=None):
        """Return a stubbed `_get_merged_integrations` that yields *integrations*."""
        from specify_cli.integrations import IntegrationCatalog

        data = list(integrations if integrations is not None else self.FAKE_INTEGRATIONS)

        def fake_merged(self, force_refresh=False):
            return data

        monkeypatch.setattr(IntegrationCatalog, "_get_merged_integrations", fake_merged)

    def _invoke(self, argv, cwd):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        old = os.getcwd()
        try:
            os.chdir(cwd)
            return runner.invoke(app, argv, catch_exceptions=False)
        finally:
            os.chdir(old)


class IntegrationListCatalogTestBase:
    def _init_project(self, tmp_path):
        """Create a minimal spec-kit project."""
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = tmp_path / "proj"
        project.mkdir()
        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "init", "--here",
                "--integration", "copilot",
                "--script", "sh",
                "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old)
        assert result.exit_code == 0, result.output
        return project
