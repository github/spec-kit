"""Resolve local and remote bundle manifests for bundle consumers."""

from __future__ import annotations

import re
from pathlib import Path

from .._download_security import MAX_DOWNLOAD_BYTES, read_response_limited
from . import BundlerError

# ZIP magic-byte signatures cover local headers, empty archives, and spanning markers.
_ZIP_SIGNATURES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")


def _local_manifest_source(arg: str):
    """Return a :class:`BundleManifest` if *arg* points at a local bundle.

    Supports a built ``.zip`` artifact, a bundle directory, or a ``bundle.yml``
    file. Returns ``None`` when *arg* is not an existing path, so callers fall
    back to catalog-stack resolution by bundle id.
    """
    from .manifest import BundleManifest

    candidate = Path(arg).expanduser()
    if not candidate.exists():
        return None

    if candidate.is_dir():
        manifest_path = candidate / "bundle.yml"
        if not manifest_path.exists():
            raise BundlerError(f"No bundle.yml found in '{candidate}'.")
        return BundleManifest.from_file(manifest_path)

    if candidate.suffix == ".zip":
        import yaml as _yaml

        from .._download_security import open_zip_bounded, read_zip_member_limited

        with open_zip_bounded(candidate, error_type=BundlerError) as archive:
            try:
                archive.getinfo("bundle.yml")
            except KeyError as exc:
                raise BundlerError(
                    f"Artifact '{candidate}' does not contain a bundle.yml."
                ) from exc
            raw = read_zip_member_limited(
                archive,
                "bundle.yml",
                error_type=BundlerError,
                label="bundle manifest",
            )
        # The bounded-zip helpers above keep archive failures inside the
        # BundlerError contract, but the manifest bytes need the same
        # treatment as yamlio.load_yaml: decode as UTF-8 explicitly —
        # feeding PyYAML the byte stream would let its Reader auto-detect
        # a UTF-16 BOM and accept a manifest the directory and bundle.yml
        # sources reject.
        try:
            text = raw.decode("utf-8")
        except UnicodeError as exc:
            raise BundlerError(
                f"Could not read bundle.yml inside '{candidate}': {exc}"
            ) from exc
        try:
            data = _yaml.safe_load(text)
        except _yaml.YAMLError as exc:
            # The sibling directory/bundle.yml branches reach YAML through
            # load_yaml(), which turns a parse failure into a BundlerError. This
            # branch parses inline, so without this it raises a raw YAMLError --
            # neither a ValueError nor an OSError -- which escapes
            # bundle_install()'s `except BundlerError` as a traceback.
            raise BundlerError(
                f"Invalid YAML in bundle.yml inside '{candidate}': {exc}"
            ) from exc
        return BundleManifest.from_dict(data)

    if candidate.name == "bundle.yml" or candidate.suffix in (".yml", ".yaml"):
        return BundleManifest.from_file(candidate)

    raise BundlerError(
        f"'{candidate}' is not a recognised bundle source (.zip artifact, bundle "
        "directory, or bundle.yml)."
    )


