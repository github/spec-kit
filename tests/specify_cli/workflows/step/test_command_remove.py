"""Command-focused workflow tests."""

from __future__ import annotations

import json
import os
import shutil
import threading
from pathlib import Path

import pytest

from tests.lock_helpers import wait_until_blocked_or_done, watch_lock_attempt


def _write_package(package_dir: Path, type_key: str) -> Path:
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "step.yml").write_text(
        f"step:\n  type_key: {type_key}\n  name: {type_key}\n  version: 0.1.0\n",
        encoding="utf-8",
    )
    (package_dir / "__init__.py").write_text("# init\n", encoding="utf-8")
    return package_dir


def _steps_dir(project_dir: Path) -> Path:
    return project_dir / ".specify" / "workflows" / "steps"


def _registered_ids(project_dir: Path) -> set[str]:
    path = _steps_dir(project_dir) / "step-registry.json"
    return set(json.loads(path.read_text(encoding="utf-8"))["steps"])


def _install(project_dir: Path, tmp_path: Path, step_id: str) -> None:
    from specify_cli.workflows.step import installer

    pkg = _write_package(tmp_path / f"pkg-{step_id}", step_id)
    installer.install_step_package(project_dir, step_id, pkg, source="local")


class _Worker(threading.Thread):
    """Run ``target`` in a named thread and record its exception, if any."""

    def __init__(self, name, target):
        super().__init__(name=name, daemon=True)
        self._target_fn = target
        self.done = threading.Event()
        self.error: BaseException | None = None

    def run(self):
        try:
            self._target_fn()
        except BaseException as exc:  # noqa: BLE001 - asserted by the test
            self.error = exc
        finally:
            self.done.set()


