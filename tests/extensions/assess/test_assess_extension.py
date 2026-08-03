"""Tests for the bundled ``assess`` extension.

Validates:
- Bundled layout (manifest, README, five command files)
- Catalog registration
- Wheel/source-checkout resolution via ``_locate_bundled_extension``
- Install via ``ExtensionManager.install_from_directory`` copies the five
  command files and records them in the installed manifest (command
  registration with AI agents is exercised separately and not asserted here)
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from specify_cli import _locate_bundled_extension


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "assess"

EXPECTED_COMMANDS = {
    "speckit.assess.intake",
    "speckit.assess.research",
    "speckit.assess.define",
    "speckit.assess.shape",
    "speckit.assess.decide",
}


# ── Bundled extension layout ─────────────────────────────────────────────────


class TestExtensionLayout:
    def test_extension_yml_exists(self):
        assert (EXT_DIR / "extension.yml").is_file()

    def test_extension_yml_has_required_fields(self):
        manifest = yaml.safe_load(
            (EXT_DIR / "extension.yml").read_text(encoding="utf-8")
        )
        assert manifest["extension"]["id"] == "assess"
        assert manifest["extension"]["name"] == "Idea Assessment Pipeline"
        assert manifest["extension"]["author"] == "spec-kit-core"
        commands = {c["name"] for c in manifest["provides"]["commands"]}
        assert commands == EXPECTED_COMMANDS

    def test_declares_no_hooks(self):
        """assess is a standalone pipeline: it must not register lifecycle
        hooks (e.g. before_specify). Discovery and specification stay
        separate processes; the only coupling is the forward decide ->
        /speckit.specify handoff described in the commands."""
        manifest = yaml.safe_load(
            (EXT_DIR / "extension.yml").read_text(encoding="utf-8")
        )
        assert "hooks" not in manifest or not manifest["hooks"]

    def test_readme_exists(self):
        readme = EXT_DIR / "README.md"
        assert readme.is_file()
        text = readme.read_text(encoding="utf-8")
        assert "Idea Assessment Pipeline Extension" in text

    def test_command_files_exist(self):
        for name in EXPECTED_COMMANDS:
            cmd = EXT_DIR / "commands" / f"{name}.md"
            assert cmd.is_file(), f"Missing command file: {cmd}"


# ── Catalog registration ─────────────────────────────────────────────────────


class TestCatalogEntry:
    def test_catalog_lists_assess_as_bundled(self):
        catalog = json.loads(
            (PROJECT_ROOT / "extensions" / "catalog.json").read_text(encoding="utf-8")
        )
        entry = catalog["extensions"]["assess"]
        assert entry["bundled"] is True
        assert entry["id"] == "assess"
        assert entry["author"] == "spec-kit-core"


# ── Bundle resolution ────────────────────────────────────────────────────────


class TestBundleResolution:
    def test_locate_bundled_extension_finds_assess(self):
        located = _locate_bundled_extension("assess")
        assert located is not None
        assert (located / "extension.yml").is_file()


# ── Install ──────────────────────────────────────────────────────────────────


class TestExtensionInstall:
    def test_install_from_directory(self, tmp_path: Path):
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manifest = manager.install_from_directory(EXT_DIR, "0.9.0", register_commands=False)

        assert manifest.id == "assess"
        assert manager.registry.is_installed("assess")

        installed = tmp_path / ".specify" / "extensions" / "assess"
        for name in EXPECTED_COMMANDS:
            assert (installed / "commands" / f"{name}.md").is_file()

    def test_install_command_names(self, tmp_path: Path):
        """The installed manifest exposes the expected command names."""
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manifest = manager.install_from_directory(EXT_DIR, "0.9.0", register_commands=False)

        names = {c["name"] for c in manifest.commands}
        assert names == EXPECTED_COMMANDS
