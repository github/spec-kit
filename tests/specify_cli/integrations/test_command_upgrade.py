"""Tests for mirrored integration CLI behavior in test_command_upgrade.py."""

from __future__ import annotations

import hashlib
import json  # noqa: F401
import os  # noqa: F401
import shutil  # noqa: F401
from pathlib import Path  # noqa: F401

import pytest  # noqa: F401

from specify_cli import app  # noqa: F401
from tests.conftest import strip_ansi  # noqa: F401
from tests.specify_cli.integrations._catalog_helpers import (
    IntegrationCatalogCliTestBase,
    _normalize_cli_output,
)
from tests.specify_cli.integrations._helpers import (
    _copy_project_template,  # noqa: F401
    _init_project,  # noqa: F401
    _integration_list_row_cells,  # noqa: F401
    _move_kilocode_install_to_legacy_layout,  # noqa: F401
    _run_in_project,  # noqa: F401
    _write_invalid_manifest,  # noqa: F401
    runner,  # noqa: F401
)

def _write_command_preset(tmp_path, preset_id):
    """Write a dev preset that overrides the core ``speckit.plan`` command."""
    import yaml

    preset_src = tmp_path / preset_id
    (preset_src / "commands").mkdir(parents=True)
    (preset_src / "commands" / "speckit.plan.md").write_text(
        "---\ndescription: Overridden plan\n---\nOverridden plan content\n",
        encoding="utf-8",
    )
    (preset_src / "preset.yml").write_text(
        yaml.dump({
            "schema_version": "1.0",
            "preset": {
                "id": preset_id,
                "name": "Command Preset",
                "version": "1.0.0",
                "description": "Test preset with a command override",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.plan",
                        "file": "commands/speckit.plan.md",
                    }
                ]
            },
        }),
        encoding="utf-8",
    )
    return preset_src


def _write_command_extension(tmp_path, aliases=()):
    import yaml

    source = tmp_path / "audit-source"
    (source / "commands").mkdir(parents=True)
    (source / "commands/run.md").write_bytes(b"---\ndescription: Audit\n---\nAUDIT-BODY\n")
    (source / "extension.yml").write_bytes(yaml.safe_dump({
        "schema_version": "1.0",
        "extension": {"id": "audit", "name": "Audit", "version": "1.0.0", "description": "Test"},
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {"commands": [{
            "name": "speckit.audit.run", "file": "commands/run.md", "aliases": list(aliases),
        }]},
    }).encode())
    return source


def _init_dotted_kiro_project(tmp_path, monkeypatch, *commands):
    """Init a Kiro project and run ``commands`` with the old dotted prompt names."""
    from specify_cli.agents import CommandRegistrar
    from specify_cli.integrations.base import MarkdownIntegration
    from specify_cli.integrations.kiro_cli import KiroCliIntegration

    CommandRegistrar._ensure_configs()
    with monkeypatch.context() as m:
        m.setattr(
            KiroCliIntegration, "command_filename",
            MarkdownIntegration.command_filename,
        )
        m.delitem(CommandRegistrar.AGENT_CONFIGS["kiro-cli"], "format_name", raising=False)
        project = _init_project(tmp_path, "kiro-cli")
        for args in commands:
            result = _run_in_project(project, args)
            assert result.exit_code == 0, result.output
    return project


