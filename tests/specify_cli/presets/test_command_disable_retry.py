"""Real filesystem regressions for retrying best-effort preset disable cleanup."""

from pathlib import Path
import shutil

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.presets import PresetManager

from .test_regex_selector_lifecycle import _write_preset
from .test_selector_provider_lifecycle import ALIAS, COMMAND, project


@pytest.mark.parametrize(
    "agent,skills,skill_only,relative_output",
    [
        ("gemini", False, False, f".gemini/commands/{COMMAND}.toml"),
        ("copilot", True, True, ".github/skills/speckit-provider-collect/SKILL.md"),
    ],
)
def test_disable_retries_failed_filesystem_cleanup(
    tmp_path, monkeypatch, agent, skills, skill_only, relative_output
):
    root = project(tmp_path, monkeypatch, agent, skills)
    manager = PresetManager(root)
    constitution = {
        "type": "template",
        "name": "constitution-template",
        "file": "constitution.md",
    }
    manager.install_from_directory(
        _write_preset(
            tmp_path,
            "constitution-sync",
            [constitution],
            {"constitution.md": "FALLBACK CONSTITUTION\n"},
        ),
        "0.1.5",
        priority=20,
    )
    manager.install_from_directory(
        _write_preset(
            tmp_path,
            "provider",
            [
                constitution,
                {
                    "type": "command",
                    "name": COMMAND,
                    "file": "commands/body.md",
                    "aliases": [ALIAS],
                },
            ],
            {
                "constitution.md": "PROVIDER CONSTITUTION\n",
                "commands/body.md": "---\ndescription: Provider\n---\nPROVIDER BODY\n",
            },
        ),
        "0.1.5",
        priority=10,
    )
    if skill_only:
        manager.registry.update("provider", {"registered_commands": {}})
    output = root / relative_output
    memory = root / ".specify/memory/constitution.md"
    assert output.is_file()
    assert memory.read_text() == "PROVIDER CONSTITUTION\n"
    before = manager.registry.get("provider")
    attempts = []
    constitution_states = []
    reconcile = PresetManager.reconcile_constitution

    def record_constitution(self, *args, **kwargs):
        constitution_states.append(self.registry.get("provider")["enabled"])
        return reconcile(self, *args, **kwargs)

    monkeypatch.setattr(PresetManager, "reconcile_constitution", record_constitution)
    if agent == "gemini":
        unlink = Path.unlink

        def fail_once(path, *args, **kwargs):
            if path == output and not attempts:
                attempts.append(path)
                assert PresetManager(root).registry.get("provider")["enabled"] is False
                raise OSError("filesystem cleanup blocked")
            return unlink(path, *args, **kwargs)

        monkeypatch.setattr(Path, "unlink", fail_once)
    else:
        rmtree = shutil.rmtree

        def fail_once(path, *args, **kwargs):
            if Path(path) == output.parent and not attempts:
                attempts.append(Path(path))
                assert PresetManager(root).registry.get("provider")["enabled"] is False
                raise OSError("filesystem cleanup blocked")
            return rmtree(path, *args, **kwargs)

        monkeypatch.setattr(shutil, "rmtree", fail_once)

    runner = CliRunner()
    with pytest.warns(UserWarning, match="provenance was preserved for retry"):
        result = runner.invoke(app, ["preset", "disable", "provider"])
    assert result.exit_code == 0, result.output
    assert "artifact cleanup failed" in result.output
    assert attempts
    assert output.is_file()
    retained = PresetManager(root).registry.get("provider")
    assert retained["enabled"] is False
    assert retained["registered_commands"] == before["registered_commands"]
    assert retained["registered_skills"] == before["registered_skills"]
    assert memory.read_text() == "FALLBACK CONSTITUTION\n"

    result = runner.invoke(app, ["preset", "disable", "provider"])
    assert result.exit_code == 0, result.output
    assert not output.exists()
    if agent == "gemini":
        assert not (output.parent / f"{ALIAS}.toml").exists()
    metadata = PresetManager(root).registry.get("provider")
    assert metadata["enabled"] is False
    assert metadata["registered_commands"] == {}
    assert metadata["registered_skills"] == {}
    assert constitution_states == [False, False]
    assert memory.read_text() == "FALLBACK CONSTITUTION\n"

    result = runner.invoke(app, ["preset", "disable", "provider"])
    assert result.exit_code == 0, result.output
    assert "already disabled" in result.output
    assert constitution_states == [False, False]


@pytest.mark.parametrize("tracking", [{}, {"gemini": []}])
def test_already_disabled_without_artifacts_is_a_clean_noop(
    tmp_path, monkeypatch, tracking
):
    root = project(tmp_path, monkeypatch)
    manager = PresetManager(root)
    source = _write_preset(
        tmp_path,
        "provider",
        [{"type": "command", "name": COMMAND, "file": "commands/body.md"}],
        {"commands/body.md": "---\ndescription: Provider\n---\nBODY\n"},
    )
    manager.install_from_directory(source, "0.1.5")
    manager.registry.update(
        "provider",
        {
            "enabled": False,
            "registered_commands": tracking,
            "registered_skills": tracking,
        },
    )
    # Compare every persisted file, not only logical registry equality.
    before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}

    def unexpected(*args, **kwargs):
        pytest.fail("an artifact-free disabled preset must not reconcile or write")

    monkeypatch.setattr(PresetManager, "_collect_selector_command_names", unexpected)
    monkeypatch.setattr(PresetManager, "reconcile_constitution", unexpected)
    monkeypatch.setattr(type(manager.registry), "update", unexpected)
    result = CliRunner().invoke(app, ["preset", "disable", "provider"])
    assert result.exit_code == 0, result.output
    assert "already disabled" in result.output
    assert {
        path: path.read_bytes() for path in root.rglob("*") if path.is_file()
    } == before
