"""Discovery helpers for ``specify extension update``."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packaging import version as pkg_version
from rich.markup import escape as _escape_markup

from .._console import console
from . import _commands


@dataclass(frozen=True)
class UpdateCandidate:
    """A validated catalog update ready for user confirmation."""

    extension_id: str
    name: str
    installed: str
    available: str
    download_url: str | None
    bundled_dir: Path | None
    catalog_name: str | None


def _bundled_update_source(ext_id: str):
    """Locate the local bundled copy of an extension and its parsed version."""
    from . import ExtensionManifest, ValidationError

    bundled_dir = _commands._locate_bundled_extension(ext_id)
    if bundled_dir is None:
        return None, None
    try:
        manifest = ExtensionManifest(bundled_dir / "extension.yml")
        return bundled_dir, pkg_version.Version(manifest.version)
    except (ValidationError, pkg_version.InvalidVersion, OSError):
        return None, None


def discover_updates(
    manager: Any,
    catalog: Any,
    extension: str | None,
) -> tuple[list[UpdateCandidate], list[str], bool]:
    """Find installable updates and report skipped or blocked entries."""
    installed = manager.list_installed()
    if extension:
        extension_id, _ = _commands._resolve_installed_extension(
            extension, installed, "update"
        )
        extension_ids = [extension_id]
    else:
        extension_ids = [ext["id"] for ext in installed]

    if not extension_ids:
        return [], [], False

    console.print("🔄 Checking for updates...\n")

    updates_available: list[UpdateCandidate] = []
    blocked_updates: list[str] = []

    for ext_id in extension_ids:
        safe_ext_id = _escape_markup(str(ext_id))
        metadata = manager.registry.get(ext_id)
        if (
            metadata is None
            or not isinstance(metadata, dict)
            or "version" not in metadata
        ):
            console.print(
                f"⚠  {safe_ext_id}: Registry entry corrupted or missing (skipping)"
            )
            continue
        try:
            installed_version = pkg_version.Version(metadata["version"])
        except pkg_version.InvalidVersion:
            console.print(
                f"⚠  {safe_ext_id}: Invalid installed version "
                f"'{_escape_markup(str(metadata.get('version')))}' in registry "
                "(skipping)"
            )
            continue

        ext_info = catalog.get_extension_info(ext_id)
        if not ext_info:
            console.print(f"⚠  {safe_ext_id}: Not found in catalog (skipping)")
            continue

        if not ext_info.get("_install_allowed", True):
            console.print(
                f"⚠  {safe_ext_id}: Updates not allowed from "
                f"'{_escape_markup(str(ext_info.get('_catalog_name', 'catalog')))}' "
                "(skipping)"
            )
            continue

        try:
            catalog_version = pkg_version.Version(ext_info["version"])
        except pkg_version.InvalidVersion:
            console.print(
                f"⚠  {safe_ext_id}: Invalid catalog version "
                f"'{_escape_markup(str(ext_info.get('version')))}' (skipping)"
            )
            continue

        if catalog_version <= installed_version:
            console.print(f"✓ {safe_ext_id}: Up to date (v{installed_version})")
            continue

        download_url = ext_info.get("download_url")
        bundled_dir = None
        available_version = catalog_version
        if ext_info.get("bundled") and not download_url:
            bundled_dir, bundled_version = _commands._bundled_update_source(ext_id)
            if bundled_dir is None or bundled_version < catalog_version:
                local_desc = (
                    f"only ships v{bundled_version}"
                    if bundled_dir is not None
                    else "does not ship a local copy"
                )
                console.print(
                    f"⚠  {safe_ext_id}: v{catalog_version} is available, but this "
                    f"spec-kit release {local_desc} — upgrade spec-kit, then rerun "
                    f"'specify extension update'"
                )
                blocked_updates.append(ext_id)
                continue
            available_version = bundled_version

        updates_available.append(
            UpdateCandidate(
                extension_id=ext_id,
                name=ext_info.get("name", ext_id),
                installed=str(installed_version),
                available=str(available_version),
                download_url=download_url,
                bundled_dir=bundled_dir,
                catalog_name=ext_info.get("_catalog_name"),
            )
        )

    return updates_available, blocked_updates, True
