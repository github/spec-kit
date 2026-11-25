"""Layout and registration of the bundled ``autopilot`` extension."""

from __future__ import annotations

import json
import re
import tomllib

import yaml

from tests.extensions.autopilot.helpers import EXT_DIR, REPO_ROOT

EXPECTED_COMMANDS = {
    "speckit.autopilot.setup",
    "speckit.autopilot.run",
    "speckit.autopilot.status",
    "speckit.autopilot.recover",
    "speckit.autopilot.epics",
    "speckit.autopilot.lead",
    "speckit.autopilot.review",
}


def _manifest() -> dict:
    return yaml.safe_load((EXT_DIR / "extension.yml").read_text(encoding="utf-8"))


def test_manifest_declares_the_three_commands_and_config():
    manifest = _manifest()
    assert manifest["extension"]["id"] == "autopilot"
    assert manifest["extension"]["author"] == "spec-kit-core"
    assert {c["name"] for c in manifest["provides"]["commands"]} == EXPECTED_COMMANDS
    for command in manifest["provides"]["commands"]:
        assert (EXT_DIR / command["file"]).is_file()
    config = manifest["provides"]["config"][0]
    assert config["name"] == "autopilot-config.yml"
    assert (EXT_DIR / config["template"]).is_file()


def test_manifest_passes_extension_validation():
    from specify_cli.extensions import ExtensionManifest

    manifest = ExtensionManifest(EXT_DIR / "extension.yml")
    assert manifest.id == "autopilot"


def test_command_files_have_descriptions_and_take_arguments():
    for name in EXPECTED_COMMANDS:
        text = (EXT_DIR / "commands" / f"{name}.md").read_text(encoding="utf-8")
        front = yaml.safe_load(text.split("---", 2)[1])
        assert front["description"]
        assert "$ARGUMENTS" in text


def test_commands_reference_the_shipped_cli():
    cli = ".specify/extensions/autopilot/scripts/python/autopilot.py"
    assert (EXT_DIR / "scripts" / "python" / "autopilot.py").is_file()
    for name in EXPECTED_COMMANDS - {"speckit.autopilot.review", "speckit.autopilot.lead"}:
        assert cli in (EXT_DIR / "commands" / f"{name}.md").read_text(encoding="utf-8"), name


def test_command_cross_references_resolve_to_declared_commands():
    declared = {name.split(".")[-1].upper() for name in EXPECTED_COMMANDS}
    for name in EXPECTED_COMMANDS:
        text = (EXT_DIR / "commands" / f"{name}.md").read_text(encoding="utf-8")
        for target in re.findall(r"__SPECKIT_COMMAND_AUTOPILOT_([A-Z_]+)__", text):
            assert target in declared, f"{name} references undeclared command {target}"


def test_cli_subcommands_named_in_commands_exist():
    import autopilot

    parser_choices = autopilot.subcommands()
    assert {"status", "drive", "stop", "unstop", "reset", "land"} <= parser_choices
    for name in EXPECTED_COMMANDS:
        text = (EXT_DIR / "commands" / f"{name}.md").read_text(encoding="utf-8")
        for sub in re.findall(r"`AP ([a-z-]+)", text):
            assert sub in parser_choices, f"{name} uses unknown CLI subcommand {sub!r}"


def test_reviewer_contract_matches_the_gate():
    from autopilot_core.gate import BLOCKING_SEVERITIES, VALID_SEVERITIES

    text = (EXT_DIR / "commands" / "speckit.autopilot.review.md").read_text(encoding="utf-8")
    for severity in VALID_SEVERITIES:
        assert f"`{severity}`" in text
    assert BLOCKING_SEVERITIES == {"blocker", "major"}
    for key in ("feature_dir=", "diff_file=", "review_file="):
        assert key in text


def test_catalog_and_wheel_registration():
    catalog = json.loads((REPO_ROOT / "extensions" / "catalog.json").read_text(encoding="utf-8"))
    entry = catalog["extensions"]["autopilot"]
    assert entry["bundled"] is True
    assert entry["version"] == _manifest()["extension"]["version"]
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        force_include = tomllib.load(handle)["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
    assert force_include["extensions/autopilot"] == "specify_cli/core_pack/extensions/autopilot"


def test_bundled_extension_is_locatable():
    from specify_cli import _locate_bundled_extension

    located = _locate_bundled_extension("autopilot")
    assert located is not None and (located / "extension.yml").is_file()


def test_lead_contract_matches_the_engine():
    text = (EXT_DIR / "commands" / "speckit.autopilot.lead.md").read_text(encoding="utf-8")
    for key in ("questions_dir=", "ids=", ".answer.json", '"needs_human": true', '"answer"'):
        assert key in text
    from autopilot_core.team import QUESTION_PROTOCOL

    assert ".specify/autopilot/inbox/questions/" in QUESTION_PROTOCOL


def test_core_is_stdlib_only():
    allowed = {
        "__future__", "argparse", "copy", "concurrent", "dataclasses", "datetime", "fnmatch", "hashlib",
        "json", "os", "pathlib", "re", "shutil", "subprocess", "sys", "tempfile", "time", "typing",
        "autopilot_core", "yaml",  # yaml: optional, imported inside a try block
    }
    for path in (EXT_DIR / "scripts" / "python").rglob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^\s*(?:from|import)\s+([A-Za-z_][\w]*)", line)
            if match and not line.lstrip().startswith("from ."):
                assert match.group(1) in allowed, f"{path.name}: {line.strip()}"
