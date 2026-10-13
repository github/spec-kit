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

from specify_cli import app
from specify_cli.extensions import (
    ExtensionManager,
    ExtensionRegistry,
    HookExecutor,
)


@pytest.mark.parametrize("command", ["enable", "disable", "remove"])
@pytest.mark.parametrize("invalid", [
    "hooks: [broken]\n",
    "hooks:\n  before_plan: [broken]\n",
    "hooks: [\n",
])
def test_mutations_preserve_state_on_invalid_hook_config(
    tmp_path, extension_dir, command, invalid
):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".specify").mkdir()
    manager = ExtensionManager(project)
    manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)
    manager.registry.update("test-ext", {"enabled": command == "disable"})
    config = HookExecutor(project).config_file
    config.write_text(invalid, encoding="utf-8")
    original = config.read_bytes()
    registry = manager.registry.get("test-ext")
    extension_path = manager.extensions_dir / "test-ext"
    files = {p.relative_to(extension_path): p.read_bytes()
             for p in extension_path.rglob("*") if p.is_file()}
    cache = project / ".specify/hook-dispatch"
    projection = {p.name: p.read_bytes() for p in cache.iterdir()}

    args = ["extension", command, "test-ext"]
    if command == "remove":
        args.append("--force")
    with patch.object(Path, "cwd", return_value=project):
        result = CliRunner().invoke(app, args, catch_exceptions=True)

    assert result.exit_code == 1, result.output
    assert "Invalid .specify/extensions.yml" in result.output
    assert config.read_bytes() == original
    assert manager.registry.get("test-ext") == registry
    assert {p.relative_to(extension_path): p.read_bytes()
            for p in extension_path.rglob("*") if p.is_file()} == files
    assert {p.name: p.read_bytes() for p in cache.iterdir()} == projection


@pytest.mark.parametrize("command", ["enable", "disable", "remove"])
def test_mutations_preserve_state_on_hook_cache_file_collision(
    tmp_path, extension_dir, command
):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".specify").mkdir()
    manager = ExtensionManager(project)
    manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)
    manager.registry.update("test-ext", {"enabled": command == "disable"})
    config = HookExecutor(project).config_file
    original = config.read_bytes()
    registry = manager.registry.get("test-ext")
    extension_path = manager.extensions_dir / "test-ext"
    files = {p.relative_to(extension_path): p.read_bytes()
             for p in extension_path.rglob("*") if p.is_file()}
    cache = project / ".specify/hook-dispatch"
    shutil.rmtree(cache)
    cache.write_text("collision", encoding="utf-8")

    args = ["extension", command, "test-ext"]
    if command == "remove":
        args.append("--force")
    with patch.object(Path, "cwd", return_value=project):
        result = CliRunner().invoke(app, args, catch_exceptions=True)

    assert result.exit_code == 1, result.output
    assert "hook dispatch cache" in result.output
    assert config.read_bytes() == original
    assert manager.registry.get("test-ext") == registry
    assert {p.relative_to(extension_path): p.read_bytes()
            for p in extension_path.rglob("*") if p.is_file()} == files
    assert cache.read_text(encoding="utf-8") == "collision"


@pytest.mark.parametrize("command", ["enable", "disable", "remove"])
@pytest.mark.parametrize("entry", ["orphan.json", "orphan.sha256", "unrelated"])
def test_mutations_preserve_projection_on_cache_directory_entry(
    tmp_path, extension_dir, command, entry
):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".specify").mkdir()
    manager = ExtensionManager(project)
    manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)
    manager.registry.update("test-ext", {"enabled": command == "disable"})
    registry = manager.registry.get("test-ext")
    extension_path = manager.extensions_dir / "test-ext"
    files = {p.relative_to(extension_path): p.read_bytes()
             for p in extension_path.rglob("*") if p.is_file()}
    executor = HookExecutor(project)
    config = executor.config_file
    original = config.read_bytes()
    cache = project / ".specify/hook-dispatch"
    (cache / entry).mkdir()
    projection = {p.name: p.read_bytes() for p in cache.iterdir() if p.is_file()}

    args = ["extension", command, "test-ext"]
    if command == "remove":
        args.append("--force")
    with patch.object(Path, "cwd", return_value=project):
        result = CliRunner().invoke(app, args, catch_exceptions=True)

    assert result.exit_code == 1, result.output
    assert "non-file hook dispatch cache entry" in result.output
    assert config.read_bytes() == original
    assert manager.registry.get("test-ext") == registry
    assert {p.relative_to(extension_path): p.read_bytes()
            for p in extension_path.rglob("*") if p.is_file()} == files
    assert (cache / entry).is_dir()
    assert {p.name: p.read_bytes() for p in cache.iterdir() if p.is_file()} == projection


@pytest.mark.parametrize("command", ["enable", "disable", "remove"])
def test_mutations_preserve_state_on_dangling_config_symlink(
    tmp_path, extension_dir, command
):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".specify").mkdir()
    manager = ExtensionManager(project)
    manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)
    manager.registry.update("test-ext", {"enabled": command == "disable"})
    registry = manager.registry.get("test-ext")
    extension_path = manager.extensions_dir / "test-ext"
    files = {p.relative_to(extension_path): p.read_bytes()
             for p in extension_path.rglob("*") if p.is_file()}
    cache = project / ".specify/hook-dispatch"
    projection = {p.name: p.read_bytes() for p in cache.iterdir()}
    config = HookExecutor(project).config_file
    config.unlink()
    target = tmp_path / "missing-extensions.yml"
    try:
        config.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"file symlinks unavailable: {exc}")
    assert not config.exists()

    args = ["extension", command, "test-ext"]
    if command == "remove":
        args.append("--force")
    with patch.object(Path, "cwd", return_value=project):
        result = CliRunner().invoke(app, args, catch_exceptions=True)

    assert result.exit_code == 1, result.output
    assert "symlinked .specify/extensions.yml" in result.output
    assert config.is_symlink() and not target.exists()
    assert manager.registry.get("test-ext") == registry
    assert {p.relative_to(extension_path): p.read_bytes()
            for p in extension_path.rglob("*") if p.is_file()} == files
    assert {p.name: p.read_bytes() for p in cache.iterdir()} == projection


class TestExtensionRemoveCLI:
    """CLI tests for `specify extension remove` confirmation prompt wording."""

    def _install_ext(self, project_dir, ext_dir):
        """Install extension and return the manager."""
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)
        return manager

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
