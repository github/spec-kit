"""Exercise final resolved winners through the public extension add command."""

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app, shared_infra
from specify_cli.extensions import HookExecutor
from specify_cli.presets import PresetManager
from tests.specify_cli.presets.test_install_transaction import tree_state
from tests.specify_cli.presets.test_selector_provider_lifecycle import (
    COMMAND,
    extension,
    preset,
    project,
)


@pytest.mark.parametrize(
    "agent,skills,relative_output",
    [
        ("gemini", False, f".gemini/commands/{COMMAND}.toml"),
        ("copilot", True, ".github/skills/speckit-provider-collect/SKILL.md"),
        ("claude", True, ".claude/skills/speckit-provider-collect/SKILL.md"),
        ("codex", False, ".agents/skills/speckit-provider-collect/SKILL.md"),
    ],
)
@pytest.mark.parametrize("strategy", ["replace", "prepend", "append", "wrap"])
@pytest.mark.parametrize("override", [False, True])
@pytest.mark.parametrize("fail_after_write", [False, True])
def test_add_materializes_resolved_winner_once(
    tmp_path,
    monkeypatch,
    agent,
    skills,
    relative_output,
    strategy,
    override,
    fail_after_write,
):
    root = project(tmp_path, monkeypatch, agent, skills)
    output = root / relative_output
    if agent in {"claude", "codex"}:
        output.parent.parent.mkdir(parents=True)
    body = (
        "SELECTOR BEFORE\n{CORE_TEMPLATE}\nSELECTOR AFTER"
        if strategy == "wrap"
        else "SELECTOR BODY"
    )
    source = preset(tmp_path, "selector", r"regex:speckit\.provider\..*", body)
    manifest_path = source / "preset.yml"
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest["provides"]["templates"][0]["strategy"] = strategy
    manifest_path.write_text(yaml.safe_dump(manifest))
    PresetManager(root).install_from_directory(source, "0.1.5")
    if override:
        override_path = root / ".specify/templates/overrides" / f"{COMMAND}.md"
        override_path.parent.mkdir(parents=True)
        override_path.write_text("---\ndescription: Local\n---\nPROJECT OVERRIDE\n")
    writes = []
    original_write = Path.write_text
    original_shared_write = shared_infra._write_shared_text

    def record_write(path, content, *args, **kwargs):
        result = original_write(path, content, *args, **kwargs)
        if path == output:
            writes.append(content)
        return result

    def record_shared_write(project_path, dest, content):
        result = original_shared_write(project_path, dest, content)
        if dest == output:
            writes.append(content)
        return result

    monkeypatch.setattr(Path, "write_text", record_write)
    monkeypatch.setattr(shared_infra, "_write_shared_text", record_shared_write)
    ext_source = extension(tmp_path)
    monkeypatch.setattr(
        "specify_cli.extensions._commands._locate_bundled_extension",
        lambda _: ext_source,
    )
    before = tree_state(root)
    if fail_after_write:

        def fail_hooks(executor, manifest):
            assert output.exists()
            assert len(writes) == 1
            raise OSError("failure after resolved materialization")

        monkeypatch.setattr(HookExecutor, "register_hooks", fail_hooks)
    result = CliRunner().invoke(app, ["extension", "add", "provider"])
    if fail_after_write:
        assert result.exit_code != 0
        assert "failure after resolved materialization" in (
            result.output + str(result.exception)
        )
        after = tree_state(root)
        # The installer retains empty operational backup directories even on
        # failed fresh installs; user artifacts and registries must be exact.
        operational_dirs = {
            ".specify/extensions",
            ".specify/extensions/.backup",
            ".specify/extensions/.backup/provider",
        }
        assert {k: v for k, v in after.items() if k not in operational_dirs} == {
            k: v for k, v in before.items() if k not in operational_dirs
        }
        assert all(after.get(k, ("dir",)) == ("dir",) for k in operational_dirs)
        assert len(writes) == 1
        return
    assert result.exit_code == 0, result.output
    text = output.read_text()
    if override:
        assert "PROJECT OVERRIDE" in text
        assert "SELECTOR" not in text
        assert "EXTENSION BODY" not in text
    elif strategy == "replace":
        assert "SELECTOR BODY" in text
        assert "EXTENSION BODY" not in text
    elif strategy == "prepend":
        assert text.index("SELECTOR BODY") < text.index("EXTENSION BODY")
    elif strategy == "append":
        assert text.index("EXTENSION BODY") < text.index("SELECTOR BODY")
    else:
        assert text.index("SELECTOR BEFORE") < text.index("EXTENSION BODY")
        assert text.index("EXTENSION BODY") < text.index("SELECTOR AFTER")
        assert "{CORE_TEMPLATE}" not in text
    assert writes == [text]
