"""Version selection for workflow catalog entries."""

from __future__ import annotations

import re
from typing import Any

from packaging.version import InvalidVersion, Version

from ..._download_security import is_https_or_localhost_http
from ..engine import _is_valid_workflow_version
from ._domain import WorkflowValidationError

_SHA256 = re.compile(r"^(?:sha256:)?[0-9a-fA-F]{64}$", re.IGNORECASE)
_CURRENT_ONLY = frozenset(
    {"version", "url", "sha256", "requires", "bundled", "releases"}
)
_RESERVED = frozenset(
    {"id", "version", "releases", "_catalog_name", "_install_allowed"}
)


def _validated_releases(entry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if "releases" not in entry:
        return {}
    releases = entry["releases"]
    workflow_id = entry.get("id", "<unknown>")
    if not isinstance(releases, dict):
        raise WorkflowValidationError(
            f"Workflow '{workflow_id}' has an invalid releases mapping."
        )

    current = entry.get("version")
    if not isinstance(current, str) or not current.strip():
        raise WorkflowValidationError(
            f"Workflow '{workflow_id}' has releases but no current version."
        )
    if not _is_valid_workflow_version(current):
        raise WorkflowValidationError(
            f"Workflow '{workflow_id}' has an invalid current version '{current}'."
        )
    try:
        seen = {Version(current)}
    except InvalidVersion:
        raise WorkflowValidationError(
            f"Workflow '{workflow_id}' has an invalid current version '{current}'."
        ) from None

    for release_version, record in releases.items():
        if not isinstance(release_version, str) or not release_version.strip():
            raise WorkflowValidationError(
                f"Workflow '{workflow_id}' has an invalid release version key."
            )
        if not _is_valid_workflow_version(release_version):
            raise WorkflowValidationError(
                f"Workflow '{workflow_id}' has invalid release version '{release_version}'."
            )
        try:
            normalized = Version(release_version)
        except InvalidVersion:
            raise WorkflowValidationError(
                f"Workflow '{workflow_id}' has invalid release version '{release_version}'."
            ) from None
        if normalized in seen:
            raise WorkflowValidationError(
                f"Workflow '{workflow_id}' repeats release version '{release_version}'."
            )
        seen.add(normalized)
        if not isinstance(record, dict):
            raise WorkflowValidationError(
                f"Workflow '{workflow_id}' release '{release_version}' must be an object."
            )
        if _RESERVED.intersection(record):
            raise WorkflowValidationError(
                f"Workflow '{workflow_id}' release '{release_version}' contains reserved fields."
            )
        if not isinstance(record.get("url"), str) or not record["url"].strip():
            raise WorkflowValidationError(
                f"Workflow '{workflow_id}' release '{release_version}' needs a url."
            )
        if not is_https_or_localhost_http(record["url"]):
            raise WorkflowValidationError(
                f"Workflow '{workflow_id}' release '{release_version}' has an invalid URL."
            )
        if not isinstance(record.get("sha256"), str) or not _SHA256.fullmatch(
            record["sha256"]
        ):
            raise WorkflowValidationError(
                f"Workflow '{workflow_id}' release '{release_version}' needs a SHA-256 digest."
            )
        if "requires" in record and not isinstance(record["requires"], dict):
            raise WorkflowValidationError(
                f"Workflow '{workflow_id}' release '{release_version}' has invalid requires."
            )
    return releases


def select_release(entry: dict[str, Any], version: str | None) -> dict[str, Any] | None:
    """Select from the winning source, preserving the advertised version."""
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
            pass  # Legacy entries without history can use non-PEP-440 versions.
    for advertised, record in releases.items():
        if requested == Version(advertised):
            common = {
                key: value for key, value in entry.items() if key not in _CURRENT_ONLY
            }
            return {**common, **record, "version": advertised}
    return None


def available_versions(entry: dict[str, Any]) -> list[str]:
    """Current first, followed by historical versions newest to oldest."""
    releases = _validated_releases(entry)
    current = entry.get("version")
    if not isinstance(current, str) or not current:
        return []
    return [current, *sorted(releases, key=Version, reverse=True)]
