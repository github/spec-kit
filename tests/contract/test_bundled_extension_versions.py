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
BUNDLES_ROOT = REPO_ROOT / "bundles"


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


def _firstparty_bundle_component_pins() -> list[tuple[str, str, str, str]]:
    """Pinned components from the published first-party bundle sources."""
    pins = []
    for manifest_path in sorted(BUNDLES_ROOT.glob("*/bundle.yml")):
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        for kind, entries in (data.get("provides") or {}).items():
            if kind == "bundles":
                continue
            for entry in entries or []:
                if kind == "steps" and not entry.get("version"):
                    continue
                pins.append(
                    (manifest_path.parent.name, kind, entry["id"], str(entry.get("version")))
                )
    return pins


def test_firstparty_bundles_pin_components():
    assert _firstparty_bundle_component_pins(), "expected component pins in bundles/"


@pytest.mark.parametrize("optional_version", [{}, {"version": None}, {"version": ""}])
def test_firstparty_bundle_pins_skip_unpinned_steps(tmp_path, monkeypatch, optional_version):
    from specify_cli.bundles.manifest import BundleManifest
    from tests.specify_cli.bundles.helpers import valid_manifest_dict, write_manifest

    data = valid_manifest_dict()
    data["provides"]["steps"] = [
        {"id": "unpinned", **optional_version},
        {"id": "pinned", "version": "1.3.0"},
    ]
    assert BundleManifest.from_dict(data).structural_errors() == []
    write_manifest(tmp_path / "demo-bundle", data)
    monkeypatch.setitem(globals(), "BUNDLES_ROOT", tmp_path)

    assert _firstparty_bundle_component_pins() == [
        ("demo-bundle", "extensions", "ext-a", "1.0.0"),
        ("demo-bundle", "presets", "preset-a", "2.0.0"),
        ("demo-bundle", "steps", "pinned", "1.3.0"),
        ("demo-bundle", "workflows", "wf-a", "0.3.0"),
    ]


@pytest.mark.parametrize("kind", ["extensions", "presets", "steps", "workflows"])
def test_firstparty_bundle_pins_retain_invalid_versions(tmp_path, monkeypatch, kind):
    from tests.specify_cli.bundles.helpers import valid_manifest_dict, write_manifest

    data = valid_manifest_dict(provides={kind: [{"id": "invalid", "version": "bad"}]})
    write_manifest(tmp_path / "demo-bundle", data)
    monkeypatch.setitem(globals(), "BUNDLES_ROOT", tmp_path)

    pins = _firstparty_bundle_component_pins()
    assert pins == [("demo-bundle", kind, "invalid", "bad")]
    with pytest.raises(InvalidVersion):
        Version(pins[0][3])


@pytest.mark.parametrize(
    "bundle_name,kind,component_id,pinned",
    _firstparty_bundle_component_pins(),
    ids=lambda v: v if isinstance(v, str) else str(v),
)
def test_firstparty_bundle_pins_match_bundled_manifest(
    bundle_name: str, kind: str, component_id: str, pinned: str
):
    """Check real first-party pins rather than synthetic or illustrative bundles."""
    manifest_path = REPO_ROOT / kind / component_id / f"{kind[:-1]}.yml"
    assert manifest_path.is_file(), f"first-party component manifest missing: {manifest_path}"
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest_version = str(data[kind[:-1]]["version"])
    assert Version(pinned) == Version(manifest_version), (
        f"bundles/{bundle_name}/bundle.yml pins {kind}:{component_id} to {pinned} but "
        f"{manifest_path.relative_to(REPO_ROOT)} declares {manifest_version}; the bundler "
        f"requires compatible pins for installation"
    )
