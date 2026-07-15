"""Contract test for the `specify bundle` CLI surface (Typer integration).

Exercises the wired commands end-to-end via CliRunner against a temp project,
asserting exit codes and the cross-cutting error guarantees from
contracts/cli-commands.md (offline, discovery-only refusal, not-a-project error).
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

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


def test_remove_reports_clean_error_when_primitive_raises_raw_exception(
    project: Path,
):
    """A raw exception from a primitive installer (e.g. an OSError from an
    unreadable workflow registry surfacing through _WorkflowKindManager's
    fail-closed construction) must not propagate uncaught through
    `specify bundle remove` -- the command only catches BundlerError, so
    without a conversion at the remove_bundle boundary this would exit
    with an unhandled exception and empty/raw output instead of a clean,
    actionable message, and no removal side effects should occur either."""
    from specify_cli.bundler.models.manifest import BundleManifest
    from specify_cli.bundler.models.records import load_records
    from specify_cli.bundler.services.adapters import DefaultPrimitiveInstaller
    from specify_cli.bundler.services.installer import install_bundle
    from specify_cli.bundler.services.resolver import resolve_install_plan
    from tests.bundler_helpers import FakeInstaller

    manifest = BundleManifest.from_dict(valid_manifest_dict())
    plan = resolve_install_plan(
        manifest, speckit_version="0.11.2", active_integration="copilot"
    )
    install_bundle(project, plan, FakeInstaller(), manifest=manifest)

    def boom(self, project_root, component):
        raise OSError("workflow registry unreadable")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(DefaultPrimitiveInstaller, "is_installed", boom)
        result = runner.invoke(app, ["bundle", "remove", "demo-bundle"])

    assert result.exit_code != 0
    assert result.output.strip() != ""
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert {r.bundle_id for r in load_records(project)} == {"demo-bundle"}


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


def _mock_manifest_download(monkeypatch, source_path: Path) -> None:
    """Mock the HTTPS manifest fetch to return a locally-authored manifest.

    Catalog ``download_url``s are HTTPS-only, so ``info`` tests can no longer
    point one at a local file. Patch ``_download_manifest`` to return the
    manifest parsed from *source_path* (a bundle.yml or a .zip artifact),
    exercising ``info``'s expansion without a network call.
    """
    from specify_cli.commands.bundle import _local_manifest_source

    monkeypatch.setattr(
        "specify_cli.commands.bundle._download_manifest",
        lambda resolved, *, offline: _local_manifest_source(str(source_path)),
    )


def test_info_expands_full_component_set(project: Path, monkeypatch):
    bundle_dir = project / "src-bundle"
    bundle_dir.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    catalog = project / "local-catalog.json"
    entry = catalog_entry_dict(
        "demo-bundle", download_url="https://example.com/demo-bundle.zip"
    )
    write_catalog_file(catalog, {"demo-bundle": entry})
    added = runner.invoke(
        app, ["bundle", "catalog", "add", str(catalog), "--id", "local"]
    )
    assert added.exit_code == 0, added.output
    _mock_manifest_download(monkeypatch, bundle_dir / "bundle.yml")

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


def test_info_expands_discovery_only_bundle(project: Path, monkeypatch):
    # Discovery-only bundles must still be fully inspectable via `info`;
    # only `install` is refused for them.
    bundle_dir = project / "disc-bundle"
    bundle_dir.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    catalog = project / "disc-catalog.json"
    entry = catalog_entry_dict(
        "demo-bundle", download_url="https://example.com/demo-bundle.zip"
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
    _mock_manifest_download(monkeypatch, bundle_dir / "bundle.yml")
    result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json", "--offline"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    components = {(c["kind"], c["id"]) for c in payload["components"]}
    assert ("extensions", "ext-a") in components


def test_info_expands_zip_sourced_bundle(project: Path, monkeypatch):
    # A .zip artifact is extracted to read bundle.yml; info expands it. (The
    # download itself is HTTPS-only now and mocked here — see contract note.)
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
        {"demo-bundle": catalog_entry_dict(
            "demo-bundle", download_url="https://example.com/demo-bundle.zip"
        )},
    )
    added = runner.invoke(
        app, ["bundle", "catalog", "add", str(catalog), "--id", "local"]
    )
    assert added.exit_code == 0, added.output
    _mock_manifest_download(monkeypatch, artifact)
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


# ===== Private GitHub release asset URL resolution =====


class FakeBundleResponse(io.BytesIO):
    """Minimal context-manager response stub for open_url fakes."""

    def __init__(self, data: bytes, url: str = "https://api.github.com/repos/org/repo/releases/assets/99"):
        super().__init__(data)
        self._url = url

    def geturl(self) -> str:
        return self._url


def _make_catalog_config(catalog_path: Path, project: Path) -> None:
    """Write a bundle-catalogs.yml pointing at *catalog_path* in *project*."""
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {
                "id": "test",
                "url": str(catalog_path),
                "priority": 1,
                "install_policy": "install-allowed",
            }
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )


def test_bundle_info_resolves_github_browser_release_url(project: Path):
    """bundle info resolves a private-repo browser release URL via the GitHub API."""
    browser_url = "https://github.com/org/repo/releases/download/v1.0/bundle.yml"
    api_asset_url = "https://api.github.com/repos/org/repo/releases/assets/99"

    captured = []
    manifest_yaml = yaml.safe_dump(valid_manifest_dict()).encode()

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        captured.append((url, extra_headers))
        if "releases/tags/" in url:
            # GitHub API release-tags lookup — return asset list
            return FakeBundleResponse(
                json.dumps({
                    "assets": [{"name": "bundle.yml", "url": api_asset_url}]
                }).encode(),
                url=url,
            )
        # Actual asset download
        return FakeBundleResponse(manifest_yaml, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=browser_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    assert result.exit_code == 0, result.output

    # The browser release URL must have been resolved via the GitHub tags API
    tag_calls = [url for url, _ in captured if "releases/tags/" in url]
    assert len(tag_calls) == 1, f"Expected exactly one tags API call; got {captured}"
    assert "releases/tags/v1.0" in tag_calls[0]

    # The actual download must use the resolved API asset URL with octet-stream
    asset_calls = [(url, h) for url, h in captured if "releases/assets/" in url]
    assert len(asset_calls) == 1
    assert asset_calls[0][0] == api_asset_url
    assert asset_calls[0][1] == {"Accept": "application/octet-stream"}


def test_bundle_info_passes_through_api_asset_url(project: Path):
    """bundle info passes a direct GitHub API asset URL through with octet-stream."""
    api_asset_url = "https://api.github.com/repos/org/repo/releases/assets/77"

    captured = []
    manifest_yaml = yaml.safe_dump(valid_manifest_dict()).encode()

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        captured.append((url, extra_headers))
        return FakeBundleResponse(manifest_yaml, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=api_asset_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    assert result.exit_code == 0, result.output

    # No tags API call — URL was already a REST asset URL
    tag_calls = [url for url, _ in captured if "releases/tags/" in url]
    assert len(tag_calls) == 0

    # Exactly one download call to the asset URL with octet-stream
    asset_calls = [(url, h) for url, h in captured if "releases/assets/" in url]
    assert len(asset_calls) == 1
    assert asset_calls[0][0] == api_asset_url
    assert asset_calls[0][1] == {"Accept": "application/octet-stream"}


def test_bundle_info_resolves_github_browser_release_url_zip(project: Path):
    """bundle info resolves a browser release URL for a .zip artifact and extracts bundle.yml."""
    import io
    import zipfile

    browser_url = "https://github.com/org/repo/releases/download/v2.0/bundle.zip"
    api_asset_url = "https://api.github.com/repos/org/repo/releases/assets/88"

    # Build a minimal in-memory ZIP containing bundle.yml
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("bundle.yml", yaml.safe_dump(valid_manifest_dict()))
    zip_bytes = buf.getvalue()

    captured = []

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        captured.append((url, extra_headers))
        if "releases/tags/" in url:
            return FakeBundleResponse(
                json.dumps({
                    "assets": [{"name": "bundle.zip", "url": api_asset_url}]
                }).encode(),
                url=url,
            )
        return FakeBundleResponse(zip_bytes, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=browser_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    assert result.exit_code == 0, result.output

    # tags API lookup must have fired
    tag_calls = [url for url, _ in captured if "releases/tags/" in url]
    assert len(tag_calls) == 1
    assert "releases/tags/v2.0" in tag_calls[0]

    # Asset download uses the resolved API URL with octet-stream
    asset_calls = [(url, h) for url, h in captured if "releases/assets/" in url]
    assert len(asset_calls) == 1
    assert asset_calls[0][0] == api_asset_url
    assert asset_calls[0][1] == {"Accept": "application/octet-stream"}

    # Manifest was successfully parsed from the ZIP
    payload = json.loads(result.output)
    assert payload["id"] == "demo-bundle"


def test_bundle_info_api_asset_url_zip_detected_by_magic_bytes(project: Path):
    """bundle info correctly handles a direct API asset URL that serves ZIP bytes."""
    import io
    import zipfile

    api_asset_url = "https://api.github.com/repos/org/repo/releases/assets/55"

    # Build a minimal in-memory ZIP containing bundle.yml
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("bundle.yml", yaml.safe_dump(valid_manifest_dict()))
    zip_bytes = buf.getvalue()

    captured = []

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        captured.append((url, extra_headers))
        return FakeBundleResponse(zip_bytes, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=api_asset_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    assert result.exit_code == 0, result.output

    # No tags API call — URL was already a REST asset URL
    tag_calls = [url for url, _ in captured if "releases/tags/" in url]
    assert len(tag_calls) == 0

    # Download used octet-stream header
    asset_calls = [(url, h) for url, h in captured if "releases/assets/" in url]
    assert len(asset_calls) == 1
    assert asset_calls[0][1] == {"Accept": "application/octet-stream"}

    # ZIP bytes were detected by magic and bundle.yml extracted correctly
    payload = json.loads(result.output)
    assert payload["id"] == "demo-bundle"


def test_bundle_info_github_release_url_resolution_failure_falls_back_and_errors(project: Path):
    """When the GitHub tags API lookup finds no matching asset, fall back to the
    original browser URL and surface a meaningful error (not a raw traceback)."""
    browser_url = "https://github.com/org/repo/releases/download/v3.0/bundle.yml"

    captured = []

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        captured.append((url, extra_headers))
        if "releases/tags/" in url:
            # Tags API responds but the asset list doesn't include our file
            return FakeBundleResponse(
                json.dumps({"assets": []}).encode(),
                url=url,
            )
        # Fallback download: GitHub serves HTML (SSO redirect) instead of YAML
        return FakeBundleResponse(b"<html>SSO login required</html>", url=url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=browser_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    # Must exit non-zero — the HTML body is not a valid bundle manifest
    assert result.exit_code == 1

    # The tags API lookup must have fired
    tag_calls = [url for url, _ in captured if "releases/tags/" in url]
    assert len(tag_calls) == 1

    # The fallback download should use the original browser URL (no octet-stream)
    fallback_calls = [(url, h) for url, h in captured if url == browser_url]
    assert len(fallback_calls) == 1
    assert fallback_calls[0][1] is None  # no Accept header on the original URL

    # Error output must be actionable (not a raw traceback)
    assert "Error:" in result.output


def test_bundle_info_resolves_ghes_browser_release_url(project: Path):
    """bundle info resolves a GHES private-repo browser release URL via /api/v3."""
    ghes_host = "ghes.example"
    browser_url = f"https://{ghes_host}/org/repo/releases/download/v1.0/bundle.yml"
    api_asset_url = f"https://{ghes_host}/api/v3/repos/org/repo/releases/assets/42"

    captured = []
    manifest_yaml = yaml.safe_dump(valid_manifest_dict()).encode()

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        captured.append((url, extra_headers))
        if "/api/v3/repos/" in url and "releases/tags/" in url:
            return FakeBundleResponse(
                json.dumps({
                    "assets": [{"name": "bundle.yml", "url": api_asset_url}]
                }).encode(),
                url=url,
            )
        return FakeBundleResponse(manifest_yaml, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=browser_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url), \
         patch("specify_cli.authentication.http.github_provider_hosts", return_value=(ghes_host,)):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    assert result.exit_code == 0, result.output

    # The GHES /api/v3 tags lookup must have fired
    tag_calls = [url for url, _ in captured if "releases/tags/" in url]
    assert len(tag_calls) == 1
    assert f"{ghes_host}/api/v3/repos/org/repo/releases/tags/v1.0" in tag_calls[0]

    # Asset download must use the resolved GHES API URL with octet-stream
    asset_calls = [(url, h) for url, h in captured if "releases/assets/" in url]
    assert len(asset_calls) == 1
    assert asset_calls[0][0] == api_asset_url
    assert asset_calls[0][1] == {"Accept": "application/octet-stream"}

    payload = json.loads(result.output)
    assert payload["id"] == "demo-bundle"
