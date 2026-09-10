"""Consistency tests for the first-party bundle catalog and manifests.

``_validate_catalog_manifest`` enforces that a bundle manifest's ``bundle.id``
and ``bundle.version`` match the catalog entry that pointed to it. This test
locks that relationship in at the source files so it cannot drift without
failing CI.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parents[2]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _extension_version(extension_id: str) -> str:
    manifest = _read_yaml(REPO_ROOT / "extensions" / extension_id / "extension.yml")
    return str(manifest["extension"]["version"])


def _workflow_version(workflow_id: str) -> str:
    manifest = _read_yaml(REPO_ROOT / "workflows" / workflow_id / "workflow.yml")
    return str(manifest["workflow"]["version"])


def _manifest_component_versions(bundle_id: str) -> dict[tuple[str, str], str]:
    """Return {(kind, id): version, ...} for pinned components in a bundle manifest."""
    manifest = _read_yaml(REPO_ROOT / "bundles" / bundle_id / "bundle.yml")
    provides = manifest.get("provides", {})
    versions: dict[tuple[str, str], str] = {}
    for kind in ("extensions", "presets", "steps", "workflows"):
        for ref in provides.get(kind, []):
            if "version" in ref:
                versions[(kind.rstrip("s"), ref["id"])] = str(ref["version"])
    return versions


def test_firstparty_catalog_matches_manifests():
    catalog = _read_json(REPO_ROOT / "bundles" / "catalog.json")

    for bundle_id, entry in catalog["bundles"].items():
        manifest = _read_yaml(REPO_ROOT / "bundles" / bundle_id / "bundle.yml")
        meta = manifest["bundle"]

        assert entry["id"] == bundle_id, (
            f"catalog key '{bundle_id}' does not match entry id '{entry['id']}'"
        )
        assert meta["id"] == bundle_id, (
            f"manifest id '{meta['id']}' does not match catalog key '{bundle_id}'"
        )
        assert entry["version"] == meta["version"], (
            f"catalog version for '{bundle_id}' ({entry['version']}) does not match "
            f"manifest version ({meta['version']})"
        )


def _workflow_catalog_entry(workflow_id: str) -> dict:
    catalog = _read_json(REPO_ROOT / "workflows" / "catalog.json")
    entry = catalog["workflows"].get(workflow_id)
    assert entry is not None, (
        f"workflow '{workflow_id}' is missing from workflows/catalog.json"
    )
    return entry


def test_firstparty_workflow_catalog_entries_match_shipped_yamls():
    """workflows/catalog.json entries must match the shipped workflow YAMLs.

    ``specify workflow add`` resolves a catalog entry by fetching its ``url``
    and then comparing the downloaded manifest's ``version`` against the
    catalog's — a stale entry version or URL makes the install fail (or worse,
    serve an old workflow). Lock id, version, and URL in at the source files so
    they cannot drift without failing CI.
    """
    for workflow_id in ("speckit", "bugfix", "assess"):
        entry = _workflow_catalog_entry(workflow_id)
        manifest = _read_yaml(REPO_ROOT / "workflows" / workflow_id / "workflow.yml")
        meta = manifest["workflow"]

        assert entry["id"] == workflow_id, (
            f"catalog entry id '{entry['id']}' does not match catalog key "
            f"'{workflow_id}'"
        )
        assert meta["id"] == workflow_id, (
            f"workflows/{workflow_id}/workflow.yml declares id '{meta['id']}', "
            f"expected '{workflow_id}'"
        )
        assert entry["version"] == str(meta["version"]), (
            f"catalog version for workflow '{workflow_id}' ({entry['version']}) "
            f"does not match the shipped workflow.yml version "
            f"({meta['version']})"
        )
        assert entry["url"] == (
            "https://raw.githubusercontent.com/github/spec-kit/main/"
            f"workflows/{workflow_id}/workflow.yml"
        ), f"catalog URL for workflow '{workflow_id}' does not point at the "
        "shipped workflow.yml on the repository default branch"


def test_firstparty_manifest_pins_match_shipped_versions():
    for bundle_id in ("bugfix", "assess"):
        manifest = _read_yaml(REPO_ROOT / "bundles" / bundle_id / "bundle.yml")
        provides = manifest.get("provides", {})

        for ext_ref in provides.get("extensions", []):
            expected = _extension_version(ext_ref["id"])
            assert str(ext_ref.get("version")) == expected, (
                f"{bundle_id} manifest pins extension {ext_ref['id']} at "
                f"{ext_ref.get('version')}, but extensions/{ext_ref['id']}/extension.yml "
                f"ships {expected}"
            )

        for wf_ref in provides.get("workflows", []):
            expected = _workflow_version(wf_ref["id"])
            assert str(wf_ref.get("version")) == expected, (
                f"{bundle_id} manifest pins workflow {wf_ref['id']} at "
                f"{wf_ref.get('version')}, but workflows/{wf_ref['id']}/workflow.yml "
                f"ships {expected}"
            )


def test_firstparty_catalog_provides_counts_match_manifests():
    catalog = _read_json(REPO_ROOT / "bundles" / "catalog.json")

    for bundle_id, entry in catalog["bundles"].items():
        manifest = _read_yaml(REPO_ROOT / "bundles" / bundle_id / "bundle.yml")
        provides = manifest.get("provides", {})

        for kind in ("extensions", "presets", "steps", "workflows"):
            expected_count = len(provides.get(kind, []))
            assert entry["provides"][kind] == expected_count, (
                f"catalog entry '{bundle_id}' claims {entry['provides'][kind]} {kind}, "
                f"but the manifest lists {expected_count}"
            )


def test_firstparty_catalog_entries_are_verified():
    catalog = _read_json(REPO_ROOT / "bundles" / "catalog.json")
    for bundle_id, entry in catalog["bundles"].items():
        assert entry.get("verified") is True, (
            f"first-party catalog entry '{bundle_id}' must be marked verified: true"
        )
