"""Strict override-skill publication in the selector priority transaction."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.presets import PresetManager
from tests.specify_cli.presets._helpers import PresetArtifactTestHelpers
from tests.specify_cli.presets.test_install_transaction import tree_state


@pytest.mark.parametrize("regex", [False, True])
def test_priority_override_write_failure_restores_state(
    project_dir, temp_dir, monkeypatch, regex
):
    helper = PresetArtifactTestHelpers()
    helper._write_init_options(project_dir, ai="claude", ai_skills=True)
    (project_dir / ".claude" / "skills").mkdir(parents=True)
    manager = PresetManager(project_dir)
    provider = helper._create_command_preset(
        temp_dir, "provider", "speckit.demo", "provider", "PROVIDER"
    )
    manager.install_from_directory(provider, "0.1.5", priority=20)
    overlay = helper._create_command_preset(
        temp_dir,
        "overlay",
        "regex:^speckit\\.demo$" if regex else "speckit.demo",
        "overlay",
        "OVERLAY",
    )
    manager.install_from_directory(overlay, "0.1.5", priority=10)
    override = project_dir / ".specify/templates/overrides/speckit.demo.md"
    override.parent.mkdir(parents=True)
    override.write_text("---\ndescription: Override\n---\n\nOVERRIDE_NEW\n")
    skill = (project_dir / ".claude/skills/speckit-demo/SKILL.md").resolve()
    before = tree_state(project_dir)
    original_replace = os.replace
    hits = []

    calls = []

    def fail_override(src, dst, *args, **kwargs):
        calls.append(str(dst))
        # Resolve both sides: Windows reports 8.3 short names (RUNNER~1) for the
        # temp root while the fixture resolved the long name.
        if Path(dst).resolve() == skill and "OVERRIDE_NEW" in Path(src).read_text(
            encoding="utf-8"
        ):
            hits.append(skill.read_bytes())
            raise OSError("override skill publication denied")
        return original_replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "replace", fail_override)
    monkeypatch.chdir(project_dir)
    result = CliRunner().invoke(app, ["preset", "set-priority", "overlay", "1"])
    assert hits, (
        f"Inject at actual writer: {result.output}; {result.exception!r}; {calls}"
    )
    assert result.exit_code != 0
    assert "override skill publication denied" in str(result.exception)
    assert PresetManager(project_dir).registry.get("overlay")["priority"] == 10
    assert tree_state(project_dir) == before
