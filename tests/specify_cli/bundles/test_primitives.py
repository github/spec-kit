"""Unit tests for the primitive-dispatch bridge (T044).

Covers routing, offline gating, and the network-aware ``DefaultPrimitiveInstaller``
seam — without touching real catalogs or the network (Constitution Principle II,
offline-first).
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundles.adapters import DefaultPrimitiveInstaller
from specify_cli.bundles.manifest import ComponentRef
from specify_cli.bundles.primitives import (
    _ExtensionKindManager,
    _PresetKindManager,
    _StepKindManager,
    _WorkflowKindManager,
    primitive_manager,
)
from specify_cli.extensions import ExtensionRegistry
from specify_cli.presets import PresetRegistry
from specify_cli.workflows.catalog import StepRegistry, WorkflowRegistry
from tests.specify_cli.bundles.helpers import valid_manifest_dict


def _component(kind: str, cid: str = "x") -> ComponentRef:
    return ComponentRef(kind=kind, id=cid)


def test_primitive_manager_routes_each_kind(tmp_path: Path):
    assert isinstance(primitive_manager("presets", tmp_path), _PresetKindManager)
    assert isinstance(primitive_manager("extensions", tmp_path), _ExtensionKindManager)
    assert isinstance(primitive_manager("workflows", tmp_path), _WorkflowKindManager)
    assert isinstance(primitive_manager("steps", tmp_path), _StepKindManager)


def test_primitive_manager_rejects_unknown_kind(tmp_path: Path):
    with pytest.raises(BundlerError, match="Unknown component kind"):
        primitive_manager("bogus", tmp_path)


def test_offline_preset_not_bundled_refuses(tmp_path: Path):
    manager = primitive_manager("presets", tmp_path, allow_network=False)
    with pytest.raises(BundlerError, match="network access is disabled"):
        manager.install(_component("presets", "definitely-not-bundled"))


def test_offline_extension_not_bundled_refuses(tmp_path: Path):
    manager = primitive_manager("extensions", tmp_path, allow_network=False)
    with pytest.raises(BundlerError, match="network access is disabled"):
        manager.install(_component("extensions", "definitely-not-bundled"))


def test_offline_workflow_refuses_without_network(tmp_path: Path):
    manager = primitive_manager("workflows", tmp_path, allow_network=False)
    with pytest.raises(BundlerError, match="network access is disabled"):
        manager.install(_component("workflows"))


def test_offline_step_refuses_without_network(tmp_path: Path):
    manager = primitive_manager("steps", tmp_path, allow_network=False)
    with pytest.raises(BundlerError, match="network access is disabled"):
        manager.install(_component("steps"))


def test_step_manager_delegates_catalog_install_from_bundle_root(tmp_path, monkeypatch):
    import specify_cli

    calls: list[tuple[str, Path]] = []

    def _add(step_id: str) -> None:
        calls.append((step_id, Path.cwd()))

    monkeypatch.setattr(specify_cli, "workflow_step_add", _add)
    manager = _StepKindManager(tmp_path, allow_network=True)

    manager.install(_component("steps", "catalog-step"))

    assert calls == [("catalog-step", tmp_path)]


def test_default_installer_threads_allow_network(tmp_path: Path):
    installer = DefaultPrimitiveInstaller(allow_network=False)
    with pytest.raises(BundlerError, match="network access is disabled"):
        installer.install(tmp_path, _component("workflows"))


@pytest.mark.parametrize("kind", ["presets", "extensions", "workflows", "steps"])
def test_offline_refresh_explains_component_needs_network(tmp_path: Path, kind: str):
    installer = DefaultPrimitiveInstaller(allow_network=False)
    with pytest.raises(BundlerError) as exc:
        installer.refresh(tmp_path, _component(kind, "definitely-not-bundled"))
    message = str(exc.value)
    assert "definitely-not-bundled" in message
    assert "refreshing this component requires network access" in message
    assert "re-run without --offline" in message
    assert "install it first" not in message


_REGISTRIES = {
    "extensions": lambda root: ExtensionRegistry(root / ".specify" / "extensions"),
    "presets": lambda root: PresetRegistry(root / ".specify" / "presets"),
    "workflows": WorkflowRegistry,
    "steps": StepRegistry,
}


@pytest.mark.parametrize("kind", sorted(_REGISTRIES))
def test_installed_version_reads_each_primitive_registry(tmp_path: Path, kind: str):
    _REGISTRIES[kind](tmp_path).add("x", {"version": "0.9.0"})
    installer = DefaultPrimitiveInstaller()

    assert installer.installed_version(tmp_path, _component(kind)) == "0.9.0"
    assert installer.installed_version(tmp_path, _component(kind, "missing")) is None


def test_offline_workflow_allows_bundled(tmp_path: Path, monkeypatch):
    # A workflow that ships with Spec Kit must install even with --offline.
    import specify_cli
    import specify_cli._assets as assets

    bundled = tmp_path / "wf"
    bundled.mkdir()
    (bundled / "workflow.yml").write_text(
        "workflow:\n  id: bundled-wf\n  version: 1.0.0\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        assets, "_locate_bundled_workflow", lambda wid: bundled
    )
    calls: list[tuple] = []

    def _workflow_add(wid, dev=None, from_url=None):
        calls.append((wid, dev, from_url))

    monkeypatch.setattr(
        specify_cli,
        "workflow_add",
        _workflow_add,
    )

    manager = primitive_manager("workflows", tmp_path, allow_network=False)
    manager.install(_component("workflows", "bundled-wf"))

    assert calls == [(str(bundled / "workflow.yml"), True, None)]


def test_assert_pinned_version_matches_passes():
    from specify_cli.bundles.primitives import _assert_pinned_version

    # Equal (including v-prefix/normalization) is accepted; no version pins are no-ops.
    _assert_pinned_version("Preset", "p", "2.0.0", "2.0.0")
    _assert_pinned_version("Preset", "p", "2.0.0", "v2.0.0")
    _assert_pinned_version("Preset", "p", None, "9.9.9")
    _assert_pinned_version("Preset", "p", "2.0.0", None)


def test_assert_pinned_version_mismatch_raises():
    from specify_cli.bundles.primitives import _assert_pinned_version

    with pytest.raises(BundlerError, match="pinned to version 2.0.0"):
        _assert_pinned_version("Preset", "preset-a", "2.0.0", "3.1.0")


def test_workflow_version_mismatch_refuses(tmp_path: Path, monkeypatch):
    from specify_cli.workflows.catalog import WorkflowCatalog

    monkeypatch.setattr(
        WorkflowCatalog, "get_workflow_info", lambda self, wid: {"version": "9.9.9"}
    )
    manager = primitive_manager("workflows", tmp_path, allow_network=True)
    component = ComponentRef(kind="workflows", id="wf-a", version="0.3.0")
    with pytest.raises(BundlerError, match="pinned to version 0.3.0"):
        manager.install(component)


def test_preset_install_preserves_explicit_zero_priority(tmp_path: Path, monkeypatch):
    import specify_cli._assets as assets

    calls = {}

    class _FakeManager:
        def install_from_directory(self, directory, speckit_version, priority):
            calls["priority"] = priority

    monkeypatch.setattr(assets, "_locate_bundled_preset", lambda cid: tmp_path)

    manager = primitive_manager("presets", tmp_path, allow_network=False)
    manager._manager = _FakeManager()
    manager.install(ComponentRef(kind="presets", id="p", priority=0))

    # An explicit priority of 0 must be passed through, not replaced by default.
    assert calls["priority"] == 0


def test_catalog_preset_install_and_refresh_forward_catalog_name(
    tmp_path: Path, monkeypatch
):
    import specify_cli._assets as assets
    from specify_cli.presets import PresetCatalog

    archive = tmp_path / "preset.zip"
    archive.write_bytes(b"placeholder")
    calls = []

    class _FakeManager:
        def install_from_zip(self, *args, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(assets, "_locate_bundled_preset", lambda _id: None)
    monkeypatch.setattr(
        PresetCatalog,
        "get_pack_info",
        lambda _self, _id: {
            "version": "1.0.0",
            "_install_allowed": True,
            "_catalog_name": "bundle-preset-catalog",
        },
    )
    monkeypatch.setattr(PresetCatalog, "download_pack", lambda _self, _id: archive)

    manager = primitive_manager("presets", tmp_path, allow_network=True)
    manager._manager = _FakeManager()
    component = ComponentRef(kind="presets", id="catalog-preset", version="1.0.0")
    manager.install(component)
    archive.write_bytes(b"placeholder")
    manager.refresh(component)

    assert [call["catalog_name"] for call in calls] == [
        "bundle-preset-catalog",
        "bundle-preset-catalog",
    ]
    assert calls[1]["force"] is True


def test_catalog_extension_install_and_refresh_forward_catalog_and_scaffolding(
    tmp_path: Path, monkeypatch
):
    import specify_cli._assets as assets
    from specify_cli.extensions import ExtensionCatalog

    archive = tmp_path / "extension.zip"
    archive.write_bytes(b"placeholder")
    installs = []
    scaffolded = []

    class _FakeManager:
        def install_from_zip(self, *args, **kwargs):
            installs.append(kwargs)
            return SimpleNamespace(id="catalog-extension")

        def scaffold_config(self, extension_id):
            scaffolded.append(extension_id)

    monkeypatch.setattr(assets, "_locate_bundled_extension", lambda _id: None)
    monkeypatch.setattr(
        ExtensionCatalog,
        "get_extension_info",
        lambda _self, _id: {
            "version": "1.0.0",
            "_install_allowed": True,
            "_catalog_name": "bundle-extension-catalog",
        },
    )
    monkeypatch.setattr(
        ExtensionCatalog, "download_extension", lambda _self, _id: archive
    )

    manager = primitive_manager("extensions", tmp_path, allow_network=True)
    manager._manager = _FakeManager()
    component = ComponentRef(
        kind="extensions", id="catalog-extension", version="1.0.0"
    )
    manager.install(component)
    archive.write_bytes(b"placeholder")
    manager.refresh(component)

    assert [call["catalog_name"] for call in installs] == [
        "bundle-extension-catalog",
        "bundle-extension-catalog",
    ]
    assert installs[1]["force"] is True
    assert scaffolded == ["catalog-extension", "catalog-extension"]


def _write_manifest(path: Path, root_key: str, version: str) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{root_key}.yml").write_text(
        f"{root_key}:\n  id: x\n  version: {version}\n", encoding="utf-8"
    )
    return path


def test_bundled_extension_pin_mismatch_refuses(tmp_path: Path, monkeypatch):
    """A bundled extension whose version != the manifest pin must be refused
    (the bundled path previously skipped the pin the catalog path enforces)."""
    import specify_cli._assets as assets
    from specify_cli.extensions import ExtensionManager

    bundled = _write_manifest(tmp_path / "ext", "extension", "1.0.0")
    monkeypatch.setattr(assets, "_locate_bundled_extension", lambda cid: bundled)
    called: list = []
    monkeypatch.setattr(
        ExtensionManager, "install_from_directory",
        lambda self, *a, **k: called.append(a),
    )

    manager = primitive_manager("extensions", tmp_path, allow_network=False)
    with pytest.raises(BundlerError, match="pinned to version 2.0.0"):
        manager.install(ComponentRef(kind="extensions", id="my-ext", version="2.0.0"))
    assert called == []  # install must not proceed


def test_bundled_extension_pin_match_installs(tmp_path: Path, monkeypatch):
    import specify_cli._assets as assets
    from specify_cli.extensions import ExtensionManager

    bundled = _write_manifest(tmp_path / "ext", "extension", "1.0.0")
    monkeypatch.setattr(assets, "_locate_bundled_extension", lambda cid: bundled)
    called: list = []

    def _fake_install(self, *a, **k):
        called.append(a)
        return SimpleNamespace(id="my-ext")

    monkeypatch.setattr(ExtensionManager, "install_from_directory", _fake_install)

    manager = primitive_manager("extensions", tmp_path, allow_network=False)
    # matching pin, and unpinned, both install cleanly
    manager.install(ComponentRef(kind="extensions", id="my-ext", version="1.0.0"))
    manager.install(ComponentRef(kind="extensions", id="my-ext", version=None))
    assert len(called) == 2


def _write_extension_with_config(ext_dir: Path) -> None:
    """A minimal, real (unmocked) extension source with a provides.config entry."""
    import yaml

    ext_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "1.0",
        "extension": {
            "id": "my-ext",
            "name": "My Extension",
            "version": "1.0.0",
            "description": "Test extension",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {
            "commands": [
                {"name": "speckit.my-ext.hello", "file": "commands/hello.md"},
            ],
            "config": [
                {"name": "my-ext-config.yml", "template": "config-template.yml"},
            ],
        },
    }
    (ext_dir / "extension.yml").write_text(yaml.dump(manifest), encoding="utf-8")
    (ext_dir / "config-template.yml").write_text("setting: default\n", encoding="utf-8")
    (ext_dir / "commands").mkdir(exist_ok=True)
    (ext_dir / "commands" / "hello.md").write_text("---\ndescription: Test\n---\n\nhi\n", encoding="utf-8")


def test_bundled_extension_install_scaffolds_config(tmp_path: Path, monkeypatch):
    """A bundle-installed extension must have its provides.config templates
    scaffolded, exactly like `specify extension add` does (issue: bundle
    install skipped ExtensionManager.scaffold_config)."""
    import specify_cli._assets as assets

    project = tmp_path / "project"
    ext_source = tmp_path / "ext-source"
    _write_extension_with_config(ext_source)
    monkeypatch.setattr(assets, "_locate_bundled_extension", lambda cid: ext_source)

    manager = primitive_manager("extensions", project, allow_network=False)
    manager.install(ComponentRef(kind="extensions", id="my-ext"))

    scaffolded = project / ".specify" / "extensions" / "my-ext" / "my-ext-config.yml"
    assert scaffolded.exists()
    assert scaffolded.read_text(encoding="utf-8") == "setting: default\n"


def test_catalog_extension_install_scaffolds_config(tmp_path: Path, monkeypatch):
    """A catalog-resolved (downloaded ZIP) extension install must also
    scaffold its provides.config templates, matching the bundled-directory
    coverage above. Exercises the reported reproduction, which installed an
    extension resolved from the catalog rather than one shipped with Spec Kit."""
    import zipfile

    import specify_cli._assets as assets
    from specify_cli.extensions import ExtensionCatalog

    project = tmp_path / "project"
    ext_source = tmp_path / "ext-source"
    _write_extension_with_config(ext_source)

    zip_path = tmp_path / "my-ext.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for f in ext_source.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(ext_source))

    # No bundled asset located: forces the catalog/ZIP branch (install_from_zip).
    monkeypatch.setattr(assets, "_locate_bundled_extension", lambda cid: None)
    monkeypatch.setattr(
        ExtensionCatalog,
        "get_extension_info",
        lambda self, eid: {"id": eid, "_install_allowed": True},
    )
    monkeypatch.setattr(
        ExtensionCatalog, "download_extension", lambda self, eid: zip_path
    )

    manager = primitive_manager("extensions", project, allow_network=True)
    manager.install(ComponentRef(kind="extensions", id="my-ext"))

    scaffolded = project / ".specify" / "extensions" / "my-ext" / "my-ext-config.yml"
    assert scaffolded.exists()
    assert scaffolded.read_text(encoding="utf-8") == "setting: default\n"


def test_bundled_preset_pin_mismatch_refuses(tmp_path: Path, monkeypatch):
    import specify_cli._assets as assets
    from specify_cli.presets import PresetManager

    bundled = _write_manifest(tmp_path / "preset", "preset", "1.0.0")
    monkeypatch.setattr(assets, "_locate_bundled_preset", lambda cid: bundled)
    called: list = []
    monkeypatch.setattr(
        PresetManager, "install_from_directory",
        lambda self, *a, **k: called.append(a),
    )

    manager = primitive_manager("presets", tmp_path, allow_network=False)
    with pytest.raises(BundlerError, match="pinned to version 2.0.0"):
        manager.install(ComponentRef(kind="presets", id="my-preset", version="2.0.0"))
    assert called == []


def test_bundled_preset_pin_match_installs(tmp_path: Path, monkeypatch):
    import specify_cli._assets as assets
    from specify_cli.presets import PresetManager

    bundled = _write_manifest(tmp_path / "preset", "preset", "1.0.0")
    monkeypatch.setattr(assets, "_locate_bundled_preset", lambda cid: bundled)
    called: list = []
    monkeypatch.setattr(
        PresetManager, "install_from_directory",
        lambda self, *a, **k: called.append(a),
    )

    manager = primitive_manager("presets", tmp_path, allow_network=False)
    # matching pin, and unpinned, both proceed to install
    manager.install(ComponentRef(kind="presets", id="my-preset", version="1.0.0"))
    manager.install(ComponentRef(kind="presets", id="my-preset", version=None))
    assert len(called) == 2


def test_extension_refresh_calls_install_with_force(tmp_path: Path, monkeypatch):
    """_ExtensionKindManager.refresh() must pass force=True to install_from_directory
    so an already-installed extension is overwritten instead of raising an error."""
    import specify_cli._assets as assets
    from specify_cli.extensions import ExtensionManager

    bundled = _write_manifest(tmp_path / "ext", "extension", "1.0.0")
    monkeypatch.setattr(assets, "_locate_bundled_extension", lambda cid: bundled)
    force_values: list = []

    def _fake_install(self, *a, **k):
        force_values.append(k.get("force", False))
        return SimpleNamespace(id="my-ext")

    monkeypatch.setattr(ExtensionManager, "install_from_directory", _fake_install)

    manager = primitive_manager("extensions", tmp_path, allow_network=False)
    manager.refresh(ComponentRef(kind="extensions", id="my-ext"))
    assert force_values == [True], "refresh() must pass force=True"


def test_preset_refresh_calls_install_with_force(tmp_path: Path, monkeypatch):
    """_PresetKindManager.refresh() must pass force=True to install_from_directory
    so an already-installed preset is overwritten instead of raising an error."""
    import specify_cli._assets as assets
    from specify_cli.presets import PresetManager

    bundled = _write_manifest(tmp_path / "preset", "preset", "1.0.0")
    monkeypatch.setattr(assets, "_locate_bundled_preset", lambda cid: bundled)
    force_values: list = []
    monkeypatch.setattr(
        PresetManager, "install_from_directory",
        lambda self, *a, **k: force_values.append(k.get("force", False)),
    )

    manager = primitive_manager("presets", tmp_path, allow_network=False)
    manager.refresh(ComponentRef(kind="presets", id="my-preset"))
    assert force_values == [True], "refresh() must pass force=True"


def test_default_installer_refresh_dispatches_to_kind_manager(tmp_path: Path, monkeypatch):
    """DefaultPrimitiveInstaller.refresh() must call the kind manager's refresh(),
    which is the hook _refresh_component() will find — fixing the --force leak."""
    import specify_cli._assets as assets
    from specify_cli.extensions import ExtensionManager

    bundled = _write_manifest(tmp_path / "ext", "extension", "1.0.0")
    monkeypatch.setattr(assets, "_locate_bundled_extension", lambda cid: bundled)
    force_values: list = []

    def _fake_install(self, *a, **k):
        force_values.append(k.get("force", False))
        return SimpleNamespace(id="my-ext")

    monkeypatch.setattr(ExtensionManager, "install_from_directory", _fake_install)

    installer = DefaultPrimitiveInstaller(allow_network=False)
    installer.refresh(tmp_path, _component("extensions", "my-ext"))
    assert force_values == [True], "DefaultPrimitiveInstaller.refresh() must use force=True"


def test_refresh_succeeds_and_passes_force_true(tmp_path: Path, monkeypatch):
    """Regression: bundle update (refresh=True) of an already-installed extension
    must succeed and pass force=True to install_from_directory."""
    import specify_cli._assets as assets
    from specify_cli.bundles.installer import install_bundle
    from specify_cli.bundles.manifest import BundleManifest
    from specify_cli.extensions import ExtensionManager

    bundled = _write_manifest(tmp_path / "ext", "extension", "1.0.0")
    monkeypatch.setattr(assets, "_locate_bundled_extension", lambda cid: bundled)
    # Simulate refresh succeeding (force=True removes the duplicate-install guard)
    force_seen: list = []
    def _fake_install_from_directory(self, *a, **k):
        force_seen.append(k.get("force", False))
        self.registry.add("my-ext", {"version": "1.0.0"})
        return SimpleNamespace(id="my-ext")

    monkeypatch.setattr(
        ExtensionManager, "install_from_directory", _fake_install_from_directory
    )

    raw = valid_manifest_dict(
        bundle={
            "id": "test-bundle",
            "name": "Test",
            "version": "1.0.0",
            "role": "developer",
            "description": "Test bundle",
            "author": "Spec Kit",
            "license": "MIT",
        },
        provides={
            "extensions": [{"id": "my-ext", "version": "1.0.0"}],
            "presets": [],
            "steps": [],
            "workflows": [],
        },
    )
    manifest = BundleManifest.from_dict(raw)
    installer = DefaultPrimitiveInstaller(allow_network=False)
    # First install
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)
    # Refresh (bundle update) — must not raise with --force hint
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest, refresh=True)
    # force=True must have been passed during the refresh call
    assert True in force_seen, "refresh path should have called install_from_directory with force=True"


def _plan(manifest):
    from specify_cli.bundles.installer import InstallPlan
    from specify_cli.bundles.manifest import ComponentRef as CR

    components = [CR(kind=c.kind, id=c.id) for c in manifest.components]
    return InstallPlan(
        bundle_id=manifest.bundle.id,
        version=manifest.bundle.version,
        role=manifest.bundle.role,
        effective_integration=None,
        components=components,
    )


def test_step_refresh_restores_registry_entry_when_reinstall_fails(
    tmp_path: Path, monkeypatch
):
    """A failed step refresh must leave the registry entry restored.

    ``refresh`` keeps a backup and restores it "if the remove+reinstall path
    fails", but the registry half of that rollback was unreachable:
    ``StepRegistry`` snapshots the file once in ``__init__`` and
    ``is_installed`` reads only that snapshot, so after ``self.remove()``
    deleted the entry from disk the stale snapshot still reported it as
    installed and ``not ...is_installed(...)`` was always False.

    The step package came back but stayed unregistered — ``workflow step
    list`` stopped showing it, and ``workflow step add`` then refused with
    "Step directory already exists".
    """
    import json

    import specify_cli
    from specify_cli.workflows.catalog import StepRegistry

    steps_dir = tmp_path / ".specify" / "workflows" / "steps"
    (steps_dir / "my-step").mkdir(parents=True)
    (steps_dir / "my-step" / "step.yml").write_text(
        "step:\n  type_key: my-step\n", encoding="utf-8"
    )
    (steps_dir / "my-step" / "__init__.py").write_text("", encoding="utf-8")
    (steps_dir / StepRegistry.REGISTRY_FILE).write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "steps": {
                    "my-step": {
                        "name": "My Step",
                        "version": "1.0.0",
                        "type_key": "my-step",
                        # Distinctive past timestamps: a rollback must put the
                        # entry back verbatim, and ``StepRegistry.add()`` would
                        # silently replace both of these with ``now``.
                        "installed_at": "2020-01-01T00:00:00+00:00",
                        "updated_at": "2020-02-02T00:00:00+00:00",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    seeded = StepRegistry(tmp_path).get("my-step")
    assert StepRegistry(tmp_path).is_installed("my-step")
    package_text = (steps_dir / "my-step" / "step.yml").read_text(encoding="utf-8")

    # Removal succeeds (real code path); only the re-install fails, which is
    # what a catalog 404 / size-limit / type_key mismatch produces.
    def _boom(step_id, *args, **kwargs):
        raise BundlerError(f"Failed to install step '{step_id}'.")

    monkeypatch.setattr(specify_cli, "workflow_step_add", _boom)

    # The backup copy and the locked remove must both run while the step lock
    # is held. A nested ``workflow_step_remove`` would take the same flock and
    # hang, so the stand-in refuses a second hold before calling the real lock.
    import contextlib
    import shutil

    import specify_cli.workflows.step.command_remove as command_remove
    import specify_cli.workflows.step.installer as step_installer

    hold = {"depth": 0}
    backup_copy_depths: list[int] = []
    remove_depths: list[int] = []
    real_txn = step_installer._step_install_transaction
    real_copytree = shutil.copytree
    real_remove = command_remove._remove_step_locked

    @contextlib.contextmanager
    def _tracking_transaction(project_root):
        if hold["depth"] >= 1:
            raise AssertionError("nested _step_install_transaction")
        hold["depth"] += 1
        try:
            with real_txn(project_root):
                yield
        finally:
            hold["depth"] -= 1

    def _tracking_copytree(src, dst, *args, **kwargs):
        if "speckit-step-refresh-" in str(dst):
            backup_copy_depths.append(hold["depth"])
        return real_copytree(src, dst, *args, **kwargs)

    def _tracking_remove(project_root, step_id):
        remove_depths.append(hold["depth"])
        return real_remove(project_root, step_id)

    monkeypatch.setattr(
        step_installer, "_step_install_transaction", _tracking_transaction
    )
    monkeypatch.setattr(shutil, "copytree", _tracking_copytree)
    monkeypatch.setattr(command_remove, "_remove_step_locked", _tracking_remove)

    manager = primitive_manager("steps", tmp_path, allow_network=True)
    with pytest.raises(BundlerError):
        manager.refresh(_component("steps", "my-step"))

    assert backup_copy_depths and min(backup_copy_depths) >= 1
    assert remove_depths and min(remove_depths) >= 1

    # Read the registry fresh from disk — the point of the fix.
    restored = StepRegistry(tmp_path)
    assert restored.is_installed("my-step"), (
        steps_dir / StepRegistry.REGISTRY_FILE
    ).read_text(encoding="utf-8")
    # A rollback must be a rollback: the entry comes back byte-for-byte, not
    # re-registered with fresh ``installed_at`` / ``updated_at`` stamps.
    assert restored.get("my-step") == seeded
    assert (steps_dir / "my-step" / "step.yml").read_text(encoding="utf-8") == (
        package_text
    )
    assert (steps_dir / "my-step" / "__init__.py").read_text(encoding="utf-8") == ""


def _seed_refresh_step(root: Path) -> tuple[Path, dict]:
    """Install ``my-step`` on disk the way a previous ``step add`` would have."""
    import json

    from specify_cli.workflows.catalog import StepRegistry

    steps_dir = root / ".specify" / "workflows" / "steps"
    package = steps_dir / "my-step"
    package.mkdir(parents=True)
    (package / "step.yml").write_text(
        "step:\n  type_key: my-step\n", encoding="utf-8"
    )
    (package / "__init__.py").write_text("", encoding="utf-8")
    entry = {
        "name": "My Step",
        "version": "1.0.0",
        "type_key": "my-step",
        "installed_at": "2020-01-01T00:00:00+00:00",
        "updated_at": "2020-02-02T00:00:00+00:00",
    }
    (steps_dir / StepRegistry.REGISTRY_FILE).write_text(
        json.dumps(
            {"schema_version": "1.0", "steps": {"my-step": entry}}
        ),
        encoding="utf-8",
    )
    return steps_dir, entry


def test_step_refresh_keeps_a_later_commit_when_reinstall_fails(
    tmp_path: Path, monkeypatch
):
    """A step operation that lands before rollback must survive the failure.

    The pre-fix restore copied the backup with ``dirs_exist_ok=True``, which
    overwrote a package a later ``step add`` had already committed.
    """
    import json

    import specify_cli
    from specify_cli.workflows.catalog import StepRegistry

    steps_dir, _entry = _seed_refresh_step(tmp_path)
    newer_step_yml = "step:\n  type_key: my-step\n  version: 2.0.0\n"
    committed = {
        "my-step": {
            "name": "My Step",
            "version": "2.0.0",
            "type_key": "my-step",
            "installed_at": "2024-03-03T00:00:00+00:00",
            "updated_at": "2024-04-04T00:00:00+00:00",
        },
        "other-step": {
            "name": "Other Step",
            "version": "1.0.0",
            "installed_at": "2024-05-05T00:00:00+00:00",
            "updated_at": "2024-05-05T00:00:00+00:00",
        },
    }

    def _boom(step_id, *args, **kwargs):
        package = steps_dir / step_id
        package.mkdir(parents=True, exist_ok=True)
        (package / "step.yml").write_text(newer_step_yml, encoding="utf-8")
        (steps_dir / StepRegistry.REGISTRY_FILE).write_text(
            json.dumps({"schema_version": "1.0", "steps": committed}),
            encoding="utf-8",
        )
        raise BundlerError(f"Failed to install step '{step_id}'.")

    monkeypatch.setattr(specify_cli, "workflow_step_add", _boom)

    manager = primitive_manager("steps", tmp_path, allow_network=True)
    with pytest.raises(BundlerError, match="Failed to install step 'my-step'"):
        manager.refresh(_component("steps", "my-step"))

    assert (steps_dir / "my-step" / "step.yml").read_text(encoding="utf-8") == (
        newer_step_yml
    )
    assert StepRegistry(tmp_path).data["steps"] == committed


def test_step_refresh_rollback_keeps_registry_keys_written_after_load(
    tmp_path: Path, monkeypatch
):
    """Rollback must save the on-disk steps object, not the loaded snapshot.

    After ``StepRegistry`` loads, a key written to ``step-registry.json``
    without being inserted into that instance has to survive ``save()``.
    """
    import json

    import specify_cli
    from specify_cli.workflows.catalog import StepRegistry

    steps_dir, entry = _seed_refresh_step(tmp_path)
    registry_path = steps_dir / StepRegistry.REGISTRY_FILE
    other_step = {
        "name": "Other Step",
        "version": "3.0.0",
        "installed_at": "2024-06-06T00:00:00+00:00",
        "updated_at": "2024-06-06T00:00:00+00:00",
    }
    real_load = StepRegistry._load
    injected = {"done": False}

    def _load(self):
        data = real_load(self)
        steps = data.get("steps")
        if (
            not injected["done"]
            and isinstance(steps, dict)
            and "my-step" not in steps
            and self.registry_path.is_file()
        ):
            injected["done"] = True
            disk = json.loads(self.registry_path.read_text(encoding="utf-8"))
            disk["steps"]["other-step"] = other_step
            self.registry_path.write_text(json.dumps(disk), encoding="utf-8")
        return data

    def _boom(step_id, *args, **kwargs):
        raise BundlerError(f"Failed to install step '{step_id}'.")

    monkeypatch.setattr(StepRegistry, "_load", _load)
    monkeypatch.setattr(specify_cli, "workflow_step_add", _boom)

    manager = primitive_manager("steps", tmp_path, allow_network=True)
    with pytest.raises(BundlerError, match="Failed to install step 'my-step'"):
        manager.refresh(_component("steps", "my-step"))

    assert injected["done"]
    saved = json.loads(registry_path.read_text(encoding="utf-8"))
    assert saved["steps"]["my-step"] == entry
    assert saved["steps"]["other-step"] == other_step


@pytest.mark.parametrize("failure", ["copy", "save"])
def test_step_refresh_notes_restoration_failure_and_keeps_backup(
    tmp_path: Path, monkeypatch, failure: str
):
    """A failed copy-back or registry write stays on the original install error."""
    import shutil

    import specify_cli
    from specify_cli.workflows.catalog import StepRegistry, StepValidationError

    steps_dir, _entry = _seed_refresh_step(tmp_path)
    original_step_yml = (steps_dir / "my-step" / "step.yml").read_text(
        encoding="utf-8"
    )

    def _boom(step_id, *args, **kwargs):
        raise BundlerError(f"Failed to install step '{step_id}'.")

    monkeypatch.setattr(specify_cli, "workflow_step_add", _boom)

    if failure == "copy":
        real_copytree = shutil.copytree

        def _copytree(src, dst, *args, **kwargs):
            if "speckit-step-refresh-" in str(src):
                raise OSError("restore copy failed")
            return real_copytree(src, dst, *args, **kwargs)

        monkeypatch.setattr(shutil, "copytree", _copytree)
        failure_text = "restore copy failed"
    else:
        real_save = StepRegistry.save
        armed = {"on": False}

        def _boom_then_arm(step_id, *args, **kwargs):
            armed["on"] = True
            raise BundlerError(f"Failed to install step '{step_id}'.")

        def _save(self):
            if armed["on"]:
                raise StepValidationError("registry write failed")
            return real_save(self)

        monkeypatch.setattr(specify_cli, "workflow_step_add", _boom_then_arm)
        monkeypatch.setattr(StepRegistry, "save", _save)
        failure_text = "registry write failed"

    manager = primitive_manager("steps", tmp_path, allow_network=True)
    with pytest.raises(BundlerError) as caught:
        manager.refresh(_component("steps", "my-step"))

    assert str(caught.value) == "Failed to install step 'my-step'."
    note = caught.value.__notes__[0]
    assert failure_text in note
    assert "speckit-step-refresh-" in note
    backup_root = Path(note.split("from backup '", 1)[1].split("'", 1)[0])
    try:
        assert backup_root.is_dir()
        assert (backup_root / "my-step" / "step.yml").read_text(
            encoding="utf-8"
        ) == original_step_yml
    finally:
        shutil.rmtree(backup_root, ignore_errors=True)


def test_step_refresh_skips_backup_when_offline_or_not_installed(
    tmp_path: Path, monkeypatch
):
    """Offline and not-installed refresh delegate to install with no backup."""
    import tempfile

    import specify_cli
    import specify_cli.workflows.step.installer as step_installer

    calls: list[tuple[str, Path]] = []

    def _add(step_id: str) -> None:
        calls.append((step_id, Path.cwd()))

    def _forbid_step_lock(*_args, **_kwargs):
        raise AssertionError("step refresh took the step lock")

    real_mkdtemp = tempfile.mkdtemp

    def _mkdtemp(*args, **kwargs):
        prefix = kwargs.get("prefix", args[0] if args else "")
        if str(prefix).startswith("speckit-step-refresh-"):
            raise AssertionError("step refresh took the backup path")
        return real_mkdtemp(*args, **kwargs)

    monkeypatch.setattr(specify_cli, "workflow_step_add", _add)
    monkeypatch.setattr(step_installer, "_step_install_transaction", _forbid_step_lock)
    monkeypatch.setattr(tempfile, "mkdtemp", _mkdtemp)

    missing = primitive_manager("steps", tmp_path, allow_network=True)
    missing.refresh(_component("steps", "missing-step"))
    assert calls == [("missing-step", tmp_path)]

    _seed_refresh_step(tmp_path)
    offline = primitive_manager("steps", tmp_path, allow_network=False)
    with pytest.raises(
        BundlerError, match="refreshing this component requires network access"
    ):
        offline.refresh(_component("steps", "my-step"))
    assert calls == [("missing-step", tmp_path)]


def _backup_root_from_note(note: str) -> Path:
    return Path(note.split("from backup '", 1)[1].split("'", 1)[0])


def test_step_refresh_wraps_initial_lock_failure_without_backup(
    tmp_path: Path, monkeypatch
):
    """Lock failure before the snapshot is wrapped and creates no backup."""
    import tempfile

    import specify_cli
    import specify_cli.workflows.step.installer as step_installer

    steps_dir, entry = _seed_refresh_step(tmp_path)
    package_text = (steps_dir / "my-step" / "step.yml").read_text(encoding="utf-8")
    registry_text = (steps_dir / StepRegistry.REGISTRY_FILE).read_text(
        encoding="utf-8"
    )

    def _lock_fails(*_args, **_kwargs):
        raise step_installer.StepInstallError(
            "Failed to acquire the step lock: busy"
        )

    def _add(*_args, **_kwargs):
        raise AssertionError("install ran after the initial lock failure")

    created: list[str] = []
    real_mkdtemp = tempfile.mkdtemp

    def _mkdtemp(*args, **kwargs):
        prefix = kwargs.get("prefix", args[0] if args else "")
        created.append(str(prefix))
        return real_mkdtemp(*args, **kwargs)

    monkeypatch.setattr(step_installer, "_step_install_transaction", _lock_fails)
    monkeypatch.setattr(specify_cli, "workflow_step_add", _add)
    monkeypatch.setattr(tempfile, "mkdtemp", _mkdtemp)

    manager = primitive_manager("steps", tmp_path, allow_network=True)
    with pytest.raises(BundlerError) as caught:
        manager.refresh(_component("steps", "my-step"))

    assert str(caught.value) == (
        "Failed to refresh step 'my-step': Failed to acquire the step lock: busy"
    )
    assert isinstance(caught.value.__cause__, step_installer.StepInstallError)
    assert not any(prefix.startswith("speckit-step-refresh-") for prefix in created)
    assert (steps_dir / "my-step" / "step.yml").read_text(encoding="utf-8") == (
        package_text
    )
    assert (steps_dir / StepRegistry.REGISTRY_FILE).read_text(encoding="utf-8") == (
        registry_text
    )
    assert StepRegistry(tmp_path).get("my-step") == entry


def test_step_refresh_notes_rollback_lock_failure_and_keeps_backup(
    tmp_path: Path, monkeypatch
):
    """A failed rollback lock keeps the install error, a note, and the backup."""
    import contextlib
    import shutil

    import specify_cli
    import specify_cli.workflows.step.installer as step_installer

    steps_dir, _entry = _seed_refresh_step(tmp_path)
    original_step_yml = (steps_dir / "my-step" / "step.yml").read_text(
        encoding="utf-8"
    )

    def _boom(step_id, *args, **kwargs):
        raise BundlerError(f"Failed to install step '{step_id}'.")

    monkeypatch.setattr(specify_cli, "workflow_step_add", _boom)

    real_txn = step_installer._step_install_transaction
    calls = {"n": 0}

    @contextlib.contextmanager
    def _fail_second(project_root):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise step_installer.StepInstallError(
                "Failed to acquire the step lock: busy"
            )
        with real_txn(project_root):
            yield

    monkeypatch.setattr(step_installer, "_step_install_transaction", _fail_second)

    manager = primitive_manager("steps", tmp_path, allow_network=True)
    with pytest.raises(BundlerError) as caught:
        manager.refresh(_component("steps", "my-step"))

    assert calls["n"] == 2
    assert str(caught.value) == "Failed to install step 'my-step'."
    assert caught.value.__cause__ is None
    note = caught.value.__notes__[0]
    assert "Failed to acquire the step lock: busy" in note
    assert "Could not restore step 'my-step'" in note
    backup_root = _backup_root_from_note(note)
    try:
        assert backup_root.is_dir()
        assert (backup_root / "my-step" / "step.yml").read_text(
            encoding="utf-8"
        ) == original_step_yml
    finally:
        shutil.rmtree(backup_root, ignore_errors=True)
    assert not (steps_dir / "my-step").exists()
    assert not StepRegistry(tmp_path).is_installed("my-step")


def _require_directory_symlink(tmp_path: Path) -> None:
    probe_target = tmp_path / "symlink-probe-target"
    probe_target.mkdir()
    probe = tmp_path / "symlink-probe"
    try:
        probe.symlink_to(probe_target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"cannot create symlink: {exc}")


def test_step_refresh_rollback_refuses_swapped_steps_symlink(
    tmp_path: Path, monkeypatch
):
    """Rollback must not read or delete through a steps directory symlink."""
    import json
    import shutil

    import specify_cli

    _require_directory_symlink(tmp_path)
    steps_dir, _entry = _seed_refresh_step(tmp_path)
    outside = tmp_path / "outside"
    external_step = outside / "my-step"
    external_step.mkdir(parents=True)
    (external_step / "secret.txt").write_text("do-not-delete", encoding="utf-8")
    external_registry = {
        "schema_version": "1.0",
        "steps": {"other-step": {"name": "Other", "version": "9.9.9"}},
    }
    (outside / StepRegistry.REGISTRY_FILE).write_text(
        json.dumps(external_registry), encoding="utf-8"
    )

    def _boom(step_id, *args, **kwargs):
        # Reinstall is outside the lock: swap the steps directory for an
        # external tree before rollback reacquires it.
        shutil.rmtree(steps_dir)
        steps_dir.symlink_to(outside, target_is_directory=True)
        raise BundlerError(f"Failed to install step '{step_id}'.")

    monkeypatch.setattr(specify_cli, "workflow_step_add", _boom)

    manager = primitive_manager("steps", tmp_path, allow_network=True)
    with pytest.raises(BundlerError) as caught:
        manager.refresh(_component("steps", "my-step"))

    assert str(caught.value) == "Failed to install step 'my-step'."
    note = caught.value.__notes__[0]
    assert "Refusing to use symlinked step directory" in note
    assert (external_step / "secret.txt").read_text(encoding="utf-8") == (
        "do-not-delete"
    )
    assert not (external_step / "step.yml").exists()
    assert (
        json.loads((outside / StepRegistry.REGISTRY_FILE).read_text(encoding="utf-8"))
        == external_registry
    )
    assert steps_dir.is_symlink()
    backup_root = _backup_root_from_note(note)
    try:
        assert (backup_root / "my-step" / "step.yml").is_file()
    finally:
        shutil.rmtree(backup_root, ignore_errors=True)


def test_step_refresh_rollback_refuses_symlinked_step_directory(
    tmp_path: Path, monkeypatch
):
    """Rollback must not delete a step directory that is itself a symlink."""
    import shutil

    import specify_cli

    _require_directory_symlink(tmp_path)
    steps_dir, _entry = _seed_refresh_step(tmp_path)
    external_step = tmp_path / "outside-step"
    external_step.mkdir()
    (external_step / "secret.txt").write_text("do-not-delete", encoding="utf-8")

    def _boom(step_id, *args, **kwargs):
        link = steps_dir / step_id
        link.symlink_to(external_step, target_is_directory=True)
        raise BundlerError(f"Failed to install step '{step_id}'.")

    monkeypatch.setattr(specify_cli, "workflow_step_add", _boom)

    manager = primitive_manager("steps", tmp_path, allow_network=True)
    with pytest.raises(BundlerError) as caught:
        manager.refresh(_component("steps", "my-step"))

    assert str(caught.value) == "Failed to install step 'my-step'."
    note = caught.value.__notes__[0]
    assert "Refusing to install step through a symlinked path" in note
    assert (external_step / "secret.txt").read_text(encoding="utf-8") == (
        "do-not-delete"
    )
    assert (steps_dir / "my-step").is_symlink()
    backup_root = _backup_root_from_note(note)
    try:
        assert (backup_root / "my-step" / "step.yml").is_file()
    finally:
        shutil.rmtree(backup_root, ignore_errors=True)
