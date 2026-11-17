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
