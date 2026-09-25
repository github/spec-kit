"""Artifact preparation helpers for ``specify extension update``."""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from packaging import version as pkg_version

from .._download_security import safe_extract_archive


@dataclass(frozen=True)
class PreflightResult:
    """Validated manifest-derived outputs needed by the update transaction."""

    command_names: list[str]
    skill_names: list[str]


def _archive_extension_directory(source_dir: Path) -> Path:
    """Package an extension directory as a ZIP archive for the update flow."""
    import zipfile

    fd, tmp_name = tempfile.mkstemp(prefix="speckit-bundled-update-", suffix=".zip")
    try:
        with os.fdopen(fd, "wb") as archive_file:
            with zipfile.ZipFile(archive_file, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(source_dir.rglob("*")):
                    if path.is_symlink():
                        continue
                    if path.is_file():
                        archive.write(path, path.relative_to(source_dir).as_posix())
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    return Path(tmp_name)


def preflight_update_archive(
    manager: Any,
    archive_path: Path,
    extension_id: str,
    available_version: str,
    speckit_version: str,
) -> PreflightResult:
    """Validate an update archive before the installed extension is modified."""
    from . import ExtensionManifest

    with tempfile.TemporaryDirectory(
        prefix="speckit-update-archive-"
    ) as archive_tmpdir:
        extracted_root = Path(archive_tmpdir)
        try:
            safe_extract_archive(archive_path, extracted_root)
        except ValueError as exc:
            if (
                "Conflicting path" in str(exc)
                and "extension.yml" in str(exc).casefold()
            ):
                raise ValueError(
                    "Downloaded extension archive contains multiple "
                    "extension.yml manifests"
                ) from exc
            raise

        top_level = list(extracted_root.iterdir())
        root_manifest_entries = [
            entry
            for entry in top_level
            if entry.name.casefold() == "extension.yml"
        ]
        if any(entry.name != "extension.yml" for entry in root_manifest_entries):
            raise ValueError("Archive must use canonical 'extension.yml' casing")

        canonical_root_manifest = next(
            (
                entry
                for entry in root_manifest_entries
                if entry.name == "extension.yml"
            ),
            None,
        )
        if canonical_root_manifest is not None:
            manifest_path = canonical_root_manifest
        else:
            top_level_dirs = [entry for entry in top_level if entry.is_dir()]
            if len(top_level_dirs) != 1:
                raise ValueError(
                    "Downloaded extension archive must contain exactly "
                    "one top-level directory"
                )
            manifest_root = top_level_dirs[0]
            nested_manifest_entries = [
                entry
                for entry in manifest_root.iterdir()
                if entry.name.casefold() == "extension.yml"
            ]
            if any(entry.name != "extension.yml" for entry in nested_manifest_entries):
                raise ValueError("Archive must use canonical 'extension.yml' casing")
            manifest_path = next(
                (
                    entry
                    for entry in nested_manifest_entries
                    if entry.name == "extension.yml"
                ),
                manifest_root / "extension.yml",
            )

        if not manifest_path.is_file():
            raise ValueError(
                "Downloaded extension archive is missing 'extension.yml'"
            )
        manifest_bytes = manifest_path.read_bytes()
        parsed_manifest = yaml.safe_load(manifest_bytes)
        manifest_data = parsed_manifest if parsed_manifest is not None else {}
        if not isinstance(manifest_data, dict):
            raise ValueError(
                "Invalid extension manifest in downloaded archive: "
                "expected YAML mapping"
            )
        extension_data = manifest_data.get("extension", {})
        if not isinstance(extension_data, dict):
            raise ValueError(
                "Invalid extension manifest in downloaded archive: "
                "expected 'extension' mapping"
            )

    with tempfile.TemporaryDirectory(
        prefix="speckit-update-manifest-"
    ) as manifest_tmpdir:
        manifest_file = Path(manifest_tmpdir) / "extension.yml"
        manifest_file.write_bytes(manifest_bytes)
        preflight_manifest = ExtensionManifest(manifest_file)
        manager.check_compatibility(preflight_manifest, speckit_version)

    if preflight_manifest.id != extension_id:
        raise ValueError(
            f"Extension ID mismatch: expected '{extension_id}', "
            f"got '{preflight_manifest.id}'"
        )

    expected_version = pkg_version.Version(available_version)
    archive_version = pkg_version.Version(preflight_manifest.version)
    if archive_version != expected_version:
        raise ValueError(
            "Extension version mismatch: "
            f"expected '{available_version}', got '{preflight_manifest.version}'"
        )

    manager._validate_install_conflicts(preflight_manifest)
    command_names = list(
        manager._collect_manifest_command_names(preflight_manifest)
    )
    skill_names = list(
        dict.fromkeys(
            manager._skill_name_for_command(command_name)
            for command_name in command_names
        )
    )
    return PreflightResult(command_names=command_names, skill_names=skill_names)
