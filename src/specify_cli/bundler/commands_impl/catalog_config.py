"""Persistence for the project-scoped catalog config (``.specify/bundle-catalogs.yml``).

Only project scope is writable; built-in defaults are never deleted (they can be
overridden by adding a same-id source). The on-disk shape mirrors
``bundle-catalog.schema.md``: ``{schema_version, catalogs: [{id,url,priority,install_policy}]}``.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import re

from .. import BundlerError
from ..lib.yamlio import dump_yaml, ensure_within, load_yaml
from ..models.catalog import (
    CONFIG_FILENAME,
    BUILTIN_DEFAULT_STACK,
    CatalogSource,
    InstallPolicy,
    Scope,
)

CONFIG_SCHEMA_VERSION = "1.0"

_BUILTIN_IDS = {raw["id"] for raw in BUILTIN_DEFAULT_STACK}

# Windows absolute paths like ``C:\catalog.json`` parse with a single-letter
# ``scheme`` under urlparse; treat them as local files rather than URLs.
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")


def _config_path(project_root: Path) -> Path:
    return Path(project_root) / ".specify" / CONFIG_FILENAME


def _read(project_root: Path) -> list[dict]:
    # Confine the read (parity with the write path's within= guard): refuse to
    # follow a symlinked or traversal-escaping .specify that resolves outside
    # project_root.
    path = ensure_within(project_root, _config_path(project_root))
    if not path.exists():
        return []
    # ``load_yaml`` returns ``{}`` only for an empty document and the raw parse
    # otherwise, so a non-mapping top level — a falsy ``[]``/``false``/``0``/``''``
    # or an explicit null (``load_yaml`` -> ``None``) — is caught by the isinstance
    # guard below and raised like a truthy one, staying consistent with the other
    # reader of this file (models/catalog._merge_config).
    data = load_yaml(path)
    if not isinstance(data, dict):
        raise BundlerError(
            f"Malformed catalog config at {path}: expected a mapping at the top "
            f"level, got {type(data).__name__}."
        )
    schema_version = data.get("schema_version")
    if schema_version is not None and (
        str(schema_version).strip().split(".")[0]
        != CONFIG_SCHEMA_VERSION.split(".")[0]
    ):
        raise BundlerError(
            f"Unsupported catalog config schema version "
            f"'{str(schema_version).strip()}' at {path}; this Spec Kit "
            f"understands version {CONFIG_SCHEMA_VERSION}. The file may have been "
            "written by a newer version or is corrupt."
        )
    catalogs = data.get("catalogs")
    if catalogs is None:
        return []
    if not isinstance(catalogs, list):
        raise BundlerError(
            f"Malformed catalog config at {path}: 'catalogs' must be a list, "
            f"got {type(catalogs).__name__}."
        )
    for entry in catalogs:
        if not isinstance(entry, dict):
            raise BundlerError(
                f"Malformed catalog config at {path}: each catalog entry must be "
                f"a mapping, got {type(entry).__name__}."
            )
    return list(catalogs)


def _write(project_root: Path, catalogs: list[dict]) -> None:
    payload = {"schema_version": CONFIG_SCHEMA_VERSION, "catalogs": catalogs}
    dump_yaml(_config_path(project_root), payload, within=project_root)


def _slug(value: str) -> str:
    # Lowercase so derived ids are deterministic and case-insensitive across
    # platforms (e.g. 'Team-A.json' and 'team-a.json' yield the same id),
    # keeping the case-sensitive duplicate check from admitting logical dupes.
    return "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-")


_REMOTE_SCHEMES = {"http", "https", "file", "builtin"}


def _is_local_path(url: str) -> bool:
    """True when *url* denotes a local filesystem path rather than a URL."""
    if _WINDOWS_DRIVE_RE.match(url):
        return True
    try:
        scheme = urlparse(url).scheme.lower()
    except ValueError:
        # Malformed URLs (e.g. an unclosed IPv6 bracket) are not local paths.
        return False
    return scheme not in _REMOTE_SCHEMES


def _canonicalize_url(url: str) -> str:
    """Make local file paths absolute so config is independent of the caller's cwd.

    Remote URLs (``http(s)://``, ``file://``, ``builtin://``) are returned
    unchanged; only bare/relative local paths are resolved to an absolute path.
    """
    if _is_local_path(url):
        return str(Path(url).expanduser().resolve())
    return url


def _derive_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc:
        # Use .hostname (not netloc.split(':')) so credentials, ports, and IPv6
        # literals (e.g. https://[2001:db8::1]/x) are handled correctly. Use the
        # full host (TLD included) so different domains sharing a second-level
        # label (example.com vs example.net) don't collide. _slug() lowercases
        # and turns separators into dashes, so 'Example.com' -> 'example-com'.
        host = parsed.hostname or ""
        path_stem = Path(parsed.path).stem if parsed.path else ""
        parts = [p for p in (_slug(host), _slug(path_stem)) if p]
        return "-".join(parts) or "catalog"
    stem = Path(parsed.path or url).stem
    return _slug(stem) or "catalog"


def add_source(
    project_root: Path,
    url: str,
    *,
    policy: str,
    priority: int,
    source_id: str | None = None,
) -> CatalogSource:
    url = url.strip()
    if not url:
        raise BundlerError("A catalog url is required.")
    try:
        parsed = urlparse(url)
        # Read .hostname inside the try: a bracketed-but-invalid IPv6 authority
        # (e.g. "https://[not-an-ip]/c.json") parses cleanly under urlparse() on
        # Python < 3.14 but raises ValueError lazily on the first .hostname access
        # (the raise moved eager into urlparse() only in 3.14). Reading it here
        # keeps that ValueError inside the guard instead of leaking a raw
        # traceback past the CLI's `except BundlerError`. Reuse the value below.
        hostname = parsed.hostname
    except ValueError as exc:
        raise BundlerError(f"Invalid catalog url: '{url}'.") from exc
    if not (parsed.scheme or parsed.path):
        raise BundlerError(f"Invalid catalog url: '{url}'.")
    # Reject unsupported URL schemes (e.g. ssh://, ftp://) up front so they are
    # never silently canonicalized as local filesystem paths. Local paths that
    # merely contain a ':' but no '://' (e.g. Windows drives) are still allowed.
    if "://" in url and parsed.scheme.lower() not in _REMOTE_SCHEMES:
        raise BundlerError(
            f"Unsupported catalog url scheme '{parsed.scheme}://' in '{url}'. "
            "Use http(s)://, file://, builtin://, or a local path."
        )
    if parsed.scheme.lower() in {"http", "https"}:
        # Mirror specify_cli.catalogs._validate_catalog_url (#3209/#3210):
        # HTTPS only (HTTP just for localhost), and check hostname, not
        # netloc — netloc is truthy for host-less URLs like "https://:8080"
        # or "https://user@". Validating here keeps junk out of
        # bundle-catalogs.yml instead of failing later at fetch time.
        is_localhost = hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme.lower() != "https" and not is_localhost:
            raise BundlerError(
                f"Catalog url must use HTTPS (got {parsed.scheme}://). "
                "HTTP is only allowed for localhost."
            )
        if not hostname:
            raise BundlerError(f"Catalog url must be a valid URL with a host: {url}")

    url = _canonicalize_url(url)
    install_policy = InstallPolicy.parse(policy)
    resolved_id = (source_id or _derive_id(url)).strip()

    catalogs = _read(project_root)
    for existing in catalogs:
        if existing.get("id") == resolved_id or existing.get("url") == url:
            raise BundlerError(
                f"Catalog source '{resolved_id}' (or url) already exists in this project."
            )

    entry = {
        "id": resolved_id,
        "url": url,
        "priority": int(priority),
        "install_policy": install_policy.value,
    }
    catalogs.append(entry)
    _write(project_root, catalogs)
    return CatalogSource.from_dict(entry, Scope.PROJECT)


def remove_source(project_root: Path, id_or_url: str) -> str:
    target = id_or_url.strip()
    if target in _BUILTIN_IDS:
        raise BundlerError(
            f"'{target}' is a built-in default source and cannot be deleted "
            "(add a same-id source to override it instead)."
        )

    catalogs = _read(project_root)
    # Prefer an exact id/url match.
    remaining = [c for c in catalogs if c.get("id") != target and c.get("url") != target]
    if len(remaining) == len(catalogs):
        # No exact match. add_source canonicalizes a local path to an absolute
        # url before storing, so fall back to a canonicalized-url match -- this
        # lets `remove ./cat.json` undo `add ./cat.json` (stored absolute).
        # Only as a *fallback*: _canonicalize_url treats a bare id as a local
        # path (empty scheme), so applying it unconditionally could also delete a
        # different source whose url equals the id's canonicalized path.
        canonical = _canonicalize_url(target)
        if canonical != target:
            remaining = [c for c in catalogs if c.get("url") != canonical]
    if len(remaining) == len(catalogs):
        raise BundlerError(
            f"No project-scoped catalog source matching '{target}' was found."
        )
    _write(project_root, remaining)
    return target
