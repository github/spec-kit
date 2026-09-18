"""Tests for ``provides.agents`` and ``provides.files`` in extension manifests.

An extension may ship subagent definitions and verbatim project files. On install they
land in the active integration's own directories (``.claude/agents/`` for Claude Code,
``.cursor/agents/`` for Cursor; ``{integration_folder}/…`` for files); on removal they
are deleted unless a person edited them since. An integration with no subagent lane
gets a note, not an error.
"""
import json
from pathlib import Path

import pytest
import yaml

from specify_cli.extensions import (
    ExtensionManager,
    ExtensionManifest,
    ValidationError,
    project_dest_violation,
)


def _init_options(project_root: Path, ai: str) -> None:
    (project_root / ".specify").mkdir(parents=True, exist_ok=True)
    (project_root / ".specify" / "init-options.json").write_text(
        json.dumps({"ai": ai, "ai_skills": True, "script": "sh"}), encoding="utf-8"
    )


def _extension(tmp: Path, ext_id: str = "tiered", *, with_agent=True, with_file=True) -> Path:
    ext = tmp / ext_id
    (ext / "agents").mkdir(parents=True)
    (ext / "workflows").mkdir()
    provides = {"commands": [{"name": f"speckit.{ext_id}.run", "file": "commands/run.md", "description": "run"}]}
    if with_agent:
        (ext / "agents" / "explorer.md").write_text(
            "---\nname: explorer\ndescription: Read-only exploration\nmodel: haiku\ntools: Read, Grep\n---\n\nMap the code.\n",
            encoding="utf-8",
        )
        provides["agents"] = [{"name": "explorer", "file": "agents/explorer.md", "description": "haiku explorer"}]
    if with_file:
        (ext / "workflows" / "panel.js").write_text("export const meta = { name: 'panel' }\nreturn 1\n", encoding="utf-8")
        provides["files"] = [
            {"name": "panel", "file": "workflows/panel.js", "dest": "{integration_folder}/workflows/panel.js", "description": "a Workflow script"},
        ]
    (ext / "commands").mkdir()
    (ext / "commands" / "run.md").write_text("---\ndescription: run\n---\n\nRun.\n", encoding="utf-8")
    (ext / "extension.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "extension": {"id": ext_id, "name": "Tiered", "version": "1.0.0", "description": "agents and files"},
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": provides,
            }
        ),
        encoding="utf-8",
    )
    return ext


def _manager(project_root: Path) -> ExtensionManager:
    (project_root / ".specify" / "extensions").mkdir(parents=True, exist_ok=True)
    return ExtensionManager(project_root)


def test_manifest_accepts_agents_and_files_and_rejects_bad_destinations(tmp_path):
    ext = _extension(tmp_path)
    manifest = ExtensionManifest(ext / "extension.yml")
    assert [a["name"] for a in manifest.agents] == ["explorer"]
    assert [f["dest"] for f in manifest.files] == ["{integration_folder}/workflows/panel.js"]

    assert project_dest_violation(".claude/workflows/x.js") is None
    assert project_dest_violation("{integration_folder}/workflows/x.js") is None
    assert project_dest_violation("/abs/x.js")
    assert project_dest_violation("../x.js")
    assert project_dest_violation(".specify/extensions/x/y.js")
    assert project_dest_violation("a/{integration_folder}/x.js")

    data = yaml.safe_load((ext / "extension.yml").read_text())
    data["provides"]["files"][0]["dest"] = "../escape.js"
    (ext / "extension.yml").write_text(yaml.safe_dump(data))
    with pytest.raises(ValidationError, match="dest"):
        ExtensionManifest(ext / "extension.yml")


def test_install_places_agent_and_file_for_claude_and_remove_cleans_them(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    _init_options(project, "claude")
    ext = _extension(tmp_path)
    manager = _manager(project)
    manager.install_from_directory(ext, "1.0.0", register_commands=False)

    agent = project / ".claude" / "agents" / "explorer.md"
    workflow = project / ".claude" / "workflows" / "panel.js"
    assert agent.read_text(encoding="utf-8").startswith("---\nname: explorer")
    assert workflow.read_text(encoding="utf-8").startswith("export const meta")

    meta = manager.registry.get("tiered")
    assert set(meta["registered_agents"]) == {".claude/agents/explorer.md"}
    assert set(meta["registered_files"]) == {".claude/workflows/panel.js"}

    assert manager.remove("tiered") is True
    assert not agent.exists()
    assert not workflow.exists()


def test_a_locally_edited_file_is_never_overwritten_or_deleted(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    _init_options(project, "claude")
    ext = _extension(tmp_path)
    manager = _manager(project)
    manager.install_from_directory(ext, "1.0.0", register_commands=False)
    agent = project / ".claude" / "agents" / "explorer.md"
    agent.write_text(agent.read_text(encoding="utf-8") + "\nA local tweak.\n", encoding="utf-8")

    # reinstall (--force) keeps the person's edit
    manager.install_from_directory(ext, "1.0.0", register_commands=False, force=True)
    assert "A local tweak." in agent.read_text(encoding="utf-8")

    # removal leaves it in place too
    manager.remove("tiered")
    assert agent.exists()
    assert not (project / ".claude" / "workflows" / "panel.js").exists(), "the untouched file is gone"


def test_cursor_gets_its_own_agents_dir_and_codex_gets_files_only(tmp_path):
    project = tmp_path / "cursor"
    project.mkdir()
    _init_options(project, "cursor-agent")
    manager = _manager(project)
    manager.install_from_directory(_extension(tmp_path / "a"), "1.0.0", register_commands=False)
    assert (project / ".cursor" / "agents" / "explorer.md").is_file()
    assert (project / ".cursor" / "workflows" / "panel.js").is_file()

    project2 = tmp_path / "codex"
    project2.mkdir()
    _init_options(project2, "codex")
    manager2 = _manager(project2)
    manager2.install_from_directory(_extension(tmp_path / "b"), "1.0.0", register_commands=False)
    assert manager2.registry.get("tiered")["registered_agents"] == {}
    assert (project2 / ".agents" / "workflows" / "panel.js").is_file()


def test_an_extension_of_only_agents_and_files_is_valid(tmp_path):
    ext = _extension(tmp_path)
    data = yaml.safe_load((ext / "extension.yml").read_text())
    del data["provides"]["commands"]
    (ext / "extension.yml").write_text(yaml.safe_dump(data))
    manifest = ExtensionManifest(ext / "extension.yml")
    assert manifest.commands == []
    assert manifest.agents and manifest.files
