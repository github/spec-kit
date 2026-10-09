"""Tests for ``specify extension set-priority``.

Mirrors ``specify_cli.extensions.command_set_priority``.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app, save_init_options
from specify_cli.extensions import (
    ExtensionManager,
)
from specify_cli.presets import PresetManager
from tests.conftest import strip_ansi

# Concrete command name shared by the two extension providers and matched by
# the regex-composing preset selector used in the reprioritization tests.
# It lives in the ``alpha`` extension namespace; the ``beta`` provider can only
# layer on the same concrete name through the documented conventional command
# filename (``commands/<full-command-name>.md``) because primary extension
# command names are namespace-validated.
SHARED_COMMAND = "speckit.alpha.collect"
SELECTOR = r"regex:speckit\.alpha\..*"
SHARED_SKILL = "speckit-alpha-collect"


def _provider_extension(tmp_path, extension_id, declared_name, body, shared_body=None):
    """Build an extension that layers on ``SHARED_COMMAND``.

    ``declared_name`` is the extension's own namespaced primary command. When
    ``shared_body`` is given, the extension directory also ships a
    ``commands/<SHARED_COMMAND>.md`` conventional command file, which is how a
    second extension contributes a second ``replace`` layer for the same
    concrete resource.
    """
    source = tmp_path / f"{extension_id}-source"
    (source / "commands").mkdir(parents=True, exist_ok=True)
    (source / "commands" / "body.md").write_text(
        f"---\ndescription: {extension_id}\n---\n{body}\n", encoding="utf-8"
    )
    if shared_body is not None:
        (source / "commands" / f"{SHARED_COMMAND}.md").write_text(
            f"---\ndescription: {extension_id}\n---\n{shared_body}\n",
            encoding="utf-8",
        )
    (source / "extension.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "extension": {
                    "id": extension_id,
                    "name": extension_id,
                    "version": "1.0.0",
                    "description": "Test",
                    "author": "Test",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "commands": [
                        {
                            "name": declared_name,
                            "file": "commands/body.md",
                            "description": "Test",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    return source


def _selector_preset(tmp_path, strategy, body):
    """Build a preset whose regex selector composes over a shared command."""
    source = tmp_path / "selector-preset"
    (source / "commands").mkdir(parents=True)
    (source / "commands" / "body.md").write_text(
        f"---\ndescription: Selector\n---\n{body}\n", encoding="utf-8"
    )
    (source / "preset.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "preset": {
                    "id": "selector",
                    "name": "selector",
                    "version": "1.0.0",
                    "description": "Test",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "templates": [
                        {
                            "type": "command",
                            "name": SELECTOR,
                            "file": "commands/body.md",
                            "strategy": strategy,
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    return source


class TestExtensionSetPriorityCLI:
    """CLI tests for ``specify extension set-priority``."""

    def test_set_priority_changes_priority(self, extension_dir, project_dir):
        """Test set-priority command changes extension priority."""

        runner = CliRunner()

        # Install extension with default priority
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Verify default priority
        assert manager.registry.get("test-ext")["priority"] == 10

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "test-ext", "5"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "priority changed: 10 → 5" in plain

        # Reload registry to see updated value
        manager2 = ExtensionManager(project_dir)
        assert manager2.registry.get("test-ext")["priority"] == 5

    def test_set_priority_same_value_no_change(self, extension_dir, project_dir):
        """Test set-priority with same value shows already set message."""

        runner = CliRunner()

        # Install extension with priority 5
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False, priority=5)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "test-ext", "5"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "already has priority 5" in plain

    def test_set_priority_repairs_corrupted_bool(self, extension_dir, project_dir):
        """A corrupted boolean priority must be repaired, not skipped.

        ``isinstance(True, int)`` is True and ``True == 1`` in Python, so a
        stored ``True`` priority would short-circuit the ``already has
        priority 1`` skip path and never get rewritten to a real int —
        contradicting the comment that promises corrupted values are
        repaired. The guard must exclude bools (like normalize_priority).
        """

        runner = CliRunner()

        manager = ExtensionManager(project_dir)
        manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False, priority=5
        )
        # Inject a corrupted boolean priority (True == 1).
        manager.registry.update("test-ext", {"priority": True})

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "test-ext", "1"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        # The corrupted bool must be repaired, not reported as already-set.
        assert "already has priority" not in plain
        assert "priority changed" in plain

        # The stored value is now a real int, not a bool.
        reloaded = ExtensionManager(project_dir).registry.get("test-ext")
        assert reloaded["priority"] == 1
        assert not isinstance(reloaded["priority"], bool)

    def test_set_priority_invalid_value(self, extension_dir, project_dir):
        """Test set-priority rejects invalid priority values."""

        runner = CliRunner()

        # Install extension
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "test-ext", "0"])

        assert result.exit_code == 1, result.output
        assert "Priority must be a positive integer" in result.output

    def test_set_priority_not_installed(self, project_dir):
        """Test set-priority fails for non-installed extension."""

        runner = CliRunner()

        # Ensure .specify exists
        (project_dir / ".specify").mkdir(parents=True, exist_ok=True)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "nonexistent", "5"])

        assert result.exit_code == 1, result.output
        assert "not installed" in result.output.lower() or "no extensions installed" in result.output.lower()

    def test_set_priority_by_display_name(self, extension_dir, project_dir):
        """Test set-priority works with extension display name."""

        runner = CliRunner()

        # Install extension
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Use display name "Test Extension" instead of ID "test-ext"
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "Test Extension", "3"])

        assert result.exit_code == 0, result.output
        assert "priority changed" in result.output

        # Reload registry to see updated value
        manager2 = ExtensionManager(project_dir)
        assert manager2.registry.get("test-ext")["priority"] == 3


class TestExtensionSetPriorityRecomposition:
    """Selector outputs must be recomposed when an extension is reprioritized.

    ``extension set-priority`` changes which lower-layer provider is the
    composition base for a regex selector preset, so the materialized
    command/skill artifact has to be rewritten — merely refreshing the
    registry or printing the new priority is not sufficient.
    """

    @pytest.mark.parametrize(
        "agent,skills,relative",
        [
            ("gemini", False, f".gemini/commands/{SHARED_COMMAND}.toml"),
            ("copilot", True, f".github/skills/{SHARED_SKILL}/SKILL.md"),
        ],
    )
    @pytest.mark.parametrize("strategy", ["append", "prepend"])
    def test_reprioritize_recomposes_selector_output(
        self, tmp_path, monkeypatch, agent, skills, relative, strategy
    ):
        root = tmp_path / "project"
        (root / ".specify").mkdir(parents=True)
        (root / ".gemini" / "commands").mkdir(parents=True)
        (root / ".github" / "agents").mkdir(parents=True)
        save_init_options(root, {"ai": agent, "ai_skills": skills, "script": "sh"})
        monkeypatch.chdir(root)

        manager = ExtensionManager(root)
        alpha_source = _provider_extension(
            tmp_path, "alpha", SHARED_COMMAND, "ALPHA BODY"
        )
        beta_source = _provider_extension(
            tmp_path,
            "beta",
            "speckit.beta.collect",
            "BETA BODY",
            shared_body="BETA BODY",
        )
        manager.install_from_directory(alpha_source, "0.1.5", priority=10)
        manager.install_from_directory(beta_source, "0.1.5", priority=20)
        PresetManager(root).install_from_directory(
            _selector_preset(tmp_path, strategy, "SELECTOR BODY"), "0.1.5", priority=5
        )

        output = root / relative
        text = output.read_text(encoding="utf-8")
        # alpha (priority 10) outranks beta (priority 20), so alpha is the
        # composition base and beta contributes nothing.
        assert "ALPHA BODY" in text
        assert "BETA BODY" not in text
        assert "SELECTOR BODY" in text

        # Demote alpha below beta through the real CLI command.
        result = CliRunner().invoke(app, ["extension", "set-priority", "alpha", "30"])
        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "priority changed: 10 → 30" in plain

        text = output.read_text(encoding="utf-8")
        # beta is now the highest-precedence extension: it must become the base
        # and alpha's stale fragment must be gone from the recomposed output.
        assert "BETA BODY" in text
        assert "ALPHA BODY" not in text
        assert "SELECTOR BODY" in text

        # The preset still owns the concrete command/skill after the switch.
        selector_meta = PresetManager(root).registry.get("selector")
        assert selector_meta is not None
        if skills:
            assert agent in selector_meta["registered_skills"]
            assert SHARED_SKILL in selector_meta["registered_skills"][agent]
        else:
            assert agent in selector_meta["registered_commands"]
            assert SHARED_COMMAND in selector_meta["registered_commands"][agent]

    def test_reprioritize_wrap_selector_recomposes(self, tmp_path, monkeypatch):
        """wrap strategy must re-insert the newly ordered lower-layer base."""

        root = tmp_path / "project"
        (root / ".specify").mkdir(parents=True)
        (root / ".gemini" / "commands").mkdir(parents=True)
        save_init_options(root, {"ai": "gemini", "ai_skills": False, "script": "sh"})
        monkeypatch.chdir(root)

        manager = ExtensionManager(root)
        alpha_source = _provider_extension(
            tmp_path, "alpha", SHARED_COMMAND, "ALPHA CORE"
        )
        beta_source = _provider_extension(
            tmp_path,
            "beta",
            "speckit.beta.collect",
            "BETA CORE",
            shared_body="BETA CORE",
        )
        manager.install_from_directory(alpha_source, "0.1.5", priority=10)
        manager.install_from_directory(beta_source, "0.1.5", priority=20)
        PresetManager(root).install_from_directory(
            _selector_preset(
                tmp_path, "wrap", "WRAPPER BEFORE\n{CORE_TEMPLATE}\nWRAPPER AFTER"
            ),
            "0.1.5",
            priority=5,
        )

        output = root / ".gemini" / "commands" / f"{SHARED_COMMAND}.toml"
        text = output.read_text(encoding="utf-8")
        assert "WRAPPER BEFORE" in text
        assert "ALPHA CORE" in text
        assert "BETA CORE" not in text

        result = CliRunner().invoke(app, ["extension", "set-priority", "alpha", "30"])
        assert result.exit_code == 0, result.output

        text = output.read_text(encoding="utf-8")
        assert "WRAPPER BEFORE" in text
        assert "WRAPPER AFTER" in text
        assert "BETA CORE" in text
        assert "ALPHA CORE" not in text
