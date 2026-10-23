from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundler import BundlerError
from specify_cli.bundles import _commands, command_install
from specify_cli.bundles._commands import _resolve_init_integration
from specify_cli.bundles.manifest import BundleManifest
from specify_cli.bundles.packager import build_bundle
from tests.specify_cli.bundles.helpers import (
    FakeInstaller,
    bundled_extension_version,
    catalog_entry_dict,
    make_project,
    valid_manifest_dict,
    reference_manifest_dict,
    write_catalog_file,
    write_manifest,
)

runner = CliRunner()
REPO_ROOT = Path(__file__).parents[3]


@pytest.mark.parametrize("refresh", [False, True])
def test_bundled_patch_upgrade_warns_and_records_actual_version(
    project: Path, monkeypatch, refresh: bool,
):
    import specify_cli._assets as assets
    from specify_cli.bundles.records import load_records

    source = project / "packaged-bug"
    shutil.copytree(REPO_ROOT / "extensions" / "bug", source)
    source_manifest = source / "extension.yml"
    data = yaml.safe_load(source_manifest.read_text(encoding="utf-8"))
    data["extension"]["version"] = "1.0.0" if refresh else "1.0.1"
    source_manifest.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setattr(assets, "_locate_bundled_extension", lambda cid: source)
    bundle = write_manifest(
        project / "custom-bundle",
        valid_manifest_dict(provides={"extensions": [{"id": "bug", "version": "1.0.0"}]}),
    )
    args = ["bundle", "install", str(bundle), "--offline"]
    if refresh:
        initial = runner.invoke(app, args)
        assert initial.exit_code == 0, initial.output
        data["extension"]["version"] = "1.0.1"
        source_manifest.write_text(yaml.safe_dump(data), encoding="utf-8")
        args.append("--refresh")

    result = runner.invoke(app, args)

    assert result.exit_code == 0, result.output
    output = " ".join(result.output.split())
    assert "Warning:" in output
    assert "1.0.0" in output and "1.0.1" in output
    record = load_records(project)[0]
    assert record.contributed_components[0].version == "1.0.0"
    assert record.installed_versions == {"extensions:bug": "1.0.1"}
    installed = yaml.safe_load(
        (project / ".specify/extensions/bug/extension.yml").read_text(encoding="utf-8")
    )
    assert installed["extension"]["version"] == "1.0.1"
    listed = runner.invoke(app, ["bundle", "list", "--json"])
    assert listed.exit_code == 0, listed.output
    assert json.loads(listed.stdout)[0]["installed_versions"] == record.installed_versions
    repeated = runner.invoke(app, ["bundle", "install", str(bundle), "--offline"])
    assert repeated.exit_code == 0, repeated.output
    assert load_records(project)[0].installed_versions == record.installed_versions
    shared_data = valid_manifest_dict(
        provides={"extensions": [{"id": "bug", "version": "1.0.0"}]},
    )
    shared_data["bundle"]["id"] = "shared-bundle"
    shared = write_manifest(project / "shared-bundle", shared_data)
    shared_result = runner.invoke(app, ["bundle", "install", str(shared), "--offline"])
    assert shared_result.exit_code == 0, shared_result.output
    shared_refresh = runner.invoke(
        app, ["bundle", "install", str(bundle), "--offline", "--refresh"],
    )
    assert shared_refresh.exit_code == 0, shared_refresh.output
    shared_data["bundle"]["id"] = "conflicting-bundle"
    shared_data["provides"]["extensions"][0]["version"] = "1.0.1"
    conflicting = write_manifest(project / "conflicting-bundle", shared_data)
    rejected = runner.invoke(
        app, ["bundle", "install", str(conflicting), "--offline"],
    )
    assert rejected.exit_code == 1, rejected.output
    assert {r.bundle_id for r in load_records(project)} == {"demo-bundle", "shared-bundle"}
    removed = runner.invoke(app, ["bundle", "remove", "demo-bundle"])
    assert removed.exit_code == 0, removed.output
    assert (project / ".specify/extensions/bug").exists()
    assert load_records(project)[0].installed_versions == record.installed_versions
    removed_shared = runner.invoke(app, ["bundle", "remove", "shared-bundle"])
    assert removed_shared.exit_code == 0, removed_shared.output
    assert not (project / ".specify/extensions/bug").exists()


def _bundled_workflow_manifest(workflow_id: str, version: str = "1.0.0") -> dict:
    return valid_manifest_dict(
        provides={"workflows": [{"id": workflow_id, "version": version}]}
    )