def _download_manifest(resolved, *, offline: bool):
    """Resolve a bundle's manifest from its catalog ``download_url``.

    Catalog ``download_url``s are HTTPS-only (``http`` allowed for localhost),
    matching the extensions/presets/workflows catalog systems. Remote URLs are
    fetched with the shared authenticated, redirect-validated HTTP client, and
    only when not ``--offline``.

    Local and ``file://`` sources are intentionally not resolved here: to
    install a bundle from disk, pass the path positionally
    (``specify bundle install ./path/to/bundle.yml`` — a bundle directory or a
    ``.zip`` artifact also works), which :func:`_local_manifest_source` handles
    before catalog resolution and which never touches ``download_url``.
    """
    from urllib.parse import urlparse

    url = resolved.entry.download_url
    if not url:
        raise BundlerError(
            f"Catalog entry '{resolved.entry.id}' has no download_url; cannot resolve "
            "its manifest."
        )
    # A malformed authority (e.g. an unclosed IPv6 bracket ``https://[::1``)
    # makes urlparse raise ValueError. Surface it as the documented
    # BundlerError, like the sibling ``_validate_remote_url``, rather than
    # leaking a raw ValueError past the callers, which only catch BundlerError.
    try:
        parsed = urlparse(url)
    except ValueError:
        raise BundlerError(
            f"Catalog entry '{resolved.entry.id}' has a malformed download_url: {url}"
        ) from None
    scheme = parsed.scheme.lower()

    # ``file://`` URLs and bare filesystem paths (including Windows drive paths
    # like ``C:\bundle.yml``, which urlparse reads as a single-letter scheme)
    # are not valid catalog download URLs. Catalog URLs are HTTPS-only across
    # every catalog system; installing from disk is done by passing the path
    # positionally, which never reaches URL resolution. Give an actionable
    # error rather than accepting a scheme the rest of the codebase rejects.
    if scheme in ("", "file") or re.match(r"^[A-Za-z]:[\\/]", url):
        raise BundlerError(
            f"Catalog entry '{resolved.entry.id}' has a non-HTTP(S) download_url "
            f"({url}); catalog download URLs must be HTTPS (http for localhost) — "
            "a file:// URL, a local filesystem path, or a scheme-less value "
            "(e.g. 'example.com/bundle.zip') is not accepted. "
            "To install a bundle from disk, pass the path directly: "
            "'specify bundle install <path-to-bundle.yml | bundle-dir | .zip>'."
        )

    # Validate the scheme/host *before* the offline gate so an invalid or
    # non-HTTPS download_url reports the real problem in every mode, rather
    # than a misleading "Network access disabled" under --offline.
    # (_download_remote_manifest re-checks this, but only once network access
    # is permitted.) HTTPS-only, http allowed for localhost.
    _require_https(f"bundle '{resolved.entry.id}'", url)

    if offline:
        raise BundlerError(
            f"Network access disabled; cannot download bundle '{resolved.entry.id}' "
            f"from {url}."
        )
    manifest = _download_remote_manifest(
        resolved.entry.id,
        url,
        expected_sha256=getattr(resolved.entry, "sha256", None),
    )
    _validate_catalog_manifest(resolved.entry, manifest)
    return manifest


def _require_https(label: str, url: str) -> None:
    from urllib.parse import urlparse

    # urlparse / hostname access raise ValueError on a malformed authority;
    # keep the documented BundlerError contract (older Pythons surface this via
    # the .hostname access below rather than at the urlparse call).
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        # Accessing ``port`` performs urllib's syntax/range validation.
        _ = parsed.port
    except ValueError:
        raise BundlerError(
            f"Refusing to download {label}: URL is malformed: {url}"
        ) from None
    is_localhost = hostname in ("localhost", "127.0.0.1", "::1")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
        raise BundlerError(f"Refusing to download {label} over non-HTTPS URL: {url}")
    if not parsed.hostname:
        raise BundlerError(f"Refusing to download {label} from URL with no host: {url}")


