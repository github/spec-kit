"""Rollback coverage for extension lifecycle mutations (#4659 review round 3).

Covers the three correctness findings that are not test- or doc-only:

* ``extension disable`` cleanup must be transactional across historical agents,
  so a failure part-way through cannot leave the extension enabled while some
  agents' artifacts are already gone.
* ``extension enable`` must snapshot conventional command candidates, not only
  manifest-declared ones, or a regex selector can create global skill
  directories that rollback never removes.
* ``extension set-priority`` must reconcile strictly and roll the priority back
  when selector-backed artifacts cannot be recomposed, instead of reporting a
  change that never reached the outputs.
"""

from __future__ import annotations

import yaml
from typer.testing import CliRunner

from specify_cli import app, save_init_options
from specify_cli.extensions import ExtensionManager
from specify_cli.extensions._commands import _snapshot_command_candidates
from specify_cli.presets import PresetManager
from tests.specify_cli.presets.test_install_transaction import tree_state
from tests.specify_cli.presets.test_selector_provider_lifecycle import (
    COMMAND,
    extension,
    preset,
    project,
)

SHARED_COMMAND = "speckit.alpha.collect"
SELECTOR = r"regex:speckit\.alpha\..*"


def _install_extension_for_two_agents(root, source):
    """Install an extension and register its artifacts for two agents."""
    manager = ExtensionManager(root)
    manager.install_from_directory(source, "0.1.5")
    manager.register_enabled_extensions_for_agent("codex", strict=True)
    metadata = ExtensionManager(root).registry.get("provider")
    assert metadata is not None
    assert set(metadata.get("registered_commands", {})) >= {"gemini", "codex"}
    return manager


# ---------------------------------------------------------------------------
# Scenario A/B: extension disable is transactional (HIGH finding)
# ---------------------------------------------------------------------------


def test_disable_failure_restores_every_agent(tmp_path, monkeypatch):
    """First agent cleanup succeeds, second raises: nothing may stay stripped."""
    root = project(tmp_path, monkeypatch)
    _install_extension_for_two_agents(root, extension(tmp_path))
    gemini = root / ".gemini" / "commands" / f"{COMMAND}.toml"
    codex = root / ".agents" / "skills" / "speckit-provider-collect" / "SKILL.md"
    assert gemini.exists()
    assert codex.exists()
    before = tree_state(root)
    registry_before = ExtensionManager(root).registry.get("provider")
    assert registry_before is not None

    original = ExtensionManager.unregister_agent_artifacts
    calls: list[str] = []

    def flaky(self, agent_name, **kwargs):
        calls.append(agent_name)
        if len(calls) == 2:
            raise OSError("second agent cleanup failed")
        return original(self, agent_name, **kwargs)

    monkeypatch.setattr(ExtensionManager, "unregister_agent_artifacts", flaky)

    result = CliRunner().invoke(app, ["extension", "disable", "provider"])

    # The command must fail loudly rather than claim success.
    assert result.exit_code != 0
    assert "second agent cleanup failed" in (result.output + str(result.exception))
    assert "disabled" not in result.output
    assert len(calls) == 2, calls

    # Registry and every agent's filesystem state are back to the pre-state.
    after_metadata = ExtensionManager(root).registry.get("provider")
    assert after_metadata is not None
    assert after_metadata.get("enabled", True) is True
    assert after_metadata.get("registered_commands") == registry_before.get(
        "registered_commands"
    )
    assert tree_state(root) == before
    assert gemini.exists()
    assert codex.exists()


def test_disable_success_cleans_every_agent(tmp_path, monkeypatch):
    """All cleanups succeed: both agents are stripped and the extension is off."""
    root = project(tmp_path, monkeypatch)
    _install_extension_for_two_agents(root, extension(tmp_path))
    gemini = root / ".gemini" / "commands" / f"{COMMAND}.toml"
    codex = root / ".agents" / "skills" / "speckit-provider-collect" / "SKILL.md"
    assert gemini.exists()
    assert codex.exists()

    result = CliRunner().invoke(app, ["extension", "disable", "provider"])

    assert result.exit_code == 0, result.output
    assert not gemini.exists()
    assert not codex.exists()
    metadata = ExtensionManager(root).registry.get("provider")
    assert metadata is not None
    assert metadata["enabled"] is False
    assert metadata.get("registered_commands", {}) == {}
    assert metadata.get("registered_skills", {}) in ({}, [])


