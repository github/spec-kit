"""Catalog models: source stack (priority + install policy) and catalog entries.

Mirrors ``contracts/bundle-catalog.schema.md``. The stack precedence is
project > user > built-in; install is permitted only from ``install-allowed``
sources.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .. import BundlerError
from ..lib.yamlio import ensure_within, load_yaml

CONFIG_FILENAME = "bundle-catalogs.yml"


class InstallPolicy(str, Enum):
    INSTALL_ALLOWED = "install-allowed"
    DISCOVERY_ONLY = "discovery-only"

    @classmethod
    def parse(cls, value: Any) -> "InstallPolicy":
        text = str(value or "").strip()
        for policy in cls:
            if policy.value == text:
                return policy
        raise BundlerError(
            f"Invalid install_policy '{value}' "
            f"(must be one of {[p.value for p in cls]})."
        )


class Scope(str, Enum):
    PROJECT = "project"
    USER = "user"
    BUILTIN = "built-in"


# Built-in default stack (used when no project/user config overrides it).
BUILTIN_DEFAULT_STACK: tuple[dict[str, Any], ...] = (
    {"id": "default", "url": "builtin://default", "priority": 1,
     "install_policy": InstallPolicy.INSTALL_ALLOWED.value},
    {"id": "community", "url": "builtin://community", "priority": 2,
     "install_policy": InstallPolicy.DISCOVERY_ONLY.value},
)


@dataclass(frozen=True)
class CatalogSource:
    id: str
    url: str
    priority: int
    install_policy: InstallPolicy
    scope: Scope = Scope.PROJECT

    @property
    def install_allowed(self) -> bool:
        return self.install_policy is InstallPolicy.INSTALL_ALLOWED

    @classmethod
    def from_dict(cls, data: Any, scope: Scope) -> "CatalogSource":
        if not isinstance(data, dict):
            raise BundlerError("Each catalog source must be a mapping.")
        source_id = str(data.get("id", "")).strip()
        url = str(data.get("url", "")).strip()
        if not source_id:
            raise BundlerError("A catalog source is missing its 'id'.")
        if not url:
            raise BundlerError(f"Catalog source '{source_id}' is missing its 'url'.")
        priority = data.get("priority")
        if priority is None:
            raise BundlerError(f"Catalog source '{source_id}' is missing its 'priority'.")
        if isinstance(priority, bool) or not isinstance(priority, (int, str)):
            raise BundlerError(
                f"Catalog source '{source_id}' has a non-integer priority: {priority!r}."
            )
        try:
            priority_int = int(priority)
        except (TypeError, ValueError):
            raise BundlerError(
                f"Catalog source '{source_id}' has a non-integer priority: {priority!r}."
            ) from None
        return cls(
            id=source_id,
            url=url,
            priority=priority_int,
            install_policy=InstallPolicy.parse(data.get("install_policy")),
            scope=scope,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "priority": self.priority,
            "install_policy": self.install_policy.value,
        }


def _parse_tags(value: Any, entry_id: str) -> tuple[str, ...]:
    """Coerce a catalog entry's ``tags`` into a tuple of strings.

    Catalogs are untrusted input: a bare string would otherwise be iterated
    character-by-character, so reject anything that is not a list/tuple.
    """
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise BundlerError(
            f"Catalog entry '{entry_id}': 'tags' must be a list of strings."
        )
    return tuple(str(t) for t in value)


def _parse_verified(value: Any, entry_id: str) -> bool:
    """Validate a catalog entry's ``verified`` flag is a real boolean.

    ``bool("false")`` is truthy, so coercing arbitrary strings would silently
    mark untrusted entries as verified; require an actual boolean instead.
    """
    if isinstance(value, bool):
        return value
    raise BundlerError(
        f"Catalog entry '{entry_id}': 'verified' must be a boolean (true/false)."
    )


@dataclass(frozen=True)
class CatalogEntry:
    id: str
    name: str
    version: str
    role: str
    description: str
    author: str
    license: str
    download_url: str
    requires_speckit_version: str
    provides: dict[str, int] = field(default_factory=dict)
    repository: str | None = None
    tags: tuple[str, ...] = ()
    verified: bool = False
    # Resolution provenance (filled in by the catalog stack at lookup time):
    source_id: str | None = None
    source_policy: InstallPolicy | None = None

    @classmethod
    def from_dict(cls, data: Any) -> "CatalogEntry":
        if not isinstance(data, dict):
            raise BundlerError("Each catalog entry must be a mapping.")
        entry_id = str(data.get("id", "")).strip()
        requires = data.get("requires") or {}
        if not isinstance(requires, dict):
            raise BundlerError(
                f"Catalog entry '{entry_id or '<unknown>'}': 'requires' must be a "
                "mapping when present."
            )
        provides_raw = data.get("provides") or {}
        if not isinstance(provides_raw, dict):
            raise BundlerError(
                f"Catalog entry '{entry_id or '<unknown>'}': 'provides' must be a "
                "mapping when present."
            )
        return cls(
            id=entry_id,
            name=str(data.get("name", "")).strip(),
            version=str(data.get("version", "")).strip(),
            role=str(data.get("role", "")).strip(),
            description=str(data.get("description", "")).strip(),
            author=str(data.get("author", "")).strip(),
            license=str(data.get("license", "")).strip(),
            download_url=str(data.get("download_url", "")).strip(),
            requires_speckit_version=str(requires.get("speckit_version", "")).strip(),
            provides=dict(provides_raw),
            repository=(str(data["repository"]) if data.get("repository") else None),
            tags=_parse_tags(data.get("tags"), entry_id),
            verified=_parse_verified(data.get("verified", False), entry_id),
        )

    def with_provenance(self, source: CatalogSource) -> "CatalogEntry":
        return CatalogEntry(
            id=self.id, name=self.name, version=self.version, role=self.role,
            description=self.description, author=self.author, license=self.license,
            download_url=self.download_url,
            requires_speckit_version=self.requires_speckit_version,
            provides=self.provides, repository=self.repository, tags=self.tags,
            verified=self.verified, source_id=source.id,
            source_policy=source.install_policy,
        )


def load_catalog_payload(data: Any) -> dict[str, CatalogEntry]:
    """Parse a catalog JSON payload into ``{bundle_id: CatalogEntry}``."""
    if not isinstance(data, dict):
        raise BundlerError("Catalog payload must be a JSON object.")
    bundles_raw = data.get("bundles")
    if not isinstance(bundles_raw, dict):
        raise BundlerError("Catalog payload is missing a 'bundles' object.")
    entries: dict[str, CatalogEntry] = {}
    for bundle_id, entry_raw in bundles_raw.items():
        key = str(bundle_id)
        entry = CatalogEntry.from_dict(entry_raw)
        # The enclosing key is the authoritative bundle id used by
        # search/resolve/install. Reject entries whose own ``id`` is missing or
        # disagrees with the key, so a malformed or malicious catalog can't list
        # an id that resolves to a different (or no) bundle.
        if not entry.id:
            raise BundlerError(
                f"Catalog entry for '{key}' is missing its 'id' field."
            )
        if entry.id != key:
            raise BundlerError(
                f"Catalog entry id mismatch: key '{key}' != entry id "
                f"'{entry.id}'."
            )
        entries[key] = entry
    return entries


def load_source_stack(project_root: Path, user_config_dir: Path | None = None) -> list[CatalogSource]:
    """Build the effective, priority-sorted source stack (project > user > built-in).

    A source id present at a higher-precedence scope overrides the same id at a
    lower scope. The built-in default stack is always the fallback.
    """
    by_id: dict[str, CatalogSource] = {}

    # Lowest precedence first; later writes override earlier ones for the same id.
    for raw in BUILTIN_DEFAULT_STACK:
        src = CatalogSource.from_dict(raw, Scope.BUILTIN)
        by_id[src.id] = src

    if user_config_dir is not None:
        _merge_config(by_id, Path(user_config_dir) / CONFIG_FILENAME, Scope.USER)

    # Confine the project-scoped read: refuse a symlinked .specify/ that
    # resolves outside the project root (consistent with other guarded reads).
    project_config = Path(project_root) / ".specify" / CONFIG_FILENAME
    if project_config.exists():
        ensure_within(project_root, project_config)
    _merge_config(by_id, project_config, Scope.PROJECT)

    return sorted(by_id.values(), key=lambda s: (s.priority, s.id))


def _merge_config(by_id: dict[str, CatalogSource], config_path: Path, scope: Scope) -> None:
    if not config_path.exists():
        return
    data = load_yaml(config_path)
    catalogs = data.get("catalogs") if isinstance(data, dict) else None
    if not catalogs:
        return
    for raw in catalogs:
        src = CatalogSource.from_dict(raw, scope)
        by_id[src.id] = src
