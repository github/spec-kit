"""Command-focused workflow tests."""

from __future__ import annotations





class TestWorkflowCliAlignment:
    """CLI alignment with extension/preset commands (#2342)."""

    def test_step_catalog_list_escapes_rich_markup(self, project_dir, monkeypatch):
        """User-editable step-catalog name/url/description must not be parsed as Rich markup."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        configs = [
            {
                "name": "Bracket [Step]",
                "url": "https://example.com/[step].json",
                "description": "step [with] brackets",
                "install_allowed": True,
            },
        ]
        monkeypatch.setattr(
            StepCatalog,
            "get_catalog_configs",
            lambda self: [dict(c) for c in configs],
        )
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "catalog", "list"])
        assert result.exit_code == 0, result.output
        assert "Bracket [Step]" in result.output
        assert "https://example.com/[step].json" in result.output
        assert "step [with] brackets" in result.output