@pytest.mark.parametrize(
    ("command", "bundle_id", "extension_id"),
    [("install", "bugfix", "bug"), ("add", "assess", "assess")],
)
def test_local_firstparty_bundle_installs_bundled_components_offline(
    project: Path, command: str, bundle_id: str, extension_id: str
):
    bundle_dir = REPO_ROOT / "bundles" / bundle_id

    result = runner.invoke(app, ["bundle", command, str(bundle_dir), "--offline"])

    assert result.exit_code == 0, result.output
    assert (
        project / ".specify" / "extensions" / extension_id / "extension.yml"
    ).is_file()
    assert (project / ".specify" / "workflows" / bundle_id / "workflow.yml").is_file()
    registry = json.loads(
        (project / ".specify" / "workflows" / "workflow-registry.json").read_text(
            encoding="utf-8"
        )
    )
    assert registry["workflows"][bundle_id]["version"] == "1.0.0"


def test_local_parent_installs_referenced_catalog_components(
    project: Path, monkeypatch
):
    """A local parent expands through the same catalog stack as a catalog root."""
    child_version = bundled_extension_version("agent-context")
    child = BundleManifest.from_dict(
        valid_manifest_dict(
            bundle={
                "id": "child-pack",
                "name": "Child Pack",
                "version": "1.0.0",
                "role": "developer",
                "description": "child",
                "author": "tests",
                "license": "MIT",
            },
            provides={
                "extensions": [{"id": "agent-context", "version": child_version}]
            },
        )
    )
    parent_path = write_manifest(
        project / "parent-pack",
        reference_manifest_dict(
            [{"id": "child-pack", "version": "1.0.0"}],
            bundle_id="parent-pack",
        ),
    )

    resolved = SimpleNamespace(
        entry=SimpleNamespace(id="child-pack"),
        source=SimpleNamespace(id="test-catalog"),
        install_allowed=True,
    )

    class Stack:
        def resolve(self, bundle_id, version=None):
            assert (bundle_id, version) == ("child-pack", "1.0.0")
            return resolved

    monkeypatch.setattr(_commands, "_build_stack", lambda *args, **kwargs: Stack())
    monkeypatch.setattr(
        command_install,
        "_download_manifest",
        lambda selected, *, offline: child,
    )

    result = runner.invoke(app, ["bundle", "add", str(parent_path), "--offline"])

    assert result.exit_code == 0, result.output
    assert (project / ".specify/extensions/agent-context/extension.yml").is_file()
    from specify_cli.bundles.records import load_records

    record = load_records(project)[0]
    assert record.bundle_id == "parent-pack"
    assert [(c.kind, c.id) for c in record.required_components] == [
        ("extensions", "agent-context")
    ]
    assert record.bundle_references[0].id == "child-pack"


def test_install_rejects_reference_source_mismatch(project: Path, monkeypatch):
    parent_path = write_manifest(
        project / "parent-pack",
        reference_manifest_dict(
            [{"id": "child-pack", "version": "1.0.0", "source": "X"}],
            bundle_id="parent-pack",
        ),
    )
    selected = SimpleNamespace(
        entry=SimpleNamespace(id="child-pack"),
        source=SimpleNamespace(id="winner"),
        install_allowed=True,
    )

    class Stack:
        def resolve(self, bundle_id, version=None):
            return selected

    monkeypatch.setattr(_commands, "_build_stack", lambda *a, **k: Stack())
    result = runner.invoke(app, ["bundle", "install", str(parent_path), "--offline"])

    assert result.exit_code == 1, result.output
    assert "requires source" in result.output


def test_catalog_root_reference_install_builds_stack_once(
    project: Path, monkeypatch
):
    child_version = bundled_extension_version("agent-context")
    parent = BundleManifest.from_dict(
        reference_manifest_dict(
            [{"id": "child-pack", "version": "1.0.0"}], bundle_id="parent-pack"
        )
    )
    child_data = valid_manifest_dict(
        provides={"extensions": [{"id": "agent-context", "version": child_version}]}
    )
    child_data["bundle"] = {
        "id": "child-pack", "name": "Child", "version": "1.0.0",
        "role": "developer", "description": "child", "author": "tests",
        "license": "MIT",
    }
    child = BundleManifest.from_dict(child_data)
    selected = {
        "parent-pack": SimpleNamespace(
            entry=SimpleNamespace(id="parent-pack"),
            source=SimpleNamespace(id="default"),
            install_allowed=True,
        ),
        "child-pack": SimpleNamespace(
            entry=SimpleNamespace(id="child-pack"),
            source=SimpleNamespace(id="default"),
            install_allowed=True,
        ),
    }
    builds = 0

    class Stack:
        def resolve(self, bundle_id, version=None):
            return selected[bundle_id]

    def build_stack(*args, **kwargs):
        nonlocal builds
        builds += 1
        return Stack()

    monkeypatch.setattr(command_install, "_build_stack", build_stack)
    monkeypatch.setattr(
        command_install,
        "_download_manifest",
        lambda resolved, *, offline: parent if resolved.entry.id == "parent-pack" else child,
    )

    result = runner.invoke(app, ["bundle", "install", "parent-pack", "--offline"])

    assert result.exit_code == 0, result.output
    assert builds == 1
    assert (project / ".specify/extensions/agent-context/extension.yml").is_file()


