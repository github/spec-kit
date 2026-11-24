"""Unit tests for the bundler YAML I/O helpers."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Self

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundler import BundlerError
from specify_cli.bundles import adapters
from specify_cli.bundles.catalogs import CatalogSource, InstallPolicy
from specify_cli.bundles.project import active_integration
from specify_cli.bundles.records import load_records
from specify_cli.bundles.yamlio import dump_yaml, load_json, load_yaml, loads_json


def test_dump_yaml_preserves_unicode(tmp_path: Path):
    # dump_yaml must write literal UTF-8, not \xNN / \uXXXX escapes, so bundle
    # config stays human-readable — matching _utils.dump_frontmatter and the
    # extensions/presets config writers (all allow_unicode=True).
    path = tmp_path / "f.yml"
    data = {"note": "café-münchen", "url": "https://例え.example"}
    dump_yaml(path, data)
    raw = path.read_text(encoding="utf-8")
    assert "café-münchen" in raw
    assert "例え" in raw
    assert "\\x" not in raw and "\\u" not in raw


def test_dump_yaml_round_trips_unicode(tmp_path: Path):
    path = tmp_path / "f.yml"
    data = {"note": "café", "city": "münchen"}
    dump_yaml(path, data)
    assert load_yaml(path) == data


def test_load_yaml_non_utf8_raises_bundler_error(tmp_path: Path):
    """A non-UTF-8 file must degrade into BundlerError, per this module's
    documented contract. UnicodeDecodeError is a ValueError, not an OSError, so
    it previously escaped as a raw traceback. UTF-16 is the realistic case:
    PowerShell 5.1's `Out-File`/`>` default to it."""
    path = tmp_path / "bundle-catalogs.yml"
    path.write_bytes('catalogs: []\n'.encode("utf-16"))
    with pytest.raises(BundlerError, match="Could not read"):
        load_yaml(path)


def test_load_json_non_utf8_raises_bundler_error(tmp_path: Path):
    """Same for the JSON reader: json.JSONDecodeError is a *sibling* of
    UnicodeDecodeError, so it does not cover a decode failure."""
    path = tmp_path / "records.json"
    path.write_bytes('{"bundles": []}'.encode("utf-16"))
    with pytest.raises(BundlerError, match="Could not read"):
        load_json(path)


def test_load_json_malformed_still_reports_invalid_json(tmp_path: Path):
    """Clause order regression guard: decodable-but-malformed JSON must keep the
    more specific 'Invalid JSON' message rather than the read-error one."""
    path = tmp_path / "records.json"
    path.write_text('{"bundles": [', encoding="utf-8")
    with pytest.raises(BundlerError, match="Invalid JSON"):
        load_json(path)


def test_load_json_accepts_utf8_bom_and_preserves_unicode(tmp_path: Path):
    path = tmp_path / "records.json"
    expected = {"note": "café 🎯", "inner_bom": "\ufeffkeep", "bundles": []}
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps(expected, ensure_ascii=False).encode("utf-8"))
    assert load_json(path) == expected


def test_loads_json_accepts_utf8_bom_and_preserves_unicode():
    expected = {"schema_version": "1.0", "note": "café 🎯", "inner_bom": "\ufeffkeep"}
    raw = "\ufeff" + json.dumps(expected, ensure_ascii=False)
    assert loads_json(raw, origin="catalog.json") == expected


def test_load_json_and_loads_json_reject_double_utf8_bom(tmp_path: Path):
    path = tmp_path / "double-bom.json"
    path.write_bytes(b"\xef\xbb\xbf\xef\xbb\xbf{}")
    with pytest.raises(BundlerError, match="Invalid JSON"):
        load_json(path)
    with pytest.raises(BundlerError, match="Invalid JSON"):
        loads_json("\ufeff\ufeff{}", origin="double-bom.json")


def test_loads_json_rejects_duplicate_keys_after_utf8_bom():
    with pytest.raises(BundlerError, match="duplicate key 'a'"):
        loads_json('\ufeff{"a": 1, "a": 2}', origin="catalog.json")


def test_load_json_and_loads_json_reject_malformed_json_after_utf8_bom(tmp_path: Path):
    path = tmp_path / "bad-bom.json"
    path.write_bytes(b'\xef\xbb\xbf{"bundles": [')
    with pytest.raises(BundlerError, match="Invalid JSON"):
        load_json(path)
    with pytest.raises(BundlerError, match="Invalid JSON"):
        loads_json('\ufeff{"bundles": [', origin="bad-bom.json")


