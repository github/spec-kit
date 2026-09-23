from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundles import BundlerError
from specify_cli.bundles import sources as bundle_sources
from specify_cli.bundles.catalogs import CatalogEntry
from specify_cli.bundles.sources import (
    _download_manifest,
    _local_manifest_source,
    _require_https,
)
from tests.specify_cli.bundles.helpers import (
    catalog_entry_dict,
    valid_manifest_dict,
    write_manifest,
)

runner = CliRunner()

_MALFORMED_URLS = [
    "https://[::1",  # unclosed IPv6 bracket
    "https://[not-an-ip]/bundle.yml",
    "https://example.com:notaport/bundle.yml",
    "https://example.com:70000/bundle.yml",
]


class _Response(io.BytesIO):
    def __init__(self, body: bytes, url: str) -> None:
        super().__init__(body)
        self._url = url

    def geturl(self) -> str:
        return self._url


def _resolved_entry(**overrides) -> SimpleNamespace:
    entry = CatalogEntry.from_dict(
        catalog_entry_dict(
            "demo-bundle",
            download_url="https://example.com/demo-bundle.yml",
            **overrides,
        )
    )
    return SimpleNamespace(entry=entry)


def _patch_download(monkeypatch, body: bytes) -> None:
    def fake_open_url(
        url,
        timeout=10,
        extra_headers=None,
        redirect_validator=None,
    ):
        return _Response(body, url)

    monkeypatch.setattr("specify_cli.authentication.http.open_url", fake_open_url)


def test_local_source_none_for_non_path():
    assert _local_manifest_source("some-catalog-bundle-id") is None


def test_local_source_from_directory(tmp_path: Path):
    write_manifest(tmp_path, valid_manifest_dict())
    manifest = _local_manifest_source(str(tmp_path))
    assert manifest is not None
    assert manifest.bundle.id == "demo-bundle"


def test_local_source_from_bundle_yml(tmp_path: Path):
    path = write_manifest(tmp_path, valid_manifest_dict())
    manifest = _local_manifest_source(str(path))
    assert manifest is not None
    assert manifest.bundle.id == "demo-bundle"


