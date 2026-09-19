"""Shared helpers for preset domain and command tests."""

from __future__ import annotations

import warnings
from pathlib import Path

import yaml

from specify_cli.presets import PresetManager, PresetManifest

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
