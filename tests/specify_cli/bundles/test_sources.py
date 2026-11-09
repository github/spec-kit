from __future__ import annotations

import hashlib
import io
import zipfile
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundles import BundlerError
from specify_cli.bundles import sources as bundle_sources
from specify_cli.bundles.catalog_stack import CatalogStack
from specify_cli.bundles.catalogs import (
    CatalogEntry,
    CatalogSource,
    InstallPolicy,
    Scope,
)
from specify_cli.bundles.expansion import expand_manifest
from specify_cli.bundles.manifest import BundleManifest, BundleRef
from specify_cli.bundles.sources import (
    CatalogBundleLoader,
    _download_manifest,
    _local_manifest_source,
    _require_https,
)
from tests.specify_cli.bundles.helpers import (
    catalog_entry_dict,
    catalog_payload,
    reference_manifest_dict,
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


def _catalog_source(
    source_id: str,
    priority: int,
    policy: InstallPolicy = InstallPolicy.INSTALL_ALLOWED,
) -> CatalogSource:
    return CatalogSource(
        id=source_id,
        url=f"builtin://{source_id}",
        priority=priority,
        install_policy=policy,
        scope=Scope.PROJECT,
    )


def _catalog_stack(sources, payloads) -> CatalogStack:
    return CatalogStack(sources, lambda source: payloads[source.id])


def _manifest(bundle_id: str, version: str = "1.2.0"):
    data = valid_manifest_dict()
    data["bundle"]["id"] = bundle_id
    data["bundle"]["version"] = version
    return BundleManifest.from_dict(data)


def _resolved_catalog_entry(
    bundle_id: str = "bugfix",
    version: str = "1.2.0",
    **overrides,
):
    return catalog_entry_dict(
        bundle_id,
        version=version,
        download_url=f"https://example.com/{bundle_id}-{version}.zip",
        **overrides,
    )


def test_catalog_loader_resolves_pinned_release_and_returns_source_policy():
    stack = _catalog_stack(
        [_catalog_source("default", 1)],
        {"default": catalog_payload({"bugfix": _resolved_catalog_entry()})},
    )
    loader = CatalogBundleLoader(
        stack,
        offline=True,
        download=lambda resolved, *, offline: _manifest(
            resolved.entry.id, resolved.entry.version
        ),
    )

    loaded = loader.load(BundleRef("bugfix", "1.2.0"), ("team",))

    assert loaded.manifest.bundle.id == "bugfix"
    assert loaded.manifest.bundle.version == "1.2.0"
    assert loaded.source_id == "default"
    assert loaded.install_allowed is True


def test_catalog_loader_omitted_source_uses_effective_stack_winner():
    stack = _catalog_stack(
        [_catalog_source("default", 1), _catalog_source("community", 20)],
        {
            "default": catalog_payload(
                {"bugfix": _resolved_catalog_entry(version="2.0.0")}
            ),
            "community": catalog_payload(
                {"bugfix": _resolved_catalog_entry(version="1.0.0")}
            ),
        },
    )
    calls = []

    def download(resolved, *, offline):
        calls.append((resolved.source.id, offline))
        return _manifest("bugfix", resolved.entry.version)

    loaded = CatalogBundleLoader(stack, offline=True, download=download).load(
        BundleRef("bugfix", "2.0.0"), ("team",)
    )

    assert loaded.source_id == "default"
    assert calls == [("default", True)]


def test_catalog_loader_omitted_source_uses_higher_priority_non_default_catalog():
    stack = _catalog_stack(
        [_catalog_source("community", 1), _catalog_source("default", 20)],
        {
            "community": catalog_payload(
                {"bugfix": _resolved_catalog_entry(version="1.2.0")}
            ),
            "default": catalog_payload(
                {"bugfix": _resolved_catalog_entry(version="1.2.0")}
            ),
        },
    )
    calls = []

    def download(resolved, *, offline):
        calls.append(resolved.source.id)
        return _manifest("bugfix", resolved.entry.version)

    loaded = CatalogBundleLoader(stack, offline=True, download=download).load(
        BundleRef("bugfix", "1.2.0"), ("team",)
    )

    assert loaded.source_id == "community"
    assert calls == ["community"]


def test_catalog_loader_project_default_definition_overrides_builtin_default(
    tmp_path: Path,
):
    project_catalog = tmp_path / "project-catalog.json"
    project_catalog.write_text(
        yaml.safe_dump(catalog_payload({
            "bugfix": _resolved_catalog_entry(version="1.2.0"),
        })),
        encoding="utf-8",
    )
    config = tmp_path / ".specify"
    config.mkdir()
    (config / "bundle-catalogs.yml").write_text(
        yaml.safe_dump({
            "catalogs": [{
                "id": "default",
                "url": str(project_catalog),
                "priority": 1,
                "install_policy": "install-allowed",
            }],
        }),
        encoding="utf-8",
    )

    stack = CatalogStack.load(
        tmp_path,
        lambda source: yaml.safe_load(Path(source.url).read_text(encoding="utf-8")),
    )
    calls = []

    def download(resolved, *, offline):
        calls.append((resolved.source.id, resolved.source.url))
        return _manifest("bugfix", resolved.entry.version)

    loaded = CatalogBundleLoader(stack, offline=True, download=download).load(
        BundleRef("bugfix", "1.2.0"), ("team",)
    )

    assert loaded.source_id == "default"
    assert calls == [("default", str(project_catalog))]


def test_catalog_loader_missing_release_does_not_fall_through_to_lower_catalog():
    stack = _catalog_stack(
        [_catalog_source("project", 1), _catalog_source("default", 20)],
        {
            "project": catalog_payload(
                {"bugfix": _resolved_catalog_entry(version="2.0.0")}
            ),
            "default": catalog_payload(
                {"bugfix": _resolved_catalog_entry(version="1.2.0")}
            ),
        },
    )
    calls = []

    def download(resolved, *, offline):
        calls.append(resolved)
        return _manifest("bugfix", resolved.entry.version)

    with pytest.raises(BundlerError, match="catalog 'project' offers 2\\.0\\.0"):
        CatalogBundleLoader(stack, offline=True, download=download).load(
            BundleRef("bugfix", "1.2.0"), ("team",)
        )

    assert calls == []


def test_catalog_loader_expansion_wraps_missing_release_and_source_failures():
    cases = [
        (
            BundleRef("bugfix", "0.9.0"),
            "Update the reference",
        ),
        (
            BundleRef("bugfix", "1.2.0", "default"),
            "winning catalog is 'community'",
        ),
    ]
    for reference, cause in cases:
        stack = _catalog_stack(
            [_catalog_source("community", 1)],
            {
                "community": catalog_payload(
                    {"bugfix": _resolved_catalog_entry(version="1.2.0")}
                ),
            },
        )
        root = BundleManifest.from_dict(
            reference_manifest_dict([{
                "id": reference.id,
                "version": reference.version,
                **({"source": reference.source} if reference.source else {}),
            }], bundle_id="team")
        )

        with pytest.raises(BundlerError) as excinfo:
            expand_manifest(
                root,
                CatalogBundleLoader(stack, offline=False, download=lambda *_args, **_kwargs: _manifest("bugfix")),
            )

        message = str(excinfo.value)
        if reference.source:
            assert message.startswith("Bundle reference bugfix (team)")
            assert "Cannot resolve bundle reference" not in message
        else:
            assert message.startswith("Cannot resolve bundle reference bugfix@")
            assert message.count("Cannot resolve bundle reference bugfix@") == 1
        assert cause in message


def test_catalog_loader_real_download_path_honors_offline_mode():
    stack = _catalog_stack(
        [_catalog_source("default", 1)],
        {"default": catalog_payload({"bugfix": _resolved_catalog_entry()})},
    )

    with pytest.raises(BundlerError, match="Network access disabled"):
        CatalogBundleLoader(stack, offline=True).load(
            BundleRef("bugfix", "1.2.0"), ("team",)
        )


def test_catalog_loader_accepts_matching_explicit_source():
    stack = _catalog_stack(
        [_catalog_source("team-catalog", 1)],
        {
            "team-catalog": catalog_payload(
                {"bugfix": _resolved_catalog_entry()}
            )
        },
    )
    loaded = CatalogBundleLoader(
        stack,
        offline=False,
        download=lambda resolved, *, offline: _manifest(
            resolved.entry.id, resolved.entry.version
        ),
    ).load(BundleRef("bugfix", "1.2.0", "team-catalog"), ("team",))

    assert loaded.source_id == "team-catalog"


def test_catalog_loader_rejects_source_mismatch_before_download():
    stack = _catalog_stack(
        [_catalog_source("project", 1), _catalog_source("default", 20)],
        {
            "project": catalog_payload({"bugfix": _resolved_catalog_entry()}),
            "default": catalog_payload({"bugfix": _resolved_catalog_entry()}),
        },
    )
    calls = []

    def download(resolved, *, offline):
        calls.append(resolved)
        return _manifest("bugfix")

    loader = CatalogBundleLoader(stack, offline=False, download=download)
    with pytest.raises(BundlerError, match="winning catalog is 'project'"):
        loader.load(BundleRef("bugfix", "1.2.0", "default"), ("team",))

    assert calls == []


def test_catalog_loader_missing_release_names_pin_and_offered_versions():
    stack = _catalog_stack(
        [_catalog_source("default", 1)],
        {
            "default": catalog_payload(
                {
                    "bugfix": _resolved_catalog_entry(
                        version="2.0.0",
                        releases={
                            "1.0.0": {
                                "download_url": "https://example.com/bugfix-1.0.0.zip",
                                "sha256": "a" * 64,
                            }
                        },
                    )
                }
            )
        },
    )

    with pytest.raises(
        BundlerError,
        match=(
            r"'team' pins bugfix 0\.9\.0, but catalog 'default' offers "
            r"2\.0\.0, 1\.0\.0\. Update the reference"
        ),
    ):
        CatalogBundleLoader(stack, offline=False).load(
            BundleRef("bugfix", "0.9.0"), ("team",)
        )


def _missing_release_stack(source):
    return _catalog_stack(
        [source],
        {
            source.id: catalog_payload(
                {"bugfix": _resolved_catalog_entry(version="1.0.1")}
            )
        },
    )


def test_catalog_loader_offline_builtin_missing_release_recommends_retry():
    stack = _missing_release_stack(_catalog_source("default", 1))

    with pytest.raises(BundlerError) as excinfo:
        CatalogBundleLoader(stack, offline=True).load(
            BundleRef("bugfix", "1.0.2"), ("team",)
        )

    message = str(excinfo.value)
    assert "'team' pins bugfix 1.0.2, but catalog 'default' offers 1.0.1." in message
    assert "built-in catalog may be outdated" in message
    assert "Re-run without --offline." in message
    assert "Update the reference" not in message


@pytest.mark.parametrize("offline", [True, False])
def test_catalog_loader_non_builtin_missing_release_keeps_update_advice(offline):
    # A local catalog named "default" must not be mistaken for the built-in one.
    local = replace(_catalog_source("default", 1), url="/tmp/default-catalog.json")
    stack = _missing_release_stack(local)

    with pytest.raises(BundlerError) as excinfo:
        CatalogBundleLoader(stack, offline=offline).load(
            BundleRef("bugfix", "1.0.2"), ("team",)
        )

    message = str(excinfo.value)
    assert "Update the reference to an advertised version." in message
    assert "--offline" not in message


def test_catalog_loader_offline_release_miss_depends_on_winning_source():
    # The built-in catalog is configured, but a local source wins the lookup.
    local = replace(_catalog_source("team", 1), url="/tmp/team-catalog.json")
    builtin = _catalog_source("default", 20)
    stack = _catalog_stack(
        [local, builtin],
        {
            "team": catalog_payload(
                {"bugfix": _resolved_catalog_entry(version="1.0.1")}
            ),
            "default": catalog_payload(
                {"bugfix": _resolved_catalog_entry(version="1.0.2")}
            ),
        },
    )

    with pytest.raises(BundlerError) as excinfo:
        CatalogBundleLoader(stack, offline=True).load(
            BundleRef("bugfix", "1.0.2"), ("team",)
        )

    assert "Update the reference to an advertised version." in str(excinfo.value)


def test_catalog_loader_offline_missing_bundle_reports_network_limit():
    stack = _catalog_stack(
        [_catalog_source("default", 1)],
        {"default": catalog_payload({})},
    )

    with pytest.raises(BundlerError) as excinfo:
        CatalogBundleLoader(stack, offline=True).load(
            BundleRef("missing", "0.9.0"), ("team",)
        )

    message = str(excinfo.value)
    assert message.startswith(
        "Bundle 'missing' was not found in any configured catalog."
    )
    assert "built-in catalog may be outdated" in message
    assert "Re-run without --offline." in message


def test_catalog_loader_offline_missing_bundle_in_local_catalog_has_no_retry_hint():
    local = replace(_catalog_source("team", 1), url="/tmp/team-catalog.json")
    stack = _catalog_stack([local], {"team": catalog_payload({})})

    with pytest.raises(BundlerError) as excinfo:
        CatalogBundleLoader(stack, offline=True).load(
            BundleRef("missing", "0.9.0"), ("team",)
        )

    assert str(excinfo.value) == (
        "Bundle 'missing' was not found in any configured catalog."
    )


def test_catalog_loader_online_missing_bundle_reports_catalog_miss():
    stack = _catalog_stack(
        [_catalog_source("default", 1)],
        {"default": catalog_payload({})},
    )

    with pytest.raises(BundlerError) as excinfo:
        CatalogBundleLoader(stack, offline=False).load(
            BundleRef("missing", "0.9.0"), ("team",)
        )

    assert str(excinfo.value) == (
        "Bundle 'missing' was not found in any configured catalog."
    )


def test_catalog_loader_propagates_offline_download_error():
    stack = _catalog_stack(
        [_catalog_source("default", 1)],
        {"default": catalog_payload({"bugfix": _resolved_catalog_entry()})},
    )
    error = BundlerError("Network access disabled; cannot download bundle 'bugfix'.")

    def download(resolved, *, offline):
        assert offline is True
        raise error

    with pytest.raises(BundlerError) as excinfo:
        CatalogBundleLoader(stack, offline=True, download=download).load(
            BundleRef("bugfix", "1.2.0"), ("team",)
        )

    assert excinfo.value is error


def test_catalog_loader_returns_discovery_only_policy():
    stack = _catalog_stack(
        [_catalog_source("community", 1, InstallPolicy.DISCOVERY_ONLY)],
        {"community": catalog_payload({"bugfix": _resolved_catalog_entry()})},
    )
    loaded = CatalogBundleLoader(
        stack,
        offline=True,
        download=lambda resolved, *, offline: _manifest(
            resolved.entry.id, resolved.entry.version
        ),
    ).load(BundleRef("bugfix", "1.2.0"), ("team",))

    assert loaded.source_id == "community"
    assert loaded.install_allowed is False


def test_catalog_loader_expands_through_real_catalog_stack():
    stack = _catalog_stack(
        [_catalog_source("default", 1)],
        {"default": catalog_payload({"bugfix": _resolved_catalog_entry()})},
    )
    root = BundleManifest.from_dict(
        reference_manifest_dict(
            [{"id": "bugfix", "version": "1.2.0"}],
            bundle_id="team",
        )
    )
    expanded = expand_manifest(
        root,
        CatalogBundleLoader(
            stack,
            offline=True,
            download=lambda resolved, *, offline: _manifest(
                resolved.entry.id, resolved.entry.version
            ),
        ),
    )

    assert [(ref.id, ref.source_id) for ref in expanded.references] == [
        ("bugfix", "default")
    ]
    assert [component.id for component in expanded.components] == [
        "ext-a",
        "preset-a",
        "step-a",
        "wf-a",
    ]


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


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.2/bundle.zip",
        "http://[0:0:0:0:0:0:0:1]/bundle.zip",
    ],
)
def test_require_https_accepts_shared_loopback_http_forms(url):
    _require_https("bundle 'x'", url)


def test_require_https_rejects_remote_http():
    with pytest.raises(BundlerError, match="non-HTTPS"):
        _require_https("bundle 'x'", "http://example.com/bundle.zip")


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

    The shared URL policy rejects malformed hosts and ports without raising, so
    callers keep the documented BundlerError contract.
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
