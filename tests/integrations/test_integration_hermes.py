"""Tests for HermesIntegration.

Hermes is special among SkillsIntegration subclasses: it writes skills
to ``~/.hermes/skills/`` (global) rather than the project-local
``.hermes/skills/`` directory.  A project-local marker (empty directory)
is created so extension commands (e.g. git) can detect Hermes.

All tests that touch ``~/.hermes/`` use ``monkeypatch`` to isolate
``Path.home()`` to a temp directory so the test suite is hermetic and
non-destructive to a developer's real Hermes installation.
"""

import json
import shutil
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


def _fake_home(tmp_path: Path) -> Path:
    """Create and return an isolated home directory under *tmp_path*."""
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    return home


class TestHermesIntegration(SkillsIntegrationTests):
    KEY = "hermes"
    FOLDER = ".hermes/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = "~/.hermes/skills"

    def test_path_guard_uses_python311_junction_fallback(
        self, tmp_path, monkeypatch
    ):
        from specify_cli.integrations.hermes import _has_symlinked_component
        import specify_cli._utils as utils

        home = _fake_home(tmp_path)
        junction = home / ".hermes" / "skills" / "speckit-plan"
        junction.mkdir(parents=True)
        target = junction / "SKILL.md"
        mount_point_tag = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)

        monkeypatch.setattr(Path, "is_junction", None, raising=False)
        monkeypatch.setattr(utils.os, "name", "nt")
        monkeypatch.setattr(
            Path,
            "lstat",
            lambda path: SimpleNamespace(
                st_mode=stat.S_IFDIR | 0o755,
                st_reparse_tag=mount_point_tag if path == junction else 0
            ),
        )

        assert _has_symlinked_component(target, home)

    # -- Hermes-specific setup: skills go to ~/.hermes/skills/ -------------

    def test_setup_writes_to_global_skills_dir(self, tmp_path, monkeypatch):
        """Skills are written to ~/.hermes/skills/, not project-local."""
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        skill_files = [f for f in created if "scripts" not in f.parts]

        assert len(skill_files) > 0, "No skill files were created"
        for f in skill_files:
            # Every skill file should be under ~/.hermes/skills/speckit-*/
            expected_prefix = str(home / ".hermes" / "skills")
            assert str(f).startswith(expected_prefix), (
                f"{f} is not under ~/.hermes/skills/"
            )

    def test_local_marker_dir_created(self, tmp_path, monkeypatch):
        """Project-local .hermes/skills/ should exist but be empty."""
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        marker = tmp_path / ".hermes" / "skills"
        assert marker.is_dir(), "Marker directory was not created"
        # Should be empty (no SKILL.md files)
        children = list(marker.iterdir())
        assert children == [], f"Marker directory should be empty, got: {children}"

    def test_setup_rejects_symlinked_global_skill_file(
        self, tmp_path, monkeypatch
    ):
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)
        external = tmp_path / "external-skill.md"
        external.write_text("external\n", encoding="utf-8")
        skill_file = home / ".hermes" / "skills" / "speckit-plan" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        try:
            skill_file.symlink_to(external)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks are not available")

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        with pytest.raises(ValueError, match="symlinked path component"):
            i.setup(tmp_path, m)

        assert external.read_text(encoding="utf-8") == "external\n"
        assert not (tmp_path / ".hermes").exists()

    def test_setup_rejects_symlinked_project_marker_before_global_writes(
        self, tmp_path, monkeypatch
    ):
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)
        external = tmp_path / "external-marker"
        external.mkdir()
        try:
            (tmp_path / ".hermes").symlink_to(external, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks are not available")

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        with pytest.raises(ValueError, match="symlinked path component"):
            i.setup(tmp_path, m)

        assert list(external.iterdir()) == []
        assert not (home / ".hermes").exists()

    # -- Override shared tests that assume project-local skills ------------

    def test_setup_writes_to_correct_directory(self, tmp_path, monkeypatch):
        """Override: Hermes writes to global, not project-local."""
        self.test_setup_writes_to_global_skills_dir(tmp_path, monkeypatch)

    def test_plan_skill_has_no_context_placeholder(self, tmp_path, monkeypatch):
        """The core plan skill must not carry a context-file placeholder —
        agent context files are owned by the opt-in agent-context extension."""
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        # Find the plan skill in global ~/.hermes/skills/
        plan_file = home / ".hermes" / "skills" / "speckit-plan" / "SKILL.md"
        assert plan_file.exists(), f"Plan skill {plan_file} not created globally"
        content = plan_file.read_text(encoding="utf-8")
        assert "__CONTEXT_FILE__" not in content, (
            "Plan skill has unprocessed __CONTEXT_FILE__ placeholder"
        )

    def test_all_files_tracked_in_manifest(self, tmp_path, monkeypatch):
        """Override: Hermes does not track skills in the project manifest
        since they live globally.  Only project-local files (scripts,
        templates, context) are tracked."""
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        for f in created:
            # Global files (in ~/.hermes/) are not tracked in manifest
            if str(f).startswith(str(home)):
                continue
            rel = f.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in m.files, f"{rel} not tracked in manifest"

    def test_install_uninstall_roundtrip(self, tmp_path, monkeypatch):
        """Override: Hermes uninstall removes global skills + local marker."""
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.install(tmp_path, m)
        assert len(created) > 0
        m.save()
        # All SKILL.md files should exist globally
        for f in created:
            if "SKILL.md" in str(f):
                assert f.exists(), f"{f} does not exist"
        # Global skills are removed on teardown without needing force
        removed, skipped = i.teardown(tmp_path, m, force=False)
        for f in created:
            if "SKILL.md" in str(f):
                assert not f.exists(), f"{f} should have been removed"
        # Local marker should be gone
        assert not (tmp_path / ".hermes" / "skills").exists()

    def test_modified_file_survives_uninstall(self, tmp_path, monkeypatch):
        """Override: Hermes global skills are ALWAYS removed on uninstall
        (they live outside the project root and aren't hash-tracked in the
        manifest), so a modified global skill is still removed — matching
        the standard behaviour where all integration files are cleaned up."""
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.install(tmp_path, m)
        m.save()
        # Pick a global skill file
        skill_files = [f for f in created if "SKILL.md" in str(f)]
        assert len(skill_files) > 0
        modified_file = skill_files[0]
        modified_file.write_text("user modified this", encoding="utf-8")
        removed, skipped = i.uninstall(tmp_path, m)
        assert not modified_file.exists(), (
            "Modified global skill should be removed on teardown (standard behaviour)"
        )

    def test_modified_global_skill_removed_on_teardown(self, tmp_path, monkeypatch):
        """Override: Hermes global skills are removed on uninstall regardless
        of the force flag, matching standard integration behaviour."""
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.install(tmp_path, m)
        m.save()
        # Pick a global skill file
        skill_files = [f for f in created if "SKILL.md" in str(f)]
        assert len(skill_files) > 0
        modified_file = skill_files[0]
        modified_file.write_text("user modified this", encoding="utf-8")
        # Global skills are removed on teardown regardless of force flag
        removed, skipped = i.teardown(tmp_path, m, force=False)
        assert not modified_file.exists(), (
            "Modified global skill should be removed on teardown (standard behaviour)"
        )

    def test_pre_existing_skills_not_removed(self, tmp_path, monkeypatch):
        """Pre-existing non-speckit global skills should survive Hermes uninstall."""
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)

        i = get_integration(self.KEY)
        # Create a foreign skill in the global dir first
        global_skills_dir = i._hermes_home_skills_dir()
        foreign_dir = global_skills_dir / "other-tool"
        foreign_dir.mkdir(parents=True, exist_ok=True)
        (foreign_dir / "SKILL.md").write_text("# Foreign skill\n")

        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)

        # Run teardown to verify foreign skill survives uninstall
        i.teardown(tmp_path, m)

        assert (foreign_dir / "SKILL.md").exists(), (
            "Foreign skill was removed by teardown"
        )

    def test_teardown_does_not_follow_symlinked_global_skills_directory(
        self, tmp_path, monkeypatch
    ):
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)
        external = tmp_path / "external-hermes-skills"
        protected = external / "speckit-userdata" / "keep.txt"
        protected.parent.mkdir(parents=True)
        protected.write_text("keep\n", encoding="utf-8")
        hermes_dir = home / ".hermes"
        hermes_dir.mkdir()
        try:
            (hermes_dir / "skills").symlink_to(
                external, target_is_directory=True
            )
        except (OSError, NotImplementedError):
            pytest.skip("symlinks are not available")

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        removed, skipped = i.teardown(tmp_path, m)

        assert removed == []
        assert home / ".hermes" / "skills" in skipped
        assert protected.read_text(encoding="utf-8") == "keep\n"

    def test_teardown_does_not_follow_symlinked_project_marker(
        self, tmp_path, monkeypatch
    ):
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)
        external = tmp_path / "external-marker"
        external.mkdir()
        marker_parent = tmp_path / ".hermes"
        marker_parent.mkdir()
        try:
            (marker_parent / "skills").symlink_to(
                external, target_is_directory=True
            )
        except (OSError, NotImplementedError):
            pytest.skip("symlinks are not available")

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        removed, skipped = i.teardown(tmp_path, m)

        assert removed == []
        assert tmp_path / ".hermes" / "skills" in skipped
        assert external.is_dir()

    def test_extension_registration_rejects_symlinked_global_skill(
        self, tmp_path, monkeypatch
    ):
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("USERPROFILE", str(home))
        external = tmp_path / "external-extension-skill"
        external.mkdir()
        external_skill = external / "SKILL.md"
        external_skill.write_text("external\n", encoding="utf-8")
        global_skills = home / ".hermes" / "skills"
        global_skills.mkdir(parents=True)
        try:
            (global_skills / "speckit-git-feature").symlink_to(
                external, target_is_directory=True
            )
        except (OSError, NotImplementedError):
            pytest.skip("symlinks are not available")

        from typer.testing import CliRunner
        from specify_cli import app

        target = tmp_path / "hermes-extension-link"
        result = CliRunner().invoke(
            app,
            [
                "init",
                str(target),
                "--integration",
                "hermes",
                "--script",
                "sh",
                "--ignore-agent-tools",
                "--extension",
                "git",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.output
        assert external_skill.read_text(encoding="utf-8") == "external\n"
        assert not (target / ".specify" / "extensions" / "git").exists()

        preview = CliRunner().invoke(
            app,
            [
                "init",
                str(tmp_path / "hermes-extension-link-preview"),
                "--dry-run",
                "--json",
                "--integration",
                "hermes",
                "--script",
                "sh",
                "--ignore-agent-tools",
                "--extension",
                "git",
            ],
            catch_exceptions=False,
        )
        assert preview.exit_code == 0, preview.output
        failures = json.loads(preview.output)["failures"]
        assert any("symlinked path component" in failure["error"] for failure in failures)
        assert external_skill.read_text(encoding="utf-8") == "external\n"

    def test_extension_alias_is_preflighted_before_any_install_write(
        self, tmp_path, monkeypatch
    ):
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("USERPROFILE", str(home))
        external = tmp_path / "external-alias-skill"
        external.mkdir()
        external_skill = external / "SKILL.md"
        external_skill.write_text("external\n", encoding="utf-8")
        global_skills = home / ".hermes" / "skills"
        global_skills.mkdir(parents=True)
        try:
            (global_skills / "speckit-my-extension-example-short").symlink_to(
                external, target_is_directory=True
            )
        except (OSError, NotImplementedError):
            pytest.skip("symlinks are not available")

        from typer.testing import CliRunner
        from specify_cli import app

        extension = Path(__file__).parents[2] / "extensions" / "template"
        target = tmp_path / "hermes-extension-alias-link"
        result = CliRunner().invoke(
            app,
            [
                "init",
                str(target),
                "--integration",
                "hermes",
                "--script",
                "sh",
                "--ignore-agent-tools",
                "--extension",
                str(extension),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.output
        assert external_skill.read_text(encoding="utf-8") == "external\n"
        assert not (
            global_skills / "speckit-my-extension-example" / "SKILL.md"
        ).exists()
        assert not (
            target / ".specify" / "extensions" / "my-extension"
        ).exists()

    def test_legacy_extension_preflight_uses_detected_hermes_target(
        self, tmp_path, monkeypatch
    ):
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)
        external = tmp_path / "external-legacy-extension"
        external.mkdir()
        external_skill = external / "SKILL.md"
        external_skill.write_text("external\n", encoding="utf-8")
        global_skills = home / ".hermes" / "skills"
        global_skills.mkdir(parents=True)
        try:
            (global_skills / "speckit-my-extension-example").symlink_to(
                external, target_is_directory=True
            )
        except (OSError, NotImplementedError):
            pytest.skip("symlinks are not available")
        (tmp_path / ".hermes" / "skills").mkdir(parents=True)

        from specify_cli.extensions import ExtensionManager
        from specify_cli.integrations.base import IntegrationOutputPathError

        extension = Path(__file__).parents[2] / "extensions" / "template"
        manager = ExtensionManager(tmp_path)
        with pytest.raises(IntegrationOutputPathError):
            manager.install_from_directory(extension, "0.3.0")

        assert external_skill.read_text(encoding="utf-8") == "external\n"
        assert not (
            tmp_path / ".specify" / "extensions" / "my-extension"
        ).exists()

    def test_extension_remove_retains_registry_when_hermes_cleanup_is_unsafe(
        self, tmp_path, monkeypatch
    ):
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("USERPROFILE", str(home))

        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.extensions import ExtensionManager
        from specify_cli.integrations.base import IntegrationOutputPathError

        target = tmp_path / "hermes-extension-remove"
        result = CliRunner().invoke(
            app,
            [
                "init",
                str(target),
                "--integration",
                "hermes",
                "--script",
                "sh",
                "--ignore-agent-tools",
                "--extension",
                "git",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output

        global_skills = home / ".hermes" / "skills"
        safe_skill = global_skills / "speckit-git-commit" / "SKILL.md"
        unsafe_dir = global_skills / "speckit-git-feature"
        assert safe_skill.is_file()
        shutil.rmtree(unsafe_dir)
        external = tmp_path / "external-remove-target"
        external.mkdir()
        external_skill = external / "SKILL.md"
        external_skill.write_text("external\n", encoding="utf-8")
        try:
            unsafe_dir.symlink_to(external, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks are not available")

        manager = ExtensionManager(target)
        with pytest.raises(IntegrationOutputPathError):
            manager.remove("git")

        assert manager.registry.is_installed("git")
        assert safe_skill.is_file()
        assert unsafe_dir.is_symlink()
        assert external_skill.read_text(encoding="utf-8") == "external\n"

        monkeypatch.chdir(target)
        cli_result = CliRunner().invoke(
            app,
            ["extension", "remove", "git", "--force"],
            catch_exceptions=False,
        )
        assert cli_result.exit_code == 1, cli_result.output
        assert "Cannot safely remove extension" in cli_result.output
        assert manager.registry.is_installed("git")

    def test_extension_remove_preflights_legacy_hermes_names(
        self, tmp_path, monkeypatch
    ):
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("USERPROFILE", str(home))

        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.extensions import ExtensionManager
        from specify_cli.integrations.base import IntegrationOutputPathError

        target = tmp_path / "hermes-legacy-remove"
        result = CliRunner().invoke(
            app,
            [
                "init",
                str(target),
                "--integration",
                "hermes",
                "--script",
                "sh",
                "--ignore-agent-tools",
                "--extension",
                "git",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output

        global_skills = home / ".hermes" / "skills"
        modern_skill = global_skills / "speckit-git-feature" / "SKILL.md"
        assert modern_skill.is_file()
        external = tmp_path / "external-legacy-remove"
        external.mkdir()
        external_skill = external / "SKILL.md"
        external_skill.write_text("external\n", encoding="utf-8")
        legacy_dir = global_skills / "speckit.git.feature"
        try:
            legacy_dir.symlink_to(external, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks are not available")

        manager = ExtensionManager(target)
        with pytest.raises(IntegrationOutputPathError):
            manager.remove("git")

        assert manager.registry.is_installed("git")
        assert modern_skill.is_file()
        assert legacy_dir.is_symlink()
        assert external_skill.read_text(encoding="utf-8") == "external\n"

    def test_preset_remove_retains_registry_when_hermes_cleanup_is_unsafe(
        self, tmp_path, monkeypatch
    ):
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("USERPROFILE", str(home))
        preset = tmp_path / "remove-preflight"
        command = preset / "commands" / "remove.md"
        command.parent.mkdir(parents=True)
        command.write_text(
            "---\ndescription: Remove preflight\n---\n\nBody\n",
            encoding="utf-8",
        )
        (preset / "preset.yml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": "remove-preflight",
                        "name": "Remove Preflight",
                        "version": "1.0.0",
                        "description": "Removal safety test",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "templates": [
                            {
                                "type": "command",
                                "name": "speckit.remove-preflight",
                                "file": "commands/remove.md",
                            }
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )

        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.integrations.base import IntegrationOutputPathError
        from specify_cli.presets import PresetManager

        target = tmp_path / "hermes-preset-remove"
        result = CliRunner().invoke(
            app,
            [
                "init",
                str(target),
                "--integration",
                "hermes",
                "--script",
                "sh",
                "--ignore-agent-tools",
                "--preset",
                str(preset),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output

        global_skills = home / ".hermes" / "skills"
        unsafe_dir = global_skills / "speckit-remove-preflight"
        shutil.rmtree(unsafe_dir)
        external = tmp_path / "external-preset-remove"
        external.mkdir()
        external_skill = external / "SKILL.md"
        external_skill.write_text("external\n", encoding="utf-8")
        try:
            unsafe_dir.symlink_to(external, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks are not available")

        manager = PresetManager(target)
        with pytest.raises(IntegrationOutputPathError):
            manager.remove("remove-preflight")

        assert manager.registry.is_installed("remove-preflight")
        assert unsafe_dir.is_symlink()
        assert external_skill.read_text(encoding="utf-8") == "external\n"

    def test_preset_alias_is_preflighted_before_any_install_write(
        self, tmp_path, monkeypatch
    ):
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("USERPROFILE", str(home))
        external = tmp_path / "external-preset-alias"
        external.mkdir()
        external_skill = external / "SKILL.md"
        external_skill.write_text("external\n", encoding="utf-8")
        global_skills = home / ".hermes" / "skills"
        global_skills.mkdir(parents=True)
        try:
            (global_skills / "speckit-my-preset-alias").symlink_to(
                external, target_is_directory=True
            )
        except (OSError, NotImplementedError):
            pytest.skip("symlinks are not available")

        preset = tmp_path / "alias-preflight"
        command = preset / "commands" / "primary.md"
        command.parent.mkdir(parents=True)
        command.write_text(
            "---\ndescription: Alias preflight\n---\n\nBody\n",
            encoding="utf-8",
        )
        (preset / "preset.yml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": "alias-preflight",
                        "name": "Alias Preflight",
                        "version": "1.0.0",
                        "description": "Alias safety test",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "templates": [
                            {
                                "type": "command",
                                "name": "speckit.my-preset-primary",
                                "file": "commands/primary.md",
                                "aliases": ["speckit.my-preset-alias"],
                            }
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )

        from typer.testing import CliRunner
        from specify_cli import app

        target = tmp_path / "hermes-preset-alias-link"
        result = CliRunner().invoke(
            app,
            [
                "init",
                str(target),
                "--integration",
                "hermes",
                "--script",
                "sh",
                "--ignore-agent-tools",
                "--preset",
                str(preset),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.output
        assert "Hermes destination" in " ".join(result.output.split())
        assert external_skill.read_text(encoding="utf-8") == "external\n"
        assert not (
            global_skills / "speckit-my-preset-primary" / "SKILL.md"
        ).exists()
        assert not (
            target / ".specify" / "presets" / "alias-preflight"
        ).exists()

    def test_hook_sections_explain_dotted_command_conversion(self, tmp_path, monkeypatch):
        """Override: Hermes skills live in global ~/.hermes/skills/."""
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        specify_skill = home / ".hermes" / "skills" / "speckit-specify" / "SKILL.md"
        assert specify_skill.exists()
        content = specify_skill.read_text(encoding="utf-8")
        assert "replace dots" in content, (
            "speckit-specify should explain dotted hook command conversion"
        )
        assert content.count("replace dots") == content.count(
            "- For each executable hook, output the following"
        )

    def test_complete_file_inventory_sh(self, tmp_path, monkeypatch):
        """Override: Hermes init produces no local SKILL.md files,
        only the empty .hermes/skills/ marker."""
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)

        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"inventory-sh-{self.KEY}"
        project.mkdir()
        old_cwd = Path.cwd()
        import os
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", self.KEY,
                "--script", "sh", "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix()
            for p in project.rglob("*") if p.is_file()
        )
        # Ensure no core .hermes/skills/speckit-*/SKILL.md in project dir
        # (extension-installed skills like agent-context-update may appear)
        hermes_skill_files = [
            f for f in actual
            if f.startswith(".hermes/skills/speckit-")
            and "agent-context" not in f
        ]
        assert hermes_skill_files == [], (
            f"Expected no local core SKILL.md files, found: {hermes_skill_files}"
        )
        # Ensure the marker exists (empty dir won't appear in file listing)
        assert (project / ".hermes" / "skills").is_dir()

    def test_complete_file_inventory_ps(self, tmp_path, monkeypatch):
        """Override: Same as sh variant but for PowerShell script type."""
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)

        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"inventory-ps-{self.KEY}"
        project.mkdir()
        old_cwd = Path.cwd()
        import os
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", self.KEY,
                "--script", "ps", "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix()
            for p in project.rglob("*") if p.is_file()
        )
        # Ensure no core .hermes/skills/speckit-*/SKILL.md in project dir
        # (extension-installed skills like agent-context-update may appear)
        hermes_skill_files = [
            f for f in actual
            if f.startswith(".hermes/skills/speckit-")
            and "agent-context" not in f
        ]
        assert hermes_skill_files == [], (
            f"Expected no local core SKILL.md files, found: {hermes_skill_files}"
        )
        assert (project / ".hermes" / "skills").is_dir()

    def test_install_uninstall_cleanup(self, tmp_path, monkeypatch):
        """Verify global skills are cleaned and local marker is removed."""
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)

        # Verify global skills exist
        global_skills = [
            f for f in created
            if "SKILL.md" in str(f)
            and str(f).startswith(str(home / ".hermes"))
        ]
        assert len(global_skills) > 0
        for f in global_skills:
            assert f.exists()

        # Verify local marker exists
        assert (tmp_path / ".hermes" / "skills").is_dir()

        # Teardown — global skills removed without needing force=True
        removed, skipped = i.teardown(tmp_path, m, force=False)

        # Global skills removed
        for f in global_skills:
            assert not f.exists(), f"{f} should have been removed"

        # Local marker removed
        assert not (tmp_path / ".hermes" / "skills").exists(), (
            "Local marker should be removed on teardown"
        )


class TestHermesInitFlow:
    """--integration hermes creates expected files."""

    def test_integration_hermes_creates_global_skills(self, tmp_path, monkeypatch):
        """--integration hermes should create global skills and a local marker."""
        home = _fake_home(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: home)

        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(app, [
            "init", str(target),
            "--integration", "hermes",
            "--ignore-agent-tools",
            "--script", "sh",
        ])

        assert result.exit_code == 0, f"init --integration hermes failed: {result.output}"
        # Skills should be in global ~/.hermes/skills/
        assert (home / ".hermes" / "skills" / "speckit-plan" / "SKILL.md").exists()
        # Local marker should exist
        assert (target / ".hermes" / "skills").is_dir()
        # No core SKILL.md files in project-local dir
        # (extension-installed skills like agent-context-update may appear)
        local_skills = [
            d for d in (target / ".hermes" / "skills").iterdir()
            if "agent-context" not in d.name
        ]
        assert local_skills == [], f"Local skills dir should be empty, got: {local_skills}"


class TestHermesBuildExecArgs:
    """CLI dispatch argv, including the operator extra-args env hook."""

    def test_build_exec_args_default_shape(self):
        i = get_integration("hermes")
        assert i.build_exec_args("/speckit-plan hi", output_json=True) == [
            "hermes", "chat", "-Q", "--json", "-s", "speckit-plan", "-q", "hi",
        ]

    def test_build_exec_args_honors_extra_args(self, monkeypatch):
        """SPECKIT_INTEGRATION_HERMES_EXTRA_ARGS is injected before the
        canonical -m/--json/-s/-q flags (same env hook as codex/opencode/
        devin; hermes previously skipped _apply_extra_args_env_var entirely).
        """
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_HERMES_EXTRA_ARGS", "--temperature 0.2"
        )
        i = get_integration("hermes")
        args = i.build_exec_args("/speckit-plan hi", output_json=True)
        assert args == [
            "hermes", "chat", "-Q", "--temperature", "0.2",
            "--json", "-s", "speckit-plan", "-q", "hi",
        ]
        # Injected before the canonical flags so it can't displace them.
        assert args.index("--temperature") < args.index("--json")
        assert args.index("--temperature") < args.index("-s")

    def test_build_exec_args_honors_executable_override(self, monkeypatch):
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_HERMES_EXECUTABLE", "/custom/hermes"
        )
        i = get_integration("hermes")
        assert i.build_exec_args("/speckit-plan hi")[0] == "/custom/hermes"
