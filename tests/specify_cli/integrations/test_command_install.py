"""Tests for mirrored integration CLI behavior in test_command_install.py."""

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

class TestIntegrationInstall:
    def test_install_requires_speckit_project(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["integration", "install", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Not a Spec Kit project" in result.output

    def test_install_unknown_integration(self, tmp_path):
        project = _init_project(tmp_path)
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "install", "nonexistent"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Unknown integration" in result.output

    def test_install_already_installed(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "install", "copilot"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        plain = strip_ansi(result.output)
        assert "already installed" in plain
        normalized = " ".join(plain.split())
        assert "specify integration upgrade copilot" in normalized
        assert "already the default integration" in normalized
        assert "No files were changed" in normalized
        assert "specify integration uninstall copilot" not in normalized

    def test_install_already_installed_non_default_guides_use(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, ["integration", "install", "codex"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        normalized = " ".join(output.split())
        assert "already installed" in normalized
        assert "specify integration use codex" in normalized
        assert "specify integration upgrade codex" in normalized
        assert "specify integration uninstall codex" not in normalized

    def test_install_different_when_one_exists(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "install", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        plain = strip_ansi(result.output)
        assert "Installed integrations: copilot" in plain
        assert "Default integration: copilot" in plain
        normalized = " ".join(plain.split())
        assert "To replace the default integration" in normalized
        assert "specify integration switch claude" in normalized
        assert "To install 'claude' alongside" in normalized
        assert "retry the same install command with --force" in normalized

    def test_install_multi_safe_integration(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        assert "installed successfully" in result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "claude"
        assert data["default_integration"] == "claude"
        assert data["integration_state_schema"] == 1
        assert data["installed_integrations"] == ["claude", "codex"]
        assert data["integration_settings"]["claude"]["invoke_separator"] == "-"
        assert data["integration_settings"]["codex"]["invoke_separator"] == "-"

        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert (project / ".agents" / "skills" / "speckit-plan" / "SKILL.md").exists()

    def test_install_non_default_refreshes_init_options_version_only(self, tmp_path, monkeypatch):
        project = _init_project(tmp_path, "claude")
        init_options = project / ".specify" / "init-options.json"
        opts = json.loads(init_options.read_text(encoding="utf-8"))
        opts["speckit_version"] = "0.6.1"
        init_options.write_text(json.dumps(opts), encoding="utf-8")

        import specify_cli.integrations._commands as _int_cmds

        monkeypatch.setattr(_int_cmds, "get_speckit_version", lambda: "0.8.11")

        result = _run_in_project(project, [
            "integration", "install", "codex",
            "--script", "sh",
        ])

        assert result.exit_code == 0, result.output
        updated = json.loads(init_options.read_text(encoding="utf-8"))
        assert updated["speckit_version"] == "0.8.11"
        assert updated["integration"] == "claude"
        assert updated["ai"] == "claude"
        assert "context_file" not in updated

    def test_install_additional_preserves_shared_manifest(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        shared_manifest = project / ".specify" / "integrations" / "speckit.manifest.json"
        before = set(json.loads(shared_manifest.read_text(encoding="utf-8"))["files"])
        assert before

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        after = set(json.loads(shared_manifest.read_text(encoding="utf-8"))["files"])
        assert before <= after

    def test_install_multi_safe_migrates_legacy_state(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        int_json = project / ".specify" / "integration.json"
        int_json.write_text(json.dumps({
            "integration": "claude",
            "version": "0.0.0",
        }), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        data = json.loads(int_json.read_text(encoding="utf-8"))
        assert data["integration"] == "claude"
        assert data["default_integration"] == "claude"
        assert data["installed_integrations"] == ["claude", "codex"]

    def test_install_multi_unsafe_requires_force(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        plain = strip_ansi(result.output)
        assert "Installed integrations: copilot" in plain
        assert "multi-install safe" in plain
        normalized = " ".join(plain.split())
        assert "To replace the default integration" in normalized
        assert "specify integration switch claude" in normalized
        assert "To install 'claude' alongside" in normalized
        assert "retry the same install command with --force" in normalized

    def test_install_multi_unsafe_allowed_with_force(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
                "--force",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "copilot"
        assert data["installed_integrations"] == ["copilot", "claude"]

    def test_install_into_bare_project(self, tmp_path):
        """Install into a project with .specify/ but no integration."""
        project = tmp_path / "bare"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        assert "installed successfully" in result.output

        # integration.json written
        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "claude"

        # Manifest created
        assert (project / ".specify" / "integrations" / "claude.manifest.json").exists()

        # Claude uses skills directory (not commands)
        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()

    def test_install_bare_project_gets_shared_infra(self, tmp_path):
        """Installing into a bare project should create shared scripts and templates."""
        project = tmp_path / "bare"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        # Shared infrastructure should be present
        assert (project / ".specify" / "scripts").is_dir()
        assert (project / ".specify" / "templates").is_dir()
        script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        script_content = script.read_text(encoding="utf-8")
        assert "/speckit-specify" in script_content
        assert "/speckit.specify" not in script_content

    def test_install_dollar_skill_into_bare_project_gets_native_shared_refs(
        self, tmp_path
    ):
        """A dollar-style integration supplies its prefix without a default."""
        project = tmp_path / "bare-codex"
        project.mkdir()
        (project / ".specify").mkdir()

        result = _run_in_project(
            project, ["integration", "install", "codex", "--script", "sh"]
        )

        assert result.exit_code == 0, result.output
        plan = project / ".specify" / "templates" / "plan-template.md"
        plan_content = plan.read_text(encoding="utf-8")
        assert "$speckit-plan" in plan_content
        assert "/speckit-plan" not in plan_content

    def test_install_defers_extension_commands_until_use(self, tmp_path):
        """Installing a second integration does not register enabled extensions.

        Maintainer-requested behavior for #2886: extension command back-fill is
        limited to ``integration use`` / ``switch`` / ``upgrade``. Plain
        ``install`` only adds the integration; selecting it with ``use`` then
        registers the enabled extensions for that agent.
        """
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

        # Install alone does not back-fill the git extension for the secondary
        # agent.
        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]
        assert "claude" in registered, "existing agent registration preserved"
        assert "codex" not in registered
        assert not (
            project / ".agents" / "skills" / "speckit-git-feature" / "SKILL.md"
        ).exists()

        result = _run_in_project(project, ["integration", "use", "codex"])
        assert result.exit_code == 0, result.output

        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]
        assert "codex" in registered, "use should register extension commands (#2886)"
        assert (
            project / ".agents" / "skills" / "speckit-git-feature" / "SKILL.md"
        ).exists()

    def test_install_does_not_register_disabled_extensions(self, tmp_path):
        """A disabled extension must not be registered for a newly installed agent."""
        project = _init_project(tmp_path, "claude")

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"
        result = _run_in_project(project, ["extension", "disable", "git"])
        assert result.exit_code == 0, result.output

        result = _run_in_project(project, [
            "integration", "install", "codex",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        registry_path = project / ".specify" / "extensions" / ".registry"
        git_meta = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]
        assert git_meta["enabled"] is False
        assert "codex" not in git_meta["registered_commands"]
        assert not (
            project / ".agents" / "skills" / "speckit-git-feature" / "SKILL.md"
        ).exists()

    def test_install_skills_mode_secondary_agent_defers_extension_artifacts(self, tmp_path):
        """A non-active skills-mode agent gets extension artifacts only on use.

        Plain ``install`` has no extension side effects. Once the secondary
        Copilot ``--skills`` integration is selected with ``use``, it becomes the
        active agent and receives extension skills.
        """
        project = _init_project(tmp_path, "claude")

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        # Copilot is not multi_install_safe, so --force is required to add it
        # alongside the existing default integration.
        result = _run_in_project(project, [
            "integration", "install", "copilot",
            "--script", "sh",
            "--integration-options", "--skills",
            "--force",
        ])
        assert result.exit_code == 0, result.output

        # Precondition that makes --skills load-bearing: copilot IS in skills
        # mode, so its own core commands are scaffolded as skills.
        assert (
            project / ".github" / "skills" / "speckit-specify" / "SKILL.md"
        ).exists(), "precondition: copilot installed in skills mode"

        # The git extension is not registered for the non-active copilot agent
        # during install.
        git_meta = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )["extensions"]["git"]
        assert "copilot" not in git_meta["registered_commands"]
        assert not (
            project / ".github" / "agents" / "speckit.git.feature.agent.md"
        ).exists()
        assert not (
            project / ".github" / "skills" / "speckit-git-feature" / "SKILL.md"
        ).exists()

        result = _run_in_project(project, ["integration", "use", "copilot"])
        assert result.exit_code == 0, result.output

        git_meta = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )["extensions"]["git"]
        # `use` makes copilot active, so extension artifacts follow copilot's
        # skills-mode layout.
        assert "copilot" not in git_meta["registered_commands"]
        assert "speckit-git-feature" in git_meta["registered_skills"]
        assert not (
            project / ".github" / "agents" / "speckit.git.feature.agent.md"
        ).exists()
        assert (
            project / ".github" / "skills" / "speckit-git-feature" / "SKILL.md"
        ).exists()

    def test_extension_add_registers_active_integration_only(self, tmp_path):
        """``extension add`` registers commands for the active integration only.

        Maintainer-requested behavior for #2948: with multiple integrations
        installed, ``extension add`` must treat the project as single-active —
        only the current integration gets the new extension's commands.
        Non-active integrations receive them when selected via
        ``integration use`` / ``switch`` (rescaffold).
        """
        project = _init_project(tmp_path, "claude")

        result = _run_in_project(project, [
            "integration", "install", "codex",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        registry_path = project / ".specify" / "extensions" / ".registry"
        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]
        assert "claude" in registered, "active integration gets the extension"
        assert "codex" not in registered, (
            "non-active integration must not be registered on add (#2948)"
        )
        assert (
            project / ".claude" / "skills" / "speckit-git-feature" / "SKILL.md"
        ).exists()
        assert not (
            project / ".agents" / "skills" / "speckit-git-feature" / "SKILL.md"
        ).exists()

        # Selecting the other integration rescaffolds it with the extension.
        result = _run_in_project(project, ["integration", "use", "codex"])
        assert result.exit_code == 0, result.output

        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]
        assert "codex" in registered, "use registers extensions for the new active agent"
        assert (
            project / ".agents" / "skills" / "speckit-git-feature" / "SKILL.md"
        ).exists()

    def test_extension_add_generic_active_does_not_backfill_other_agents(self, tmp_path):
        """A recorded but unsupported active key (``generic``) must not
        fall back to registering every detected agent.

        ``generic`` is deliberately excluded from ``AGENT_CONFIGS`` because
        its output directory is only known via ``--commands-dir``, not a
        static config. Before the fix, treating that active key like "no
        active integration recorded" made the fallback register the
        extension for every other detected agent — exactly the multi-target
        behavior #2948 is meant to stop.
        """
        project = _init_project(
            tmp_path, "generic",
            integration_options="--commands-dir .myagent/commands",
        )

        result = _run_in_project(project, [
            "integration", "install", "codex",
            "--script", "sh",
            "--force",
        ])
        assert result.exit_code == 0, result.output

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        registry_path = project / ".specify" / "extensions" / ".registry"
        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]
        assert "codex" not in registered, (
            "a recorded but unsupported active key must not target other "
            "detected agents (#2948)"
        )

    def test_extension_add_malformed_ai_value_fails_closed(self, tmp_path):
        """A recorded but malformed ``ai`` value (e.g. a list) must not be
        treated as "no active integration recorded" and must not crash.

        Before the fix, ``init_options.get("ai")`` being falsy (``[]``,
        ``""``, ``0``) triggered the same all-agents fallback as a missing
        key, and a *truthy* non-string value (e.g. a non-empty list) would
        reach ``AGENT_CONFIGS.get(active_agent)`` and raise ``TypeError``
        because a list is unhashable. Corrupted init-options must instead
        fail closed: register nothing rather than crash or back-fill every
        detected agent.
        """
        project = _init_project(tmp_path, "claude")

        result = _run_in_project(project, [
            "integration", "install", "codex",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        init_options_path = project / ".specify" / "init-options.json"
        init_options = json.loads(init_options_path.read_text(encoding="utf-8"))
        init_options["ai"] = []
        init_options_path.write_text(json.dumps(init_options), encoding="utf-8")

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        registry_path = project / ".specify" / "extensions" / ".registry"
        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]
        assert registered == {}, (
            "a malformed recorded 'ai' value must fail closed, not "
            "back-fill every detected agent (#2948)"
        )

    def test_extension_add_corrupted_init_options_file_fails_closed(self, tmp_path):
        """A present-but-unparseable init-options.json must fail closed too,
        not be treated the same as "no file at all".

        ``load_init_options`` returns ``{}`` for a corrupted/unreadable
        file just like it does for a missing file, so a naive "no active
        agent recorded" check based on ``load_init_options`` alone can't
        tell a legacy pre-init-options project (legitimate all-agent
        fallback) apart from a corrupted-but-present file for a #2948
        project (must fail closed). Corrupting the file after a normal
        init must not reintroduce the all-agent fallback.
        """
        project = _init_project(tmp_path, "claude")

        result = _run_in_project(project, [
            "integration", "install", "codex",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        init_options_path = project / ".specify" / "init-options.json"
        init_options_path.write_text("{not valid json", encoding="utf-8")

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        registry_path = project / ".specify" / "extensions" / ".registry"
        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]
        assert registered == {}, (
            "a corrupted init-options.json must fail closed, not be "
            "treated like a legacy project missing the file entirely (#2948)"
        )

    def test_extension_add_dangling_init_options_symlink_fails_closed(self, tmp_path):
        """A dangling init-options.json symlink must fail closed too, not be
        treated the same as "no file at all".

        ``Path.exists()`` follows symlinks and returns False for a broken
        symlink whose target doesn't exist, so a naive presence check based
        on ``Path.exists()`` alone mistakes a dangling symlink for "no file"
        and falls back to registering every detected agent.
        """
        project = _init_project(tmp_path, "claude")

        result = _run_in_project(project, [
            "integration", "install", "codex",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        init_options_path = project / ".specify" / "init-options.json"
        init_options_path.unlink()
        init_options_path.symlink_to(project / ".specify" / "does-not-exist.json")
        assert not init_options_path.exists()  # sanity: dangling
        assert init_options_path.is_symlink()

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        registry_path = project / ".specify" / "extensions" / ".registry"
        registered = json.loads(registry_path.read_text(encoding="utf-8"))[
            "extensions"
        ]["git"]["registered_commands"]
        assert registered == {}, (
            "a dangling init-options.json symlink must fail closed, not be "
            "treated like a legacy project missing the file entirely (#2948)"
        )


class TestScriptTypeValidation:
    def test_invalid_script_type_rejected(self, tmp_path):
        """--script with an invalid value should fail with a clear error."""
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "bash",
            ])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Invalid script type" in result.output

    def test_valid_script_types_accepted(self, tmp_path):
        """Both 'sh' and 'ps' should be accepted."""
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0


class TestIntegrationInstallDiagnostics(IntegrationCatalogCliTestBase):
    def test_integration_install_failure_reports_phase_target_and_rollback(
        self, tmp_path, monkeypatch
    ):
        from specify_cli.integrations import INTEGRATION_REGISTRY
        from specify_cli.integrations.base import IntegrationBase

        class BrokenIntegration(IntegrationBase):
            key = "broken-test"
            config = {
                "name": "Broken Test",
                "folder": ".broken/",
                "commands_subdir": "commands",
                "install_url": None,
                "requires_cli": False,
            }
            registrar_config = {
                "dir": ".broken/commands",
                "format": "markdown",
                "args": "$ARGUMENTS",
                "extension": ".md",
            }

            def setup(self, project_root, manifest, **kwargs):
                raise OSError("setup exploded\nwith context")

            def teardown(self, project_root, manifest, force=False):
                raise OSError("rollback exploded")

        project = self._make_project(tmp_path)
        monkeypatch.setitem(INTEGRATION_REGISTRY, "broken-test", BrokenIntegration())

        result = self._invoke(["integration", "install", "broken-test"], project)
        normalized = _normalize_cli_output(result.output)

        assert result.exit_code == 1, result.output
        assert "Failed to rollback integration 'broken-test'" in normalized
        assert "rollback exploded" in normalized
        assert "Failed to install integration 'broken-test'" in normalized
        assert "setup exploded with context" in normalized
