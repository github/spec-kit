"""Exact-release validation and selection for bundle catalog entries."""

from __future__ import annotations

import re
from typing import Any

from packaging.version import InvalidVersion, Version

from .._download_security import is_https_or_localhost_http
from . import BundlerError
from .catalogs import CatalogEntry
from .versioning import is_semver

_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_CURRENT_ONLY = frozenset(
    {
        "version",
        "download_url",
        "sha256",
        "requires",
        "provides",
        "verified",
        "releases",
    }
)
_RESERVED = frozenset({"id", "version", "releases"})


def _raw(entry: CatalogEntry) -> dict[str, Any]:
    return entry.raw if entry.raw is not None else {}


def _release_error(entry: CatalogEntry, version: str, error: BundlerError) -> BundlerError:
    return BundlerError(f"Bundle '{entry.id}' release '{version}' has {error}")


def _validated_releases(entry: CatalogEntry) -> dict[str, dict[str, Any]]:
    """Return checked historical releases or reject an ambiguous entry."""
    raw = _raw(entry)
    if "releases" not in raw:
        return {}
    releases = raw["releases"]
    if not isinstance(releases, dict):
        raise BundlerError(f"Bundle '{entry.id}' has an invalid releases mapping.")

    current = raw.get("version")
    if not isinstance(current, str) or not current.strip():
        raise BundlerError(f"Bundle '{entry.id}' has releases but no current version.")
    if not is_semver(current):
        raise BundlerError(
            f"Bundle '{entry.id}' has an invalid current version '{current}'."
        )
    try:
        seen = {Version(current)}
    except InvalidVersion:
        raise BundlerError(
            f"Bundle '{entry.id}' has an invalid current version '{current}'."
        ) from None

    for advertised, record in releases.items():
        if not isinstance(advertised, str) or not advertised.strip():
            raise BundlerError(
                f"Bundle '{entry.id}' has an invalid release version key."
            )
        if not is_semver(advertised):
            raise BundlerError(
                f"Bundle '{entry.id}' has invalid release version '{advertised}'."
            )
        try:
            normalized = Version(advertised)
        except InvalidVersion:
            raise BundlerError(
                f"Bundle '{entry.id}' has invalid release version '{advertised}'."
            ) from None
        if normalized in seen:
            raise BundlerError(
                f"Bundle '{entry.id}' repeats release version '{advertised}'."
            )
        seen.add(normalized)
        if not isinstance(record, dict):
            raise BundlerError(
                f"Bundle '{entry.id}' release '{advertised}' must be an object."
            )
        if _RESERVED.intersection(record):
            raise BundlerError(
                f"Bundle '{entry.id}' release '{advertised}' contains reserved fields."
            )
        if (
            not isinstance(record.get("download_url"), str)
            or not record["download_url"].strip()
        ):
            raise BundlerError(
                f"Bundle '{entry.id}' release '{advertised}' needs a download_url."
            )
        if not is_https_or_localhost_http(record["download_url"]):
            raise BundlerError(
                f"Bundle '{entry.id}' release '{advertised}' has an invalid "
                "download_url."
            )
        digest = record.get("sha256")
        if isinstance(digest, str):
            digest = digest.strip()
            if digest[:7].lower() == "sha256:":
                digest = digest[7:].strip()
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise BundlerError(
                f"Bundle '{entry.id}' release '{advertised}' needs a SHA-256 digest."
            )
        for field in ("requires", "provides"):
            if field in record and not isinstance(record[field], dict):
                raise BundlerError(
                    f"Bundle '{entry.id}' release '{advertised}' has invalid {field}."
                )
        common = {key: value for key, value in raw.items() if key not in _CURRENT_ONLY}
        try:
            CatalogEntry.from_dict({**common, **record, "version": advertised})
        except BundlerError as exc:
            raise _release_error(entry, advertised, exc) from exc
    return releases


def select_release(entry: CatalogEntry, version: str | None) -> CatalogEntry | None:
    """Select an exact release from one winning catalog entry."""
    releases = _validated_releases(entry)
    current = entry.version
    if version is None or version == current:
        return entry
    try:
        requested = Version(version)
    except InvalidVersion:
        return None
    try:
        if requested == Version(current):
            return entry
    except InvalidVersion:
        # Legacy entries without history may retain older non-PEP-440 spellings.
        pass
    raw = _raw(entry)
    for advertised, record in releases.items():
        if requested == Version(advertised):
            common = {
                key: value for key, value in raw.items() if key not in _CURRENT_ONLY
            }
            return CatalogEntry.from_dict({**common, **record, "version": advertised})
    return None


def available_versions(entry: CatalogEntry) -> list[str]:
    """Return the current version, then historical releases newest first."""
    releases = _validated_releases(entry)
    if not entry.version:
        return []
    return [entry.version, *sorted(releases, key=Version, reverse=True)]
