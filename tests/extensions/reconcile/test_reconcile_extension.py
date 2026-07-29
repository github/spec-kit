"""Tests for the bundled ``reconcile`` extension."""

from __future__ import annotations

import json
from pathlib import Path
import tomllib

import yaml

from specify_cli import _locate_bundled_extension


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "reconcile"

EXPECTED_COMMANDS = {
    "speckit.reconcile.intent",
    "speckit.reconcile.decisions",
}


class TestExtensionLayout:
    def test_manifest_declares_focused_mandatory_hooks(self):
        manifest = yaml.safe_load(
            (EXT_DIR / "extension.yml").read_text(encoding="utf-8")
        )

        assert manifest["extension"]["id"] == "reconcile"
        assert manifest["extension"]["name"] == "Intent Reconciliation"
        assert manifest["extension"]["author"] == "spec-kit-core"
        assert {
            command["name"] for command in manifest["provides"]["commands"]
        } == EXPECTED_COMMANDS
        assert manifest["hooks"] == {
            "before_implement": {
                "command": "speckit.reconcile.intent",
                "priority": 1,
                "optional": False,
                "description": "Confirm approved intent and resolve pending decisions before implementation",
            },
            "after_implement": {
                "command": "speckit.reconcile.decisions",
                "priority": 1,
                "optional": False,
                "description": "Capture and reconcile decisions discovered during implementation",
            },
        }

    def test_documentation_and_commands_exist(self):
        assert (EXT_DIR / "README.md").is_file()
        for name in EXPECTED_COMMANDS:
            assert (EXT_DIR / "commands" / f"{name}.md").is_file()

    def test_decision_command_enforces_authority_boundary(self):
        text = (
            EXT_DIR / "commands" / "speckit.reconcile.decisions.md"
        ).read_text(encoding="utf-8")

        assert "Implementation is **evidence, not authority**" in text
        assert "`decisions.md` is append-only" in text
        assert "Never infer approval" in text
        assert all(
            classification in text
            for classification in (
                "implementation-defect",
                "contract-discovery",
                "design-decision",
                "intent-change",
                "accidental-divergence",
            )
        )


class TestCatalogEntry:
    def test_catalog_lists_reconcile_as_bundled(self):
        catalog = json.loads(
            (PROJECT_ROOT / "extensions" / "catalog.json").read_text(encoding="utf-8")
        )
        entry = catalog["extensions"]["reconcile"]
        assert entry["bundled"] is True
        assert entry["id"] == "reconcile"
        assert entry["author"] == "spec-kit-core"


class TestBundleResolution:
    def test_locate_bundled_extension_finds_reconcile(self):
        located = _locate_bundled_extension("reconcile")
        assert located is not None
        assert (located / "extension.yml").is_file()

    def test_wheel_force_includes_reconcile(self):
        with (PROJECT_ROOT / "pyproject.toml").open("rb") as pyproject_file:
            pyproject = tomllib.load(pyproject_file)

        force_include = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"][
            "force-include"
        ]
        assert force_include["extensions/reconcile"] == (
            "specify_cli/core_pack/extensions/reconcile"
        )


class TestExtensionInstall:
    def test_install_from_directory_includes_commands_and_hooks(self, tmp_path: Path):
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manifest = manager.install_from_directory(
            EXT_DIR, "0.12.0", register_commands=False
        )

        assert manifest.id == "reconcile"
        assert manager.registry.is_installed("reconcile")
        assert {command["name"] for command in manifest.commands} == EXPECTED_COMMANDS
        assert set(manifest.hooks) == {"before_implement", "after_implement"}

        installed = tmp_path / ".specify" / "extensions" / "reconcile"
        for name in EXPECTED_COMMANDS:
            assert (installed / "commands" / f"{name}.md").is_file()

    def test_reconciliation_precedes_default_priority_hooks(self, tmp_path: Path):
        from specify_cli.extensions import ExtensionManager, HookExecutor

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manager.install_from_directory(
            PROJECT_ROOT / "extensions" / "git",
            "0.12.0",
            register_commands=False,
        )
        manager.install_from_directory(
            EXT_DIR,
            "0.12.0",
            register_commands=False,
        )

        hooks = HookExecutor(tmp_path).get_hooks_for_event("after_implement")
        assert hooks[0]["command"] == "speckit.reconcile.decisions"
        assert hooks[0]["priority"] == 1