def test_disable_rollback_failure_is_reported(tmp_path, monkeypatch):
    """A rollback that itself fails must surface both errors, never success."""
    root = project(tmp_path, monkeypatch)
    _install_extension_for_two_agents(root, extension(tmp_path))

    from specify_cli.presets._transaction import _ArtifactSnapshot

    original_unregister = ExtensionManager.unregister_agent_artifacts
    calls: list[str] = []

    def flaky(self, agent_name, **kwargs):
        calls.append(agent_name)
        if len(calls) == 2:
            raise OSError("second agent cleanup failed")
        return original_unregister(self, agent_name, **kwargs)

    def exploding_restore(self):
        raise OSError("snapshot restore failed")

    monkeypatch.setattr(ExtensionManager, "unregister_agent_artifacts", flaky)
    monkeypatch.setattr(_ArtifactSnapshot, "restore", exploding_restore)

    result = CliRunner().invoke(app, ["extension", "disable", "provider"])

    assert result.exit_code != 0
    assert "second agent cleanup failed" in (result.output + str(result.exception))
    assert "disabled" not in result.output
    notes = getattr(result.exception, "__notes__", [])
    assert any("rollback failed" in note for note in notes), notes
    assert any("snapshot restore failed" in note for note in notes), notes


# ---------------------------------------------------------------------------
# Phase 4: enable snapshot covers conventional command candidates (MEDIUM)
# ---------------------------------------------------------------------------


def test_enable_rollback_removes_selector_global_skill(tmp_path, monkeypatch):
    """A selector-matched conventional command must not survive enable rollback."""
    root = tmp_path / "project"
    (root / ".specify").mkdir(parents=True)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: home)
    # Hermes materialises preset skills into a global skills root, which is the
    # layout that exposes the missing conventional-candidate snapshots.
    save_init_options(root, {"ai": "hermes", "ai_skills": True, "script": "sh"})
    monkeypatch.chdir(root)

    source = _extension_source(
        tmp_path,
        "provider",
        "speckit.provider.declared",
        "DECLARED BODY",
        conventional_name=COMMAND,
        conventional_body="EXTENSION BODY",
    )
    manager = ExtensionManager(root)
    manager.install_from_directory(source, "0.1.5")
    manager.registry.update("provider", {"enabled": False})

    PresetManager(root).install_from_directory(
        preset(tmp_path, "selector", r"regex:speckit\.provider\..*", "SELECTOR BODY"),
        "0.1.5",
        priority=5,
    )

    # The conventional candidate is exactly what the resolver can match, and it
    # must be part of the snapshot seed set.
    manifest = manager.get_extension("provider")
    assert manifest is not None
    candidates = _snapshot_command_candidates(manager, manifest)
    assert COMMAND in candidates, candidates
    assert not any(name.startswith("regex:") for name in candidates)

    global_skills = tmp_path / "home" / ".hermes" / "skills"
    created = (
        list(global_skills.glob("speckit-provider-*")) if global_skills.is_dir() else []
    )

    from specify_cli.extensions import HookExecutor

    def failing_save(self, config):
        raise OSError("hook step failed")

    # Seed a hook for this extension so the enable path reaches the hook write,
    # then take the baseline: the seeded config is part of the restored state.
    (root / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump(
            {"hooks": {"after_tasks": [{"extension": "provider", "elidable": True}]}}
        )
    )
    before = tree_state(root)
    monkeypatch.setattr(HookExecutor, "save_project_config", failing_save)

    result = CliRunner().invoke(app, ["extension", "enable", "provider"])

    assert result.exit_code != 0
    assert "hook step failed" in (result.output + str(result.exception))
    metadata = ExtensionManager(root).registry.get("provider")
    assert metadata is not None
    assert metadata.get("enabled", True) is False
    # No newly written global skill may survive the rollback.
    after = (
        list(global_skills.glob("speckit-provider-*")) if global_skills.is_dir() else []
    )
    assert len(after) <= len(created), (created, after)
    assert tree_state(root) == before


