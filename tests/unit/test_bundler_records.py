"""Unit tests for installed-bundle records and collateral-protection logic."""
from __future__ import annotations

from pathlib import Path

from specify_cli.bundler.models.manifest import ComponentRef
from specify_cli.bundler.models.records import (
    InstalledBundleRecord,
    components_still_needed,
    load_records,
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