def test_local_source_from_zip_artifact(tmp_path: Path):
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    write_manifest(bundle_dir, valid_manifest_dict())
    (bundle_dir / "README.md").write_text("# demo\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["bundle", "build", "--path", str(bundle_dir)])
    assert result.exit_code == 0, result.output
    artifact = next(bundle_dir.glob("*.zip"))

    manifest = _local_manifest_source(str(artifact))
    assert manifest is not None
    assert manifest.bundle.id == "demo-bundle"


def test_local_source_rejects_unknown_file(tmp_path: Path):
    weird = tmp_path / "thing.txt"
    weird.write_text("nope", encoding="utf-8")
    with pytest.raises(BundlerError, match="not a recognised bundle source"):
        _local_manifest_source(str(weird))


def test_local_source_zip_non_utf8_manifest_raises_bundler_error(tmp_path: Path):
    """Undecodable bundle.yml bytes inside a .zip must raise BundlerError.

    The manifest bytes are decoded as UTF-8 explicitly, matching
    ``yamlio.load_yaml``'s "Could not read ..." contract, instead of
    escaping as a raw ``UnicodeDecodeError``/``ReaderError`` traceback.
    """
    artifact = tmp_path / "demo.zip"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("bundle.yml", b"\xff\xfe bundle \xc3\x28\n")

    with pytest.raises(BundlerError, match="Could not read"):
        _local_manifest_source(str(artifact))


def test_local_source_zip_utf16_manifest_rejected_like_directory(tmp_path: Path):
    """A well-formed UTF-16 manifest must fail the same way in a .zip.

    ``yamlio.load_yaml`` decodes strictly as UTF-8, so a UTF-16 bundle.yml
    (the realistic PowerShell ``Out-File`` output) is rejected when read
    from a directory. Feeding the zip bytes straight to PyYAML would let
    its Reader honour the UTF-16 BOM and *accept* the same manifest,
    making zip and directory sources diverge.
    """
    artifact = tmp_path / "demo.zip"
    manifest_text = "bundle:\n  id: demo-bundle\n  version: 1.0.0\n"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("bundle.yml", manifest_text.encode("utf-16"))

    with pytest.raises(BundlerError, match="Could not read"):
        _local_manifest_source(str(artifact))


def test_download_manifest_rejects_file_url(tmp_path: Path):
    """A catalog ``file://`` download_url is rejected — catalog URLs are
    HTTPS-only, matching extensions/presets/workflows. Disk installs go through
    the positional path (see the local-source tests above), not download_url.
    """
    from types import SimpleNamespace

    from specify_cli.bundles.sources import _download_manifest

    manifest_path = write_manifest(tmp_path / "my bundles")
    resolved = SimpleNamespace(
        entry=SimpleNamespace(id="demo-bundle", download_url=manifest_path.as_uri())
    )

    with pytest.raises(BundlerError, match="bundle install"):
        _download_manifest(resolved, offline=True)


def test_download_manifest_rejects_bare_path(tmp_path: Path):
    """A bare filesystem path download_url is likewise rejected."""
    from types import SimpleNamespace

    from specify_cli.bundles.sources import _download_manifest

    manifest_path = write_manifest(tmp_path / "plain")
    resolved = SimpleNamespace(
        entry=SimpleNamespace(id="demo-bundle", download_url=str(manifest_path))
    )

    with pytest.raises(BundlerError, match="bundle install"):
        _download_manifest(resolved, offline=True)


def test_local_install_still_resolves_via_positional_path(tmp_path: Path):
    """The supported local route — a positional path, not a download_url —
    still resolves the manifest via _local_manifest_source."""
    manifest_path = write_manifest(tmp_path / "my bundles")
    manifest = _local_manifest_source(str(manifest_path))
    assert manifest is not None
    assert manifest.bundle.id == "demo-bundle"


def test_download_manifest_rejects_non_https_url_even_offline(tmp_path: Path):
    """A non-HTTPS download_url must report the HTTPS problem, not a misleading
    'Network access disabled', even under --offline (scheme is validated before
    the offline gate)."""
    from types import SimpleNamespace

    from specify_cli.bundles.sources import _download_manifest

    resolved = SimpleNamespace(
        entry=SimpleNamespace(
            id="demo-bundle", download_url="http://example.com/bundle.zip"
        )
    )
    with pytest.raises(BundlerError, match="HTTPS"):
        _download_manifest(resolved, offline=True)


def test_local_zip_uses_bounded_archive_open(tmp_path: Path):
    artifact = tmp_path / "too-many-entries.zip"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("bundle.yml", yaml.safe_dump(valid_manifest_dict()))
        for index in range(512):
            archive.writestr(f"assets/{index}.txt", "")

    with pytest.raises(BundlerError, match="too many entries"):
        _local_manifest_source(str(artifact))


def test_local_zip_wraps_malformed_manifest_yaml(tmp_path: Path):
    """A malformed bundle.yml inside a .zip must raise BundlerError.

    The zip branch parses YAML inline rather than through load_yaml(), so the
    raw yaml.YAMLError used to escape. It is neither a ValueError nor an
    OSError, so nothing upstream caught it.
    """
    artifact = tmp_path / "bad-manifest.zip"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("bundle.yml", "bundle: [unclosed\n  id: demo\n")

    with pytest.raises(BundlerError, match="Invalid YAML"):
        _local_manifest_source(str(artifact))


@pytest.mark.parametrize("url", _MALFORMED_URLS)
def test_download_manifest_rejects_malformed_url_cleanly(url):
    """A malformed download_url must raise BundlerError, not a raw ValueError.

    ``urlparse`` raises ``ValueError`` on a malformed authority (e.g. an
    unclosed IPv6 bracket). The bundle CLI commands only catch BundlerError, so
    a raw ValueError would escape as an uncaught traceback. Sibling of the
    guarded ``_validate_remote_url`` (adapters) and the merged #3576 fix.
    """
    resolved = SimpleNamespace(entry=SimpleNamespace(id="mybundle", download_url=url))
    with pytest.raises(BundlerError):
        _download_manifest(resolved, offline=True)


@pytest.mark.parametrize("url", _MALFORMED_URLS)
def test_require_https_rejects_malformed_url_cleanly(url):
    """``_require_https`` must also surface BundlerError on a malformed authority.

    On older Python versions the ValueError is raised at ``.hostname`` access
    rather than at ``urlparse``, so guarding both keeps the contract across the
    CI Python matrix.
    """
    with pytest.raises(BundlerError):
        _require_https("bundle 'x'", url)


def test_download_manifest_bounds_remote_artifact(monkeypatch):
    body = yaml.safe_dump(valid_manifest_dict()).encode()
    _patch_download(monkeypatch, body)
    monkeypatch.setattr(bundle_sources, "MAX_DOWNLOAD_BYTES", len(body) - 1)

    with pytest.raises(BundlerError, match="exceeds maximum size"):
        _download_manifest(_resolved_entry(), offline=False)


def test_download_manifest_accepts_matching_sha256(monkeypatch):
    body = yaml.safe_dump(valid_manifest_dict()).encode()
    digest = hashlib.sha256(body).hexdigest()
    _patch_download(monkeypatch, body)

    manifest = _download_manifest(
        _resolved_entry(sha256=f"sha256:{digest}"),
        offline=False,
    )

    assert manifest.bundle.id == "demo-bundle"


def test_download_manifest_accepts_legacy_entry_without_sha256(monkeypatch):
    body = yaml.safe_dump(valid_manifest_dict()).encode()
    _patch_download(monkeypatch, body)
    resolved = SimpleNamespace(
        entry=SimpleNamespace(
            id="demo-bundle",
            version="1.2.0",
            download_url="https://example.com/demo-bundle.yml",
        )
    )

    manifest = _download_manifest(resolved, offline=False)

    assert manifest.bundle.version == "1.2.0"


@pytest.mark.parametrize("declared", ["0" * 64, "not-a-sha256"])
def test_download_manifest_rejects_bad_sha256(monkeypatch, declared):
    body = yaml.safe_dump(valid_manifest_dict()).encode()
    _patch_download(monkeypatch, body)

    with pytest.raises(BundlerError, match="sha256|Integrity check"):
        _download_manifest(
            _resolved_entry(sha256=declared),
            offline=False,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("id", "other-bundle", "id mismatch"),
        ("version", "9.9.9", "version mismatch"),
    ],
)
def test_download_manifest_rejects_catalog_identity_mismatch(
    monkeypatch,
    field,
    value,
    message,
):
    data = valid_manifest_dict()
    data["bundle"][field] = value
    _patch_download(monkeypatch, yaml.safe_dump(data).encode())

    with pytest.raises(BundlerError, match=message):
        _download_manifest(_resolved_entry(), offline=False)


def test_download_manifest_rejects_invalid_structure(monkeypatch):
    data = valid_manifest_dict()
    data["bundle"]["author"] = ""
    _patch_download(monkeypatch, yaml.safe_dump(data).encode())

    with pytest.raises(BundlerError, match="invalid bundle manifest"):
        _download_manifest(_resolved_entry(), offline=False)
