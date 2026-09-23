"""Command-focused workflow tests."""

from __future__ import annotations

import os

import pytest



class TestWorkflowRemoveGuard:
    def test_remove_rejects_traversal_registry_key(self, project_dir, monkeypatch):
        """A corrupted registry key must not let remove delete outside workflows/."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("../outside", {"name": "Bad"})
        outside = project_dir / ".specify" / "outside"
        outside.mkdir()
        sentinel = outside / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")

        monkeypatch.chdir(project_dir)
        result = CliRunner().invoke(app, ["workflow", "remove", "../outside"])

        assert result.exit_code != 0
        assert "Invalid workflow ID" in result.output
        assert sentinel.read_text(encoding="utf-8") == "keep"

    @pytest.mark.parametrize("workflow_id", ["overlays", "runs", "steps"])
    def test_remove_rejects_reserved_storage_ids(
        self, project_dir, monkeypatch, workflow_id
    ):
        """Reserved workflow storage directories must never be removable workflows."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add(workflow_id, {"name": "Bad"})
        reserved_dir = project_dir / ".specify" / "workflows" / workflow_id
        reserved_dir.mkdir(exist_ok=True)
        sentinel = reserved_dir / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")

        monkeypatch.chdir(project_dir)
        result = CliRunner().invoke(app, ["workflow", "remove", workflow_id])

        assert result.exit_code != 0
        assert "Invalid workflow ID" in result.output
        assert sentinel.read_text(encoding="utf-8") == "keep"

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_remove_refuses_symlinked_workflow_dir(self, project_dir, monkeypatch):
        """A symlinked workflow directory must not let remove delete its target."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test"})
        outside = project_dir / "outside-workflow-remove-target"
        outside.mkdir(exist_ok=True)
        sentinel = outside / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")
        (project_dir / ".specify" / "workflows" / "test-wf").symlink_to(
            outside, target_is_directory=True
        )

        monkeypatch.chdir(project_dir)
        result = CliRunner().invoke(app, ["workflow", "remove", "test-wf"])

        assert result.exit_code != 0
        assert "symlinked .specify/workflows/test-wf" in result.output
        assert sentinel.read_text(encoding="utf-8") == "keep"
        assert WorkflowRegistry(project_dir).is_installed("test-wf")

    def test_remove_refuses_non_directory_workflow_path(self, project_dir, monkeypatch):
        """A file at the workflow path must fail cleanly instead of crashing."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test"})
        workflow_path = project_dir / ".specify" / "workflows" / "test-wf"
        workflow_path.write_text("not a directory", encoding="utf-8")

        monkeypatch.chdir(project_dir)
        result = CliRunner().invoke(app, ["workflow", "remove", "test-wf"])

        assert result.exit_code != 0
        assert "exists but is not a directory" in result.output
        assert workflow_path.read_text(encoding="utf-8") == "not a directory"
        assert WorkflowRegistry(project_dir).is_installed("test-wf")

    @pytest.mark.parametrize("error_type", [OSError, TypeError, ValueError])
    def test_remove_registry_save_failure_preserves_files_and_registry(
        self, project_dir, monkeypatch, error_type
    ):
        """If persisting the registry removal fails, the workflow's files must
        not have already been deleted: the CLI must not delete files before the
        registry successfully records the removal, and it must fail cleanly."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test", "version": "1.0.0"})
        workflow_dir = project_dir / ".specify" / "workflows" / "test-wf"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        (workflow_dir / "workflow.yml").write_text("keep-me", encoding="utf-8")

        def boom(self):
            raise error_type("save failed")

        monkeypatch.chdir(project_dir)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(WorkflowRegistry, "save", boom)
            result = CliRunner().invoke(app, ["workflow", "remove", "test-wf"])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert result.output.strip() != ""
        # Files must survive a registry-save failure.
        assert (workflow_dir / "workflow.yml").read_text(encoding="utf-8") == "keep-me"
        # The on-disk registry must still claim the workflow installed.
        assert WorkflowRegistry(project_dir).is_installed("test-wf")
        # The directory must be restored to its exact original location, with
        # no leftover staging directory from the stage/restore-on-failure
        # sequence.
        entries = [
            p.name
            for p in (project_dir / ".specify" / "workflows").iterdir()
            if p.name != "workflow-registry.json"
        ]
        assert entries == ["test-wf"]

    def test_remove_staged_cleanup_failure_reports_warning_not_error(
        self, project_dir, monkeypatch
    ):
        """The directory is staged (atomically renamed out of
        .specify/workflows/<id>) *before* the registry write, and the actual
        deletion of the staged directory only happens *after* the registry
        has already durably recorded the removal. If that final deletion
        fails, the registry write already succeeded and must stand -- an
        "Error: Failed to remove..." message at that point would contradict
        the registry, which is exactly the incoherent state this staging
        order exists to prevent. It must be reported as a cleanup warning,
        and the command must still succeed."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test", "version": "1.0.0"})
        workflow_dir = project_dir / ".specify" / "workflows" / "test-wf"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        (workflow_dir / "workflow.yml").write_text("keep-me", encoding="utf-8")

        def boom(*args, **kwargs):
            raise OSError("permission denied")

        monkeypatch.chdir(project_dir)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("shutil.rmtree", boom)
            result = CliRunner().invoke(app, ["workflow", "remove", "test-wf"])

        assert result.exit_code == 0
        assert "Warning" in result.output
        # The registry write already committed -- it must stand.
        assert not WorkflowRegistry(project_dir).is_installed("test-wf")
        # The original install path is gone (staged away before the registry
        # write ever ran); only a leftover staged directory remains, never
        # at the original path the registry/CLI would treat as installed.
        assert not workflow_dir.exists()
        leftovers = [
            p
            for p in (project_dir / ".specify" / "workflows").iterdir()
            if p.name != "workflow-registry.json"
        ]
        assert len(leftovers) == 1
        assert (leftovers[0] / "workflow.yml").read_text(encoding="utf-8") == "keep-me"

    def test_remove_stage_restore_failure_escapes_rich_markup(
        self, temp_dir, monkeypatch
    ):
        """When the registry write fails (already rolled back in-memory by
        WorkflowRegistry.remove()) and the attempt to rename the staged
        directory back to its original location also fails, both the
        restore exception and the registry-update exception interpolated
        into these warning/error messages must be escaped like every other
        error path here."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        project_dir = temp_dir / "weird[project]"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".specify" / "workflows").mkdir()

        registry = WorkflowRegistry(project_dir)
        registry.add("test-wf", {"name": "Test", "version": "1.0.0"})
        workflow_dir = project_dir / ".specify" / "workflows" / "test-wf"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        (workflow_dir / "workflow.yml").write_text("keep-me", encoding="utf-8")

        def save_boom(self):
            raise OSError("[reg] disk full")

        real_rename = os.rename
        rename_calls = {"n": 0}

        def rename_boom(src, dst):
            rename_calls["n"] += 1
            if rename_calls["n"] == 1:
                # Allow the initial stage-out rename to succeed so the
                # restore-back rename (the second call) is what fails.
                return real_rename(src, dst)
            raise OSError("[stage] permission denied")

        monkeypatch.chdir(project_dir)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(WorkflowRegistry, "save", save_boom)
            mp.setattr(os, "rename", rename_boom)
            result = CliRunner().invoke(app, ["workflow", "remove", "test-wf"])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        output_compact = "".join(result.output.split())
        assert "[stage]permissiondenied" in output_compact
        assert "[reg]diskfull" in output_compact



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

    def test_remove_serializes_with_concurrent_catalog_install(
        self, project_dir, monkeypatch
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

        removal_ready = threading.Event()
        install_done = threading.Event()
        real_remove = WorkflowRegistry.remove

        def coordinated_remove(registry, workflow_id):
            if threading.current_thread().name == "remove":
                removal_ready.set()
                install_done.wait(0.5)
            return real_remove(registry, workflow_id)

        monkeypatch.setattr(WorkflowRegistry, "remove", coordinated_remove)
        errors = []

        def remove():
            try:
                _commands.workflow_remove("align-wf")
            except BaseException as exc:
                errors.append(exc)

        def install():
            try:
                _commands._install_workflow_from_catalog(
                    project_dir,
                    workflows_dir,
                    "align-wf",
                )
            except BaseException as exc:
                errors.append(exc)
            finally:
                install_done.set()

        remove_thread = threading.Thread(target=remove, name="remove")
        install_thread = threading.Thread(target=install, name="install")
        remove_thread.start()
        assert removal_ready.wait(2)
        install_thread.start()
        remove_thread.join(5)
        install_thread.join(5)

        assert not remove_thread.is_alive()
        assert not install_thread.is_alive()
        assert errors == []
        assert WorkflowDefinition.from_yaml(workflow_file).version == "2.0.0"
        metadata = WorkflowRegistry(project_dir).get("align-wf")
        assert metadata["version"] == "2.0.0"
