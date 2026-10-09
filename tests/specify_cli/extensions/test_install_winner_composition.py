"""Exercise final resolved winners through the public extension add command."""

from pathlib import Path, PureWindowsPath

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
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["provides"]["templates"][0]["strategy"] = strategy
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    PresetManager(root).install_from_directory(source, "0.1.5")
    if override:
        override_path = root / ".specify/templates/overrides" / f"{COMMAND}.md"
        override_path.parent.mkdir(parents=True)
        override_path.write_text(
            "---\ndescription: Local\n---\nPROJECT OVERRIDE\n", encoding="utf-8"
        )
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
    text = output.read_text(encoding="utf-8")
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


def test_override_staged_declaration_is_portable_on_windows(tmp_path, monkeypatch):
    """Windows rendering of the staged override payload must stay portable.

    ``relative_extension_path_violation`` rejects backslashes and
    ``CommandRegistrar.register_commands`` *skips* a declaration whose ``file``
    violates that policy, so building the staged reference with a native
    ``str(Path)`` silently drops the command on Windows only — every platform
    with ``os.sep == "/"`` keeps passing. Render the staged reference exactly as
    Windows would (``PureWindowsPath``) and assert the artifact still lands.
    """
    root = project(tmp_path, monkeypatch, "gemini", False)
    source = preset(
        tmp_path, "selector", r"regex:speckit\.provider\..*", "SELECTOR BODY"
    )
    PresetManager(root).install_from_directory(source, "0.1.5")
    override_path = root / ".specify" / "templates" / "overrides" / f"{COMMAND}.md"
    override_path.parent.mkdir(parents=True)
    override_path.write_text("---\ndescription: Local\n---\nPROJECT OVERRIDE\n")

    real_relative_to = Path.relative_to

    def windows_relative_to(self, *args, **kwargs):
        result = real_relative_to(self, *args, **kwargs)
        parts = result.parts
        if parts and parts[0] == ".resolved":
            # Exactly the string a native str(Path) yields on Windows.
            return PureWindowsPath("/".join(parts))
        return result

    monkeypatch.setattr(Path, "relative_to", windows_relative_to)
    ext_source = extension(tmp_path)
    monkeypatch.setattr(
        "specify_cli.extensions._commands._locate_bundled_extension",
        lambda _: ext_source,
    )

    result = CliRunner().invoke(app, ["extension", "add", "provider"])

    assert result.exit_code == 0, result.output
    output = root / ".gemini" / "commands" / f"{COMMAND}.toml"
    assert output.exists(), "staged override payload was dropped as unmaterialized"
    text = output.read_text(encoding="utf-8")
    assert "PROJECT OVERRIDE" in text
    assert "SELECTOR" not in text


def test_override_staged_reference_passes_shared_path_policy(tmp_path, monkeypatch):
    """Every declaration the installer hands to the registrar must be portable.

    ``relative_extension_path_violation`` is the single path-safety policy
    shared by manifest validation and the registrar's runtime guard, so a
    ``file`` that fails it is skipped rather than materialized.
    """
    from specify_cli._utils import relative_extension_path_violation
    from specify_cli.agents import CommandRegistrar

    root = project(tmp_path, monkeypatch, "gemini", False)
    source = preset(
        tmp_path, "selector", r"regex:speckit\.provider\..*", "SELECTOR BODY"
    )
    PresetManager(root).install_from_directory(source, "0.1.5")
    override_path = root / ".specify" / "templates" / "overrides" / f"{COMMAND}.md"
    override_path.parent.mkdir(parents=True)
    override_path.write_text("---\ndescription: Local\n---\nPROJECT OVERRIDE\n")

    seen: list[str] = []
    original = CommandRegistrar.register_commands

    def capture(self, *args, **kwargs):
        for candidate in list(args) + list(kwargs.values()):
            if (
                isinstance(candidate, list)
                and candidate
                and isinstance(candidate[0], dict)
                and "name" in candidate[0]
            ):
                seen.extend(
                    entry["file"]
                    for entry in candidate
                    if isinstance(entry.get("file"), str)
                )
                break
        return original(self, *args, **kwargs)

    monkeypatch.setattr(CommandRegistrar, "register_commands", capture)
    ext_source = extension(tmp_path)
    monkeypatch.setattr(
        "specify_cli.extensions._commands._locate_bundled_extension",
        lambda _: ext_source,
    )

    result = CliRunner().invoke(app, ["extension", "add", "provider"])

    assert result.exit_code == 0, result.output
    assert any(value.startswith(".resolved/") for value in seen), seen
    for value in seen:
        assert "\\" not in value, value
        assert relative_extension_path_violation(value) is None, value
