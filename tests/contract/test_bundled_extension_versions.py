"""Contract tests: bundled extension versions must stay in sync with the catalog.

``specify extension update`` decides whether an installed extension needs
updating by comparing the semver in ``extensions/catalog.json`` against the
installed copy's registered version, and its preflight rejects a manifest
whose version differs from the catalog's. A catalog entry that drifts from
its ``extension.yml`` therefore either hides updates from every installed
copy or makes every offered update fail validation (#4345).

The companion "content change requires a version bump" rule needs the git
diff of a PR and lives in CI
(``.github/scripts/check_extension_version_bump.py`` via the
``extension-version-guard.yml`` workflow); this test enforces the half that
is checkable from a plain working tree.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from packaging.version import InvalidVersion, Version

REPO_ROOT = Path(__file__).parents[2]
EXTENSIONS_ROOT = REPO_ROOT / "extensions"
EXAMPLE_BUNDLES_ROOT = REPO_ROOT / "examples" / "bundles"


def _catalog_entries() -> dict[str, dict]:
    catalog = json.loads((EXTENSIONS_ROOT / "catalog.json").read_text(encoding="utf-8"))
    return catalog["extensions"]


def _manifest_version(ext_id: str) -> str:
    manifest_path = EXTENSIONS_ROOT / ext_id / "extension.yml"
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    return data["extension"]["version"]


def test_catalog_lists_extensions():
    assert _catalog_entries(), "expected at least one extension in extensions/catalog.json"


@pytest.mark.parametrize("ext_id", sorted(_catalog_entries()))
def test_catalog_version_matches_manifest(ext_id: str):
    entry = _catalog_entries()[ext_id]
    manifest_path = EXTENSIONS_ROOT / ext_id / "extension.yml"
    if not manifest_path.is_file():
        pytest.skip(f"'{ext_id}' has no in-repo extension directory")
    assert entry.get("version") == _manifest_version(ext_id), (
        f"extensions/catalog.json entry '{ext_id}' and {manifest_path.relative_to(REPO_ROOT)} "
        f"declare different versions - `specify extension update` compares against the "
        f"catalog, so the two must move together"
    )


@pytest.mark.parametrize("ext_id", sorted(_catalog_entries()))
def test_bundled_entries_ship_an_extension_directory(ext_id: str):
    entry = _catalog_entries()[ext_id]
    if not entry.get("bundled"):
        pytest.skip(f"'{ext_id}' is not marked bundled")
    assert (EXTENSIONS_ROOT / ext_id / "extension.yml").is_file(), (
        f"catalog marks '{ext_id}' as bundled but extensions/{ext_id}/extension.yml is missing"
    )


@pytest.mark.parametrize("ext_id", sorted(_catalog_entries()))
def test_catalog_version_is_valid_pep440(ext_id: str):
    """`extension update` parses each catalog version with packaging and skips
    entries it cannot parse, so every entry - bundled or hosted - must carry
    a valid version, independent of whether it has an in-repo directory."""
    version = _catalog_entries()[ext_id].get("version")
    assert isinstance(version, str) and version.strip(), (
        f"extensions/catalog.json entry '{ext_id}' has no string version"
    )
    try:
        Version(version)
    except InvalidVersion as exc:
        pytest.fail(
            f"extensions/catalog.json entry '{ext_id}' version {version!r} is not a valid "
            f"PEP 440 version ({exc}); `extension update` would skip it"
        )


def _example_bundle_extension_pins() -> list[tuple[str, str, str]]:
    """(bundle name, extension id, pinned version) for every example bundle."""
    pins = []
    for manifest_path in sorted(EXAMPLE_BUNDLES_ROOT.glob("*/bundle.yml")):
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        for entry in (data.get("provides") or {}).get("extensions") or []:
            pins.append((manifest_path.parent.name, entry["id"], str(entry.get("version"))))
    return pins


def test_example_bundles_pin_extensions():
    assert _example_bundle_extension_pins(), "expected at least one extension pin in examples/bundles"


@pytest.mark.parametrize(
    "bundle_name,ext_id,pinned",
    _example_bundle_extension_pins(),
    ids=lambda v: v if isinstance(v, str) else str(v),
)
def test_example_bundle_pins_match_bundled_manifest(bundle_name: str, ext_id: str, pinned: str):
    """``BundleExtensionPrimitive`` refuses to install when the resolved
    extension version differs from the bundle's pin, so an example bundle that
    still pins a bundled extension's previous version fails for every user who
    installs it. Test fixtures derive their pins from the bundled manifest and
    therefore cannot catch this; the shipped examples must be checked directly."""
    manifest_path = EXTENSIONS_ROOT / ext_id / "extension.yml"
    if not manifest_path.is_file():
        pytest.skip(f"'{ext_id}' is not a bundled extension; pin resolves via the catalog at install time")
    manifest_version = _manifest_version(ext_id)
    assert Version(pinned) == Version(manifest_version), (
        f"examples/bundles/{bundle_name}/bundle.yml pins '{ext_id}' to {pinned} but "
        f"{manifest_path.relative_to(REPO_ROOT)} declares {manifest_version}; the bundler "
        f"enforces exact pins, so installing this example would fail"
    )
