"""Validate and select releases from a preset catalog entry."""

from __future__ import annotations

import re
from typing import Any

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from .._download_security import is_https_or_localhost_http
from ._manifest import PresetError, PresetManifest, PresetValidationError

_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_CURRENT_FIELDS = frozenset(
    {"version", "download_url", "sha256", "requires", "provides", "bundled", "releases"}
)


def _validated_releases(entry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if "releases" not in entry:
        return {}
    pack_id = entry.get("id", "<unknown>")
    releases = entry["releases"]
    if not isinstance(releases, dict):
        raise PresetError(f"Preset '{pack_id}' has an invalid releases mapping.")
    current = entry.get("version")
    if not isinstance(current, str) or not current.strip():
        raise PresetError(f"Preset '{pack_id}' has releases but no current version.")
    try:
        current_version = Version(current)
    except InvalidVersion:
        raise PresetError(
            f"Preset '{pack_id}' has invalid current version '{current}'."
        ) from None

    seen = {current_version}
    for release_version, record in releases.items():
        if not isinstance(release_version, str) or not release_version.strip():
            raise PresetError(f"Preset '{pack_id}' has an invalid release version key.")
        try:
            parsed = Version(release_version)
        except InvalidVersion:
            raise PresetError(
                f"Preset '{pack_id}' has invalid release version '{release_version}'."
            ) from None
        if parsed in seen:
            raise PresetError(
                f"Preset '{pack_id}' repeats release version '{release_version}'."
            )
        seen.add(parsed)
        if not isinstance(record, dict):
            raise PresetError(
                f"Preset '{pack_id}' release '{release_version}' must be an object."
            )
        if any(
            field in record
            for field in (
                "id",
                "version",
                "releases",
                "_catalog_name",
                "_install_allowed",
            )
        ):
            raise PresetError(
                f"Preset '{pack_id}' release '{release_version}' contains reserved fields."
            )
        if (
            not isinstance(record.get("download_url"), str)
            or not record["download_url"].strip()
        ):
            raise PresetError(
                f"Preset '{pack_id}' release '{release_version}' needs a download_url."
            )
        if not is_https_or_localhost_http(record["download_url"]):
            raise PresetError(
                f"Preset '{pack_id}' release '{release_version}' has an invalid download_url."
            )
        digest = record.get("sha256")
        if isinstance(digest, str):
            digest = digest.strip()
            if digest[:7].lower() == "sha256:":
                digest = digest[7:].strip()
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise PresetError(
                f"Preset '{pack_id}' release '{release_version}' needs a SHA-256 digest."
            )
        for field in ("requires", "provides"):
            if field in record and not isinstance(record[field], dict):
                raise PresetError(
                    f"Preset '{pack_id}' release '{release_version}' has invalid {field}."
                )
        requires = record.get("requires", {})
        if "speckit_version" in requires:
            specifier = requires["speckit_version"]
            if not isinstance(specifier, str) or not specifier.strip():
                raise PresetError(
                    f"Preset '{pack_id}' release '{release_version}' has invalid requires.speckit_version."
                )
            try:
                SpecifierSet(specifier)
            except InvalidSpecifier:
                raise PresetError(
                    f"Preset '{pack_id}' release '{release_version}' has invalid requires.speckit_version."
                ) from None
        if "extensions" in requires:
            try:
                PresetManifest._validate_requires_extensions(requires["extensions"])
            except PresetValidationError as exc:
                raise PresetError(
                    f"Preset '{pack_id}' release '{release_version}' has {exc}"
                ) from exc
        if "bundled" in record and not isinstance(record["bundled"], bool):
            raise PresetError(
                f"Preset '{pack_id}' release '{release_version}' has invalid bundled."
            )
    return releases


def select_release(entry: dict[str, Any], version: str | None) -> dict[str, Any] | None:
    """Return current or exact historical metadata from the winning entry."""
    releases = _validated_releases(entry)
    current = entry.get("version")
    if version is None or version == current:
        return entry
    try:
        requested = Version(version)
    except (InvalidVersion, TypeError):
        return None
    if isinstance(current, str):
        try:
            if requested == Version(current):
                return entry
        except InvalidVersion:
            pass  # Legacy entries may use a non-PEP-440 current version.
    for advertised, record in releases.items():
        if requested == Version(advertised):
            common = {
                key: value for key, value in entry.items() if key not in _CURRENT_FIELDS
            }
            return {**common, **record, "version": advertised}
    return None


def available_versions(entry: dict[str, Any]) -> list[str]:
    """Return advertised current first, then historical versions descending."""
    releases = _validated_releases(entry)
    current = entry.get("version")
    if not isinstance(current, str) or not current:
        return []
    return [current, *sorted(releases, key=Version, reverse=True)]
