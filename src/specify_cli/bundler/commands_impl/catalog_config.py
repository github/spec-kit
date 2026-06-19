"""Persistence for the project-scoped catalog config (``.specify/bundle-catalogs.yml``).

Only project scope is writable; built-in defaults are never deleted (they can be
overridden by adding a same-id source). The on-disk shape mirrors
``bundle-catalog.schema.md``: ``{schema_version, catalogs: [{id,url,priority,install_policy}]}``.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from .. import BundlerError
from ..lib.yamlio import dump_yaml, load_yaml
from ..models.catalog import (
    CONFIG_FILENAME,
    BUILTIN_DEFAULT_STACK,
    CatalogSource,
    InstallPolicy,
    Scope,
)

CONFIG_SCHEMA_VERSION = "1.0"

_BUILTIN_IDS = {raw["id"] for raw in BUILTIN_DEFAULT_STACK}


def _config_path(project_root: Path) -> Path:
    return Path(project_root) / ".specify" / CONFIG_FILENAME


def _read(project_root: Path) -> list[dict]:
    path = _config_path(project_root)
    if not path.exists():
        return []
    data = load_yaml(path)
    catalogs = data.get("catalogs") if isinstance(data, dict) else None
    return list(catalogs) if catalogs else []


def _write(project_root: Path, catalogs: list[dict]) -> None:
    payload = {"schema_version": CONFIG_SCHEMA_VERSION, "catalogs": catalogs}
    dump_yaml(_config_path(project_root), payload)


def _derive_id(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    stem = Path(host).stem or host or "catalog"
    return stem.replace("/", "-").strip("-") or "catalog"


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
