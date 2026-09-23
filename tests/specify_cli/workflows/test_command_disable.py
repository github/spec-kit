"""Command-focused workflow tests."""

from __future__ import annotations

import os

import pytest



class TestWorkflowCliAlignment:
    """CLI alignment with extension/preset commands (#2342)."""

    WORKFLOW_YAML = """
schema_version: "1.0"
workflow:
  id: "align-wf"
  name: "Align Workflow"
  version: "{version}"
  description: "CLI alignment test workflow"
steps:
  - id: step-one
    type: shell
    run: "echo hello"
"""

    def _write_workflow_dir(self, base, version="1.0.0"):
        d = base / "wf-src"
        d.mkdir(parents=True, exist_ok=True)
        (d / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version=version), encoding="utf-8"
        )
        return d

    def _install_dev(self, runner, app, project_dir):
        src = self._write_workflow_dir(project_dir)
        result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])
        assert result.exit_code == 0, result.output
        return src

    class _FakeResponse:
        def __init__(self, data, url="https://example.com/workflow.yml", headers=None):
            self._data = data
            self._url = url
            self._pos = 0
            self._headers = headers or {}

        def read(self, amt=None):
            if amt is None:
                chunk = self._data[self._pos :]
                self._pos = len(self._data)
                return chunk
            chunk = self._data[self._pos : self._pos + amt]
            self._pos += len(chunk)
            return chunk

        def getheader(self, name, default=None):
            return self._headers.get(name, default)

        def geturl(self):
            return self._url

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    @pytest.mark.parametrize(
        ("command_name", "initial_enabled", "expected_enabled"),
        [
            ("enable", False, True),
            ("disable", True, False),
        ],
    )
    def test_toggle_serializes_with_concurrent_catalog_update(
        self,
        project_dir,
        monkeypatch,
        command_name,
        initial_enabled,
        expected_enabled,
    ):
        import threading
        from specify_cli.workflows import _commands
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry
        from specify_cli.workflows.engine import WorkflowDefinition

        workflows_dir = project_dir / ".specify" / "workflows"
        workflow_file = workflows_dir / "align-wf" / "workflow.yml"
        workflow_file.parent.mkdir(parents=True)
        workflow_file.write_text(
            self.WORKFLOW_YAML.format(version="1.0.0"), encoding="utf-8"
        )
        WorkflowRegistry(project_dir).add(
            "align-wf",
            {
                "name": "Align Workflow",
                "version": "1.0.0",
                "source": "catalog",
                "enabled": initial_enabled,
            },
        )
        monkeypatch.setattr(
            _commands, "_require_specify_project", lambda: project_dir
        )
        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "name": "Align Workflow",
                "version": "2.0.0",
                "url": "https://example.com/workflow.yml",
                "_install_allowed": True,
                "_catalog_name": "test-catalog",
            },
        )
        new_data = self.WORKFLOW_YAML.format(version="2.0.0").encode()
        monkeypatch.setattr(
            "specify_cli.authentication.http.open_url",
            lambda url, timeout=None, extra_headers=None,
            redirect_validator=None: self._FakeResponse(new_data, url),
        )

        toggle_ready = threading.Event()
        update_done = threading.Event()
        real_add = WorkflowRegistry.add

        def coordinated_add(registry, workflow_id, metadata):
            if threading.current_thread().name == "toggle":
                toggle_ready.set()
                update_done.wait(0.5)
            return real_add(registry, workflow_id, metadata)

        monkeypatch.setattr(WorkflowRegistry, "add", coordinated_add)
        errors = []

        def toggle():
            try:
                getattr(_commands, f"workflow_{command_name}")("align-wf")
            except BaseException as exc:
                errors.append(exc)

        def update():
            try:
                _commands._install_workflow_from_catalog(
                    project_dir,
                    workflows_dir,
                    "align-wf",
                )
            except BaseException as exc:
                errors.append(exc)
            finally:
                update_done.set()

        toggle_thread = threading.Thread(target=toggle, name="toggle")
        update_thread = threading.Thread(target=update, name="update")
        toggle_thread.start()
        assert toggle_ready.wait(2)
        update_thread.start()
        toggle_thread.join(5)
        update_thread.join(5)

        assert not toggle_thread.is_alive()
        assert not update_thread.is_alive()
        assert errors == []
        assert WorkflowDefinition.from_yaml(workflow_file).version == "2.0.0"
        metadata = WorkflowRegistry(project_dir).get("align-wf")
        assert metadata["version"] == "2.0.0"
        assert metadata.get("enabled", True) is expected_enabled

    def test_disable_blocks_run_enable_restores(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)

        result = runner.invoke(app, ["workflow", "disable", "align-wf"])
        assert result.exit_code == 0, result.output
        assert WorkflowRegistry(project_dir).get("align-wf")["enabled"] is False

        result = runner.invoke(app, ["workflow", "run", "align-wf"])
        assert result.exit_code != 0
        assert "disabled" in result.output

        result = runner.invoke(app, ["workflow", "enable", "align-wf"])
        assert result.exit_code == 0, result.output
        assert WorkflowRegistry(project_dir).get("align-wf")["enabled"] is True

        result = runner.invoke(app, ["workflow", "run", "align-wf"])
        assert result.exit_code == 0, result.output

    def test_disable_blocks_case_variant_installed_path(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)

        result = runner.invoke(app, ["workflow", "disable", "align-wf"])
        assert result.exit_code == 0, result.output

        case_variant = (
            project_dir
            / ".SPECIFY"
            / "WORKFLOWS"
            / "ALIGN-WF"
            / "workflow.yml"
        )
        if not case_variant.is_file():
            pytest.skip("filesystem is case-sensitive")

        result = runner.invoke(
            app, ["workflow", "run", str(case_variant)]
        )

        assert result.exit_code != 0
        assert "disabled" in result.output

    def test_disable_blocks_run_via_path_equivalent_id(self, project_dir, monkeypatch):
        """Path-equivalent and newline IDs must not dodge the registry lookup."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)

        result = runner.invoke(app, ["workflow", "disable", "align-wf"])
        assert result.exit_code == 0, result.output

        for spelling in ("align-wf/", "align-wf/.", "align-wf\n"):
            result = runner.invoke(app, ["workflow", "run", spelling])
            assert result.exit_code != 0, spelling
            assert "Invalid workflow ID" in result.output, spelling

        # Direct path to the installed workflow's own YAML must also refuse.
        installed_yaml = ".specify/workflows/align-wf/workflow.yml"
        assert (project_dir / installed_yaml).is_file()
        result = runner.invoke(app, ["workflow", "run", installed_yaml])
        assert result.exit_code != 0
        assert "disabled" in result.output

        # Same guard must hold when invoked from outside the project.
        outside = project_dir.parent / "outside-cwd"
        outside.mkdir(exist_ok=True)
        monkeypatch.chdir(outside)
        result = runner.invoke(
            app, ["workflow", "run", str(project_dir / installed_yaml)]
        )
        assert result.exit_code != 0
        assert "disabled" in result.output

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_disable_blocks_run_when_installed_yaml_is_symlinked(
        self, project_dir, monkeypatch
    ):
        """A disabled workflow's own workflow.yml being replaced with a symlink
        must not bypass the disabled check. Resolving the path before mapping
        it back to its registry owner would follow the symlink out of
        .specify/workflows, fail to find an owner, and let engine.load_workflow
        run the original symlink target anyway -- ownership must be
        determined from the normalized *lexical* path (not resolve()), and a
        symlinked path component in the installed tree must be refused."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)

        result = runner.invoke(app, ["workflow", "disable", "align-wf"])
        assert result.exit_code == 0, result.output

        installed_yaml = project_dir / ".specify" / "workflows" / "align-wf" / "workflow.yml"
        external_target = project_dir / "external-workflow.yml"
        external_target.write_text(
            self.WORKFLOW_YAML.format(version="9.9.9"), encoding="utf-8"
        )
        installed_yaml.unlink()
        installed_yaml.symlink_to(external_target)

        result = runner.invoke(app, ["workflow", "run", str(installed_yaml)])
        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "disabled" in result.output or "symlink" in result.output.lower()

    def test_disable_shows_marker_in_list(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)
        runner.invoke(app, ["workflow", "disable", "align-wf"])
        result = runner.invoke(app, ["workflow", "list"])
        assert result.exit_code == 0, result.output
        assert "[disabled]" in result.output