def test_flat_local_install_never_builds_catalog_stack(project: Path, monkeypatch):
    bundle = write_manifest(project / "flat", valid_manifest_dict(provides={}))

    monkeypatch.setattr(
        command_install,
        "_build_stack",
        lambda *args, **kwargs: pytest.fail("flat local install built a catalog stack"),
    )

    result = runner.invoke(app, ["bundle", "install", str(bundle), "--offline"])

    assert result.exit_code == 0, result.output


def test_reference_only_parent_installs_without_own_components(
    project: Path, monkeypatch
):
    child = BundleManifest.from_dict(
        valid_manifest_dict(
            bundle={
                "id": "child-pack", "name": "Child", "version": "1.0.0",
                "role": "developer", "description": "child", "author": "tests",
                "license": "MIT",
            },
            provides={"extensions": [{"id": "child-ext", "version": "1.0.0"}]},
        )
    )
    parent_path = write_manifest(
        project / "reference-only-parent",
        reference_manifest_dict(
            [{"id": "child-pack", "version": "1.0.0"}],
            bundle_id="reference-only-parent",
        ),
    )
    resolved = SimpleNamespace(
        entry=SimpleNamespace(id="child-pack"),
        source=SimpleNamespace(id="test-catalog"),
        install_allowed=True,
    )

    class Stack:
        def resolve(self, bundle_id, version=None):
            return resolved

    monkeypatch.setattr(_commands, "_build_stack", lambda *a, **k: Stack())
    monkeypatch.setattr(command_install, "_download_manifest", lambda *a, **k: child)
    installer = FakeInstaller()
    monkeypatch.setattr(
        "specify_cli.bundles.adapters.DefaultPrimitiveInstaller",
        lambda **kwargs: installer,
    )
    result = runner.invoke(app, ["bundle", "install", str(parent_path), "--offline"])
    assert result.exit_code == 0, result.output
    assert installer.install_calls == [("extensions", "child-ext")]


def test_no_project_reference_gate_runs_before_init(tmp_path: Path, monkeypatch):
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.chdir(empty)
    child_data = valid_manifest_dict(
        bundle={
            "id": "child-pack", "name": "Child", "version": "1.0.0",
            "role": "developer", "description": "child", "author": "tests",
            "license": "MIT",
        },
        requires={"speckit_version": ">=999.0.0"},
        provides={"extensions": []},
    )
    child = BundleManifest.from_dict(child_data)
    parent = write_manifest(
        tmp_path / "parent",
        reference_manifest_dict(
            [{"id": "child-pack", "version": "1.0.0"}], bundle_id="parent"
        ),
    )
    resolved = SimpleNamespace(
        entry=SimpleNamespace(id="child-pack"),
        source=SimpleNamespace(id="test-catalog"),
        install_allowed=True,
    )

    class Stack:
        def resolve(self, bundle_id, version=None):
            return resolved

    monkeypatch.setattr(_commands, "_build_stack", lambda *a, **k: Stack())
    monkeypatch.setattr(command_install, "_download_manifest", lambda *a, **k: child)
    with patch("specify_cli.bundles.command_install._run_init") as run_init:
        result = runner.invoke(app, ["bundle", "install", str(parent), "--offline"])
    assert result.exit_code == 1
    assert "Bundle 'child-pack'" in result.output
    run_init.assert_not_called()
    assert not (empty / ".specify").exists()


