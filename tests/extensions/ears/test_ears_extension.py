"""Tests for the bundled ``ears`` extension.

Validates:
- Bundled layout (manifest, README, three command files)
- Catalog registration
- Wheel/source-checkout resolution via ``_locate_bundled_extension``
- Install via ``ExtensionManager.install_from_directory`` copies the three
  command files and records them in the installed manifest (command
  registration with AI agents is exercised separately and not asserted here)
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import yaml

from specify_cli import _locate_bundled_extension


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "ears"

EXPECTED_COMMANDS = {
    "speckit.ears.author",
    "speckit.ears.lint",
    "speckit.ears.convert",
}


# ── Bundled extension layout ─────────────────────────────────────────────────


class TestExtensionLayout:
    def test_extension_yml_exists(self):
        assert (EXT_DIR / "extension.yml").is_file()

    def test_extension_yml_has_required_fields(self):
        manifest = yaml.safe_load(
            (EXT_DIR / "extension.yml").read_text(encoding="utf-8")
        )
        assert manifest["extension"]["id"] == "ears"
        assert manifest["extension"]["name"] == "EARS Requirements Syntax"
        assert manifest["extension"]["author"] == "spec-kit-core"
        commands = {c["name"] for c in manifest["provides"]["commands"]}
        assert commands == EXPECTED_COMMANDS

    def test_readme_exists(self):
        readme = EXT_DIR / "README.md"
        assert readme.is_file()
        text = readme.read_text(encoding="utf-8")
        assert "EARS Requirements Syntax Extension" in text

    def test_command_files_exist(self):
        for name in EXPECTED_COMMANDS:
            cmd = EXT_DIR / "commands" / f"{name}.md"
            assert cmd.is_file(), f"Missing command file: {cmd}"


# ── Catalog registration ─────────────────────────────────────────────────────


class TestCatalogEntry:
    def test_catalog_lists_ears_as_bundled(self):
        catalog = json.loads(
            (PROJECT_ROOT / "extensions" / "catalog.json").read_text(encoding="utf-8")
        )
        entry = catalog["extensions"]["ears"]
        assert entry["bundled"] is True
        assert entry["id"] == "ears"
        assert entry["author"] == "spec-kit-core"


# ── Bundle resolution ────────────────────────────────────────────────────────


class TestBundleResolution:
    def test_locate_bundled_extension_finds_ears(self):
        located = _locate_bundled_extension("ears")
        assert located is not None
        assert (located / "extension.yml").is_file()

    def test_pyproject_force_includes_ears_for_wheel_builds(self):
        """The catalog marks ``ears`` as bundled, so the wheel build must
        force-include ``extensions/ears`` alongside the other bundled
        extensions. Otherwise `specify extension add ears` fails on wheel
        installs because `_locate_bundled_extension()` only finds bundled
        extensions under `specify_cli/core_pack/extensions/` in that case."""
        pyproject = tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        force_include = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"][
            "force-include"
        ]
        assert force_include.get("extensions/ears") == (
            "specify_cli/core_pack/extensions/ears"
        )


# ── Install ──────────────────────────────────────────────────────────────────


class TestExtensionInstall:
    def test_install_from_directory(self, tmp_path: Path):
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manifest = manager.install_from_directory(EXT_DIR, "0.9.0", register_commands=False)

        assert manifest.id == "ears"
        assert manager.registry.is_installed("ears")

        # All three command files are copied into the installed extension dir
        installed = tmp_path / ".specify" / "extensions" / "ears"
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
