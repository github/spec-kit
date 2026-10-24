from __future__ import annotations

import io  # noqa: F401
import json  # noqa: F401
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch  # noqa: F401

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundler import BundlerError
from specify_cli.bundles.manifest import BundleManifest
from specify_cli.bundles.packager import build_bundle  # noqa: F401
from tests.conftest import strip_ansi
from tests.specify_cli.bundles.helpers import (
    bundled_extension_version,
    catalog_entry_dict,
    reference_manifest_dict,
    valid_manifest_dict,
    write_catalog_file,
)

runner = CliRunner()


@pytest.mark.parametrize(
    "actual,exit_code,warning",
    [("1.0.1", 0, True), ("1.0.0", 0, False), ("0.9.9", 1, False),
     ("1.1.0", 1, False), ("2.0.0", 1, False), ("1.0.1-rc1", 1, False)],
)
def test_validate_bundled_patch_compatibility(
    project: Path, monkeypatch, actual: str, exit_code: int, warning: bool,
):
    import specify_cli._assets as assets

    payload = project / "packaged-extension"
    payload.mkdir()
    (payload / "extension.yml").write_text(
        yaml.safe_dump({"extension": {"id": "x", "version": actual}}), encoding="utf-8",
    )
    monkeypatch.setattr(assets, "_locate_bundled_extension", lambda cid: payload)
    data = valid_manifest_dict(
        provides={"extensions": [{"id": "x", "version": "1.0.0"}]},
    )
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")

    result = runner.invoke(app, ["bundle", "validate", "--offline"])

    assert result.exit_code == exit_code, result.output
    assert ("newer packaged patch" in " ".join(result.output.split())) is warning


def test_validate_rejects_non_positive_preset_priority(project: Path, monkeypatch):
    """A manifest every install would reject must not be reported as valid."""
    import specify_cli._assets as assets

    payload = project / "packaged-preset"
    payload.mkdir()
    (payload / "preset.yml").write_text(
        yaml.safe_dump({"preset": {"id": "p", "version": "1.0.0"}}), encoding="utf-8",
    )
    monkeypatch.setattr(assets, "_locate_bundled_preset", lambda cid: payload)
    data = valid_manifest_dict(
        provides={
            "presets": [
                {"id": "p", "version": "1.0.0", "priority": 0, "strategy": "replace"}
            ]
        },
    )
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")

    result = runner.invoke(app, ["bundle", "validate", "--offline"])

    assert result.exit_code == 1, result.output
    assert "preset 'p' priority must be 1 or higher, got 0" in " ".join(
        result.output.split()
    )


