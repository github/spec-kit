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
    data = load_yaml(path)
    if data is None:
        return []
    if not isinstance(data, dict):
        raise BundlerError(
            f"Malformed catalog config at {path}: expected a mapping at the top "
            f"level, got {type(data).__name__}."
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
    scheme = urlparse(url).scheme.lower()
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
        host = parsed.netloc.split("@")[-1].split(":")[0]
        # Hostnames are case-insensitive; _slug() lowercases so 'Example.com'
        # and 'example.com' derive the same, deterministic id.
        host_label = Path(host).stem or host
        path_stem = Path(parsed.path).stem if parsed.path else ""
        parts = [p for p in (_slug(host_label), _slug(path_stem)) if p]
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
    parsed = urlparse(url)
    if not (parsed.scheme or parsed.path):
        raise BundlerError(f"Invalid catalog url: '{url}'.")

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
    remaining = [
        c for c in catalogs if c.get("id") != target and c.get("url") != target
    ]
    if len(remaining) == len(catalogs):
        raise BundlerError(
            f"No project-scoped catalog source matching '{target}' was found."
        )
    _write(project_root, remaining)
    return target
