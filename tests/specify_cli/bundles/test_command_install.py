from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundles._commands import _resolve_init_integration
from specify_cli.bundles.manifest import BundleManifest
from specify_cli.bundles.packager import build_bundle
from tests.specify_cli.bundles.helpers import (
    FakeInstaller,
    bundled_extension_version,
    catalog_entry_dict,
    make_project,
    valid_manifest_dict,
    write_catalog_file,
    write_manifest,
)

runner = CliRunner()
REPO_ROOT = Path(__file__).parents[3]


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


def test_local_bundle_refuses_unbundled_workflow_offline(project: Path):
    bundle_dir = project / "unbundled-workflow"
    (bundle_dir / "bundle.yml").parent.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(_bundled_workflow_manifest("not-bundled")), encoding="utf-8"
    )

    result = runner.invoke(app, ["bundle", "install", str(bundle_dir), "--offline"])

    assert result.exit_code == 1
    assert "network access is disabled" in " ".join(result.output.lower().split())


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

    def download_extension(self, extension_id):
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
        "get_extension_info",
        lambda self, cid: {"id": cid, "version": version, "_install_allowed": True},
    )
    monkeypatch.setattr(ExtensionCatalog, "download_extension", download_extension)
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
