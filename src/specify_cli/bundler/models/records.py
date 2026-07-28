"""Installed-bundle records — provenance for precise list/remove/update.

Records are stored as JSON at ``.specify/bundle-records.json``. Each record
captures exactly which components a bundle contributed so removal touches only
that bundle's components and never collateral (FR-022, SC-004).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import BundlerError
from ..lib.yamlio import dump_json, ensure_within, load_json
from .manifest import COMPONENT_KINDS, ComponentRef

RECORDS_FILENAME = "bundle-records.json"
RECORDS_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class InstalledBundleRecord:
    bundle_id: str
    version: str
    contributed_components: tuple[ComponentRef, ...]
    installed_at: str

    @classmethod
    def create(
        cls,
        bundle_id: str,
        version: str,
        components: list[ComponentRef],
        installed_at: str | None = None,
    ) -> "InstalledBundleRecord":
        return cls(
            bundle_id=bundle_id,
            version=version,
            contributed_components=tuple(components),
            installed_at=installed_at or _utc_now(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "version": self.version,
            "installed_at": self.installed_at,
            "contributed_components": [
                _component_to_dict(c) for c in self.contributed_components
            ],
        }

    @classmethod
    def from_dict(cls, data: Any) -> "InstalledBundleRecord":
        if not isinstance(data, dict):
            raise BundlerError("Each installed-bundle record must be a mapping.")
        components_raw = data.get("contributed_components")
        if components_raw is None:
            components_raw = []
        elif not isinstance(components_raw, list):
            # `or []` would coerce a FALSY non-list (0, '', False, {}) to []
            # before this guard, silently accepting a corrupt record; only an
            # absent/None value means "no components".
            raise BundlerError(
                "Corrupt record: 'contributed_components' must be a list."
            )
        bundle_id = str(data.get("bundle_id", "")).strip()
        version = str(data.get("version", "")).strip()
        if not bundle_id:
            raise BundlerError(
                "Corrupt records file: an installed-bundle record is missing "
                "its 'bundle_id'."
            )
        if not version:
            raise BundlerError(
                f"Corrupt records file: record for bundle '{bundle_id}' is "
                "missing its 'version'."
            )
        return cls(
            bundle_id=bundle_id,
            version=version,
            installed_at=str(data.get("installed_at", "")).strip(),
            contributed_components=tuple(
                _component_from_dict(c) for c in components_raw
            ),
        )


def records_path(project_root: Path) -> Path:
    return Path(project_root) / ".specify" / RECORDS_FILENAME


def _check_schema_version(value: Any, *, path: Path, required: bool) -> None:
    """Reject a records file whose schema version we cannot safely parse.

    A future incompatible format (or a corrupted file) must fail fast with an
    actionable error rather than being silently mis-parsed, which could lead to
    incorrect bundle attribution or removal. Forward-compatible minor bumps that
    keep the same major version are accepted.
    """
    if value is None:
        if required:
            raise BundlerError(
                f"Corrupt records file: {path} — missing 'schema_version'. "
                f"Expected version {RECORDS_SCHEMA_VERSION}."
            )
        return
    seen = str(value).strip()
    if seen.split(".")[0] != RECORDS_SCHEMA_VERSION.split(".")[0]:
        raise BundlerError(
            f"Unsupported records schema version '{seen}' at {path}; this "
            f"Spec Kit understands version {RECORDS_SCHEMA_VERSION}. The file may "
            "have been written by a newer version or is corrupt."
        )


def load_records(project_root: Path) -> list[InstalledBundleRecord]:
    # Defense in depth (mirrors the write path's within= confinement): refuse to
    # read through a symlinked or traversal-escaping ``.specify`` that resolves
    # outside project_root.
    path = ensure_within(project_root, records_path(project_root))
    if not path.exists():
        return []
    data = load_json(path)
    if not isinstance(data, dict):
        raise BundlerError(f"Corrupt records file: {path}")
    _check_schema_version(data.get("schema_version"), path=path, required=True)
    bundles = data.get("bundles")
    if bundles is None:
        bundles = []
    elif not isinstance(bundles, list):
        # `or []` would coerce a FALSY non-list (0, '', False, {}) to [] before
        # this guard, silently treating a corrupt file as "no bundles"; only an
        # absent/None value means empty.
        raise BundlerError(
            f"Corrupt records file: {path} — 'bundles' must be a list."
        )
    return [InstalledBundleRecord.from_dict(item) for item in bundles]


def save_records(project_root: Path, records: list[InstalledBundleRecord]) -> None:
    payload = {
        "schema_version": RECORDS_SCHEMA_VERSION,
        "updated_at": _utc_now(),
        "bundles": [r.to_dict() for r in records],
    }
    dump_json(records_path(project_root), payload, within=project_root)


def find_record(
    records: list[InstalledBundleRecord], bundle_id: str
) -> InstalledBundleRecord | None:
    for record in records:
        if record.bundle_id == bundle_id:
            return record
    return None


def upsert_record(
    records: list[InstalledBundleRecord], record: InstalledBundleRecord
) -> list[InstalledBundleRecord]:
    """Return a new list with *record* replacing any same-id record (append otherwise)."""
    updated = [r for r in records if r.bundle_id != record.bundle_id]
    updated.append(record)
    return updated


def remove_record(
    records: list[InstalledBundleRecord], bundle_id: str
) -> list[InstalledBundleRecord]:
    return [r for r in records if r.bundle_id != bundle_id]


def components_still_needed(
    records: list[InstalledBundleRecord], exclude_bundle_id: str
) -> set[tuple[str, str]]:
    """Set of ``(kind, id)`` component keys required by bundles other than the excluded one."""
    needed: set[tuple[str, str]] = set()
    for record in records:
        if record.bundle_id == exclude_bundle_id:
            continue
        for component in record.contributed_components:
            needed.add((component.kind, component.id))
    return needed


def _component_to_dict(ref: ComponentRef) -> dict[str, Any]:
    data: dict[str, Any] = {"kind": ref.kind, "id": ref.id}
    if ref.version is not None:
        data["version"] = ref.version
    if ref.source is not None:
        data["source"] = ref.source
    if ref.priority is not None:
        data["priority"] = ref.priority
    if ref.strategy is not None:
        data["strategy"] = ref.strategy
    return data


def _component_from_dict(data: Any) -> ComponentRef:
    if not isinstance(data, dict):
        raise BundlerError("Each contributed component must be a mapping.")
    kind = str(data.get("kind", "")).strip()
    cid = str(data.get("id", "")).strip()
    if kind not in COMPONENT_KINDS:
        raise BundlerError(
            f"Corrupt records file: component 'kind' must be one of "
            f"{list(COMPONENT_KINDS)}, got {kind or '<missing>'!r}."
        )
    if not cid:
        raise BundlerError(
            "Corrupt records file: a contributed component is missing its 'id'."
        )
    return ComponentRef(
        kind=kind,
        id=cid,
        version=(str(data["version"]) if data.get("version") else None),
        source=(str(data["source"]) if data.get("source") else None),
        priority=_parse_priority(data.get("priority")),
        strategy=(str(data["strategy"]) if data.get("strategy") else None),
    )


def _parse_priority(raw: Any) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, (int, str)):
        raise BundlerError(f"Component priority must be an integer, got {raw!r}.")
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise BundlerError(
            f"Component priority must be an integer, got {raw!r}."
        ) from None


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