@pytest.mark.parametrize("offline", [False, True])
def test_validate_bundled_workflow_patch_warns_without_catalog_lookup(
    project: Path, monkeypatch, offline: bool,
):
    import specify_cli._assets as assets
    from specify_cli.workflows.catalog import WorkflowCatalog

    payload = project / "packaged-workflow"
    payload.mkdir()
    (payload / "workflow.yml").write_text(
        yaml.safe_dump({"workflow": {"id": "x", "version": "1.0.1"}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(assets, "_locate_bundled_workflow", lambda cid: payload)
    monkeypatch.setattr(
        WorkflowCatalog, "get_active_catalogs",
        lambda self: pytest.fail("a compatible packaged patch must not consult catalogs"),
    )
    data = valid_manifest_dict(
        provides={"workflows": [{"id": "x", "version": "1.0.0"}]},
    )
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    args = ["bundle", "validate"]
    if offline:
        args.append("--offline")

    result = runner.invoke(app, args)

    assert result.exit_code == 0, result.output
    output = " ".join(result.output.split())
    assert "Workflow 'x' is pinned to version 1.0.0" in output
    assert "Spec Kit ships 1.0.1" in output
    assert output.count("newer packaged patch") == 1
    assert "well-formed and valid" in output


def test_validate_reports_invalid_manifest(project: Path):
    data = valid_manifest_dict()
    del data["bundle"]["license"]
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    result = runner.invoke(app, ["bundle", "validate"])
    assert result.exit_code == 1
    assert "license" in result.output


@pytest.mark.parametrize("version", ["1.2.0", "1.20.30-12alpha.1+build.01", "V10.20.30"])
def test_validate_accepts_valid_manifest(project: Path, version: str):
    data = valid_manifest_dict()
    data["bundle"]["version"] = version
    (project / "bundle.yml").write_text(
        yaml.safe_dump(data), encoding="utf-8"
    )
    # Offline mode does not fail on references it cannot verify (synthetic ids
    # here); they surface as warnings while structure is confirmed valid.
    result = runner.invoke(app, ["bundle", "validate", "--offline"])
    assert result.exit_code == 0, result.output
    assert "valid" in result.output


@pytest.mark.parametrize("version", ["1٢.2.3", "1.2.3-1٢", "1.2.3-٢alpha"])
@pytest.mark.parametrize("field", ["bundle", "extension"])
def test_validate_rejects_non_ascii_version(project: Path, version: str, field: str):
    data = valid_manifest_dict()
    if field == "bundle":
        data["bundle"]["version"] = version
    else:
        data["provides"]["extensions"][0]["version"] = version
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")

    result = runner.invoke(app, ["bundle", "validate", "--offline"])

    assert result.exit_code == 1, result.output
    assert "invalid" in result.output
    assert version in result.output


def test_validate_escapes_manifest_markup_in_errors(project: Path):
    data = valid_manifest_dict()
    # An invalid constraint is echoed back inside the validation error.
    data["requires"] = {"speckit_version": ">=1.0[/bold]"}
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")

    result = runner.invoke(app, ["bundle", "validate", "--offline"])

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert ">=1.0[/bold]" in strip_ansi(result.output)


def test_validate_escapes_manifest_markup_in_warnings(project: Path):
    data = valid_manifest_dict()
    # Step ids are not charset-validated, and the unresolved-reference warning
    # echoes them -- so an otherwise *valid* manifest crashed just as readily as
    # an invalid one, on the success path.
    data["provides"]["steps"] = [{"id": "step[/bold]a"}]
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")

    result = runner.invoke(app, ["bundle", "validate", "--offline"])

    assert result.exit_code == 0, repr(result.exception)
    assert "step[/bold]a" in strip_ansi(result.output)


def test_validate_rejects_broken_reference(project: Path):
    # Synthetic component ids resolve to nothing in any catalog → hard failure.
    (project / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    result = runner.invoke(app, ["bundle", "validate"])
    assert result.exit_code == 1
    assert "preset-a" in result.output or "ext-a" in result.output


def test_validate_warns_instead_of_rejecting_reference_during_partial_outage(
    project: Path, monkeypatch,
):
    from urllib.error import URLError

    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
    )

    data = valid_manifest_dict(
        provides={"steps": [{"id": "requested", "version": "1.0.0"}]}
    )
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    sources = [
        StepCatalogEntry("https://example.com/high.json", "high", 1, True),
        StepCatalogEntry("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(StepCatalog, "get_active_catalogs", lambda self: sources)

    def fetch(self, entry, force_refresh=False):
        if entry.name == "low":
            raise URLError("catalog timed out")
        return {"steps": {"other-step": {"version": "1.0.0"}}}

    monkeypatch.setattr(StepCatalog, "_fetch_single_catalog", fetch)

    result = runner.invoke(app, ["bundle", "validate"])

    assert result.exit_code == 0, result.output
    assert "unreachable" in result.output
    assert "not available" not in result.output


def test_validate_accepts_bundled_reference(project: Path):
    data = valid_manifest_dict()
    data["provides"] = {"extensions": [{
        "id": "agent-context", "version": bundled_extension_version("agent-context")
    }]}
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    result = runner.invoke(app, ["bundle", "validate"])
    assert result.exit_code == 0, result.output
    assert "valid" in result.output


@pytest.mark.parametrize("kind,id,version", [
    ("presets", "lean", "1.0.0"),
    ("extensions", "agent-context", bundled_extension_version("agent-context")),
])
@pytest.mark.parametrize("offline", [False, True])
def test_validate_rejects_mismatched_bundled_component(
    project: Path, monkeypatch, kind: str, id: str, version: str, offline: bool,
):
    from specify_cli.extensions import ExtensionCatalog
    from specify_cli.presets import PresetCatalog

    data = valid_manifest_dict(
        provides={kind: [{"id": id, "version": "9.9.9"}]}
    )
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setattr(
        PresetCatalog, "get_pack_info",
        lambda self, _id, version=None: {
            "version": version or "9.9.9",
            "_catalog_name": "trusted",
            "_install_allowed": True,
        },
    )
    monkeypatch.setattr(
        ExtensionCatalog, "get_extension_info",
        lambda self, _id, version=None: {
            "version": version or "9.9.9",
            "_catalog_name": "trusted",
            "_install_allowed": True,
        },
    )

    command = ["bundle", "validate", *(["--offline"] if offline else [])]
    result = runner.invoke(app, command)

    assert result.exit_code == 1, result.output
    assert f"resolved version is {version}" in result.output


def test_validate_expands_references_and_checks_expanded_components(project: Path, monkeypatch):
    parent = reference_manifest_dict([{"id": "child", "version": "1.0.0"}], bundle_id="parent")
    child = valid_manifest_dict(
        bundle={"id": "child", "name": "Child", "version": "1.0.0", "role": "developer", "description": "child", "author": "tests", "license": "MIT"},
        provides={"extensions": [{"id": "child-extension", "version": "1.0.0"}]},
    )
    path = project / "bundle.yml"
    path.write_text(yaml.safe_dump(parent), encoding="utf-8")
    selected = SimpleNamespace(entry=SimpleNamespace(id="child", version="1.0.0", verified=True), source=SimpleNamespace(id="default"), install_allowed=True)

    class Stack:
        def resolve(self, bundle_id, version=None):
            return selected

    monkeypatch.setattr("specify_cli.bundles._commands._build_stack", lambda *a, **k: Stack())
    monkeypatch.setattr("specify_cli.bundles.command_validate._download_manifest", lambda *a, **k: BundleManifest.from_dict(child))
    monkeypatch.setattr("specify_cli.bundles.references.make_reference_checker", lambda *a, **k: lambda component: "synthetic unresolved component" if component.id == "child-extension" else None)
    result = runner.invoke(app, ["bundle", "validate", "--path", str(path)])
    assert result.exit_code == 1, result.output
    assert "child-extension" in result.output
    assert "synthetic unresolved component" in " ".join(result.output.split())


def test_validate_offline_warns_once_per_direct_reference(project: Path):
    data = valid_manifest_dict(schema_version="1.1", provides={"bundles": [
        {"id": "first-child", "version": "1.0.0"},
        {"id": "second-child", "version": "1.0.0"},
    ]})
    path = project / "bundle.yml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    result = runner.invoke(app, ["bundle", "validate", "--path", str(path), "--offline"])
    assert result.exit_code == 0, result.output
    assert "first-child@1.0.0" in result.output
    assert "second-child@1.0.0" in result.output
    assert " ".join(result.output.split()).count("was not expanded") == 2


def _write_reference_bundle(project: Path, references, *, bundle_id="parent", provides=None):
    data = reference_manifest_dict(references, bundle_id=bundle_id)
    if provides is not None:
        data["provides"].update(provides)
    path = project / f"{bundle_id}.yml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def _selected(bundle_id, *, install_allowed=True, source="default"):
    return SimpleNamespace(entry=SimpleNamespace(id=bundle_id, version="1.0.0", verified=True), source=SimpleNamespace(id=source), install_allowed=install_allowed)


def test_validate_online_success(project: Path, monkeypatch):
    path = _write_reference_bundle(project, [{"id": "child", "version": "1.0.0"}])
    child = BundleManifest.from_dict(valid_manifest_dict(bundle={"id": "child", "name": "Child", "version": "1.0.0", "role": "developer", "description": "child", "author": "tests", "license": "MIT"}, provides={}))
    class Stack:
        def resolve(self, bundle_id, version=None): return _selected(bundle_id)
    monkeypatch.setattr("specify_cli.bundles._commands._build_stack", lambda *a, **k: Stack())
    monkeypatch.setattr("specify_cli.bundles.command_validate._download_manifest", lambda *a, **k: child)
    result = runner.invoke(app, ["bundle", "validate", "--path", str(path)])
    assert result.exit_code == 0, result.output


def test_validate_rejects_reference_source_mismatch(project: Path, monkeypatch):
    path = _write_reference_bundle(
        project,
        [{"id": "child", "version": "1.0.0", "source": "X"}],
    )
    child = BundleManifest.from_dict(
        valid_manifest_dict(
            bundle={
                "id": "child", "name": "Child", "version": "1.0.0",
                "role": "developer", "description": "child", "author": "tests",
                "license": "MIT",
            },
            provides={},
        )
    )

    class Stack:
        def resolve(self, bundle_id, version=None):
            return _selected(bundle_id, source="winner")

    monkeypatch.setattr("specify_cli.bundles._commands._build_stack", lambda *a, **k: Stack())
    monkeypatch.setattr(
        "specify_cli.bundles.command_validate._download_manifest",
        lambda *a, **k: child,
    )
    result = runner.invoke(app, ["bundle", "validate", "--path", str(path)])

    assert result.exit_code == 1, result.output
    assert "requires source" in result.output


def test_validate_cycle_and_discovery_only_errors(project: Path, monkeypatch):
    path = _write_reference_bundle(project, [{"id": "child", "version": "1.0.0"}])
    child_data = reference_manifest_dict([{"id": "parent", "version": "1.0.0"}], bundle_id="child")
    child_data["bundle"]["version"] = "1.0.0"
    child = BundleManifest.from_dict(child_data)
    class Stack:
        def resolve(self, bundle_id, version=None): return _selected(bundle_id, install_allowed=False, source="community")
    monkeypatch.setattr("specify_cli.bundles._commands._build_stack", lambda *a, **k: Stack())
    monkeypatch.setattr("specify_cli.bundles.command_validate._download_manifest", lambda *a, **k: child)
    result = runner.invoke(app, ["bundle", "validate", "--path", str(path)])
    assert result.exit_code == 1, result.output
    assert "Bundle reference cycle" in result.output

    child = BundleManifest.from_dict(valid_manifest_dict(bundle={"id": "child", "name": "Child", "version": "1.0.0", "role": "developer", "description": "child", "author": "tests", "license": "MIT"}, provides={}))
    monkeypatch.setattr("specify_cli.bundles.command_validate._download_manifest", lambda *a, **k: child)
    result = runner.invoke(app, ["bundle", "validate", "--path", str(path)])
    assert result.exit_code == 1, result.output
    assert "discovery-only" in result.output


def test_validate_structural_error_skips_expansion(project: Path, monkeypatch):
    path = _write_reference_bundle(project, [{"id": "child", "version": "1.0.0"}])
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["schema_version"] = "1.0"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setattr("specify_cli.bundles.command_validate._expand_manifest", lambda *a, **k: pytest.fail("expanded structural error"))
    result = runner.invoke(app, ["bundle", "validate", "--path", str(path)])
    assert result.exit_code == 1
    assert "Bundle references require schema_version" in result.output


def test_validate_expansion_failure_reports_own_error_once(project: Path, monkeypatch):
    path = _write_reference_bundle(project, [{"id": "child", "version": "1.0.0"}], provides={"extensions": [{"id": "own", "version": "1.0.0"}]})
    monkeypatch.setattr("specify_cli.bundles.command_validate._expand_manifest", lambda *a, **k: (_ for _ in ()).throw(BundlerError("expansion boom")))
    monkeypatch.setattr("specify_cli.bundles.references.make_reference_checker", lambda *a, **k: lambda component: "own problem" if component.id == "own" else None)
    result = runner.invoke(app, ["bundle", "validate", "--path", str(path)])
    assert result.exit_code == 1
    assert result.output.count("expansion boom") == 1
    assert result.output.count("own problem") == 1
    assert result.output.index("expansion boom") < result.output.index("own problem")


def test_validate_flat_manifest_never_expands(project: Path, monkeypatch):
    path = project / "flat.yml"
    path.write_text(yaml.safe_dump(valid_manifest_dict(provides={})), encoding="utf-8")
    monkeypatch.setattr("specify_cli.bundles.command_validate._expand_manifest", lambda *a, **k: pytest.fail("flat manifest expanded"))
    result = runner.invoke(app, ["bundle", "validate", "--path", str(path), "--offline"])
    assert result.exit_code == 0, result.output


def test_validate_real_catalog_with_patched_download(project: Path, monkeypatch):
    path = _write_reference_bundle(project, [{"id": "child", "version": "1.0.0"}])
    child_path = project / "child.yml"
    child_path.write_text(yaml.safe_dump(valid_manifest_dict(bundle={"id": "child", "name": "Child", "version": "1.0.0", "role": "developer", "description": "child", "author": "tests", "license": "MIT"}, provides={})), encoding="utf-8")
    catalog = project / "catalog.json"
    write_catalog_file(catalog, {"child": catalog_entry_dict("child", version="1.0.0")})
    (project / ".specify" / "bundle-catalogs.yml").write_text(yaml.safe_dump({"schema_version": "1.0", "catalogs": [{"id": "file", "url": str(catalog), "priority": 0, "install_policy": "install-allowed"}]}), encoding="utf-8")
    monkeypatch.setattr("specify_cli.bundles.command_validate._download_manifest", lambda *a, **k: BundleManifest.from_file(child_path))
    result = runner.invoke(app, ["bundle", "validate", "--path", str(path)])
    assert result.exit_code == 0, result.output


def test_validate_reports_sibling_conflict(project: Path, monkeypatch):
    path = _write_reference_bundle(
        project,
        [{"id": "first", "version": "1.0.0"}, {"id": "second", "version": "1.0.0"}],
    )
    children = {
        "first": BundleManifest.from_dict(valid_manifest_dict(
            bundle={"id": "first", "name": "First", "version": "1.0.0", "role": "developer", "description": "first", "author": "tests", "license": "MIT"},
            provides={"extensions": [{"id": "shared", "version": "1.0.0"}]},
        )),
        "second": BundleManifest.from_dict(valid_manifest_dict(
            bundle={"id": "second", "name": "Second", "version": "1.0.0", "role": "developer", "description": "second", "author": "tests", "license": "MIT"},
            provides={"extensions": [{"id": "shared", "version": "2.0.0"}]},
        )),
    }

    class Stack:
        def resolve(self, bundle_id, version=None):
            return _selected(bundle_id)

    monkeypatch.setattr("specify_cli.bundles._commands._build_stack", lambda *a, **k: Stack())
    monkeypatch.setattr(
        "specify_cli.bundles.command_validate._download_manifest",
        lambda resolved, *, offline: children[resolved.entry.id],
    )
    result = runner.invoke(app, ["bundle", "validate", "--path", str(path)])
    assert result.exit_code == 1, result.output
    assert "declare 'shared'" in result.output


def test_validate_reports_override_warning(project: Path, monkeypatch):
    path = _write_reference_bundle(
        project,
        [{"id": "child", "version": "1.0.0"}],
        provides={"extensions": [{"id": "shared", "version": "2.0.0"}]},
    )
    child = BundleManifest.from_dict(valid_manifest_dict(
        bundle={"id": "child", "name": "Child", "version": "1.0.0", "role": "developer", "description": "child", "author": "tests", "license": "MIT"},
        provides={"extensions": [{"id": "shared", "version": "1.0.0"}]},
    ))
    class Stack:
        def resolve(self, bundle_id, version=None):
            return _selected(bundle_id)

    monkeypatch.setattr("specify_cli.bundles._commands._build_stack", lambda *a, **k: Stack())
    monkeypatch.setattr("specify_cli.bundles.command_validate._download_manifest", lambda *a, **k: child)
    monkeypatch.setattr("specify_cli.bundles.references.make_reference_checker", lambda *a, **k: lambda component: None)
    result = runner.invoke(app, ["bundle", "validate", "--path", str(path)])
    assert result.exit_code == 0, result.output
    assert "overrides" in result.output


def test_validate_inherited_component_error_names_origin_chain(project: Path, monkeypatch):
    parent = reference_manifest_dict(
        [{"id": "child", "version": "1.0.0"}],
        bundle_id="parent",
        extensions=[{"id": "own-ext", "version": "1.0.0"}],
    )
    child = valid_manifest_dict(
        bundle={"id": "child", "name": "Child", "version": "1.0.0", "role": "developer", "description": "child", "author": "tests", "license": "MIT"},
        provides={"extensions": [{"id": "child-ext", "version": "1.0.0"}]},
    )
    path = project / "bundle.yml"
    path.write_text(yaml.safe_dump(parent), encoding="utf-8")
    selected = SimpleNamespace(
        entry=SimpleNamespace(id="child", version="1.0.0", verified=True),
        source=SimpleNamespace(id="default"),
        install_allowed=True,
    )

    class Stack:
        def resolve(self, bundle_id, version=None):
            return selected

    monkeypatch.setattr("specify_cli.bundles._commands._build_stack", lambda *a, **k: Stack())
    monkeypatch.setattr("specify_cli.bundles.command_validate._download_manifest", lambda *a, **k: BundleManifest.from_dict(child))
    monkeypatch.setattr(
        "specify_cli.bundles.references.make_reference_checker",
        lambda *a, **k: lambda component: f"unresolved {component.id}",
    )
    result = runner.invoke(app, ["bundle", "validate", "--path", str(path)])
    assert result.exit_code == 1, result.output
    output = " ".join(result.output.split())
    assert "Unresolved reference extension:child-ext@1.0.0 (from parent → child): unresolved child-ext" in output
    assert "Unresolved reference extension:own-ext@1.0.0: unresolved own-ext" in output
    assert "from parent" not in output.split("own-ext@1.0.0", 1)[1]


def test_validate_offline_and_flat_error_text_unchanged(project: Path, monkeypatch):
    flat_data = valid_manifest_dict(
        bundle={"id": "flat-bundle", "name": "Flat", "version": "1.0.0", "role": "developer", "description": "flat", "author": "tests", "license": "MIT"},
        provides={"extensions": [{"id": "ext-a", "version": "1.0.0"}]},
    )
    path = project / "bundle.yml"
    path.write_text(yaml.safe_dump(flat_data), encoding="utf-8")
    monkeypatch.setattr(
        "specify_cli.bundles.references.make_reference_checker",
        lambda *a, **k: lambda component: "flat problem",
    )
    result_flat = runner.invoke(app, ["bundle", "validate", "--path", str(path)])
    assert result_flat.exit_code == 1
    assert "Unresolved reference extension:ext-a@1.0.0: flat problem" in " ".join(result_flat.output.split())
    assert "(from" not in result_flat.output

    ref_data = reference_manifest_dict(
        [{"id": "child", "version": "1.0.0"}],
        bundle_id="parent-bundle",
        extensions=[{"id": "own-ext", "version": "1.0.0"}],
    )
    path.write_text(yaml.safe_dump(ref_data), encoding="utf-8")
    result_offline = runner.invoke(app, ["bundle", "validate", "--offline", "--path", str(path)])
    assert result_offline.exit_code == 1
    assert "Unresolved reference extension:own-ext@1.0.0: flat problem" in " ".join(result_offline.output.split())
    assert "(from" not in result_offline.output
