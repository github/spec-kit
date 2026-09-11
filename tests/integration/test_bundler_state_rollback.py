"""Rollback through real primitive managers; only artifact lookup and save fail."""
from __future__ import annotations

import pytest
import yaml

from specify_cli.bundler import BundlerError
from specify_cli.bundler.models.manifest import BundleManifest
from specify_cli.bundler.models.records import records_path
from specify_cli.bundler.services.adapters import DefaultPrimitiveInstaller
from specify_cli.bundler.services.installer import install_bundle, remove_bundle
from specify_cli.bundler.services.resolver import resolve_install_plan
from tests.bundler_helpers import make_project, valid_manifest_dict


@pytest.fixture(params=["extensions", "presets"])
def installed_components(tmp_path, monkeypatch, request):
    from specify_cli import _assets
    from specify_cli.extensions import ExtensionManager, HookExecutor
    from specify_cli.presets import PresetManager

    kind = request.param
    singular = kind[:-1]
    project = tmp_path / "project"
    make_project(project)
    sources = tmp_path / "sources"
    for component_id in ("owned", "keeper"):
        source = sources / component_id
        source.mkdir(parents=True)
        data = {
            "schema_version": "1.0",
            singular: {
                "id": component_id,
                "name": component_id,
                "version": "1.0.0",
                "description": "Rollback fixture",
            },
            "requires": {"speckit_version": ">=0.1.0"},
        }
        if kind == "extensions":
            data["provides"] = {"commands": [{
                "name": f"speckit.{component_id}.check",
                "file": "content.md",
            }]}
            data["hooks"] = {"after_tasks": {
                "command": f"speckit.{component_id}.check",
                "optional": True,
            }}
        else:
            data["provides"] = {"templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "content.md",
            }]}
        (source / f"{singular}.yml").write_text(
            yaml.safe_dump(data), encoding="utf-8"
        )
        (source / "content.md").write_text("# Original\n", encoding="utf-8")

    monkeypatch.setattr(
        _assets, f"_locate_bundled_{singular}", lambda cid: sources / cid
    )

    def plan(ids):
        manifest = BundleManifest.from_dict(valid_manifest_dict(
            provides={kind: [
                {
                    "id": cid,
                    "version": "1.0.0",
                    **({"priority": 10, "strategy": "replace"} if kind == "presets" else {}),
                }
                for cid in ids
            ]}
        ))
        return resolve_install_plan(
            manifest, speckit_version="1.0.6", active_integration="copilot"
        )

    installer = DefaultPrimitiveInstaller(allow_network=False)
    initial = plan(["owned", "keeper"])
    install_bundle(project, initial, installer)
    manager_type = ExtensionManager if kind == "extensions" else PresetManager
    registry = manager_type(project).registry
    original_metadata = {
        **registry.get("owned"),
        "enabled": False,
        "installed_at": "2020-01-02T03:04:05+00:00",
        "priority": 7,
        "user_settings": {"keep": ["original"]},
    }
    registry.restore("owned", original_metadata)
    payload = project / ".specify" / kind / "owned"
    (payload / "owned-config.yml").write_text(
        "setting: customized\n", encoding="utf-8"
    )
    if kind == "extensions":
        HookExecutor(project).disable_hooks("owned")
    yield project, kind, manager_type, installer, plan, original_metadata


@pytest.mark.parametrize("operation", ["refresh", "drop", "remove"])
def test_save_failure_restores_complete_installed_state(
    installed_components, monkeypatch, operation
):
    from specify_cli.extensions import HookExecutor

    project, kind, manager_type, installer, plan, metadata = installed_components
    original_record = records_path(project).read_bytes()
    original_hooks = (
        HookExecutor(project).get_project_config()["hooks"]
        if kind == "extensions" else None
    )
    payload = project / ".specify" / kind / "owned"
    original_config = (payload / "owned-config.yml").read_bytes()

    def fail_save(*_args):
        raise OSError("provenance write refused")

    monkeypatch.setattr(
        "specify_cli.bundler.services.installer.save_records", fail_save
    )
    with pytest.raises(BundlerError, match="provenance write refused"):
        if operation == "remove":
            remove_bundle(project, "demo-bundle", installer)
        else:
            install_bundle(
                project,
                plan(["owned", "keeper"] if operation == "refresh" else ["keeper"]),
                installer,
                refresh=True,
            )

    assert manager_type(project).registry.get("owned") == metadata
    assert (payload / "owned-config.yml").read_bytes() == original_config
    assert records_path(project).read_bytes() == original_record
    if original_hooks is not None:
        assert HookExecutor(project).get_project_config()["hooks"] == original_hooks


