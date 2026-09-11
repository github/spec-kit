"""Rollback preserves real outputs after integration activation history."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from specify_cli import save_init_options
from specify_cli.agents import CommandRegistrar
from specify_cli.bundler import BundlerError
from specify_cli.bundler.models.manifest import BundleManifest
from specify_cli.bundler.models.records import records_path
from specify_cli.bundler.services.adapters import DefaultPrimitiveInstaller
from specify_cli.bundler.services.installer import install_bundle, remove_bundle
from specify_cli.bundler.services.resolver import resolve_install_plan
from specify_cli.extensions import ExtensionManager
from specify_cli.presets import PresetManager
from tests.bundler_helpers import make_project, valid_manifest_dict


@pytest.fixture(params=["presets", "extensions"])
def artifact_project(tmp_path, monkeypatch, request):
    from specify_cli import _assets

    kind = request.param
    project = make_project(tmp_path / "project")
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: home)
    sources = tmp_path / "sources"
    singular = kind[:-1]
    for component_id in ("owned", "keeper"):
        source = sources / component_id
        source.mkdir(parents=True)
        command = {
            "name": f"speckit.{component_id}.check",
            "file": "command.md",
            "aliases": [f"speckit.{component_id}.short"],
        }
        provides = (
            {"templates": [{"type": "command", **command}]}
            if kind == "presets" else {"commands": [command]}
        )
        (source / f"{singular}.yml").write_text(yaml.safe_dump({
            "schema_version": "1.0",
            singular: {
                "id": component_id, "name": component_id, "version": "1.0.0",
                "description": "Artifact restoration",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": provides,
        }), encoding="utf-8")
        (source / "command.md").write_text(
            f"---\ndescription: {component_id} command\n---\n"
            f"ORIGINAL {component_id} BODY\n",
            encoding="utf-8",
        )
    monkeypatch.setattr(
        _assets, f"_locate_bundled_{singular}", lambda cid: sources / cid
    )

    def plan(ids):
        manifest = BundleManifest.from_dict(valid_manifest_dict(provides={
            kind: [
                {"id": cid, "version": "1.0.0",
                 **({"priority": 10, "strategy": "replace"} if kind == "presets" else {})}
                for cid in ids
            ],
        }))
        return resolve_install_plan(
            manifest, speckit_version="1.0.7", active_integration=None
        )

    def activate(agent, skills):
        registrar = CommandRegistrar()
        registrar._resolve_agent_dir(
            agent, registrar.AGENT_CONFIGS[agent], project
        ).mkdir(parents=True, exist_ok=True)
        save_init_options(project, {"ai": agent, "ai_skills": skills, "script": "sh"})

    manager_type = PresetManager if kind == "presets" else ExtensionManager
    return project, home, manager_type, DefaultPrimitiveInstaller(allow_network=False), plan, activate


def artifact_files(project, home):
    return {
        path: path.read_bytes()
        for root in (project, home)
        for path in root.rglob("*")
        if path.is_file() and ".specify" not in path.relative_to(root).parts
    }


def install_history(
    artifact_project, historical_agent, skills, current_registered=True
):
    project, home, manager_type, installer, plan, activate = artifact_project
    activate(historical_agent, skills)
    install_bundle(project, plan(["owned", "keeper"]), installer)
    historical_files = artifact_files(project, home)
    assert any(b"ORIGINAL owned BODY" in body for body in historical_files.values())
    for path, body in historical_files.items():
        if path.name == "SKILL.md" and b"ORIGINAL owned BODY" in body:
            (path.parent / "user-support.txt").write_text("keep support", encoding="utf-8")

    current_agent = "gemini" if historical_agent != "gemini" else "copilot"
    activate(current_agent, False)
    manager = manager_type(project)
    if current_registered:
        if manager_type is PresetManager:
            manager.register_enabled_presets_for_agent(current_agent)
        else:
            manager.register_enabled_extensions_for_agent(current_agent)
    metadata = {**manager.registry.get("owned"), "enabled": False}
    manager.registry.restore("owned", metadata)
    before = artifact_files(project, home)
    original_record = records_path(project).read_bytes()
    return metadata, before, original_record


@pytest.mark.parametrize(
    ("historical_agent", "skills"),
    [("claude", True), ("gemini", False), ("copilot", False),
     ("copilot", True), ("codex", True), ("hermes", True)],
)
@pytest.mark.parametrize("operation", ["refresh", "drop", "remove"])
@pytest.mark.parametrize("current_registered", [False, True])
def test_failed_bundle_change_restores_historical_outputs(
    artifact_project, monkeypatch, historical_agent, skills, operation, current_registered
):
    project, home, manager_type, installer, plan, _ = artifact_project
    metadata, before, original_record = install_history(
        artifact_project, historical_agent, skills, current_registered
    )

    def fail_save(*_args):
        raise OSError("record write refused")

    monkeypatch.setattr("specify_cli.bundler.services.installer.save_records", fail_save)
    with pytest.raises(BundlerError, match="record write refused"):
        if operation == "remove":
            remove_bundle(project, "demo-bundle", installer)
        else:
            install_bundle(
                project,
                plan(["owned", "keeper"] if operation == "refresh" else ["keeper"]),
                installer, refresh=True,
            )
    assert artifact_files(project, home) == before
    assert manager_type(project).registry.get("owned") == metadata
    assert records_path(project).read_bytes() == original_record


@pytest.mark.parametrize("failure", ["snapshot", "restore"])
def test_artifact_io_failures_preserve_state_or_report_incomplete_recovery(
    artifact_project, monkeypatch, failure
):
    import shutil

    from specify_cli.bundler.services import artifacts

    project, home, manager_type, installer, _, _ = artifact_project
    metadata, before, original_record = install_history(
        artifact_project, "gemini", False, current_registered=False
    )
    target = project / ".gemini/commands/speckit.owned.check.toml"
    copy_file = shutil.copy2

    def fail_artifact_copy(source, destination, *args, **kwargs):
        attempted = source if failure == "snapshot" else destination
        if Path(attempted) == target:
            raise PermissionError("artifact I/O denied")
        return copy_file(source, destination, *args, **kwargs)

    def fail_save(*_args):
        raise OSError("record write refused")

    monkeypatch.setattr(artifacts.shutil, "copy2", fail_artifact_copy)
    if failure == "restore":
        monkeypatch.setattr("specify_cli.bundler.services.installer.save_records", fail_save)
    message = "artifact I/O denied" if failure == "snapshot" else "Rollback was incomplete"
    with pytest.raises(BundlerError, match=message):
        remove_bundle(project, "demo-bundle", installer)
    assert records_path(project).read_bytes() == original_record
    if failure == "snapshot":
        assert artifact_files(project, home) == before
        assert manager_type(project).registry.get("owned") == metadata
    else:
        assert not target.exists()
        for path, body in before.items():
            if "keeper" in str(path):
                assert path.read_bytes() == body


def test_legacy_detection_does_not_leave_new_agent_outputs_after_rollback(
    artifact_project, monkeypatch
):
    project, home, _, installer, _, _ = artifact_project
    _, before, original_record = install_history(
        artifact_project, "gemini", False, current_registered=False
    )
    (project / ".specify/init-options.json").unlink()

    def fail_save(*_args):
        raise OSError("record write refused")

    monkeypatch.setattr("specify_cli.bundler.services.installer.save_records", fail_save)
    with pytest.raises(BundlerError, match="record write refused"):
        remove_bundle(project, "demo-bundle", installer)
    assert artifact_files(project, home) == before
    assert records_path(project).read_bytes() == original_record
