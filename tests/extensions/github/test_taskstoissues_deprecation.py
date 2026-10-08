"""Text contracts for the core command's deprecation transition."""

from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / "templates/commands/taskstoissues.md"
EXTENSION = ROOT / "extensions/github/commands/speckit.github.taskstoissues.md"


def test_core_deprecation_warning_and_continuation():
    text = CORE.read_text(encoding="utf-8")
    assert "## Deprecation Notice" in text
    assert "## Pre-Execution Checks" in text
    notice = text.split("## Deprecation Notice\n", 1)[1].split("## User Input", 1)[0]
    assert text.index("## Deprecation Notice") < text.index("## User Input") < text.index("## Pre-Execution Checks")
    for phrase in (
        "MUST display the following concise warning before doing anything else",
        "`__SPECKIT_COMMAND_TASKSTOISSUES__` is deprecated",
        "will be removed in a future minor release",
        "bundled `github` extension",
        "specify extension add github",
        "__SPECKIT_COMMAND_GITHUB_TASKSTOISSUES__",
        "Continue with the existing workflow unchanged",
        "Do not install or enable the extension automatically",
        "do not stop",
        "do not run the replacement command",
    ):
        assert phrase in notice


def test_core_frontmatter_preserves_execution_metadata():
    metadata = yaml.safe_load(CORE.read_text(encoding="utf-8").split("---", 2)[1])
    assert metadata["description"].startswith("Deprecated: ")
    assert metadata["tools"] == [
        "github/github-mcp-server/list_issues",
        "github/github-mcp-server/issue_write",
    ]
    assert metadata["scripts"] == {
        "sh": "scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks",
        "ps": "scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks",
        "py": "scripts/python/check_prerequisites.py --json --require-tasks --include-tasks",
    }


def test_recommended_extension_is_not_deprecated():
    text = EXTENSION.read_text(encoding="utf-8")
    assert "## Deprecation Notice" not in text
    assert "future minor release" not in text
    assert not yaml.safe_load(text.split("---", 2)[1])["description"].startswith("Deprecated:")


@pytest.mark.parametrize("command", [CORE, EXTENSION], ids=["core", "github"])
def test_taskstoissues_hooks_and_safety_contracts_remain(command):
    text = command.read_text(encoding="utf-8")
    assert "hooks.before_taskstoissues" in text
    assert "hooks.after_taskstoissues" in text
    assert "ONLY PROCEED TO NEXT STEPS IF THE REMOTE IS A GITHUB URL" in text
    assert "**Fetch existing issues for deduplication**" in text
    assert "**Skip** any task whose ID is already present" in text
    assert "Only create issues for tasks that do not yet have a matching issue." in text
    assert "UNDER NO CIRCUMSTANCES EVER CREATE ISSUES IN REPOSITORIES THAT DO NOT MATCH THE REMOTE URL" in text


@pytest.mark.parametrize(
    ("integration_key", "core_invocation", "replacement_invocation"),
    [
        ("opencode", "/speckit.taskstoissues", "/speckit.github.taskstoissues"),
        ("agy", "/speckit-taskstoissues", "/speckit-github-taskstoissues"),
    ],
)
def test_rendered_core_warning_uses_integration_invocations(
    tmp_path, integration_key, core_invocation, replacement_invocation
):
    from specify_cli.integrations import get_integration
    from specify_cli.integrations.manifest import IntegrationManifest

    integration = get_integration(integration_key)
    created = integration.setup(
        tmp_path, IntegrationManifest(integration_key, tmp_path), script_type="sh"
    )
    command = next(
        path for path in created
        if path.name == "speckit.taskstoissues.md"
        or path.parent.name == "speckit-taskstoissues"
    )
    text = command.read_text(encoding="utf-8")
    assert "## Deprecation Notice" in text
    assert "## Pre-Execution Checks" in text
    notice = text.split("## Deprecation Notice", 1)[1].split("## User Input", 1)[0]
    assert f"`{core_invocation}` is deprecated" in notice
    assert f"invoke `{replacement_invocation}`" in notice
    assert "__SPECKIT_COMMAND_" not in notice
    assert "specify extension add github" in notice
    assert not (tmp_path / ".specify/extensions/github").exists()
