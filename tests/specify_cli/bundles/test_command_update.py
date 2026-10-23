from __future__ import annotations

import io  # noqa: F401
import json  # noqa: F401
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch  # noqa: F401

import yaml  # noqa: F401
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundles.packager import build_bundle  # noqa: F401
from tests.conftest import strip_ansi  # noqa: F401
from tests.specify_cli.bundles.helpers import (
    FakeInstaller,
    catalog_entry_dict,
    reference_manifest_dict,
    valid_manifest_dict,
    write_catalog_file,
)

runner = CliRunner()


def test_update_accepts_integration_override():
    # Update must expose --integration so integration-pinned bundles can be
    # updated in projects where the active integration can't be auto-detected.
    # Rich may insert ANSI escapes between the two leading dashes, so match the
    # un-split option word rather than the literal "--integration".
    result = runner.invoke(app, ["bundle", "update", "--help"])
    assert result.exit_code == 0
    assert "integration" in result.output


def test_update_refuses_discovery_only_source(project: Path):
    # An installed bundle whose only resolvable source is discovery-only must
    # not be updatable from there (FR-025), mirroring the install policy gate.
    from specify_cli.bundles.manifest import ComponentRef
    from specify_cli.bundles.records import (
        InstalledBundleRecord,
        save_records,
    )

    save_records(
        project,
        [
            InstalledBundleRecord.create(
                "demo",
                "1.0.0",
                [ComponentRef(kind="extensions", id="ext-a", version=None)],
            )
        ],
    )

    catalog = project / "disc.json"
    write_catalog_file(catalog, {"demo": catalog_entry_dict("demo")})
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {
                "id": "disc",
                "url": str(catalog),
                "priority": 1,
                "install_policy": "discovery-only",
            }
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )

    result = runner.invoke(app, ["bundle", "update", "demo", "--offline"])
    assert result.exit_code == 1
    assert "discovery-only" in result.output


def test_update_refresh_removes_dropped_referenced_component(
    project: Path, monkeypatch
):
    from specify_cli.bundles.manifest import BundleManifest, ComponentRef
    from specify_cli.bundles.records import (
        InstalledBundleRecord,
        load_records,
        save_records,
    )

    component = ComponentRef("extensions", "ext-a", "1.0.0")
    save_records(
        project,
        [
            InstalledBundleRecord.create(
                "parent",
                "1.0.0",
                [component],
                required_components=[component],
            )
        ],
    )
    installer = FakeInstaller()
    installer.installed.add((component.kind, component.id))
    installer.versions[(component.kind, component.id)] = component.version
    monkeypatch.setattr(
        "specify_cli.bundles.adapters.DefaultPrimitiveInstaller",
        lambda **kwargs: installer,
    )

    parent = BundleManifest.from_dict(
        reference_manifest_dict(
            [{"id": "child", "version": "1.0.0"}], bundle_id="parent"
        )
    )
    child_data = reference_manifest_dict([], bundle_id="child")
    child_data["bundle"]["version"] = "1.0.0"
    child = BundleManifest.from_dict(child_data)
    selected = {
        "parent": SimpleNamespace(
            entry=SimpleNamespace(id="parent"),
            source=SimpleNamespace(id="test-catalog"),
            install_allowed=True,
        ),
        "child": SimpleNamespace(
            entry=SimpleNamespace(id="child"),
            source=SimpleNamespace(id="test-catalog"),
            install_allowed=True,
        ),
    }

    class Stack:
        def resolve(self, bundle_id, version=None):
            return selected[bundle_id]

    monkeypatch.setattr(
        "specify_cli.bundles.command_update._build_stack",
        lambda *a, **k: Stack(),
    )
    monkeypatch.setattr(
        "specify_cli.bundles.command_update._download_manifest",
        lambda resolved, *, offline: parent if resolved.entry.id == "parent" else child,
    )

    result = runner.invoke(app, ["bundle", "update", "parent", "--offline"])

    assert result.exit_code == 0, result.output
    assert installer.remove_calls == [("extensions", "ext-a")]
    assert not load_records(project)[0].required_components


