from __future__ import annotations

import io  # noqa: F401
import json  # noqa: F401
from pathlib import Path
from unittest.mock import patch  # noqa: F401

import pytest
import yaml  # noqa: F401
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundles.packager import build_bundle  # noqa: F401
from tests.conftest import strip_ansi  # noqa: F401
from tests.specify_cli.bundles._command_helpers import (
    MARKUP_BUNDLE_ID,
    MARKUP_SOURCE_ID,
    configure_markup_catalog as _configure_markup_catalog,
    mock_manifest_download as _mock_manifest_download,
)
from tests.specify_cli.bundles.helpers import (
    catalog_entry_dict,
    valid_manifest_dict,
    write_catalog_file,
)

runner = CliRunner()


class FakeBundleResponse(io.BytesIO):
    def __init__(
        self,
        data: bytes,
        url: str = "https://api.github.com/repos/org/repo/releases/assets/99",
    ):
        super().__init__(data)
        self._url = url

    def geturl(self) -> str:
        return self._url


def _make_catalog_config(catalog_path: Path, project: Path) -> None:
    """Write a bundle-catalogs.yml pointing at *catalog_path* in *project*.

    Priority 0 keeps this test catalog ahead of the packaged first-party
    catalog, avoiding unrelated network resolution in info tests.
    """
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {
                "id": "test",
                "url": str(catalog_path),
                "priority": 0,
                "install_policy": "install-allowed",
            }
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )


def test_info_unknown_bundle_without_project_reports_not_found(
    tmp_path: Path, monkeypatch
):
    monkeypatch.chdir(tmp_path)  # no .specify/
    result = runner.invoke(app, ["bundle", "info", "does-not-exist", "--offline"])
    # Reaches catalog resolution (not the project gate) and reports a clean miss.
    assert result.exit_code == 1
    assert "Spec Kit project" not in result.output


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

    result = runner.invoke(
        app, ["bundle", "info", "demo-bundle", "--json", "--offline"]
    )
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


def test_info_versions_lists_history_without_downloading_manifest(project: Path):
    catalog = project / "history-catalog.json"
    entry = catalog_entry_dict(
        "history",
        version="1.2.0",
        releases={
            "1.1.0": {
                "download_url": "https://example.com/history-1.1.0.zip",
                "sha256": "a" * 64,
            }
        },
    )
    write_catalog_file(catalog, {"history": entry})
    added = runner.invoke(
        app, ["bundle", "catalog", "add", str(catalog), "--id", "history"]
    )
    assert added.exit_code == 0, added.output

    text = runner.invoke(app, ["bundle", "info", "history", "--versions", "--offline"])
    assert text.exit_code == 0, text.output
    assert "Catalog versions for history:" in text.output
    assert "1.2.0 (current)" in text.output
    assert "1.1.0" in text.output
    assert "1.1.0 (current)" not in text.output
    assert text.output.index("1.2.0") < text.output.index("1.1.0")
    assert "Source: history (install-allowed)" in text.output
    assert "Discovery only" not in text.output

    as_json = runner.invoke(
        app, ["bundle", "info", "history", "--versions", "--json", "--offline"]
    )
    assert as_json.exit_code == 0, as_json.output
    assert json.loads(as_json.output) == {
        "id": "history",
        "versions": ["1.2.0", "1.1.0"],
        "current": "1.2.0",
        "source": "history",
        "install_policy": "install-allowed",
    }


def _add_history_catalog(project: Path, releases, *, policy="install-allowed") -> None:
    catalog = project / "history-catalog.json"
    entry = catalog_entry_dict(
        "history",
        version="1.2.0",
        download_url="https://example.com/history-1.2.0.zip",
        releases=releases,
    )
    write_catalog_file(catalog, {"history": entry})
    added = runner.invoke(
        app,
        ["bundle", "catalog", "add", str(catalog), "--id", "history", "--policy", policy],
    )
    assert added.exit_code == 0, added.output


def test_info_versions_notes_discovery_only_winner(project: Path):
    _add_history_catalog(
        project,
        {"1.1.0": {"download_url": "https://example.com/history-1.1.0.zip", "sha256": "a" * 64}},
        policy="discovery-only",
    )

    text = runner.invoke(app, ["bundle", "info", "history", "--versions", "--offline"])
    as_json = runner.invoke(
        app, ["bundle", "info", "history", "--versions", "--json", "--offline"]
    )

    assert text.exit_code == 0, text.output
    assert "Source: history (discovery-only)" in text.output
    assert "Discovery only; catalog installation is disabled." in text.output
    assert as_json.exit_code == 0, as_json.output
    assert json.loads(as_json.output)["install_policy"] == "discovery-only"


