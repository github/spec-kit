"""Contract tests for the catalog schema and source stack.

Mirrors contracts/bundle-catalog.schema.md: source precedence project > user >
built-in, install policy gating, payload parsing.
"""
from __future__ import annotations

import json
import tomllib
from pathlib import Path

import yaml

from specify_cli.bundler.models.catalog import (
    BUILTIN_DEFAULT_STACK,
    CatalogSource,
    InstallPolicy,
    Scope,
    load_catalog_payload,
    load_source_stack,
)
from specify_cli.bundler import BundlerError
import pytest
from tests.bundler_helpers import catalog_entry_dict, catalog_payload, make_project


def test_non_integer_source_priority_raises_actionable_error():
    with pytest.raises(BundlerError, match="non-integer priority"):
        CatalogSource.from_dict(
            {"id": "corp", "url": "https://corp/catalog.json", "priority": "high"},
            Scope.PROJECT,
        )


def test_builtin_default_stack_when_no_config(tmp_path: Path):
    make_project(tmp_path)
    sources = load_source_stack(tmp_path)
    ids = [s.id for s in sources]
    assert ids == ["default", "community"]
    assert sources[0].install_policy is InstallPolicy.INSTALL_ALLOWED
    assert sources[1].install_policy is InstallPolicy.DISCOVERY_ONLY
    assert sources[1].priority == 20
    assert all(s.scope is Scope.BUILTIN for s in sources)


def test_project_config_overrides_same_id(tmp_path: Path):
    make_project(tmp_path)
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {"id": "default", "url": "file://local", "priority": 1,
             "install_policy": "install-allowed"},
            {"id": "corp", "url": "https://corp/catalog.json", "priority": 0,
             "install_policy": "install-allowed"},
        ],
    }
    (tmp_path / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )
    sources = load_source_stack(tmp_path)
    by_id = {s.id: s for s in sources}
    assert by_id["default"].scope is Scope.PROJECT
    assert by_id["default"].url == "file://local"
    # Highest precedence (lowest priority number) sorts first.
    assert sources[0].id == "corp"


def test_user_scope_between_builtin_and_project(tmp_path: Path):
    make_project(tmp_path)
    user_dir = tmp_path / "userconf"
    user_dir.mkdir()
    (user_dir / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(
            {"catalogs": [
                {"id": "community", "url": "https://u", "priority": 2,
                 "install_policy": "install-allowed"}
            ]}
        ),
        encoding="utf-8",
    )
    sources = load_source_stack(tmp_path, user_config_dir=user_dir)
    by_id = {s.id: s for s in sources}
    # User overrode the built-in community policy to install-allowed.
    assert by_id["community"].scope is Scope.USER
    assert by_id["community"].install_allowed is True


def test_load_payload_parses_entries():
    payload = catalog_payload({"demo-bundle": catalog_entry_dict()})
    entries = load_catalog_payload(payload)
    assert "demo-bundle" in entries
    assert entries["demo-bundle"].version == "1.2.0"
    assert entries["demo-bundle"].provides["presets"] == 1


def test_builtin_default_stack_constant_shape():
    ids = {raw["id"] for raw in BUILTIN_DEFAULT_STACK}
    assert ids == {"default", "community"}


def test_repository_community_bundle_catalog_matches_contract():
    catalog_path = Path(__file__).parents[2] / "bundles" / "catalog.community.json"
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "1.0"
    assert payload["catalog_url"].endswith("/bundles/catalog.community.json")
    entries = load_catalog_payload(payload)
    assert all(entry.verified is False for entry in entries.values())


def test_wheel_packages_community_bundle_catalog():
    repo_root = Path(__file__).parents[2]
    with (repo_root / "pyproject.toml").open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)

    force_include = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"][
        "force-include"
    ]
    assert force_include["bundles/catalog.community.json"] == (
        "specify_cli/core_pack/bundles/catalog.community.json"
    )


def test_catalog_entry_rejects_string_tags():
    from specify_cli.bundler.models.catalog import CatalogEntry

    data = catalog_entry_dict("demo")
    data["tags"] = "not-a-list"
    with pytest.raises(BundlerError, match="'tags' must be a list"):
        CatalogEntry.from_dict(data)


def test_catalog_entry_rejects_non_boolean_verified():
    from specify_cli.bundler.models.catalog import CatalogEntry

    data = catalog_entry_dict("demo")
    data["verified"] = "false"  # truthy string must not mark the entry verified
    with pytest.raises(BundlerError, match="'verified' must be a boolean"):
        CatalogEntry.from_dict(data)


def test_load_payload_rejects_id_key_mismatch():
    # The enclosing key is authoritative; an entry whose own id disagrees with
    # the key must be rejected so a catalog can't list a spoofed/unresolvable id.
    payload = catalog_payload({"demo-bundle": catalog_entry_dict("other-id")})
    with pytest.raises(BundlerError, match="id mismatch"):
        load_catalog_payload(payload)


def test_load_payload_rejects_missing_entry_id():
    entry = catalog_entry_dict("demo-bundle")
    entry["id"] = ""
    payload = catalog_payload({"demo-bundle": entry})
    with pytest.raises(BundlerError, match="missing its 'id'"):
        load_catalog_payload(payload)


def test_catalog_entry_rejects_non_mapping_requires():
    from specify_cli.bundler.models.catalog import CatalogEntry

    data = catalog_entry_dict("demo")
    data["requires"] = "speckit>=0.1"
    with pytest.raises(BundlerError, match="'requires' must be a mapping"):
        CatalogEntry.from_dict(data)


def test_catalog_entry_rejects_non_mapping_provides():
    from specify_cli.bundler.models.catalog import CatalogEntry

    data = catalog_entry_dict("demo")
    data["provides"] = "extensions"
    with pytest.raises(BundlerError, match="'provides' must be a mapping"):
        CatalogEntry.from_dict(data)
