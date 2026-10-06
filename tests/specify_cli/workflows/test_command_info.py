"""Command-focused workflow tests."""

from __future__ import annotations





class TestWorkflowInfoStepGraph:
    """`workflow info` must render each step as `→ <id> [<type>]` with LITERAL
    brackets. Rich parses an unescaped `[<type>]` as a style tag and silently
    swallows it, so the step type would vanish from the output."""

    def test_step_type_rendered_in_literal_brackets(self, temp_dir, monkeypatch):
        import types

        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.engine import WorkflowEngine

        (temp_dir / ".specify" / "workflows").mkdir(parents=True)

        fake = types.SimpleNamespace(
            name="My WF", id="my-wf", version="1.0.0", author="", description="",
            default_integration=None, inputs={},
            steps=[{"id": "step-one", "type": "gate"}],
        )
        monkeypatch.setattr(WorkflowEngine, "load_workflow", lambda self, wid: fake)
        monkeypatch.chdir(temp_dir)

        result = CliRunner().invoke(app, ["workflow", "info", "my-wf"])

        assert result.exit_code == 0, result.output
        assert "step-one" in result.output
        # The step type must survive as a literal bracketed token, not be eaten
        # by Rich as an unknown style tag.
        assert "[gate]" in result.output

    def test_definition_metadata_fields_escaped(self, temp_dir, monkeypatch):
        """Every metadata field printed from the workflow definition (name,
        description, author, integration, input name/type) is untrusted
        workflow.yml content. An unescaped `[...]` in any of them would be
        parsed as a Rich style tag and silently swallowed, so bracketed text
        must survive literally in the output."""
        import types

        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.engine import WorkflowEngine

        (temp_dir / ".specify" / "workflows").mkdir(parents=True)

        fake = types.SimpleNamespace(
            name="My [WF]",
            id="my-wf",
            version="1.0.0 [beta]",
            author="Jane [Doe]",
            description="Does [stuff] nicely",
            default_integration="claude [code]",
            inputs={"in [put]": {"type": "str [ing]", "required": True}},
            steps=[],
        )
        monkeypatch.setattr(WorkflowEngine, "load_workflow", lambda self, wid: fake)
        monkeypatch.chdir(temp_dir)

        result = CliRunner().invoke(app, ["workflow", "info", "my-wf"])

        assert result.exit_code == 0, result.output
        # Each bracketed token must render literally rather than be consumed as
        # an unknown Rich style tag.
        assert "My [WF]" in result.output
        assert "1.0.0 [beta]" in result.output
        assert "Jane [Doe]" in result.output
        assert "Does [stuff] nicely" in result.output
        assert "claude [code]" in result.output
        assert "in [put]" in result.output
        assert "str [ing]" in result.output

    def test_catalog_metadata_fields_escaped(self, temp_dir, monkeypatch):
        """When the workflow is only found in the catalog (not on disk), its
        catalog-derived fields (name, description, tags) are untrusted too and
        must be escaped so bracketed content renders literally."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.engine import WorkflowEngine
        from specify_cli.workflows import catalog as catalog_mod

        (temp_dir / ".specify" / "workflows").mkdir(parents=True)

        def _not_on_disk(self, wid):
            raise FileNotFoundError(wid)

        monkeypatch.setattr(WorkflowEngine, "load_workflow", _not_on_disk)
        monkeypatch.setattr(
            catalog_mod.WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "name": "Cat [WF]",
                "version": "2.0.0 [rc]",
                "description": "From [catalog]",
                "tags": ["a [b]", "c [d]"],
            },
        )
        monkeypatch.chdir(temp_dir)

        result = CliRunner().invoke(app, ["workflow", "info", "cat-wf"])

        assert result.exit_code == 0, result.output
        assert "Cat [WF]" in result.output
        assert "2.0.0 [rc]" in result.output
        assert "From [catalog]" in result.output
        assert "a [b]" in result.output
        assert "c [d]" in result.output

    def test_not_found_id_escaped(self, temp_dir, monkeypatch):
        """When the workflow is neither on disk nor in the catalog, the
        not-found error echoes the requested ID. That ID is user input, so a
        bracketed value must render literally instead of being parsed (and
        swallowed) as a Rich style tag."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.engine import WorkflowEngine
        from specify_cli.workflows import catalog as catalog_mod

        (temp_dir / ".specify" / "workflows").mkdir(parents=True)

        def _not_on_disk(self, wid):
            raise FileNotFoundError(wid)

        monkeypatch.setattr(WorkflowEngine, "load_workflow", _not_on_disk)
        monkeypatch.setattr(
            catalog_mod.WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: None,
        )
        monkeypatch.chdir(temp_dir)

        result = CliRunner().invoke(app, ["workflow", "info", "ghost [wf]"])

        assert result.exit_code == 1, result.output
        assert "not found" in result.output
        # The bracketed ID must survive literally, not be eaten as markup.
        assert "ghost [wf]" in result.output
