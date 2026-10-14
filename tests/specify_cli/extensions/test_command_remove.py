"""Tests for ``specify extension remove``.

Mirrors ``specify_cli.extensions.command_remove``.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from typer.testing import CliRunner
import yaml

from specify_cli import app
from specify_cli.extensions import (
    ExtensionManager,
    ExtensionRegistry,
    HookExecutor,
)
from tests.specify_cli.extensions._helpers import (
    enable_native_hooks,
    installed_generic_hook_extension,
)


class TestExtensionRemoveCLI:
    """CLI tests for `specify extension remove` confirmation prompt wording."""

    def _install_ext(self, project_dir, ext_dir):
        """Install extension and return the manager."""
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)
        return manager

    def test_default_remove_legacy_hook_without_projection(self, project_dir, extension_dir):
        manifest_path = extension_dir / "extension.yml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest["hooks"] = {"custom:after": {"command": "speckit.test-ext.hello"}}
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
        self._install_ext(project_dir, extension_dir)
        with patch.object(Path, "cwd", return_value=project_dir):
            result = CliRunner().invoke(app, ["extension", "remove", "test-ext", "--force"])
        assert result.exit_code == 0, result.output
        assert not ExtensionManager(project_dir).registry.is_installed("test-ext")
        assert not (project_dir / ".specify/hook-dispatch").exists()

    def test_remove_confirmation_singular_command(self, tmp_path, extension_dir):
        """Confirmation prompt should say '1 command' (singular) when one command registered."""

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        manager = self._install_ext(project_dir, extension_dir)
        # Inject registered_commands with 1 entry so cmd_count == 1
        manager.registry.update("test-ext", {"registered_commands": {"claude": ["speckit.test-ext.hello"]}})

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app, ["extension", "remove", "test-ext"], input="n\n", catch_exceptions=False
            )

        assert "1 command" in result.output
        assert "1 commands" not in result.output

    def test_remove_confirmation_plural_commands(self, tmp_path, extension_dir):
        """Confirmation prompt should say '2 commands' (plural) when two commands registered."""

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        manager = self._install_ext(project_dir, extension_dir)
        # Inject registered_commands with 2 entries so cmd_count == 2
        manager.registry.update("test-ext", {"registered_commands": {"claude": ["speckit.test-ext.hello", "speckit.test-ext.run"]}})

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app, ["extension", "remove", "test-ext"], input="n\n", catch_exceptions=False
            )

        assert "2 commands" in result.output

    def test_remove_output_escapes_extension_id_markup(self, tmp_path):
        """Removal paths and reinstall hints must not parse extension IDs as markup."""
        from typer.testing import CliRunner

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        extension_id = "[red]bad[/red]"
        installed = [
            {
                "id": extension_id,
                "name": "Bad Extension",
                "version": "1.0.0",
                "description": "Test extension",
                "enabled": True,
            }
        ]

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionManager, "list_installed", return_value=installed), \
             patch.object(ExtensionManager, "get_extension", return_value=SimpleNamespace(commands=[])), \
             patch.object(ExtensionRegistry, "get", return_value={"registered_commands": {}, "registered_skills": []}), \
             patch.object(ExtensionManager, "remove", return_value=True):
            result = runner.invoke(
                app,
                ["extension", "remove", extension_id, "--force"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert ".specify/extensions/.backup/[red]bad[/red]/" in result.output
        assert "specify extension add [red]bad[/red]" in result.output

    def test_remove_reports_invalid_hooks_without_mutating_installation(
        self, project_dir, extension_dir
    ):
        enable_native_hooks(project_dir)
        manager = self._install_ext(project_dir, extension_dir)
        config = project_dir / ".specify/extensions.yml"
        config.write_text("hooks:\n  before_plan: invalid\n", encoding="utf-8")
        with patch.object(Path, "cwd", return_value=project_dir):
            result = CliRunner().invoke(app, ["extension", "remove", "test-ext", "--force"])
        assert result.exit_code == 1
        assert "expected a list" in result.output
        assert manager.registry.is_installed("test-ext")
        assert (project_dir / ".specify/extensions/test-ext").exists()
        assert config.read_text(encoding="utf-8") == "hooks:\n  before_plan: invalid\n"

    def test_remove_publication_failure_retains_generic_installation(
        self, tmp_path, extension_dir
    ):
        project, _, artifact = installed_generic_hook_extension(
            tmp_path, extension_dir, native_hooks=True
        )
        manager = ExtensionManager(project)
        extension_dir = project / ".specify/extensions/test-ext"
        config = project / ".specify/extensions.yml"
        cache = project / ".specify/hook-dispatch"
        original = (artifact.read_bytes(), config.read_bytes(), (cache / "source.yml").read_bytes())
        original_save = HookExecutor.save_project_config

        def fail_hook_removal(executor, updated):
            if not updated.get("hooks", {}).get("before_plan"):
                raise OSError("projection failed")
            return original_save(executor, updated)

        with patch.object(Path, "cwd", return_value=project), \
             patch.object(HookExecutor, "save_project_config", fail_hook_removal):
            result = CliRunner().invoke(app, ["extension", "remove", "test-ext", "--force"])
        assert result.exit_code == 1
        assert "projection failed" in result.output
        assert manager.registry.is_installed("test-ext")
        assert extension_dir.is_dir()
        assert (artifact.read_bytes(), config.read_bytes(), (cache / "source.yml").read_bytes()) == original

    def test_remove_artifact_failure_restores_published_hooks(
        self, tmp_path, extension_dir
    ):
        project, _, artifact = installed_generic_hook_extension(
            tmp_path, extension_dir, native_hooks=True
        )
        manager = ExtensionManager(project)
        source = project / ".specify/extensions/test-ext"
        config = project / ".specify/extensions.yml"
        cache = project / ".specify/hook-dispatch"
        original = (artifact.read_bytes(), config.read_bytes(), (cache / "source.yml").read_bytes())
        with patch.object(Path, "cwd", return_value=project), \
             patch.object(ExtensionManager, "_remove_generic_artifact_paths", side_effect=OSError("cleanup failed")):
            result = CliRunner().invoke(app, ["extension", "remove", "test-ext", "--force"])
        assert result.exit_code == 1
        assert "cleanup failed" in result.output
        assert manager.registry.is_installed("test-ext")
        assert source.is_dir()
        assert (artifact.read_bytes(), config.read_bytes(), (cache / "source.yml").read_bytes()) == original
        assert yaml.safe_load(config.read_text())["hooks"]["before_plan"][0]["extension"] == "test-ext"
        assert (cache / "before_plan.json").is_file()

    def test_remove_partial_cleanup_restores_hooks_not_artifacts(
        self, tmp_path, extension_dir
    ):
        project, _, artifact = installed_generic_hook_extension(
            tmp_path, extension_dir, native_hooks=True
        )
        manager = ExtensionManager(project)
        config = project / ".specify/extensions.yml"
        cache = project / ".specify/hook-dispatch"
        original = (config.read_bytes(), (cache / "before_plan.json").read_bytes())
        original_remove = ExtensionManager._remove_generic_artifact_paths

        def remove_then_fail(manager, extension_id, metadata):
            original_remove(manager, extension_id, metadata)
            raise OSError("cleanup failed after artifact removal")

        with patch.object(Path, "cwd", return_value=project), \
             patch.object(ExtensionManager, "_remove_generic_artifact_paths", remove_then_fail):
            result = CliRunner().invoke(app, ["extension", "remove", "test-ext", "--force"])
        assert result.exit_code == 1
        assert "cleanup failed after artifact removal" in result.output
        assert manager.registry.is_installed("test-ext")
        assert not artifact.exists()
        assert (config.read_bytes(), (cache / "before_plan.json").read_bytes()) == original
        assert (cache / "source.yml").read_bytes() == config.read_bytes()

    def test_remove_cleanup_failure_preserves_exact_yaml_and_cache(
        self, tmp_path, extension_dir
    ):
        project, manager, artifact = installed_generic_hook_extension(
            tmp_path, extension_dir, native_hooks=True
        )
        config = project / ".specify/extensions.yml"
        config.write_bytes(b"# preserve this comment\r\n" + config.read_bytes().replace(b"\n", b"\r\n"))
        HookExecutor(project).migrate_project_config()
        cache = project / ".specify/hook-dispatch"
        original_yaml = config.read_bytes()
        original_cache = {entry.name: entry.read_bytes() for entry in cache.iterdir()}

        with patch.object(
            manager, "_remove_generic_artifact_paths", side_effect=OSError("cleanup failed")
        ):
            with pytest.raises(OSError, match="cleanup failed"):
                manager.remove("test-ext")
        assert manager.registry.is_installed("test-ext")
        assert artifact.exists()
        assert config.read_bytes() == original_yaml
        assert {entry.name: entry.read_bytes() for entry in cache.iterdir()} == original_cache

    def test_remove_cleanup_failure_restores_absent_yaml_and_cache(
        self, tmp_path, extension_dir
    ):
        project, manager, _ = installed_generic_hook_extension(
            tmp_path, extension_dir, native_hooks=True
        )
        config = project / ".specify/extensions.yml"
        cache = project / ".specify/hook-dispatch"
        config.unlink()
        shutil.rmtree(cache)
        with patch.object(
            manager, "_remove_generic_artifact_paths", side_effect=OSError("cleanup failed")
        ):
            with pytest.raises(OSError, match="cleanup failed"):
                manager.remove("test-ext")
        assert manager.registry.is_installed("test-ext")
        assert not config.exists()
        assert not cache.exists()

    def test_remove_reports_failed_hook_restoration(
        self, tmp_path, extension_dir
    ):
        project, _, _ = installed_generic_hook_extension(
            tmp_path, extension_dir, native_hooks=True
        )

        with patch.object(Path, "cwd", return_value=project), \
             patch.object(ExtensionManager, "_remove_generic_artifact_paths", side_effect=OSError("cleanup failed")), \
             patch("specify_cli.extensions._hook_projection.restore", side_effect=OSError("restore failed")):
            result = CliRunner().invoke(app, ["extension", "remove", "test-ext", "--force"])
        assert result.exit_code == 1
        assert "cleanup failed" in result.output
        assert "hook rollback failed" in result.output
        assert "restore failed" in " ".join(result.output.split())
