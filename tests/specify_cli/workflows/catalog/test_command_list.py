"""Command-focused workflow tests."""

from __future__ import annotations





class TestWorkflowCliAlignment:
    """CLI alignment with extension/preset commands (#2342)."""

    def test_catalog_list_escapes_rich_markup(self, project_dir, monkeypatch):
        """User-editable catalog name/url/description must not be parsed as Rich markup."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog

        monkeypatch.chdir(project_dir)
        configs = [
            {
                "name": "Bracket [Catalog]",
                "url": "https://example.com/[cat].json",
                "description": "desc [with] brackets",
                "install_allowed": True,
            },
        ]
        monkeypatch.setattr(
            WorkflowCatalog,
            "get_catalog_configs",
            lambda self: [dict(c) for c in configs],
        )
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "catalog", "list"])
        assert result.exit_code == 0, result.output
        assert "Bracket [Catalog]" in result.output
        assert "https://example.com/[cat].json" in result.output
        assert "desc [with] brackets" in result.output
