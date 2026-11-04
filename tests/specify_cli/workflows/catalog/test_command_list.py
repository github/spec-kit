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
                "priority": 1,
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

    def test_catalog_list_output_and_configured_urls_are_unchanged(
        self, project_dir, monkeypatch
    ):
        """The human listing keeps its layout and prints URLs as configured."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        monkeypatch.delenv("SPECKIT_WORKFLOW_CATALOG_URL", raising=False)
        (project_dir / ".specify" / "workflow-catalogs.yml").write_text(
            "catalogs:\n"
            "  - name: private\n"
            "    url: https://user:token@e.example/c.json?key=value\n"
            "    install_allowed: true\n"
            "    description: Private source\n"
            "  - name: public\n"
            "    url: https://p.example/c.json\n",
            encoding="utf-8",
        )
        result = CliRunner().invoke(
            app, ["workflow", "catalog", "list"], env={"COLUMNS": "200"}
        )
        assert result.exit_code == 0, result.output
        assert [line.strip() for line in result.output.splitlines() if line.strip()] == [
            "Workflow Catalog Sources:",
            "[0] private — install allowed",
            "https://user:token@e.example/c.json?key=value",
            "Private source",
            "[1] public — discovery only",
            "https://p.example/c.json",
        ]

    def test_catalog_list_reports_invalid_config_and_exits_nonzero(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        monkeypatch.delenv("SPECKIT_WORKFLOW_CATALOG_URL", raising=False)
        (project_dir / ".specify" / "workflow-catalogs.yml").write_text(
            "catalogs: 5\n", encoding="utf-8"
        )
        result = CliRunner().invoke(app, ["workflow", "catalog", "list"])
        assert result.exit_code == 1
        assert "'catalogs' must be a list" in result.output

    def test_catalog_list_keeps_local_diagnostics_for_malformed_urls(
        self, project_dir, monkeypatch
    ):
        """The shared message is secret-free; the CLI still names what to repair."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        monkeypatch.delenv("SPECKIT_WORKFLOW_CATALOG_URL", raising=False)
        (project_dir / ".specify" / "workflow-catalogs.yml").write_text(
            'catalogs:\n  - name: bad\n    url: "https://user:token@[::1"\n',
            encoding="utf-8",
        )
        result = CliRunner().invoke(
            app, ["workflow", "catalog", "list"], env={"COLUMNS": "200"}
        )
        assert result.exit_code == 1
        assert "Catalog URL is malformed: https://user:token@[::1" in result.output
