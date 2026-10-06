"""Validate and select display-only integration catalog release metadata."""

from __future__ import annotations

from typing import Any

from packaging.version import InvalidVersion, Version

from . import IntegrationCatalogError

_RELEASE_FIELDS = frozenset(
    {
        "name",
        "description",
        "author",
        "repository",
        "license",
        "tags",
        "requires",
    }
)
_CURRENT_ONLY = frozenset(
    {
        "version",
        "description",
        "repository",
        "license",
        "tags",
        "requires",
        "provides",
        "download_url",
        "sha256",
        "bundled",
        "verified",
        "releases",
    }
)


def _validated_releases(entry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if "releases" not in entry:
        return {}
    integration_id = entry.get("id", "<unknown>")
    releases = entry["releases"]
    if not isinstance(releases, dict):
        raise IntegrationCatalogError(
            f"Integration '{integration_id}' has an invalid releases mapping."
        )

    current = entry.get("version")
    if not isinstance(current, str) or not current.strip():
        raise IntegrationCatalogError(
            f"Integration '{integration_id}' has releases but no current version."
        )
    try:
        seen = {Version(current)}
    except InvalidVersion:
        raise IntegrationCatalogError(
            f"Integration '{integration_id}' has an invalid current version '{current}'."
        ) from None

    for advertised, metadata in releases.items():
        if not isinstance(advertised, str) or not advertised.strip():
            raise IntegrationCatalogError(
                f"Integration '{integration_id}' has an invalid release version key."
            )
        try:
            normalized = Version(advertised)
        except InvalidVersion:
            raise IntegrationCatalogError(
                f"Integration '{integration_id}' has invalid release version '{advertised}'."
            ) from None
        if normalized in seen:
            raise IntegrationCatalogError(
                f"Integration '{integration_id}' repeats release version '{advertised}'."
            )
        seen.add(normalized)
        if not isinstance(metadata, dict):
            raise IntegrationCatalogError(
                f"Integration '{integration_id}' release '{advertised}' must be an object."
            )
        for field, value in metadata.items():
            if field not in _RELEASE_FIELDS:
                label = (
                    "reserved"
                    if field
                    in {
                        "id",
                        "version",
                        "releases",
                        "_catalog_name",
                        "_install_allowed",
                    }
                    else "unsupported"
                )
                raise IntegrationCatalogError(
                    f"Integration '{integration_id}' release '{advertised}' has {label} field '{field}'."
                )
            if field == "tags":
                valid = isinstance(value, list) and all(
                    isinstance(tag, str) and tag.strip() for tag in value
                )
            elif field == "requires":
                valid = isinstance(value, dict)
            else:
                valid = isinstance(value, str) and (
                    bool(value.strip()) or field == "description"
                )
            if not valid:
                raise IntegrationCatalogError(
                    f"Integration '{integration_id}' release '{advertised}' has invalid {field}."
                )
    return releases


def select_release(entry: dict[str, Any], version: str | None) -> dict[str, Any] | None:
    """Select from the winning source without inheriting current-only metadata."""
    releases = _validated_releases(entry)
    current = entry.get("version")
    if version is None or (
        isinstance(current, str) and current.strip() and version == current
    ):
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
            pass  # Legacy single-release catalogs may use non-PEP 440 versions.
    for advertised, metadata in releases.items():
        if requested == Version(advertised):
            shared = {
                key: value for key, value in entry.items() if key not in _CURRENT_ONLY
            }
            return {**shared, **metadata, "version": advertised}
    return None


def available_versions(entry: dict[str, Any]) -> list[str]:
    """Return current first, then older release spellings in descending order."""
    releases = _validated_releases(entry)
    current = entry.get("version")
    if not isinstance(current, str) or not current:
        return []
    return [current, *sorted(releases, key=Version, reverse=True)]