@pytest.mark.parametrize("installed_components", ["extensions"], indirect=True)
@pytest.mark.parametrize("backup_state", ["absent", "empty", "contents"])
@pytest.mark.parametrize("operation", ["refresh", "drop", "remove"])
def test_save_failure_restores_extension_backup_preimage(
    installed_components, monkeypatch, backup_state, operation,
):
    from specify_cli import _assets

    project, _, manager_type, installer, plan, metadata = installed_components
    backup_root = project / ".specify/extensions/.backup"
    if backup_state != "absent":
        owned_backup = backup_root / "owned"
        owned_backup.mkdir(parents=True)
        unrelated = backup_root / "unrelated"
        unrelated.mkdir()
        (unrelated / "saved-config.yml").write_text("unrelated\n", encoding="utf-8")
        if backup_state == "contents":
            (owned_backup / "owned-config.yml").write_text(
                "setting: previous backup\n", encoding="utf-8"
            )
            (owned_backup / "notes").mkdir()
            (owned_backup / "notes/context.txt").write_text(
                "retained backup context\n", encoding="utf-8"
            )

    def backup_tree():
        if not backup_root.exists():
            return None
        return {
            str(path.relative_to(backup_root)): path.read_bytes() if path.is_file() else None
            for path in backup_root.rglob("*")
        }

    before = backup_tree()
    original_record = records_path(project).read_bytes()
    source = _assets._locate_bundled_extension("owned")
    (source / "replacement-config.yml").write_text("new defaults\n", encoding="utf-8")

    def fail_save(*_args):
        raise OSError("provenance write refused")

    monkeypatch.setattr("specify_cli.bundler.services.installer.save_records", fail_save)
    with pytest.raises(BundlerError, match="provenance write refused"):
        if operation == "remove":
            remove_bundle(project, "demo-bundle", installer)
        else:
            install_bundle(
                project,
                plan(["owned", "keeper"] if operation == "refresh" else ["keeper"]),
                installer, refresh=True,
            )
    assert backup_tree() == before
    assert manager_type(project).registry.get("owned") == metadata
    assert records_path(project).read_bytes() == original_record
    assert not (project / ".specify/extensions/owned/replacement-config.yml").exists()


@pytest.mark.parametrize("installed_components", ["extensions"], indirect=True)
@pytest.mark.parametrize("failure", ["snapshot", "restore"])
def test_extension_backup_io_failure_is_reported(
    installed_components, monkeypatch, failure,
):
    import shutil
    from pathlib import Path

    project, _, manager_type, installer, _, metadata = installed_components
    backup = project / ".specify/extensions/.backup/owned"
    backup.mkdir(parents=True)
    original = backup / "owned-config.yml"
    original.write_text("prior backup\n", encoding="utf-8")
    original_record = records_path(project).read_bytes()
    copy_tree = shutil.copytree

    def fail_copy(source, destination, *args, **kwargs):
        attempted = source if failure == "snapshot" else destination
        if Path(attempted) == backup:
            raise PermissionError("backup I/O denied")
        return copy_tree(source, destination, *args, **kwargs)

    def fail_save(*_args):
        raise OSError("provenance write refused")

    monkeypatch.setattr("specify_cli.bundler.services.artifacts.shutil.copytree", fail_copy)
    if failure == "restore":
        monkeypatch.setattr("specify_cli.bundler.services.installer.save_records", fail_save)
    message = "backup I/O denied" if failure == "snapshot" else "Rollback was incomplete"
    with pytest.raises(BundlerError, match=message):
        remove_bundle(project, "demo-bundle", installer)
    assert manager_type(project).registry.get("owned") == metadata
    assert records_path(project).read_bytes() == original_record
    if failure == "snapshot":
        assert original.read_text(encoding="utf-8") == "prior backup\n"
    else:
        assert not backup.exists()