@pytest.mark.parametrize(
    ("raw_bytes", "raw_text"),
    [
        pytest.param(b"\xef\xbb\xbf", "\ufeff", id="bom-only"),
        pytest.param(b" \xef\xbb\xbf{}", " \ufeff{}", id="non-leading-bom"),
    ],
)
def test_load_json_and_loads_json_reject_empty_or_non_leading_bom(
    tmp_path: Path, raw_bytes: bytes, raw_text: str
):
    path = tmp_path / "edge-bom.json"
    path.write_bytes(raw_bytes)
    with pytest.raises(BundlerError, match="Invalid JSON"):
        load_json(path)
    with pytest.raises(BundlerError, match="Invalid JSON"):
        loads_json(raw_text, origin="edge-bom.json")


class _FakeBomResponse:
    def __init__(self, body: bytes, final_url: str) -> None:
        self._body = body
        self._offset = 0
        self._final_url = final_url

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> bool:
        return False

    def geturl(self) -> str:
        return self._final_url

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self._body) - self._offset
        start = self._offset
        self._offset = min(len(self._body), self._offset + size)
        return self._body[start:self._offset]


def test_bom_catalog_works_across_local_file_url_and_https_fetchers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    payload = {"schema_version": "1.0", "bundles": {}}
    bom_bytes = b"\xef\xbb\xbf" + json.dumps(payload).encode("utf-8")
    catalog_file = tmp_path / "catalog.json"
    catalog_file.write_bytes(bom_bytes)

    def _source(url: str) -> CatalogSource:
        return CatalogSource(
            id="team",
            url=url,
            priority=10,
            install_policy=InstallPolicy.INSTALL_ALLOWED,
        )

    offline_fetcher = adapters.make_catalog_fetcher(allow_network=False)
    assert offline_fetcher(_source(str(catalog_file))) == payload
    assert offline_fetcher(_source(catalog_file.as_uri())) == payload

    monkeypatch.setattr(
        "specify_cli.authentication.http.open_url",
        lambda url, **_kwargs: _FakeBomResponse(bom_bytes, url),
    )
    online_fetcher = adapters.make_catalog_fetcher(allow_network=True)
    assert online_fetcher(_source("https://example.com/catalog.json")) == payload


def test_bom_bundle_records_and_integration_json_load_cleanly(tmp_path: Path):
    project = tmp_path / "proj"
    specify = project / ".specify"
    specify.mkdir(parents=True)
    records_payload = {
        "schema_version": "1.0",
        "bundles": [
            {
                "bundle_id": "demo",
                "version": "1.0.0",
                "installed_at": "2026-11-24T00:00:00Z",
                "contributed_components": [],
                "required_components": [],
            }
        ],
    }
    (specify / "bundle-records.json").write_bytes(
        b"\xef\xbb\xbf" + json.dumps(records_payload).encode("utf-8")
    )
    (specify / "integration.json").write_bytes(
        b"\xef\xbb\xbf" + json.dumps({"default_integration": "claude"}).encode("utf-8")
    )

    records = load_records(project)
    assert len(records) == 1
    assert records[0].bundle_id == "demo"
    assert active_integration(project) == "claude"


@pytest.mark.skipif(
    os.name != "nt" or shutil.which("powershell.exe") is None,
    reason="Windows PowerShell 5.1 BOM regression requires Windows powershell.exe",
)
def test_powershell_51_utf8_catalog_works_end_to_end_in_bundle_search(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    catalog_file = project / "team-catalog.json"
    ps_script = (
        "$obj = @{ schema_version = '1.0'; bundles = @{ demo = @{ "
        "id = 'demo'; name = 'Demo Bundle'; version = '1.0.0'; role = 'dev'; "
        "description = 'Authored in PowerShell 5.1'; author = 'Team'; "
        "license = 'MIT'; download_url = 'https://example.com/demo.zip'; "
        "requires = @{ speckit_version = '>=0.1.0' } } } }; "
        f"$obj | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath '{catalog_file}' -Encoding UTF8"
    )
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", ps_script],
        check=True,
        capture_output=True,
    )
    assert catalog_file.read_bytes().startswith(b"\xef\xbb\xbf")

    monkeypatch.chdir(project)
    monkeypatch.delenv("SPECIFY_INIT_DIR", raising=False)
    runner = CliRunner()
    added = runner.invoke(app, ["bundle", "catalog", "add", str(catalog_file)])
    assert added.exit_code == 0, added.output

    searched = runner.invoke(app, ["bundle", "search", "demo", "--offline", "--json"])
    assert searched.exit_code == 0, searched.output
    results = json.loads(searched.stdout)
    assert any(item["id"] == "demo" and item["name"] == "Demo Bundle" for item in results)