@pytest.mark.parametrize("as_json", [False, True])
def test_info_versions_rejects_malformed_history_cleanly(project: Path, as_json: bool):
    _add_history_catalog(project, {"1.1.0": {"download_url": "https://example.com/x.zip"}})
    args = ["bundle", "info", "history", "--versions", "--offline"]
    if as_json:
        args.append("--json")

    result = runner.invoke(app, args)

    assert result.exit_code == 1
    assert "release '1.1.0' needs a SHA-256 digest" in " ".join(result.output.split())
    assert "Traceback" not in result.output
    assert isinstance(result.exception, SystemExit)


def test_info_without_versions_is_unchanged_by_history(project: Path, monkeypatch):
    bundle_dir = project / "history-bundle"
    manifest = valid_manifest_dict()
    manifest["bundle"]["id"] = "history"
    bundle_dir.mkdir()
    (bundle_dir / "bundle.yml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    _add_history_catalog(
        project,
        {"1.1.0": {"download_url": "https://example.com/history-1.1.0.zip", "sha256": "a" * 64}},
    )
    _mock_manifest_download(monkeypatch, bundle_dir / "bundle.yml")

    result = runner.invoke(app, ["bundle", "info", "history", "--offline"])

    assert result.exit_code == 0, result.output
    assert "Catalog versions for" not in result.output
    assert "preset-a v2.0.0" in result.output


def test_info_escapes_catalog_markup(project: Path, monkeypatch):
    entry = _configure_markup_catalog(project)
    bundle_dir = project / "markup-bundle"
    bundle_dir.mkdir()
    manifest_data = valid_manifest_dict()
    manifest_data["bundle"]["id"] = MARKUP_BUNDLE_ID
    manifest_data["integration"] = {"id": "[conceal]markup-integration[/conceal]"}
    manifest_path = bundle_dir / "bundle.yml"
    manifest_path.write_text(yaml.safe_dump(manifest_data), encoding="utf-8")
    _mock_manifest_download(monkeypatch, manifest_path)
    monkeypatch.setattr(
        "specify_cli.bundles.command_info._manifest_component_view",
        lambda manifest: [
            {
                "kind": "extensions",
                "id": "[reverse]markup-component[/reverse]",
                "version": "[strike]2.0.0[/strike]",
            }
        ],
    )
    monkeypatch.setattr(
        "specify_cli.bundles.command_info._bundle_overlaps",
        lambda project_root, manifest, *, offline: ["[blink]markup-overlap[/blink]"],
    )

    result = runner.invoke(
        app,
        ["bundle", "info", MARKUP_BUNDLE_ID, "--offline"],
    )

    assert result.exit_code == 0, result.output
    output = " ".join(strip_ansi(result.output).split())
    for value in (
        entry["id"],
        entry["name"],
        entry["version"],
        entry["role"],
        entry["description"],
        entry["author"],
        entry["license"],
        entry["requires"]["speckit_version"],
        MARKUP_SOURCE_ID,
        "[conceal]markup-integration[/conceal]",
        "[reverse]markup-component[/reverse]",
        "[strike]2.0.0[/strike]",
        "[blink]markup-overlap[/blink]",
    ):
        assert value in output


