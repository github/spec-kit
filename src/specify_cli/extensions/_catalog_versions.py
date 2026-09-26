"""Exact-version selection for extension catalog entries.

Legacy entries advertise one release at the top level. A versioned entry keeps
that current release unchanged for older clients and adds historical releases
under ``releases``. Historical records must carry their own URL and digest; a
new current release must never supply either for an older version by accident.
"""

from __future__ import annotations

import re
from typing import Any

from packaging.version import InvalidVersion, Version

from . import ExtensionError

_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_CURRENT_ONLY = frozenset(
    {
        "version",
        "download_url",
        "sha256",
        "requires",
        "provides",
        "bundled",
        "verified",
        "releases",
    }
)


def _validated_releases(entry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return a checked history, or reject an ambiguous catalog entry."""
    if "releases" not in entry:
        return {}
    releases = entry["releases"]
    extension_id = entry.get("id", "<unknown>")
    if not isinstance(releases, dict):
        raise ExtensionError(
            f"Extension '{extension_id}' has an invalid releases mapping."
        )

    current = entry.get("version")
    if not isinstance(current, str) or not current.strip():
        raise ExtensionError(
            f"Extension '{extension_id}' has releases but no current version."
        )
    try:
        normalized_current = Version(current)
    except InvalidVersion:
        raise ExtensionError(
            f"Extension '{extension_id}' has an invalid current version '{current}'."
        ) from None

    seen = {normalized_current}
    for release_version, record in releases.items():
        if not isinstance(release_version, str) or not release_version.strip():
            raise ExtensionError(
                f"Extension '{extension_id}' has an invalid release version key."
            )
        try:
            normalized = Version(release_version)
        except InvalidVersion:
            raise ExtensionError(
                f"Extension '{extension_id}' has invalid release version '{release_version}'."
            ) from None
        if normalized in seen:
            raise ExtensionError(
                f"Extension '{extension_id}' repeats release version '{release_version}'."
            )
        seen.add(normalized)
        if not isinstance(record, dict):
            raise ExtensionError(
                f"Extension '{extension_id}' release '{release_version}' must be an object."
            )
        if any(
            key in record
            for key in (
                "id",
                "version",
                "releases",
                "_catalog_name",
                "_install_allowed",
            )
        ):
            raise ExtensionError(
                f"Extension '{extension_id}' release '{release_version}' contains reserved fields."
            )
        if (
            not isinstance(record.get("download_url"), str)
            or not record["download_url"].strip()
        ):
            raise ExtensionError(
                f"Extension '{extension_id}' release '{release_version}' needs a download_url."
            )
        if not isinstance(record.get("sha256"), str) or not _SHA256.fullmatch(
            record["sha256"]
        ):
            raise ExtensionError(
                f"Extension '{extension_id}' release '{release_version}' needs a SHA-256 digest."
            )
        for field in ("requires", "provides"):
            if field in record and not isinstance(record[field], dict):
                raise ExtensionError(
                    f"Extension '{extension_id}' release '{release_version}' has invalid {field}."
                )

    return releases


def select_release(entry: dict[str, Any], version: str | None) -> dict[str, Any] | None:
    """Select from the winning catalog entry without consulting lower sources.

    ``None`` is returned when the requested version is absent. Callers can then
    report a missing historical release without falling through to another
    catalog or silently substituting the current release.
    """
    releases = _validated_releases(entry)
    current = entry.get("version")
    if version is None or version == current:
        return entry
    try:
        requested = Version(version)
    except InvalidVersion:
        return None
    if isinstance(current, str):
        try:
            if requested == Version(current):
                return entry
        except InvalidVersion:
            # Legacy entries without history are still selectable by exact
            # spelling above, even if their version is not PEP 440 compliant.
            pass
    for advertised, record in releases.items():
        if requested == Version(advertised):
            common = {
                key: value for key, value in entry.items() if key not in _CURRENT_ONLY
            }
            return {**common, **record, "version": advertised}
    return None


def available_versions(entry: dict[str, Any]) -> list[str]:
    """Current version first, then historical versions in descending order."""
    releases = _validated_releases(entry)
    current = entry.get("version")
    if not isinstance(current, str) or not current:
        return []
    return [current, *sorted(releases, key=Version, reverse=True)]