def _download_remote_manifest(
    entry_id: str,
    url: str,
    *,
    expected_sha256: str | None = None,
):
    """Fetch a remote bundle artifact over HTTPS and extract its manifest."""
    import tempfile
    from pathlib import PurePosixPath
    from urllib.parse import urlparse as _urlparse

    import yaml as _yaml

    from ..authentication.http import github_provider_hosts, open_url
    from ..authentication.github_http import resolve_github_release_asset_api_url
    from .manifest import BundleManifest
    from ..shared_infra import verify_archive_sha256

    def _validate_redirect(old_url: str, new_url: str) -> None:
        _require_https(f"bundle '{entry_id}'", new_url)

    _require_https(f"bundle '{entry_id}'", url)

    # For private/SSO-protected GitHub repos, browser release download URLs
    # (https://github.com/<owner>/<repo>/releases/download/<tag>/<asset>)
    # redirect to an HTML/SSO page instead of delivering the asset.  Resolve
    # such URLs to the GitHub REST API asset URL so the authenticated client
    # can download the actual file.
    extra_headers = None
    effective_url = url
    resolved = resolve_github_release_asset_api_url(
        url, open_url, timeout=30, github_hosts=github_provider_hosts()
    )
    if resolved:
        effective_url = resolved
        _require_https(f"bundle '{entry_id}'", effective_url)
        extra_headers = {"Accept": "application/octet-stream"}

    # Human-readable description of where the bytes came from, reused across
    # all post-download error messages so failures point at the catalog URL
    # (and resolved API URL, if any) instead of an opaque temp path.
    if effective_url != url:
        _source_desc = f"{url} (resolved to {effective_url})"
    else:
        _source_desc = url

    try:
        with open_url(
            effective_url,
            timeout=30,
            redirect_validator=_validate_redirect,
            extra_headers=extra_headers,
        ) as resp:
            _require_https(f"bundle '{entry_id}'", resp.geturl())
            raw = read_response_limited(
                resp,
                max_bytes=MAX_DOWNLOAD_BYTES,
                error_type=BundlerError,
                label=f"bundle '{entry_id}' download",
            )
        verify_archive_sha256(
            raw,
            expected_sha256,
            entry_id,
            BundlerError,
        )
    except BundlerError:
        raise
    except Exception as exc:  # noqa: BLE001
        # Report the original catalog URL so users know which entry to fix,
        # and include the resolved URL when it differs for easier debugging.
        raise BundlerError(
            f"Failed to download bundle '{entry_id}' from {_source_desc}: {exc}"
        ) from exc

    # A .zip artifact is written to a temp file and parsed via the local-source
    # path (which extracts bundle.yml); any other payload is treated as YAML.
    # Detection uses the path component of the original catalog URL (via
    # PurePosixPath so query strings and fragments are ignored, and URL paths
    # are always treated as POSIX regardless of host OS), falling back to the
    # module-level _ZIP_SIGNATURES magic-byte check for direct REST API asset
    # URLs which carry no file extension.
    _url_ext = PurePosixPath(_urlparse(url).path).suffix.lower()
    try:
        if _url_ext == ".zip" or raw[:4] in _ZIP_SIGNATURES:
            with tempfile.TemporaryDirectory() as tmp:
                artifact = Path(tmp) / "bundle.zip"
                artifact.write_bytes(raw)
                # Wrap ZIP parsing so any failure (BadZipFile, missing
                # bundle.yml, etc.) references the source URL rather than the
                # opaque temporary path, consistent with the download-error
                # handling above.
                try:
                    manifest = _local_manifest_source(str(artifact))
                except Exception as exc:  # noqa: BLE001
                    raise BundlerError(
                        f"Downloaded artifact for bundle '{entry_id}' from "
                        f"{_source_desc} is not a valid bundle: {exc}"
                    ) from exc
                # _local_manifest_source returns None only when the file does
                # not exist; since we just wrote *artifact* that cannot happen
                # here.  The explicit guard ensures callers never receive None
                # and silently degrade instead of raising a clear error.
                if manifest is None:
                    raise BundlerError(
                        f"Downloaded artifact for bundle '{entry_id}' from "
                        f"{_source_desc} is not a valid bundle."
                    )
                return manifest

        # Decode as UTF-8 explicitly -- matching yamlio.load_yaml's contract --
        # instead of feeding PyYAML the raw byte stream. PyYAML's Reader
        # auto-detects a UTF-16 BOM and would silently *accept* a manifest
        # that the local directory/bundle.yml sources reject, letting this
        # remote-download path diverge from them (see the sibling .zip fix
        # for _local_manifest_source, which had the identical bug).
        try:
            text = raw.decode("utf-8")
        except UnicodeError as exc:
            raise BundlerError(
                f"Downloaded content for bundle '{entry_id}' from "
                f"{_source_desc} could not be read: {exc}"
            ) from exc
        data = _yaml.safe_load(text)
        return BundleManifest.from_dict(data)
    except BundlerError:
        raise
    except _yaml.YAMLError as exc:
        raise BundlerError(
            f"Downloaded content for bundle '{entry_id}' from {_source_desc} "
            f"is not valid YAML: {exc}"
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise BundlerError(
            f"Failed to parse downloaded bundle '{entry_id}' from {_source_desc}: {exc}"
        ) from exc


def _validate_manifest_structure(manifest, *, source: str) -> None:
    """Reject a malformed manifest before any project mutation can occur."""
    from .validator import validate_manifest

    report = validate_manifest(manifest)
    if report.ok:
        return
    raise BundlerError(
        f"{source} contains an invalid bundle manifest:\n  - "
        + "\n  - ".join(report.errors)
    )


def _validate_catalog_manifest(entry, manifest) -> None:
    """Bind a downloaded manifest to the catalog identity that selected it."""
    if manifest.bundle.id != entry.id:
        raise BundlerError(
            f"Downloaded bundle id mismatch: catalog entry {entry.id!r} points to "
            f"a manifest for {manifest.bundle.id!r}."
        )
    if manifest.bundle.version != entry.version:
        raise BundlerError(
            f"Downloaded bundle version mismatch for {entry.id!r}: catalog declares "
            f"{entry.version!r}, but the manifest declares "
            f"{manifest.bundle.version!r}."
        )
    _validate_manifest_structure(
        manifest,
        source=f"Downloaded bundle {entry.id!r}",
    )
