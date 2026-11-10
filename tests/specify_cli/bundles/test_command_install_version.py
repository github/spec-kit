"""End-to-end coverage for installing exact bundle catalog releases."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundles.records import load_records, records_path
from tests.specify_cli.bundles.helpers import (
    FakeInstaller,
    catalog_entry_dict,
    valid_manifest_dict,
    write_catalog_file,
)

runner = CliRunner()

BUNDLE_ID = "history"
CURRENT_URL = "https://example.com/history-1.2.0.yml"
HISTORICAL_URL = "https://example.com/history-1.1.0.yml"


def _manifest_bytes(version: str, bundle_id: str = BUNDLE_ID) -> bytes:
    data = valid_manifest_dict()
    data["bundle"]["id"] = bundle_id
    data["bundle"]["version"] = version
    return yaml.safe_dump(data).encode()


def _digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


class _Response(io.BytesIO):
    def __init__(self, data: bytes, url: str):
        super().__init__(data)
        self._url = url

    def geturl(self) -> str:
        return self._url


class _Downloads:
    """Serve bundle artifacts by URL and record every artifact download.

    Built-in catalog URLs get their packaged snapshot, so tests stay offline
    while ``bundle install`` keeps network access enabled.
    """

    def __init__(self, artifacts: dict[str, bytes]):
        from specify_cli.bundles.adapters import (
            _BUILTIN_PACKAGED_SNAPSHOTS,
            _BUILTIN_REPOSITORY_URLS,
            _load_packaged_catalog,
        )

        self.artifacts = artifacts
        self.catalogs = {
            repository_url: json.dumps(
                _load_packaged_catalog(_BUILTIN_PACKAGED_SNAPSHOTS[builtin])
            ).encode()
            for builtin, repository_url in _BUILTIN_REPOSITORY_URLS.items()
        }
        self.urls: list[str] = []

    def __call__(self, url, timeout=None, extra_headers=None, redirect_validator=None):
        if url in self.catalogs:
            return _Response(self.catalogs[url], url)
        self.urls.append(url)
        if url not in self.artifacts:
            raise AssertionError(f"Unexpected download: {url}")
        return _Response(self.artifacts[url], url)


@pytest.fixture
def installer(monkeypatch) -> FakeInstaller:
    fake = FakeInstaller()
    monkeypatch.setattr(
        "specify_cli.bundles.adapters.DefaultPrimitiveInstaller",
        lambda **kwargs: fake,
    )
    return fake


@pytest.fixture
def user_config(tmp_path: Path, monkeypatch) -> Path:
    """Keep the developer's real ~/.specify catalogs out of these tests."""
    config_dir = tmp_path / "user-config"
    config_dir.mkdir()
    monkeypatch.setattr(
        "specify_cli.bundles._commands._user_config_dir", lambda: config_dir
    )
    return config_dir


def _history_entry(
    *,
    current_body: bytes | None = None,
    historical_body: bytes | None = None,
    **historical_overrides,
) -> dict:
    current_body = current_body if current_body is not None else _manifest_bytes("1.2.0")
    historical_body = (
        historical_body if historical_body is not None else _manifest_bytes("1.1.0")
    )
    historical = {"download_url": HISTORICAL_URL, "sha256": _digest(historical_body)}
    historical.update(historical_overrides)
    return catalog_entry_dict(
        BUNDLE_ID,
        version="1.2.0",
        download_url=CURRENT_URL,
        sha256=_digest(current_body),
        releases={"1.1.0": historical},
    )


def _configure(
    config_dir: Path, sources: list[tuple[str, str, dict]], catalog_dir: Path
) -> None:
    catalogs = []
    for priority, (source_id, policy, entry) in enumerate(sources, start=1):
        catalog = write_catalog_file(
            catalog_dir / f"{source_id}.json", {entry["id"]: entry}
        )
        catalogs.append(
            {
                "id": source_id,
                "url": str(catalog),
                "priority": priority,
                "install_policy": policy,
            }
        )
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "bundle-catalogs.yml").write_text(
        yaml.safe_dump({"schema_version": "1.0", "catalogs": catalogs}),
        encoding="utf-8",
    )


def _serve(monkeypatch, artifacts: dict[str, bytes]) -> _Downloads:
    downloads = _Downloads(artifacts)
    monkeypatch.setattr("specify_cli.authentication.http.open_url", downloads)
    return downloads


