"""Unit tests for installed-bundle records and collateral-protection logic."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundler.models.manifest import ComponentRef
from specify_cli.bundler.models.records import (
    InstalledBundleRecord,
    components_still_needed,
    load_records,
    records_path,
    remove_record,
    save_records,
    upsert_record,
)


def _record(bundle_id: str, comps) -> InstalledBundleRecord:
    return InstalledBundleRecord.create(
        bundle_id=bundle_id,
        version="1.0.0",
        components=[ComponentRef(kind=k, id=i) for k, i in comps],
    )


def test_save_and_load_roundtrip(tmp_path: Path):
    (tmp_path / ".specify").mkdir()
    rec = _record("a", [("presets", "p1"), ("steps", "s1")])
    save_records(tmp_path, [rec])
    loaded = load_records(tmp_path)
    assert len(loaded) == 1
    assert loaded[0].bundle_id == "a"
    assert {(c.kind, c.id) for c in loaded[0].contributed_components} == {
        ("presets", "p1"),
        ("steps", "s1"),
    }


def test_load_missing_file_returns_empty(tmp_path: Path):
    (tmp_path / ".specify").mkdir()
    assert load_records(tmp_path) == []


@pytest.mark.parametrize("bad", [0, False, "", {}])
def test_load_records_rejects_falsy_non_list_bundles(tmp_path: Path, bad):
    # `data.get("bundles") or []` coerced a FALSY non-list (0, '', False, {})
    # to [] before the isinstance guard, silently treating a corrupt records
    # file as "no bundles". Only an absent/None value means empty.
    (tmp_path / ".specify").mkdir()
    records_path(tmp_path).write_text(
        json.dumps({"schema_version": "1.0", "bundles": bad}), encoding="utf-8"
    )
    with pytest.raises(BundlerError, match="'bundles' must be a list"):
        load_records(tmp_path)


@pytest.mark.parametrize("bad", [0, False, "", {}])
def test_from_dict_rejects_falsy_non_list_contributed_components(bad):
    # Same falsy-coercion hole for a record's 'contributed_components'.
    data = {"bundle_id": "a", "version": "1.0.0", "contributed_components": bad}
    with pytest.raises(BundlerError, match="'contributed_components' must be a list"):
        InstalledBundleRecord.from_dict(data)


def test_corrupt_priority_raises_actionable_error(tmp_path: Path):
    (tmp_path / ".specify").mkdir()
    rec = _record("a", [("presets", "p1")])
    save_records(tmp_path, [rec])
    path = records_path(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["bundles"][0]["contributed_components"][0]["priority"] = "high"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(BundlerError, match="priority must be an integer"):
        load_records(tmp_path)


def test_upsert_replaces_same_id():
    rec1 = _record("a", [("presets", "p1")])
    rec2 = _record("a", [("presets", "p2")])
    result = upsert_record([rec1], rec2)
    assert len(result) == 1
    assert result[0].contributed_components[0].id == "p2"


def test_remove_record_drops_target():
    recs = [_record("a", [("presets", "p1")]), _record("b", [("steps", "s1")])]
    result = remove_record(recs, "a")
    assert [r.bundle_id for r in result] == ["b"]


def test_components_still_needed_excludes_target():
    recs = [
        _record("a", [("presets", "shared"), ("steps", "only-a")]),
        _record("b", [("presets", "shared")]),
    ]
    needed = components_still_needed(recs, exclude_bundle_id="a")
    assert ("presets", "shared") in needed
    assert ("steps", "only-a") not in needed


def test_save_records_refuses_symlinked_specify_escape(tmp_path: Path):
    # Defense-in-depth: a symlinked .specify pointing outside the project must
    # not let records be written outside project_root.
    project = tmp_path / "proj"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / ".specify").symlink_to(outside, target_is_directory=True)

    with pytest.raises(BundlerError, match="escapes the allowed root"):
        save_records(project, [_record("a", [("presets", "p1")])])


def test_load_records_rejects_non_list_bundles(tmp_path: Path):
    (tmp_path / ".specify").mkdir()
    path = records_path(tmp_path)
    path.write_text(json.dumps({"schema_version": "1.0", "bundles": "oops"}), encoding="utf-8")
    with pytest.raises(BundlerError, match="'bundles' must be a list"):
        load_records(tmp_path)


def test_load_records_rejects_non_list_contributed_components(tmp_path: Path):
    (tmp_path / ".specify").mkdir()
    path = records_path(tmp_path)
    payload = {
        "schema_version": "1.0",
        "bundles": [
            {"bundle_id": "a", "version": "1.0.0", "contributed_components": "oops"}
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(BundlerError, match="'contributed_components' must be a list"):
        load_records(tmp_path)


def test_load_records_rejects_unknown_component_kind(tmp_path: Path):
    (tmp_path / ".specify").mkdir()
    path = records_path(tmp_path)
    payload = {
        "schema_version": "1.0",
        "bundles": [
            {
                "bundle_id": "a",
                "version": "1.0.0",
                "contributed_components": [{"kind": "bogus", "id": "x"}],
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(BundlerError, match="must be one of"):
        load_records(tmp_path)


def test_load_records_rejects_component_missing_id(tmp_path: Path):
    (tmp_path / ".specify").mkdir()
    path = records_path(tmp_path)
    payload = {
        "schema_version": "1.0",
        "bundles": [
            {
                "bundle_id": "a",
                "version": "1.0.0",
                "contributed_components": [{"kind": "presets", "id": ""}],
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(BundlerError, match="missing its 'id'"):
        load_records(tmp_path)


def test_load_records_rejects_missing_schema_version(tmp_path: Path):
    (tmp_path / ".specify").mkdir()
    records_path(tmp_path).write_text(json.dumps({"bundles": []}), encoding="utf-8")
    with pytest.raises(BundlerError, match="missing 'schema_version'"):
        load_records(tmp_path)


def test_load_records_rejects_unknown_schema_version(tmp_path: Path):
    (tmp_path / ".specify").mkdir()
    payload = {"schema_version": "2.0", "bundles": []}
    records_path(tmp_path).write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(BundlerError, match="Unsupported records schema version"):
        load_records(tmp_path)


def test_load_records_rejects_record_missing_bundle_id(tmp_path: Path):
    (tmp_path / ".specify").mkdir()
    payload = {"schema_version": "1.0", "bundles": [{"version": "1.0.0"}]}
    records_path(tmp_path).write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(BundlerError, match="missing its 'bundle_id'"):
        load_records(tmp_path)


def test_load_records_rejects_record_missing_version(tmp_path: Path):
    (tmp_path / ".specify").mkdir()
    payload = {"schema_version": "1.0", "bundles": [{"bundle_id": "a"}]}
    records_path(tmp_path).write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(BundlerError, match="missing its 'version'"):
        load_records(tmp_path)


def test_load_records_accepts_forward_compatible_minor_schema(tmp_path: Path):
    (tmp_path / ".specify").mkdir()
    payload = {"schema_version": "1.5", "bundles": []}
    records_path(tmp_path).write_text(json.dumps(payload), encoding="utf-8")
    assert load_records(tmp_path) == []
