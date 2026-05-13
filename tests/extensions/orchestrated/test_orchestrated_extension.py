"""Tests for the bundled orchestrated extension."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_orchestrated_manifest_validates():
    from specify_cli.extensions import ExtensionManifest

    manifest = ExtensionManifest(
        PROJECT_ROOT / "extensions" / "orchestrated" / "extension.yml"
    )

    assert manifest.id == "orchestrated"
    assert [cmd["name"] for cmd in manifest.commands] == [
        "speckit.orchestrated.implement"
    ]


def test_orchestrated_command_invokes_workflow():
    command_path = (
        PROJECT_ROOT
        / "extensions"
        / "orchestrated"
        / "commands"
        / "speckit.orchestrated.implement.md"
    )

    content = command_path.read_text(encoding="utf-8")
    assert "specify workflow run speckit-orchestrated-implement" in content
    assert "-i integration=__AGENT__" in content
    assert '-i args="$ARGUMENTS"' in content


def test_orchestrated_command_registers_for_markdown_agent(tmp_path):
    from specify_cli.extensions import ExtensionManager

    project = tmp_path / "project"
    project.mkdir()
    (project / ".windsurf" / "workflows").mkdir(parents=True)

    manager = ExtensionManager(project)
    manager.install_from_directory(
        PROJECT_ROOT / "extensions" / "orchestrated",
        "0.8.9",
    )

    command_file = (
        project
        / ".windsurf"
        / "workflows"
        / "speckit.orchestrated.implement.md"
    )
    assert command_file.exists()
    content = command_file.read_text(encoding="utf-8")
    assert "specify workflow run speckit-orchestrated-implement" in content
    assert "__AGENT__" not in content
    assert "-i integration=windsurf" in content