def _default_artifacts() -> dict[str, bytes]:
    return {
        CURRENT_URL: _manifest_bytes("1.2.0"),
        HISTORICAL_URL: _manifest_bytes("1.1.0"),
    }


@pytest.mark.parametrize("command", ["install", "add"])
@pytest.mark.parametrize(
    ("requested", "advertised", "manifest"),
    [
        ("1.1.0", "1.1.0", "1.1.0"),
        ("v1.1.0", "1.1.0", "1.1.0"),
        ("v1.1.0", "v1.1.0", "1.1.0"),
        ("1.0.0-rc.1", "1.0.0-rc.1", "1.0.0-rc1"),
    ],
)
def test_version_installs_historical_release(
    project: Path, monkeypatch, installer, user_config, command, requested, advertised, manifest
):
    historical_body = _manifest_bytes(manifest)
    entry = _history_entry(historical_body=historical_body)
    entry["releases"] = {advertised: entry["releases"]["1.1.0"]}
    _configure(project / ".specify", [("history", "install-allowed", entry)], project)
    downloads = _serve(
        monkeypatch,
        {CURRENT_URL: _manifest_bytes("1.2.0"), HISTORICAL_URL: historical_body},
    )

    result = runner.invoke(app, ["bundle", command, BUNDLE_ID, "--version", requested])

    assert result.exit_code == 0, result.output
    assert downloads.urls == [HISTORICAL_URL]
    [record] = load_records(project)
    assert (record.bundle_id, record.version) == (BUNDLE_ID, manifest)
    assert installer.install_calls


def test_version_matching_current_installs_current_release(
    project: Path, monkeypatch, installer, user_config
):
    _configure(project / ".specify", [("history", "install-allowed", _history_entry())], project)
    downloads = _serve(monkeypatch, _default_artifacts())

    result = runner.invoke(app, ["bundle", "install", BUNDLE_ID, "--version", "1.2.0"])

    assert result.exit_code == 0, result.output
    assert downloads.urls == [CURRENT_URL]
    assert load_records(project)[0].version == "1.2.0"


def test_unknown_version_fails_without_download_or_record(
    project: Path, monkeypatch, installer, user_config
):
    _configure(project / ".specify", [("history", "install-allowed", _history_entry())], project)
    downloads = _serve(monkeypatch, _default_artifacts())

    result = runner.invoke(app, ["bundle", "install", BUNDLE_ID, "--version", "9.9.9"])

    assert result.exit_code == 1
    output = " ".join(result.output.split())
    assert "no release 9.9.9" in output
    assert "advertised: 1.2.0, 1.1.0" in output
    assert downloads.urls == []
    assert not records_path(project).exists()
    assert installer.install_calls == []


def test_unknown_version_outside_project_does_not_initialize(
    tmp_path: Path, monkeypatch, installer, user_config
):
    workdir = tmp_path / "outside-project"
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    _configure(user_config, [("history", "install-allowed", _history_entry())], tmp_path)
    downloads = _serve(monkeypatch, _default_artifacts())
    monkeypatch.setattr(
        "specify_cli.bundles.command_install._run_init",
        lambda *args, **kwargs: pytest.fail("project must not be initialized"),
    )

    result = runner.invoke(app, ["bundle", "install", BUNDLE_ID, "--version", "9.9.9"])

    assert result.exit_code == 1
    assert "no release 9.9.9" in " ".join(result.output.split())
    assert downloads.urls == []
    assert not (workdir / ".specify").exists()


def test_historical_digest_mismatch_fails_without_record(
    project: Path, monkeypatch, installer, user_config
):
    entry = _history_entry(sha256="0" * 64)
    _configure(project / ".specify", [("history", "install-allowed", entry)], project)
    downloads = _serve(monkeypatch, _default_artifacts())

    result = runner.invoke(app, ["bundle", "install", BUNDLE_ID, "--version", "1.1.0"])

    assert result.exit_code == 1
    assert "integrity" in result.output.lower()
    assert downloads.urls == [HISTORICAL_URL]
    assert not records_path(project).exists()
    assert installer.install_calls == []


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (_manifest_bytes("1.2.0"), "Downloaded bundle version mismatch"),
        (_manifest_bytes("1.1.0", bundle_id="other"), "Downloaded bundle id mismatch"),
    ],
)
def test_historical_manifest_identity_mismatch_fails_without_record(
    project: Path, monkeypatch, installer, user_config, body, message
):
    entry = _history_entry(historical_body=body)
    _configure(project / ".specify", [("history", "install-allowed", entry)], project)
    _serve(monkeypatch, {CURRENT_URL: _manifest_bytes("1.2.0"), HISTORICAL_URL: body})

    result = runner.invoke(app, ["bundle", "install", BUNDLE_ID, "--version", "1.1.0"])

    assert result.exit_code == 1
    assert message in " ".join(result.output.split())
    assert not records_path(project).exists()
    assert installer.install_calls == []


