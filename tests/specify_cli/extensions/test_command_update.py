"""Tests for ``specify extension update``.

Mirrors ``specify_cli.extensions.command_update``.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import (
    ExtensionCatalog,
    ExtensionManager,
    HookExecutor,
)


class TestExtensionUpdateCLI:
    """CLI integration tests for extension update command."""

    @staticmethod
    def _create_extension_source(base_dir: Path, version: str, include_config: bool = False) -> Path:
        """Create a minimal extension source directory for install tests."""

        ext_dir = base_dir / f"test-ext-{version}"
        ext_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "test-ext",
                "name": "Test Extension",
                "version": version,
                "description": "A test extension",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.test-ext.hello",
                        "file": "commands/hello.md",
                        "description": "Test command",
                    }
                ]
            },
            "hooks": {
                "after_tasks": {
                    "command": "speckit.test-ext.hello",
                    "optional": True,
                }
            },
        }

        (ext_dir / "extension.yml").write_text(yaml.dump(manifest, sort_keys=False))
        commands_dir = ext_dir / "commands"
        commands_dir.mkdir(exist_ok=True)
        (commands_dir / "hello.md").write_text("---\ndescription: Test\n---\n\n$ARGUMENTS\n")
        if include_config:
            (ext_dir / "linear-config.yml").write_text("custom: true\nvalue: original\n")
        return ext_dir

    @staticmethod
    def _create_catalog_zip(
        zip_path: Path,
        version: str,
        manifest_path: str = "extension.yml",
        extra_manifest_path: str | None = None,
    ):
        """Create a minimal ZIP that passes extension_update ID validation."""
        import zipfile

        manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "test-ext",
                "name": "Test Extension",
                "version": version,
                "description": "A test extension",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {"commands": [{"name": "speckit.test-ext.hello", "file": "commands/hello.md"}]},
        }

        with zipfile.ZipFile(zip_path, "w") as zf:
            manifest_text = yaml.dump(manifest, sort_keys=False)
            zf.writestr(manifest_path, manifest_text)
            if extra_manifest_path is not None:
                zf.writestr(extra_manifest_path, manifest_text)

    @pytest.mark.parametrize(
        "manifest_path",
        [
            "../extension.yml",
            "/extension.yml",
            "./extension.yml",
            "C:/extension.yml",
        ],
    )
    def test_update_rejects_unsafe_manifest_path_before_removal(
        self, tmp_path, manifest_path
    ):
        """Unsafe manifest paths fail before the installed extension is removed."""
        from specify_cli import app

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(
            v1_dir, "0.1.0", catalog_name="previous-catalog"
        )
        installed_extension_dir = manager.extensions_dir / "test-ext"
        removed_paths = []
        real_rmtree = shutil.rmtree

        def track_rmtree(path, *args, **kwargs):
            removed_paths.append(Path(path).resolve())
            return real_rmtree(path, *args, **kwargs)

        zip_path = tmp_path / "unsafe-manifest.zip"
        self._create_catalog_zip(
            zip_path,
            "2.0.0",
            manifest_path=manifest_path,
        )

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "_install_allowed": True,
             }), \
             patch.object(
                 ExtensionCatalog,
                 "download_extension",
                 return_value=zip_path,
             ), \
             patch.object(shutil, "rmtree", side_effect=track_rmtree), \
             patch.object(ExtensionManager, "remove") as remove, \
             patch.object(ExtensionManager, "install_from_zip") as install:
            result = runner.invoke(
                app,
                ["extension", "update", "test-ext"],
                input="y\n",
                catch_exceptions=True,
            )

        assert result.exit_code == 1
        assert "Unsafe path in ZIP archive" in result.output
        remove.assert_not_called()
        install.assert_not_called()
        assert installed_extension_dir.resolve() not in removed_paths
        assert not list(
            (manager.extensions_dir / ".backup").glob(
                "update-*-*"
            )
        )
        assert ExtensionManager(project_dir).registry.get("test-ext")["version"] == "1.0.0"

    @pytest.mark.parametrize(
        ("first_path", "second_path"),
        [
            ("repo/extension.yml", "repo\\extension.yml"),
            ("repo/extension.yml", "repo/EXTENSION.YML"),
            ("caf\u00e9/extension.yml", "cafe\u0301/extension.yml"),
        ],
    )
    def test_update_rejects_normalized_manifest_collision_before_removal(
        self, tmp_path, first_path, second_path
    ):
        """Pre-scan and extraction must agree on the manifest identity."""
        import zipfile

        from typer.testing import CliRunner
        from specify_cli import app

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(v1_dir, "0.1.0")

        valid_manifest = yaml.safe_dump(
            {
                "schema_version": "1.0",
                "extension": {
                    "id": "test-ext",
                    "name": "Test Extension",
                    "version": "2.0.0",
                },
            }
        )
        injected_manifest = yaml.safe_dump(
            {
                "schema_version": "1.0",
                "extension": {
                    "id": "injected",
                    "name": "Injected",
                    "version": "2.0.0",
                },
            }
        )
        zip_path = tmp_path / "manifest-collision.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr(first_path, valid_manifest)
            zf.writestr(second_path, injected_manifest)

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "_install_allowed": True,
             }), \
             patch.object(
                 ExtensionCatalog,
                 "download_extension",
                 return_value=zip_path,
             ), \
             patch.object(ExtensionManager, "remove") as remove, \
             patch.object(ExtensionManager, "install_from_zip") as install:
            result = runner.invoke(
                app,
                ["extension", "update", "test-ext"],
                input="y\n",
                catch_exceptions=True,
            )

        assert result.exit_code == 1
        assert "multiple extension.yml" in result.output
        remove.assert_not_called()
        install.assert_not_called()
        assert ExtensionManager(project_dir).registry.get("test-ext")["version"] == "1.0.0"

    def test_update_preflights_entry_count_before_opening_zip(
        self, tmp_path
    ):
        """Manifest inspection must not bypass the bounded ZIP opener."""
        import struct

        from specify_cli import app

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(v1_dir, "0.1.0")

        zip_path = tmp_path / "too-many.zip"
        zip_path.write_bytes(
            struct.pack(
                "<4s4H2LH",
                b"PK\x05\x06",
                0,
                0,
                513,
                513,
                0,
                0,
                0,
            )
        )

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "_install_allowed": True,
             }), \
             patch.object(
                 ExtensionCatalog,
                 "download_extension",
                 return_value=zip_path,
             ), \
             patch(
                 "specify_cli._download_security.zipfile.ZipFile",
                 side_effect=AssertionError("ZipFile constructor was called"),
             ), \
             patch.object(ExtensionManager, "remove") as remove, \
             patch.object(ExtensionManager, "install_from_zip") as install:
            result = runner.invoke(
                app,
                ["extension", "update", "test-ext"],
                input="y\n",
                catch_exceptions=True,
            )

        assert result.exit_code == 1
        assert "too many entries" in result.output
        remove.assert_not_called()
        install.assert_not_called()

    @pytest.mark.parametrize(
        ("manifest_path", "extra_manifest_path"),
        [
            ("extension.yml", None),
            ("repo/extension.yml", None),
            ("extension.yml", "repo/extension.yml"),
        ],
    )
    def test_update_success_preserves_installed_at(
        self, tmp_path, manifest_path, extra_manifest_path
    ):
        """Successful update should keep original installed_at and apply new version."""
        from specify_cli import app

        runner = CliRunner()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0", include_config=True)
        manager.install_from_directory(v1_dir, "0.1.0")
        original_installed_at = manager.registry.get("test-ext")["installed_at"]
        original_config_content = (
            project_dir / ".specify" / "extensions" / "test-ext" / "linear-config.yml"
        ).read_text()

        zip_path = tmp_path / "test-ext-update.zip"
        self._create_catalog_zip(
            zip_path,
            "2.0.0",
            manifest_path=manifest_path,
            extra_manifest_path=extra_manifest_path,
        )
        v2_dir = self._create_extension_source(tmp_path, "2.0.0")

        def fake_install_from_zip(
            self_obj, _zip_path, speckit_version, *, catalog_name=None
        ):
            return self_obj.install_from_directory(
                v2_dir, speckit_version, catalog_name=catalog_name
            )

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                "name": "Test Extension",
                "version": "2.0.0",
                "_install_allowed": True,
                "_catalog_name": "updated-catalog",
             }), \
             patch.object(ExtensionCatalog, "download_extension", return_value=zip_path), \
             patch.object(ExtensionManager, "install_from_zip", fake_install_from_zip):
            result = runner.invoke(app, ["extension", "update", "test-ext"], input="y\n", catch_exceptions=True)

        assert result.exit_code == 0, result.output

        updated = ExtensionManager(project_dir).registry.get("test-ext")
        assert updated["version"] == "2.0.0"
        assert updated["installed_at"] == original_installed_at
        assert updated["source"] == {
            "kind": "catalog",
            "catalog": "updated-catalog",
        }
        restored_config_content = (
            project_dir / ".specify" / "extensions" / "test-ext" / "linear-config.yml"
        ).read_text()
        assert restored_config_content == original_config_content

    def test_update_installs_bundled_extension_from_local_copy(self, tmp_path):
        """A bundled extension (no download URL) updates from the copy shipped
        with the running spec-kit release instead of failing at download (#4345)."""
        from specify_cli import app

        runner = CliRunner()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(v1_dir, "0.1.0")
        v2_dir = self._create_extension_source(tmp_path, "2.0.0")

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "bundled": True,
                 "_install_allowed": True,
             }), \
             patch(
                 "specify_cli._locate_bundled_extension", return_value=v2_dir
             ), \
             patch.object(
                 ExtensionCatalog,
                 "download_extension",
                 side_effect=AssertionError("bundled update must not download"),
             ):
            result = runner.invoke(
                app, ["extension", "update", "test-ext"], input="y\n", catch_exceptions=True
            )

        flat = " ".join(result.output.split())
        assert result.exit_code == 0, result.output
        assert "Updated to v2.0.0" in flat
        assert ExtensionManager(project_dir).registry.get("test-ext")["version"] == "2.0.0"

    def test_update_bundled_blocked_when_local_copy_lags_catalog(self, tmp_path):
        """When the catalog advertises a newer version than the running release
        bundles, the update is reported as requiring a spec-kit upgrade instead
        of being offered and then failing."""
        from specify_cli import app

        runner = CliRunner()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(v1_dir, "0.1.0")

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "bundled": True,
                 "_install_allowed": True,
             }), \
             patch(
                 "specify_cli._locate_bundled_extension", return_value=v1_dir
             ):
            result = runner.invoke(
                app, ["extension", "update", "test-ext"], catch_exceptions=True
            )

        flat = " ".join(result.output.split())
        assert result.exit_code == 0, result.output
        assert "only ships v1.0.0" in flat
        assert "upgrade spec-kit" in flat
        assert "Update these extensions?" not in flat
        assert "All extensions are up to date!" not in flat
        assert ExtensionManager(project_dir).registry.get("test-ext")["version"] == "1.0.0"

    def test_update_bundled_blocked_when_local_copy_is_intermediate_version(self, tmp_path):
        """A bundled copy newer than the installation but older than the
        catalog must be blocked, not installed: an intermediate version would
        leave the project lagging the catalog while reporting success."""
        from specify_cli import app

        runner = CliRunner()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(v1_dir, "0.1.0")
        v2_dir = self._create_extension_source(tmp_path, "2.0.0")

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "3.0.0",
                 "bundled": True,
                 "_install_allowed": True,
             }), \
             patch(
                 "specify_cli._locate_bundled_extension", return_value=v2_dir
             ), \
             patch.object(
                 ExtensionCatalog,
                 "download_extension",
                 side_effect=AssertionError("blocked bundled update must not download"),
             ):
            result = runner.invoke(
                app, ["extension", "update", "test-ext"], catch_exceptions=True
            )

        flat = " ".join(result.output.split())
        assert result.exit_code == 0, result.output
        assert "only ships v2.0.0" in flat
        assert "upgrade spec-kit" in flat
        assert "Update these extensions?" not in flat
        assert ExtensionManager(project_dir).registry.get("test-ext")["version"] == "1.0.0"

    def test_update_installs_bundled_copy_newer_than_catalog(self, tmp_path):
        """A dev/source checkout can ship a copy newer than the fetched
        catalog advertises; the local copy is offered and installed."""
        from specify_cli import app

        runner = CliRunner()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(v1_dir, "0.1.0")
        v3_dir = self._create_extension_source(tmp_path, "3.0.0")

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "bundled": True,
                 "_install_allowed": True,
             }), \
             patch(
                 "specify_cli._locate_bundled_extension", return_value=v3_dir
             ):
            result = runner.invoke(
                app, ["extension", "update", "test-ext"], input="y\n", catch_exceptions=True
            )

        flat = " ".join(result.output.split())
        assert result.exit_code == 0, result.output
        assert "Updated to v3.0.0" in flat
        assert ExtensionManager(project_dir).registry.get("test-ext")["version"] == "3.0.0"

    def test_update_bundled_blocked_when_no_local_copy_exists(self, tmp_path):
        """A bundled catalog entry with no locally shipped copy points at a
        spec-kit upgrade instead of failing the update at download time."""
        from specify_cli import app

        runner = CliRunner()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(v1_dir, "0.1.0")

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "bundled": True,
                 "_install_allowed": True,
             }), \
             patch(
                 "specify_cli._locate_bundled_extension", return_value=None
             ):
            result = runner.invoke(
                app, ["extension", "update", "test-ext"], catch_exceptions=True
            )

        flat = " ".join(result.output.split())
        assert result.exit_code == 0, result.output
        assert "does not ship a local copy" in flat
        assert "upgrade spec-kit" in flat
        assert ExtensionManager(project_dir).registry.get("test-ext")["version"] == "1.0.0"

    def test_update_failure_rolls_back_registry_hooks_and_commands(self, tmp_path, monkeypatch):
        """Failed update should restore original registry, hooks, and command files."""
        from specify_cli import app
        import yaml

        # Isolate home directory so Hermes' global ~/.hermes/skills/ doesn't
        # interfere — without a real skills dir, Hermes is skipped during
        # command registration, keeping the test focused on Claude/Codex/etc.
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        runner = CliRunner()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(
            v1_dir, "0.1.0", catalog_name="original-catalog"
        )

        backup_registry_entry = manager.registry.get("test-ext")
        hooks_before = yaml.safe_load((project_dir / ".specify" / "extensions.yml").read_text())

        registered_commands = backup_registry_entry.get("registered_commands", {})
        command_files = []
        from specify_cli.agents import CommandRegistrar as AgentRegistrar
        agent_registrar = AgentRegistrar()
        for agent_name, cmd_names in registered_commands.items():
            if agent_name not in agent_registrar.AGENT_CONFIGS:
                continue
            agent_cfg = agent_registrar.AGENT_CONFIGS[agent_name]
            commands_dir = AgentRegistrar._resolve_agent_dir(
                agent_name, agent_cfg, project_dir
            )
            for cmd_name in cmd_names:
                output_name = AgentRegistrar._compute_output_name(agent_name, cmd_name, agent_cfg)
                cmd_path = commands_dir / f"{output_name}{agent_cfg['extension']}"
                command_files.append(cmd_path)

        assert command_files, "Expected at least one registered command file"
        for cmd_file in command_files:
            assert cmd_file.exists(), f"Expected command file to exist before update: {cmd_file}"

        zip_path = tmp_path / "test-ext-update.zip"
        self._create_catalog_zip(zip_path, "2.0.0")

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "_install_allowed": True,
             }), \
             patch.object(ExtensionCatalog, "download_extension", return_value=zip_path), \
             patch.object(ExtensionManager, "install_from_zip", side_effect=RuntimeError("install failed")):
            result = runner.invoke(app, ["extension", "update", "test-ext"], input="y\n", catch_exceptions=True)

        assert result.exit_code == 1, result.output

        restored_entry = ExtensionManager(project_dir).registry.get("test-ext")
        assert restored_entry == backup_registry_entry

        hooks_after = yaml.safe_load((project_dir / ".specify" / "extensions.yml").read_text())
        assert hooks_after == hooks_before

        for cmd_file in command_files:
            assert cmd_file.exists(), f"Expected command file to be restored after rollback: {cmd_file}"

    def test_update_failure_after_skill_registration_restores_old_skills(
        self, tmp_path, monkeypatch
    ):
        """Rollback must not depend on a new registry entry to restore skills."""
        import zipfile

        from typer.testing import CliRunner
        from unittest.mock import patch

        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        specify_dir = project_dir / ".specify"
        specify_dir.mkdir()
        copilot_agents_dir = project_dir / ".github" / "agents"
        copilot_agents_dir.mkdir(parents=True)
        (specify_dir / "init-options.json").write_text(
            json.dumps(
                {
                    "ai": "claude",
                    "ai_skills": True,
                    "script": "sh",
                }
            ),
            encoding="utf-8",
        )

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(
            v1_dir,
            "0.1.0",
            register_commands=False,
        )

        old_registry_entry = manager.registry.get("test-ext")
        skills_dir = project_dir / ".claude" / "skills"
        old_skill = skills_dir / "speckit-test-ext-hello"
        old_skill_content = (old_skill / "SKILL.md").read_text(encoding="utf-8")
        assert old_registry_entry["registered_skills"] == [old_skill.name]
        new_skill = skills_dir / "speckit-test-ext-new"
        new_skill.mkdir()
        user_skill_content = (
            "---\n"
            "name: user-new-skill\n"
            "description: User-owned skill\n"
            "metadata:\n"
            "  source: user\n"
            "---\n\nUSER SKILL\n"
        )
        (new_skill / "SKILL.md").write_text(
            user_skill_content,
            encoding="utf-8",
        )
        user_support_file = new_skill / "support.txt"
        user_support_file.write_text("USER CONTENT", encoding="utf-8")

        v2_dir = self._create_extension_source(tmp_path, "2.0.0")
        manifest_path = v2_dir / "extension.yml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest["provides"]["commands"].append(
            {
                "name": "speckit.test-ext.new",
                "file": "commands/new.md",
                "description": "New command",
            }
        )
        manifest["provides"]["commands"].append(
            {
                "name": "speckit.test-ext.fresh",
                "file": "commands/fresh.md",
                "description": "Fresh command",
            }
        )
        manifest_path.write_text(
            yaml.safe_dump(manifest, sort_keys=False),
            encoding="utf-8",
        )
        (v2_dir / "commands" / "hello.md").write_text(
            "---\ndescription: New hello\n---\n\nNEW HELLO\n",
            encoding="utf-8",
        )
        (v2_dir / "commands" / "new.md").write_text(
            "---\ndescription: New command\n---\n\nNEW COMMAND\n",
            encoding="utf-8",
        )
        (v2_dir / "commands" / "fresh.md").write_text(
            "---\ndescription: Fresh command\n---\n\nFRESH COMMAND\n",
            encoding="utf-8",
        )

        zip_path = tmp_path / "test-ext-update.zip"
        with zipfile.ZipFile(zip_path, "w") as archive:
            for source_path in v2_dir.rglob("*"):
                if source_path.is_file():
                    archive.write(
                        source_path,
                        source_path.relative_to(v2_dir),
                    )

        def fail_after_skill_registration(self, manifest):
            raise RuntimeError("Hook registration failed")

        runner = CliRunner()
        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(
                ExtensionCatalog,
                "get_extension_info",
                return_value={
                    "id": "test-ext",
                    "name": "Test Extension",
                    "version": "2.0.0",
                    "_install_allowed": True,
                },
            ),
            patch.object(
                ExtensionCatalog,
                "download_extension",
                return_value=zip_path,
            ),
            patch.object(
                HookExecutor,
                "register_hooks",
                fail_after_skill_registration,
            ),
        ):
            result = runner.invoke(
                app,
                ["extension", "update", "test-ext"],
                input="y\n",
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert "Hook registration failed" in result.output
        assert "Rollback successful" in result.output
        assert ExtensionManager(project_dir).registry.get("test-ext") == old_registry_entry
        assert (old_skill / "SKILL.md").read_text(encoding="utf-8") == old_skill_content
        assert user_support_file.read_text(encoding="utf-8") == "USER CONTENT"
        assert (
            new_skill / "SKILL.md"
        ).read_text(encoding="utf-8") == user_skill_content
        assert not (skills_dir / "speckit-test-ext-fresh").exists()
        for command_name in ("hello", "new", "fresh"):
            qualified_name = f"speckit.test-ext.{command_name}"
            assert not (
                copilot_agents_dir / f"{qualified_name}.agent.md"
            ).exists()
            assert not (
                project_dir
                / ".github"
                / "prompts"
                / f"{qualified_name}.prompt.md"
            ).exists()

    @pytest.mark.parametrize(
        ("manifest_text", "expected_detail"),
        [
            ("- not\n- a\n- mapping\n", "YAML mapping"),
            ("extension: []\n", "'extension' mapping"),
        ],
    )
    def test_update_rejects_malformed_zip_manifest(
        self, tmp_path, monkeypatch, manifest_text, expected_detail
    ):
        """Downloaded extension.yml shape must be valid before ID validation."""
        from specify_cli import app
        import zipfile

        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        runner = CliRunner()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(v1_dir, "0.1.0")
        original_registry_entry = manager.registry.get("test-ext")

        zip_path = tmp_path / "bad-manifest.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("extension.yml", manifest_text)

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "_install_allowed": True,
             }), \
             patch.object(ExtensionCatalog, "download_extension", return_value=zip_path):
            result = runner.invoke(
                app,
                ["extension", "update", "test-ext"],
                input="y\n",
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert "Invalid extension manifest in downloaded archive" in result.output
        assert expected_detail in result.output
        assert "AttributeError" not in result.output
        assert ExtensionManager(project_dir).registry.get("test-ext") == original_registry_entry
