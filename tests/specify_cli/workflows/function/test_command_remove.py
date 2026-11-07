"""``specify workflow function remove``."""

from __future__ import annotations

import os
import shutil

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.workflows.function import FunctionRegistry

from .helpers import functions_dir, install_dir, write_installed, write_package


@pytest.fixture
def cli(project_dir, monkeypatch):
    monkeypatch.chdir(project_dir)
    runner = CliRunner()
    return lambda *args: runner.invoke(app, ["workflow", "function", *args])


def install(cli, tmp_path, function_id="text", name="trim"):
    source = write_package(tmp_path / function_id, function_id, [{"name": name, "handler": "trim"}])
    assert cli("add", function_id, "--dev", str(source)).exit_code == 0


class TestRemove:
    def test_removes_directory_and_registry_entry(self, cli, project_dir, tmp_path):
        install(cli, tmp_path)
        result = cli("remove", "text")
        assert result.exit_code == 0, result.output
        assert "Workflow function package 'text' uninstalled" in result.output
        assert not install_dir(project_dir, "text").exists()
        assert not FunctionRegistry(project_dir).is_installed("text")

    def test_other_packages_are_untouched(self, cli, project_dir, tmp_path):
        install(cli, tmp_path, "alpha", "one")
        install(cli, tmp_path, "beta", "two")
        assert cli("remove", "alpha").exit_code == 0
        assert install_dir(project_dir, "beta").is_dir()
        assert FunctionRegistry(project_dir).is_installed("beta")

    def test_names_are_free_again_after_removal(self, cli, tmp_path):
        install(cli, tmp_path, "alpha", "shared")
        assert cli("remove", "alpha").exit_code == 0
        install(cli, tmp_path, "beta", "shared")

    def test_unknown_id(self, cli):
        result = cli("remove", "ghost")
        assert result.exit_code == 1 and "'ghost' is not installed" in result.output

    @pytest.mark.parametrize("bad", ["../x", ".cache", "function-registry.json", "a/b"])
    def test_invalid_id_is_rejected_and_nothing_is_touched(self, cli, project_dir, tmp_path, bad):
        install(cli, tmp_path)
        result = cli("remove", bad)
        assert result.exit_code == 1 and "function id" in result.output
        assert install_dir(project_dir, "text").is_dir()
        assert (functions_dir(project_dir) / "function-registry.json").is_file()

    def test_unregistered_directory_is_removed(self, cli, project_dir):
        write_installed(project_dir, "text")
        assert cli("remove", "text").exit_code == 0
        assert not install_dir(project_dir, "text").exists()

    def test_registry_only_entry_is_removed(self, cli, project_dir, tmp_path):
        install(cli, tmp_path)
        shutil.rmtree(install_dir(project_dir, "text"))
        assert cli("remove", "text").exit_code == 0
        assert not FunctionRegistry(project_dir).is_installed("text")

    def test_filesystem_failure_restores_the_registry_entry(self, cli, project_dir, tmp_path, monkeypatch):
        install(cli, tmp_path)

        real = shutil.rmtree
        target = install_dir(project_dir, "text")

        def fail(path, *args, **kwargs):
            if os.fspath(path) == os.fspath(target.resolve()):
                raise OSError("busy")
            return real(path, *args, **kwargs)

        monkeypatch.setattr(shutil, "rmtree", fail)
        result = cli("remove", "text")
        assert result.exit_code == 1 and "Failed to remove function directory" in result.output
        assert "busy" in result.output
        assert install_dir(project_dir, "text").is_dir()
        assert FunctionRegistry(project_dir).is_installed("text")

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_symlinked_package_is_not_followed(self, cli, project_dir, tmp_path):
        outside = write_package(tmp_path / "outside", "text")
        functions_dir(project_dir).mkdir(parents=True)
        install_dir(project_dir, "text").symlink_to(outside, target_is_directory=True)
        result = cli("remove", "text")
        assert result.exit_code == 1 and "Invalid function id 'text'" in result.output
        assert (outside / "function.yml").is_file()

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_symlinked_functions_directory_is_refused(self, cli, project_dir, tmp_path):
        outside = tmp_path / "outside"
        write_package(outside / "text", "text")
        functions_dir(project_dir).symlink_to(outside, target_is_directory=True)
        result = cli("remove", "text")
        assert result.exit_code == 1 and "symlinked" in result.output
        assert (outside / "text" / "function.yml").is_file()


class TestSharedRemoval:
    """Removal behaves like step removal: same lock, notes and orphan handling."""

    def test_both_remove_commands_use_the_shared_removal(self):
        import inspect

        from specify_cli.workflows.function import command_remove as function_remove
        from specify_cli.workflows.step import command_remove as step_remove

        assert "package_install.remove_package(" in inspect.getsource(function_remove)
        assert "package_install.remove_package(" in inspect.getsource(step_remove)
        assert "remove_package_locked(" in inspect.getsource(step_remove)

    def test_orphaned_directory_warns_and_is_removed(self, cli, project_dir):
        write_installed(project_dir, "text")
        result = cli("remove", "text")
        assert result.exit_code == 0
        output = " ".join(result.output.split())
        assert "'text' has no registry entry" in output and "uninstalled" in output
        assert not install_dir(project_dir, "text").exists()

    def test_registered_package_removal_prints_no_orphan_warning(self, cli, tmp_path):
        install(cli, tmp_path)
        assert "no registry entry" not in cli("remove", "text").output

    def test_directory_failure_keeps_timestamps_when_restoring(self, cli, project_dir, tmp_path, monkeypatch):
        install(cli, tmp_path)
        before = FunctionRegistry(project_dir).get("text")
        real = shutil.rmtree
        target = install_dir(project_dir, "text")

        def fail(path, *args, **kwargs):
            if os.fspath(path) == os.fspath(target.resolve()):
                raise OSError("busy")
            return real(path, *args, **kwargs)

        monkeypatch.setattr(shutil, "rmtree", fail)
        assert cli("remove", "text").exit_code == 1
        assert FunctionRegistry(project_dir).get("text") == before

    def test_failed_restore_is_reported_as_a_warning_before_the_error(self, cli, project_dir, tmp_path, monkeypatch):
        install(cli, tmp_path)
        real = shutil.rmtree
        target = install_dir(project_dir, "text")

        def fail(path, *args, **kwargs):
            if os.fspath(path) == os.fspath(target.resolve()):
                raise OSError("busy")
            return real(path, *args, **kwargs)

        monkeypatch.setattr(shutil, "rmtree", fail)
        monkeypatch.setattr(FunctionRegistry, "restore", lambda *a: (_ for _ in ()).throw(OSError("no disk")))
        result = cli("remove", "text")
        output = " ".join(result.output.split())
        assert result.exit_code == 1
        assert output.index("Warning: Failed to restore registry entry for 'text'") < output.index("Error: Failed to remove")

    def test_lock_failure_names_the_package_once(self, cli, project_dir):
        lock = project_dir / ".specify" / ".function-install.lock"
        lock.mkdir(parents=True, exist_ok=True)
        result = cli("remove", "text")
        flat = " ".join(result.output.split())
        assert result.exit_code == 1
        assert "Failed to lock function removal 'text'" in flat
        assert flat.count("Failed to acquire") == 0
