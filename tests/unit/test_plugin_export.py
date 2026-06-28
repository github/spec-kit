"""Unit tests for the speckit→adg plugin producer."""
from __future__ import annotations

import json

import pytest

from specify_cli.plugin_export import build_plugin, produce_core_skills, to_semver

CORE_SKILLS = {
    "speckit-analyze",
    "speckit-checklist",
    "speckit-clarify",
    "speckit-constitution",
    "speckit-converge",
    "speckit-implement",
    "speckit-plan",
    "speckit-specify",
    "speckit-tasks",
    "speckit-taskstoissues",
}


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("0.11.4", "0.11.4"),
        ("0.11.4.dev0", "0.11.4-dev0"),
        ("1.2.3-rc.1", "1.2.3-rc.1"),
        ("1.0.0.post2", "1.0.0-post2"),
        ("not-a-version", "0.0.0"),
    ],
)
def test_to_semver(raw, expected):
    assert to_semver(raw) == expected


def test_produce_core_skills(tmp_path):
    skills_dir = produce_core_skills(tmp_path, "sh")
    assert skills_dir == (tmp_path / "skills")
    names = {p.name for p in skills_dir.iterdir() if p.is_dir()}
    assert names == CORE_SKILLS
    for name in names:
        assert (skills_dir / name / "SKILL.md").is_file()


def test_skill_content_is_project_relative_not_plugin_root(tmp_path):
    skills_dir = produce_core_skills(tmp_path, "sh")
    txt = (skills_dir / "speckit-plan" / "SKILL.md").read_text(encoding="utf-8")
    # Skills keep referencing the project's .specify/ — NOT a plugin root.
    assert ".specify/scripts" in txt
    assert "CLAUDE_PLUGIN_ROOT" not in txt
    assert "SPECKIT_PLUGIN_ROOT" not in txt
    # Claude post-processing ran (skills frontmatter injected).
    assert "user-invocable" in txt


def test_plugin_passes_upstream_skill_names_through(tmp_path):
    # The producer must NOT rewrite the upstream skill name/content contract.
    skills_dir = produce_core_skills(tmp_path, "sh")
    md = (skills_dir / "speckit-specify" / "SKILL.md").read_text(encoding="utf-8")
    assert 'name: "speckit-specify"' in md


def test_build_plugin_full_tree(tmp_path):
    out = build_plugin(tmp_path / "speckit-plugin", "sh")
    manifest = json.loads((out / ".agents" / ".plugin.json").read_text())
    assert manifest["schemaVersion"] == "adg.plugin/v1"
    assert manifest["name"] == "speckit"
    assert manifest["skills"] == "./skills/"
    assert manifest["hooks"] == "./hooks/"
    # semver-valid version
    assert to_semver(manifest["version"]) == manifest["version"]

    # One base hook in Claude's native format; adg routes it to each runtime.
    hooks = json.loads((out / "hooks" / "hooks.json").read_text())
    assert "UserPromptExpansion" in hooks["hooks"]
    cmd = hooks["hooks"]["UserPromptExpansion"][0]["hooks"][0]["command"]
    assert "${CLAUDE_PLUGIN_ROOT}/hooks/ensure-specify.sh" in cmd
    assert not (out / ".agents" / "hooks.json").exists()  # no retired adg DSL

    hook = out / "hooks" / "ensure-specify.sh"
    assert hook.is_file()
    import sys
    if sys.platform != "win32":
        assert hook.stat().st_mode & 0o111  # executable bit preserved

    names = {p.name for p in (out / "skills").iterdir() if p.is_dir()}
    assert names == CORE_SKILLS


def test_build_plugin_without_hook(tmp_path):
    out = build_plugin(tmp_path / "p", "sh", include_hook=False)
    manifest = json.loads((out / ".agents" / ".plugin.json").read_text())
    assert "hooks" not in manifest
    assert not (out / "hooks").exists()
