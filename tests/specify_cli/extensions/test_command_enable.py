"""Tests for ``specify extension enable``.

Mirrors ``specify_cli.extensions.command_enable``.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import (
    ExtensionManager,
    ExtensionRegistry,
)
from tests.specify_cli.integrations._helpers import _init_project, _run_in_project


def _registration(project: Path, extension_id: str) -> dict:
    """Return the artifacts the registry tracks for *extension_id*."""
    registry = json.loads(
        (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
    )
    entry = registry["extensions"][extension_id]
    return {
        "registered_commands": entry["registered_commands"],
        "registered_skills": entry["registered_skills"],
    }


class TestExtensionEnableCLI:
    """CLI tests for ``specify extension enable``."""

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


class TestExtensionEnableAfterIntegrationChange:
    """``enable`` must leave the extension usable by the active integration."""

    # (integration, --integration-options, generated file, registry entry).
    # Claude renders extension commands as skills itself; Copilot in skills
    # mode gets them through the extension skill registration instead.
    LAYOUTS = [
        pytest.param(
            "claude",
            None,
            ".claude/skills/speckit-test-ext-hello/SKILL.md",
            {"registered_commands": {"claude": ["speckit.test-ext.hello"]},
             "registered_skills": []},
            id="claude",
        ),
        pytest.param(
            "copilot",
            "--skills",
            ".github/skills/speckit-test-ext-hello/SKILL.md",
            {"registered_commands": {},
             "registered_skills": ["speckit-test-ext-hello"]},
            id="copilot-skills",
        ),
    ]

    @pytest.mark.parametrize(("integration", "options", "artifact", "expected"), LAYOUTS)
    def test_enable_registers_commands_for_integration_switched_while_disabled(
        self, tmp_path, extension_dir, integration, options, artifact, expected
    ):
        """``integration switch`` registers only enabled extensions for the new
        agent and removes a disabled one's commands from the old agent, so the
        re-enabled extension must be registered for the now-active agent."""
        project = _init_project(tmp_path, "opencode")
        assert _run_in_project(
            project, ["extension", "add", str(extension_dir), "--dev"]
        ).exit_code == 0
        assert _run_in_project(project, ["extension", "disable", "test-ext"]).exit_code == 0
        switch = ["integration", "switch", integration, "--script", "sh"]
        if options:
            switch += ["--integration-options", options]
        switched = _run_in_project(project, switch)
        assert switched.exit_code == 0, switched.output
        generated = project / artifact
        assert not generated.exists(), "precondition: switch skips disabled extensions"

        result = _run_in_project(project, ["extension", "enable", "test-ext"])

        assert result.exit_code == 0, result.output
        assert generated.is_file()
        assert _registration(project, "test-ext") == expected

    @pytest.mark.parametrize(("integration", "options", "artifact", "expected"), LAYOUTS)
    def test_enable_leaves_commands_still_registered_for_active_integration(
        self, tmp_path, extension_dir, integration, options, artifact, expected
    ):
        """A plain disable/enable cycle does not rewrite the agent's files."""
        project = _init_project(tmp_path, integration, options)
        assert _run_in_project(
            project, ["extension", "add", str(extension_dir), "--dev"]
        ).exit_code == 0
        generated = project / artifact
        generated.unlink()
        generated.write_text("customized by the user\n", encoding="utf-8")
        assert _run_in_project(project, ["extension", "disable", "test-ext"]).exit_code == 0

        result = _run_in_project(project, ["extension", "enable", "test-ext"])

        assert result.exit_code == 0, result.output
        assert generated.read_text(encoding="utf-8") == "customized by the user\n"
        assert _registration(project, "test-ext") == expected

    @pytest.mark.parametrize(("integration", "options", "artifact", "expected"), LAYOUTS)
    def test_enable_keeps_dev_symlinked_outputs(
        self, tmp_path, extension_dir, integration, options, artifact, expected
    ):
        """A disable/enable cycle keeps a ``--dev`` install's symlinked output."""
        project = _init_project(tmp_path, integration, options)
        assert _run_in_project(
            project, ["extension", "add", str(extension_dir), "--dev"]
        ).exit_code == 0
        generated = project / artifact
        if not generated.is_symlink():
            pytest.skip("dev-mode symlinks are not available here")
        assert _run_in_project(project, ["extension", "disable", "test-ext"]).exit_code == 0

        result = _run_in_project(project, ["extension", "enable", "test-ext"])

        assert result.exit_code == 0, result.output
        assert generated.is_symlink()


def _enabled(project: Path, extension_id: str) -> bool:
    registry = json.loads(
        (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
    )
    return registry["extensions"][extension_id]["enabled"]


class TestExtensionEnableRegistrationFailure:
    """``enable`` must not report success when registration leaves files missing."""

    LAYOUTS = [
        pytest.param("claude", None, ".claude/skills/speckit-test-ext-hello/SKILL.md", id="claude"),
        pytest.param("copilot", "--skills", ".github/skills/speckit-test-ext-hello/SKILL.md", id="copilot-skills"),
        pytest.param("gemini", None, ".gemini/commands/speckit.test-ext.hello.toml", id="gemini-commands"),
    ]

    def _disabled_after_switch(self, tmp_path, extension_dir, integration, options):
        project = _init_project(tmp_path, "opencode")
        assert _run_in_project(
            project, ["extension", "add", str(extension_dir), "--dev"]
        ).exit_code == 0
        assert _run_in_project(project, ["extension", "disable", "test-ext"]).exit_code == 0
        switch = ["integration", "switch", integration, "--script", "sh"]
        if options:
            switch += ["--integration-options", options]
        assert _run_in_project(project, switch).exit_code == 0
        return project

    @pytest.mark.parametrize(
        "failure",
        [
            pytest.param(lambda *a, **k: None, id="writes-nothing"),
            pytest.param(
                lambda *a, **k: (_ for _ in ()).throw(RuntimeError("adapter setup failed")),
                id="raises",
            ),
        ],
    )
    @pytest.mark.parametrize(("integration", "options", "artifact"), LAYOUTS)
    def test_failed_registration_keeps_extension_disabled_and_retry_works(
        self, tmp_path, extension_dir, integration, options, artifact, failure
    ):
        project = self._disabled_after_switch(tmp_path, extension_dir, integration, options)
        generated = project / artifact

        with patch.object(
            ExtensionManager, "register_enabled_extensions_for_agent", failure
        ):
            failed = _run_in_project(project, ["extension", "enable", "test-ext"])

        assert failed.exit_code == 1, failed.output
        assert "Could not register invocations" in failed.output
        assert _enabled(project, "test-ext") is False
        assert not generated.exists()

        retried = _run_in_project(project, ["extension", "enable", "test-ext"])

        assert retried.exit_code == 0, retried.output
        assert _enabled(project, "test-ext") is True
        assert generated.exists()
