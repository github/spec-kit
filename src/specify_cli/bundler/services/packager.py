"""Packager: produce a single versioned distributable artifact from a bundle dir.

``specify bundle build`` zips the manifest, README, and any local assets into
``<id>-<version>.zip``. Build refuses on an invalid manifest, pointing the
author to ``validate``. All file reads are confined within the bundle source
directory (Principle V path confinement).
"""
from __future__ import annotations

import os
import re
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

    # The artifact contract requires a human-facing README.md alongside the
    # manifest; refuse early rather than publish a bundle with no description.
    if not (bundle_dir / "README.md").exists():
        raise BundlerError(
            f"No README.md found in '{bundle_dir}'. Every bundle must ship a "
            "README.md describing it."
        )

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
    # Defense in depth: even though validate_manifest() rejects unsafe ids, make
    # sure a crafted id cannot push the artifact outside the output directory.
    ensure_within(out_dir, artifact_path)

    # If the output dir lives inside the bundle, skip its whole subtree so
    # previously-built artifacts are never re-packaged (keeps builds
    # reproducible and bounded).
    skip_dir = out_dir if out_dir != bundle_dir and _is_within(bundle_dir, out_dir) else None
    # Also skip any prior build artifact for this bundle (e.g. an older
    # <id>-<version>.zip sitting next to bundle.yml), not just the current one.
    # Match only a semver-looking version segment so legitimate assets that
    # merely start with the bundle id (e.g. <id>-assets.zip) are still packaged.
    artifact_re = re.compile(
        rf"^{re.escape(manifest.bundle.id)}-"
        r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?\.zip$"
    )
    files = _collect_files(
        bundle_dir, skip=artifact_path, skip_dir=skip_dir, artifact_re=artifact_re
    )
    with zipfile.ZipFile(artifact_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in files:
            # Confinement: every packaged file must live under bundle_dir.
            ensure_within(bundle_dir, file_path)
            arcname = file_path.relative_to(bundle_dir).as_posix()
            # Fixed timestamp so identical inputs yield a byte-for-byte
            # identical artifact (reproducible builds).
            info = zipfile.ZipInfo(filename=arcname, date_time=_FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            # Reproducible, normalized permissions: preserve executability so
            # bundled scripts (e.g. extension hook scripts) stay runnable after
            # extraction, but collapse to two canonical modes (0755 when any
            # execute bit is set on the source, otherwise 0644) so identical
            # inputs yield a byte-for-byte identical artifact.
            mode = 0o755 if file_path.stat().st_mode & 0o111 else 0o644
            info.external_attr = mode << 16
            archive.writestr(info, file_path.read_bytes())

    return BuildResult(artifact_path=artifact_path, file_count=len(files))


def _is_within(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _collect_files(
    bundle_dir: Path,
    skip: Path,
    skip_dir: Path | None = None,
    artifact_re: re.Pattern[str] | None = None,
) -> list[Path]:
    collected: list[Path] = []
    # followlinks=False so a symlinked directory is never descended into,
    # which would otherwise pull in out-of-tree files and then fail at
    # ensure_within(). Symlinked dirs are pruned from traversal explicitly.
    for root, dirnames, filenames in os.walk(bundle_dir, followlinks=False):
        root_path = Path(root)
        # Prune directories we must not descend into (in-place edit of dirnames).
        dirnames[:] = [
            d
            for d in dirnames
            if d not in EXCLUDE_NAMES and not (root_path / d).is_symlink()
        ]
        if skip_dir is not None and _is_within(skip_dir, root_path):
            dirnames[:] = []
            continue
        for name in filenames:
            path = root_path / name
            if path == skip:
                continue
            if name in EXCLUDE_NAMES:
                continue
            if artifact_re is not None and artifact_re.match(name):
                # A prior build artifact for this bundle — never re-package it.
                continue
            if path.is_symlink():
                # Skip symlinked files to avoid escaping the bundle directory.
                continue
            collected.append(path)
    # Order by the canonical POSIX arcname (the same key build_bundle uses to
    # NAME each member), not by pathlib.Path comparison. Path ordering is
    # platform-dependent (Windows folds case and uses backslash separators),
    # which would lay out zip members differently across build hosts and break
    # the byte-for-byte reproducible-build guarantee even though the member
    # names are identical.
    return sorted(collected, key=lambda p: p.relative_to(bundle_dir).as_posix())
