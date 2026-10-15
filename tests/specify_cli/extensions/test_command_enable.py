"""Tests for ``specify extension enable``.

Mirrors ``specify_cli.extensions.command_enable``.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner
import yaml

from specify_cli import app
from specify_cli.extensions import (
    ExtensionError,
    ExtensionManager,
    ExtensionRegistry,
    HookExecutor,
)
from specify_cli.extensions import _commands
from tests.specify_cli.extensions._helpers import enable_native_hooks, installed_generic_hook_extension


class TestExtensionEnableCLI:
    """CLI tests for ``specify extension enable``."""

    def test_enable_cli_delegates_transaction_to_domain(self, tmp_path):
        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)
        installed = [{"id": "test-ext", "name": "Test Extension", "enabled": False}]
        with patch.object(Path, "cwd", return_value=project), \
             patch.object(ExtensionManager, "list_installed", return_value=installed), \
             patch.object(ExtensionManager, "enable", return_value=True) as operation, \
             patch.object(HookExecutor, "load_project_config_for_update", side_effect=AssertionError("CLI loaded hook config")), \
             patch.object(ExtensionRegistry, "update", side_effect=AssertionError("CLI updated registry")), \
             patch.object(_commands, "_refresh_events_and_warn"), \
             patch.object(ExtensionManager, "scaffold_config", return_value=([], [], [])):
            result = CliRunner().invoke(app, ["extension", "enable", "test-ext"])
        assert result.exit_code == 0, result.output
        operation.assert_called_once_with("test-ext")

    @pytest.mark.parametrize("native_hooks", [False, True])
    def test_disable_enable_preserves_declaration_disabled_hook_only_when_opted_in(
        self, project_dir, extension_dir, native_hooks
    ):
        if native_hooks:
            enable_native_hooks(project_dir)
        manifest_path = extension_dir / "extension.yml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest["hooks"] = {
            "before_plan": [
                {"command": "speckit.test-ext.hello", "enabled": False},
                {"command": "speckit.test-ext.other", "enabled": True},
            ]
        }
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)
        config_path = project_dir / ".specify/extensions.yml"
        before = yaml.safe_load(config_path.read_text(encoding="utf-8"))["hooks"]["before_plan"]
        assert [hook["enabled"] for hook in before] == ([False, True] if native_hooks else [True, True])

        assert manager.disable("test-ext") is True
        assert all(
            not hook["enabled"]
            for hook in yaml.safe_load(config_path.read_text(encoding="utf-8"))["hooks"]["before_plan"]
        )
        assert manager.enable("test-ext") is True
        assert manager.enable("test-ext") is False
        after = yaml.safe_load(config_path.read_text(encoding="utf-8"))["hooks"]["before_plan"]
        assert [hook["enabled"] for hook in after] == [hook["enabled"] for hook in before]
        cache = project_dir / ".specify/hook-dispatch"
        if native_hooks:
            assert [
                hook["command"]
                for hook in json.loads((cache / "before_plan.json").read_text())["hooks"]
            ] == ["speckit.test-ext.other"]
        else:
            assert not cache.exists()

    def test_enable_registry_error_escapes_extension_id_markup(self, tmp_path):
        """Registry-corruption errors should render extension IDs literally."""

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
                "enabled": False,
            }
        ]

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionManager, "list_installed", return_value=installed), \
             patch.object(ExtensionRegistry, "get", return_value=None):
            result = runner.invoke(
                app,
                ["extension", "enable", extension_id],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert "Extension '[red]bad[/red]' not found in registry" in result.output

    def test_enable_publication_failure_restores_generic_disabled_state(
        self, tmp_path, extension_dir
    ):
        project, _, artifact = installed_generic_hook_extension(
            tmp_path, extension_dir, native_hooks=True
        )
        with patch.object(Path, "cwd", return_value=project):
            disabled = CliRunner().invoke(app, ["extension", "disable", "test-ext"])
        assert disabled.exit_code == 0, disabled.output
        assert not artifact.exists()
        config = project / ".specify/extensions.yml"
        original_config = config.read_bytes()
        with patch.object(Path, "cwd", return_value=project), \
             patch.object(HookExecutor, "save_project_config", side_effect=OSError("projection failed")):
            result = CliRunner().invoke(app, ["extension", "enable", "test-ext"])
        assert result.exit_code == 1
        assert "projection failed" in result.output
        assert ExtensionManager(project).registry.get("test-ext")["enabled"] is False, result.output
        assert not artifact.exists()
        assert config.read_bytes() == original_config

    def test_domain_enable_rejects_changed_hook_identity_before_mutation(
        self, tmp_path, extension_dir
    ):
        project, manager, artifact = installed_generic_hook_extension(
            tmp_path, extension_dir, native_hooks=True
        )
        assert manager.disable("test-ext")
        metadata = manager.registry.get("test-ext")
        metadata["disabled_hook_states"][0]["command"] = "speckit.test-ext.other"
        manager.registry.restore("test-ext", metadata)
        config = project / ".specify/extensions.yml"
        original = config.read_bytes()
        with pytest.raises(ExtensionError, match="owned hooks changed since disable"):
            manager.enable("test-ext")
        assert manager.registry.get("test-ext")["enabled"] is False
        assert not artifact.exists()
        assert config.read_bytes() == original

    def test_domain_enable_publication_failure_retains_disabled_hook_state(
        self, tmp_path, extension_dir
    ):
        project, manager, artifact = installed_generic_hook_extension(
            tmp_path, extension_dir, native_hooks=True
        )
        assert manager.disable("test-ext")
        previous = manager.registry.get("test-ext")
        config = project / ".specify/extensions.yml"
        original = config.read_bytes()
        with patch.object(HookExecutor, "save_project_config", side_effect=OSError("save failed")):
            with pytest.raises(OSError, match="save failed"):
                manager.enable("test-ext")
        assert manager.registry.get("test-ext") == previous
        assert not artifact.exists()
        assert config.read_bytes() == original

    def test_enable_older_disabled_extension_uses_manifest_declared_states(
        self, project_dir, extension_dir
    ):
        enable_native_hooks(project_dir)
        manifest_path = extension_dir / "extension.yml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest["hooks"] = {
            "before_plan": [
                {"command": "speckit.test-ext.hello", "enabled": False},
                {"command": "speckit.test-ext.other", "enabled": True},
            ]
        }
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)
        assert manager.disable("test-ext")
        previous = manager.registry.get("test-ext")
        previous.pop("disabled_hook_states")
        manager.registry.restore("test-ext", previous)
        assert manager.enable("test-ext")
        config = yaml.safe_load((project_dir / ".specify/extensions.yml").read_text())
        assert [hook["enabled"] for hook in config["hooks"]["before_plan"]] == [False, True]

    def test_cli_enable_keeps_manifest_disabled_hook_out_of_projection(
        self, project_dir, extension_dir
    ):
        enable_native_hooks(project_dir)
        manifest_path = extension_dir / "extension.yml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest["hooks"] = {
            "before_plan": [
                {"command": "speckit.test-ext.hello", "enabled": False},
                {"command": "speckit.test-ext.other", "enabled": True},
            ]
        }
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)
        assert manager.disable("test-ext")
        with patch.object(Path, "cwd", return_value=project_dir):
            result = CliRunner().invoke(app, ["extension", "enable", "test-ext"])
        assert result.exit_code == 0, result.output
        config = yaml.safe_load((project_dir / ".specify/extensions.yml").read_text())
        assert [hook["enabled"] for hook in config["hooks"]["before_plan"]] == [False, True]
        cache = project_dir / ".specify/hook-dispatch/before_plan.json"
        assert [
            hook["command"] for hook in json.loads(cache.read_text())["hooks"]
        ] == ["speckit.test-ext.other"]

    def test_opted_in_enable_restores_user_override_not_manifest_default(
        self, project_dir, extension_dir
    ):
        enable_native_hooks(project_dir)
        manifest_path = extension_dir / "extension.yml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest["hooks"] = {
            "before_plan": [
                {"command": "speckit.test-ext.hello", "enabled": False},
                {"command": "speckit.test-ext.other", "enabled": True},
            ]
        }
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)
        executor = HookExecutor(project_dir)
        config = executor.load_project_config_for_update()
        config["hooks"]["before_plan"][0]["enabled"] = True
        config["hooks"]["before_plan"][1]["enabled"] = False
        executor.save_project_config(config)

        assert manager.disable("test-ext")
        assert manager.enable("test-ext")
        restored = yaml.safe_load(executor.config_file.read_text())
        assert [hook["enabled"] for hook in restored["hooks"]["before_plan"]] == [True, False]
        assert [
            hook["command"] for hook in json.loads(
                (project_dir / ".specify/hook-dispatch/before_plan.json").read_text()
            )["hooks"]
        ] == ["speckit.test-ext.hello"]