def test_update_follows_parent_reference_pin_bump(project: Path, monkeypatch):
    from specify_cli.bundles.manifest import BundleManifest, ComponentRef
    from specify_cli.bundles.records import InstalledBundleRecord, load_records, save_records

    old_component = ComponentRef("extensions", "child-ext", "1.0.0")
    save_records(
        project,
        [InstalledBundleRecord.create("parent", "1.0.0", [old_component])],
    )
    installer = FakeInstaller()
    installer.installed.add((old_component.kind, old_component.id))
    installer.versions[(old_component.kind, old_component.id)] = old_component.version
    monkeypatch.setattr(
        "specify_cli.bundles.adapters.DefaultPrimitiveInstaller",
        lambda **kwargs: installer,
    )
    parent = BundleManifest.from_dict(
        reference_manifest_dict(
            [{"id": "child", "version": "2.0.0"}], bundle_id="parent"
        )
    )
    child_data = valid_manifest_dict(
        bundle={
            "id": "child", "name": "Child", "version": "2.0.0",
            "role": "developer", "description": "child", "author": "tests",
            "license": "MIT",
        },
        provides={"extensions": [{"id": "child-ext", "version": "2.0.0"}]},
    )
    child = BundleManifest.from_dict(child_data)
    selected = {
        "parent": SimpleNamespace(entry=SimpleNamespace(id="parent"), source=SimpleNamespace(id="default"), install_allowed=True),
        "child": SimpleNamespace(entry=SimpleNamespace(id="child"), source=SimpleNamespace(id="default"), install_allowed=True),
    }

    class Stack:
        def resolve(self, bundle_id, version=None):
            return selected[bundle_id]

    monkeypatch.setattr(
        "specify_cli.bundles.command_update._build_stack", lambda *a, **k: Stack()
    )
    monkeypatch.setattr(
        "specify_cli.bundles.command_update._download_manifest",
        lambda resolved, *, offline: parent if resolved.entry.id == "parent" else child,
    )
    result = runner.invoke(app, ["bundle", "update", "parent", "--offline"])
    assert result.exit_code == 0, result.output
    assert installer.refresh_calls == [("extensions", "child-ext")]
    record = load_records(project)[0]
    assert record.bundle_references[0].version == "2.0.0"
    assert record.required_components[0].version == "2.0.0"


def test_update_escapes_reference_plan_warning_markup(
    project: Path, monkeypatch
):
    from specify_cli.bundles.manifest import BundleManifest, ComponentRef
    from specify_cli.bundles.primitives import _bundled_pin_warning
    from specify_cli.bundles.records import InstalledBundleRecord, save_records

    existing = ComponentRef("extensions", "[bold]x[/bold]", "1.0.0")
    save_records(project, [InstalledBundleRecord.create("parent", "1.0.0", [existing])])

    class WarningInstaller(FakeInstaller):
        def refresh(self, root, component):
            from specify_cli._console import console

            console.print("REFRESH_MARKER")
            super().refresh(root, component)
            return _bundled_pin_warning("Extension", component, "2.0.1")

    installer = WarningInstaller()
    installer.installed.add((existing.kind, existing.id))
    installer.versions[(existing.kind, existing.id)] = "2.0.0"
    monkeypatch.setattr(
        "specify_cli.bundles.adapters.DefaultPrimitiveInstaller",
        lambda **kwargs: installer,
    )
    parent_data = reference_manifest_dict(
        [{"id": "child", "version": "1.0.0"}], bundle_id="parent",
        extensions=[{"id": "[bold]x[/bold]", "version": "2.0.0"}],
    )
    parent_data["requires"] = {
        "speckit_version": ">=0.1.0", "tools": ["docker"], "mcp": ["server-a"]
    }
    parent = BundleManifest.from_dict(parent_data)
    child_data = valid_manifest_dict(
        bundle={
            "id": "child", "name": "Child", "version": "1.0.0",
            "role": "developer", "description": "child", "author": "tests",
            "license": "MIT",
        },
        integration={"id": "claude"},
        provides={"extensions": [{"id": "[bold]x[/bold]", "version": "1.0.0"}]},
    )
    child = BundleManifest.from_dict(child_data)
    selected = {
        "parent": SimpleNamespace(entry=SimpleNamespace(id="parent"), source=SimpleNamespace(id="default"), install_allowed=True),
        "child": SimpleNamespace(entry=SimpleNamespace(id="child"), source=SimpleNamespace(id="default"), install_allowed=True),
    }

    class Stack:
        def resolve(self, bundle_id, version=None):
            return selected[bundle_id]

    monkeypatch.setattr(
        "specify_cli.bundles.command_update._build_stack", lambda *a, **k: Stack()
    )
    monkeypatch.setattr(
        "specify_cli.bundles.command_update.active_integration", lambda root: "copilot"
    )
    monkeypatch.setattr(
        "specify_cli.bundles.command_update._download_manifest",
        lambda resolved, *, offline: parent if resolved.entry.id == "parent" else child,
    )
    result = runner.invoke(app, ["bundle", "update", "parent", "--offline"])
    assert result.exit_code == 0, result.output
    output = " ".join(result.output.split())
    assert output.count("Requires external tools: docker") == 1
    assert output.count("Requires MCP servers: server-a") == 1
    assert output.count("targets 'claude'") == 1
    assert output.count("overrides") == 1
    assert "[bold]x[/bold]" in strip_ansi(result.output)
    assert output.count("Warning:") == 1
    marker = output.index("REFRESH_MARKER")
    assert output.index("Requires external tools") < marker
    assert output.index("Requires MCP servers") < marker
    assert output.index("targets 'claude'") < marker
    assert output.index("overrides") < marker
    assert marker < output.index("Warning:")