# ---------------------------------------------------------------------------
# Phase 5: extension priority uses a strict transaction (MEDIUM)
# ---------------------------------------------------------------------------


def _extension_source(
    tmp_path,
    extension_id,
    declared_name,
    body,
    conventional_name=None,
    conventional_body=None,
):
    """Build an extension source, optionally shipping a conventional command file.

    Primary extension command names are namespace-validated, so a second
    provider can only layer on the same concrete command through the documented
    conventional filename lookup (``commands/<concrete-name>.md``).
    """
    source = tmp_path / f"{extension_id}-source"
    (source / "commands").mkdir(parents=True, exist_ok=True)
    (source / "commands" / "body.md").write_text(
        f"---\ndescription: {extension_id}\n---\n{body}\n"
    )
    if conventional_name is not None:
        (source / "commands" / f"{conventional_name}.md").write_text(
            f"---\ndescription: {extension_id}\n---\n{conventional_body}\n"
        )
    (source / "extension.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "extension": {
                    "id": extension_id,
                    "name": extension_id,
                    "version": "1.0.0",
                    "description": "Test",
                    "author": "Test",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "commands": [
                        {
                            "name": declared_name,
                            "file": "commands/body.md",
                            "description": "Test",
                        }
                    ]
                },
            }
        )
    )
    return source


def _priority_project(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    manager = ExtensionManager(root)
    # alpha declares the concrete command directly; beta reaches the same
    # concrete name only through its conventional command filename, which is
    # what makes the extension priority decide the composition base.
    manager.install_from_directory(
        _extension_source(tmp_path, "alpha", SHARED_COMMAND, "ALPHA BODY"),
        "0.1.5",
        priority=10,
    )
    manager.install_from_directory(
        _extension_source(
            tmp_path,
            "beta",
            "speckit.beta.collect",
            "BETA BODY",
            conventional_name=SHARED_COMMAND,
            conventional_body="BETA BODY",
        ),
        "0.1.5",
        priority=20,
    )
    PresetManager(root).install_from_directory(
        preset(tmp_path, "selector", SELECTOR, "SELECTOR BODY", strategy="append"),
        "0.1.5",
        priority=5,
    )
    return root, root / ".gemini" / "commands" / f"{SHARED_COMMAND}.toml"


def test_set_priority_recomposes_and_commits(tmp_path, monkeypatch):
    root, output = _priority_project(tmp_path, monkeypatch)
    text = output.read_text()
    assert "ALPHA BODY" in text and "BETA BODY" not in text

    result = CliRunner().invoke(app, ["extension", "set-priority", "alpha", "30"])

    assert result.exit_code == 0, result.output
    text = output.read_text()
    assert "BETA BODY" in text
    assert "ALPHA BODY" not in text
    assert "SELECTOR BODY" in text
    alpha = ExtensionManager(root).registry.get("alpha")
    assert alpha is not None
    assert alpha["priority"] == 30


def test_set_priority_failure_rolls_back_everything(tmp_path, monkeypatch):
    root, output = _priority_project(tmp_path, monkeypatch)
    before = tree_state(root)
    registry_before = ExtensionManager(root).registry.get("alpha")
    text_before = output.read_text()

    original = PresetManager.register_enabled_presets_for_agent

    def failing_reconcile(self, agent_name, **kwargs):
        if kwargs.get("strict"):
            raise OSError("selector reconciliation failed")
        return original(self, agent_name, **kwargs)

    monkeypatch.setattr(
        PresetManager, "register_enabled_presets_for_agent", failing_reconcile
    )

    result = CliRunner().invoke(app, ["extension", "set-priority", "alpha", "30"])

    assert result.exit_code != 0
    assert "selector reconciliation failed" in (result.output + str(result.exception))
    assert "priority changed" not in result.output

    # Priority, registry ownership, and the composed artifact all roll back.
    alpha_after = ExtensionManager(root).registry.get("alpha")
    assert alpha_after is not None
    assert alpha_after == registry_before
    assert alpha_after["priority"] == 10
    assert output.read_text() == text_before
    assert tree_state(root) == before