class TestIntegrationUpgradeDetailed:
    def test_upgrade_invalid_manifest_reports_cli_error(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        _write_invalid_manifest(project, "claude")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "manifest" in result.output
        assert "unreadable" in result.output

    def test_upgrade_refreshes_init_options_speckit_version(self, tmp_path, monkeypatch):
        project = _init_project(tmp_path, "claude")
        init_options = project / ".specify" / "init-options.json"
        opts = json.loads(init_options.read_text(encoding="utf-8"))
        opts["speckit_version"] = "0.6.1"
        init_options.write_text(json.dumps(opts), encoding="utf-8")

        import specify_cli.integrations._commands as _int_cmds

        monkeypatch.setattr(_int_cmds, "get_speckit_version", lambda: "0.8.11")

        result = _run_in_project(project, [
            "integration", "upgrade", "claude",
            "--force",
        ])

        assert result.exit_code == 0, result.output
        updated = json.loads(init_options.read_text(encoding="utf-8"))
        assert updated["speckit_version"] == "0.8.11"

    def test_upgrade_non_default_refreshes_init_options_version_only(self, tmp_path, monkeypatch):
        project = _init_project(tmp_path, "gemini")
        install = _run_in_project(project, [
            "integration", "install", "claude",
            "--script", "sh",
        ])
        assert install.exit_code == 0, install.output

        init_options = project / ".specify" / "init-options.json"
        opts = json.loads(init_options.read_text(encoding="utf-8"))
        opts["speckit_version"] = "0.6.1"
        init_options.write_text(json.dumps(opts), encoding="utf-8")

        import specify_cli.integrations._commands as _int_cmds

        monkeypatch.setattr(_int_cmds, "get_speckit_version", lambda: "0.8.11")

        result = _run_in_project(project, [
            "integration", "upgrade", "claude",
            "--script", "sh",
            "--force",
        ])

        assert result.exit_code == 0, result.output
        updated = json.loads(init_options.read_text(encoding="utf-8"))
        assert updated["speckit_version"] == "0.8.11"
        assert updated["integration"] == "gemini"
        assert updated["ai"] == "gemini"
        assert "context_file" not in updated

    def test_upgrade_does_not_persist_state_when_shared_infra_refresh_fails(self, tmp_path, monkeypatch):
        project = _init_project(tmp_path, "claude")
        int_json = project / ".specify" / "integration.json"
        init_options = project / ".specify" / "init-options.json"
        manifest_path = project / ".specify" / "integrations" / "claude.manifest.json"

        before_state = json.loads(int_json.read_text(encoding="utf-8"))
        before_options = json.loads(init_options.read_text(encoding="utf-8"))
        before_manifest = manifest_path.read_text(encoding="utf-8")

        import specify_cli

        real_install_shared_infra = specify_cli._install_shared_infra
        calls = {"count": 0}

        def fail_refresh(*args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 2:
                raise ValueError("refuse refresh")
            return real_install_shared_infra(*args, **kwargs)

        monkeypatch.setattr(specify_cli, "_install_shared_infra", fail_refresh)

        result = _run_in_project(project, [
            "integration", "upgrade", "claude",
            "--force",
        ])

        assert result.exit_code != 0
        assert "Failed to refresh shared infrastructure" in result.output
        assert json.loads(int_json.read_text(encoding="utf-8")) == before_state
        assert json.loads(init_options.read_text(encoding="utf-8")) == before_options
        assert manifest_path.read_text(encoding="utf-8") == before_manifest

    def test_upgrade_default_refreshes_shared_script_refs_for_option_separator_change(self, tmp_path):
        project = _init_project(
            tmp_path, "copilot", integration_options="--commands"
        )
        template = project / ".specify" / "templates" / "plan-template.md"
        managed_script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        customized_script = project / ".specify" / "scripts" / "bash" / "setup-tasks.sh"

        assert "/speckit.plan" in template.read_text(encoding="utf-8")
        assert "/speckit.specify" in managed_script.read_text(encoding="utf-8")
        customized_before = customized_script.read_text(encoding="utf-8") + "\n# user customization\n"
        customized_script.write_text(customized_before, encoding="utf-8")

        result = _run_in_project(project, [
            "integration", "upgrade", "copilot",
            "--integration-options", "--skills",
        ])

        assert result.exit_code == 0, result.output
        assert "/speckit-plan" in template.read_text(encoding="utf-8")
        managed_content = managed_script.read_text(encoding="utf-8")
        assert "/speckit-specify" in managed_content
        assert "/speckit.specify" not in managed_content
        assert customized_script.read_text(encoding="utf-8") == customized_before

    def test_upgrade_preserves_historical_copilot_commands_without_options(
        self, tmp_path
    ):
        """A command manifest restores missing files instead of migrating."""
        project = _init_project(
            tmp_path, "copilot", integration_options="--commands"
        )
        state_path = project / ".specify" / "integration.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        copilot_settings = state["integration_settings"]["copilot"]
        copilot_settings.pop("raw_options", None)
        copilot_settings.pop("parsed_options", None)
        state_path.write_text(json.dumps(state), encoding="utf-8")

        for path in (project / ".github" / "agents").glob(
            "speckit.*.agent.md"
        ):
            path.unlink()
        for path in (project / ".github" / "prompts").glob(
            "speckit.*.prompt.md"
        ):
            path.unlink()

        result = _run_in_project(
            project,
            ["integration", "upgrade", "copilot", "--script", "sh", "--force"],
        )

        assert result.exit_code == 0, result.output
        assert (
            project / ".github" / "agents" / "speckit.plan.agent.md"
        ).exists()
        assert not (project / ".github" / "skills").exists()
        init_options = json.loads(
            (project / ".specify" / "init-options.json").read_text(
                encoding="utf-8"
            )
        )
        assert init_options.get("ai_skills") is not True

    def test_upgrade_non_default_keeps_default_template_invocations(self, tmp_path):
        project = _init_project(tmp_path, "gemini")
        template = project / ".specify" / "templates" / "plan-template.md"
        script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        assert "/speckit.plan" in template.read_text(encoding="utf-8")
        assert "/speckit.plan" in script.read_text(encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, [
                "integration", "upgrade", "claude",
                "--script", "sh",
                "--force",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "gemini"
        assert "/speckit.plan" in template.read_text(encoding="utf-8")
        assert "/speckit.plan" in script.read_text(encoding="utf-8")
        assert "/speckit-plan" not in script.read_text(encoding="utf-8")

    def test_upgrade_migrates_opencode_legacy_dir(self, tmp_path):
        """Upgrade moves OpenCode commands from .opencode/command/ to .opencode/commands/."""
        project = _init_project(tmp_path, "opencode")

        # Simulate a legacy project: rename commands/ back to command/
        canonical = project / ".opencode" / "commands"
        legacy = project / ".opencode" / "command"
        assert canonical.is_dir(), "init should have created .opencode/commands/"
        canonical.rename(legacy)
        assert legacy.is_dir()
        assert not canonical.exists()

        # Patch the manifest to reflect old paths (command/ not commands/)
        manifest_path = project / ".specify" / "integrations" / "opencode.manifest.json"
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        patched_files = {}
        for path, info in manifest_data.get("files", {}).items():
            patched_files[path.replace(".opencode/commands/", ".opencode/command/")] = info
        manifest_data["files"] = patched_files
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        old_commands = sorted(legacy.glob("speckit.*.md"))
        assert len(old_commands) > 0, "Legacy dir should have speckit command files"

        result = _run_in_project(project, [
            "integration", "upgrade", "opencode",
            "--script", "sh",
            "--force",
        ])
        assert result.exit_code == 0, f"upgrade failed: {result.output}"

        # New commands in canonical dir
        assert canonical.is_dir(), ".opencode/commands/ should exist after upgrade"
        new_commands = sorted(canonical.glob("speckit.*.md"))
        assert len(new_commands) > 0, "Commands should exist in .opencode/commands/"

        # Stale files removed from legacy dir (extension-installed commands
        # like agent-context.update may still appear — only check the original
        # core command stems that should have been migrated).
        core_remaining = [
            f for f in legacy.glob("speckit.*.md")
            if "agent-context" not in f.name
        ]
        assert len(core_remaining) == 0, (
            f"Legacy .opencode/command/ should have no core speckit files after upgrade, "
            f"found: {[f.name for f in core_remaining]}"
        )

    def test_upgrade_migrates_kilocode_legacy_dir(self, tmp_path):
        """Upgrade moves Kilo commands from .kilocode/workflows/ to .kilo/commands/."""
        project = _init_project(tmp_path, "kilocode")
        canonical, legacy = _move_kilocode_install_to_legacy_layout(project)

        old_commands = sorted(legacy.glob("speckit.*.md"))
        assert old_commands, "Legacy dir should have speckit command files"

        result = _run_in_project(project, [
            "integration", "upgrade", "kilocode",
            "--script", "sh",
            "--force",
        ])
        assert result.exit_code == 0, f"upgrade failed: {result.output}"

        assert canonical.is_dir(), ".kilo/commands/ should exist after upgrade"
        new_commands = sorted(canonical.glob("speckit.*.md"))
        assert new_commands, "Commands should exist in .kilo/commands/"

        core_remaining = [
            f for f in legacy.glob("speckit.*.md")
            if "agent-context" not in f.name
        ]
        assert core_remaining == [], (
            "Legacy .kilocode/workflows/ should have no core speckit files "
            f"after upgrade, found: {[f.name for f in core_remaining]}"
        )

    def test_upgrade_replaces_dotted_kiro_prompts(self, tmp_path, monkeypatch):
        """Kiro installs used to write ``.kiro/prompts/speckit.<cmd>.md``,
        which Kiro CLI cannot invoke (#4797). Upgrade replaces them, including
        enabled extension prompts, with ``speckit-<cmd>.md``, but a
        user-modified one blocks it."""
        project = _init_dotted_kiro_project(
            tmp_path, monkeypatch, ["extension", "add", "git"]
        )
        prompts = project / ".kiro" / "prompts"
        assert (prompts / "speckit.git.commit.md").is_file()
        dotted_plan = prompts / "speckit.plan.md"
        # Bytes, not text: write_text() would turn "\n" into "\r\n" on
        # Windows, so the restored file would no longer match the manifest.
        original = dotted_plan.read_bytes()

        dotted_plan.write_bytes(original + b"my note\n")
        blocked = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert blocked.exit_code != 0
        assert "speckit.plan.md" in blocked.output
        assert dotted_plan.read_bytes() == original + b"my note\n"

        dotted_plan.write_bytes(original)
        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        assert sorted(prompts.glob("speckit.*.md")) == []
        assert (prompts / "speckit-plan.md").is_file()
        assert (prompts / "speckit-git-commit.md").is_file()

    def test_upgrade_refuses_kiro_prompt_rename_while_presets_are_installed(
        self, tmp_path, monkeypatch
    ):
        """A preset override shares its path with the command it overrides,
        and its rescaffold is best-effort. If the preset can't be
        re-registered, the rename would leave only the core prompt, so
        upgrade refuses before changing files, even with ``--force`` (#4797),
        as for the Kilo command-root and command/skills layout migrations."""
        preset_src = _write_command_preset(tmp_path, "cmd-preset")
        project = _init_dotted_kiro_project(
            tmp_path, monkeypatch, ["preset", "add", "--dev", str(preset_src)]
        )
        prompts = project / ".kiro" / "prompts"
        before = {path.name: path.read_bytes() for path in prompts.iterdir()}
        assert b"Overridden plan content" in before["speckit.plan.md"]
        # The preset can no longer be re-registered.
        (
            project / ".specify" / "presets" / "cmd-preset" / "commands"
            / "speckit.plan.md"
        ).unlink()

        result = _run_in_project(
            project, ["integration", "upgrade", "kiro-cli", "--force"]
        )
        assert result.exit_code != 0
        assert "cmd-preset" in result.output
        assert {path.name: path.read_bytes() for path in prompts.iterdir()} == before

    def test_upgrade_keeps_dotted_kiro_prompts_when_reregistration_fails(
        self, tmp_path, monkeypatch
    ):
        """A dotted extension prompt is removed only after its hyphenated
        replacement exists (#4797), as in
        ``test_upgrade_layout_change_preserves_extension_artifacts_when_reregistration_fails``.
        If re-registration can't rebuild it, the old prompt and its registry
        entry survive the upgrade."""
        project = _init_dotted_kiro_project(
            tmp_path, monkeypatch, ["extension", "add", "git"]
        )
        specify = project / ".specify"
        (specify / "extensions" / "git" / "extension.yml").write_text(
            "invalid: [", encoding="utf-8"
        )

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output

        prompts = project / ".kiro" / "prompts"
        assert (prompts / "speckit-plan.md").is_file()
        assert not (prompts / "speckit.plan.md").exists()
        assert (prompts / "speckit.git.commit.md").is_file()
        registry = json.loads(
            (specify / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        assert "kiro-cli" in registry["extensions"]["git"]["registered_commands"]

    def _kiro_git_commands(self, project):
        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(
                encoding="utf-8"
            )
        )
        return list(
            registry["extensions"]["git"]["registered_commands"]["kiro-cli"]
        )

    def test_upgrade_keeps_tracking_when_one_kiro_command_source_is_missing(
        self, tmp_path, monkeypatch
    ):
        """A valid manifest whose command source is missing must not drop
        that command's dotted prompt from the registry.

        ``register_commands`` returns only the commands it wrote, so a
        partial list used to replace ``registered_commands["kiro-cli"]``
        before retirement. The missing command's dotted prompt stayed on
        disk and ``extension remove`` left it there (#4797).
        """
        project = _init_dotted_kiro_project(
            tmp_path, monkeypatch, ["extension", "add", "git"]
        )
        prompts = project / ".kiro" / "prompts"
        before = self._kiro_git_commands(project)
        assert "speckit.git.commit" in before
        assert (prompts / "speckit.git.commit.md").is_file()
        (
            project / ".specify" / "extensions" / "git" / "commands"
            / "speckit.git.commit.md"
        ).unlink()

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output

        assert (prompts / "speckit.git.commit.md").is_file()
        assert not (prompts / "speckit-git-commit.md").exists()
        assert (prompts / "speckit-git-feature.md").is_file()
        assert not (prompts / "speckit.git.feature.md").exists()
        assert (prompts / "speckit-plan.md").is_file()
        assert set(self._kiro_git_commands(project)) == set(before)
        assert "speckit.git.commit" in self._kiro_git_commands(project)

        result = _run_in_project(
            project, ["extension", "remove", "git", "--force"]
        )
        assert result.exit_code == 0, result.output
        assert not (prompts / "speckit.git.commit.md").exists()
        assert not (prompts / "speckit-git-feature.md").exists()
        assert (prompts / "speckit-plan.md").is_file()

    def test_upgrade_keeps_tracking_when_every_kiro_command_source_is_missing(
        self, tmp_path, monkeypatch
    ):
        """An empty command registration must not drop dotted prompts that
        were already registered.

        With every extension command source gone, registration returns
        nothing and used to pop ``registered_commands["kiro-cli"]``. The
        dotted prompts remained, untracked, so removing the extension left
        them behind (#4797).
        """
        project = _init_dotted_kiro_project(
            tmp_path, monkeypatch, ["extension", "add", "git"]
        )
        prompts = project / ".kiro" / "prompts"
        before = self._kiro_git_commands(project)
        assert before
        sources = list(
            (project / ".specify" / "extensions" / "git" / "commands").glob(
                "*.md"
            )
        )
        assert sources
        for source in sources:
            source.unlink()

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output

        assert (prompts / "speckit-plan.md").is_file()
        assert not (prompts / "speckit.plan.md").exists()
        for name in before:
            assert (prompts / f"{name}.md").is_file(), name
            assert not (prompts / f"{name.replace('.', '-')}.md").exists(), name
        assert set(self._kiro_git_commands(project)) == set(before)

        result = _run_in_project(
            project, ["extension", "remove", "git", "--force"]
        )
        assert result.exit_code == 0, result.output
        for name in before:
            assert not (prompts / f"{name}.md").exists(), name
        assert (prompts / "speckit-plan.md").is_file()

    def test_upgrade_keeps_tracking_when_a_rewritten_kiro_source_disappears(
        self, tmp_path, monkeypatch
    ):
        """A hyphenated prompt already written stays tracked when a later
        pass cannot write it, and so does an alias from the same source.

        The dotted file is already gone. The live files are
        ``speckit-git-commit.md`` and the alias prompt. Dropping either
        name would leave that file behind after extension removal (#4797).
        """
        import yaml

        project = _init_dotted_kiro_project(
            tmp_path, monkeypatch, ["extension", "add", "git"]
        )
        manifest_path = (
            project / ".specify" / "extensions" / "git" / "extension.yml"
        )
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        for command in manifest["provides"]["commands"]:
            if command["name"] == "speckit.git.commit":
                command["aliases"] = ["speckit-git-c"]
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        prompts = project / ".kiro" / "prompts"
        assert (prompts / "speckit-git-commit.md").is_file()
        assert (prompts / "speckit-git-c.md").is_file()
        assert not (prompts / "speckit.git.commit.md").exists()
        before = self._kiro_git_commands(project)
        assert {"speckit.git.commit", "speckit-git-c"} <= set(before)

        (
            project / ".specify" / "extensions" / "git" / "commands"
            / "speckit.git.commit.md"
        ).unlink()
        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output

        assert (prompts / "speckit-git-commit.md").is_file()
        assert (prompts / "speckit-git-c.md").is_file()
        assert not (prompts / "speckit.git.commit.md").exists()
        assert set(self._kiro_git_commands(project)) == set(before)

        result = _run_in_project(
            project, ["extension", "remove", "git", "--force"]
        )
        assert result.exit_code == 0, result.output
        assert not (prompts / "speckit-git-commit.md").exists()
        assert not (prompts / "speckit-git-c.md").exists()
        assert (prompts / "speckit-plan.md").is_file()

    def test_upgrade_drops_a_kiro_command_the_manifest_no_longer_declares(
        self, tmp_path, monkeypatch
    ):
        """A command the manifest no longer provides is dropped from the
        registry.

        ``extension remove`` deletes the formatted prompt for every name
        still tracked. Keeping ``speckit.git.commit`` after the extension
        stops providing it would unlink ``speckit-git-commit.md`` even
        when another extension now owns that path.
        """
        import yaml

        project = _init_dotted_kiro_project(
            tmp_path, monkeypatch, ["extension", "add", "git"]
        )
        manifest_path = (
            project / ".specify" / "extensions" / "git" / "extension.yml"
        )
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        for command in manifest["provides"]["commands"]:
            if command["name"] == "speckit.git.commit":
                command["aliases"] = ["speckit-git-c"]
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        before = self._kiro_git_commands(project)
        assert {"speckit.git.commit", "speckit-git-c"} <= set(before)

        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest["provides"]["commands"] = [
            command for command in manifest["provides"]["commands"]
            if command.get("name") != "speckit.git.commit"
        ]
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
        (
            project / ".specify" / "extensions" / "git" / "commands"
            / "speckit.git.commit.md"
        ).unlink()

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        after = set(self._kiro_git_commands(project))
        assert "speckit.git.commit" not in after
        assert "speckit-git-c" not in after
        assert "speckit.git.feature" in after
        prompts = project / ".kiro" / "prompts"
        assert (prompts / "speckit-git-feature.md").is_file()
        assert (prompts / "speckit-plan.md").is_file()
        assert not (prompts / "speckit-git-commit.md").exists()
        assert not (prompts / "speckit-git-c.md").exists()

    @pytest.mark.parametrize(
        ("agent", "output"),
        [
            ("claude", ".claude/skills/speckit-foo-bar-baz/SKILL.md"),
            ("cline", ".clinerules/workflows/speckit-foo-bar-baz.md"),
            ("junie", ".junie/commands/speckit-foo-bar-baz.md"),
        ],
    )
    def test_unwritten_name_is_dropped_where_removal_does_not_check_owners(
        self, tmp_path, agent, output
    ):
        """Only Kiro CLI and Qoder keep a registered name whose source is
        missing, because only their removal checks who owns a shared file.
        Elsewhere an older pair can share the file, and keeping ``foo``'s
        name would let removing ``foo`` delete ``foo-bar``'s (#4797)."""
        from specify_cli.extensions import ExtensionManager

        project = _init_project(tmp_path, agent)
        self._plant_extension(project, "foo", [
            {"name": "speckit.foo.bar-baz", "body": "FOO-BODY\n"},
        ], agent=agent)
        self._plant_extension(project, "foo-bar", [
            {"name": "speckit.foo-bar.baz", "body": "BAR-BODY\n"},
        ], agent=agent)
        (
            project / ".specify/extensions/foo/commands/speckit.foo.bar-baz.md"
        ).unlink()
        ExtensionManager(project).register_enabled_extensions_for_agent(agent)
        shared = project / output
        before = shared.read_bytes()
        assert b"BAR-BODY" in before

        result = _run_in_project(project, ["extension", "remove", "foo", "--force"])
        assert result.exit_code == 0, result.output
        assert shared.read_bytes() == before

    @pytest.mark.parametrize("operation", ["remove", "switch", "upgrade"])
    @pytest.mark.parametrize("agent", ["kiro-cli", "qodercli"])
    @pytest.mark.parametrize("body", [b"USER\n", b"<!-- Extension: other -->\n", b"\xff"])
    def test_legacy_extension_cleanup_respects_ownership_and_replacements(
        self, tmp_path, operation, agent, body
    ):
        project = _init_project(tmp_path, agent)
        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, result.output
        directory = ".kiro/prompts" if agent == "kiro-cli" else ".qoder/commands"
        legacy = project / directory / "speckit.git.commit.md"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_bytes(body)
        args = (
            ["extension", "remove", "git", "--force"] if operation == "remove"
            else ["integration", "switch", "claude"] if operation == "switch"
            else ["integration", "upgrade", agent]
        )
        result = _run_in_project(project, args)
        assert result.exit_code == 0, result.output
        assert legacy.read_bytes() == body
        assert "Preserving the legacy file" in result.output
        if operation == "switch":
            from specify_cli.extensions import ExtensionManager

            tracked = ExtensionManager(project).registry.get("git")["registered_commands"]
            assert "speckit.git.commit" in tracked[agent]
            legacy.write_bytes(b"<!-- Extension: git -->\nRestored ownership\n")
            result = _run_in_project(project, ["extension", "remove", "git", "--force"])
            assert result.exit_code == 0, result.output
            assert not legacy.exists()

    @pytest.mark.parametrize("agent", ["kiro-cli", "qodercli"])
    @pytest.mark.parametrize("commands_only", [False, True])
    def test_integration_cleanup_retires_owned_legacy_extension_commands(
        self, tmp_path, agent, commands_only
    ):
        project = _init_project(tmp_path, agent)
        # A pre-existing collision keeps both owners in the legacy layout.
        for ext_id, name in [("foo", "speckit.foo.bar-baz"), ("foo-bar", "speckit.foo-bar.baz")]:
            self._plant_extension(project, ext_id, [{"name": name, "body": "BODY\n"}], agent=agent)
        directory = ".kiro/prompts" if agent == "kiro-cli" else ".qoder/commands"
        legacy = project / directory / "speckit.foo.bar-baz.md"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_bytes(b"<!-- Extension: foo -->\nFOO\n")
        if commands_only:
            from specify_cli.extensions import ExtensionManager

            manager = ExtensionManager(project)
            manager.unregister_agent_artifacts(agent, commands_only=True)
            assert legacy.exists()
            assert agent in manager.registry.get("foo")["registered_commands"]
            assert manager.remove("foo")
            assert not legacy.exists()
            return
        result = _run_in_project(project, ["integration", "switch", "claude"])
        assert result.exit_code == 0, result.output
        assert not legacy.exists()
        from specify_cli.extensions import ExtensionManager

        assert agent not in ExtensionManager(project).registry.get("foo")["registered_commands"]

    @pytest.mark.parametrize("agent", ["kiro-cli", "qodercli"])
    @pytest.mark.parametrize("operation", ["use", "upgrade", "remove"])
    @pytest.mark.parametrize("readable_manifest", [True, False])
    @pytest.mark.parametrize("damage", ["entry", "null-agent", "missing"])
    def test_malformed_owner_cannot_lose_shared_extension_file(
        self, tmp_path, agent, operation, readable_manifest, damage
    ):
        project = _init_project(tmp_path, agent)
        self._plant_extension(project, "foo-bar", [{
            "name": "speckit.foo-bar.baz", "body": "BAR\n", "aliases": ["speckit-foo-bar-baz"],
        }], agent=agent)
        result = _run_in_project(project, ["integration", "use", agent])
        assert result.exit_code == 0, result.output
        output = (
            ".kiro/prompts/speckit-foo-bar-baz.md" if agent == "kiro-cli"
            else ".qoder/skills/speckit-foo-bar-baz/SKILL.md"
        )
        shared = project / output
        before = shared.read_bytes()
        self._plant_extension(project, "foo", [{
            "name": "speckit.foo.bar-baz", "body": "FOO\n",
        }], agent=agent)
        registry_path = project / ".specify/extensions/.registry"
        registry = json.loads(registry_path.read_bytes())
        registry["extensions"]["foo-bar"] = (
            "damaged" if damage == "entry"
            else {"enabled": False, "registered_commands": {agent: None}}
        )
        if damage == "missing":
            del registry["extensions"]["foo-bar"]["registered_commands"]
        registry_path.write_bytes(json.dumps(registry).encode())
        if not readable_manifest:
            (project / ".specify/extensions/foo-bar/extension.yml").write_bytes(b"invalid: [")
        args = (
            ["extension", "remove", "foo", "--force"] if operation == "remove"
            else ["integration", operation, agent]
        )
        result = _run_in_project(project, args)
        assert shared.read_bytes() == before
        assert result.exit_code == 0, result.output
        if operation == "remove":
            del registry["extensions"]["foo"]
            assert json.loads(registry_path.read_bytes()) == registry
        elif not readable_manifest:
            assert "foo-bar" in result.output
            assert "Fix or restore .specify/extensions/.registry" in _normalize_cli_output(result.output)
            assert json.loads(registry_path.read_bytes()) == registry

    @pytest.mark.parametrize("operation", ["use", "upgrade", "switch", "reinstall", "update"])
    @pytest.mark.parametrize("linked", [False, True])
    @pytest.mark.parametrize("agent", ["kiro-cli", "qodercli"])
    def test_migration_preserves_unowned_destination(self, tmp_path, monkeypatch, operation, linked, agent):
        import yaml
        from specify_cli.extensions import ExtensionCatalog, ExtensionManager

        source = _write_command_extension(tmp_path)
        if agent == "kiro-cli":
            project = _init_dotted_kiro_project(
                tmp_path, monkeypatch, ["extension", "add", "--dev", str(source)]
            )
            destination = project / ".kiro/prompts/speckit-audit-run.md"
        else:
            project = _init_project(tmp_path, agent)
            assert _run_in_project(project, ["extension", "add", "--dev", str(source)]).exit_code == 0
            destination = project / ".qoder/skills/speckit-audit-run/SKILL.md"
            legacy = project / ".qoder/commands/speckit.audit.run.md"
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_bytes(destination.read_bytes())
            destination.unlink()
        target = project / "user-prompt.md"
        before = b"USER WORKAROUND PROMPT\n"
        if linked:
            target.write_bytes(before)
            try:
                destination.symlink_to(target)
            except OSError:
                pytest.skip("Symlinks are unavailable")
        else:
            destination.write_bytes(before)
        if operation == "switch":
            assert _run_in_project(project, ["integration", "install", "claude"]).exit_code == 0
            assert _run_in_project(project, ["integration", "use", "claude"]).exit_code == 0
        tracked = ExtensionManager(project).registry.get("audit")["registered_commands"][agent]
        if operation == "update":
            monkeypatch.setattr(ExtensionCatalog, "get_extension_info", lambda *args: {
                "id": "audit", "name": "Audit", "version": "2.0.0", "bundled": True, "_install_allowed": True,
            })
            monkeypatch.setattr("specify_cli._locate_bundled_extension", lambda key: source)
            monkeypatch.setattr(ExtensionCatalog, "download_extension", lambda *args: pytest.fail("Unexpected download"))
            manifest = yaml.safe_load((source / "extension.yml").read_bytes())
            manifest["extension"]["version"] = "2.0.0"
            (source / "extension.yml").write_bytes(yaml.safe_dump(manifest).encode())
            from contextlib import chdir

            with chdir(project):
                result = runner.invoke(app, ["extension", "update", "audit"], input="y\n", catch_exceptions=False)
        else:
            args = ["extension", "add", "--dev", str(source), "--force"] if operation == "reinstall" else ["integration", operation, agent]
            result = _run_in_project(project, args)
        assert destination.read_bytes() == before
        if linked:
            assert destination.is_symlink() and target.read_bytes() == before
        assert "Move or remove" in _normalize_cli_output(result.output)
        assert destination.relative_to(project).as_posix() in _normalize_cli_output(result.output)
        assert ExtensionManager(project).registry.get("audit")["registered_commands"][agent] == tracked

    @pytest.mark.parametrize("alias", ["speckit-plan", "plan"])
    @pytest.mark.parametrize("linked", [False, True])
    @pytest.mark.parametrize("core_manifest,operation", [
        (state, "init") for state in ("readable", "missing", "unreadable", "empty")
    ] + [("empty", "upgrade")])
    def test_kiro_reinit_preserves_legacy_alias(self, tmp_path, monkeypatch, alias, linked, core_manifest, operation):
        from specify_cli.extensions import ExtensionManager

        source = _write_command_extension(tmp_path, aliases=[alias])
        with monkeypatch.context() as patch:
            patch.setattr(ExtensionManager, "_validate_install_conflicts", lambda *args: None)
            project = _init_dotted_kiro_project(
                tmp_path, patch, ["extension", "add", "--dev", str(source)]
            )
        path = project / ".kiro/prompts" / f"{alias}.md"
        before = path.read_bytes()
        if linked:
            target = project / ".specify/extensions/audit/alias-cache.md"
            target.write_bytes(before)
            path.unlink()
            try:
                path.symlink_to(target)
            except OSError:
                pytest.skip("Symlinks are unavailable")
        manifest_path = project / ".specify/integrations/kiro-cli.manifest.json"
        if core_manifest == "missing":
            manifest_path.unlink()
        elif core_manifest == "unreadable":
            manifest_path.write_bytes(b"invalid: [")
        elif core_manifest == "empty":
            manifest = json.loads(manifest_path.read_bytes())
            manifest["files"] = {}
            manifest_path.write_bytes(json.dumps(manifest).encode())
        snapshot = {p: p.read_bytes() for root in (project / ".specify", project / ".kiro") for p in root.rglob("*") if p.is_file()}
        args = (["integration", "upgrade", "kiro-cli"] if operation == "upgrade" else
                ["init", "--here", "--integration", "kiro-cli", "--script", "sh", "--ignore-agent-tools", "--force"])
        result = _run_in_project(project, args)
        assert path.read_bytes() == before
        if linked:
            assert path.is_symlink() and target.read_bytes() == before
        if alias == "speckit-plan":
            assert result.exit_code == 1, result.output
            assert {p: p.read_bytes() for p in snapshot} == snapshot
        else:
            assert result.exit_code == 0, result.output

    @pytest.mark.parametrize("agent", ["kiro-cli", "qodercli"])
    @pytest.mark.parametrize("legacy", [False, True])
    @pytest.mark.parametrize("content", [None, b"USER FILE\n", b"\xff"])
    def test_manifest_rename_retires_owned_output(self, tmp_path, monkeypatch, agent, legacy, content):
        import yaml
        from specify_cli.agents import CommandRegistrar
        from specify_cli.extensions import ExtensionManager

        source = _write_command_extension(tmp_path)
        if legacy and agent == "kiro-cli":
            project = _init_dotted_kiro_project(tmp_path, monkeypatch, ["extension", "add", "--dev", str(source)])
            old = project / ".kiro/prompts/speckit.audit.run.md"
        else:
            project = _init_project(tmp_path, agent)
            assert _run_in_project(project, ["extension", "add", "--dev", str(source)]).exit_code == 0
            assert _run_in_project(project, ["integration", "use", agent]).exit_code == 0
            registrar = CommandRegistrar(project)
            config = registrar.AGENT_CONFIGS[agent]
            stem = registrar._compute_output_name(agent, "speckit.audit.run", config)
            old = project / config["dir"] / f"{stem}{config['extension']}"
            if legacy:
                flat = project / ".qoder/commands/speckit.audit.run.md"
                flat.parent.mkdir(parents=True)
                flat.write_bytes(old.read_bytes())
                old.unlink()
                old = flat
        if content is not None:
            old.unlink()
            old.write_bytes(content)
        path = project / ".specify/extensions/audit/extension.yml"
        manifest = yaml.safe_load(path.read_bytes())
        manifest["provides"]["commands"][0]["name"] = "speckit.audit.renamed"
        path.write_bytes(yaml.safe_dump(manifest).encode())
        assert _run_in_project(project, ["integration", "use", agent]).exit_code == 0
        if content is None:
            assert not old.exists() and not old.is_symlink()
        else:
            assert old.read_bytes() == content
            assert "speckit.audit.run" in ExtensionManager(project).registry.get("audit")["registered_commands"][agent]
        result = _run_in_project(project, ["extension", "remove", "audit", "--force"])
        assert result.exit_code == 0, result.output
        if content is not None:
            assert old.read_bytes() == content
            assert "Preserving" in result.output

    @pytest.mark.parametrize("agent", ["kiro-cli", "qodercli"])
    @pytest.mark.parametrize("operation", ["remove", "switch"])
    @pytest.mark.parametrize("readable_manifest", [True, False])
    @pytest.mark.parametrize("damage", ["per-agent", None, [], "speckit.audit.run", "missing", "empty", "stale"])
    def test_malformed_cleanup_recovers_names_or_keeps_tracking(self, tmp_path, agent, operation, readable_manifest, damage):
        from specify_cli.agents import CommandRegistrar
        from specify_cli.extensions import ExtensionManager

        project = _init_project(tmp_path, agent)
        source = _write_command_extension(tmp_path, aliases=["audit-extra"] if damage in ("missing", "empty") else [])
        assert _run_in_project(project, ["extension", "add", "--dev", str(source)]).exit_code == 0
        assert _run_in_project(project, ["integration", "use", agent]).exit_code == 0
        registrar = CommandRegistrar(project)
        config = registrar.AGENT_CONFIGS[agent]
        def output(name):
            return project / config["dir"] / f"{registrar._compute_output_name(agent, name, config)}{config['extension']}"
        owned, unrelated = output("speckit.audit.run"), output("audit-extra" if damage in ("missing", "empty") else "s")
        owned_body = owned.read_bytes()
        unrelated.parent.mkdir(parents=True, exist_ok=True)
        unrelated.unlink(missing_ok=True)
        unrelated.write_bytes(b"USER\n")
        manager = ExtensionManager(project)
        recorded = {agent: "speckit.audit.run"} if damage == "per-agent" else damage
        if damage == "stale":
            import yaml

            manifest_path = project / ".specify/extensions/audit/extension.yml"
            manifest = yaml.safe_load(manifest_path.read_bytes())
            manifest["provides"]["commands"][0]["name"] = "speckit.audit.renamed"
            manifest_path.write_bytes(yaml.safe_dump(manifest).encode())
            recorded = {agent: ["speckit.audit.run", 1]}
        manager.registry.update("audit", {"registered_commands": recorded})
        if damage in ("missing", "empty"):
            registry = project / ".specify/extensions/.registry"
            data = json.loads(registry.read_bytes())
            if damage == "missing":
                del data["extensions"]["audit"]["registered_commands"]
            else:
                data["extensions"]["audit"] = {}
            registry.write_bytes(json.dumps(data).encode())
        if not readable_manifest:
            (project / ".specify/extensions/audit/extension.yml").write_bytes(b"invalid: [")
        args = ["extension", "remove", "audit", "--force"] if operation == "remove" else ["integration", "switch", "claude"]
        result = _run_in_project(project, args)
        assert unrelated.read_bytes() == b"USER\n"
        if readable_manifest:
            assert result.exit_code == 0, result.output
            assert not owned.exists()
            if operation == "switch" and damage in ("missing", "empty"):
                tracked = ExtensionManager(project).registry.get("audit")["registered_commands"]
                assert {"speckit.audit.run", "audit-extra"} <= set(tracked[agent])
                unrelated.write_bytes(owned_body)
                assert _run_in_project(project, ["extension", "remove", "audit", "--force"]).exit_code == 0
                assert not unrelated.exists()
        else:
            assert os.path.lexists(owned)
            metadata = ExtensionManager(project).registry.get("audit")
            if operation == "remove":
                assert result.exit_code == 0, result.output
                assert metadata is None
            elif damage in ("missing", "empty"):
                assert "registered_commands" not in metadata
            else:
                assert metadata["registered_commands"] == recorded
            assert "Neither its manifest nor its registered commands can be read." in _normalize_cli_output(result.output)
            assert f"Keeping its command files for {agent}." in _normalize_cli_output(result.output)

    @pytest.mark.parametrize("target_agent", ["kiro-cli", "qodercli"])
    @pytest.mark.parametrize("damage", ["missing", "null-agent"])
    def test_refresh_recovers_unknown_tracking_before_removal(self, tmp_path, target_agent, damage):
        from specify_cli.extensions import ExtensionManager

        project = _init_project(tmp_path, "kiro-cli")
        assert _run_in_project(project, ["extension", "add", "git"]).exit_code == 0
        prompt = next((project / ".kiro/prompts").glob("*git*commit.md"))
        before = prompt.read_bytes()
        if target_agent == "kiro-cli":
            (project / ".specify/extensions/git/commands/speckit.git.commit.md").unlink()
        else:
            assert _run_in_project(project, ["integration", "install", target_agent]).exit_code == 0
        registry = project / ".specify/extensions/.registry"
        data = json.loads(registry.read_bytes())
        if damage == "missing":
            del data["extensions"]["git"]["registered_commands"]
        else:
            data["extensions"]["git"]["registered_commands"] = {"kiro-cli": None}
        registry.write_bytes(json.dumps(data).encode())
        result = _run_in_project(project, ["integration", "use", target_agent])
        assert result.exit_code == 0, result.output
        assert prompt.read_bytes() == before
        tracked = ExtensionManager(project).registry.get("git")["registered_commands"]
        assert "speckit.git.commit" in tracked["kiro-cli"]
        assert _run_in_project(project, ["extension", "remove", "git", "--force"]).exit_code == 0
        assert not prompt.exists()

    @pytest.mark.parametrize("tracking", ["valid", "missing", "null-agent"])
    def test_failed_update_restores_qoder_legacy_commands(self, tmp_path, monkeypatch, tracking):
        import yaml
        from contextlib import chdir
        from specify_cli.extensions import ExtensionCatalog, ExtensionManager

        project = _init_project(tmp_path, "qodercli")
        source = _write_command_extension(tmp_path)
        assert _run_in_project(project, ["extension", "add", "--dev", str(source)]).exit_code == 0
        legacy = project / ".qoder/commands/speckit.audit.run.md"
        legacy.parent.mkdir(parents=True)
        body = b"<!-- Extension: audit -->\nLOCAL LEGACY EDIT\n"
        legacy.write_bytes(body)
        (project / ".qoder/skills/speckit-audit-run/SKILL.md").unlink()
        registry = project / ".specify/extensions/.registry"
        data = json.loads(registry.read_bytes())
        if tracking == "missing":
            del data["extensions"]["audit"]["registered_commands"]
        elif tracking == "null-agent":
            data["extensions"]["audit"]["registered_commands"] = {"qodercli": None}
        registry.write_bytes(json.dumps(data).encode())
        monkeypatch.setattr(ExtensionCatalog, "get_extension_info", lambda *args: {
            "id": "audit", "name": "Audit", "version": "2.0.0", "bundled": True, "_install_allowed": True,
        })
        monkeypatch.setattr("specify_cli._locate_bundled_extension", lambda key: source)
        monkeypatch.setattr(ExtensionCatalog, "download_extension", lambda *args: pytest.fail("Unexpected download"))
        manifest_path = source / "extension.yml"
        manifest = yaml.safe_load(manifest_path.read_bytes())
        manifest["extension"]["version"] = "2.0.0"
        manifest_path.write_bytes(yaml.safe_dump(manifest).encode())
        def fail_install(*args, **kwargs):
            raise RuntimeError("Injected install failure")
        monkeypatch.setattr(ExtensionManager, "install_from_zip", fail_install)
        with chdir(project):
            result = runner.invoke(app, ["extension", "update", "audit"], input="y\n", catch_exceptions=False)
        assert result.exit_code == 1, result.output
        assert "Injected install failure" in result.output
        assert legacy.read_bytes() == body
        assert json.loads(registry.read_bytes()) == data

    @pytest.mark.parametrize("agent", ["kiro-cli", "qodercli"])
    @pytest.mark.parametrize("operation", ["use", "upgrade"])
    @pytest.mark.parametrize("missing_source", [False, True])
    def test_dropped_alias_keeps_declared_command_output(self, tmp_path, agent, operation, missing_source):
        import yaml
        from specify_cli.agents import CommandRegistrar

        project = _init_project(tmp_path, agent)
        source = _write_command_extension(tmp_path, aliases=["audit-run"])
        assert _run_in_project(project, ["extension", "add", "--dev", str(source)]).exit_code == 0
        assert _run_in_project(project, ["integration", "use", agent]).exit_code == 0
        registrar = CommandRegistrar(project)
        config = registrar.AGENT_CONFIGS[agent]
        stem = registrar._compute_output_name(agent, "speckit.audit.run", config)
        path = project / config["dir"] / f"{stem}{config['extension']}"
        before = path.read_bytes()
        manifest_path = project / ".specify/extensions/audit/extension.yml"
        manifest = yaml.safe_load(manifest_path.read_bytes())
        manifest["provides"]["commands"][0]["aliases"] = []
        manifest_path.write_bytes(yaml.safe_dump(manifest).encode())
        if missing_source:
            (manifest_path.parent / "commands/run.md").unlink()
        result = _run_in_project(project, ["integration", operation, agent])
        assert result.exit_code == 0, result.output
        assert path.is_file()
        assert path.read_bytes() == before if missing_source else b"AUDIT-BODY" in path.read_bytes()

    @pytest.mark.parametrize("missing_source", [False, True])
    def test_dropped_legacy_alias_stays_tracked_for_removal(self, tmp_path, monkeypatch, missing_source):
        import yaml
        from specify_cli.extensions import ExtensionManager

        source = _write_command_extension(tmp_path, aliases=["audit-run"])
        project = _init_dotted_kiro_project(tmp_path, monkeypatch, ["extension", "add", "--dev", str(source)])
        alias = project / ".kiro/prompts/audit-run.md"
        assert alias.is_file()
        path = project / ".specify/extensions/audit/extension.yml"
        manifest = yaml.safe_load(path.read_bytes())
        manifest["provides"]["commands"][0]["aliases"] = []
        path.write_bytes(yaml.safe_dump(manifest).encode())
        if missing_source:
            (path.parent / "commands/run.md").unlink()
        assert _run_in_project(project, ["integration", "use", "kiro-cli"]).exit_code == 0
        assert "audit-run" in ExtensionManager(project).registry.get("audit")["registered_commands"]["kiro-cli"]
        assert _run_in_project(project, ["extension", "remove", "audit", "--force"]).exit_code == 0
        assert not os.path.lexists(alias)

    @pytest.mark.parametrize("operation", ["use", "upgrade", "reinstall", "update", "remove"])
    def test_template_metadata_does_not_hide_generated_owner(self, tmp_path, monkeypatch, operation):
        from specify_cli.extensions import ExtensionCatalog
        from specify_cli.agents import CommandRegistrar
        from contextlib import chdir

        project = _init_project(tmp_path, "kiro-cli")
        source = _write_command_extension(tmp_path)
        (source / "commands/run.md").write_bytes(
            b"---\ndescription: Audit\nmetadata: {source: upstream-template}\n---\nAUDIT-BODY\n"
        )
        assert _run_in_project(project, ["extension", "add", "--dev", str(source)]).exit_code == 0
        registrar = CommandRegistrar(project)
        config = registrar.AGENT_CONFIGS["kiro-cli"]
        stem = registrar._compute_output_name("kiro-cli", "speckit.audit.run", config)
        path = project / config["dir"] / f"{stem}{config['extension']}"
        assert path.is_file()
        if operation == "update":
            manifest_path = source / "extension.yml"
            manifest_path.write_bytes(manifest_path.read_bytes().replace(b"version: 1.0.0", b"version: 2.0.0"))
            monkeypatch.setattr(ExtensionCatalog, "get_extension_info", lambda *args: {
                "id": "audit", "name": "Audit", "version": "2.0.0", "bundled": True, "_install_allowed": True,
            })
            monkeypatch.setattr("specify_cli._locate_bundled_extension", lambda key: source)
            monkeypatch.setattr(ExtensionCatalog, "download_extension", lambda *args: pytest.fail("Unexpected download"))
            with chdir(project):
                result = runner.invoke(app, ["extension", "update", "audit"], input="y\n", catch_exceptions=False)
        else:
            args = (["extension", "remove", "audit", "--force"] if operation == "remove" else
                    ["extension", "add", "--dev", str(source), "--force"] if operation == "reinstall" else
                    ["integration", operation, "kiro-cli"])
            result = _run_in_project(project, args)
        assert result.exit_code == 0, result.output
        assert "not marked as owned" not in _normalize_cli_output(result.output)
        if operation == "remove":
            assert not os.path.lexists(path)
        else:
            assert b"AUDIT-BODY" in path.read_bytes()

    @pytest.mark.parametrize("agent,source_metadata", [
        ("kiro-cli", "foo:upstream-template"), ("kiro-cli", "extension:foo"), ("qodercli", None),
    ])
    def test_generated_owner_overrules_other_formats_marker(self, tmp_path, monkeypatch, agent, source_metadata):
        import yaml
        from specify_cli.extensions import ExtensionManager

        sources = []
        for extension_id, command in (("foo", "speckit.foo.bar-baz"), ("foo-bar", "speckit.foo-bar.baz")):
            source = _write_command_extension(tmp_path / extension_id)
            path = source / "extension.yml"
            manifest = yaml.safe_load(path.read_bytes())
            manifest["extension"]["id"] = extension_id
            manifest["provides"]["commands"][0]["name"] = command
            if extension_id == "foo-bar":
                manifest["provides"]["commands"][0]["aliases"] = ["speckit-foo-bar-baz"] if agent == "kiro-cli" else []
                frontmatter = {"description": "Borrowed template", "metadata": {"source": source_metadata}}
                (source / "commands/run.md").write_bytes(
                    ("---\n" + yaml.safe_dump(frontmatter) + "---\nSURVIVOR\n<!-- Extension: foo -->\n").encode()
                )
            path.write_bytes(yaml.safe_dump(manifest).encode())
            sources.append(source)
        with monkeypatch.context() as patch:
            patch.setattr(ExtensionManager, "_validate_install_conflicts", lambda *args: None)
            commands = [["extension", "add", "--dev", str(source)] for source in sources]
            if agent == "kiro-cli":
                project = _init_dotted_kiro_project(tmp_path, patch, *commands)
            else:
                project = _init_project(tmp_path, agent)
                for args in commands:
                    assert _run_in_project(project, args).exit_code == 0
        path = project / (".kiro/prompts/speckit-foo-bar-baz.md" if agent == "kiro-cli" else
                          ".qoder/skills/speckit-foo-bar-baz/SKILL.md")
        before = path.read_bytes()
        assert b"SURVIVOR" in before
        result = _run_in_project(project, ["extension", "remove", "foo", "--force"])
        assert result.exit_code == 0, result.output
        assert path.read_bytes() == before
        assert ExtensionManager(project).registry.get("foo-bar")["enabled"]

    @pytest.mark.parametrize("readable_preset", [True, False])
    @pytest.mark.parametrize("operation", ["use", "upgrade", "reinstall", "update"])
    def test_pending_migration_preserves_preset_override(self, tmp_path, monkeypatch, operation, readable_preset):
        import yaml
        from contextlib import chdir
        from specify_cli.extensions import ExtensionCatalog, ExtensionManager

        source = _write_command_extension(tmp_path)
        project = _init_dotted_kiro_project(tmp_path, monkeypatch, ["extension", "add", "--dev", str(source)])
        assert _run_in_project(project, ["extension", "disable", "audit"]).exit_code == 0
        assert _run_in_project(project, ["integration", "upgrade", "kiro-cli"]).exit_code == 0
        preset = _write_command_preset(tmp_path, "audit-preset")
        preset_path = preset / "preset.yml"
        data = yaml.safe_load(preset_path.read_bytes())
        data["provides"]["templates"][0]["name"] = "speckit.audit.run"
        preset_path.write_bytes(yaml.safe_dump(data).encode())
        assert _run_in_project(project, ["preset", "add", "--dev", str(preset)]).exit_code == 0
        destination = project / ".kiro/prompts/speckit-audit-run.md"
        before = destination.read_bytes()
        legacy = project / ".kiro/prompts/speckit.audit.run.md"
        old_content = legacy.read_bytes()
        tracked = ExtensionManager(project).registry.get("audit")["registered_commands"]
        if not readable_preset:
            (project / ".specify/presets/audit-preset/preset.yml").write_bytes(b"invalid: [")
        assert _run_in_project(project, ["extension", "enable", "audit"]).exit_code == 0
        if operation == "update":
            monkeypatch.setattr(ExtensionCatalog, "get_extension_info", lambda *args: {
                "id": "audit", "name": "Audit", "version": "2.0.0", "bundled": True, "_install_allowed": True,
            })
            monkeypatch.setattr("specify_cli._locate_bundled_extension", lambda key: source)
            monkeypatch.setattr(ExtensionCatalog, "download_extension", lambda *args: pytest.fail("Unexpected download"))
            manifest_path = source / "extension.yml"
            manifest = yaml.safe_load(manifest_path.read_bytes())
            manifest["extension"]["version"] = "2.0.0"
            manifest_path.write_bytes(yaml.safe_dump(manifest).encode())
            with chdir(project):
                result = runner.invoke(app, ["extension", "update", "audit"], input="y\n", catch_exceptions=False)
        else:
            args = (["extension", "add", "--dev", str(source), "--force"] if operation == "reinstall" else
                    ["integration", operation, "kiro-cli"] + (["--force"] if operation == "upgrade" else []))
            result = _run_in_project(project, args)
        assert result.exit_code == (1 if operation in ("reinstall", "update") else 0), result.output
        assert "Move or remove" in _normalize_cli_output(result.output)
        assert destination.read_bytes() == before
        assert legacy.read_bytes() == old_content
        assert ExtensionManager(project).registry.get("audit")["registered_commands"] == tracked

    @pytest.mark.parametrize("alias", ["SKILL", "ordinary-alias"])
    @pytest.mark.parametrize("operation", ["remove", "switch", "use", "upgrade"])
    def test_flat_alias_uses_command_ownership_regardless_of_basename(self, tmp_path, monkeypatch, alias, operation):
        source = _write_command_extension(tmp_path, aliases=[alias])
        project = _init_dotted_kiro_project(
            tmp_path, monkeypatch, ["extension", "add", "--dev", str(source)], ["integration", "use", "kiro-cli"]
        )
        legacy = project / ".kiro/prompts" / f"{alias}.md"
        assert b"<!-- Extension: audit -->" in legacy.read_bytes()
        if operation == "remove":
            args = ["extension", "remove", "audit", "--force"]
        elif operation == "switch":
            args = ["integration", "switch", "claude"]
        else:
            args = ["integration", operation, "kiro-cli"]
        result = _run_in_project(project, args)
        assert result.exit_code == 0, result.output
        if operation in ("use", "upgrade"):
            assert _run_in_project(project, ["extension", "remove", "audit", "--force"]).exit_code == 0
        assert not os.path.lexists(legacy)

    @pytest.mark.parametrize("operation", ["reinstall", "update"])
    @pytest.mark.parametrize("destination_kind", ["file", "symlink", "absent"])
    def test_package_rename_preserves_pending_destination(self, tmp_path, monkeypatch, operation, destination_kind):
        import yaml
        from contextlib import chdir
        from specify_cli.extensions import ExtensionCatalog

        source = _write_command_extension(tmp_path)
        project = _init_dotted_kiro_project(tmp_path, monkeypatch, ["extension", "add", "--dev", str(source)])
        destination = project / ".kiro/prompts/speckit-audit-run.md"
        target = project / "user-workaround.md"
        before = b"USER WORKAROUND\n"
        if destination_kind == "file":
            destination.write_bytes(before)
        elif destination_kind == "symlink":
            target.write_bytes(before)
            try:
                destination.symlink_to(target)
            except OSError:
                pytest.skip("Symlinks are unavailable")
        path = source / "extension.yml"
        manifest = yaml.safe_load(path.read_bytes())
        manifest["provides"]["commands"][0].update(name="speckit.audit.other", aliases=["audit-run"])
        manifest["extension"]["version"] = "2.0.0"
        path.write_bytes(yaml.safe_dump(manifest).encode())
        if operation == "update":
            monkeypatch.setattr(ExtensionCatalog, "get_extension_info", lambda *args: {
                "id": "audit", "name": "Audit", "version": "2.0.0", "bundled": True, "_install_allowed": True,
            })
            monkeypatch.setattr("specify_cli._locate_bundled_extension", lambda key: source)
            monkeypatch.setattr(ExtensionCatalog, "download_extension", lambda *args: pytest.fail("Unexpected download"))
            with chdir(project):
                result = runner.invoke(app, ["extension", "update", "audit"], input="y\n", catch_exceptions=False)
        else:
            result = _run_in_project(project, ["extension", "add", "--dev", str(source), "--force"])
        if destination_kind == "absent":
            assert result.exit_code == 0, result.output
            from specify_cli.agents import CommandRegistrar

            registrar = CommandRegistrar(project)
            config = registrar.AGENT_CONFIGS["kiro-cli"]
            stem = registrar._compute_output_name("kiro-cli", "audit-run", config)
            assert b"AUDIT-BODY" in (project / config["dir"] / f"{stem}{config['extension']}").read_bytes()
        else:
            assert destination.read_bytes() == before
            if destination_kind == "symlink":
                assert destination.is_symlink() and target.read_bytes() == before

    def _plant_extension(
        self,
        project,
        ext_id,
        commands,
        *,
        enabled=True,
        registered=None,
        agent="kiro-cli",
    ):
        """Write an extension that is already installed, skipping install checks."""
        import yaml

        from specify_cli.extensions import ExtensionManager

        ext_dir = project / ".specify" / "extensions" / ext_id
        (ext_dir / "commands").mkdir(parents=True, exist_ok=True)
        manifest_commands = []
        registered_names = []
        for command in commands:
            filename = f"{command['name']}.md"
            (ext_dir / "commands" / filename).write_text(
                command["body"], encoding="utf-8"
            )
            entry = {"name": command["name"], "file": f"commands/{filename}"}
            if command.get("aliases"):
                entry["aliases"] = list(command["aliases"])
            manifest_commands.append(entry)
            registered_names.append(command["name"])
            registered_names.extend(command.get("aliases") or [])
        (ext_dir / "extension.yml").write_text(yaml.safe_dump({
            "schema_version": "1.0",
            "extension": {
                "id": ext_id,
                "name": ext_id,
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {"commands": manifest_commands},
        }), encoding="utf-8")
        ExtensionManager(project).registry.add(ext_id, {
            "version": "1.0.0",
            "source": "local",
            "enabled": enabled,
            "priority": 10,
            "registered_commands": {
                agent: list(registered) if registered is not None else registered_names
            },
            "registered_skills": [],
        })

    def test_upgrade_leaves_extensions_that_hyphenate_to_one_prompt_unregistered(
        self, tmp_path, monkeypatch
    ):
        """``speckit.foo.bar-baz`` and ``speckit.foo-bar.baz`` both become
        ``speckit-foo-bar-baz.md`` (#4797). Install rejects that pair, but a
        project can already have both. Upgrade must not write one body over
        the other or retire either dotted prompt, so both extensions stay as
        they were until one is removed. Everything else still moves."""
        project = _init_dotted_kiro_project(
            tmp_path, monkeypatch, ["extension", "add", "git"]
        )
        prompts = project / ".kiro" / "prompts"
        foo_body = "---\ndescription: Foo\n---\n\n<!-- Extension: foo -->\nFOO-BODY\n"
        bar_body = "---\ndescription: Bar\n---\n\n<!-- Extension: foo-bar -->\nBAR-BODY\n"
        other_body = "---\ndescription: Other\n---\n\n<!-- Extension: foo -->\nOTHER-BODY\n"
        self._plant_extension(project, "foo", [
            {"name": "speckit.foo.bar-baz", "body": foo_body},
            {"name": "speckit.foo.other", "body": other_body},
        ])
        self._plant_extension(project, "foo-bar", [
            {"name": "speckit.foo-bar.baz", "body": bar_body},
        ])
        planted = {
            "speckit.foo.bar-baz.md": foo_body,
            "speckit.foo.other.md": other_body,
            "speckit.foo-bar.baz.md": bar_body,
        }
        for name, body in planted.items():
            (prompts / name).write_bytes(body.encode("utf-8"))
        registry_path = project / ".specify" / "extensions" / ".registry"
        before = json.loads(registry_path.read_text(encoding="utf-8"))["extensions"]

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        output = " ".join(result.output.split())
        assert (
            "speckit.foo.bar-baz (speckit-foo-bar-baz, also written by "
            "extension 'foo-bar')"
        ) in output
        assert (
            "speckit.foo-bar.baz (speckit-foo-bar-baz, also written by "
            "extension 'foo')"
        ) in output
        for name, body in planted.items():
            assert (prompts / name).read_bytes() == body.encode("utf-8"), name
        assert not (prompts / "speckit-foo-bar-baz.md").exists()
        assert not (prompts / "speckit-foo-other.md").exists()
        after = json.loads(registry_path.read_text(encoding="utf-8"))["extensions"]
        for ext_id in ("foo", "foo-bar"):
            assert (
                after[ext_id]["registered_commands"]
                == before[ext_id]["registered_commands"]
            )
        assert (prompts / "speckit-plan.md").is_file()
        assert (prompts / "speckit-git-commit.md").is_file()
        assert not (prompts / "speckit.git.commit.md").exists()

        result = _run_in_project(
            project, ["extension", "remove", "foo-bar", "--force"]
        )
        assert result.exit_code == 0, result.output
        assert not (prompts / "speckit.foo-bar.baz.md").exists()
        assert (prompts / "speckit.foo.bar-baz.md").read_bytes() == foo_body.encode(
            "utf-8"
        )

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        assert "FOO-BODY" in (prompts / "speckit-foo-bar-baz.md").read_text(
            encoding="utf-8"
        )
        assert "OTHER-BODY" in (prompts / "speckit-foo-other.md").read_text(
            encoding="utf-8"
        )
        assert sorted(prompts.glob("speckit.*.md")) == []

    @pytest.mark.parametrize("state", ["disabled", "unreadable"])
    def test_inactive_extension_keeps_its_claim_on_a_shared_kiro_prompt(
        self, tmp_path, monkeypatch, state
    ):
        """A disabled extension, or one whose manifest can't be read, is not
        registered, but its tracked dotted prompt is still on disk. Moving the
        other extension onto ``speckit-foo-bar-baz.md`` would let removing the
        first one delete that file, so both stay as they were (#4797)."""
        project = _init_dotted_kiro_project(tmp_path, monkeypatch)
        prompts = project / ".kiro" / "prompts"
        foo_body = "---\ndescription: Foo\n---\n\n<!-- Extension: foo -->\nFOO-BODY\n"
        bar_body = "---\ndescription: Bar\n---\n\n<!-- Extension: foo-bar -->\nBAR-BODY\n"
        self._plant_extension(project, "foo", [
            {"name": "speckit.foo.bar-baz", "body": foo_body},
        ])
        self._plant_extension(
            project,
            "foo-bar",
            [{"name": "speckit.foo-bar.baz", "body": bar_body}],
            enabled=state != "disabled",
        )
        if state == "unreadable":
            (
                project / ".specify" / "extensions" / "foo-bar" / "extension.yml"
            ).write_text("invalid: [", encoding="utf-8")
        (prompts / "speckit.foo.bar-baz.md").write_bytes(foo_body.encode("utf-8"))
        (prompts / "speckit.foo-bar.baz.md").write_bytes(bar_body.encode("utf-8"))

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        assert (prompts / "speckit.foo.bar-baz.md").read_bytes() == foo_body.encode(
            "utf-8"
        )
        assert not (prompts / "speckit-foo-bar-baz.md").exists()

        result = _run_in_project(
            project, ["extension", "remove", "foo-bar", "--force"]
        )
        assert result.exit_code == 0, result.output
        assert not (prompts / "speckit.foo-bar.baz.md").exists()

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        assert "FOO-BODY" in (prompts / "speckit-foo-bar-baz.md").read_text(
            encoding="utf-8"
        )
        assert not (prompts / "speckit.foo.bar-baz.md").exists()

    @pytest.mark.parametrize(
        "damage",
        [[], "speckit.foo-bar.baz", {"kiro-cli": "speckit.foo-bar.baz"}, {"kiro-cli": [1]}, "missing"],
    )
    def test_disabled_extension_with_unreadable_registration_keeps_its_prompt(
        self, tmp_path, damage
    ):
        """A disabled extension's prompt stays on disk. When its registry
        entry can't be read, its manifest still names the command, so another
        extension that writes the same file is not registered over it
        (#4797)."""
        project = _init_project(tmp_path, "kiro-cli")
        self._plant_extension(project, "foo-bar", [
            {"name": "speckit.foo-bar.baz", "body": "BAR-BODY\n"},
        ], enabled=False)
        shared = project / ".kiro" / "prompts" / "speckit-foo-bar-baz.md"
        body = b"---\ndescription: Bar\n---\n\n<!-- Extension: foo-bar -->\nBAR-BODY\n"
        shared.write_bytes(body)
        registry = project / ".specify" / "extensions" / ".registry"
        data = json.loads(registry.read_bytes())
        if damage == "missing":
            del data["extensions"]["foo-bar"]["registered_commands"]
        else:
            data["extensions"]["foo-bar"]["registered_commands"] = damage
        registry.write_bytes(json.dumps(data).encode())
        self._plant_extension(project, "foo", [
            {"name": "speckit.foo.bar-baz", "body": "FOO-BODY\n"},
        ])

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        assert (
            "speckit.foo.bar-baz (speckit-foo-bar-baz, also written by "
            "extension 'foo-bar')"
        ) in " ".join(result.output.split())
        assert shared.read_bytes() == body

    def test_enabling_a_colliding_extension_keeps_the_migrated_prompt(
        self, tmp_path, monkeypatch
    ):
        """A disabled extension with no Kiro prompts does not block the other
        one's rename. Enabling it only flips its flag, and the next
        registration pass leaves both as they are instead of writing its body
        over the migrated prompt (#4797). Removing the migrated extension
        deletes its own prompt, and the other one moves on the next pass."""
        project = _init_dotted_kiro_project(tmp_path, monkeypatch)
        prompts = project / ".kiro" / "prompts"
        foo_body = "---\ndescription: Foo\n---\n\n<!-- Extension: foo -->\nFOO-BODY\n"
        bar_body = "---\ndescription: Bar\n---\n\n<!-- Extension: foo-bar -->\nBAR-BODY\n"
        self._plant_extension(project, "foo", [
            {"name": "speckit.foo.bar-baz", "body": foo_body},
        ])
        self._plant_extension(
            project,
            "foo-bar",
            [{"name": "speckit.foo-bar.baz", "body": bar_body}],
            enabled=False,
            registered=[],
        )
        (prompts / "speckit.foo.bar-baz.md").write_bytes(foo_body.encode("utf-8"))
        migrated = prompts / "speckit-foo-bar-baz.md"

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        assert "FOO-BODY" in migrated.read_text(encoding="utf-8")
        assert not (prompts / "speckit.foo.bar-baz.md").exists()

        for args in (
            ["extension", "enable", "foo-bar"],
            ["integration", "upgrade", "kiro-cli"],
        ):
            result = _run_in_project(project, args)
            assert result.exit_code == 0, result.output
        assert (
            "speckit.foo-bar.baz (speckit-foo-bar-baz, also written by "
            "extension 'foo')"
        ) in " ".join(result.output.split())
        assert "FOO-BODY" in migrated.read_text(encoding="utf-8")

        result = _run_in_project(project, ["extension", "remove", "foo", "--force"])
        assert result.exit_code == 0, result.output
        assert not migrated.exists()

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        assert "BAR-BODY" in migrated.read_text(encoding="utf-8")

    def test_alias_that_hyphenates_onto_a_core_prompt_never_replaces_it(
        self, tmp_path, monkeypatch
    ):
        """Spec Kit 1.0.7 and earlier accepted an alias like ``plan``, which
        Kiro CLI now names ``speckit-plan.md``, the core prompt's file. The
        extension is left unregistered, and removing it keeps the core
        prompt while deleting the extension's own files (#4797)."""
        project = _init_dotted_kiro_project(tmp_path, monkeypatch)
        prompts = project / ".kiro" / "prompts"
        body = "---\ndescription: Old\n---\n\n<!-- Extension: old -->\nOLD-BODY\n"
        self._plant_extension(project, "old", [
            {"name": "speckit.old.plan", "body": body, "aliases": ["plan"]},
        ])
        for name in ("speckit.old.plan", "plan"):
            (prompts / f"{name}.md").write_bytes(body.encode("utf-8"))

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        assert (
            "plan (speckit-plan, also written by a core command)"
        ) in " ".join(result.output.split())
        core_plan = prompts / "speckit-plan.md"
        assert "OLD-BODY" not in core_plan.read_text(encoding="utf-8")
        core_bytes = core_plan.read_bytes()

        result = _run_in_project(project, ["extension", "remove", "old", "--force"])
        assert result.exit_code == 0, result.output
        assert core_plan.read_bytes() == core_bytes
        assert not (prompts / "speckit.old.plan.md").exists()
        assert not (prompts / "plan.md").exists()

    @pytest.mark.parametrize("agent", ["kiro-cli", "qodercli"])
    @pytest.mark.parametrize("damage", ["missing", "empty-files"])
    def test_removal_preserves_core_without_manifest_tracking(self, tmp_path, agent, damage):
        """An old alias must not delete an untracked core prompt (#4797)."""
        project = _init_project(tmp_path, agent)
        self._plant_extension(project, "old", [{
            "name": "speckit.old.plan", "aliases": ["plan"], "body": "OLD-BODY\n",
        }], agent=agent)
        core = project / (
            ".kiro/prompts/speckit-plan.md" if agent == "kiro-cli"
            else ".qoder/skills/speckit-plan/SKILL.md"
        )
        before = core.read_bytes()
        manifest = project / ".specify/integrations" / f"{agent}.manifest.json"
        if damage == "missing":
            manifest.unlink()
        else:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["files"] = {}
            manifest.write_text(json.dumps(data), encoding="utf-8")

        result = _run_in_project(project, ["extension", "remove", "old", "--force"])
        assert result.exit_code == 0, result.output
        assert core.read_bytes() == before
        assert "Preserving" not in result.output

    @pytest.mark.parametrize("operation", ["switch", "uninstall"])
    def test_integration_cleanup_preserves_modified_core_with_old_alias(
        self, tmp_path, monkeypatch, operation
    ):
        """Switch tests extension cleanup; uninstall tests only manifest teardown (#4797)."""
        project = _init_dotted_kiro_project(tmp_path, monkeypatch)
        self._plant_extension(project, "old", [{
            "name": "speckit.old.plan", "aliases": ["plan"], "body": "OLD-BODY\n",
        }])
        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        core = project / ".kiro/prompts/speckit-plan.md"
        before = core.read_bytes() + b"\nUser customization\n"
        core.write_bytes(before)

        target = "claude" if operation == "switch" else "kiro-cli"
        result = _run_in_project(project, ["integration", operation, target])
        assert result.exit_code == 0, result.output
        assert core.read_bytes() == before

    @pytest.mark.parametrize("agent", ["kiro-cli", "qodercli"])
    @pytest.mark.parametrize("state", ["enabled", "disabled", "unreadable"])
    @pytest.mark.parametrize("removed", ["foo", "foo-bar"])
    @pytest.mark.parametrize("marker", ["generated", "missing", "invalid-utf8"])
    def test_removing_colliding_extension_preserves_other_owners_migrated_file(
        self, tmp_path, agent, state, removed, marker
    ):
        from specify_cli.extensions import ExtensionManager

        project = _init_project(tmp_path, agent)
        self._plant_extension(
            project,
            "foo",
            [{"name": "speckit.foo.bar-baz", "body": "FOO-BODY\n"}],
            agent=agent,
        )
        manager = ExtensionManager(project)
        manager.register_enabled_extensions_for_agent(agent)
        if agent == "kiro-cli":
            migrated = project / ".kiro/prompts/speckit-foo-bar-baz.md"
            legacy = project / ".kiro/prompts/speckit.foo-bar.baz.md"
        else:
            migrated = project / ".qoder/skills/speckit-foo-bar-baz/SKILL.md"
            legacy = project / ".qoder/commands/speckit.foo-bar.baz.md"
        assert b"FOO-BODY" in migrated.read_bytes()
        if marker == "missing":
            migrated.write_text("UNMARKED-BODY\n", encoding="utf-8")
        elif marker == "invalid-utf8":
            migrated.write_bytes(b"\xff")
        before = migrated.read_bytes()

        self._plant_extension(
            project,
            "foo-bar",
            [{
                "name": "speckit.foo-bar.baz",
                "body": "BAR-BODY\n",
                "aliases": ["speckit-foo-bar-baz"],
            }],
            enabled=state != "disabled",
            agent=agent,
        )
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy_body = "---\ndescription: Bar\n---\n\n<!-- Extension: foo-bar -->\nBAR-BODY\n"
        legacy.write_text(legacy_body, encoding="utf-8")
        legacy_alias = legacy.parent / "speckit-foo-bar-baz.md"
        alias_body = "---\ndescription: Bar\n---\n\n<!-- Extension: foo-bar -->\nBAR-ALIAS\n"
        if agent == "qodercli":
            legacy_alias.write_text(alias_body, encoding="utf-8")
        if state == "unreadable":
            (
                project / ".specify/extensions/foo-bar/extension.yml"
            ).write_text("invalid: [", encoding="utf-8")

        manager = ExtensionManager(project)
        manager.register_enabled_extensions_for_agent(agent)
        assert migrated.read_bytes() == before
        assert legacy.read_text(encoding="utf-8") == legacy_body

        result = _run_in_project(
            project, ["extension", "remove", removed, "--force"]
        )
        assert result.exit_code == 0, result.output
        if removed == "foo-bar" or marker != "generated":
            assert migrated.read_bytes() == before
            assert "Preserving the shared file" in result.output
        else:
            assert not migrated.exists()
        if removed == "foo-bar":
            assert not legacy.exists()
            if agent == "qodercli":
                assert not legacy_alias.exists()
        else:
            assert legacy.read_text(encoding="utf-8") == legacy_body
            if agent == "qodercli":
                assert legacy_alias.read_text(encoding="utf-8") == alias_body

    def test_upgrade_refuses_while_an_extension_prompt_has_a_core_prompt_name(
        self, tmp_path, monkeypatch
    ):
        """An older alias ``speckit-plan`` has its prompt where the renamed
        core ``speckit.plan`` goes. Upgrade refuses before changing files.
        Until the rename, that file is the extension's, so removing the
        extension deletes it, and the upgrade then writes the core prompt
        (#4797)."""
        project = _init_dotted_kiro_project(tmp_path, monkeypatch)
        prompts = project / ".kiro" / "prompts"
        body = "---\ndescription: Old\n---\n\n<!-- Extension: old -->\nOLD-BODY\n"
        self._plant_extension(project, "old", [
            {"name": "speckit.old.plan", "body": body, "aliases": ["speckit-plan"]},
        ])
        for name in ("speckit.old.plan", "speckit-plan"):
            (prompts / f"{name}.md").write_bytes(body.encode("utf-8"))
        manifest = project / ".specify" / "integrations" / "kiro-cli.manifest.json"
        before = {path.name: path.read_bytes() for path in prompts.iterdir()}
        manifest_before = manifest.read_bytes()

        for args in (
            ["integration", "upgrade", "kiro-cli"],
            ["integration", "upgrade", "kiro-cli", "--force"],
        ):
            result = _run_in_project(project, args)
            assert result.exit_code == 1, result.output
            assert "old (speckit-plan)" in " ".join(result.output.split())
            assert {
                path.name: path.read_bytes() for path in prompts.iterdir()
            } == before
            assert manifest.read_bytes() == manifest_before

        result = _run_in_project(project, ["extension", "remove", "old", "--force"])
        assert result.exit_code == 0, result.output
        assert not (prompts / "speckit-plan.md").exists()
        assert not (prompts / "speckit.old.plan.md").exists()

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        assert "OLD-BODY" not in (prompts / "speckit-plan.md").read_text(
            encoding="utf-8"
        )
        assert not (prompts / "speckit.plan.md").exists()

    @pytest.mark.parametrize(
        "corruption",
        ["registry", "entry", "registered_commands", "agent_entry", "agent_item", "missing"],
    )
    def test_upgrade_refuses_kiro_prompt_rename_while_extension_registry_is_unreadable(
        self, tmp_path, monkeypatch, corruption
    ):
        """Without a readable registry entry, upgrade can't tell that the
        alias ``speckit-plan`` owns the renamed core prompt's file, so it
        refuses before changing files, even with ``--force`` (#4797)."""
        project = _init_dotted_kiro_project(tmp_path, monkeypatch)
        prompts = project / ".kiro" / "prompts"
        body = "---\ndescription: Old\n---\n\nOLD-BODY\n"
        self._plant_extension(project, "old", [
            {"name": "speckit.old.plan", "body": body, "aliases": ["speckit-plan"]},
        ])
        for name in ("speckit.old.plan", "speckit-plan"):
            (prompts / f"{name}.md").write_bytes(body.encode("utf-8"))
        registry = project / ".specify" / "extensions" / ".registry"
        data = json.loads(registry.read_text(encoding="utf-8"))
        entry = data["extensions"]["old"]
        if corruption == "registry":
            registry.write_text("{not json", encoding="utf-8")
        else:
            if corruption == "entry":
                data["extensions"]["old"] = "old"
            elif corruption == "registered_commands":
                entry["registered_commands"] = "kiro-cli"
            elif corruption == "agent_entry":
                entry["registered_commands"] = {"kiro-cli": "speckit-plan"}
            elif corruption == "missing":
                del entry["registered_commands"]
            else:
                entry["registered_commands"] = {"kiro-cli": [1, 2]}
            registry.write_bytes(json.dumps(data).encode())
        manifest = project / ".specify" / "integrations" / "kiro-cli.manifest.json"
        before = {path.name: path.read_bytes() for path in prompts.iterdir()}
        manifest_before = manifest.read_bytes()

        for args in (
            ["integration", "upgrade", "kiro-cli"],
            ["integration", "upgrade", "kiro-cli", "--force"],
        ):
            result = _run_in_project(project, args)
            assert result.exit_code == 1, result.output
            assert "extension registry could not be read" in " ".join(
                result.output.split()
            )
            assert {
                path.name: path.read_bytes() for path in prompts.iterdir()
            } == before
            assert manifest.read_bytes() == manifest_before

    @pytest.mark.parametrize("linked", [False, True])
    @pytest.mark.parametrize("force", [False, True])
    def test_kiro_upgrade_checks_untracked_core_destinations(self, tmp_path, monkeypatch, linked, force):
        """An empty core manifest cannot bypass destination protection (#4797)."""
        project = _init_dotted_kiro_project(tmp_path, monkeypatch)
        manifest_path = project / ".specify/integrations/kiro-cli.manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        manifest["files"] = {}
        manifest_path.write_bytes(json.dumps(manifest).encode())
        destination = project / ".kiro/prompts/speckit-plan.md"
        body = b"USER PLAN\n"
        target = project / "user-plan.md"
        if linked:
            target.write_bytes(body)
            try:
                destination.symlink_to(target)
            except OSError:
                pytest.skip("Symlinks are unavailable")
        else:
            destination.write_bytes(body)
        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"] + (["--force"] if force else []))
        if force and not linked:
            assert result.exit_code == 0, result.output
            assert destination.read_bytes() != body
        else:
            assert result.exit_code == 1, result.output
            assert ".kiro/prompts/speckit-plan.md" in result.output
            assert destination.read_bytes() == body
            if linked:
                assert destination.is_symlink() and target.read_bytes() == body

    @pytest.mark.parametrize("kind", ["file", "symlink"])
    def test_upgrade_replaces_a_kiro_prompt_it_did_not_install_only_with_force(
        self, tmp_path, monkeypatch, kind
    ):
        """No extension tracks this ``speckit-plan.md``; a user may have
        written it because Kiro ignored the dotted prompts. Upgrade replaces
        it only with ``--force``, and never writes through a symlink (#4797)."""
        project = _init_dotted_kiro_project(tmp_path, monkeypatch)
        prompts = project / ".kiro" / "prompts"
        mine = b"---\ndescription: Mine\n---\n\nMY-PLAN\n"
        if kind == "symlink":
            target = tmp_path / "my-plan.md"
            target.write_bytes(mine)
            try:
                (prompts / "speckit-plan.md").symlink_to(target)
            except OSError:
                pytest.skip("symlinks are unavailable")
        else:
            (prompts / "speckit-plan.md").write_bytes(mine)
        before = {path.name: path.read_bytes() for path in prompts.iterdir()}

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 1, result.output
        assert ".kiro/prompts/speckit-plan.md" in result.output
        assert {path.name: path.read_bytes() for path in prompts.iterdir()} == before

        result = _run_in_project(
            project, ["integration", "upgrade", "kiro-cli", "--force"]
        )
        if kind == "symlink":
            assert result.exit_code == 1, result.output
            assert "Symbolic links are not overwritten" in " ".join(
                result.output.split()
            )
            assert {
                path.name: path.read_bytes() for path in prompts.iterdir()
            } == before
        else:
            assert result.exit_code == 0, result.output
            assert "MY-PLAN" not in (prompts / "speckit-plan.md").read_text(
                encoding="utf-8"
            )
            assert not (prompts / "speckit.plan.md").exists()

    def test_install_refuses_a_kiro_prompt_name_another_extension_still_tracks(
        self, tmp_path
    ):
        """foo's manifest stops declaring ``speckit.foo.bar-baz``, but its
        prompt stays registered and on disk. ``speckit.foo-bar.baz`` would
        write the same file, and removing foo would then delete it, so the
        install is refused (#4797)."""
        import yaml

        def write_source(ext_id, name, body):
            source = tmp_path / f"src-{ext_id}"
            (source / "commands").mkdir(parents=True)
            (source / "commands" / "cmd.md").write_text(body, encoding="utf-8")
            (source / "extension.yml").write_text(yaml.safe_dump({
                "schema_version": "1.0",
                "extension": {
                    "id": ext_id,
                    "name": ext_id,
                    "version": "1.0.0",
                    "description": "Test",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "commands": [{"name": name, "file": "commands/cmd.md"}]
                },
            }), encoding="utf-8")
            return source

        project = _init_project(tmp_path, "kiro-cli")
        prompts = project / ".kiro" / "prompts"
        foo = write_source("foo", "speckit.foo.bar-baz", "FOO-BODY\n")
        result = _run_in_project(project, ["extension", "add", "--dev", str(foo)])
        assert result.exit_code == 0, result.output
        manifest_path = project / ".specify" / "extensions" / "foo" / "extension.yml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest["provides"]["commands"][0]["name"] = "speckit.foo.qux"
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

        bar = write_source("foo-bar", "speckit.foo-bar.baz", "BAR-BODY\n")
        result = _run_in_project(project, ["extension", "add", "--dev", str(bar)])
        assert result.exit_code != 0
        assert (
            "speckit.foo-bar.baz (writes 'speckit-foo-bar-baz', already provided "
            "by extension 'foo' as 'speckit.foo.bar-baz')"
        ) in " ".join(result.output.split())
        assert "FOO-BODY" in (prompts / "speckit-foo-bar-baz.md").read_text(
            encoding="utf-8"
        )

    def test_removal_keeps_a_kiro_prompt_another_extension_wrote_at_a_stale_name(
        self, tmp_path
    ):
        """foo's manifest no longer declares ``speckit.foo.bar-baz``, but the
        registry still does. When foo-bar's ``speckit.foo-bar.baz`` already
        wrote ``speckit-foo-bar-baz.md``, removing foo checks the file's owner
        and keeps it (#4797)."""
        import yaml

        from specify_cli.extensions import ExtensionManager

        project = _init_project(tmp_path, "kiro-cli")
        self._plant_extension(project, "foo", [
            {"name": "speckit.foo.bar-baz", "body": "FOO-BODY\n"},
        ])
        ExtensionManager(project).register_enabled_extensions_for_agent("kiro-cli")
        shared = project / ".kiro" / "prompts" / "speckit-foo-bar-baz.md"
        assert "FOO-BODY" in shared.read_text(encoding="utf-8")
        manifest_path = project / ".specify" / "extensions" / "foo" / "extension.yml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest["provides"]["commands"][0]["name"] = "speckit.foo.qux"
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
        self._plant_extension(project, "foo-bar", [
            {"name": "speckit.foo-bar.baz", "body": "BAR-BODY\n"},
        ])
        shared.write_bytes(b"<!-- Extension: foo-bar -->\nBAR-BODY\n")

        result = _run_in_project(project, ["extension", "remove", "foo", "--force"])
        assert result.exit_code == 0, result.output
        assert "Preserving the shared file" in result.output
        assert shared.read_bytes() == b"<!-- Extension: foo-bar -->\nBAR-BODY\n"

    def test_removal_ignores_another_extensions_marker_quoted_in_body(self, tmp_path):
        """The first generated marker owns a prompt even if its body quotes another (#4797)."""
        project = _init_project(tmp_path, "kiro-cli")
        self._plant_extension(project, "foo", [{
            "name": "speckit.foo.bar-baz",
            "body": "FOO-BODY\n\nExample header:\n<!-- Extension: foo-bar -->\n",
        }])
        result = _run_in_project(project, ["integration", "use", "kiro-cli"])
        assert result.exit_code == 0, result.output
        shared = project / ".kiro/prompts/speckit-foo-bar-baz.md"
        before = shared.read_bytes()
        assert b"<!-- Extension: foo -->" in before
        self._plant_extension(project, "foo-bar", [{
            "name": "speckit.foo-bar.baz", "body": "BAR-BODY\n",
        }])

        result = _run_in_project(project, ["extension", "remove", "foo-bar", "--force"])
        assert result.exit_code == 0, result.output
        assert shared.read_bytes() == before
        assert "Preserving the shared file" in result.output

    def test_qoder_upgrade_leaves_extensions_that_share_a_skill_unregistered(
        self, tmp_path
    ):
        """Qoder's flat commands become skills through the same retirement
        step (#4205), so the same pair would merge into one skill (#4797)."""
        project = _init_project(tmp_path, "qodercli")
        commands = project / ".qoder" / "commands"
        commands.mkdir(parents=True, exist_ok=True)
        foo_body = "---\ndescription: Foo\n---\n\n<!-- Extension: foo -->\nFOO-BODY\n"
        bar_body = "---\ndescription: Bar\n---\n\n<!-- Extension: foo-bar -->\nBAR-BODY\n"
        self._plant_extension(
            project,
            "foo",
            [{"name": "speckit.foo.bar-baz", "body": foo_body}],
            agent="qodercli",
        )
        self._plant_extension(
            project,
            "foo-bar",
            [{"name": "speckit.foo-bar.baz", "body": bar_body}],
            agent="qodercli",
        )
        (commands / "speckit.foo.bar-baz.md").write_bytes(foo_body.encode("utf-8"))
        (commands / "speckit.foo-bar.baz.md").write_bytes(bar_body.encode("utf-8"))

        result = _run_in_project(project, ["integration", "upgrade", "qodercli"])
        assert result.exit_code == 0, result.output
        assert (commands / "speckit.foo.bar-baz.md").read_bytes() == foo_body.encode(
            "utf-8"
        )
        assert (commands / "speckit.foo-bar.baz.md").read_bytes() == bar_body.encode(
            "utf-8"
        )
        skill = project / ".qoder" / "skills" / "speckit-foo-bar-baz" / "SKILL.md"
        assert not skill.parent.exists()

        # Removal deletes the skipped extension's old flat command too, and
        # the remaining extension then migrates.
        result = _run_in_project(
            project, ["extension", "remove", "foo-bar", "--force"]
        )
        assert result.exit_code == 0, result.output
        assert not (commands / "speckit.foo-bar.baz.md").exists()
        assert (commands / "speckit.foo.bar-baz.md").read_bytes() == foo_body.encode(
            "utf-8"
        )

        result = _run_in_project(project, ["integration", "upgrade", "qodercli"])
        assert result.exit_code == 0, result.output
        assert "FOO-BODY" in skill.read_text(encoding="utf-8")
        assert not (commands / "speckit.foo.bar-baz.md").exists()

    @pytest.mark.parametrize("marker", ["missing", "other-extension", "invalid-utf8", "owned"])
    def test_qoder_removal_requires_ownership_of_legacy_command(self, tmp_path, marker):
        """Removal may retire a Qoder flat command only with its owner's marker (#4797)."""
        project = _init_project(tmp_path, "qodercli")
        self._plant_extension(project, "foo", [{
            "name": "speckit.foo.run", "body": "FOO-BODY\n",
        }], agent="qodercli")
        result = _run_in_project(project, ["integration", "use", "qodercli"])
        assert result.exit_code == 0, result.output
        legacy = project / ".qoder/commands/speckit.foo.run.md"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        before = {
            "missing": b"User command\n",
            "other-extension": b"<!-- Extension: other -->\nOther owner's command\n",
            "invalid-utf8": b"\xff",
            "owned": b"---\ndescription: Foo\n---\n\n<!-- Extension: foo -->\nFOO-BODY\n",
        }[marker]
        legacy.write_bytes(before)

        result = _run_in_project(project, ["extension", "remove", "foo", "--force"])
        assert result.exit_code == 0, result.output
        assert not (project / ".qoder/skills/speckit-foo-run/SKILL.md").exists()
        if marker == "owned":
            assert not legacy.exists()
        else:
            assert legacy.read_bytes() == before
            assert "Preserving the legacy file" in result.output

    def test_upgrade_migrates_alias_that_hyphenates_to_its_own_command(
        self, tmp_path, monkeypatch
    ):
        import yaml

        project = _init_dotted_kiro_project(
            tmp_path, monkeypatch, ["extension", "add", "git"]
        )
        manifest_path = project / ".specify" / "extensions" / "git" / "extension.yml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        for command in manifest["provides"]["commands"]:
            if command["name"] == "speckit.git.commit":
                command["aliases"] = ["speckit-git-commit"]
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        prompts = project / ".kiro" / "prompts"
        assert (prompts / "speckit-git-commit.md").is_file()
        assert not (prompts / "speckit.git.commit.md").exists()

    def test_force_reinstall_replaces_dotted_prompts_written_before_hyphenation(
        self, tmp_path, monkeypatch
    ):
        """``extension add --force`` removes the extension first, which
        deletes its dotted prompts, then writes the hyphenated ones."""
        project = _init_dotted_kiro_project(
            tmp_path, monkeypatch, ["extension", "add", "git"]
        )
        prompts = project / ".kiro" / "prompts"
        assert (prompts / "speckit.git.commit.md").is_file()

        result = _run_in_project(project, ["extension", "add", "git", "--force"])
        assert result.exit_code == 0, result.output
        assert (prompts / "speckit-git-commit.md").is_file()
        assert not (prompts / "speckit.git.commit.md").exists()
        # Reinstall does not run integration setup, so the core prompt stays
        # dotted until upgrade.
        assert (prompts / "speckit.plan.md").is_file()
        assert not (prompts / "speckit-plan.md").exists()

    def test_preset_core_override_still_writes_kiro_prompt(self, tmp_path):
        preset_src = _write_command_preset(tmp_path, "cmd-preset")
        project = _init_project(tmp_path, "kiro-cli")
        result = _run_in_project(
            project, ["preset", "add", "--dev", str(preset_src)]
        )
        assert result.exit_code == 0, result.output
        plan = (project / ".kiro" / "prompts" / "speckit-plan.md").read_text(
            encoding="utf-8"
        )
        assert "Overridden plan content" in plan

    @pytest.mark.parametrize("activate", ["use", "switch"])
    def test_activating_kiro_after_secondary_upgrade_retires_dotted_prompts(
        self, tmp_path, monkeypatch, activate
    ):
        """Upgrading Kiro while another integration is active skips extension
        registration (#2948), so its dotted extension prompts survive, and the
        new manifest no longer shows a rename. ``use`` or ``switch`` registers
        the hyphenated prompts and then retires the dotted ones (#4797)."""
        project = _init_dotted_kiro_project(
            tmp_path,
            monkeypatch,
            ["extension", "add", "git"],
            ["integration", "install", "claude"],
            ["integration", "use", "claude"],
        )
        prompts = project / ".kiro" / "prompts"

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        assert (prompts / "speckit-plan.md").is_file()
        assert (prompts / "speckit.git.commit.md").is_file()

        result = _run_in_project(project, ["integration", activate, "kiro-cli"])
        assert result.exit_code == 0, result.output
        assert sorted(prompts.glob("speckit.*.md")) == []
        assert (prompts / "speckit-git-commit.md").is_file()

    def test_enabling_extension_after_kiro_rename_retires_its_dotted_prompts(
        self, tmp_path, monkeypatch
    ):
        """A disabled extension keeps its dotted prompts through the rename.
        Once it is enabled, the next registration pass replaces them, although
        that upgrade no longer sees a rename (#4797)."""
        project = _init_dotted_kiro_project(
            tmp_path,
            monkeypatch,
            ["extension", "add", "git"],
            ["extension", "disable", "git"],
        )
        prompts = project / ".kiro" / "prompts"

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        assert (prompts / "speckit.git.commit.md").is_file()

        for args in (
            ["extension", "enable", "git"],
            ["integration", "upgrade", "kiro-cli"],
        ):
            result = _run_in_project(project, args)
            assert result.exit_code == 0, result.output
        assert sorted(prompts.glob("speckit.*.md")) == []
        assert (prompts / "speckit-git-commit.md").is_file()

    def test_kiro_prompt_named_without_dots_is_not_retired(self, tmp_path):
        """Aliases are free-form, and one without dots is already its Kiro
        prompt name, so its old and new prompt are the same file."""
        import yaml

        project = _init_project(tmp_path, "kiro-cli")
        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, result.output
        manifest_path = project / ".specify" / "extensions" / "git" / "extension.yml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        for command in manifest["provides"]["commands"]:
            if command["name"] == "speckit.git.commit":
                command["aliases"] = ["speckit-git-c"]
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

        result = _run_in_project(project, ["integration", "upgrade", "kiro-cli"])
        assert result.exit_code == 0, result.output
        assert (project / ".kiro" / "prompts" / "speckit-git-c.md").is_file()

    @pytest.mark.parametrize(
        ("old_files", "new_files", "expected"),
        [
            (["speckit.plan.md", "speckit.tasks.md"],
             ["speckit-plan.md", "speckit-tasks.md"], True),
            (["speckit.plan.md", "speckit.old.md"],
             ["speckit.plan.md", "speckit.new.md"], False),
            (["speckit.plan.md"], ["speckit.plan.md", "speckit.new.md"], False),
            (["speckit-plan/SKILL.md", "speckit-old/SKILL.md"],
             ["speckit-plan/SKILL.md", "speckit-new/SKILL.md"], False),
        ],
    )
    def test_command_file_names_changed_needs_a_rename(
        self, old_files, new_files, expected
    ):
        """Commands added and dropped in the same release are not a rename,
        so upgrade must not refuse them while presets are installed."""
        from types import SimpleNamespace

        from specify_cli.integrations._command_upgrade_layout import (
            _command_file_names_changed,
        )

        integration = SimpleNamespace(registrar_config={"dir": ".kiro/prompts"})

        def files(names):
            return {f".kiro/prompts/{name}" for name in names}

        assert _command_file_names_changed(
            integration, files(old_files), files(new_files)
        ) is expected

    def test_upgrade_migrates_qodercli_extension_commands_to_skills(self, tmp_path):
        """Qoder upgrade retires old extension commands after skills exist."""
        project = _init_project(tmp_path, "qodercli")
        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        skills = project / ".qoder" / "skills"
        commands = project / ".qoder" / "commands"
        commands.mkdir(parents=True)

        manifest_path = (
            project / ".specify" / "integrations" / "qodercli.manifest.json"
        )
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        legacy_manifest_files = {}
        for path, info in manifest_data["files"].items():
            skill_path = project / path
            command_name = skill_path.parent.name.replace("speckit-", "speckit.", 1)
            legacy_path = commands / f"{command_name}.md"
            legacy_path.write_bytes(skill_path.read_bytes())
            legacy_manifest_files[
                legacy_path.relative_to(project).as_posix()
            ] = info
        manifest_data["files"] = legacy_manifest_files
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        registry_path = project / ".specify" / "extensions" / ".registry"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        git_metadata = registry["extensions"]["git"]
        registered_commands = git_metadata["registered_commands"]["qodercli"]
        for command_name in registered_commands:
            skill_name = command_name.replace("speckit.", "speckit-", 1).replace(
                ".", "-"
            )
            old_command = commands / f"{command_name}.md"
            old_command.write_bytes(
                (skills / skill_name / "SKILL.md").read_bytes()
            )
        missing_replacement = commands / "speckit.git.missing.md"
        missing_replacement.write_text("# preserve until replaced\n", encoding="utf-8")
        registered_commands.append("speckit.git.missing")
        git_metadata["registered_skills"] = []
        registry_path.write_text(json.dumps(registry), encoding="utf-8")

        shutil.rmtree(skills)
        result = _run_in_project(project, [
            "integration", "upgrade", "qodercli", "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, f"upgrade failed: {result.output}"

        for command_name in registered_commands[:-1]:
            skill_name = command_name.replace("speckit.", "speckit-", 1).replace(
                ".", "-"
            )
            assert (skills / skill_name / "SKILL.md").is_file()
            assert not (commands / f"{command_name}.md").exists()
        assert missing_replacement.is_file(), (
            "a legacy command must remain when no replacement skill was written"
        )

    def test_upgrade_kilocode_legacy_dir_rejects_installed_preset_overrides(
        self, tmp_path
    ):
        """Kilo legacy command-root migration must fail closed with presets."""
        project = _init_project(tmp_path, "kilocode")
        canonical, legacy = _move_kilocode_install_to_legacy_layout(project)

        preset_file = legacy / "speckit.plan.md"
        preset_file.write_text("# preset plan override\n", encoding="utf-8")

        presets_dir = project / ".specify" / "presets"
        presets_dir.mkdir(parents=True, exist_ok=True)
        (presets_dir / ".registry").write_text(
            json.dumps({
                "presets": {
                    "my-preset": {
                        "version": "1.0.0",
                        "enabled": True,
                        "registered_commands": {"kilocode": ["speckit.plan"]},
                        "registered_skills": [],
                    }
                }
            }),
            encoding="utf-8",
        )

        result = _run_in_project(project, [
            "integration", "upgrade", "kilocode",
            "--script", "sh",
            "--force",
        ])
        assert result.exit_code != 0, (
            "Kilo legacy command-root migration with presets must be rejected"
        )
        assert "preset" in result.output.lower()
        assert "my-preset" in result.output
        assert ".kilocode/workflows" in strip_ansi(result.output)
        assert ".kilo/commands" in strip_ansi(result.output)
        assert not canonical.exists(), (
            "canonical Kilo commands must not be scaffolded after rejection"
        )
        assert preset_file.read_text(encoding="utf-8") == "# preset plan override\n"

    def test_upgrade_reconciles_kilocode_legacy_extension_artifacts(self, tmp_path):
        """Kilo upgrade moves enabled extension commands to the canonical dir."""
        project = _init_project(tmp_path, "kilocode")
        canonical, legacy = _move_kilocode_install_to_legacy_layout(project)

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"
        assert sorted(legacy.glob("speckit.git.*.md")), (
            "legacy Kilo should render the git extension under .kilocode/workflows"
        )
        assert not canonical.exists()

        result = _run_in_project(project, [
            "integration", "upgrade", "kilocode",
            "--script", "sh",
            "--force",
        ])
        assert result.exit_code == 0, f"upgrade failed: {result.output}"

        assert sorted(canonical.glob("speckit.git.*.md")), (
            "enabled git extension commands should be recreated in .kilo/commands"
        )
        assert not sorted(legacy.glob("speckit.git.*.md")), (
            "legacy git extension commands should be removed after Kilo upgrade"
        )

        registry_path = project / ".specify" / "extensions" / ".registry"
        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]
        assert "kilocode" in registered

    def test_upgrade_preserves_disabled_kilocode_legacy_extension_and_user_file(
        self, tmp_path
    ):
        """Legacy reconciliation must not clean disabled or user-owned files."""
        project = _init_project(tmp_path, "kilocode")
        canonical, legacy = _move_kilocode_install_to_legacy_layout(project)

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"
        result = _run_in_project(project, ["extension", "disable", "git"])
        assert result.exit_code == 0, f"extension disable failed: {result.output}"

        disabled_extension_files = sorted(legacy.glob("speckit.git.*.md"))
        assert disabled_extension_files, "disabled extension artifact should remain pre-upgrade"

        user_file = legacy / "speckit.user-owned.md"
        user_file.write_text("# user-owned legacy command", encoding="utf-8")

        result = _run_in_project(project, [
            "integration", "upgrade", "kilocode",
            "--script", "sh",
            "--force",
        ])
        assert result.exit_code == 0, f"upgrade failed: {result.output}"

        assert canonical.is_dir(), ".kilo/commands/ should exist after upgrade"
        assert user_file.read_text(encoding="utf-8") == "# user-owned legacy command"
        for disabled_file in disabled_extension_files:
            assert disabled_file.exists(), (
                "disabled extension artifacts should be preserved during "
                "legacy command-root reconciliation"
            )
        assert not sorted(canonical.glob("speckit.git.*.md")), (
            "disabled extensions must not be re-registered in the canonical dir"
        )

    def test_upgrade_secondary_kilocode_legacy_dir_cleans_commands_without_backfill(
        self, tmp_path
    ):
        """Kilo cleanup stays agent-scoped without inactive extension backfill."""
        project = _init_project(tmp_path, "copilot", integration_options="--skills")
        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        skill = project / ".github" / "skills" / "speckit-git-feature" / "SKILL.md"
        assert skill.exists(), "precondition: active copilot has the git extension skill"

        registry_path = project / ".specify" / "extensions" / ".registry"

        def _git_skills():
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            return data["extensions"]["git"].get("registered_skills", [])

        assert _git_skills(), "precondition: git skills registered for active copilot"

        result = _run_in_project(project, [
            "integration", "install", "kilocode",
            "--script", "sh",
            "--force",
        ])
        assert result.exit_code == 0, result.output

        canonical, legacy = _move_kilocode_install_to_legacy_layout(project)
        legacy_git_command = legacy / "speckit.git.feature.md"
        legacy_git_command.write_text("# legacy Kilo git command\n", encoding="utf-8")
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["extensions"]["git"].setdefault("registered_commands", {})[
            "kilocode"
        ] = ["speckit.git.feature"]
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
        assert legacy_git_command.exists(), (
            "precondition: secondary Kilo has a legacy extension command file"
        )

        result = _run_in_project(project, [
            "integration", "upgrade", "kilocode",
            "--script", "sh",
            "--force",
        ])
        assert result.exit_code == 0, result.output

        assert canonical.is_dir(), ".kilo/commands/ should exist after upgrade"
        assert not sorted(canonical.glob("speckit.git.*.md")), (
            "inactive Kilo must wait for use/switch before extension rescaffolding"
        )
        assert not legacy_git_command.exists(), (
            "secondary Kilo legacy extension commands should still be cleaned up"
        )
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registered_commands = registry["extensions"]["git"].get(
            "registered_commands", {}
        )
        assert "kilocode" not in registered_commands
        assert skill.exists(), (
            "secondary Kilo legacy cleanup must not delete the active agent's "
            "extension skill"
        )
        assert _git_skills(), (
            "secondary Kilo legacy cleanup must not untrack the active agent's "
            "extension skills in the registry"
        )

    def test_upgrade_bob_skills_migration_preserves_manifest(self, tmp_path):
        """Regression (review #3415, 4724160183, comment 1).

        ``integration upgrade bob --integration-options="--skills"`` migrates a
        legacy Bob 1.x install (``.bob/commands/*.md``) to the skills layout
        (``.bob/skills/speckit-*/SKILL.md``) and stale-removes the old command
        files.  Because that stale-file pass shrinks the tracked set, the
        upgrade's Phase 2 must NOT delete the freshly-saved ``bob.manifest.json``
        — otherwise the migrated project is left untracked and un-upgradeable.
        """
        project = _init_project(
            tmp_path, "bob", integration_options="--legacy-commands"
        )

        commands = project / ".bob" / "commands"
        skills = project / ".bob" / "skills"
        manifest_path = (
            project / ".specify" / "integrations" / "bob.manifest.json"
        )
        assert commands.is_dir() and sorted(commands.glob("speckit.*.md"))
        assert not skills.exists()
        assert manifest_path.is_file()

        result = _run_in_project(project, [
            "integration", "upgrade", "bob",
            "--integration-options", "--skills",
            "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, f"migration upgrade failed: {result.output}"

        # Skills layout scaffolded; legacy core command files removed.
        assert skills.is_dir(), ".bob/skills/ must exist after --skills migration"
        assert sorted(skills.glob("speckit-*")), "expected migrated skill dirs"
        core_commands = [
            f for f in commands.glob("speckit.*.md")
            if "agent-context" not in f.name
        ] if commands.exists() else []
        assert core_commands == [], (
            f"legacy core command files should be removed, found: "
            f"{[f.name for f in core_commands]}"
        )

        # The manifest must survive so the project stays tracked/upgradeable.
        assert manifest_path.is_file(), (
            "bob.manifest.json must survive a layout-shrinking migration"
        )
        reupgrade = _run_in_project(project, [
            "integration", "upgrade", "bob", "--script", "sh", "--force",
        ])
        assert reupgrade.exit_code == 0, (
            f"migrated project must remain upgradeable: {reupgrade.output}"
        )

    def test_upgrade_bob_layout_change_reconciles_extension_artifacts(self, tmp_path):
        """Regression (review #3415, 4725829110).

        When a dual-mode agent (Bob) flips layout across an upgrade, the old
        layout's *extension* artifacts must be reconciled — not left orphaned.
        A legacy Bob install renders enabled extensions as ``.bob/commands/``
        command files; migrating to skills via ``--skills`` must remove those
        command files, recreate the extension as ``.bob/skills/`` skills, and
        update the extension registry accordingly (and vice-versa for the
        reverse ``--legacy-commands`` migration).
        """
        project = _init_project(
            tmp_path, "bob", integration_options="--legacy-commands"
        )

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        commands = project / ".bob" / "commands"
        skills = project / ".bob" / "skills"
        registry_path = project / ".specify" / "extensions" / ".registry"

        def _git_registry():
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            g = data["extensions"]["git"]
            return list(g.get("registered_commands", {})), g.get(
                "registered_skills", []
            )

        # Legacy precondition: git renders as command files under .bob/commands.
        assert sorted(commands.glob("speckit.git.*.md")), (
            "legacy Bob should render the git extension as command files"
        )
        assert not list(skills.glob("speckit-git-*")) if skills.exists() else True
        cmds_agents, skill_names = _git_registry()
        assert "bob" in cmds_agents and not skill_names

        # Migrate legacy -> skills.
        result = _run_in_project(project, [
            "integration", "upgrade", "bob",
            "--integration-options", "--skills",
            "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, f"--skills migration failed: {result.output}"

        # Old-layout git command files removed; skills recreated.
        assert not sorted(commands.glob("speckit.git.*.md")), (
            "git extension command files must be removed after --skills migration"
        )
        assert sorted(skills.glob("speckit-git-*")), (
            "git extension must be recreated as skills after --skills migration"
        )
        cmds_agents, skill_names = _git_registry()
        assert "bob" not in cmds_agents, (
            "extension registry must drop the stale bob command entry"
        )
        assert skill_names, "extension registry must record the migrated skills"

        # Migrate skills -> legacy: the reverse reconciliation must also hold.
        result = _run_in_project(project, [
            "integration", "upgrade", "bob",
            "--integration-options", "--legacy-commands",
            "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, (
            f"--legacy-commands migration failed: {result.output}"
        )
        assert not sorted(skills.glob("speckit-git-*")), (
            "git extension skills must be removed after --legacy-commands migration"
        )
        assert sorted(commands.glob("speckit.git.*.md")), (
            "git extension command files must be recreated in legacy layout"
        )
        cmds_agents, skill_names = _git_registry()
        assert "bob" in cmds_agents and not skill_names

    def test_upgrade_layout_change_preserves_extension_artifacts_when_reregistration_fails(
        self, tmp_path
    ):
        """Regression (review 3624075109).

        A layout-changing upgrade must not eagerly unregister the agent's
        extension artifacts before re-registration: the retirement of each
        opposite-mode artifact belongs to
        ``register_enabled_extensions_for_agent``'s deferred toggle cleanup,
        which retires an old artifact only after its replacement in the new
        layout is confirmed. If re-registration cannot rebuild an extension
        (here: its installed manifest is corrupted), the old artifact and its
        registry tracking must survive instead of leaving the extension with
        no artifacts at all.
        """
        project = _init_project(
            tmp_path, "bob", integration_options="--legacy-commands"
        )
        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        commands = project / ".bob" / "commands"
        assert sorted(commands.glob("speckit.git.*.md")), (
            "precondition: git extension renders as legacy command files"
        )

        # Corrupt the installed extension manifest so re-registration cannot
        # rebuild the artifacts in the new layout.
        (
            project / ".specify" / "extensions" / "git" / "extension.yml"
        ).write_text("invalid: [", encoding="utf-8")

        result = _run_in_project(project, [
            "integration", "upgrade", "bob",
            "--integration-options", "--skills",
            "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, (
            f"upgrade is best-effort about extensions: {result.output}"
        )

        assert sorted(commands.glob("speckit.git.*.md")), (
            "old-layout extension artifacts must survive when their "
            "replacement could not be registered"
        )
        registry_path = project / ".specify" / "extensions" / ".registry"
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        assert "bob" in data["extensions"]["git"].get("registered_commands", {}), (
            "extension registry must keep tracking the surviving artifacts"
        )

    def test_upgrade_active_layout_change_rejected_before_missing_preset_source_can_lose_override(
        self, tmp_path
    ):
        """Regression (review 3623357447).

        Layout-changing upgrades must fail closed even for the active
        integration. Preset rescaffolding is best-effort, so a missing source
        file could otherwise let stale integration cleanup delete the tracked
        old-layout override without creating its replacement.
        """
        project = _init_project(
            tmp_path, "bob", integration_options="--legacy-commands"
        )
        commands = project / ".bob" / "commands"
        skills = project / ".bob" / "skills"

        preset_src = tmp_path / "cmd-preset"
        (preset_src / "commands").mkdir(parents=True)
        (preset_src / "commands" / "speckit.plan.md").write_text(
            "---\ndescription: Overridden plan\n---\nOverridden plan content\n",
            encoding="utf-8",
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "cmd-preset",
                "name": "Command Preset",
                "version": "1.0.0",
                "description": "Test preset with a command override",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.plan",
                        "file": "commands/speckit.plan.md",
                    }
                ]
            },
        }
        import yaml

        (preset_src / "preset.yml").write_text(
            yaml.dump(manifest_data), encoding="utf-8"
        )
        result = _run_in_project(project, ["preset", "add", "--dev", str(preset_src)])
        assert result.exit_code == 0, f"preset add failed: {result.output}"

        cmd_file = commands / "speckit.plan.md"
        assert "Overridden plan content" in cmd_file.read_text(encoding="utf-8")

        installed_source = (
            project
            / ".specify"
            / "presets"
            / "cmd-preset"
            / "commands"
            / "speckit.plan.md"
        )
        assert installed_source.exists(), "precondition: preset source was installed"
        installed_source.unlink()

        result = _run_in_project(project, [
            "integration", "upgrade", "bob",
            "--integration-options", "--skills",
            "--script", "sh", "--force",
        ])
        assert result.exit_code != 0, (
            "layout change with tracked preset artifacts must be rejected"
        )
        assert "cmd-preset" in result.output
        assert not skills.exists(), "no skills layout must be scaffolded on rejection"
        assert "Overridden plan content" in cmd_file.read_text(encoding="utf-8"), (
            "tracked old-layout override must remain untouched"
        )

    def test_upgrade_active_layout_change_rejected_with_disabled_preset(
        self, tmp_path
    ):
        """Regression (review 3623779277).

        The post-upgrade rescaffold iterates *enabled* presets only, and a
        disabled preset's artifacts are deliberately frozen until removal
        (``preset disable``). An active-agent layout change must therefore be
        rejected while a disabled preset still owns artifacts for the agent —
        proceeding would delete its old-layout files in stale-manifest
        cleanup, skip recreating them, and leave its registry entries stale.
        Re-enabling does not make a non-transactional layout migration safe.
        """
        project = _init_project(
            tmp_path, "bob", integration_options="--legacy-commands"
        )
        commands = project / ".bob" / "commands"
        skills = project / ".bob" / "skills"

        preset_src = tmp_path / "cmd-preset"
        (preset_src / "commands").mkdir(parents=True)
        (preset_src / "commands" / "speckit.plan.md").write_text(
            "---\ndescription: Overridden plan\n---\nOverridden plan content\n",
            encoding="utf-8",
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "cmd-preset",
                "name": "Command Preset",
                "version": "1.0.0",
                "description": "Test preset with a command override",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.plan",
                        "file": "commands/speckit.plan.md",
                    }
                ]
            },
        }
        import yaml

        (preset_src / "preset.yml").write_text(
            yaml.dump(manifest_data), encoding="utf-8"
        )
        result = _run_in_project(project, ["preset", "add", "--dev", str(preset_src)])
        assert result.exit_code == 0, f"preset add failed: {result.output}"
        result = _run_in_project(project, ["preset", "disable", "cmd-preset"])
        assert result.exit_code == 0, f"preset disable failed: {result.output}"

        cmd_file = commands / "speckit.plan.md"
        assert "Overridden plan content" in cmd_file.read_text(encoding="utf-8")

        result = _run_in_project(project, [
            "integration", "upgrade", "bob",
            "--integration-options", "--skills",
            "--script", "sh", "--force",
        ])
        assert result.exit_code != 0, (
            "layout change with a disabled preset must be rejected"
        )
        assert "cmd-preset" in result.output
        assert not skills.exists(), "no skills layout must be scaffolded on rejection"
        assert "Overridden plan content" in cmd_file.read_text(encoding="utf-8"), (
            "the disabled preset's command file must be left untouched"
        )

        # Enabled presets are also rejected: rescaffolding can still fail.
        result = _run_in_project(project, ["preset", "enable", "cmd-preset"])
        assert result.exit_code == 0, f"preset enable failed: {result.output}"
        result = _run_in_project(project, [
            "integration", "upgrade", "bob",
            "--integration-options", "--skills",
            "--script", "sh", "--force",
        ])
        assert result.exit_code != 0
        assert "cmd-preset" in result.output
        assert not skills.exists()
        assert "Overridden plan content" in cmd_file.read_text(encoding="utf-8")

    def test_upgrade_secondary_layout_change_rejected_with_presets_installed(
        self, tmp_path
    ):
        """Regression (review #3415, 4726193915; updated for review 3623357447).

        Preset rescaffolding is active-agent-only, so a layout-changing
        ``upgrade`` of a *non-active* integration still cannot reconcile that
        agent's preset artifacts. It must reject the migration with an
        actionable error *before any mutation* when preset overrides are
        installed for that agent. A same-layout upgrade must still succeed.
        """
        project = _init_project(tmp_path, "copilot")
        result = _run_in_project(project, [
            "integration", "install", "bob",
            "--integration-options", "--legacy-commands",
            "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, result.output
        commands = project / ".bob" / "commands"
        skills = project / ".bob" / "skills"
        assert sorted(commands.glob("speckit.*.md"))

        # Simulate a historical preset registration for the non-active bob.
        presets_dir = project / ".specify" / "presets"
        presets_dir.mkdir(parents=True, exist_ok=True)
        (presets_dir / ".registry").write_text(
            json.dumps({
                "presets": {
                    "my-preset": {
                        "version": "1.0.0",
                        "enabled": True,
                        "registered_commands": {"bob": ["speckit.plan"]},
                        "registered_skills": {},
                    }
                }
            }),
            encoding="utf-8",
        )

        # Layout-changing upgrade of the secondary agent is rejected untouched.
        result = _run_in_project(project, [
            "integration", "upgrade", "bob",
            "--integration-options", "--skills",
            "--script", "sh", "--force",
        ])
        assert result.exit_code != 0, (
            "secondary layout change with presets must be rejected"
        )
        assert "preset" in result.output.lower()
        assert "my-preset" in result.output
        assert not skills.exists(), "no skills layout must be scaffolded on rejection"
        assert sorted(commands.glob("speckit.*.md")), (
            "legacy command files must be left untouched on rejection"
        )

        # A same-layout upgrade (no flag) must still succeed with presets present.
        result = _run_in_project(project, [
            "integration", "upgrade", "bob", "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, (
            f"same-layout upgrade must not be blocked by presets: {result.output}"
        )

    def test_upgrade_bob_layout_change_rejected_when_preset_registry_unreadable(
        self, tmp_path
    ):
        """Regression (review #3415, 4744636079).

        The preset guard must fail *closed*: if the preset registry exists but
        cannot be read/parsed (corruption, permissions), the layout-changing
        upgrade must be rejected before any mutation rather than proceeding on
        a false "no presets installed" assumption (which would let ``--force``
        delete preset-overridden command files while their registry state is
        unknown). A genuinely absent registry must still be allowed.
        """
        project = _init_project(
            tmp_path, "bob", integration_options="--legacy-commands"
        )
        commands = project / ".bob" / "commands"
        skills = project / ".bob" / "skills"
        assert sorted(commands.glob("speckit.*.md"))

        # Corrupted (unparseable) registry: exists but cannot be read as JSON.
        presets_dir = project / ".specify" / "presets"
        presets_dir.mkdir(parents=True, exist_ok=True)
        (presets_dir / ".registry").write_text("{ not valid json", encoding="utf-8")

        result = _run_in_project(project, [
            "integration", "upgrade", "bob",
            "--integration-options", "--skills",
            "--script", "sh", "--force",
        ])
        assert result.exit_code != 0, (
            "layout change must be rejected when preset registry is unreadable"
        )
        assert "preset registry" in result.output.lower()
        assert not skills.exists(), "no skills layout may be scaffolded on rejection"
        assert sorted(commands.glob("speckit.*.md")), (
            "legacy command files must be untouched when failing closed"
        )

        # A valid, empty registry must NOT block the migration.
        (presets_dir / ".registry").write_text(
            json.dumps({"presets": {}}), encoding="utf-8"
        )
        result = _run_in_project(project, [
            "integration", "upgrade", "bob",
            "--integration-options", "--skills",
            "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, (
            f"valid empty preset registry must not block migration: {result.output}"
        )
        assert skills.exists(), "skills layout should be scaffolded once unblocked"

    def test_upgrade_secondary_bob_layout_change_preserves_active_agent_skills(
        self, tmp_path
    ):
        """Regression (review #3415, 4726347306).

        ``integration upgrade`` supports upgrading a *secondary* (non-active)
        integration. The layout-change extension reconciliation must NOT run
        for a secondary agent: ``unregister_agent_artifacts`` treats the
        unscoped per-extension ``registered_skills`` as belonging to the passed
        agent and, if that agent's skills dir is absent, scans every agent's
        skills dir — which could delete/untrack the *active* agent's extension
        skills. The following re-registration cannot repair that because
        extension skill rendering is active-agent-scoped (#2948).
        """
        # Active agent: copilot in skills mode → git extension renders as skills.
        project = _init_project(tmp_path, "copilot", integration_options="--skills")
        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        skill = project / ".github" / "skills" / "speckit-git-feature" / "SKILL.md"
        assert skill.exists(), "precondition: active copilot has the git extension skill"

        registry_path = project / ".specify" / "extensions" / ".registry"

        def _git_skills():
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            return data["extensions"]["git"].get("registered_skills", [])

        assert _git_skills(), "precondition: git skills registered for active copilot"

        # Add a secondary (non-active) Bob in the legacy commands layout.
        result = _run_in_project(project, [
            "integration", "install", "bob",
            "--integration-options", "--legacy-commands",
            "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, result.output

        # Flip the *secondary* Bob's layout to skills. copilot stays active.
        result = _run_in_project(project, [
            "integration", "upgrade", "bob",
            "--integration-options", "--skills",
            "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, result.output

        # The active agent's extension skill must be untouched on disk and in
        # the registry — the secondary layout change must not reconcile it.
        assert skill.exists(), (
            "secondary Bob layout change must not delete the active agent's "
            "extension skill"
        )
        assert _git_skills(), (
            "secondary Bob layout change must not untrack the active agent's "
            "extension skills in the registry"
        )

    def test_upgrade_preserves_existing_vscode_settings(self, tmp_path):
        """Regression: copilot upgrade must not stale-delete .vscode/settings.json.

        On init the file is created and recorded in the manifest. On upgrade,
        setup() merges into the now-existing file and intentionally stops
        tracking it, so without ``stale_cleanup_exclusions()`` the Phase 2
        stale cleanup would delete it (destroying the user's settings).
        """
        project = _init_project(
            tmp_path, "copilot", integration_options="--commands"
        )
        settings = project / ".vscode" / "settings.json"
        assert settings.is_file(), "init should create .vscode/settings.json"
        before = json.loads(settings.read_text(encoding="utf-8"))
        assert before, "settings.json should contain managed defaults"

        # Simulate a user editing their settings: add a custom key that the
        # integration does not manage.  It must survive the upgrade.
        before["editor.fontSize"] = 17
        settings.write_text(json.dumps(before), encoding="utf-8")

        result = _run_in_project(project, [
            "integration", "upgrade", "copilot",
            "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, result.output

        assert settings.is_file(), ".vscode/settings.json must survive upgrade"
        after = json.loads(settings.read_text(encoding="utf-8"))
        assert after.get("editor.fontSize") == 17, (
            "user-defined settings must be preserved after upgrade"
        )

    def test_upgrade_restores_executable_bit_on_shared_scripts(self, tmp_path):
        """Regression: scripts refreshed by the managed-refresh step stay +x."""
        if os.name == "nt":
            pytest.skip("POSIX execute bits are not meaningful on Windows")
        project = _init_project(tmp_path, "copilot")
        script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        assert script.is_file()
        # Simulate a perms-losing install (e.g. wheel extraction dropping +x).
        script.chmod(0o644)
        assert not (script.stat().st_mode & 0o111)

        result = _run_in_project(project, [
            "integration", "upgrade", "copilot",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        assert script.stat().st_mode & 0o111, (
            "shared .sh scripts must be executable after upgrade"
        )

    def test_upgrade_does_not_backfill_non_active_integration(self, tmp_path):
        """Upgrading a non-active integration must not register extensions for it.

        Maintainer-requested behavior for #2948 (reverses the #2886 upgrade
        back-fill): non-active integrations only receive extension artifacts
        when selected via ``integration use`` / ``switch``. Upgrade of a
        non-active integration refreshes its own files and nothing else.
        """
        project = _init_project(tmp_path, "claude")

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        result = _run_in_project(project, [
            "integration", "install", "codex",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        registry_path = project / ".specify" / "extensions" / ".registry"
        assert "codex" not in json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]

        result = _run_in_project(project, [
            "integration", "upgrade", "codex",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]
        assert "codex" not in registered, (
            "upgrade must not back-fill non-active integrations (#2948)"
        )
        assert not (
            project / ".agents" / "skills" / "speckit-git-feature" / "SKILL.md"
        ).exists()

    def test_upgrade_active_integration_reregisters_extensions(self, tmp_path):
        """Upgrading the active integration restores its extension commands.

        The active integration keeps the re-registration pass on upgrade so
        missing or stale extension command files are recreated (#2948 scopes
        the pass to the active integration; #2886 introduced it).
        """
        project = _init_project(tmp_path, "claude")

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        cmd_file = project / ".claude" / "skills" / "speckit-git-feature" / "SKILL.md"
        assert cmd_file.exists(), "precondition: extension command registered"
        cmd_file.unlink()

        result = _run_in_project(project, [
            "integration", "upgrade", "claude",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        assert cmd_file.exists(), (
            "upgrade of the active integration re-registers extension commands"
        )

    def test_upgrade_copilot_skills_restores_extension_skill_over_regenerated_dir(
        self, tmp_path
    ):
        """End-to-end regression for #3849 (upgrade-overwrites-copilot-skills).

        In Copilot skills mode, ``integration upgrade`` runs ``setup()`` — which
        regenerates the core-template skill directories — *before* re-registering
        installed extensions. The extension re-registration then hits the
        ``skill_dir_preexists`` guard in ``_register_extension_skills`` (the skill
        sub-directory exists, courtesy of ``setup()``, but its ``SKILL.md`` has
        not been rewritten with extension content), so pre-fix the extension
        skill was silently left missing — its command content lost even though the
        extension remained installed and registered.

        The fix threads ``force=True`` from ``integration_upgrade()`` down to
        ``_register_extension_skills`` so the guard is bypassed and the extension
        content is re-composed on top of the just-regenerated directory. This test
        exercises the full ``specify integration upgrade`` command path and fails
        without the fix (the skill is never recreated).
        """
        project = _init_project(
            tmp_path, "copilot", integration_options="--skills"
        )

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        skill_dir = project / ".github" / "skills" / "speckit-git-feature"
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), (
            "precondition: git extension renders as a Copilot skill"
        )
        original = skill_file.read_text(encoding="utf-8")
        assert "source: extension:git" in original, (
            "precondition: skill carries the git extension ownership marker"
        )

        # Simulate the exact pre-condition the bug depends on: the skill file is
        # gone but its directory survives (as it does once setup() regenerates the
        # core-template layout during upgrade), triggering the skill_dir_preexists
        # skip guard on re-registration.
        skill_file.unlink()
        assert skill_dir.exists() and not skill_file.exists()

        result = _run_in_project(project, [
            "integration", "upgrade", "copilot",
            "--integration-options", "--skills",
            "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, result.output

        assert skill_file.exists(), (
            "upgrade must restore the extension skill even when its directory "
            "already exists (regression #3849)"
        )
        restored = skill_file.read_text(encoding="utf-8")
        assert "source: extension:git" in restored, (
            "restored skill must contain the git extension content, not a bare "
            "core-template stub"
        )
        assert "# Git Feature Skill" in restored

    def test_upgrade_active_integration_reregisters_presets(self, tmp_path):
        """Upgrading the active integration restores missing preset artifacts."""
        import yaml

        project = _init_project(tmp_path, "claude")
        preset_src = tmp_path / "upgrade-preset"
        (preset_src / "commands").mkdir(parents=True)
        (preset_src / "commands" / "speckit.upgrade-check.md").write_text(
            "---\ndescription: Upgrade check\n---\nPreset upgrade body\n",
            encoding="utf-8",
        )
        manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "upgrade-preset",
                "name": "Upgrade Preset",
                "version": "1.0.0",
                "description": "Upgrade preset test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.upgrade-check",
                        "file": "commands/speckit.upgrade-check.md",
                    }
                ]
            },
        }
        (preset_src / "preset.yml").write_text(
            yaml.dump(manifest), encoding="utf-8"
        )

        result = _run_in_project(
            project, ["preset", "add", "--dev", str(preset_src)]
        )
        assert result.exit_code == 0, result.output

        skill_dir = (
            project / ".claude" / "skills" / "speckit-upgrade-check"
        )
        skill_file = skill_dir / "SKILL.md"
        assert "Preset upgrade body" in skill_file.read_text(encoding="utf-8")
        shutil.rmtree(skill_dir)

        result = _run_in_project(project, [
            "integration", "upgrade", "claude",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output
        assert "Preset upgrade body" in skill_file.read_text(encoding="utf-8")

    def test_upgrade_force_syncs_manifest_hash_for_preset_overridden_skill(
        self, tmp_path
    ):
        """Regression for #4696.

        A preset overriding a core command that renders as a skill
        (e.g. ``speckit.tasks`` for ``codex``/``claude``) is rewritten by
        ``_register_presets_for_agent`` *after* ``new_manifest.save()`` during
        ``integration upgrade --force``. Without a post-registration resync,
        the manifest keeps the base template's hash for that skill file, so
        ``integration status`` immediately reports it as modified and a
        subsequent ``upgrade`` (without ``--force``) is blocked.
        """
        import yaml

        project = _init_project(tmp_path, "claude")

        preset_src = tmp_path / "tasks-preset"
        (preset_src / "commands").mkdir(parents=True)
        (preset_src / "commands" / "speckit.tasks.md").write_text(
            "---\ndescription: Tasks override\n---\nPreset tasks body\n",
            encoding="utf-8",
        )
        manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "tasks-preset",
                "name": "Tasks Preset",
                "version": "1.0.0",
                "description": "Preset overriding speckit.tasks",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.tasks",
                        "file": "commands/speckit.tasks.md",
                    }
                ]
            },
        }
        (preset_src / "preset.yml").write_text(
            yaml.dump(manifest), encoding="utf-8"
        )

        result = _run_in_project(project, ["preset", "add", "--dev", str(preset_src)])
        assert result.exit_code == 0, result.output

        skill_rel = ".claude/skills/speckit-tasks/SKILL.md"
        skill_file = project / skill_rel
        assert "Preset tasks body" in skill_file.read_text(encoding="utf-8")

        result = _run_in_project(project, [
            "integration", "upgrade", "claude",
            "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, result.output

        manifest_path = project / ".specify" / "integrations" / "claude.manifest.json"
        recorded_hash = json.loads(manifest_path.read_text(encoding="utf-8"))["files"][skill_rel]
        actual_hash = hashlib.sha256(skill_file.read_bytes()).hexdigest()
        assert recorded_hash == actual_hash, (
            "manifest hash for the preset-overridden skill must match the "
            "file `_register_presets_for_agent` just wrote"
        )

        status_result = _run_in_project(project, ["integration", "status"])
        assert "Integration status: OK" in status_result.output, status_result.output
        assert "Modified managed files: 0" in status_result.output
        assert "managed-files-modified" not in status_result.output

    def test_resync_manifest_warns_on_per_file_failure_and_keeps_going(
        self, tmp_path, capsys
    ):
        """A single file's rehash failure must warn, not vanish silently.

        ``_resync_manifest_after_registration`` best-effort-skips files it
        can't rehash, but a skip that produces no warning leaves the user
        with a stale hash and no signal that the manifest wasn't fully
        synchronized. Rehashing must also continue for the remaining files.
        """
        from specify_cli.integrations._helpers import (
            _resync_manifest_after_registration,
        )
        from specify_cli.integrations.manifest import IntegrationManifest

        project = tmp_path / "proj"
        project.mkdir()
        (project / "ok.md").write_text("ok content\n", encoding="utf-8")
        (project / "bad.md").write_text("bad content\n", encoding="utf-8")

        manifest = IntegrationManifest("claude", project, version="test")
        manifest.record_existing("ok.md")
        manifest.record_existing("bad.md")
        stale_hash = manifest._files["bad.md"]
        manifest.save()

        # Both files' bytes changed on disk after the manifest was saved
        # (simulating registration overwriting them), but only "bad.md"
        # fails to rehash.
        (project / "ok.md").write_text("ok content v2\n", encoding="utf-8")
        (project / "bad.md").write_text("bad content v2\n", encoding="utf-8")

        real_record_existing = IntegrationManifest.record_existing

        def fake_record_existing(self, rel_path, **kwargs):
            if str(rel_path) == "bad.md":
                raise OSError("permission denied")
            return real_record_existing(self, rel_path, **kwargs)

        import unittest.mock as mock

        with mock.patch.object(
            IntegrationManifest, "record_existing", fake_record_existing
        ):
            _resync_manifest_after_registration(
                manifest, "claude", continuing="Continuing."
            )

        captured = strip_ansi(capsys.readouterr().out)
        assert "Warning:" in captured
        assert "bad.md" in captured

        reloaded = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
        ok_hash = hashlib.sha256(
            (project / "ok.md").read_bytes()
        ).hexdigest()
        assert reloaded["files"]["ok.md"] == ok_hash
        assert reloaded["files"]["bad.md"] == stale_hash

    def test_resync_manifest_probe_error_does_not_abort_remaining_files(
        self, tmp_path, capsys
    ):
        """An ``OSError`` from the pre-rehash filesystem probes must warn
        and continue, not abort the whole resync loop.

        ``is_symlink()``/``is_file()`` run before the per-file ``try`` that
        wraps ``record_existing()``. If one of those probes raises (e.g. an
        inaccessible path), it must not jump past the remaining files in
        ``new_manifest.files`` and leave their hashes stale.
        """
        from specify_cli.integrations._helpers import (
            _resync_manifest_after_registration,
        )
        from specify_cli.integrations.manifest import IntegrationManifest

        project = tmp_path / "proj"
        project.mkdir()
        (project / "bad.md").write_text("bad content\n", encoding="utf-8")
        (project / "ok.md").write_text("ok content\n", encoding="utf-8")

        manifest = IntegrationManifest("claude", project, version="test")
        manifest.record_existing("bad.md")
        manifest.record_existing("ok.md")
        manifest.save()

        # Both files' bytes changed on disk after the manifest was saved
        # (simulating registration overwriting them), but "bad.md" fails
        # during the pre-rehash filesystem probe, not during rehashing.
        (project / "bad.md").write_text("bad content v2\n", encoding="utf-8")
        (project / "ok.md").write_text("ok content v2\n", encoding="utf-8")

        real_is_file = Path.is_file

        def fake_is_file(self):
            if self.name == "bad.md":
                raise OSError("permission denied")
            return real_is_file(self)

        import unittest.mock as mock

        with mock.patch.object(Path, "is_file", fake_is_file):
            _resync_manifest_after_registration(
                manifest, "claude", continuing="Continuing."
            )

        captured = strip_ansi(capsys.readouterr().out)
        assert "Warning:" in captured
        assert "bad.md" in captured

        reloaded = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
        ok_hash = hashlib.sha256((project / "ok.md").read_bytes()).hexdigest()
        assert reloaded["files"]["ok.md"] == ok_hash, (
            "a probe error on an earlier file must not abort rehashing of "
            "the remaining tracked files"
        )

    def test_upgrade_non_active_agent_preserves_active_agent_skills(self, tmp_path):
        """Upgrading a non-active agent must not touch the active agent's skills.

        Regression for the #2886 wiring: extension skill rendering is
        active-agent-scoped, so routing upgrade of a *secondary* agent through
        ``register_enabled_extensions_for_agent`` used to re-render the
        *active* skills-mode agent's extension skills as a side effect —
        resurrecting skill files the user had deliberately deleted. The skills
        pass is now gated on the target being the active agent. (Skills parity
        for non-active agents is tracked separately in #2948.)
        """
        # Active agent: copilot in skills mode → git extension renders as skills.
        project = _init_project(tmp_path, "copilot", integration_options="--skills")
        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        skill = project / ".github" / "skills" / "speckit-git-feature" / "SKILL.md"
        assert skill.exists(), "precondition: active copilot has the git extension skill"

        # Add a secondary (non-active) agent; copilot is not multi_install_safe.
        result = _run_in_project(project, [
            "integration", "install", "codex", "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, result.output

        # The user deliberately removes the active agent's git skill.
        shutil.rmtree(skill.parent)
        assert not skill.exists()

        # Upgrading the *non-active* agent must not re-render copilot's skills.
        result = _run_in_project(project, [
            "integration", "upgrade", "codex", "--script", "sh",
        ])
        assert result.exit_code == 0, result.output
        assert not skill.exists(), (
            "upgrading a non-active agent must not resurrect the active agent's "
            "deleted extension skill (#2886)"
        )



class TestIntegrationUpgradeDiagnostics(IntegrationCatalogCliTestBase):
    def test_integration_upgrade_failure_reports_phase_and_target(
        self, tmp_path, monkeypatch
    ):
        from specify_cli.integrations import INTEGRATION_REGISTRY
        from specify_cli.integrations.copilot import CopilotIntegration

        class UpgradeBrokenIntegration(CopilotIntegration):
            key = "upgrade-broken"
            config = dict(CopilotIntegration.config)
            config["name"] = "Upgrade Broken"

            def setup(self, project_root, manifest, **kwargs):
                raise OSError("upgrade exploded\nwith context")

        project = self._make_project(tmp_path)
        monkeypatch.setitem(
            INTEGRATION_REGISTRY, "upgrade-broken", UpgradeBrokenIntegration()
        )

        (project / ".specify" / "integrations").mkdir(parents=True, exist_ok=True)
        (project / ".specify" / "integration.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "integration": "upgrade-broken",
                    "integrations": ["upgrade-broken"],
                    "integration_settings": {"upgrade-broken": {"script": "sh"}},
                }
            ),
            encoding="utf-8",
        )
        (
            project / ".specify" / "integrations" / "upgrade-broken.manifest.json"
        ).write_text(
            json.dumps(
                {
                    "integration": "upgrade-broken",
                    "version": "0.0.0",
                    "installed_at": "2026-05-16T00:00:00+00:00",
                    "files": {},
                }
            ),
            encoding="utf-8",
        )

        result = self._invoke(["integration", "upgrade", "upgrade-broken"], project)
        normalized = _normalize_cli_output(result.output)

        assert result.exit_code == 1, result.output
        assert "Failed to upgrade integration 'upgrade-broken'" in normalized
        assert "upgrade exploded with context" in normalized
        assert "previous integration files may still be in place" in normalized


class TestIntegrationUpgradeBasic:
    """Test ``specify integration upgrade``."""

    def _init_project(self, tmp_path, integration="copilot"):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = tmp_path / "proj"
        project.mkdir()
        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "init", "--here",
                "--integration", integration,
                "--script", "sh",
                "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old)
        assert result.exit_code == 0, result.output
        return project

    def test_upgrade_requires_speckit_project(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["integration", "upgrade"])
        finally:
            os.chdir(old)
        assert result.exit_code != 0
        assert "Not a Spec Kit project" in result.output

    def test_upgrade_no_integration_installed(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade"])
        finally:
            os.chdir(old)
        assert result.exit_code == 0
        assert "No integration is currently installed" in result.output

    def test_upgrade_succeeds(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = self._init_project(tmp_path, "copilot")

        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade"], catch_exceptions=False)
        finally:
            os.chdir(old)
        assert result.exit_code == 0
        assert "upgraded successfully" in result.output

    def test_upgrade_blocks_on_modified_files(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = self._init_project(tmp_path, "copilot")

        # Modify a tracked file so the manifest hash won't match
        manifest_path = project / ".specify" / "integrations" / "copilot.manifest.json"
        assert manifest_path.exists(), "Manifest should exist after init"
        manifest_data = json.loads(manifest_path.read_text())
        tracked_files = manifest_data.get("files", {})
        assert tracked_files, "Manifest should track at least one file"
        first_rel = next(iter(tracked_files))
        target_file = project / first_rel
        assert target_file.exists(), f"Tracked file {first_rel} should exist"
        target_file.write_text("MODIFIED CONTENT\n")

        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade"])
        finally:
            os.chdir(old)
        assert result.exit_code != 0
        assert "modified" in result.output.lower()

    def test_upgrade_force_overwrites_modified(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = self._init_project(tmp_path, "copilot")

        # Modify a tracked file
        manifest_path = project / ".specify" / "integrations" / "copilot.manifest.json"
        manifest_data = json.loads(manifest_path.read_text())
        tracked_files = manifest_data.get("files", {})
        assert tracked_files, "Manifest should track at least one file"
        first_rel = next(iter(tracked_files))
        target_file = project / first_rel
        assert target_file.exists(), f"Tracked file {first_rel} should exist"
        target_file.write_text("MODIFIED CONTENT\n")

        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade", "--force"], catch_exceptions=False)
        finally:
            os.chdir(old)
        assert result.exit_code == 0
        assert "upgraded successfully" in result.output

    def test_upgrade_wrong_integration_key(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = self._init_project(tmp_path, "copilot")

        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade", "claude"])
        finally:
            os.chdir(old)
        assert result.exit_code != 0
        assert "not installed" in result.output

    def test_upgrade_no_manifest(self, tmp_path):
        """Upgrade with missing manifest suggests fresh install."""
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = self._init_project(tmp_path, "copilot")

        # Remove manifest
        manifest_path = project / ".specify" / "integrations" / "copilot.manifest.json"
        if manifest_path.exists():
            manifest_path.unlink()

        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade"])
        finally:
            os.chdir(old)
        assert result.exit_code == 0
        assert "Nothing to upgrade" in result.output
