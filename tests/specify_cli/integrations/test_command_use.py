"""Tests for mirrored integration CLI behavior in test_command_use.py."""

from __future__ import annotations

import json  # noqa: F401
import os  # noqa: F401
import shutil  # noqa: F401
from pathlib import Path  # noqa: F401

import pytest  # noqa: F401

from specify_cli import app  # noqa: F401
from tests.conftest import strip_ansi  # noqa: F401
from tests.specify_cli.integrations._helpers import (
    _copy_project_template,  # noqa: F401
    _init_project,  # noqa: F401
    _integration_list_row_cells,  # noqa: F401
    _move_kilocode_install_to_legacy_layout,  # noqa: F401
    _run_in_project,  # noqa: F401
    _write_invalid_manifest,  # noqa: F401
    runner,  # noqa: F401
)

class TestIntegrationUse:
    def test_use_installed_integration_sets_default(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, ["integration", "use", "codex"], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "codex"
        assert data["default_integration"] == "codex"
        assert data["installed_integrations"] == ["claude", "codex"]

        opts = json.loads((project / ".specify" / "init-options.json").read_text(encoding="utf-8"))
        assert opts["integration"] == "codex"
        assert opts["ai"] == "codex"

    def test_use_preserves_copilot_skills_mode(self, tmp_path):
        """`use` on a skills-mode Copilot keeps ``ai_skills`` (issue #3550).

        Re-selecting the same skills-mode Copilot must not drop ``ai_skills``
        from init-options.json nor regenerate extension commands in the legacy
        ``.agent.md``/``.prompt.md`` layout.
        """
        project = _init_project(tmp_path, "copilot", integration_options="--skills")

        opts = json.loads((project / ".specify" / "init-options.json").read_text(encoding="utf-8"))
        assert opts.get("ai_skills") is True, "precondition: init recorded skills mode"

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        # Simulate a fresh process: `use` in real life runs in its own process
        # where the registry's Copilot instance has _skills_mode == False (it is
        # only set during setup()). In-process test invocations otherwise reuse
        # the singleton left in skills mode by init, masking the bug (#3550).
        from specify_cli.integrations import get_integration

        get_integration("copilot")._skills_mode = False

        result = _run_in_project(project, ["integration", "use", "copilot"])
        assert result.exit_code == 0, result.output

        opts = json.loads((project / ".specify" / "init-options.json").read_text(encoding="utf-8"))
        assert opts.get("ai_skills") is True, "ai_skills must survive `use copilot`"

        # No legacy command-layout files should be regenerated for the
        # skills-mode agent.
        assert not (project / ".github" / "agents" / "speckit.git.feature.agent.md").exists()
        assert not (project / ".github" / "prompts" / "speckit.git.feature.prompt.md").exists()
        assert (
            project / ".github" / "skills" / "speckit-git-feature" / "SKILL.md"
        ).exists()

    def test_use_requires_installed_integration(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "use", "codex"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "not installed" in result.output

    def test_use_registers_presets_for_the_newly_active_agent(self, tmp_path):
        """``integration use`` is the single rescaffold point for presets too.

        Mirrors the extension single-active rule (#2948): a preset command
        override installed while ``claude`` was active must not target the
        inactive ``codex`` integration, and switching via ``integration use``
        must rescaffold it there.
        """
        project = _init_project(tmp_path, "claude")

        result = _run_in_project(project, [
            "integration", "install", "codex",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        preset_src = tmp_path / "cmd-preset"
        (preset_src / "commands").mkdir(parents=True)
        (preset_src / "commands" / "speckit.specify.md").write_text(
            "---\ndescription: Overridden specify\n---\nOverridden content\n",
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

        registry_path = project / ".specify" / "presets" / ".registry"
        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "presets"
        ]["cmd-preset"]["registered_commands"]
        assert "claude" in registered, "active integration gets the preset command override"
        assert "codex" not in registered, (
            "non-active integration must not be registered on preset add (#2948)"
        )

        result = _run_in_project(project, ["integration", "use", "codex"])
        assert result.exit_code == 0, result.output

        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "presets"
        ]["cmd-preset"]["registered_commands"]
        assert "codex" in registered, "use registers presets for the new active agent"
        assert "claude" in registered, "the previous agent's registration is preserved"

    def test_use_reregisters_presets_highest_precedence_last(self, tmp_path):
        """When two enabled presets override the same command, the
        higher-precedence preset (lower priority number) must win the
        materialized file after ``integration use`` rescaffolds them.

        ``register_enabled_presets_for_agent`` iterates presets and each
        pass overwrites the same target file, so the write order matters.
        Before the fix, presets were processed lowest-number-first (highest
        precedence first), so the lower-precedence preset was written last
        and won -- reversing the documented priority stack (#2948).
        """
        project = _init_project(tmp_path, "claude")

        result = _run_in_project(project, [
            "integration", "install", "codex",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        import yaml

        def _make_preset(pack_id: str, content: str) -> Path:
            src = tmp_path / pack_id
            (src / "commands").mkdir(parents=True)
            (src / "commands" / "speckit.specify.md").write_text(
                f"---\ndescription: {pack_id}\n---\n{content}\n",
                encoding="utf-8",
            )
            manifest_data = {
                "schema_version": "1.0",
                "preset": {
                    "id": pack_id,
                    "name": pack_id,
                    "version": "1.0.0",
                    "description": f"Test preset {pack_id}",
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
            (src / "preset.yml").write_text(yaml.dump(manifest_data), encoding="utf-8")
            return src

        # Lower-precedence preset (higher priority number), installed first.
        low_precedence_src = _make_preset("low-precedence-preset", "LOW PRECEDENCE CONTENT")
        result = _run_in_project(project, [
            "preset", "add", "--dev", str(low_precedence_src), "--priority", "20",
        ])
        assert result.exit_code == 0, f"preset add (low) failed: {result.output}"

        # Higher-precedence preset (lower priority number), installed second.
        high_precedence_src = _make_preset("high-precedence-preset", "HIGH PRECEDENCE CONTENT")
        result = _run_in_project(project, [
            "preset", "add", "--dev", str(high_precedence_src), "--priority", "1",
        ])
        assert result.exit_code == 0, f"preset add (high) failed: {result.output}"

        # Sanity: the priority stack already picks the high-precedence
        # preset's content for the active (claude) integration.
        claude_skill = project / ".claude" / "skills" / "speckit-specify" / "SKILL.md"
        assert "HIGH PRECEDENCE CONTENT" in claude_skill.read_text(encoding="utf-8")
        assert "LOW PRECEDENCE CONTENT" not in claude_skill.read_text(encoding="utf-8")

        result = _run_in_project(project, ["integration", "use", "codex"])
        assert result.exit_code == 0, result.output

        # After rescaffolding for the newly active codex integration, the
        # high-precedence preset must still win -- not whichever preset
        # register_enabled_presets_for_agent happened to write last.
        codex_skill = project / ".agents" / "skills" / "speckit-specify" / "SKILL.md"
        content = codex_skill.read_text(encoding="utf-8")
        assert "HIGH PRECEDENCE CONTENT" in content, (
            "highest-precedence preset must win after `use` rescaffolds "
            "presets for the newly active integration (#2948)"
        )
        assert "LOW PRECEDENCE CONTENT" not in content

    def test_use_refreshes_shared_templates_between_command_styles(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        template = project / ".specify" / "templates" / "plan-template.md"
        script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        assert "/speckit-plan" in template.read_text(encoding="utf-8")
        assert "/speckit-plan" in script.read_text(encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "gemini",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            use_gemini = runner.invoke(app, ["integration", "use", "gemini"], catch_exceptions=False)
            assert use_gemini.exit_code == 0, use_gemini.output
            assert "/speckit.plan" in template.read_text(encoding="utf-8")
            assert "/speckit.plan" in script.read_text(encoding="utf-8")
            assert "/speckit-plan" not in script.read_text(encoding="utf-8")

            use_claude = runner.invoke(app, ["integration", "use", "claude"], catch_exceptions=False)
            assert use_claude.exit_code == 0, use_claude.output
            assert "/speckit-plan" in template.read_text(encoding="utf-8")
            assert "/speckit-plan" in script.read_text(encoding="utf-8")
            assert "/speckit.plan" not in script.read_text(encoding="utf-8")
        finally:
            os.chdir(old_cwd)

    def test_use_preserves_modified_templates_unless_forced(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        template = project / ".specify" / "templates" / "plan-template.md"
        template.write_text("custom template with /speckit-plan\n", encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "gemini",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            use_gemini = runner.invoke(app, ["integration", "use", "gemini"], catch_exceptions=False)
            assert use_gemini.exit_code == 0, use_gemini.output
            normalized = " ".join(use_gemini.output.split())
            assert "specify integration use gemini --force" in normalized
            assert template.read_text(encoding="utf-8") == "custom template with /speckit-plan\n"

            force_use = runner.invoke(app, [
                "integration", "use", "gemini",
                "--force",
            ], catch_exceptions=False)
            assert force_use.exit_code == 0, force_use.output
        finally:
            os.chdir(old_cwd)

        updated = template.read_text(encoding="utf-8")
        assert "/speckit.plan" in updated
        assert "custom template" not in updated

    def test_use_does_not_persist_default_when_shared_infra_refresh_fails(self, tmp_path, monkeypatch):
        project = _init_project(tmp_path, "claude")
        int_json = project / ".specify" / "integration.json"
        init_options = project / ".specify" / "init-options.json"

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            before_state = json.loads(int_json.read_text(encoding="utf-8"))
            before_options = json.loads(init_options.read_text(encoding="utf-8"))
            import specify_cli

            def fail_refresh(*args, **kwargs):
                raise ValueError("refuse refresh")

            monkeypatch.setattr(specify_cli, "_install_shared_infra", fail_refresh)

            result = runner.invoke(app, [
                "integration", "use", "codex",
                "--force",
            ])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        assert "Failed to refresh shared infrastructure" in result.output
        assert json.loads(int_json.read_text(encoding="utf-8")) == before_state
        assert json.loads(init_options.read_text(encoding="utf-8")) == before_options