def test_discovery_only_winner_refuses_version_without_using_lower_source(
    project: Path, monkeypatch, installer, user_config
):
    lower = catalog_entry_dict(
        BUNDLE_ID,
        version="1.1.0",
        download_url=HISTORICAL_URL,
        sha256=_digest(_manifest_bytes("1.1.0")),
    )
    _configure(
        project / ".specify",
        [
            ("discovery", "discovery-only", _history_entry()),
            ("lower", "install-allowed", lower),
        ],
        project,
    )
    downloads = _serve(monkeypatch, _default_artifacts())

    result = runner.invoke(app, ["bundle", "install", BUNDLE_ID, "--version", "1.1.0"])

    assert result.exit_code == 1
    assert "discovery-only" in result.output
    assert downloads.urls == []
    assert not records_path(project).exists()


def test_discovery_only_winner_without_version_reports_missing_release(
    project: Path, monkeypatch, installer, user_config
):
    _configure(
        project / ".specify",
        [("discovery", "discovery-only", _history_entry())],
        project,
    )
    downloads = _serve(monkeypatch, _default_artifacts())

    result = runner.invoke(app, ["bundle", "install", BUNDLE_ID, "--version", "9.9.9"])

    assert result.exit_code == 1
    output = " ".join(result.output.split())
    assert "no release 9.9.9" in output
    assert "discovery-only" not in output
    assert downloads.urls == []


def test_version_for_already_installed_bundle_keeps_existing_rules(
    project: Path, monkeypatch, installer, user_config
):
    _configure(project / ".specify", [("history", "install-allowed", _history_entry())], project)
    _serve(monkeypatch, _default_artifacts())
    first = runner.invoke(app, ["bundle", "install", BUNDLE_ID])
    assert first.exit_code == 0, first.output
    original = load_records(project)

    older = runner.invoke(app, ["bundle", "install", BUNDLE_ID, "--version", "1.1.0"])
    same = runner.invoke(app, ["bundle", "install", BUNDLE_ID, "--version", "1.2.0"])

    assert older.exit_code == 1
    assert "already installed at version 1.2.0" in " ".join(older.output.split())
    assert same.exit_code == 0, same.output
    assert load_records(project) == original


@pytest.mark.parametrize(
    "url", ["http://example.com/history-1.1.0.yml", "file:///tmp/history-1.1.0.yml"]
)
def test_insecure_historical_download_url_is_rejected_before_download(
    project: Path, monkeypatch, installer, user_config, url
):
    entry = _history_entry(download_url=url)
    _configure(project / ".specify", [("history", "install-allowed", entry)], project)
    downloads = _serve(monkeypatch, _default_artifacts())

    result = runner.invoke(app, ["bundle", "install", BUNDLE_ID, "--version", "1.1.0"])

    assert result.exit_code == 1
    assert "release '1.1.0' has an invalid download_url" in " ".join(
        result.output.split()
    )
    assert downloads.urls == []
    assert not records_path(project).exists()


def test_update_moves_historical_install_to_current_release(
    project: Path, monkeypatch, installer, user_config
):
    _configure(project / ".specify", [("history", "install-allowed", _history_entry())], project)
    downloads = _serve(monkeypatch, _default_artifacts())
    installed = runner.invoke(app, ["bundle", "install", BUNDLE_ID, "--version", "1.1.0"])
    assert installed.exit_code == 0, installed.output

    updated = runner.invoke(app, ["bundle", "update", BUNDLE_ID])

    assert updated.exit_code == 0, updated.output
    assert downloads.urls == [HISTORICAL_URL, CURRENT_URL]
    assert load_records(project)[0].version == "1.2.0"


def test_init_with_bundle_installs_current_release_when_history_exists(
    project: Path, monkeypatch, installer, user_config
):
    _configure(project / ".specify", [("history", "install-allowed", _history_entry())], project)
    downloads = _serve(monkeypatch, _default_artifacts())

    result = runner.invoke(app, ["bundle", "init", BUNDLE_ID])

    assert result.exit_code == 0, result.output
    assert downloads.urls == [CURRENT_URL]
    assert load_records(project)[0].version == "1.2.0"