def test_discovery_only_reference_is_rejected_with_parent_chain(
    project: Path, monkeypatch
):
    child = BundleManifest.from_dict(
        valid_manifest_dict(
            bundle={
                "id": "child-pack", "name": "Child", "version": "1.0.0",
                "role": "developer", "description": "child", "author": "tests",
                "license": "MIT",
            },
            provides={"extensions": []},
        )
    )
    parent = write_manifest(
        project / "parent",
        reference_manifest_dict(
            [{"id": "child-pack", "version": "1.0.0"}], bundle_id="parent"
        ),
    )
    resolved = SimpleNamespace(
        entry=SimpleNamespace(id="child-pack"),
        source=SimpleNamespace(id="community"),
        install_allowed=False,
    )

    class Stack:
        def resolve(self, bundle_id, version=None):
            return resolved

    monkeypatch.setattr(_commands, "_build_stack", lambda *a, **k: Stack())
    monkeypatch.setattr(command_install, "_download_manifest", lambda *a, **k: child)
    result = runner.invoke(app, ["bundle", "install", str(parent), "--offline"])
    assert result.exit_code == 1
    assert "discovery-only" in result.output
    assert "parent → child-pack" in result.output
    assert not (project / ".specify/bundle-records.json").exists()


def test_offline_reference_failure_names_reference_and_chain(
    project: Path, monkeypatch
):
    parent = write_manifest(
        project / "parent",
        reference_manifest_dict(
            [{"id": "child", "version": "1.0.0"}], bundle_id="parent"
        ),
    )
    resolved = SimpleNamespace(
        entry=SimpleNamespace(id="child"),
        source=SimpleNamespace(id="default"),
        install_allowed=True,
    )

    class Stack:
        def resolve(self, bundle_id, version=None):
            return resolved

    def offline_download(selected, *, offline):
        raise BundlerError("Network access disabled")

    monkeypatch.setattr(_commands, "_build_stack", lambda *a, **k: Stack())
    monkeypatch.setattr(command_install, "_download_manifest", offline_download)
    result = runner.invoke(app, ["bundle", "install", str(parent), "--offline"])
    assert result.exit_code == 1
    assert "Cannot resolve bundle reference child@1.0.0" in result.output
    assert "child@1.0.0 (parent):" in result.output
    assert "Network access" in result.output
    assert not (project / ".specify/bundle-records.json").exists()


def test_local_reference_bundle_offline_names_reference_and_network_limit(project: Path):
    parent = write_manifest(
        project / "parent",
        reference_manifest_dict(
            [{"id": "missing-child", "version": "1.0.0"}], bundle_id="parent"
        ),
    )

    result = runner.invoke(app, ["bundle", "install", str(parent), "--offline"])

    assert result.exit_code == 1, result.output
    output = " ".join(result.output.split())
    assert "Cannot resolve bundle reference missing-child@1.0.0 (parent)" in output
    assert "Network access disabled" in output
    assert "not found in any configured catalog" not in output


def test_local_bundle_rejects_mismatched_bundled_workflow_pin_offline(project: Path):
    bundle_dir = project / "mismatched-workflow-pin"
    (bundle_dir / "bundle.yml").parent.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(_bundled_workflow_manifest("bugfix", "9.9.9")),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["bundle", "install", str(bundle_dir), "--offline"])

    assert result.exit_code == 1
    assert "pinned to version 9.9.9" in result.output
    assert not (project / ".specify" / "workflows" / "bugfix").exists()


def test_local_bundle_with_non_positive_priority_is_rejected_before_any_install(
    project: Path,
):
    """A priority the preset installer refuses must fail before earlier components install."""
    bundle_dir = project / "zero-priority"
    bundle_dir.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(
            valid_manifest_dict(
                provides={
                    "extensions": [
                        {"id": "bug", "version": bundled_extension_version("bug")}
                    ],
                    "presets": [
                        {"id": "lean", "version": "1.0.0", "priority": 0, "strategy": "replace"}
                    ],
                }
            )
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["bundle", "install", str(bundle_dir), "--offline"])

    assert result.exit_code == 1
    assert "preset 'lean' priority must be 1 or higher, got 0" in " ".join(
        result.output.split()
    )
    assert not (project / ".specify" / "extensions").exists()


def test_local_bundle_refuses_unbundled_workflow_offline(project: Path):
    bundle_dir = project / "unbundled-workflow"
    (bundle_dir / "bundle.yml").parent.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(_bundled_workflow_manifest("not-bundled")), encoding="utf-8"
    )

    result = runner.invoke(app, ["bundle", "install", str(bundle_dir), "--offline"])

    assert result.exit_code == 1
    assert "network access is disabled" in " ".join(result.output.lower().split())


