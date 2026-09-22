"""Command-focused workflow tests."""

from __future__ import annotations





class TestWorkflowCliAlignment:
    """CLI alignment with extension/preset commands (#2342)."""

    def test_search_author_filters(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog

        monkeypatch.chdir(project_dir)
        workflows = {
            "wf-a": {"name": "Workflow A", "version": "1.0.0", "description": "", "author": "alice"},
            "wf-b": {"name": "Workflow B", "version": "1.0.0", "description": "", "author": "bob"},
        }
        monkeypatch.setattr(
            WorkflowCatalog,
            "_get_merged_workflows",
            lambda self, force_refresh=False: {k: dict(v) for k, v in workflows.items()},
        )
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "search", "--author", "Alice"])
        assert result.exit_code == 0, result.output
        assert "wf-a" in result.output
        assert "wf-b" not in result.output

    def test_search_escapes_rich_markup_in_catalog_fields(self, project_dir, monkeypatch):
        """Catalog-derived name/description/tags must not be parsed as Rich markup."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog

        monkeypatch.chdir(project_dir)
        workflows = {
            "wf-a": {
                "name": "Bracket [Search]",
                "version": "1.0.0",
                "description": "desc [with] brackets",
                "tags": ["tag[1]", "tag2"],
            },
        }
        monkeypatch.setattr(
            WorkflowCatalog,
            "_get_merged_workflows",
            lambda self, force_refresh=False: {k: dict(v) for k, v in workflows.items()},
        )
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "search"])
        assert result.exit_code == 0, result.output
        assert "Bracket [Search]" in result.output
        assert "desc [with] brackets" in result.output
        assert "tag[1]" in result.output

    def test_search_and_info_tolerate_non_list_tags(self, project_dir, monkeypatch):
        """A scalar ``tags:`` value must not crash the search/info display.

        ``WorkflowCatalog.search`` guards its tag *filter* with
        ``isinstance(raw_tags, list)``, but the ``workflow search`` and
        ``workflow info`` display paths only tested truthiness before
        iterating. ``tags: 5`` is truthy and not iterable, so both raised
        ``TypeError: 'int' object is not iterable``.
        """
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog

        monkeypatch.chdir(project_dir)
        workflows = {
            "wf-a": {
                "name": "Workflow A",
                "version": "1.0.0",
                "description": "desc",
                "tags": 5,
            },
        }
        monkeypatch.setattr(
            WorkflowCatalog,
            "_get_merged_workflows",
            lambda self, force_refresh=False: {k: dict(v) for k, v in workflows.items()},
        )
        runner = CliRunner()
        searched = runner.invoke(app, ["workflow", "search"])
        info = runner.invoke(app, ["workflow", "info", "wf-a"])

        assert searched.exit_code == 0, searched.output
        assert "Workflow A" in searched.output
        assert "Tags:" not in searched.output

        assert info.exit_code == 0, info.output
        assert "Tags:" not in info.output
