"""Workflow-level integration tests for ``specify preset update``.

``tests/test_presets.py`` covers the orchestration contract with mocked
``preset_remove``/``preset_add`` calls, which proves *what* the wrapper calls
but not that the calls are wired to the real install/remove machinery. These
tests drive the CLI through ``CliRunner`` against a real project and a real
``PresetManager``, asserting on registry and on-disk state rather than call
counts, so the destructive remove-then-add contract is verified end to end.
"""
from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.presets import PresetManager
from tests.conftest import strip_ansi

PRESET_ID = "update-workflow-demo"


def make_project(root: Path) -> Path:
    """Create a minimal Spec Kit project with the core templates presets need."""
    templates = root / ".specify" / "templates"
    (templates / "commands").mkdir(parents=True, exist_ok=True)
    (templates / "spec-template.md").write_text(
        "# Core Spec Template\n", encoding="utf-8"
    )
    return root


def write_preset(
    directory: Path,
    *,
    version: str,
    body: str,
    extra_file: str | None = None,
) -> Path:
    """Write a minimal single-template preset under *directory*.

    ``extra_file`` adds a version-specific file so a later install can be
    distinguished from a stale copy of the previous one that was never removed.
    """
    templates = directory / "templates"
    templates.mkdir(parents=True, exist_ok=True)
    (templates / "spec-template.md").write_text(body, encoding="utf-8")
    if extra_file is not None:
        (directory / extra_file).write_text("marker\n", encoding="utf-8")

    (directory / "preset.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "preset": {
                    "id": PRESET_ID,
                    "name": "Update Workflow Demo",
                    "version": version,
                    "description": "Fixture preset for update workflow tests",
                    "author": "Spec Kit tests",
                    "license": "MIT",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "templates": [
                        {
                            "type": "template",
                            "name": "spec-template",
                            "file": "templates/spec-template.md",
                            "description": "Replacement spec template",
                            "replaces": "spec-template",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    return directory


def render_command(args: list[str]) -> str:
    """Render *args* the way ``preset update`` renders its retry command."""
    if os.name == "nt":
        return subprocess.list2cmdline(args)
    return shlex.join(args)


def parse_command(rendered: str) -> list[str]:
    """Inverse of :func:`render_command` for the simple args used here."""
    if os.name == "nt":
        return [token.strip('"') for token in shlex.split(rendered, posix=False)]
    return shlex.split(rendered)


def retry_command_from(output: str) -> str:
    """Extract the retry command printed after a failed update."""
    for line in strip_ansi(output).splitlines():
        stripped = line.strip()
        if stripped.startswith("Retry with: "):
            return stripped[len("Retry with: ") :].strip()
    raise AssertionError(f"No retry command found in output:\n{output}")


@pytest.fixture
def project(tmp_path: Path, monkeypatch) -> Path:
    root = make_project(tmp_path / "proj")
    monkeypatch.chdir(root)
    return root


def test_preset_update_cli_contract():
    """Typer exposes the required ID and only the supported update options."""
    runner = CliRunner()

    missing_id = runner.invoke(app, ["preset", "update"])
    assert missing_id.exit_code == 2
    assert "Missing argument 'preset_id'" in strip_ansi(missing_id.output)

    for unsupported_option in ("--all", "--dry-run"):
        rejected = runner.invoke(
            app, ["preset", "update", PRESET_ID, unsupported_option]
        )
        assert rejected.exit_code == 2
        assert f"No such option: {unsupported_option}" in strip_ansi(rejected.output)

    help_result = runner.invoke(app, ["preset", "update", "--help"])
    assert help_result.exit_code == 0
    help_output = strip_ansi(help_result.output)
    assert "Usage: specify preset update [OPTIONS] {preset_id}" in help_output
    assert (
        "Replace an installed preset using the normal remove and add flows."
        in help_output
    )
    assert "Installed preset ID to replace" in help_output
    for supported_option in ("--from", "--dev", "--priority"):
        assert supported_option in help_output
    assert "--all" not in help_output
    assert "--dry-run" not in help_output


def test_preset_update_replaces_installed_preset(project: Path, tmp_path: Path):
    """A successful update really swaps the installed preset on disk."""
    runner = CliRunner()

    original = write_preset(
        tmp_path / "v1",
        version="1.0.0",
        body="# Version One Template\n",
        extra_file="only-in-v1.md",
    )
    replacement = write_preset(
        tmp_path / "v2",
        version="2.0.0",
        body="# Version Two Template\n",
        extra_file="only-in-v2.md",
    )

    install = runner.invoke(
        app, ["preset", "add", "--dev", str(original), "--priority", "20"]
    )
    assert install.exit_code == 0, install.output

    installed_dir = project / ".specify" / "presets" / PRESET_ID
    assert (installed_dir / "only-in-v1.md").exists()

    update = runner.invoke(
        app,
        ["preset", "update", PRESET_ID, "--dev", str(replacement), "--priority", "5"],
    )
    assert update.exit_code == 0, update.output

    metadata = PresetManager(project).registry.get(PRESET_ID)
    assert metadata is not None, "update must leave the preset installed"
    assert metadata["version"] == "2.0.0"
    assert metadata["priority"] == 5

    template = installed_dir / "templates" / "spec-template.md"
    assert template.read_text(encoding="utf-8") == "# Version Two Template\n"
    assert (installed_dir / "only-in-v2.md").exists()
    assert not (installed_dir / "only-in-v1.md").exists(), (
        "the previous preset's files must be removed, not merged with the "
        "replacement"
    )


def test_preset_update_failed_replacement_prints_working_retry_command(
    project: Path, tmp_path: Path
):
    """A failed replacement leaves the preset removed and the retry usable."""
    runner = CliRunner()

    original = write_preset(
        tmp_path / "v1", version="1.0.0", body="# Version One Template\n"
    )
    install = runner.invoke(app, ["preset", "add", "--dev", str(original)])
    assert install.exit_code == 0, install.output
    assert PresetManager(project).registry.is_installed(PRESET_ID)

    # The source does not exist yet, so add fails after remove has run.
    replacement = tmp_path / "replacement"
    update = runner.invoke(
        app,
        ["preset", "update", PRESET_ID, "--dev", str(replacement), "--priority", "7"],
    )

    assert update.exit_code == 1, update.output
    output = strip_ansi(update.output)
    assert "Directory not found" in output, "add's own error must be preserved"
    assert "previous preset was removed" in output
    assert not PresetManager(project).registry.is_installed(PRESET_ID), (
        "update is destructive: a failed replacement must leave the preset "
        "removed rather than silently restored"
    )
    assert not (project / ".specify" / "presets" / PRESET_ID).exists()

    rendered = retry_command_from(update.output)
    assert rendered == render_command(
        [
            "specify",
            "preset",
            "add",
            PRESET_ID,
            "--dev",
            str(replacement),
            "--priority",
            "7",
        ]
    )

    # Supply a valid source at the advertised path and run the printed command
    # verbatim: the retry must actually recover the project, not merely appear.
    write_preset(replacement, version="2.0.0", body="# Recovered Template\n")
    retry_args = parse_command(rendered)
    assert retry_args[0] == "specify"
    retry = runner.invoke(app, retry_args[1:])

    assert retry.exit_code == 0, retry.output
    metadata = PresetManager(project).registry.get(PRESET_ID)
    assert metadata is not None
    assert metadata["version"] == "2.0.0"
    assert metadata["priority"] == 7