def test_local_bundle_refuses_independently_installed_extension_at_other_version(
    project: Path,
):
    from specify_cli.bundles.records import records_path

    older = project / "bug-older"
    shutil.copytree(REPO_ROOT / "extensions" / "bug", older)
    ext_manifest = yaml.safe_load((older / "extension.yml").read_text(encoding="utf-8"))
    ext_manifest["extension"]["version"] = "0.0.1"
    (older / "extension.yml").write_text(yaml.safe_dump(ext_manifest), encoding="utf-8")
    added = runner.invoke(app, ["extension", "add", str(older), "--dev"])
    assert added.exit_code == 0, added.output

    pinned = bundled_extension_version("bug")
    bundle_dir = project / "pins-bug"
    bundle_dir.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(
            valid_manifest_dict(
                provides={"extensions": [{"id": "bug", "version": pinned}]}
            )
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["bundle", "install", str(bundle_dir), "--offline"])

    assert result.exit_code == 1
    assert f"extension 'bug' to {pinned}, but 0.0.1 is installed" in " ".join(
        result.output.split()
    )
    assert not records_path(project).exists()
    registry = json.loads(
        (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
    )
    assert registry["extensions"]["bug"]["version"] == "0.0.1"


def test_install_refuses_discovery_only_source(project: Path, monkeypatch):
    # Point a discovery-only catalog at a local payload containing the bundle.
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
    result = runner.invoke(app, ["bundle", "install", "demo", "--offline"])
    assert result.exit_code == 1
    assert "discovery-only" in result.output


@pytest.mark.parametrize("command", ["install", "add"])
@pytest.mark.parametrize("source_kind", ["directory", "manifest", "broken-zip"])
def test_version_rejects_local_bundle_source_before_reading(
    tmp_path: Path, monkeypatch, command: str, source_kind: str
):
    workdir = tmp_path / "outside-project"
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    if source_kind == "directory":
        source = tmp_path / "broken-bundle"
        source.mkdir()
    elif source_kind == "manifest":
        source = tmp_path / "bundle.yml"
        source.write_text("bundle: [not, a, mapping", encoding="utf-8")
    else:
        source = tmp_path / "broken.zip"
        source.write_bytes(b"not a zip archive")

    with patch("specify_cli.bundles.command_install._run_init") as run_init:
        result = runner.invoke(
            app, ["bundle", command, str(source), "--version", "1.0.0", "--offline"]
        )

    assert result.exit_code == 1
    assert "--version requires a catalog bundle ID" in result.output
    run_init.assert_not_called()
    assert not (workdir / ".specify").exists()


def test_version_rejects_blank_and_refresh_before_resolution(project: Path):
    blank = runner.invoke(
        app, ["bundle", "install", "history", "--version", " ", "--offline"]
    )
    refresh = runner.invoke(
        app, ["bundle", "install", "history", "--version", "1.0.0", "--refresh", "--offline"]
    )

    assert blank.exit_code == 1
    assert "--version must not be blank" in blank.output
    assert refresh.exit_code == 1
    assert "--version cannot be used with --refresh" in refresh.output


def test_install_integration_override_cannot_bypass_clash_guard(project: Path):
    # An initialized project's recorded active integration is authoritative:
    # passing --integration must not let a differently-pinned bundle install.
    import json

    (project / ".specify" / "integration.json").write_text(
        json.dumps({"integration": "copilot"}), encoding="utf-8"
    )
    bundle_dir = project / "claude-bundle"
    bundle_dir.mkdir()
    data = valid_manifest_dict(integration={"id": "claude"})
    (bundle_dir / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    (bundle_dir / "README.md").write_text("# Claude bundle", encoding="utf-8")

    result = runner.invoke(
        app,
        ["bundle", "install", str(bundle_dir), "--integration", "claude", "--offline"],
    )
    assert result.exit_code == 1
    assert "claude" in result.output and "copilot" in result.output


def test_install_bundled_extension_from_zip_offline(tmp_path: Path):
    """End-to-end: build → install (offline, local .zip) → list → remove."""
    project = make_project(tmp_path / "proj")

    bundle_dir = tmp_path / "mini"
    bundle_dir.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "bundle": {
                    "id": "mini",
                    "name": "Mini",
                    "version": "1.0.0",
                    "role": "developer",
                    "description": "minimal",
                    "author": "tests",
                    "license": "MIT",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "extensions": [
                        {
                            "id": "agent-context",
                            "version": bundled_extension_version("agent-context"),
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "README.md").write_text("# Mini\n", encoding="utf-8")

    runner = CliRunner()
    previous = Path.cwd()
    os.chdir(project)
    try:
        build = runner.invoke(app, ["bundle", "build", "--path", str(bundle_dir)])
        assert build.exit_code == 0, build.output
        artifact = next(bundle_dir.glob("*.zip"))

        install = runner.invoke(app, ["bundle", "install", str(artifact), "--offline"])
        assert install.exit_code == 0, install.output

        from specify_cli.extensions import ExtensionManager

        assert ExtensionManager(project).registry.is_installed("agent-context")

        listing = runner.invoke(app, ["bundle", "list"])
        assert "mini" in listing.output

        remove = runner.invoke(app, ["bundle", "remove", "mini"])
        assert remove.exit_code == 0, remove.output
        assert not ExtensionManager(project).registry.is_installed("agent-context")
    finally:
        os.chdir(previous)


def test_malformed_manifest_yaml_fails_alike_for_every_local_source(tmp_path: Path):
    """`bundle install` reports malformed YAML the same way for all 3 sources.

    Directory and bundle.yml sources already exited 1 with an "Invalid YAML"
    message; the .zip source dumped a yaml.parser.ParserError traceback.
    """
    bad_yaml = "bundle: [unclosed\n  id: demo\n"

    directory = tmp_path / "dir-src"
    directory.mkdir()
    (directory / "bundle.yml").write_text(bad_yaml, encoding="utf-8")

    manifest_file = tmp_path / "standalone.yml"
    manifest_file.write_text(bad_yaml, encoding="utf-8")

    artifact = tmp_path / "artifact.zip"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("bundle.yml", bad_yaml)

    runner = CliRunner()
    for source in (directory, manifest_file, artifact):
        result = runner.invoke(app, ["bundle", "install", str(source)])
        assert result.exit_code == 1, f"{source.name}: {result.output}"
        assert result.exception is None or isinstance(result.exception, SystemExit), (
            f"{source.name} leaked {type(result.exception).__name__}"
        )
        assert "Invalid YAML" in result.output, f"{source.name}: {result.output}"


def test_invalid_local_manifest_is_rejected_before_project_init(
    tmp_path: Path,
    monkeypatch,
):
    bundle_dir = tmp_path / "invalid-bundle"
    data = valid_manifest_dict()
    data["bundle"]["author"] = ""
    write_manifest(bundle_dir, data)
    empty_cwd = tmp_path / "empty"
    empty_cwd.mkdir()
    monkeypatch.chdir(empty_cwd)

    runner = CliRunner()
    with patch("specify_cli.bundles.command_install._run_init") as run_init:
        result = runner.invoke(
            app,
            ["bundle", "install", str(bundle_dir), "--offline"],
        )

    assert result.exit_code == 1
    assert "Missing required field: bundle.author" in result.output
    run_init.assert_not_called()


def test_incompatible_local_manifest_is_rejected_before_project_init(
    tmp_path: Path,
    monkeypatch,
):
    bundle_dir = tmp_path / "incompatible-bundle"
    data = valid_manifest_dict()
    data["requires"]["speckit_version"] = ">=999.0.0"
    write_manifest(bundle_dir, data)
    empty_cwd = tmp_path / "empty"
    empty_cwd.mkdir()
    monkeypatch.chdir(empty_cwd)

    runner = CliRunner()
    with patch("specify_cli.bundles.command_install._run_init") as run_init:
        result = runner.invoke(
            app,
            ["bundle", "install", str(bundle_dir), "--offline"],
        )

    assert result.exit_code == 1
    assert "requires Spec Kit >=999.0.0" in result.output
    run_init.assert_not_called()


@pytest.mark.parametrize("source_kind", ["manifest", "directory", "zip"])
@pytest.mark.parametrize("bundle_version", ["1.2.0", "2.0.0"])
def test_local_install_refresh_updates_owned_components(
    tmp_path: Path,
    monkeypatch,
    source_kind: str,
    bundle_version: str,
):
    """Local upgrades refresh owned pins before advancing the bundle record."""
    from specify_cli.bundles.records import load_records, records_path

    project = make_project(tmp_path / "proj")
    monkeypatch.chdir(project)
    versions = {}

    class VersionedInstaller(FakeInstaller):
        def install(self, root, component):
            super().install(root, component)
            versions[(component.kind, component.id)] = component.version

        def refresh(self, root, component):
            assert load_records(root)[0].version == "1.2.0"
            super().refresh(root, component)
            versions[(component.kind, component.id)] = component.version

    installer = VersionedInstaller()
    monkeypatch.setattr(
        "specify_cli.bundles.adapters.DefaultPrimitiveInstaller",
        lambda **kwargs: installer,
    )
    data = valid_manifest_dict()
    manifest_path = write_manifest(tmp_path / "local bundle", data)
    runner = CliRunner()
    first = runner.invoke(app, ["bundle", "install", str(manifest_path), "--offline"])
    assert first.exit_code == 0, first.output
    original_record = records_path(project).read_bytes()
    original_versions = dict(versions)

    data["bundle"]["version"] = bundle_version
    data["provides"]["extensions"][0]["version"] = "2.0.0"
    data["provides"]["presets"][0]["version"] = "3.0.0"
    data["provides"]["workflows"][0]["version"] = "0.4.0"
    write_manifest(manifest_path.parent, data)
    if source_kind == "manifest":
        source = manifest_path
    elif source_kind == "directory":
        source = manifest_path.parent
    else:
        source = tmp_path / "local bundle.zip"
        with zipfile.ZipFile(source, "w") as archive:
            archive.write(manifest_path, "bundle.yml")

    rejected = runner.invoke(app, ["bundle", "install", str(source), "--offline"])
    assert rejected.exit_code == 1, rejected.output
    assert records_path(project).read_bytes() == original_record
    assert versions == original_versions
    assert installer.refresh_calls == []

    refreshed = runner.invoke(
        app,
        ["bundle", "install", str(source), "--offline", "--refresh"],
    )
    assert refreshed.exit_code == 0, refreshed.output
    assert "--refresh" in rejected.output
    assert "4 refreshed" in refreshed.output
    expected = {
        ("extensions", "ext-a"): "2.0.0",
        ("presets", "preset-a"): "3.0.0",
        ("steps", "step-a"): None,
        ("workflows", "wf-a"): "0.4.0",
    }
    assert versions == expected
    assert set(installer.refresh_calls) == set(expected)
    record = load_records(project)[0]
    assert record.version == bundle_version
    assert {
        (c.kind, c.id): c.version for c in record.contributed_components
    } == expected


@pytest.mark.parametrize("source_kind", ["manifest", "directory", "zip"])
@pytest.mark.parametrize("bundle_version", ["1.2.0", "2.0.0"])
def test_local_refresh_catalog_extension_requires_network(
    tmp_path: Path,
    monkeypatch,
    source_kind: str,
    bundle_version: str,
):
    """Use the real installer; replace only catalog I/O with local artifacts."""
    from specify_cli.bundles.records import load_records, records_path
    from specify_cli.extensions import ExtensionCatalog

    project = make_project(tmp_path / "project")
    monkeypatch.chdir(project)
    monkeypatch.setattr(
        "specify_cli.bundles.command_install._bundle_overlaps", lambda *a, **kw: []
    )
    monkeypatch.setattr(
        "specify_cli._assets._locate_bundled_extension", lambda cid: None
    )
    version = "1.0.0"
    downloads = []

    def download_extension_info(self, info):
        extension_id = info["id"]
        downloads.append((extension_id, version))
        artifact = tmp_path / "extension.zip"
        extension = {
            "schema_version": "1.0",
            "extension": {
                "id": extension_id,
                "name": "Catalog extension",
                "version": version,
                "description": "Refresh regression",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {"name": "speckit.catalog-ext.hello", "file": "commands/hello.md"},
                ]
            },
        }
        with zipfile.ZipFile(artifact, "w") as archive:
            archive.writestr("extension.yml", yaml.safe_dump(extension))
            archive.writestr(
                "commands/hello.md", f"---\ndescription: Test\n---\n{version}\n"
            )
        return artifact

    monkeypatch.setattr(
        ExtensionCatalog,
        "_fetch_single_catalog",
        lambda self, entry, force_refresh=False: {
            "schema_version": "1.0",
            "extensions": {"catalog-ext": {"version": version}},
        },
    )
    monkeypatch.setattr(
        ExtensionCatalog, "download_extension_info", download_extension_info
    )
    data = valid_manifest_dict(
        provides={"extensions": [{"id": "catalog-ext", "version": version}]}
    )
    manifest_path = write_manifest(tmp_path / "local bundle", data)
    runner = CliRunner()
    first = runner.invoke(app, ["bundle", "install", str(manifest_path)])
    assert first.exit_code == 0, first.output
    installed_dir = project / ".specify" / "extensions" / "catalog-ext"
    payload = installed_dir / "commands" / "hello.md"
    original_payload = payload.read_bytes()
    original_manifest = (installed_dir / "extension.yml").read_bytes()
    original_record = records_path(project).read_bytes()

    version = "2.0.0"
    data["bundle"]["version"] = bundle_version
    data["provides"]["extensions"][0]["version"] = version
    write_manifest(manifest_path.parent, data)
    if source_kind == "manifest":
        source = manifest_path
    elif source_kind == "directory":
        source = manifest_path.parent
    else:
        source = tmp_path / "local bundle.zip"
        with zipfile.ZipFile(source, "w") as archive:
            archive.write(manifest_path, "bundle.yml")

    rejected = runner.invoke(app, ["bundle", "install", str(source), "--offline"])
    assert rejected.exit_code == 1, rejected.output
    assert "--refresh" in rejected.output
    assert downloads == [("catalog-ext", "1.0.0")]
    assert records_path(project).read_bytes() == original_record
    assert payload.read_bytes() == original_payload
    assert (installed_dir / "extension.yml").read_bytes() == original_manifest

    offline = runner.invoke(
        app, ["bundle", "install", str(source), "--refresh", "--offline"]
    )
    assert offline.exit_code == 1, offline.output
    output = " ".join(offline.output.split())
    assert "catalog-ext" in output
    assert "refreshing this component requires network access" in output
    assert "re-run without --offline" in output
    assert "install it first" not in output
    assert downloads == [("catalog-ext", "1.0.0")]
    assert records_path(project).read_bytes() == original_record
    assert payload.read_bytes() == original_payload
    assert (installed_dir / "extension.yml").read_bytes() == original_manifest

    refreshed = runner.invoke(app, ["bundle", "install", str(source), "--refresh"])
    assert refreshed.exit_code == 0, refreshed.output
    assert "1 refreshed" in refreshed.output
    assert downloads == [("catalog-ext", "1.0.0"), ("catalog-ext", "2.0.0")]
    assert payload.read_text(encoding="utf-8").endswith("2.0.0\n")
    assert (
        yaml.safe_load((installed_dir / "extension.yml").read_text(encoding="utf-8"))[
            "extension"
        ]["version"]
        == version
    )
    record = load_records(project)[0]
    assert record.version == bundle_version
    assert record.contributed_components[0].version == version


def _manifest(**overrides):
    data = valid_manifest_dict(**overrides)
    return BundleManifest.from_dict(data)


def _build_mini(tmp_path: Path) -> Path:
    bundle = tmp_path / "mini"
    bundle.mkdir()
    (bundle / "bundle.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "bundle": {
                    "id": "mini",
                    "name": "Mini",
                    "version": "1.0.0",
                    "role": "developer",
                    "description": "minimal",
                    "author": "tests",
                    "license": "MIT",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "extensions": [
                        {
                            "id": "agent-context",
                            "version": bundled_extension_version("agent-context"),
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    (bundle / "README.md").write_text("# Mini\n", encoding="utf-8")
    return build_bundle(bundle).artifact_path


def test_precedence_override_wins():
    manifest = _manifest(integration={"id": "claude"})
    assert _resolve_init_integration("gemini", manifest) == "gemini"


def test_precedence_bundle_declared_when_no_override():
    manifest = _manifest(integration={"id": "claude"})
    assert _resolve_init_integration(None, manifest) == "claude"


def test_precedence_default_when_unspecified():
    manifest = _manifest()
    assert _resolve_init_integration(None, manifest) == "copilot"
    assert _resolve_init_integration(None, None) == "copilot"


def test_precedence_default_honors_env_var(monkeypatch):
    monkeypatch.setenv("SPECKIT_INTEGRATION_DEFAULT", "gemini")
    # With no override and no bundle-declared integration, the env-var default
    # applies instead of the hardcoded "copilot".
    assert _resolve_init_integration(None, None) == "gemini"
    assert _resolve_init_integration(None, _manifest()) == "gemini"
    # Explicit override and bundle-declared integration still take precedence.
    assert _resolve_init_integration("claude", None) == "claude"
    assert (
        _resolve_init_integration(None, _manifest(integration={"id": "claude"}))
        == "claude"
    )


def test_install_initializes_uninitialized_project(tmp_path: Path):
    project = tmp_path / "proj"
    project.mkdir()
    artifact = _build_mini(tmp_path)

    previous = Path.cwd()
    os.chdir(project)
    try:
        result = runner.invoke(app, ["bundle", "install", str(artifact), "--offline"])
        assert result.exit_code == 0, result.output
    finally:
        os.chdir(previous)

    assert (project / ".specify").is_dir()
    marker = project / ".specify" / "integration.json"
    assert marker.exists()
    data = json.loads(marker.read_text(encoding="utf-8"))
    assert "copilot" in json.dumps(data)
