"""Every ``__SPECKIT_COMMAND_<NAME>__`` placeholder names a command that exists.

``IntegrationBase.resolve_command_refs`` rewrites the token with a regex and
does not consult a list of commands, so a misspelled placeholder does not fail.
``__SPECKIT_COMMAND_ASSES_SHAPE__`` becomes ``/speckit.asses.shape``, which is
shipped into agent instructions as a plausible-looking command that no agent can
run. Existing coverage in ``tests/test_agent_config_consistency.py`` and
``tests/integrations/test_base.py`` asserts that the rewrite uses the right
separator and prefix, which is the mechanism rather than the target.

The command set is derived from the files that define commands rather than
restated here, so a command added or renamed is covered without editing this
module.
"""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

PLACEHOLDER = re.compile(r"__SPECKIT_COMMAND_([A-Z][A-Z0-9_]*)__")

# Directories whose markdown is installed into a user's project.
SHIPPED = ("templates", "extensions", "presets")


def placeholder_to_command(name: str) -> str:
    """The command ``resolve_command_refs`` produces for this placeholder."""
    return "speckit." + name.lower().replace("_", ".")


def core_commands() -> set[str]:
    directory = REPO_ROOT / "templates" / "commands"
    assert directory.is_dir(), f"expected core command templates at {directory}"
    commands = {"speckit." + path.stem for path in directory.glob("*.md")}
    assert commands, f"no core command templates found under {directory}"
    return commands


def manifest_commands() -> set[str]:
    commands: set[str] = set()
    manifests = list((REPO_ROOT / "extensions").glob("*/extension.yml"))
    manifests += list((REPO_ROOT / "presets").glob("*/preset.yml"))
    assert manifests, "no extension or preset manifests found"
    for manifest in manifests:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
        provides = data.get("provides") or {}
        for entry in provides.get("commands") or []:
            name = entry.get("name")
            if name:
                commands.add(name)
            for alias in entry.get("aliases") or []:
                commands.add(alias)
    return commands


def shipped_markdown() -> list[Path]:
    paths: list[Path] = []
    for directory in SHIPPED:
        paths.extend(sorted((REPO_ROOT / directory).rglob("*.md")))
    assert paths, "no shipped markdown found to scan"
    return paths


def placeholders_by_file() -> dict[Path, set[str]]:
    found: dict[Path, set[str]] = {}
    for path in shipped_markdown():
        names = set(PLACEHOLDER.findall(path.read_text(encoding="utf-8")))
        if names:
            found[path] = names
    return found


def test_placeholders_are_present_to_be_checked():
    """A scan that silently finds nothing would pass forever."""
    assert placeholders_by_file(), (
        "no __SPECKIT_COMMAND_*__ placeholders found in shipped markdown; the "
        "token spelling or the shipped directories changed"
    )


def test_every_placeholder_names_a_command_that_exists():
    known = core_commands() | manifest_commands()
    unresolved: dict[str, list[str]] = {}
    for path, names in placeholders_by_file().items():
        for name in names:
            command = placeholder_to_command(name)
            if command not in known:
                relative = path.relative_to(REPO_ROOT).as_posix()
                unresolved.setdefault(command, []).append(relative)
    assert not unresolved, (
        "placeholders resolve to commands that do not exist: "
        + "; ".join(
            f"/{command} referenced by {', '.join(sorted(files))}"
            for command, files in sorted(unresolved.items())
        )
    )


def test_core_templates_do_not_reference_extension_commands():
    """A core template must work when no extension is installed."""
    core = core_commands()
    extension_only = manifest_commands() - core
    leaked: dict[str, list[str]] = {}
    for path, names in placeholders_by_file().items():
        if not path.is_relative_to(REPO_ROOT / "templates"):
            continue
        for name in names:
            command = placeholder_to_command(name)
            if command in extension_only:
                relative = path.relative_to(REPO_ROOT).as_posix()
                leaked.setdefault(command, []).append(relative)
    assert not leaked, (
        "core templates reference commands only an extension provides, so the "
        "instruction is dead unless that extension is installed: "
        + "; ".join(
            f"/{command} in {', '.join(sorted(files))}"
            for command, files in sorted(leaked.items())
        )
    )


@pytest.mark.parametrize(
    ("placeholder", "expected"),
    [
        ("PLAN", "speckit.plan"),
        ("GIT_COMMIT", "speckit.git.commit"),
        ("ASSESS_SHAPE", "speckit.assess.shape"),
    ],
)
def test_placeholder_to_command_matches_resolve_command_refs(placeholder, expected):
    """The mapping used here is the one the resolver implements."""
    from specify_cli.integrations.base import IntegrationBase

    resolved = IntegrationBase.resolve_command_refs(
        f"__SPECKIT_COMMAND_{placeholder}__", separator=".", prefix="/"
    )
    assert resolved == f"/{expected}"
    assert placeholder_to_command(placeholder) == expected