def test_info_escapes_catalog_provides_fallback_markup(project: Path, monkeypatch):
    markup_count = "[bold]markup-count[/bold]"
    _configure_markup_catalog(
        project,
        provides={"extensions": markup_count},
    )
    bundle_dir = project / "markup-bundle"
    bundle_dir.mkdir()
    manifest_data = valid_manifest_dict(provides={})
    manifest_data["bundle"]["id"] = MARKUP_BUNDLE_ID
    manifest_path = bundle_dir / "bundle.yml"
    manifest_path.write_text(yaml.safe_dump(manifest_data), encoding="utf-8")
    _mock_manifest_download(monkeypatch, manifest_path)

    result = runner.invoke(
        app,
        ["bundle", "info", MARKUP_BUNDLE_ID, "--offline"],
    )

    assert result.exit_code == 0, result.output
    assert markup_count in strip_ansi(result.output)


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
    _mock_manifest_download(monkeypatch, bundle_dir / "bundle.yml")
    result = runner.invoke(
        app, ["bundle", "info", "demo-bundle", "--json", "--offline"]
    )
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
        {
            "demo-bundle": catalog_entry_dict(
                "demo-bundle", download_url="https://example.com/demo-bundle.zip"
            )
        },
    )
    added = runner.invoke(
        app, ["bundle", "catalog", "add", str(catalog), "--id", "local"]
    )
    assert added.exit_code == 0, added.output
    _mock_manifest_download(monkeypatch, artifact)
    result = runner.invoke(
        app, ["bundle", "info", "demo-bundle", "--json", "--offline"]
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    components = {(c["kind"], c["id"]) for c in payload["components"]}
    assert ("extensions", "ext-a") in components


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
                json.dumps(
                    {"assets": [{"name": "bundle.yml", "url": api_asset_url}]}
                ).encode(),
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


def test_bundle_info_rejects_utf16_remote_manifest_like_local_sources(project: Path):
    """A downloaded (non-zip) bundle.yml must be decoded strictly as UTF-8.

    ``yamlio.load_yaml`` decodes local ``bundle.yml`` sources strictly as
    UTF-8, so a well-formed UTF-16 manifest (a realistic PowerShell
    ``Out-File`` output) is rejected. Feeding the downloaded bytes straight
    to ``yaml.safe_load(io.BytesIO(raw))`` let PyYAML's Reader honour the
    UTF-16 BOM and silently *accept* the same manifest instead, diverging
    from local/zip sources (the zip branch of this same download path was
    already fixed for the identical bug).
    """
    api_asset_url = "https://api.github.com/repos/org/repo/releases/assets/99"
    manifest_yaml_utf16 = yaml.safe_dump(valid_manifest_dict()).encode("utf-16")

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        return FakeBundleResponse(manifest_yaml_utf16, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=api_asset_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    assert result.exit_code == 1
    output_flat = " ".join(result.output.split())
    assert "could not be read" in output_flat.lower()


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
                json.dumps(
                    {"assets": [{"name": "bundle.zip", "url": api_asset_url}]}
                ).encode(),
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


def test_bundle_info_github_release_url_resolution_failure_falls_back_and_errors(
    project: Path,
):
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
                json.dumps(
                    {"assets": [{"name": "bundle.yml", "url": api_asset_url}]}
                ).encode(),
                url=url,
            )
        return FakeBundleResponse(manifest_yaml, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=browser_url)},
    )
    _make_catalog_config(catalog, project)

    with (
        patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url),
        patch(
            "specify_cli.authentication.http.github_provider_hosts",
            return_value=(ghes_host,),
        ),
    ):
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


def test_bundle_info_resolves_ghecom_browser_release_url_zip(project: Path):
    """bundle info resolves a GHE.com release ZIP through its API subdomain."""
    import zipfile

    web_host = "msft.ghe.com"
    api_host = f"api.{web_host}"
    browser_url = f"https://{web_host}/org/repo/releases/download/v2.0/bundle.zip"
    api_asset_url = f"https://{api_host}/repos/org/repo/releases/assets/42"

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("bundle.yml", yaml.safe_dump(valid_manifest_dict()))
    zip_bytes = archive.getvalue()
    captured = []

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        captured.append((url, extra_headers))
        if "releases/tags/" in url:
            return FakeBundleResponse(
                json.dumps(
                    {"assets": [{"name": "bundle.zip", "url": api_asset_url}]}
                ).encode(),
                url=url,
            )
        return FakeBundleResponse(zip_bytes, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=browser_url)},
    )
    _make_catalog_config(catalog, project)

    with (
        patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url),
        patch(
            "specify_cli.authentication.http.github_provider_hosts",
            return_value=(web_host, api_host),
        ),
    ):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    assert result.exit_code == 0, result.output

    tag_calls = [url for url, _ in captured if "releases/tags/" in url]
    assert tag_calls == [f"https://{api_host}/repos/org/repo/releases/tags/v2.0"]

    asset_calls = [(url, headers) for url, headers in captured if url == api_asset_url]
    assert asset_calls == [(api_asset_url, {"Accept": "application/octet-stream"})]

    payload = json.loads(result.output)
    assert payload["id"] == "demo-bundle"


def test_bundle_download_rejects_oversized_response(project: Path, monkeypatch):
    """Bundle download rejects responses exceeding MAX_DOWNLOAD_BYTES."""
    # Monkeypatch to a small limit so the test is fast and low-memory.
    monkeypatch.setattr("specify_cli.bundles.sources.MAX_DOWNLOAD_BYTES", 100)

    api_asset_url = "https://api.github.com/repos/org/repo/releases/assets/99"

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        # Return a response that exceeds 100 bytes.
        return FakeBundleResponse(b"x" * 200, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=api_asset_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    # Must fail with a size-limit error, not an unhandled traceback.
    assert result.exit_code == 1
    # Rich may wrap the message across lines; normalise whitespace before checking.
    output_flat = " ".join(result.output.split())
    assert "exceeds maximum size of 100 bytes" in output_flat
