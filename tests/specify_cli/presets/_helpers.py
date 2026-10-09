"""Shared helpers for preset domain and command tests."""

from __future__ import annotations

import json
import warnings
from datetime import UTC, datetime
from pathlib import Path

import yaml

from specify_cli.presets import (
    PresetCatalog,
    PresetCatalogEntry,
    PresetManager,
    PresetManifest,
)

REPO_ROOT = Path(__file__).parents[3]
SELF_TEST_PRESET_DIR = REPO_ROOT / "presets" / "self-test"
CONSTITUTION_SYNC_PRESET_DIR = REPO_ROOT / "presets" / "constitution-sync"
SELF_TEST_WRAP_WARNING = (
    r"Cannot compose command 'speckit\.wrap-test': no base layer\. "
    r"Stale command files may remain\."
)

CORE_TEMPLATE_NAMES = [
    "spec-template",
    "plan-template",
    "tasks-template",
    "checklist-template",
    "constitution-template",
]


def seed_catalog(
    project_dir: Path,
    tags: object,
    extra: dict[str, object] | None = None,
) -> PresetCatalog:
    """Seed cached catalog metadata used by search and info command tests."""
    catalog = PresetCatalog(project_dir)
    catalog.cache_dir.mkdir(parents=True, exist_ok=True)
    pack = {
        "name": "Numeric Tags",
        "description": "Preset with non-string tags",
        "version": "1.0.0",
        "tags": tags,
    }
    if extra:
        pack.update(extra)
    catalog.cache_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "presets": {"numeric-tags": pack},
            }
        )
    )
    catalog.cache_metadata_file.write_text(
        json.dumps({"cached_at": datetime.now(UTC).isoformat()})
    )
    return catalog


def default_catalog_entries(catalog: PresetCatalog) -> list[PresetCatalogEntry]:
    """Return the default catalog as the only active catalog."""
    return [
        PresetCatalogEntry(
            url=catalog.DEFAULT_CATALOG_URL,
            name="default",
            priority=1,
            install_allowed=True,
        )
    ]


def install_self_test_preset(
    manager: PresetManager, speckit_version: str = "0.1.5"
) -> PresetManifest:
    """Install self-test while filtering its intentionally missing wrap base."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=SELF_TEST_WRAP_WARNING,
            category=UserWarning,
            module=r"specify_cli\.presets",
        )
        return manager.install_from_directory(SELF_TEST_PRESET_DIR, speckit_version)


def install_constitution_sync_preset(manager: PresetManager) -> PresetManifest:
    """Enable guarded install-time constitution materialization."""
    return manager.install_from_directory(CONSTITUTION_SYNC_PRESET_DIR, "0.15.0")


def make_convention_constitution_preset(temp_dir: Path) -> Path:
    """Create a preset whose constitution is found by convention."""
    preset_dir = temp_dir / "convention-constitution"
    (preset_dir / "templates").mkdir(parents=True)
    (preset_dir / "templates" / "constitution-template.md").write_text(
        "# Convention Constitution\n"
    )
    (preset_dir / "templates" / "spec-template.md").write_text("# Spec\n")
    (preset_dir / "preset.yml").write_text(
        yaml.dump(
            {
                "schema_version": "1.0",
                "preset": {
                    "id": "convention-constitution",
                    "name": "Convention Constitution",
                    "version": "1.0.0",
                    "description": "Convention-based constitution for testing",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "templates": [
                        {
                            "type": "template",
                            "name": "spec-template",
                            "file": "templates/spec-template.md",
                        }
                    ]
                },
            }
        )
    )
    return preset_dir


class PresetArtifactTestHelpers:
    """Shared setup for preset command, skill, and lifecycle tests."""

    def _write_init_options(self, project_dir, ai="claude", ai_skills=True, script="sh"):
        from specify_cli import save_init_options

        save_init_options(project_dir, {"ai": ai, "ai_skills": ai_skills, "script": script})

    def _create_skill(self, skills_dir, skill_name, body="original body"):
        skill_dir = skills_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {skill_name}\n---\n\n{body}\n"
        )
        return skill_dir

    def _create_command_preset(self, temp_dir, preset_id, command_name, description, body):
        preset_dir = temp_dir / preset_id
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        # A regex selector is a legal manifest name but not a legal file name on
        # every platform (Windows rejects ':' in paths), so sanitize the on-disk
        # file name while leaving the declared name untouched.
        safe_name = "".join(
            ch if (ch.isalnum() or ch in "._-") else "_" for ch in command_name
        ) or "command"
        command_file = f"{safe_name}.md"
        (preset_dir / "commands" / command_file).write_text(
            f"---\ndescription: {description}\n---\n\n{body}\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": preset_id,
                "name": preset_id,
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": command_name,
                        "file": f"commands/{command_file}",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)
        return preset_dir

    def _create_multi_command_preset(self, temp_dir, preset_id, command_names):
        """Install-directory helper for a preset with more than one command.

        Used to prove partial-result handling: a command's own template
        entry can genuinely be skipped by registration (missing source
        file, safety-validation rejection) while sibling commands in the
        same preset still succeed.
        """
        preset_dir = temp_dir / preset_id
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        templates = []
        for command_name in command_names:
            safe_name = "".join(
                ch if (ch.isalnum() or ch in "._-") else "_" for ch in command_name
            ) or "command"
            command_file = f"{safe_name}.md"
            (preset_dir / "commands" / command_file).write_text(
                f"---\ndescription: {command_name} test command\n---\n\n"
                f"{command_name} body\n"
            )
            templates.append({
                "type": "command",
                "name": command_name,
                "file": f"commands/{command_file}",
            })
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": preset_id,
                "name": preset_id,
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {"templates": templates},
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)
        return preset_dir

    def _create_multi_command_preset_with_aliases(self, temp_dir, preset_id, command_specs):
        """Install-directory helper for a preset whose commands carry aliases.

        ``command_specs`` is a list of ``(primary_name, [alias, ...])``
        tuples. Each command gets its own source file (aliases share the
        same source/content as their primary — CommandRegistrar renders
        them from the same command file, just under a different output
        name (#2948)).
        """
        preset_dir = temp_dir / preset_id
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        templates = []
        for primary_name, aliases in command_specs:
            # Same platform rule as _create_command_preset: a regex selector is a
            # legal manifest name but not a legal Windows file name (':' and '*'
            # are rejected), so sanitize the on-disk name only.
            safe_name = "".join(
                ch if (ch.isalnum() or ch in "._-") else "_" for ch in primary_name
            ) or "command"
            command_file = f"{safe_name}.md"
            (preset_dir / "commands" / command_file).write_text(
                f"---\ndescription: {primary_name} test command\n---\n\n"
                f"{primary_name} body\n",
                encoding="utf-8",
            )
            templates.append({
                "type": "command",
                "name": primary_name,
                "file": f"commands/{command_file}",
                "aliases": list(aliases),
            })
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": preset_id,
                "name": preset_id,
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {"templates": templates},
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)
        return preset_dir
