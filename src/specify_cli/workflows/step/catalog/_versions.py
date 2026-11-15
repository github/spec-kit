"""Release selection for step catalog entries."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

from packaging.version import InvalidVersion, Version

from ._domain import StepCatalogError

_DIGEST = re.compile(r"[0-9a-fA-F]{64}\Z")
_CURRENT_ONLY = frozenset(
    {
        "version",
        "url",
        "step_yml_url",
        "init_url",
        "extra_files",
        "sha256",
        "requires",
        "provides",
        "releases",
    }
)


def validate_checksums(entry: dict[str, Any], step_id: str, *, required: bool) -> None:
    """Check that a release pins exactly the files its installer downloads."""
    hashes = entry.get("sha256")
    if hashes is None and not required:
        return
    files = entry.get("extra_files", {})
    if not isinstance(files, dict) or any(
        not isinstance(path, str)
        or not path.strip()
        or "\\" in path
        or any(part in ("", ".", "..") for part in path.split("/"))
        or PurePosixPath(path).is_absolute()
        or path.casefold() in ("step.yml", "__init__.py")
        or not isinstance(url, str)
        or not url.strip()
        for path, url in files.items()
    ):
        raise StepCatalogError(f"Step '{step_id}' has invalid extra_files.")
    expected = {"step.yml", "__init__.py", *files}
    if (
        not isinstance(hashes, dict)
        or hashes.keys() != expected
        or any(
            not isinstance(value, str) or not _DIGEST.fullmatch(value)
            for value in hashes.values()
        )
    ):
        raise StepCatalogError(
            f"Step '{step_id}' needs SHA-256 digests for exactly {sorted(expected)}."
        )


def _validated_releases(
    entry: dict[str, Any], step_id: str
) -> dict[str, dict[str, Any]]:
    if "releases" not in entry:
        return {}
    releases = entry["releases"]
    if not isinstance(releases, dict):
        raise StepCatalogError(f"Step '{step_id}' has an invalid releases mapping.")
    if entry.get("id", step_id) != step_id:
        raise StepCatalogError(f"Step '{step_id}' has a mismatched catalog ID.")
    current = entry.get("version")
    if not isinstance(current, str) or not current.strip():
        raise StepCatalogError(f"Step '{step_id}' has releases but no current version.")
    try:
        seen = {Version(current)}
    except InvalidVersion:
        raise StepCatalogError(
            f"Step '{step_id}' has invalid current version '{current}'."
        ) from None
    for release_version, record in releases.items():
        if not isinstance(release_version, str) or not release_version.strip():
            raise StepCatalogError(
                f"Step '{step_id}' has an invalid release version key."
            )
        try:
            normalized = Version(release_version)
        except InvalidVersion:
            raise StepCatalogError(
                f"Step '{step_id}' has invalid release version '{release_version}'."
            ) from None
        if normalized in seen:
            raise StepCatalogError(
                f"Step '{step_id}' repeats release version '{release_version}'."
            )
        seen.add(normalized)
        if not isinstance(record, dict):
            raise StepCatalogError(
                f"Step '{step_id}' release '{release_version}' must be an object."
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
            raise StepCatalogError(
                f"Step '{step_id}' release '{release_version}' "
                "contains reserved fields."
            )
        url = record.get("step_yml_url", record.get("url"))
        if (
            not isinstance(url, str)
            or not url.strip()
            or (
                "url" in record
                and "step_yml_url" in record
                and record["url"] != record["step_yml_url"]
            )
        ):
            raise StepCatalogError(
                f"Step '{step_id}' release '{release_version}' needs a step.yml URL."
            )
        init_url = record.get("init_url")
        if (
            init_url is not None
            and (not isinstance(init_url, str) or not init_url.strip())
        ) or (init_url is None and not url.endswith("step.yml")):
            raise StepCatalogError(
                f"Step '{step_id}' release '{release_version}' "
                "needs an __init__.py URL."
            )
        for field in ("requires", "provides"):
            if field in record and not isinstance(record[field], dict):
                raise StepCatalogError(
                    f"Step '{step_id}' release '{release_version}' has invalid {field}."
                )
        validate_checksums(record, step_id, required=True)
    return releases


def select_release(
    entry: dict[str, Any], step_id: str, version: str | None
) -> dict[str, Any] | None:
    """Select a release from the winning entry; never consult another source."""
    releases = _validated_releases(entry, step_id)
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
            pass  # Legacy versions still support exact spelling above.
    for advertised, record in releases.items():
        if requested == Version(advertised):
            common = {
                key: value for key, value in entry.items() if key not in _CURRENT_ONLY
            }
            return {**common, **record, "version": advertised}
    return None


def available_versions(entry: dict[str, Any], step_id: str) -> list[str]:
    """List the advertised current version before historical versions."""
    releases = _validated_releases(entry, step_id)
    current = entry.get("version")
    if not isinstance(current, str) or not current:
        return []
    return [current, *sorted(releases, key=Version, reverse=True)]
