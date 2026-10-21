"""Contracts for opt-in issue tracking after removal from core."""

from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / "templates/commands/taskstoissues.md"
EXTENSION = ROOT / "extensions/github/commands/speckit.github.taskstoissues.md"


def test_core_template_is_removed():
    assert not CORE.exists()


def test_extension_frontmatter_preserves_execution_metadata():
    metadata = yaml.safe_load(EXTENSION.read_text(encoding="utf-8").split("---", 2)[1])
    assert metadata["tools"] == [
        "github/github-mcp-server/list_issues",
        "github/github-mcp-server/issue_write",
    ]
    assert metadata["scripts"] == {
        "sh": "scripts/bash/resolve-tasks.sh --json",
        "ps": "scripts/powershell/resolve-tasks.ps1 -Json",
        "py": "scripts/python/resolve_tasks.py --json",
    }


def test_recommended_extension_is_not_deprecated():
    text = EXTENSION.read_text(encoding="utf-8")
    assert "## Deprecation Notice" not in text
    assert "future minor release" not in text
    assert not yaml.safe_load(text.split("---", 2)[1])["description"].startswith("Deprecated:")


def test_taskstoissues_hooks_and_safety_contracts_remain():
    text = EXTENSION.read_text(encoding="utf-8")
    assert "hooks.before_taskstoissues" in text
    assert "hooks.after_taskstoissues" in text
    assert "ONLY PROCEED TO NEXT STEPS IF THE REMOTE IS A GITHUB URL" in text
    assert "**Fetch existing issues for deduplication**" in text
    assert "**Skip** any task whose ID is already present" in text
    assert "Only create issues for tasks that do not yet have a matching issue." in text
    assert "UNDER NO CIRCUMSTANCES EVER CREATE ISSUES IN REPOSITORIES THAT DO NOT MATCH THE REMOTE URL" in text


@pytest.mark.parametrize(
    "integration_key", ["opencode", "agy", "claude", "copilot", "gemini", "goose"],
)
def test_fresh_integration_has_no_issue_tracking(tmp_path, integration_key):
    from specify_cli.integrations import get_integration
    from specify_cli.integrations.manifest import IntegrationManifest

    integration = get_integration(integration_key)
    created = integration.setup(
        tmp_path, IntegrationManifest(integration_key, tmp_path), script_type="sh"
    )
    assert created
    assert not any("taskstoissues" in path.as_posix() for path in created)
    assert not (tmp_path / ".specify/extensions/github").exists()


def test_core_inventories_release_the_legacy_name():
    from specify_cli import SKILL_DESCRIPTIONS
    from specify_cli.extensions import CORE_COMMAND_NAMES, _FALLBACK_CORE_COMMAND_NAMES
    from specify_cli.integrations.base import _CORE_COMMAND_TEMPLATE_ORDER
    from specify_cli.integrations.copilot import _COPILOT_CORE_COMMANDS
    from specify_cli.integrations.claude import ARGUMENT_HINTS as claude_hints
    from specify_cli.integrations.alquimia import ARGUMENT_HINTS as alquimia_hints

    for inventory in (
        SKILL_DESCRIPTIONS, CORE_COMMAND_NAMES, _FALLBACK_CORE_COMMAND_NAMES,
        _CORE_COMMAND_TEMPLATE_ORDER, _COPILOT_CORE_COMMANDS,
        claude_hints, alquimia_hints,
    ):
        assert "taskstoissues" not in inventory


def test_legacy_alias_is_not_installed_by_the_extension():
    text = EXTENSION.read_text(encoding="utf-8")
    manifest = yaml.safe_load((ROOT / "extensions/github/extension.yml").read_text(encoding="utf-8"))
    assert "## Compatibility Alias" not in text
    assert "__SPECKIT_COMMAND_TASKSTOISSUES__" not in text
    assert all(not command.get("aliases") for command in manifest["provides"]["commands"])