def test_update_rejects_discovery_only_reference(project: Path, monkeypatch):
    from specify_cli.bundles.manifest import BundleManifest
    from specify_cli.bundles.records import InstalledBundleRecord, save_records

    save_records(project, [InstalledBundleRecord.create("parent", "1.0.0", [])])
    parent = BundleManifest.from_dict(
        reference_manifest_dict(
            [{"id": "child", "version": "1.0.0"}], bundle_id="parent"
        )
    )
    child = BundleManifest.from_dict(valid_manifest_dict(
        bundle={
            "id": "child", "name": "Child", "version": "1.0.0",
            "role": "developer", "description": "child", "author": "tests",
            "license": "MIT",
        },
        provides={"extensions": []},
    ))
    selected = {
        "parent": SimpleNamespace(entry=SimpleNamespace(id="parent"), source=SimpleNamespace(id="default"), install_allowed=True),
        "child": SimpleNamespace(entry=SimpleNamespace(id="child"), source=SimpleNamespace(id="community"), install_allowed=False),
    }

    class Stack:
        def resolve(self, bundle_id, version=None):
            return selected[bundle_id]

    monkeypatch.setattr(
        "specify_cli.bundles.command_update._build_stack", lambda *a, **k: Stack()
    )
    monkeypatch.setattr(
        "specify_cli.bundles.command_update._download_manifest",
        lambda resolved, *, offline: parent if resolved.entry.id == "parent" else child,
    )
    result = runner.invoke(app, ["bundle", "update", "parent", "--offline"])
    assert result.exit_code == 1
    assert "parent → child" in result.output
    assert "discovery-only" in result.output


def test_update_flat_plan_warnings_keep_existing_output(project: Path, monkeypatch):
    from specify_cli.bundles.manifest import BundleManifest
    from specify_cli.bundles.records import InstalledBundleRecord, save_records

    save_records(project, [InstalledBundleRecord.create("flat", "1.0.0", [])])
    data = valid_manifest_dict()
    data["bundle"]["id"] = "flat"
    data["requires"]["tools"] = ["docker"]
    manifest = BundleManifest.from_dict(data)
    selected = SimpleNamespace(
        entry=SimpleNamespace(id="flat"), source=SimpleNamespace(id="default"),
        install_allowed=True,
    )

    class Stack:
        def resolve(self, bundle_id, version=None):
            return selected

    monkeypatch.setattr(
        "specify_cli.bundles.command_update._build_stack", lambda *a, **k: Stack()
    )
    monkeypatch.setattr(
        "specify_cli.bundles.command_update._download_manifest",
        lambda resolved, *, offline: manifest,
    )
    monkeypatch.setattr(
        "specify_cli.bundles.adapters.DefaultPrimitiveInstaller",
        lambda **kwargs: FakeInstaller(),
    )
    result = runner.invoke(app, ["bundle", "update", "flat", "--offline"])
    assert result.exit_code == 0, result.output
    assert "Requires external tools" not in result.output
    assert "Updated 'flat' to v1.2.0." in result.output