@pytest.mark.parametrize("operation", ["refresh", "remove"])
@pytest.mark.parametrize(
    "scenario", ["success", "save-failure", "rollback-failure", "capture-failure"]
)
def test_snapshot_cleanup_failure_preserves_transaction_outcome(
    installed_components, monkeypatch, caplog, operation, scenario,
):
    import shutil
    from pathlib import Path
    from tempfile import TemporaryDirectory

    project, kind, manager_type, installer, plan, metadata = installed_components
    original_record = records_path(project).read_bytes()
    cleanup = TemporaryDirectory.cleanup
    copy_tree = shutil.copytree
    attempted = []

    def deny_cleanup(directory):
        if Path(directory.name).name.startswith("speckit-bundle-rollback-"):
            attempted.append(directory)
            raise PermissionError("snapshot cleanup denied")
        return cleanup(directory)

    def fail_copy(source, destination, *args, **kwargs):
        if Path(source) == project / ".specify" / kind / "owned":
            raise PermissionError("snapshot copy refused")
        return copy_tree(source, destination, *args, **kwargs)

    def fail_save(*_args):
        raise OSError("provenance write refused")

    def fail_restore(*_args):
        raise OSError("restoration refused")

    def change():
        if operation == "remove":
            return remove_bundle(project, "demo-bundle", installer)
        return install_bundle(project, plan(["owned", "keeper"]), installer, refresh=True)

    monkeypatch.setattr(TemporaryDirectory, "cleanup", deny_cleanup)
    if scenario in ("save-failure", "rollback-failure"):
        monkeypatch.setattr("specify_cli.bundler.services.installer.save_records", fail_save)
    if scenario == "rollback-failure":
        monkeypatch.setattr(installer, "restore", fail_restore)
    if scenario == "capture-failure":
        monkeypatch.setattr(shutil, "copytree", fail_copy)
    try:
        if scenario == "success":
            assert change().changed
            assert (manager_type(project).registry.get("owned") is not None) == (
                operation == "refresh"
            )
        else:
            message = (
                "snapshot copy refused" if scenario == "capture-failure"
                else "provenance write refused"
            )
            with pytest.raises(BundlerError, match=message) as error:
                change()
            assert ("Rollback was incomplete" in str(error.value)) == (
                scenario == "rollback-failure"
            )
            assert records_path(project).read_bytes() == original_record
            if scenario != "rollback-failure":
                assert manager_type(project).registry.get("owned") == metadata
    finally:
        for directory in attempted:
            cleanup(directory)
    assert attempted
    assert "snapshot cleanup denied" in caplog.text
    for directory in attempted:
        assert directory.name in caplog.text


@pytest.mark.parametrize("kind", ["steps", "workflows"])
def test_dropped_component_restores_local_payload_and_exact_registry(
    tmp_path, monkeypatch, kind
):
    from specify_cli.bundler.models.manifest import ComponentRef
    from specify_cli.bundler.models.records import InstalledBundleRecord, save_records
    from specify_cli.bundler.services.resolver import InstallPlan
    from specify_cli.workflows.catalog import StepRegistry, WorkflowRegistry

    make_project(tmp_path)
    registry_type = StepRegistry if kind == "steps" else WorkflowRegistry
    registry = registry_type(tmp_path)
    payload = tmp_path / ".specify" / "workflows"
    if kind == "steps":
        payload /= "steps"
    payload /= "owned"
    payload.mkdir(parents=True)
    if kind == "steps":
        data = {"step": {"type_key": "owned", "version": "1.0.0"}}
        (payload / "__init__.py").write_text("# original package\n", encoding="utf-8")
    else:
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "owned", "name": "Owned", "version": "1.0.0"},
            "steps": [{"id": "check", "type": "shell", "run": "echo original"}],
        }
    (payload / ("step.yml" if kind == "steps" else "workflow.yml")).write_text(
        yaml.safe_dump(data), encoding="utf-8"
    )
    (payload / "settings.txt").write_text("user customization", encoding="utf-8")
    registry.add("owned", {
        "name": "Owned", "version": "1.0.0", "enabled": False,
        "source": "local", "user_settings": {"keep": ["original"]},
    })
    metadata = dict(registry.get("owned"))
    component = ComponentRef(kind=kind, id="owned", version="1.0.0")
    save_records(tmp_path, [InstalledBundleRecord.create(
        bundle_id="demo", version="1.0.0", components=[component]
    )])
    original_record = records_path(tmp_path).read_bytes()

    def fail_save(*_args):
        raise OSError("provenance write refused")

    monkeypatch.setattr(
        "specify_cli.bundler.services.installer.save_records", fail_save
    )
    with pytest.raises(BundlerError, match="provenance write refused"):
        install_bundle(
            tmp_path,
            InstallPlan(
                bundle_id="demo", version="2.0.0", role="developer",
                effective_integration=None, components=[],
            ),
            DefaultPrimitiveInstaller(allow_network=False),
            refresh=True,
        )
    assert registry_type(tmp_path).get("owned") == metadata
    assert (payload / "settings.txt").read_text(encoding="utf-8") == "user customization"
    assert records_path(tmp_path).read_bytes() == original_record


