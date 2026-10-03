from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.presets import PresetManager, PresetRegistry
from tests.conftest import strip_ansi


def _write_selector_preset(
    project_dir: Path, preset_id: str, templates: list[dict]
) -> Path:
    preset_dir = project_dir / ".specify" / "presets" / preset_id
    preset_dir.mkdir(parents=True)
    for template in templates:
        payload = preset_dir / template["file"]
        payload.parent.mkdir(parents=True, exist_ok=True)
        payload.write_text("# selector fixture\n", encoding="utf-8")
    manifest = {
        "schema_version": "1.0",
        "preset": {
            "id": preset_id,
            "name": preset_id,
            "version": "1.0.0",
            "description": "diagnostic fixture",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {"templates": templates},
    }
    (preset_dir / "preset.yml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    PresetRegistry(project_dir / ".specify" / "presets").add(
        preset_id, {"enabled": True, "priority": 1, "version": "1.0.0"}
    )
    return preset_dir


def _info(project_dir: Path, preset_id: str) -> str:
    from unittest.mock import patch

    with patch.object(Path, "cwd", return_value=project_dir):
        result = CliRunner().invoke(app, ["preset", "info", preset_id])
    assert result.exit_code == 0, result.output
    return strip_ansi(result.output)


def test_preset_info_shows_regex_template_and_script_matches(project_dir):
    # Core files are the concrete lower-layer resources for both declarations.
    (project_dir / ".specify" / "templates" / "plan-template.md").write_text(
        "# Core plan\n", encoding="utf-8"
    )
    scripts = project_dir / ".specify" / "templates" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "check-prerequisites.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    preset_dir = _write_selector_preset(
        project_dir,
        "diagnostic-selectors",
        [
            {
                "type": "template",
                "name": r"regex:^plan-.*$",
                "file": "templates/overlay.md",
                "strategy": "append",
            },
            {
                "type": "script",
                "name": r"regex:^check-.*$",
                "file": "scripts/overlay.sh",
                "strategy": "wrap",
            },
        ],
    )

    output = _info(project_dir, preset_dir.name)

    assert r"regex:^plan-.*$" in output
    assert "plan-template" in output
    assert r"regex:^check-.*$" in output
    assert "check-prerequisites" in output
    assert "No current matches" not in output


def test_preset_info_reports_unmatched_regex_selector(project_dir):
    preset_dir = _write_selector_preset(
        project_dir,
        "empty-diagnostic-selector",
        [
            {
                "type": "template",
                "name": r"regex:^nothing-matches$",
                "file": "templates/overlay.md",
                "strategy": "append",
            }
        ],
    )

    output = _info(project_dir, preset_dir.name)

    assert r"regex:^nothing-matches$" in output
    assert "No current matches" in output


def test_preset_info_expands_regex_command_to_concrete_names(project_dir):
    preset_dir = _write_selector_preset(
        project_dir,
        "command-diagnostic-selector",
        [
            {
                "type": "command",
                "name": r"regex:^speckit\.(plan|tasks)$",
                "file": "commands/override.md",
                "strategy": "replace",
            }
        ],
    )

    output = _info(project_dir, preset_dir.name)

    assert r"regex:^speckit\.(plan|tasks)$" in output
    assert "speckit.plan" in output
    assert "speckit.tasks" in output
    assert "No current matches" not in output


def test_install_regex_commands_registers_concrete_ai_skills(project_dir):
    from specify_cli import save_init_options

    (project_dir / ".claude" / "skills").mkdir(parents=True)
    save_init_options(
        project_dir,
        {"ai": "claude", "ai_skills": True, "script": "sh"},
    )
    source_dir = project_dir / "source"
    source_dir.mkdir()
    source = source_dir / "skill-selector"
    source.mkdir()
    (source / "commands").mkdir()
    (source / "commands" / "override.md").write_text(
        "---\ndescription: Preset override\n---\n\nConcrete selector skill.\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": "1.0",
        "preset": {
            "id": "skill-selector",
            "name": "Skill selector",
            "version": "1.0.0",
            "description": "AI skills selector fixture",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {
            "templates": [
                {
                    "type": "command",
                    "name": r"regex:^speckit\.(plan|tasks)$",
                    "file": "commands/override.md",
                    "strategy": "replace",
                }
            ]
        },
    }
    (source / "preset.yml").write_text(yaml.safe_dump(manifest), encoding="utf-8")

    manager = PresetManager(project_dir)
    installed = manager.install_from_directory(source, "0.1.0")

    metadata = manager.registry.get(installed.id)
    assert metadata is not None
    assert metadata["registered_commands"]
    skill_names = {
        name for names in metadata["registered_skills"].values() for name in names
    }
    assert skill_names == {"speckit-plan", "speckit-tasks"}
    for skill_name in skill_names:
        skill_file = project_dir / ".claude" / "skills" / skill_name / "SKILL.md"
        assert skill_file.is_file()
        assert "Concrete selector skill." in skill_file.read_text(encoding="utf-8")
    assert all(
        not name.startswith("regex:")
        for names in metadata["registered_commands"].values()
        for name in names
    )
