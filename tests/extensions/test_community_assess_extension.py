"""Tests for the bundled community pull request assessment extension."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from specify_cli import _locate_bundled_extension


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "community-assess"
COMMAND = "speckit.community-assess.assess"


def test_manifest_and_command_are_bundled():
    manifest = yaml.safe_load((EXT_DIR / "extension.yml").read_text(encoding="utf-8"))
    assert manifest["extension"]["id"] == "community-assess"
    assert manifest["extension"]["author"] == "spec-kit-core"
    assert {c["name"] for c in manifest["provides"]["commands"]} == {COMMAND}
    assert (EXT_DIR / "README.md").is_file()
    assert (EXT_DIR / "commands" / f"{COMMAND}.md").is_file()


def test_catalog_registers_community_assessment_as_bundled():
    catalog = json.loads(
        (PROJECT_ROOT / "extensions" / "catalog.json").read_text(encoding="utf-8")
    )
    entry = catalog["extensions"]["community-assess"]
    assert entry["id"] == "community-assess"
    assert entry["bundled"] is True


def test_bundled_extension_is_resolvable():
    located = _locate_bundled_extension("community-assess")
    assert located == EXT_DIR


def test_bundled_extension_is_force_included_in_wheels():
    import tomllib

    pyproject = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    force_include = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"][
        "force-include"
    ]
    assert force_include["extensions/community-assess"] == (
        "specify_cli/core_pack/extensions/community-assess"
    )


def test_install_copies_the_assessment_command(tmp_path: Path):
    from specify_cli.extensions import ExtensionManager

    (tmp_path / ".specify").mkdir()
    manager = ExtensionManager(tmp_path)
    manifest = manager.install_from_directory(
        EXT_DIR, "0.9.0", register_commands=False
    )

    assert manifest.id == "community-assess"
    installed = tmp_path / ".specify" / "extensions" / "community-assess"
    assert (installed / "commands" / f"{COMMAND}.md").is_file()
