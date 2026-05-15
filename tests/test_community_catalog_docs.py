from __future__ import annotations

import json
from pathlib import Path

import pytest

from specify_cli.community_catalog_docs import list_community_extensions, render_community_extensions_table


def _write_catalog(tmp_path: Path, extensions: dict) -> Path:
    p = tmp_path / "catalog.community.json"
    p.write_text(json.dumps({"extensions": extensions}), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Happy-path tests against the real catalog
# ---------------------------------------------------------------------------

def test_community_extensions_table_renders() -> None:
    table = render_community_extensions_table()
    assert "| Extension" in table
    assert "| ID" in table
    assert "| Description" in table
    assert "| Tags" in table
    assert "| Verified" in table


def test_community_extensions_are_sorted_by_name() -> None:
    rows = list_community_extensions()
    names = [row["name"] for row in rows]
    assert names == sorted(names, key=str.casefold)


# ---------------------------------------------------------------------------
# Edge-case tests using synthetic catalogs
# ---------------------------------------------------------------------------

def test_missing_catalog_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="spec-kit source checkout"):
        list_community_extensions(path=tmp_path / "missing.json")


def test_malformed_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("not valid json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        list_community_extensions(path=bad)


def test_non_dict_root(tmp_path: Path) -> None:
    f = tmp_path / "catalog.json"
    f.write_text(json.dumps([{"id": "foo"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        list_community_extensions(path=f)


def test_missing_extensions_key(tmp_path: Path) -> None:
    f = tmp_path / "catalog.json"
    f.write_text(json.dumps({"other": {}}), encoding="utf-8")
    with pytest.raises(ValueError, match="'extensions' object"):
        list_community_extensions(path=f)


def test_non_dict_extension_value(tmp_path: Path) -> None:
    f = _write_catalog(tmp_path, {"foo": "not-a-dict"})
    with pytest.raises(ValueError, match="must be a mapping"):
        list_community_extensions(path=f)


def test_empty_catalog_raises(tmp_path: Path) -> None:
    f = _write_catalog(tmp_path, {})
    with pytest.raises(ValueError, match="no extensions"):
        render_community_extensions_table(path=f)


def test_extension_without_repository(tmp_path: Path) -> None:
    f = _write_catalog(tmp_path, {
        "foo": {"name": "Foo", "id": "foo", "description": "A foo tool", "tags": [], "verified": False, "repository": ""},
    })
    table = render_community_extensions_table(path=f)
    assert "Foo" in table
    assert "[Foo](" not in table  # plain name, no link


def test_tags_containing_pipe_do_not_break_table(tmp_path: Path) -> None:
    f = _write_catalog(tmp_path, {
        # No "id" field — exercises ext_id fallback; tag has pipe — exercises stripping
        "foo": {"name": "Foo", "description": "", "tags": ["foo|bar"], "verified": False, "repository": ""},
    })
    table = render_community_extensions_table(path=f)
    # pipe stripped from tag value
    assert "`foobar`" in table
    # id falls back to the dict key when "id" field is absent
    assert "`foo`" in table
    # row is well-formed: 5-column table has exactly 6 pipe separators per row
    foo_row = next(line for line in table.split("\n") if line.startswith("| ") and "Foo" in line)
    assert foo_row.count("|") == 6


def test_non_list_tags_renders_em_dash(tmp_path: Path) -> None:
    f = _write_catalog(tmp_path, {
        "foo": {"name": "Foo", "description": "", "tags": "not-a-list", "verified": False, "repository": ""},
    })
    table = render_community_extensions_table(path=f)
    assert "—" in table
