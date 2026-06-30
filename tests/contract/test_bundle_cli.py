"""Contract test for the `specify bundle` CLI surface (Typer integration).

Exercises the wired commands end-to-end via CliRunner against a temp project,
asserting exit codes and the cross-cutting error guarantees from
contracts/cli-commands.md (offline, discovery-only refusal, not-a-project error).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundler.services.packager import build_bundle
from tests.bundler_helpers import (
    catalog_entry_dict,
    valid_manifest_dict,
    write_catalog_file,
)

runner = CliRunner()


@pytest.fixture()
def project(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / ".specify").mkdir()
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_bundle_help_lists_all_commands():
    result = runner.invoke(app, ["bundle", "--help"])
    assert result.exit_code == 0
    for cmd in ("search", "info", "list", "install", "update", "remove",
                "validate", "build", "init", "catalog"):
        assert cmd in result.output


def test_update_accepts_integration_override():
    # Update must expose --integration so integration-pinned bundles can be
    # updated in projects where the active integration can't be auto-detected.
    # Rich may insert ANSI escapes between the two leading dashes, so match the
    # un-split option word rather than the literal "--integration".
    result = runner.invoke(app, ["bundle", "update", "--help"])
    assert result.exit_code == 0
    assert "integration" in result.output


def test_list_empty_project(project: Path):
    result = runner.invoke(app, ["bundle", "list"])
    assert result.exit_code == 0
    assert "No bundles installed" in result.output


def test_commands_outside_project_fail_with_guidance(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no .specify/
    result = runner.invoke(app, ["bundle", "list"])
    assert result.exit_code == 1
    assert "Spec Kit project" in result.output


def test_fail_writes_error_to_stderr_not_stdout(capsys):
    """_fail must write to stderr, not stdout: every bundle command routes errors
    through it, and under --json the error would otherwise corrupt the JSON payload
    that consumers read from stdout."""
    import typer

    from specify_cli.commands.bundle import _fail

    with pytest.raises(typer.Exit):
        _fail("something broke")
    captured = capsys.readouterr()
    assert "something broke" in captured.err
    assert "something broke" not in captured.out


def test_search_works_without_a_project(tmp_path: Path, monkeypatch):
    # Discovery commands fall back to the built-in/user catalog stack and must
    # not require a Spec Kit project (matches README/quickstart examples).
    monkeypatch.chdir(tmp_path)  # no .specify/
    result = runner.invoke(app, ["bundle", "search", "--offline", "--json"])
    assert result.exit_code == 0, result.output
    assert result.output.strip().startswith("[")


def test_info_unknown_bundle_without_project_reports_not_found(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no .specify/
    result = runner.invoke(app, ["bundle", "info", "does-not-exist", "--offline"])
    # Reaches catalog resolution (not the project gate) and reports a clean miss.
    assert result.exit_code == 1
    assert "Spec Kit project" not in result.output


def test_catalog_list_shows_builtin_defaults(project: Path):
    result = runner.invoke(app, ["bundle", "catalog", "list"])
    assert result.exit_code == 0
    assert "default" in result.output
    assert "community" in result.output
    assert "built-in default stack" in result.output


def test_catalog_add_and_remove(project: Path):
    catalog = project / "local-catalog.json"
    write_catalog_file(catalog, {"demo": catalog_entry_dict("demo")})

    added = runner.invoke(
        app, ["bundle", "catalog", "add", str(catalog), "--id", "local"]
    )
    assert added.exit_code == 0, added.output

    listed = runner.invoke(app, ["bundle", "catalog", "list"])
    assert "local" in listed.output

    removed = runner.invoke(app, ["bundle", "catalog", "remove", "local"])
    assert removed.exit_code == 0


def test_catalog_remove_builtin_is_refused(project: Path):
    result = runner.invoke(app, ["bundle", "catalog", "remove", "default"])
    assert result.exit_code == 1
    assert "built-in" in result.output


def test_validate_reports_invalid_manifest(project: Path):
    data = valid_manifest_dict()
    del data["bundle"]["license"]
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    result = runner.invoke(app, ["bundle", "validate"])
    assert result.exit_code == 1
    assert "license" in result.output


def test_validate_accepts_valid_manifest(project: Path):
    (project / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    # Offline mode does not fail on references it cannot verify (synthetic ids
    # here); they surface as warnings while structure is confirmed valid.
    result = runner.invoke(app, ["bundle", "validate", "--offline"])
    assert result.exit_code == 0, result.output
    assert "valid" in result.output


def test_validate_rejects_broken_reference(project: Path):
    # Synthetic component ids resolve to nothing in any catalog → hard failure.
    (project / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    result = runner.invoke(app, ["bundle", "validate"])
    assert result.exit_code == 1
    assert "preset-a" in result.output or "ext-a" in result.output


def test_validate_accepts_bundled_reference(project: Path):
    data = valid_manifest_dict()
    data["provides"] = {"extensions": [{"id": "agent-context", "version": "1.0.0"}]}
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    result = runner.invoke(app, ["bundle", "validate"])
    assert result.exit_code == 0, result.output
    assert "valid" in result.output


def test_build_produces_artifact(project: Path):
    (project / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    (project / "README.md").write_text("# Demo", encoding="utf-8")
    result = runner.invoke(app, ["bundle", "build", "--output", str(project / "dist")])
    assert result.exit_code == 0, result.output
    artifacts = list((project / "dist").glob("*.zip"))
    assert len(artifacts) == 1


def test_info_expands_full_component_set(project: Path):
    bundle_dir = project / "src-bundle"
    bundle_dir.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    catalog = project / "local-catalog.json"
    entry = catalog_entry_dict(
        "demo-bundle", download_url=str(bundle_dir / "bundle.yml")
    )
    write_catalog_file(catalog, {"demo-bundle": entry})
    added = runner.invoke(
        app, ["bundle", "catalog", "add", str(catalog), "--id", "local"]
    )
    assert added.exit_code == 0, added.output

    result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json", "--offline"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    components = {(c["kind"], c["id"]): c for c in payload["components"]}
    assert ("extensions", "ext-a") in components
    preset = components[("presets", "preset-a")]
    assert preset["version"] == "2.0.0"
    assert preset["priority"] == 10
    assert preset["strategy"] == "append"
    assert payload["trust"] == "verified"

    text = runner.invoke(app, ["bundle", "info", "demo-bundle", "--offline"])
    assert "preset-a v2.0.0" in text.output
    assert "Trust" in text.output


def test_info_expands_discovery_only_bundle(project: Path):
    # Discovery-only bundles must still be fully inspectable via `info`;
    # only `install` is refused for them.
    bundle_dir = project / "disc-bundle"
    bundle_dir.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    catalog = project / "disc-catalog.json"
    entry = catalog_entry_dict(
        "demo-bundle", download_url=str(bundle_dir / "bundle.yml")
    )
    write_catalog_file(catalog, {"demo-bundle": entry})
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {"id": "disc", "url": str(catalog), "priority": 1,
             "install_policy": "discovery-only"}
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )
    result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json", "--offline"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    components = {(c["kind"], c["id"]) for c in payload["components"]}
    assert ("extensions", "ext-a") in components


def test_info_resolves_local_zip_download_url(project: Path):
    # A local .zip artifact as download_url is extracted to read bundle.yml.
    bundle_dir = project / "zip-src"
    bundle_dir.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    (bundle_dir / "README.md").write_text("# Demo", encoding="utf-8")
    artifact = build_bundle(bundle_dir, output_dir=project / "dist").artifact_path
    catalog = project / "zip-catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=str(artifact))},
    )
    added = runner.invoke(
        app, ["bundle", "catalog", "add", str(catalog), "--id", "local"]
    )
    assert added.exit_code == 0, added.output
    result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json", "--offline"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    components = {(c["kind"], c["id"]) for c in payload["components"]}
    assert ("extensions", "ext-a") in components


def test_install_refuses_discovery_only_source(project: Path, monkeypatch):
    # Point a discovery-only catalog at a local payload containing the bundle.
    catalog = project / "disc.json"
    write_catalog_file(catalog, {"demo": catalog_entry_dict("demo")})
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {"id": "disc", "url": str(catalog), "priority": 1,
             "install_policy": "discovery-only"}
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )
    result = runner.invoke(app, ["bundle", "install", "demo", "--offline"])
    assert result.exit_code == 1
    assert "discovery-only" in result.output


def test_update_refuses_discovery_only_source(project: Path):
    # An installed bundle whose only resolvable source is discovery-only must
    # not be updatable from there (FR-025), mirroring the install policy gate.
    from specify_cli.bundler.models.manifest import ComponentRef
    from specify_cli.bundler.models.records import (
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
            {"id": "disc", "url": str(catalog), "priority": 1,
             "install_policy": "discovery-only"}
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )

    result = runner.invoke(app, ["bundle", "update", "demo", "--offline"])
    assert result.exit_code == 1
    assert "discovery-only" in result.output


def test_info_fails_loudly_when_manifest_unresolvable_offline(project: Path):
    # `info` must expand the real component set; if the manifest can't be
    # resolved (here: --offline against an https download_url), it should error
    # and exit non-zero rather than silently degrading to `provides` counts.
    catalog = project / "remote-catalog.json"
    entry = catalog_entry_dict(
        "demo-bundle", download_url="https://example.com/demo-bundle.zip"
    )
    write_catalog_file(catalog, {"demo-bundle": entry})
    added = runner.invoke(
        app, ["bundle", "catalog", "add", str(catalog), "--id", "remote"]
    )
    assert added.exit_code == 0, added.output

    result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--offline"])
    assert result.exit_code == 1
    assert "Network access disabled" in result.output


def test_search_json_offline(project: Path):
    catalog = project / "c.json"
    write_catalog_file(catalog, {"demo": catalog_entry_dict("demo")})
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {"id": "c", "url": str(catalog), "priority": 1,
             "install_policy": "install-allowed"}
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )
    result = runner.invoke(app, ["bundle", "search", "--offline", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload[0]["id"] == "demo"
    # Trust indicator is exposed on the discovery surface (FR-010 / FR-027).
    assert payload[0]["verified"] is True
    assert payload[0]["trust"] == "verified"


def test_search_text_shows_trust(project: Path):
    catalog = project / "c.json"
    write_catalog_file(
        catalog,
        {
            "verified-one": catalog_entry_dict("verified-one", verified=True),
            "community-one": catalog_entry_dict("community-one", verified=False),
        },
    )
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {"id": "c", "url": str(catalog), "priority": 1,
             "install_policy": "install-allowed"}
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )
    result = runner.invoke(app, ["bundle", "search", "--offline"])
    assert result.exit_code == 0, result.output
    assert "verified" in result.output
    assert "community" in result.output


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
