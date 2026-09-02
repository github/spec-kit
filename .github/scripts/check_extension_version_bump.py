#!/usr/bin/env python3
"""Fail a PR that changes bundled extension content without a version bump.

Update offers from `specify extension update` are version-driven: an
extension is offered (and installed) only when the semver in
`extensions/catalog.json` exceeds the installed copy's registered
version. A content change shipped without a version bump is therefore
never delivered automatically (#4345) — a bump is what makes a change
actually reach existing installs, and this guard is what makes the bump
non-optional.

This check enforces two invariants on the extensions listed in
`extensions/catalog.json`:

1. Any change to a file under `extensions/<id>/` must increase the
   `version:` in that extension's `extension.yml` (PEP 440 comparison,
   the same semantics `extension update` uses).
2. The `version` in `extensions/catalog.json` must equal the manifest's
   `extension.version` (the catalog is what update checks compare
   against, and the update preflight rejects a manifest whose version
   differs from the catalog's).

Usage:
    check_extension_version_bump.py BASE_REF [HEAD_REF]

BASE_REF is a git ref/SHA for the PR base (must be fetchable with
`git show`). HEAD_REF defaults to the working tree's HEAD. Exits 0 when
all invariants hold, 1 otherwise, printing one line per violation.

Extensions under `extensions/` that are not in the catalog (the
`selftest` fixture and the `template` scaffold) are exempt: no update
flow is driven by their versions.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import PurePosixPath

import yaml
from packaging.version import InvalidVersion, Version

EXTENSIONS_ROOT = "extensions"
CATALOG_PATH = f"{EXTENSIONS_ROOT}/catalog.json"


def _changed_paths(base_ref: str, head_ref: str) -> list[str]:
    """Paths under extensions/ that differ between *base_ref* and *head_ref*.

    Uses NUL-delimited output (``-z``): without it git C-quotes any path
    containing non-ASCII or control characters (``"extensions/x/caf\\303\\251"``,
    quotes included), so the leading component would no longer equal
    ``extensions`` and that change would silently escape the guard. Paths
    are decoded with surrogateescape so an undecodable byte can never crash
    the check; only the ASCII ``extensions/<id>/`` prefix is interpreted.
    """
    raw = subprocess.run(
        [
            "git", "diff", "--name-only", "-z", "--no-renames",
            base_ref, head_ref, "--", EXTENSIONS_ROOT,
        ],
        check=True,
        capture_output=True,
    ).stdout
    return [
        chunk.decode("utf-8", errors="surrogateescape")
        for chunk in raw.split(b"\0")
        if chunk
    ]


def _show(ref: str, path: str) -> str | None:
    """Return the file's content at *ref*, or None when absent there."""
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"], capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else None


def _manifest_version(manifest_text: str, origin: str) -> str:
    data = yaml.safe_load(manifest_text)
    if not isinstance(data, dict) or not isinstance(data.get("extension"), dict):
        raise ValueError(f"{origin}: manifest is not a mapping with an 'extension' block")
    version = data["extension"].get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError(f"{origin}: extension.version is missing or not a string")
    return version.strip()


def main(argv: list[str]) -> int:
    if len(argv) < 2 or len(argv) > 3:
        print(__doc__, file=sys.stderr)
        return 2
    base_ref = argv[1]
    head_ref = argv[2] if len(argv) == 3 else "HEAD"

    catalog_text = _show(head_ref, CATALOG_PATH)
    if catalog_text is None:
        print(f"::error::{CATALOG_PATH} is missing at {head_ref}")
        return 1
    catalog = json.loads(catalog_text)
    catalog_entries = catalog.get("extensions", {})

    errors: list[str] = []

    # -- Invariant 1: content change requires a version bump ---------------
    changed_ids = {
        parts[1]
        for path in _changed_paths(base_ref, head_ref)
        if len(parts := PurePosixPath(path).parts) >= 3 and parts[0] == EXTENSIONS_ROOT
    }

    for ext_id in sorted(changed_ids):
        if ext_id not in catalog_entries:
            continue  # not driven by `extension update` (selftest, template)
        manifest_path = f"{EXTENSIONS_ROOT}/{ext_id}/extension.yml"
        head_manifest = _show(head_ref, manifest_path)
        if head_manifest is None:
            continue  # extension removed in this PR
        base_manifest = _show(base_ref, manifest_path)
        if base_manifest is None:
            continue  # new extension; any initial version is fine
        try:
            base_version = _manifest_version(base_manifest, f"{base_ref}:{manifest_path}")
            head_version = _manifest_version(head_manifest, f"{head_ref}:{manifest_path}")
        except ValueError as exc:
            errors.append(str(exc))
            continue

        # Compare with the same PEP 440 semantics the extension update and
        # install code use (packaging.version), so prereleases and other
        # accepted forms cannot bypass the guard (e.g. 2.0.0 -> 1.0.0rc1 is
        # a downgrade). Unparseable versions fail closed.
        try:
            base_parsed = Version(base_version)
            head_parsed = Version(head_version)
        except InvalidVersion as exc:
            errors.append(
                f"{manifest_path}: could not compare versions "
                f"{base_version!r} -> {head_version!r}: {exc}"
            )
            continue
        if head_parsed <= base_parsed:
            errors.append(
                f"{manifest_path}: files under {EXTENSIONS_ROOT}/{ext_id}/ changed but "
                f"extension.version did not increase ({base_version} -> {head_version}). "
                f"Installed copies only receive changes when the version is bumped."
            )

    # -- Invariant 2: catalog.json version matches the manifest ------------
    for ext_id, entry in sorted(catalog_entries.items()):
        manifest_path = f"{EXTENSIONS_ROOT}/{ext_id}/extension.yml"
        head_manifest = _show(head_ref, manifest_path)
        if head_manifest is None:
            continue  # catalog-only entry (e.g. hosted elsewhere)
        try:
            manifest_version = _manifest_version(head_manifest, f"{head_ref}:{manifest_path}")
        except ValueError as exc:
            errors.append(str(exc))
            continue
        catalog_version = entry.get("version")
        if catalog_version != manifest_version:
            errors.append(
                f"{CATALOG_PATH}: entry '{ext_id}' has version {catalog_version!r} but "
                f"{manifest_path} declares {manifest_version!r}. `extension update` "
                f"compares against the catalog, so the two must move together."
            )

    for error in errors:
        print(f"::error::{error}")
    if not errors:
        print("Extension version guard: all invariants hold.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