class TestWorkflowStepRemoveLocking:
    """`step remove` must share the install lock with `step add`."""

    def test_remove_waiting_on_install_does_not_resurrect_entry(
        self, project_dir, tmp_path, monkeypatch
    ):
        """Install of `new` holds the lock while `old` is removed.

        Without the lock, the installer's stale `{old}` snapshot is saved as
        `{old, new}` after removal persisted `{}`, resurrecting `old` with no
        directory.
        """
        from specify_cli.workflows.step import installer
        from specify_cli.workflows.step.command_remove import workflow_step_remove

        monkeypatch.chdir(project_dir)
        _install(project_dir, tmp_path, "old-step")
        new_pkg = _write_package(tmp_path / "pkg-new", "new-step")

        installer_inside = threading.Event()
        release_installer = threading.Event()
        real_replace = installer._replace_install

        def _paused_replace(*args, **kwargs):
            if threading.current_thread().name == "installer":
                installer_inside.set()
                if not release_installer.wait(10):
                    raise AssertionError("installer was never released")
            return real_replace(*args, **kwargs)

        monkeypatch.setattr(installer, "_replace_install", _paused_replace)
        remover_attempted = watch_lock_attempt(monkeypatch, "remover")

        install_thread = _Worker(
            "installer",
            lambda: installer.install_step_package(
                project_dir, "new-step", new_pkg, source="local"
            ),
        )
        remove_thread = _Worker("remover", lambda: workflow_step_remove("old-step"))

        install_thread.start()
        assert installer_inside.wait(10), "installer never reached the lock"
        remove_thread.start()
        wait_until_blocked_or_done(remover_attempted, remove_thread.done)
        release_installer.set()
        install_thread.join(10)
        remove_thread.join(10)

        assert install_thread.error is None
        assert remove_thread.error is None
        assert _registered_ids(project_dir) == {"new-step"}
        assert not (_steps_dir(project_dir) / "old-step").exists()
        assert (_steps_dir(project_dir) / "new-step").is_dir()

    def test_install_waiting_on_remove_is_not_unregistered(
        self, project_dir, tmp_path, monkeypatch
    ):
        """Removal of `old` holds the lock while `new` is installed.

        Without the lock, removal's stale `{old}` snapshot is saved as `{}`
        after the installer persisted `{old, new}`, leaving `new` on disk but
        unregistered.
        """
        from specify_cli.workflows.step import installer
        from specify_cli.workflows.step.catalog import StepRegistry
        from specify_cli.workflows.step.command_remove import workflow_step_remove

        monkeypatch.chdir(project_dir)
        _install(project_dir, tmp_path, "old-step")
        new_pkg = _write_package(tmp_path / "pkg-new", "new-step")

        remover_inside = threading.Event()
        release_remover = threading.Event()
        real_remove = StepRegistry.remove

        def _paused_remove(self, step_id):
            if threading.current_thread().name == "remover":
                remover_inside.set()
                if not release_remover.wait(10):
                    raise AssertionError("remover was never released")
            return real_remove(self, step_id)

        monkeypatch.setattr(StepRegistry, "remove", _paused_remove)
        installer_attempted = watch_lock_attempt(monkeypatch, "installer")

        remove_thread = _Worker("remover", lambda: workflow_step_remove("old-step"))
        install_thread = _Worker(
            "installer",
            lambda: installer.install_step_package(
                project_dir, "new-step", new_pkg, source="local"
            ),
        )

        remove_thread.start()
        assert remover_inside.wait(10), "remover never reached the registry update"
        install_thread.start()
        wait_until_blocked_or_done(installer_attempted, install_thread.done)
        release_remover.set()
        remove_thread.join(10)
        install_thread.join(10)

        assert remove_thread.error is None
        assert install_thread.error is None
        assert _registered_ids(project_dir) == {"new-step"}
        assert not (_steps_dir(project_dir) / "old-step").exists()
        assert (_steps_dir(project_dir) / "new-step").is_dir()

    def test_remove_fails_cleanly_when_lock_cannot_be_acquired(
        self, project_dir, tmp_path, monkeypatch
    ):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        _install(project_dir, tmp_path, "my-step")
        # A directory at the lock path cannot be opened as the lock file.
        lock_path = project_dir / ".specify" / ".step-install.lock"
        if lock_path.exists():
            lock_path.unlink()
        lock_path.mkdir()

        result = CliRunner().invoke(app, ["workflow", "step", "remove", "my-step"])

        assert result.exit_code == 1, result.output
        output = _flat(result.output)
        assert "Failed to lock step removal 'my-step'" in output
        # One removal-specific message, not wrapped in the shared helper's text.
        assert output.count("Failed to") == 1, output
        assert "installation" not in output
        assert _registered_ids(project_dir) == {"my-step"}
        assert (_steps_dir(project_dir) / "my-step").is_dir()

    def test_remove_restores_registry_entry_when_directory_delete_fails(
        self, project_dir, tmp_path, monkeypatch
    ):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        _install(project_dir, tmp_path, "my-step")
        step_dir = (_steps_dir(project_dir) / "my-step").resolve()
        real_rmtree = shutil.rmtree

        def _failing_rmtree(path, *args, **kwargs):
            if Path(path).resolve() == step_dir:
                raise OSError("simulated delete failure")
            return real_rmtree(path, *args, **kwargs)

        monkeypatch.setattr(shutil, "rmtree", _failing_rmtree)

        result = CliRunner().invoke(app, ["workflow", "step", "remove", "my-step"])

        assert result.exit_code == 1, result.output
        assert "Failed to remove step directory" in result.output
        assert _registered_ids(project_dir) == {"my-step"}
        assert step_dir.is_dir()