@pytest.mark.parametrize("operation", ["refresh", "drop", "remove"])
def test_primitive_failure_restores_the_mutated_component(
    installed_components, monkeypatch, operation
):
    project, kind, manager_type, installer, plan, metadata = installed_components
    original_record = records_path(project).read_bytes()
    method = "refresh" if operation == "refresh" else "remove"
    mutate = getattr(installer, method)

    def mutate_then_fail(root, component):
        mutate(root, component)
        if component.id == "owned":
            raise BundlerError("primitive interrupted")

    monkeypatch.setattr(installer, method, mutate_then_fail)
    with pytest.raises(BundlerError, match="primitive interrupted"):
        if operation == "remove":
            remove_bundle(project, "demo-bundle", installer)
        else:
            install_bundle(
                project,
                plan(["owned", "keeper"] if operation == "refresh" else ["keeper"]),
                installer, refresh=True,
            )
    assert manager_type(project).registry.get("owned") == metadata
    assert (
        project / ".specify" / kind / "owned" / "owned-config.yml"
    ).read_text(encoding="utf-8") == "setting: customized\n"
    assert records_path(project).read_bytes() == original_record


@pytest.mark.parametrize("operation", ["drop", "remove"])
def test_rollback_restores_steps_before_workflows_that_use_them(
    tmp_path, monkeypatch, operation
):
    from specify_cli.bundler.models.manifest import ComponentRef
    from specify_cli.bundler.models.records import InstalledBundleRecord, save_records
    from specify_cli.bundler.services.resolver import InstallPlan
    from specify_cli.workflows import load_custom_steps
    from specify_cli.workflows.catalog import StepRegistry, WorkflowRegistry

    make_project(tmp_path)
    steps = tmp_path / ".specify/workflows/steps/custom"
    steps.mkdir(parents=True)
    (steps / "step.yml").write_text(
        "step:\n  type_key: custom\n  version: '1.0.0'\n", encoding="utf-8"
    )
    (steps / "__init__.py").write_text(
        "from specify_cli.workflows.base import StepBase, StepResult\n"
        "class Custom(StepBase):\n"
        "    type_key = 'custom'\n"
        "    def execute(self, config, context): return StepResult()\n",
        encoding="utf-8",
    )
    workflows = tmp_path / ".specify/workflows/owned"
    workflows.mkdir()
    workflow = workflows / "workflow.yml"
    workflow.write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {"id": "owned", "name": "Owned", "version": "1.0.0"},
        "steps": [{"id": "check", "type": "custom"}],
    }), encoding="utf-8")
    original_workflow = workflow.read_bytes()
    StepRegistry(tmp_path).add("custom", {"version": "1.0.0", "type_key": "custom"})
    WorkflowRegistry(tmp_path).add("owned", {"version": "1.0.0", "enabled": False})
    original_metadata = WorkflowRegistry(tmp_path).get("owned")
    save_records(tmp_path, [InstalledBundleRecord.create(
        bundle_id="demo", version="1.0.0", components=[
            ComponentRef(kind="steps", id="custom", version="1.0.0"),
            ComponentRef(kind="workflows", id="owned", version="1.0.0"),
        ],
    )])

    def fail_save(*_args):
        raise OSError("provenance write refused")

    monkeypatch.setattr(
        "specify_cli.bundler.services.installer.save_records", fail_save
    )
    installer = DefaultPrimitiveInstaller(allow_network=False)
    try:
        with pytest.raises(BundlerError, match="provenance write refused"):
            if operation == "remove":
                remove_bundle(tmp_path, "demo", installer)
            else:
                install_bundle(
                    tmp_path,
                    InstallPlan(
                        bundle_id="demo", version="2.0.0", role="developer",
                        effective_integration=None, components=[],
                    ),
                    installer, refresh=True,
                )
        assert WorkflowRegistry(tmp_path).get("owned") == original_metadata
        assert workflow.read_bytes() == original_workflow
        assert StepRegistry(tmp_path).is_installed("custom")
    finally:
        load_custom_steps(tmp_path / "empty")
