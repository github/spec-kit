"""Packager: produce a single versioned distributable artifact from a bundle dir.

``specify bundle build`` zips the manifest, README, and any local assets into
``<id>-<version>.zip``. Build refuses on an invalid manifest, pointing the
author to ``validate``. All file reads are confined within the bundle source
directory (Principle V path confinement).
"""
from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path

from .. import BundlerError
from ..lib.yamlio import ensure_within
from ..models.manifest import BundleManifest
from .validator import validate_manifest

# Files/dirs never included in an artifact.
EXCLUDE_NAMES = {".git", "__pycache__", ".DS_Store"}

# Fixed member timestamp (zip epoch) for reproducible, byte-stable artifacts.
_FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


@dataclass
class BuildResult:
    artifact_path: Path
    file_count: int


def build_bundle(
    bundle_dir: Path,
    output_dir: Path | None = None,
) -> BuildResult:
    bundle_dir = Path(bundle_dir).resolve()
    manifest_path = bundle_dir / "bundle.yml"
    if not manifest_path.exists():
        raise BundlerError(f"No bundle.yml found in '{bundle_dir}'.")

    manifest = BundleManifest.from_file(manifest_path)
    report = validate_manifest(manifest)
    if not report.ok:
        raise BundlerError(
            "Refusing to build an invalid manifest. Run 'specify bundle validate' "
            "and fix:\n  - " + "\n  - ".join(report.errors)
        )

    out_dir = Path(output_dir).resolve() if output_dir else bundle_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_name = f"{manifest.bundle.id}-{manifest.bundle.version}.zip"
    artifact_path = out_dir / artifact_name

    # If the output dir lives inside the bundle, skip its whole subtree so
    # previously-built artifacts are never re-packaged (keeps builds
    # reproducible and bounded).
    skip_dir = out_dir if out_dir != bundle_dir and _is_within(bundle_dir, out_dir) else None
    files = _collect_files(bundle_dir, skip=artifact_path, skip_dir=skip_dir)
    with zipfile.ZipFile(artifact_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in files:
            # Confinement: every packaged file must live under bundle_dir.
            ensure_within(bundle_dir, file_path)
            arcname = file_path.relative_to(bundle_dir).as_posix()
            # Fixed timestamp + permissions so identical inputs yield a
            # byte-for-byte identical artifact (reproducible builds).
            info = zipfile.ZipInfo(filename=arcname, date_time=_FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, file_path.read_bytes())

    return BuildResult(artifact_path=artifact_path, file_count=len(files))


def _is_within(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _collect_files(bundle_dir: Path, skip: Path, skip_dir: Path | None = None) -> list[Path]:
    collected: list[Path] = []
    for path in sorted(bundle_dir.rglob("*")):
        if path.is_dir():
            continue
        if path == skip:
            continue
        if skip_dir is not None and _is_within(skip_dir, path):
            continue
        if any(part in EXCLUDE_NAMES for part in path.relative_to(bundle_dir).parts):
            continue
        if path.is_symlink():
            # Skip symlinks to avoid escaping the bundle directory.
            continue
        collected.append(path)
    return collected
