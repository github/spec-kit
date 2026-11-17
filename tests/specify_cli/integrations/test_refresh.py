"""Extension-add readiness across the recorded installed integration set."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app, get_speckit_version, save_init_options
from specify_cli.integration_state import write_integration_json
from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest


def prepare_project(root: Path, keys=("claude", "codex"), options=None):
    root.mkdir(exist_ok=True)
    (root / ".specify").mkdir(exist_ok=True)
    options = options or {}
    settings = {}
    for key in keys:
        integration = get_integration(key)
        assert integration is not None
        parsed = options.get(key)
        manifest = IntegrationManifest(key, root, get_speckit_version())
        integration.setup(root, manifest, parsed_options=parsed, script_type="py")
        manifest.save()
        settings[key] = {"script": "py", "parsed_options": parsed or {}}
    default = get_integration(keys[0])
    save_init_options(root, {
        "ai": keys[0], "integration": keys[0], "script": "py",
        "ai_skills": default.is_skills_mode(options.get(keys[0]), root),
    })
    write_integration_json(
        root, integration_key=keys[0], installed_integrations=list(keys),
        settings=settings, version=get_speckit_version(),
    )


def add_assess(root, monkeypatch, *args):
    with monkeypatch.context() as scoped:
        scoped.chdir(root)
        return CliRunner().invoke(app, ["extension", "add", "assess", *args])


def test_add_restores_core_and_all_five_commands_without_selecting_default(tmp_path, monkeypatch):
    from specify_cli.extensions import ExtensionCatalog

    prepare_project(tmp_path)
    context = tmp_path / "AGENTS.md"
    context.write_bytes(b"my project context\n")
    monkeypatch.setattr(
        ExtensionCatalog, "_open_url",
        lambda *args, **kwargs: pytest.fail("Local readiness must not access the network"),
    )
    before_state = (tmp_path / ".specify/integration.json").read_bytes()
    before_options = (tmp_path / ".specify/init-options.json").read_bytes()
    missing_core = tmp_path / ".agents/skills/speckit-plan/SKILL.md"
    missing_core.unlink()
    result = add_assess(tmp_path, monkeypatch)
    assert result.exit_code == 0, result.output
    assert len(list((tmp_path / ".claude/skills").glob("speckit-assess-*/SKILL.md"))) == 5
    assert len(list((tmp_path / ".agents/skills").glob("speckit-assess-*/SKILL.md"))) == 5
    assert missing_core.is_file()
    assert (tmp_path / ".specify/integration.json").read_bytes() == before_state
    assert (tmp_path / ".specify/init-options.json").read_bytes() == before_options
    assert context.read_bytes() == b"my project context\n"


def test_add_retains_extension_and_modified_output_on_refresh_failure(tmp_path, monkeypatch):
    prepare_project(tmp_path)
    customized = tmp_path / ".agents/skills/speckit-plan/SKILL.md"
    customized.write_text("my customized workflow\n", encoding="utf-8")
    result = add_assess(tmp_path, monkeypatch)
    assert result.exit_code == 1, result.output
    assert customized.read_text() == "my customized workflow\n"
    assert (tmp_path / ".specify/extensions/assess/extension.yml").is_file()
    assert "codex" in result.output
    assert "completed" in result.output.lower()
    assert "retry" in result.output.lower()
    assert "Extension installed successfully" not in result.output


def test_add_does_not_prepare_directory_only_integration(tmp_path, monkeypatch):
    prepare_project(tmp_path, ("claude",))
    (tmp_path / ".agents/skills").mkdir(parents=True)
    result = add_assess(tmp_path, monkeypatch)
    assert result.exit_code == 0, result.output
    assert not list((tmp_path / ".agents/skills").glob("speckit-*"))


@pytest.mark.parametrize("parsed", [{"commands": True}, {"skills": True}])
def test_add_honors_saved_non_default_copilot_mode(tmp_path, monkeypatch, parsed):
    prepare_project(tmp_path, ("claude", "copilot"), {"copilot": parsed})
    result = add_assess(tmp_path, monkeypatch)
    assert result.exit_code == 0, result.output
    if parsed.get("skills"):
        assert len(list((tmp_path / ".github/skills").glob("speckit-assess-*/SKILL.md"))) == 5
        assert not list((tmp_path / ".github/agents").glob("speckit.assess.*.agent.md"))
    else:
        assert len(list((tmp_path / ".github/agents").glob("speckit.assess.*.agent.md"))) == 5
        assert not list((tmp_path / ".github/skills").glob("speckit-assess-*/SKILL.md"))


def test_add_reports_missing_adapter_and_preserves_completed_refresh(tmp_path, monkeypatch):
    prepare_project(tmp_path)
    state_file = tmp_path / ".specify/integration.json"
    state = json.loads(state_file.read_text())
    state["installed_integrations"].append("missing-adapter")
    state_file.write_text(json.dumps(state), encoding="utf-8")
    result = add_assess(tmp_path, monkeypatch)
    assert result.exit_code == 1, result.output
    assert "missing-adapter" in result.output
    assert "Completed: claude, codex" in result.output
    assert (tmp_path / ".agents/skills/speckit-assess-intake/SKILL.md").is_file()


def test_add_without_recorded_integrations_does_not_use_detected_directories(tmp_path, monkeypatch):
    (tmp_path / ".specify").mkdir()
    (tmp_path / ".claude/skills").mkdir(parents=True)
    result = add_assess(tmp_path, monkeypatch)
    assert result.exit_code == 1, result.output
    assert "integration state" in result.output
    assert not list((tmp_path / ".claude/skills").glob("speckit-*"))
    assert (tmp_path / ".specify/extensions/assess/extension.yml").is_file()


def test_failure_retains_owned_outputs_for_safe_retry(tmp_path, monkeypatch):
    from specify_cli.integrations.refresh import refresh_installed_integrations

    prepare_project(tmp_path)
    conflict = tmp_path / ".agents/skills/speckit-plan/SKILL.md"
    original = conflict.read_bytes()
    conflict.write_bytes(b"customized\n")
    first = add_assess(tmp_path, monkeypatch)
    assert first.exit_code == 1
    conflict.write_bytes(original)
    retried = refresh_installed_integrations(tmp_path)
    assert retried.success, retried.failed
    for key in ("claude", "codex"):
        assert IntegrationManifest.load(key, tmp_path).check_modified() == []


def test_add_preserves_untracked_output_and_context_files(tmp_path, monkeypatch):
    prepare_project(tmp_path)
    custom = tmp_path / ".agents/skills/speckit-assess-intake/SKILL.md"
    custom.parent.mkdir()
    custom.write_bytes(b"my unrelated skill\n")
    context = tmp_path / "AGENTS.md"
    context.write_bytes(b"my context\n")
    result = add_assess(tmp_path, monkeypatch)
    assert result.exit_code == 1
    assert custom.read_bytes() == b"my unrelated skill\n"
    assert context.read_bytes() == b"my context\n"
    assert "untracked" in result.output


def test_add_strictly_propagates_registration_failure(tmp_path, monkeypatch):
    from specify_cli.extensions import CommandRegistrar

    prepare_project(tmp_path)
    monkeypatch.setattr(CommandRegistrar, "register_commands_for_agent", lambda *a, **k: [])
    result = add_assess(tmp_path, monkeypatch)
    assert result.exit_code == 1
    assert "Missing invocation artifacts" in " ".join(result.output.split())
    assert "Extension installed successfully" not in result.output


def test_empty_core_setup_cannot_claim_readiness_or_delete_previous_core(tmp_path, monkeypatch):
    prepare_project(tmp_path)
    core = tmp_path / ".agents/skills/speckit-plan/SKILL.md"
    before = core.read_bytes()
    monkeypatch.setattr(type(get_integration("codex")), "setup", lambda *args, **kwargs: [])
    added = add_assess(tmp_path, monkeypatch)
    assert added.exit_code == 1, added.output
    assert "No core invocation artifacts" in " ".join(added.output.split())
    assert core.read_bytes() == before


def test_workflow_dynamically_dispatches_both_agents_without_preparation(tmp_path, monkeypatch):
    from specify_cli.workflows.base import StepContext, StepStatus
    from specify_cli.workflows.step.command import CommandStep

    prepare_project(tmp_path)
    added = add_assess(tmp_path, monkeypatch)
    assert added.exit_code == 0, added.output
    before = (tmp_path / ".specify/integration.json").read_bytes()
    executable = tmp_path / "fake_agent.py"
    executable.write_text(
        "import sys\nfrom pathlib import Path\n"
        "agent, invocation = sys.argv[1:3]\n"
        "folder = '.claude/skills' if agent == 'claude' else '.agents/skills'\n"
        "assert (Path.cwd() / folder / 'speckit-assess-intake/SKILL.md').is_file()\n"
        "assert 'speckit-assess-intake' in invocation\n"
        "print('ready ' + agent)\n",
        encoding="utf-8",
    )
    for key in ("claude", "codex"):
        monkeypatch.setattr(
            type(get_integration(key)), "build_exec_args",
            lambda self, prompt, **kwargs: [sys.executable, str(executable), self.key, prompt],
        )
        context = StepContext(
            inputs={"agent": key}, project_root=str(tmp_path), default_integration="claude",
        )
        executed = CommandStep().execute({
            "id": f"assess-{key}", "command": "speckit.assess.intake",
            "integration": "{{ inputs.agent }}", "capture": True,
        }, context)
        assert executed.status == StepStatus.COMPLETED, executed
        assert f"ready {key}" in executed.output["stdout"]
    assert (tmp_path / ".specify/integration.json").read_bytes() == before


@pytest.mark.parametrize("empty_registration", [False, True])
def test_presets_are_composed_for_all_integrations_without_losing_existing_overlay(
    tmp_path, monkeypatch, empty_registration,
):
    import yaml

    from specify_cli.presets import PresetManager

    prepare_project(tmp_path)
    source = tmp_path / "preset-source"
    source.mkdir()
    (source / "plan.md").write_text("---\ndescription: Effective plan\n---\n# Effective plan override\n")
    (source / "preset.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "preset": {"id": "effective-plan", "name": "Effective Plan", "version": "1.0.0", "description": "Test"},
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {"templates": [{"type": "command", "name": "speckit.plan", "file": "plan.md"}]},
    }), encoding="utf-8")
    PresetManager(tmp_path).install_from_directory(source, get_speckit_version())
    if empty_registration:
        monkeypatch.setattr(PresetManager, "_register_commands", lambda *a, **k: {})
        monkeypatch.setattr(PresetManager, "_register_skills", lambda *a, **k: {})
    added = add_assess(tmp_path, monkeypatch)
    if empty_registration:
        assert added.exit_code == 1, added.output
        assert "Missing preset invocation artifacts" in " ".join(added.output.split())
        return
    assert added.exit_code == 0, added.output
    for folder in (".claude/skills", ".agents/skills"):
        assert "# Effective plan override" in (tmp_path / folder / "speckit-plan/SKILL.md").read_text()


def test_add_restores_missing_and_preserves_modified_home_scoped_skills(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    project = tmp_path / "project"
    prepare_project(project, ("claude", "hermes"))
    missing = home / ".hermes/skills/speckit-plan/SKILL.md"
    missing.unlink()
    added = add_assess(project, monkeypatch)
    assert added.exit_code == 0, added.output
    assert missing.is_file()
    assert len(list((home / ".hermes/skills").glob("speckit-assess-*/SKILL.md"))) == 5
    missing.write_text("customized global skill\n")
    from specify_cli.integrations.refresh import refresh_installed_integrations

    result = refresh_installed_integrations(project)
    assert not result.success and "hermes" in result.failed
    assert missing.read_text() == "customized global skill\n"


def test_replacement_force_cannot_destroy_customized_extension_skill(tmp_path, monkeypatch):
    prepare_project(tmp_path)
    assert add_assess(tmp_path, monkeypatch).exit_code == 0
    customized = tmp_path / ".agents/skills/speckit-assess-intake/SKILL.md"
    customized.write_bytes(b"customized extension skill\n")
    result = add_assess(tmp_path, monkeypatch, "--force")
    assert result.exit_code == 1, result.output
    assert customized.read_bytes() == b"customized extension skill\n"
    assert (tmp_path / ".specify/extensions/assess/extension.yml").is_file()


def test_disabled_contributions_are_removed_during_full_refresh(tmp_path, monkeypatch):
    from specify_cli.extensions import ExtensionManager
    from specify_cli.integrations.refresh import refresh_installed_integrations

    prepare_project(tmp_path)
    assert add_assess(tmp_path, monkeypatch).exit_code == 0
    ExtensionManager(tmp_path).registry.update("assess", {"enabled": False})
    result = refresh_installed_integrations(tmp_path)
    assert result.success, result.failed
    for folder in (".claude/skills", ".agents/skills"):
        assert not list((tmp_path / folder).glob("speckit-assess-*/SKILL.md"))


def test_shared_customization_is_preserved_across_retries(tmp_path, monkeypatch):
    from specify_cli.integrations.refresh import refresh_installed_integrations

    prepare_project(tmp_path)
    assert add_assess(tmp_path, monkeypatch).exit_code == 0
    customized = tmp_path / ".specify/templates/spec-template.md"
    customized.write_bytes(b"my shared template\n")
    for _ in range(2):
        result = refresh_installed_integrations(tmp_path)
        assert not result.success
        assert "shared infrastructure" in result.failed
        assert customized.read_bytes() == b"my shared template\n"


def test_incompatible_destinations_cannot_invalidate_completed_integration(tmp_path, monkeypatch):
    prepare_project(tmp_path)
    original = (tmp_path / ".claude/skills/speckit-plan/SKILL.md").read_bytes()
    monkeypatch.setattr(
        type(get_integration("codex")), "skills_dest",
        lambda self, root: root / ".claude/skills",
    )
    result = add_assess(tmp_path, monkeypatch)
    assert result.exit_code == 1, result.output
    assert "Completed: claude" in result.output
    assert "Incompatible shared destination" in " ".join(result.output.split())
    assert (tmp_path / ".claude/skills/speckit-plan/SKILL.md").read_bytes() == original


def test_native_events_refresh_each_installed_integration_and_keep_user_settings(tmp_path, monkeypatch):
    import yaml

    prepare_project(tmp_path, ("claude", "copilot"), {"copilot": {"skills": True}})
    source = tmp_path / "event-source"
    source.mkdir()
    (source / "boot.md").write_text("---\ndescription: Boot\n---\n# Boot\n")
    (source / "extension.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "extension": {"id": "event-ready", "name": "Events", "version": "1.0.0", "description": "Test"},
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {"commands": [{"name": "speckit.event-ready.boot", "file": "boot.md"}]},
        "events": {"session_start": {"command": "speckit.event-ready.boot"}},
    }), encoding="utf-8")
    settings = tmp_path / ".claude/settings.json"
    settings.parent.mkdir(exist_ok=True)
    settings.write_text('{"user_setting": "keep"}\n')
    with monkeypatch.context() as scoped:
        scoped.chdir(tmp_path)
        result = CliRunner().invoke(app, ["extension", "add", "--dev", str(source)])
    assert result.exit_code == 0, result.output
    assert json.loads(settings.read_text())["user_setting"] == "keep"
    assert "speckit.event-ready.boot" in settings.read_text()
    hooks = list((tmp_path / ".github").rglob("*.json"))
    assert any("speckit.event-ready.boot" in path.read_text() for path in hooks)


def test_rendering_context_is_project_scoped_nested_and_reset_after_failure(tmp_path):
    from specify_cli import load_init_options
    from specify_cli.integration_runtime import registration_options

    root = tmp_path / "project"
    other = tmp_path / "other"
    prepare_project(root, ("claude",))
    prepare_project(other, ("codex",))
    before = (root / ".specify/init-options.json").read_bytes()
    with registration_options(root, {"ai": "copilot", "ai_skills": True}):
        assert load_init_options(root)["ai"] == "copilot"
        assert load_init_options(other)["ai"] == "codex"
        with pytest.raises(RuntimeError, match="nested"), registration_options(root, {"ai": "codex"}):
            assert load_init_options(root)["ai"] == "codex"
            raise RuntimeError("nested")
        assert load_init_options(root)["ai"] == "copilot"
    assert load_init_options(root)["ai"] == "claude"
    assert (root / ".specify/init-options.json").read_bytes() == before


def test_saved_raw_options_and_script_settings_are_used_without_rewriting_state(tmp_path, monkeypatch):
    prepare_project(tmp_path, ("claude", "copilot"), {"copilot": {"commands": True}})
    state_file = tmp_path / ".specify/integration.json"
    state = json.loads(state_file.read_text())
    setting = state["integration_settings"]["copilot"]
    setting.pop("parsed_options")
    setting["raw_options"] = "--commands"
    setting["script"] = "sh"
    state_file.write_text(json.dumps(state), encoding="utf-8")
    before = state_file.read_bytes()
    added = add_assess(tmp_path, monkeypatch)
    assert added.exit_code == 0, added.output
    agent = tmp_path / ".github/agents/speckit.assess.intake.agent.md"
    assert agent.is_file()
    assert state_file.read_bytes() == before
    core = (tmp_path / ".github/agents/speckit.plan.agent.md").read_text()
    assert ".specify/scripts/bash/" in core


@pytest.mark.parametrize("damage", ["corrupt", "symlink", "traversal"])
def test_invalid_manifest_cannot_authorize_output_changes(tmp_path, monkeypatch, damage):
    import hashlib

    prepare_project(tmp_path)
    manifest = tmp_path / ".specify/integrations/codex.manifest.json"
    outside = tmp_path.parent / f"{tmp_path.name}-outside.txt"
    outside.write_bytes(b"untouched\n")
    if damage == "corrupt":
        manifest.write_text("{bad json")
    elif damage == "symlink":
        manifest.unlink()
        try:
            manifest.symlink_to(outside)
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"Symlinks are unavailable: {exc}")
    else:
        data = json.loads(manifest.read_text())
        data["files"][f"../{outside.name}"] = hashlib.sha256(outside.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(data))
    added = add_assess(tmp_path, monkeypatch)
    assert added.exit_code == 1, added.output
    assert "Failed codex:" in added.output
    assert outside.read_bytes() == b"untouched\n"


def local_extension(root, monkeypatch, commands=("boot",), *, events=False):
    import yaml

    from specify_cli.extensions import _commands

    source = root / "review-source"
    source.mkdir(exist_ok=True)
    for command in commands:
        (source / f"{command}.md").write_text(f"---\ndescription: {command}\n---\n# {command}\n")
    data = {
        "schema_version": "1.0",
        "extension": {"id": "review-ready", "name": "Review", "version": "1.0.0", "description": "Test"},
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {"commands": [
            {"name": f"speckit.review-ready.{command}", "file": f"{command}.md"} for command in commands
        ]},
    }
    if events:
        data["events"] = {"session_start": {"command": "speckit.review-ready.boot"}}
    (source / "extension.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    original = _commands._locate_bundled_extension
    monkeypatch.setattr(
        _commands, "_locate_bundled_extension",
        lambda name: source if name == "review-ready" else original(name),
    )
    return source


def add_local(root, monkeypatch, *args):
    with monkeypatch.context() as scoped:
        scoped.chdir(root)
        return CliRunner().invoke(app, ["extension", "add", "review-ready", *args])


@pytest.mark.parametrize(("key", "relative"), [
    ("claude", ".specify/events.py"),
    ("opencode", ".opencode/plugin/speckit-events.ts"),
])
def test_stale_protection_does_not_authorize_overwriting_event_outputs(
    tmp_path, monkeypatch, key, relative,
):
    prepare_project(tmp_path, (key,))
    local_extension(tmp_path, monkeypatch, events=True)
    first = add_local(tmp_path, monkeypatch)
    assert first.exit_code == 0, first.output
    output = tmp_path / relative
    output.write_bytes(b"customized generated event output\n")
    added = add_assess(tmp_path, monkeypatch)
    assert added.exit_code == 1, added.output
    assert output.read_bytes() == b"customized generated event output\n"
    assert relative in added.output


@pytest.mark.parametrize("content", ['{broken', '{// JSONC\n"user": true\n}', '[]'])
@pytest.mark.parametrize(("key", "relative"), [
    ("claude", ".claude/settings.json"),
    ("copilot", ".vscode/settings.json"),
])
def test_skipped_required_settings_merge_cannot_claim_readiness(
    tmp_path, monkeypatch, key, relative, content,
):
    prepare_project(tmp_path, (key,), {"copilot": {"commands": True}})
    local_extension(tmp_path, monkeypatch, events=True)
    settings = tmp_path / relative
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(content, encoding="utf-8")
    before = settings.read_bytes()
    added = add_local(tmp_path, monkeypatch)
    assert added.exit_code == 1, added.output
    assert settings.read_bytes() == before
    assert relative in added.output
    assert "Extension installed successfully" not in added.output


@pytest.mark.parametrize("keys", [("none",), ("none", "claude"), ("claude", "none")])
def test_artifact_free_integration_needs_no_extension_or_preset_invocations(tmp_path, monkeypatch, keys):
    import yaml

    from specify_cli.presets import PresetManager

    prepare_project(tmp_path, keys)
    source = tmp_path / "preset-source"
    source.mkdir()
    (source / "plan.md").write_text("---\ndescription: Plan\n---\n# Effective plan\n")
    (source / "preset.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "preset": {"id": "review-plan", "name": "Plan", "version": "1.0.0", "description": "Test"},
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {"templates": [{"type": "command", "name": "speckit.plan", "file": "plan.md"}]},
    }), encoding="utf-8")
    PresetManager(tmp_path).install_from_directory(source, get_speckit_version())
    added = add_assess(tmp_path, monkeypatch)
    assert added.exit_code == 0, added.output
    assert IntegrationManifest.load("none", tmp_path).files == {}
    if "claude" in keys:
        assert len(list((tmp_path / ".claude/skills").glob("speckit-assess-*/SKILL.md"))) == 5
        assert "# Effective plan" in (tmp_path / ".claude/skills/speckit-plan/SKILL.md").read_text()


@pytest.mark.parametrize("customized", [False, True])
def test_legacy_generated_skills_are_verified_before_refresh(tmp_path, monkeypatch, customized):
    from specify_cli.extensions import ExtensionManager, _commands

    prepare_project(tmp_path)
    ExtensionManager(tmp_path).install_from_directory(_commands._locate_bundled_extension("assess"), get_speckit_version())
    output = tmp_path / ".claude/skills/speckit-assess-intake/SKILL.md"
    if customized:
        output.write_bytes(b"customized legacy skill\n")
    before = output.read_bytes()
    local_extension(tmp_path, monkeypatch)
    added = add_local(tmp_path, monkeypatch)
    assert added.exit_code == (1 if customized else 0), added.output
    if customized:
        assert output.read_bytes() == before
    else:
        contributions = json.loads((tmp_path / ".specify/integrations/.contributions/claude.manifest.json").read_text())
        assert ".claude/skills/speckit-assess-intake/SKILL.md" in contributions["files"]


@pytest.mark.parametrize("legacy", [False, True])
@pytest.mark.parametrize("drop_command", [False, True])
def test_generic_replacement_preserves_and_reconciles_verified_registration(
    tmp_path, monkeypatch, legacy, drop_command,
):
    from specify_cli.extensions import ExtensionManager

    prepare_project(tmp_path, ("generic",), {"generic": {"commands_dir": ".custom/prompts"}})
    source = local_extension(tmp_path, monkeypatch, ("boot", "retired"))
    if legacy:
        ExtensionManager(tmp_path).install_from_directory(source, get_speckit_version())
    else:
        first = add_local(tmp_path, monkeypatch)
        assert first.exit_code == 0, first.output
    if drop_command:
        local_extension(tmp_path, monkeypatch)
    (source / "boot.md").write_text("---\ndescription: Updated boot\n---\n# Updated boot\n")
    added = add_local(tmp_path, monkeypatch, "--force")
    assert added.exit_code == 0, added.output
    assert (tmp_path / ".custom/prompts/speckit.review-ready.boot.md").is_file()
    assert "# Updated boot" in (tmp_path / ".custom/prompts/speckit.review-ready.boot.md").read_text()
    assert (tmp_path / ".custom/prompts/speckit.review-ready.retired.md").exists() is not drop_command
    metadata = ExtensionManager(tmp_path).registry.get("review-ready")
    assert metadata["generic_artifact_hashes"]
    if drop_command:
        assert ".custom/prompts/speckit.review-ready.retired.md" not in metadata["generic_artifact_hashes"]


def test_generic_replacement_preserves_modified_obsolete_output_until_reconciled(tmp_path, monkeypatch):
    from specify_cli.extensions import ExtensionManager

    prepare_project(tmp_path, ("generic",), {"generic": {"commands_dir": ".custom/prompts"}})
    source = local_extension(tmp_path, monkeypatch, ("boot", "retired"))
    ExtensionManager(tmp_path).install_from_directory(source, get_speckit_version())
    obsolete = tmp_path / ".custom/prompts/speckit.review-ready.retired.md"
    original = obsolete.read_bytes()
    obsolete.write_bytes(b"customized obsolete command\n")
    local_extension(tmp_path, monkeypatch)
    added = add_local(tmp_path, monkeypatch, "--force")
    assert added.exit_code == 1, added.output
    assert obsolete.read_bytes() == b"customized obsolete command\n"
    obsolete.write_bytes(original)
    retried = add_local(tmp_path, monkeypatch, "--force")
    assert retried.exit_code == 0, retried.output
    assert not obsolete.exists()


@pytest.mark.parametrize("legacy", [False, True])
def test_replacement_does_not_orphan_unverified_legacy_commands(tmp_path, monkeypatch, legacy):
    from specify_cli.extensions import ExtensionManager

    prepare_project(tmp_path, ("claude",))
    source = local_extension(tmp_path, monkeypatch, ("boot", "retired"))
    if legacy:
        ExtensionManager(tmp_path).install_from_directory(source, get_speckit_version())
    else:
        first = add_local(tmp_path, monkeypatch)
        assert first.exit_code == 0, first.output
    obsolete = tmp_path / ".claude/skills/speckit-review-ready-retired/SKILL.md"
    before = obsolete.read_bytes()
    local_extension(tmp_path, monkeypatch)
    added = add_local(tmp_path, monkeypatch, "--force")
    assert added.exit_code == (1 if legacy else 0), added.output
    if legacy:
        assert obsolete.read_bytes() == before
        assert "Unverified obsolete extension output" in added.output
        metadata = ExtensionManager(tmp_path).registry.get("review-ready")
        assert "speckit.review-ready.retired" in metadata["registered_commands"]["claude"]
        obsolete.unlink()
        retried = add_local(tmp_path, monkeypatch, "--force")
        assert retried.exit_code == 0, retried.output
    assert not obsolete.exists()


def install_review_preset(root, command="speckit.plan", strategy="replace"):
    import yaml

    from specify_cli.presets import PresetManager

    source = root / "preset-source"
    source.mkdir()
    (source / "command.md").write_text("---\ndescription: Review preset\n---\n# Preset content\n{CORE_TEMPLATE}\n")
    (source / "preset.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "preset": {"id": "review-preset", "name": "Review", "version": "1.0.0", "description": "Test"},
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {"templates": [
            {"type": "command", "name": command, "file": "command.md", "strategy": strategy},
        ]},
    }), encoding="utf-8")
    PresetManager(root).install_from_directory(source, get_speckit_version())


@pytest.mark.parametrize("home_scoped", [False, True])
def test_intermediate_core_equality_cannot_authorize_preset_overwrite(tmp_path, monkeypatch, home_scoped):
    from specify_cli.integrations.refresh import refresh_installed_integrations

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    root = tmp_path / "project"
    key = "hermes" if home_scoped else "claude"
    prepare_project(root, (key,))
    output = (
        home / ".hermes/skills/speckit-plan/SKILL.md"
        if home_scoped else root / ".claude/skills/speckit-plan/SKILL.md"
    )
    core = output.read_bytes()
    install_review_preset(root)
    assert add_assess(root, monkeypatch).exit_code == 0
    assert output.read_bytes() != core
    output.write_bytes(core)
    result = refresh_installed_integrations(root)
    assert not result.success and key in result.failed
    assert output.read_bytes() == core


@pytest.mark.parametrize("empty_directory", [False, True])
def test_missing_core_sources_cannot_delete_existing_invocations(tmp_path, monkeypatch, empty_directory):
    prepare_project(tmp_path)
    output = tmp_path / ".agents/skills/speckit-plan/SKILL.md"
    before = output.read_bytes()
    source = tmp_path / "empty-commands"
    if empty_directory:
        source.mkdir()
    monkeypatch.setattr(type(get_integration("codex")), "shared_commands_dir", lambda self: source)
    added = add_assess(tmp_path, monkeypatch)
    assert added.exit_code == 1, added.output
    assert "Core command templates are unavailable" in " ".join(added.output.split())
    assert output.read_bytes() == before


@pytest.mark.parametrize("ownership", ["untracked", "customized", "managed"])
def test_legacy_qoder_retirement_requires_verified_ownership(tmp_path, monkeypatch, ownership):
    prepare_project(tmp_path, ("qodercli",))
    relative = ".qoder/commands/speckit.assess.intake.md"
    output = tmp_path / relative
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"old generated command\n")
    if ownership != "untracked":
        manifest = IntegrationManifest.load("qodercli", tmp_path)
        manifest.record_existing(relative)
        manifest.save()
    if ownership == "customized":
        output.write_bytes(b"my customized legacy command\n")
    before = output.read_bytes()
    added = add_assess(tmp_path, monkeypatch)
    assert added.exit_code == (0 if ownership == "managed" else 1), added.output
    if ownership == "managed":
        assert not output.exists()
    else:
        assert output.read_bytes() == before
        assert relative in added.output


@pytest.mark.parametrize("key", ["claude", "copilot"])
def test_failed_add_does_not_grant_removal_ownership_of_untracked_file(tmp_path, monkeypatch, key):
    from specify_cli.extensions import ExtensionManager

    prepare_project(tmp_path, (key,), {"copilot": {"commands": True}})
    output = tmp_path / (
        ".claude/skills/speckit-assess-intake/SKILL.md"
        if key == "claude" else ".github/agents/speckit.assess.intake.agent.md"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"my unrelated invocation\n")
    added = add_assess(tmp_path, monkeypatch)
    assert added.exit_code == 1, added.output
    assert output.read_bytes() == b"my unrelated invocation\n"
    assert ExtensionManager(tmp_path).remove("assess")
    assert output.read_bytes() == b"my unrelated invocation\n"


@pytest.mark.parametrize("strategy", ["wrap", "prepend", "append"])
@pytest.mark.parametrize("key", ["claude", "copilot"])
def test_no_base_preset_composition_does_not_block_unrelated_add(tmp_path, monkeypatch, strategy, key):
    prepare_project(tmp_path, (key,), {"copilot": {"commands": True}})
    with pytest.warns(UserWarning):
        install_review_preset(tmp_path, "speckit.absent.review", strategy)
    added = add_assess(tmp_path, monkeypatch)
    assert added.exit_code == 0, added.output
    directory = ".claude/skills" if key == "claude" else ".github/agents"
    assert not list((tmp_path / directory).glob("*absent*"))
    assert list((tmp_path / directory).glob("*assess*"))
