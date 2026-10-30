from __future__ import annotations

import hashlib
import io  # noqa: F401
import json  # noqa: F401
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch  # noqa: F401

import pytest
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


@pytest.mark.parametrize("mutation", ["install", "refresh"])
@pytest.mark.parametrize("answer", ["accept", "decline", "eof", "flag"])
def test_update_all_reapproves_changed_step_code(project, monkeypatch, mutation, answer):
    from specify_cli.bundles.manifest import BundleManifest, ComponentRef
    from specify_cli.bundles.records import InstalledBundleRecord, save_records
    from specify_cli.workflows.catalog import StepCatalog, WorkflowRegistry
    from specify_cli.workflows.step.installer import install_step_package
    from tests.specify_cli.workflows.helpers import (
        force_workflow_stdin,
        write_step_import_probe,
    )

    original_marker = write_step_import_probe(project)
    new_marker = project / "new-step-imported.txt"
    force_workflow_stdin(monkeypatch, tty=True)
    step_metadata = yaml.safe_dump({
        "schema_version": "1.0",
        "step": {"type_key": "new-step", "name": "New step", "version": "1.0.0"},
    })
    original_init = (
        "from specify_cli.workflows.base import StepBase, StepResult\n"
        "class NewStep(StepBase):\n"
        "    type_key = 'new-step'\n"
        "    def execute(self, config, context):\n"
        "        return StepResult()\n"
    )
    new_init = (
        f"from pathlib import Path\nPath({str(new_marker)!r}).touch()\n"
        + original_init
    )
    step_files = {"step.yml": step_metadata.encode(), "__init__.py": new_init.encode()}
    if mutation == "refresh":
        original_package = project / "original-step"
        original_package.mkdir()
        (original_package / "step.yml").write_text(step_metadata, encoding="utf-8")
        (original_package / "__init__.py").write_text(original_init, encoding="utf-8")
        install_step_package(project, "new-step", original_package, source="local")

    manifests = {}
    records = []
    packaged = {}
    for bundle_id, workflow_id in (
        ("first-bundle", "first-workflow"), ("second-bundle", "second-workflow"),
    ):
        workflow = {
            "schema_version": "1.0",
            "workflow": {"id": workflow_id, "name": workflow_id, "version": "1.0.0"},
            "steps": [{"id": "probe", "type": "import-probe"}],
        }
        packaged[workflow_id] = project / "packaged" / workflow_id
        packaged[workflow_id].mkdir(parents=True)
        workflow_text = yaml.safe_dump(workflow)
        (packaged[workflow_id] / "workflow.yml").write_text(workflow_text, encoding="utf-8")
        installed_dir = project / ".specify" / "workflows" / workflow_id
        installed_dir.mkdir(parents=True)
        (installed_dir / "workflow.yml").write_text(workflow_text, encoding="utf-8")
        WorkflowRegistry(project).add(workflow_id, {"version": "1.0.0"})
        components = [ComponentRef("workflows", workflow_id, "1.0.0")]
        data = valid_manifest_dict(provides={
            "workflows": [{"id": workflow_id, "version": "1.0.0"}],
        })
        data["bundle"]["id"] = bundle_id
        if bundle_id == "second-bundle":
            data["provides"]["steps"] = [{"id": "new-step", "version": "1.0.0"}]
            if mutation == "refresh":
                components.append(ComponentRef("steps", "new-step", "1.0.0"))
        manifests[bundle_id] = BundleManifest.from_dict(data)
        records.append(InstalledBundleRecord.create(bundle_id, "1.2.0", components))
    save_records(project, records)
    monkeypatch.setattr(
        "specify_cli._assets._locate_bundled_workflow", lambda wid: packaged.get(wid),
    )
    monkeypatch.setattr(
        "specify_cli.bundles.command_update._build_stack",
        lambda *args, **kwargs: SimpleNamespace(resolve=lambda bid: SimpleNamespace(
            install_allowed=True, entry=SimpleNamespace(id=bid),
        )),
    )
    monkeypatch.setattr(
        "specify_cli.bundles.command_update._download_manifest",
        lambda resolved, **kwargs: manifests[resolved.entry.id],
    )
    catalog_source = SimpleNamespace(
        name="test", url="https://example.com/steps.json", install_allowed=True,
    )
    monkeypatch.setattr(StepCatalog, "get_active_catalogs", lambda self: [catalog_source])
    monkeypatch.setattr(
        StepCatalog, "_fetch_single_catalog",
        lambda self, entry: {"steps": {"new-step": {
            "id": "new-step", "version": "1.0.0",
            "url": "https://example.com/new-step/step.yml",
            "init_url": "https://example.com/new-step/__init__.py",
            "sha256": {
                name: hashlib.sha256(content).hexdigest()
                for name, content in step_files.items()
            },
        }}},
    )

    class StepResponse(io.BytesIO):
        def __init__(self, url):
            super().__init__(step_files[url.rsplit("/", 1)[1]])
            self.url = url

        def geturl(self):
            return self.url

    monkeypatch.setattr(
        "specify_cli.authentication.http.open_url",
        lambda url, **kwargs: StepResponse(url),
    )
    arguments = ["bundle", "update", "--all"]
    if answer == "flag":
        arguments.append("--trust-steps")
    responses = {"accept": "y\ny\n", "decline": "y\nn\n", "eof": "y\n", "flag": ""}

    result = runner.invoke(app, arguments, input=responses[answer])

    approved = answer in {"accept", "flag"}
    assert new_marker.exists() is approved, result.output
    assert result.exit_code == (0 if approved else 1), result.output
    assert original_marker.exists()
    assert result.output.count("Trust all custom workflow step code") == (
        0 if answer == "flag" else 2
    )


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
            entry=SimpleNamespace(id="parent", verified=True),
            source=SimpleNamespace(id="test-catalog"),
            install_allowed=True,
        ),
        "child": SimpleNamespace(
            entry=SimpleNamespace(id="child", verified=True),
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
        "parent": SimpleNamespace(entry=SimpleNamespace(id="parent", verified=True), source=SimpleNamespace(id="default"), install_allowed=True),
        "child": SimpleNamespace(entry=SimpleNamespace(id="child", verified=True), source=SimpleNamespace(id="default"), install_allowed=True),
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
        "parent": SimpleNamespace(entry=SimpleNamespace(id="parent", verified=True), source=SimpleNamespace(id="default"), install_allowed=True),
        "child": SimpleNamespace(entry=SimpleNamespace(id="child", verified=True), source=SimpleNamespace(id="default"), install_allowed=True),
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
        "parent": SimpleNamespace(entry=SimpleNamespace(id="parent", verified=True), source=SimpleNamespace(id="default"), install_allowed=True),
        "child": SimpleNamespace(entry=SimpleNamespace(id="child", verified=True), source=SimpleNamespace(id="community"), install_allowed=False),
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
        entry=SimpleNamespace(id="flat", verified=True), source=SimpleNamespace(id="default"),
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
