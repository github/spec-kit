"""Pin the prompt contract for bundled bug-command lifecycle hooks."""

import re
from pathlib import Path

import pytest
import yaml

from specify_cli.extensions import ExtensionManifest, HookExecutor

ROOT = Path(__file__).resolve().parents[3]
EXT_DIR = ROOT / "extensions" / "bug"
COMMANDS = ("assess", "fix", "test")
EVENTS = tuple(f"{when}_bug_{command}" for command in COMMANDS for when in ("before", "after"))
PARSE_FAILURE = re.compile(r"^.*If the YAML cannot be parsed or is invalid.*$", re.MULTILINE)
REPORTED = (
    "could not be read",
    "include the parser error",
    "no hooks were checked",
    "including any mandatory (`optional: false`) hooks",
    "then continue",
)


@pytest.mark.parametrize("command", COMMANDS)
def test_hook_placement_and_context(command):
    text = (EXT_DIR / "commands" / f"speckit.bug.{command}.md").read_text(encoding="utf-8")
    before = f"`hooks.before_bug_{command}`"
    after = f"`hooks.after_bug_{command}`"
    assert before in text
    assert after in text
    assert text.index("## Prerequisites") < text.index(before) < text.index("## Execution")
    report = "assessment" if command == "assess" else command
    assert text.index(f"Write to `BUG_DIR/{report}.md`") < text.index(after) < text.index("**Report back**")
    pre_section = text.split("## Pre-Execution Checks", 1)[1].split("## Execution", 1)[0]
    post_section = text.split("## Mandatory Post-Execution Hooks", 1)[1].split("**Report back**", 1)[0]
    for section in (pre_section, post_section):
        assert "BUG_SLUG" in section
        assert "BUG_DIR" in section
    assert "written report" not in pre_section
    assert "written report" in post_section


@pytest.mark.parametrize("command", COMMANDS)
def test_hook_checks_preserve_core_semantics(command):
    text = (EXT_DIR / "commands" / f"speckit.bug.{command}.md").read_text(encoding="utf-8")
    assert "skip hook checking silently" not in text
    lines = PARSE_FAILURE.findall(text)
    assert len(lines) == 2
    for line in lines:
        for phrase in REPORTED:
            assert phrase in line
    for phrase in (
        "Check if `.specify/extensions.yml` exists in the project root.",
        "Filter out hooks where `enabled` is explicitly `false`",
        "Treat hooks without an `enabled` field as enabled by default",
        "If the hook defines a non-empty `condition`, skip the hook",
        "**Optional hook** (`optional: true`)",
        "**Mandatory hook** (`optional: false`)",
        "EXECUTE_COMMAND: {command}",
        "MUST actually invoke the hook and wait for it to finish before continuing",
        "Emitting the block alone does not run the hook",
    ):
        assert text.count(phrase) == 2, phrase
    assert "If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently" in text
    assert f"no hooks are registered under `hooks.after_bug_{command}`" in text


def test_extension_still_registers_no_hooks_of_its_own():
    manifest = yaml.safe_load((EXT_DIR / "extension.yml").read_text(encoding="utf-8"))
    assert "hooks" not in manifest


def test_assess_ensures_bug_directory_before_hook_checks():
    text = (EXT_DIR / "commands/speckit.bug.assess.md").read_text(encoding="utf-8")
    pre_section = text.split("## Pre-Execution Checks", 1)[1].split("## Execution", 1)[0]
    first_bullet = next(line for line in pre_section.splitlines() if line.startswith("- "))
    assert "Ensure `BUG_DIR` exists" in first_bullet
    assert "Prerequisites" in first_bullet
    assert "before checking hooks" in first_bullet


@pytest.mark.parametrize("path", [
    ROOT / "extensions/EXTENSION-API-REFERENCE.md",
    ROOT / "extensions/EXTENSION-DEVELOPMENT-GUIDE.md",
    ROOT / "extensions/EXTENSION-USER-GUIDE.md",
    EXT_DIR / "README.md",
])
def test_hook_events_documented(path):
    text = path.read_text(encoding="utf-8")
    for event in EVENTS:
        assert event in text


@pytest.mark.parametrize("event", EVENTS)
def test_bug_hook_event_names_are_accepted_and_registered(tmp_path, event):
    """Pin acceptance and registration of all six bug hook event names.

    Manifest validation has no event-name allow-list today. This guard passes
    on main, is not regression evidence, and never invokes a hook.
    """
    data = yaml.safe_load((EXT_DIR / "extension.yml").read_text(encoding="utf-8"))
    command = f"speckit.bug.{event.rsplit('_', 1)[1]}"
    data["hooks"] = {event: {"command": command, "optional": False}}
    path = tmp_path / "extension.yml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    manifest = ExtensionManifest(path)
    executor = HookExecutor(tmp_path)
    executor.register_hooks(manifest)
    hooks = executor.get_hooks_for_event(event)
    assert len(hooks) == 1
    assert hooks[0]["command"] == command