class TestWorkflowStepRemoveCLI:
    """Test the 'specify workflow step remove' CLI command edge cases."""

    def test_remove_orphaned_directory(self, project_dir, monkeypatch):
        """step remove works when directory exists but registry entry is missing.

        This covers the case where the registry was reset due to corruption.
        """
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)

        # Create an orphaned step directory (no registry entry)
        step_dir = project_dir / ".specify" / "workflows" / "steps" / "orphan-step"
        step_dir.mkdir(parents=True)
        (step_dir / "step.yml").write_text(
            "step:\n  type_key: orphan-step\n", encoding="utf-8"
        )
        (step_dir / "__init__.py").write_text("", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "remove", "orphan-step"])

        assert result.exit_code == 0, result.output
        assert not step_dir.exists()
        # Warning should be printed about missing registry entry
        assert "Warning" in result.output or "warning" in result.output.lower()

    def test_remove_not_installed(self, project_dir, monkeypatch):
        """step remove fails cleanly when neither directory nor registry entry exist."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "remove", "ghost-step"])

        assert result.exit_code != 0
        assert "not installed" in result.output

    def test_remove_registered_step(self, project_dir, monkeypatch):
        """step remove works normally when both directory and registry entry exist."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.step.catalog import StepRegistry

        monkeypatch.chdir(project_dir)

        # Set up a registered step with a directory
        registry = StepRegistry(project_dir)
        registry.add("my-step", {"name": "My Step", "type_key": "my-step", "version": "1.0.0"})
        step_dir = project_dir / ".specify" / "workflows" / "steps" / "my-step"
        step_dir.mkdir(parents=True)
        (step_dir / "step.yml").write_text(
            "step:\n  type_key: my-step\n", encoding="utf-8"
        )
        (step_dir / "__init__.py").write_text("", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "remove", "my-step"])

        assert result.exit_code == 0, result.output
        assert not step_dir.exists()
        registry2 = StepRegistry(project_dir)
        assert not registry2.is_installed("my-step")

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_remove_rejects_symlinked_steps_base_dir(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        outside = project_dir.parent / "outside-steps"
        outside.mkdir(parents=True, exist_ok=True)
        steps_link = project_dir / ".specify" / "workflows" / "steps"
        steps_link.symlink_to(outside, target_is_directory=True)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "remove", "my-step"])

        assert result.exit_code != 0
        assert "Refusing to use symlinked step directory" in result.output


# A valid step ID (brackets are allowed) that Rich would otherwise parse as a
# style tag and drop from the output.
_MARKUP_STEP_ID = "[red]step"


def _flat(output: str) -> str:
    """Undo Rich line wrapping so long messages can be matched."""
    return output.replace("\n", "")


class TestWorkflowStepRemoveMarkupEscaping:
    """User-controlled values are printed literally, not parsed as markup."""

    def test_not_installed_error(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        result = CliRunner().invoke(
            app, ["workflow", "step", "remove", _MARKUP_STEP_ID]
        )

        assert result.exit_code == 1, result.output
        assert f"Step type '{_MARKUP_STEP_ID}' is not installed" in result.output

    def test_lock_failure_error(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        lock_path = project_dir / ".specify" / ".step-install.lock"
        if lock_path.exists():
            lock_path.unlink()
        lock_path.mkdir()

        result = CliRunner().invoke(
            app, ["workflow", "step", "remove", _MARKUP_STEP_ID]
        )

        assert result.exit_code == 1, result.output
        assert f"Failed to lock step removal '{_MARKUP_STEP_ID}'" in _flat(
            result.output
        )

    def test_orphan_warning_and_success_message(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        step_dir = _steps_dir(project_dir) / _MARKUP_STEP_ID
        step_dir.mkdir(parents=True)

        result = CliRunner().invoke(
            app, ["workflow", "step", "remove", _MARKUP_STEP_ID]
        )

        assert result.exit_code == 0, result.output
        output = _flat(result.output)
        assert f"'{_MARKUP_STEP_ID}' has no registry entry" in output
        assert f"Step type '{_MARKUP_STEP_ID}' uninstalled" in output
        assert not step_dir.exists()

    def test_directory_delete_failure_error(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.step.catalog import StepRegistry

        monkeypatch.chdir(project_dir)
        StepRegistry(project_dir).add(
            _MARKUP_STEP_ID, {"name": "x", "type_key": _MARKUP_STEP_ID}
        )
        step_dir = _steps_dir(project_dir) / _MARKUP_STEP_ID
        step_dir.mkdir(parents=True)
        real_rmtree = shutil.rmtree

        def _failing_rmtree(path, *args, **kwargs):
            if Path(path).name == _MARKUP_STEP_ID:
                raise OSError("simulated [bold]delete[/bold] failure")
            return real_rmtree(path, *args, **kwargs)

        monkeypatch.setattr(shutil, "rmtree", _failing_rmtree)

        result = CliRunner().invoke(
            app, ["workflow", "step", "remove", _MARKUP_STEP_ID]
        )

        assert result.exit_code == 1, result.output
        output = _flat(result.output)
        assert f"{_MARKUP_STEP_ID}: simulated [bold]delete[/bold] failure" in output
        assert step_dir.is_dir()
