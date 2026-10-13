"""Tests for mirrored integration CLI behavior in test_command_switch.py."""

from __future__ import annotations

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

class TestIntegrationSwitch:
    def test_switch_requires_speckit_project(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["integration", "switch", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Not a Spec Kit project" in result.output

    def test_switch_unknown_target(self, tmp_path):
        project = _init_project(tmp_path)
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "switch", "nonexistent"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Unknown integration" in result.output

    def test_switch_invalid_current_manifest_reports_cli_error(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        _write_invalid_manifest(project, "claude")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "codex",
                "--script", "sh",
            ])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Could not read integration manifest" in result.output

    def test_switch_same_noop(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "switch", "copilot"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "already the default integration" in result.output

    def test_switch_same_force_refreshes_shared_templates(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        template = project / ".specify" / "templates" / "plan-template.md"
        script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        template.write_text("# custom shared template\n", encoding="utf-8")
        script.write_text("# custom shared script\n", encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "claude",
                "--force",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        assert "shared infrastructure refreshed" in result.output
        assert "managed shared infrastructure refreshed" not in result.output
        assert "/speckit-plan" in template.read_text(encoding="utf-8")
        assert "/speckit-plan" in script.read_text(encoding="utf-8")

    def test_switch_installed_target_rejects_integration_options(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, [
                "integration", "switch", "codex",
                "--integration-options", "--bogus",
            ])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "--integration-options cannot be used" in result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["default_integration"] == "claude"

    def test_switch_between_integrations(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        # Verify claude files exist (claude uses skills)
        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()
        shared_script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        assert "/speckit-specify" in shared_script.read_text(encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        assert "Switched to" in result.output

        # Old claude files removed
        assert not (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()

        # New default Copilot skills created
        assert (
            project / ".github" / "skills" / "speckit-plan" / "SKILL.md"
        ).exists()
        assert "/speckit-specify" in shared_script.read_text(encoding="utf-8")
        assert "/speckit.specify" not in shared_script.read_text(encoding="utf-8")

        # integration.json updated
        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "copilot"

    def test_switch_rejects_conflicting_copilot_modes_before_uninstall(
        self, tmp_path
    ):
        project = _init_project(tmp_path, "claude")
        claude_skill = (
            project / ".claude" / "skills" / "speckit-plan" / "SKILL.md"
        )
        before_state = json.loads(
            (project / ".specify" / "integration.json").read_text(
                encoding="utf-8"
            )
        )

        result = _run_in_project(
            project,
            [
                "integration",
                "switch",
                "copilot",
                "--integration-options",
                "--skills --commands",
                "--script",
                "sh",
            ],
        )

        assert result.exit_code == 1
        assert "--skills and --commands are mutually exclusive" in result.output
        assert claude_skill.exists()
        assert not (project / ".github" / "skills").exists()
        assert not (project / ".github" / "agents").exists()
        after_state = json.loads(
            (project / ".specify" / "integration.json").read_text(
                encoding="utf-8"
            )
        )
        assert after_state == before_state

    def test_switch_preserves_target_options_with_fallback_integration(
        self, tmp_path
    ):
        project = _init_project(tmp_path, "claude")
        install = _run_in_project(
            project,
            [
                "integration",
                "install",
                "opencode",
                "--script",
                "sh",
                "--force",
            ],
        )
        assert install.exit_code == 0, install.output

        result = _run_in_project(
            project,
            [
                "integration",
                "switch",
                "copilot",
                "--integration-options",
                "--commands",
                "--script",
                "sh",
            ],
        )

        assert result.exit_code == 0, result.output
        assert (
            project / ".github" / "agents" / "speckit.plan.agent.md"
        ).exists()
        assert not (project / ".github" / "skills").exists()
        state = json.loads(
            (project / ".specify" / "integration.json").read_text(
                encoding="utf-8"
            )
        )
        assert state["integration_settings"]["copilot"]["parsed_options"] == {
            "commands": True
        }

    def test_switch_migrates_extension_commands(self, tmp_path):
        """Switching should migrate extension commands to the new agent directory."""
        project = _init_project(tmp_path, "kimi")

        # Install the bundled git extension
        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        # Verify git extension skills exist for kimi
        kimi_git_feature = project / ".kimi-code" / "skills" / "speckit-git-feature" / "SKILL.md"
        assert kimi_git_feature.exists(), "Git extension skill should exist for kimi"

        result = _run_in_project(project, [
            "integration", "switch", "opencode",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        # Git extension commands should exist for opencode
        opencode_git_feature = project / ".opencode" / "commands" / "speckit.git.feature.md"
        assert opencode_git_feature.exists(), "Git extension command should exist for opencode"

        # Old kimi extension skills should be removed
        assert not kimi_git_feature.exists(), "Old kimi extension skill should be removed"

        # Extension registry should be updated
        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        registered_commands = registry["extensions"]["git"]["registered_commands"]
        assert "opencode" in registered_commands
        assert "kimi" not in registered_commands

        # Switch to claude
        result = _run_in_project(project, [
            "integration", "switch", "claude",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        # Git extension skills should exist for claude
        claude_git_feature = project / ".claude" / "skills" / "speckit-git-feature" / "SKILL.md"
        assert claude_git_feature.exists(), "Git extension skill should exist for claude"

        # Old opencode extension commands should be removed
        assert not opencode_git_feature.exists(), "Old opencode extension command should be removed"

        # Extension registry should be updated
        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        registered_commands = registry["extensions"]["git"]["registered_commands"]
        assert "claude" in registered_commands
        assert "opencode" not in registered_commands

    def test_switch_installed_target_backfills_extension_commands(self, tmp_path):
        """Switching to an already-installed agent should register extensions."""
        project = _init_project(tmp_path, "claude")

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        registry_path = project / ".specify" / "extensions" / ".registry"
        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]
        assert "claude" in registered
        assert "codex" not in registered, "precondition: codex not yet installed"

        result = _run_in_project(project, [
            "integration", "install", "codex",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        codex_git_feature = (
            project / ".agents" / "skills" / "speckit-git-feature" / "SKILL.md"
        )
        assert not codex_git_feature.exists()

        result = _run_in_project(project, ["integration", "switch", "codex"])
        assert result.exit_code == 0, result.output

        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]
        assert "codex" in registered
        assert codex_git_feature.exists()

    def test_switch_migrates_copilot_skills_extension_commands(self, tmp_path):
        """Copilot --skills should receive extension skills, not .agent.md files."""
        project = _init_project(tmp_path, "opencode")

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        result = _run_in_project(project, [
            "integration", "switch", "copilot",
            "--script", "sh",
            "--integration-options", "--skills",
        ])
        assert result.exit_code == 0, result.output

        copilot_git_feature = project / ".github" / "skills" / "speckit-git-feature" / "SKILL.md"
        copilot_agent_file = project / ".github" / "agents" / "speckit.git.feature.agent.md"
        assert copilot_git_feature.exists(), "Git extension skill should exist for Copilot skills mode"
        assert not copilot_agent_file.exists(), "Copilot skills mode should not create extension .agent.md files"

        # Verify Copilot skill frontmatter does NOT contain mode: — VS Code Copilot does not support it
        skill_content = copilot_git_feature.read_text(encoding="utf-8")
        assert "mode:" not in skill_content, (
            "Copilot skill frontmatter must not contain unsupported 'mode' field"
        )

        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        git_meta = registry["extensions"]["git"]
        assert "speckit-git-feature" in git_meta["registered_skills"]
        assert "copilot" not in git_meta["registered_commands"]

        result = _run_in_project(project, [
            "integration", "switch", "opencode",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        opencode_git_feature = project / ".opencode" / "commands" / "speckit.git.feature.md"
        assert opencode_git_feature.exists(), "Git extension command should exist for opencode"
        assert not copilot_git_feature.exists(), "Old Copilot extension skill should be removed"

        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        git_meta = registry["extensions"]["git"]
        assert git_meta["registered_skills"] == []
        assert "opencode" in git_meta["registered_commands"]
        assert "copilot" not in git_meta["registered_commands"]

    def test_switch_to_not_yet_installed_unregisters_old_preset_artifacts(self, tmp_path):
        """Switching to a not-yet-installed integration must also clean up
        the old agent's preset command overrides, mirroring the existing
        extension cleanup on the same code path (#2948).

        Without this, a preset's command override -- including a custom
        preset command -- rendered for the previous agent lingers as an
        orphan once a different, not-yet-installed integration becomes the
        new active agent.
        """
        project = _init_project(tmp_path, "auggie")

        preset_src = tmp_path / "switch-cleanup-preset"
        (preset_src / "commands").mkdir(parents=True)
        (preset_src / "commands" / "speckit.specify.md").write_text(
            "---\ndescription: Custom preset command\n---\nOverridden content\n",
            encoding="utf-8",
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "switch-cleanup-preset",
                "name": "Switch Cleanup Preset",
                "version": "1.0.0",
                "description": "Test preset with a custom command override",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.specify",
                        "file": "commands/speckit.specify.md",
                    }
                ]
            },
        }
        import yaml

        (preset_src / "preset.yml").write_text(yaml.dump(manifest_data), encoding="utf-8")

        result = _run_in_project(project, ["preset", "add", "--dev", str(preset_src)])
        assert result.exit_code == 0, f"preset add failed: {result.output}"

        auggie_cmd = project / ".augment" / "commands" / "speckit.specify.md"
        assert auggie_cmd.exists(), "sanity: preset command registered for auggie"

        registry_path = project / ".specify" / "presets" / ".registry"
        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "presets"
        ]["switch-cleanup-preset"]["registered_commands"]
        assert "auggie" in registered, "sanity: auggie tracked before switch"

        # opencode is not yet installed in this project.
        result = _run_in_project(project, [
            "integration", "switch", "opencode",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        assert not auggie_cmd.exists(), (
            "old agent's preset command override must be removed on switch "
            "to a not-yet-installed integration, mirroring the existing "
            "extension cleanup on this same code path (#2948)"
        )

        opencode_cmd = project / ".opencode" / "commands" / "speckit.specify.md"
        assert opencode_cmd.exists(), "preset command should be registered for the new agent"

        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "presets"
        ]["switch-cleanup-preset"]["registered_commands"]
        assert "auggie" not in registered, (
            "old agent's tracking must be dropped after switch cleanup"
        )
        assert "opencode" in registered

    def test_switch_does_not_register_disabled_extensions(self, tmp_path):
        """Disabled extensions should stay disabled and should not migrate commands."""
        project = _init_project(tmp_path, "opencode")

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"
        result = _run_in_project(project, ["extension", "disable", "git"])
        assert result.exit_code == 0, result.output

        opencode_git_feature = project / ".opencode" / "commands" / "speckit.git.feature.md"
        assert opencode_git_feature.exists(), "Disabled extension command remains until integration switch"

        result = _run_in_project(project, [
            "integration", "switch", "claude",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        claude_git_feature = project / ".claude" / "skills" / "speckit-git-feature" / "SKILL.md"
        assert not claude_git_feature.exists(), "Disabled extension should not be registered for new agent"
        assert not opencode_git_feature.exists(), "Old disabled extension command should be removed on switch"

        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        git_meta = registry["extensions"]["git"]
        assert git_meta["enabled"] is False
        assert "claude" not in git_meta["registered_commands"]
        assert "opencode" not in git_meta["registered_commands"]

    def test_switch_refreshes_managed_shared_script_refs(self, tmp_path):
        """Switching refreshes managed shared scripts to the target command style."""
        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "setup-tasks.sh"
        assert shared_script.exists()
        shared_content = shared_script.read_text(encoding="utf-8")
        assert "/speckit-plan" in shared_content

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--integration-options", "--commands",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0

        assert shared_script.exists()
        updated = shared_script.read_text(encoding="utf-8")
        assert "/speckit.plan" in updated
        assert "/speckit-plan" not in updated

    def test_switch_refreshes_stale_managed_shared_infra(self, tmp_path):
        """Regression for #2293: stale managed shared scripts get refreshed on switch."""
        import hashlib

        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "setup-tasks.sh"
        assert "/speckit-plan" in shared_script.read_text(encoding="utf-8")

        # Simulate a stale vendored script: write truncated content as bytes
        # (write_text would translate \n→\r\n on Windows and break the hash)
        # and update the speckit manifest hash so the stale copy is treated
        # as "managed" (installed by spec-kit, not a user customization).
        stale_bytes = b"#!/usr/bin/env bash\n# stale vendored copy\n"
        shared_script.write_bytes(stale_bytes)

        manifest_path = project / ".specify" / "integrations" / "speckit.manifest.json"
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_data["files"][".specify/scripts/bash/setup-tasks.sh"] = (
            hashlib.sha256(stale_bytes).hexdigest()
        )
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--integration-options", "--commands",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0

        # Stale managed file should be replaced by the target integration's rendered version.
        updated = shared_script.read_text(encoding="utf-8")
        assert "# stale vendored copy" not in updated
        assert "/speckit.plan" in updated
        assert "/speckit-plan" not in updated

    def test_switch_preserves_user_customized_shared_infra(self, tmp_path):
        """User customizations (hash divergence from manifest) survive switch without --refresh-shared-infra."""
        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "common.sh"

        # User customization: append bytes but do NOT update manifest hash,
        # so on-disk hash diverges from the recorded one.
        original = shared_script.read_bytes()
        custom_bytes = original + b"\n# user customization\n"
        shared_script.write_bytes(custom_bytes)

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--integration-options", "--commands",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert shared_script.read_bytes() == custom_bytes
        assert "Preserved" in result.output

    def test_switch_refresh_shared_infra_overwrites_customizations(self, tmp_path):
        """--refresh-shared-infra explicitly overwrites user customizations on switch."""
        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "setup-tasks.sh"
        assert "/speckit-plan" in shared_script.read_text(encoding="utf-8")
        rendered_bytes = shared_script.read_bytes()

        # User customization (hash diverges from manifest)
        custom_bytes = rendered_bytes + b"\n# user customization\n"
        shared_script.write_bytes(custom_bytes)

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--integration-options", "--commands",
                "--script", "sh",
                "--refresh-shared-infra",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        # Customization is overwritten with the target integration's rendered version.
        updated = shared_script.read_text(encoding="utf-8")
        assert "# user customization" not in updated
        assert "/speckit.plan" in updated
        assert "/speckit-plan" not in updated

    def test_switch_preserves_recovered_files(self, tmp_path):
        """Regression for #2918: files marked recovered in the manifest are not overwritten.

        When a file already exists on disk before init and is recorded with
        ``recovered=True``, ``integration use``/``switch`` must not treat it as
        managed even when the on-disk hash matches the manifest hash.
        """
        import hashlib

        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "setup-tasks.sh"
        assert shared_script.is_file()

        # Simulate a team-customized file that was recorded as recovered:
        # write custom content, then update the manifest to record its hash
        # with the recovered flag set.
        custom_bytes = b"#!/usr/bin/env bash\n# team custom workflow\nexit 0\n"
        shared_script.write_bytes(custom_bytes)

        manifest_path = project / ".specify" / "integrations" / "speckit.manifest.json"
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        rel = ".specify/scripts/bash/setup-tasks.sh"
        manifest_data["files"][rel] = hashlib.sha256(custom_bytes).hexdigest()
        manifest_data.setdefault("recovered_files", []).append(rel)
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        # Recovered file must NOT be overwritten — team content preserved.
        assert shared_script.read_bytes() == custom_bytes

    def test_switch_skips_symlinked_parent_directory(self, tmp_path):
        """Regression: if .specify/scripts/bash is a symlink, switch must not write through it.

        Copilot follow-up on #2375: leaf-only symlink check let writes escape
        when an *ancestor* directory was symlinked outside the project root.
        """
        import sys
        if sys.platform.startswith("win"):
            import pytest as _pytest
            _pytest.skip("Symlink creation typically requires admin on Windows")

        project = _init_project(tmp_path, "claude")
        bash_dir = project / ".specify" / "scripts" / "bash"
        outside = tmp_path / "outside"
        outside.mkdir()
        for child in bash_dir.iterdir():
            child.rename(outside / child.name)
        bash_dir.rmdir()
        bash_dir.symlink_to(outside, target_is_directory=True)
        sentinel = (outside / "common.sh").read_bytes()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        # Symlinked tree reported, not written through.
        assert "symlink" in result.output.lower()
        # Outside dir contents unchanged.
        assert (outside / "common.sh").read_bytes() == sentinel

    def test_switch_force_alone_does_not_overwrite_shared_customizations(self, tmp_path):
        """--force (uninstall semantics) must NOT overwrite shared-infra customizations.

        Regression: ensures the decoupling of --force and --refresh-shared-infra.
        """
        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "common.sh"
        bundled_bytes = shared_script.read_bytes()

        custom_bytes = bundled_bytes + b"\n# user customization\n"
        shared_script.write_bytes(custom_bytes)

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
                "--force",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        # --force alone preserves the customization
        assert shared_script.read_bytes() == custom_bytes

    def test_switch_from_nothing(self, tmp_path):
        """Switch when no integration is installed should just install the target."""
        project = tmp_path / "bare"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "Switched to" in result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "claude"

    def test_failed_switch_keeps_fallback_metadata_consistent(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, [
                "integration", "switch", "generic",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "codex"
        assert data["installed_integrations"] == ["codex"]

        opts = json.loads((project / ".specify" / "init-options.json").read_text(encoding="utf-8"))
        assert opts["integration"] == "codex"
        assert opts["ai"] == "codex"

        template = project / ".specify" / "templates" / "plan-template.md"
        assert "$speckit-plan" in template.read_text(encoding="utf-8")

    def test_failed_switch_rescaffolds_fallback_extensions(self, tmp_path):
        """Regression (review 3624184343).

        When Phase 2 of a switch fails, rollback selects another installed
        integration as the new default. Under active-only registration that
        fallback may never have received extension artifacts (it was
        installed while another integration was active), and Phase 1 already
        unregistered the outgoing agent's artifacts — so the restored default
        must be rescaffolded, not just written to metadata.
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
        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]
        assert "codex" not in registered, (
            "precondition: secondary install has no extension artifacts"
        )

        result = _run_in_project(project, [
            "integration", "switch", "generic",
            "--script", "sh",
        ])
        assert result.exit_code != 0

        data = json.loads(
            (project / ".specify" / "integration.json").read_text(encoding="utf-8")
        )
        assert data["integration"] == "codex", "precondition: fallback restored"

        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]
        assert "codex" in registered, (
            "rollback must rescaffold extensions for the restored default"
        )
        assert (
            project / ".agents" / "skills" / "speckit-git-feature" / "SKILL.md"
        ).exists()


class TestSwitchClearsMetadataAfterTeardown:
    def test_metadata_cleared_between_phases(self, tmp_path):
        """After a successful switch, metadata should reference the new integration."""
        project = _init_project(tmp_path, "claude")

        # Verify initial state
        int_json = project / ".specify" / "integration.json"
        assert json.loads(int_json.read_text(encoding="utf-8"))["integration"] == "claude"

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            # Switch to copilot — should succeed and update metadata
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0

        # integration.json should reference copilot, not claude
        data = json.loads(int_json.read_text(encoding="utf-8"))
        assert data["integration"] == "copilot"

        # init-options.json should reference copilot
        opts_json = project / ".specify" / "init-options.json"
        opts = json.loads(opts_json.read_text(encoding="utf-8"))
        assert opts.get("ai") == "copilot"


class TestIntegrationSwitchDiagnostics(IntegrationCatalogCliTestBase):
    def test_integration_switch_cleanup_warning_reports_phase_and_targets(
        self, tmp_path, monkeypatch
    ):
        from specify_cli.extensions import ExtensionManager

        project = self._make_project(tmp_path)
        (project / ".specify" / "integrations").mkdir(parents=True, exist_ok=True)
        (project / ".specify" / "integration.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "integration": "copilot",
                    "integrations": ["copilot"],
                    "integration_settings": {"copilot": {"script": "sh"}},
                }
            ),
            encoding="utf-8",
        )
        (project / ".specify" / "integrations" / "copilot.manifest.json").write_text(
            json.dumps(
                {
                    "integration": "copilot",
                    "version": "0.0.0",
                    "installed_at": "2026-05-16T00:00:00+00:00",
                    "files": {},
                }
            ),
            encoding="utf-8",
        )

        def fail_cleanup(self, integration_key):
            raise OSError("cleanup exploded")

        monkeypatch.setattr(ExtensionManager, "unregister_agent_artifacts", fail_cleanup)

        result = self._invoke(["integration", "switch", "claude"], project)
        normalized = _normalize_cli_output(result.output)

        assert result.exit_code == 0, result.output
        assert "Failed to clean up extension artifacts for integration 'copilot'" in normalized
        assert "cleanup exploded" in normalized
        assert "Switched to integration" in normalized
