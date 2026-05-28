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
    from specify_cli.community_catalog_docs import COMMUNITY_CATALOG_PATH
    if not COMMUNITY_CATALOG_PATH.exists():
        pytest.skip(
            f"Community catalog not found at {COMMUNITY_CATALOG_PATH}. "
            "Skipping (expected when running from sdist/wheel)."
        )
    table = render_community_extensions_table()
    assert "| Extension" in table
    assert "| ID" in table
    assert "| Description" in table
    assert "| Tags" in table
    assert "| Verified" in table


def test_community_extensions_are_sorted_by_name() -> None:
    from specify_cli.community_catalog_docs import COMMUNITY_CATALOG_PATH
    if not COMMUNITY_CATALOG_PATH.exists():
        pytest.skip(
            f"Community catalog not found at {COMMUNITY_CATALOG_PATH}. "
            "Skipping (expected when running from sdist/wheel)."
        )
    rows = list_community_extensions()
    names = [row["name"] for row in rows]
    assert names == sorted(names, key=str.casefold)


def test_community_extensions_table_rows_are_rendered_in_sorted_order(tmp_path: Path) -> None:
    catalog = _write_catalog(
        tmp_path,
        {
            "gamma": {
                "name": "Gamma",
                "id": "gamma",
                "description": "Third entry",
                "tags": [],
                "verified": False,
                "repository": "",
            },
            "alpha": {
                "name": "Alpha",
                "id": "alpha",
                "description": "First entry",
                "tags": [],
                "verified": True,
                "repository": "",
            },
            "beta": {
                "name": "Beta",
                "id": "beta",
                "description": "Second entry",
                "tags": [],
                "verified": False,
                "repository": "",
            },
        },
    )
    table = render_community_extensions_table(path=catalog)

    rendered_rows: list[tuple[str, str]] = []
    for line in table.splitlines():
        if not line.startswith("| "):
            continue
        if line == "| Extension | ID | Description | Tags | Verified |":
            continue
        if line == "| --- | --- | --- | --- | --- |":
            continue
        cells = [part.strip() for part in line.strip("|").split("|")]
        assert len(cells) == 5, f"Malformed table row: {line}"
        extension_cell = cells[0]
        if extension_cell.startswith("[") and "](" in extension_cell:
            extension_name = extension_cell[1:extension_cell.index("](")]
        else:
            extension_name = extension_cell
        rendered_rows.append((extension_name, cells[1].strip("`")))

    expected_rows = [("Alpha", "alpha"), ("Beta", "beta"), ("Gamma", "gamma")]
    assert rendered_rows == expected_rows


# ---------------------------------------------------------------------------
# Edge-case tests using synthetic catalogs
# ---------------------------------------------------------------------------

def test_missing_catalog_file(tmp_path: Path) -> None:
    with pytest.raises(
        FileNotFoundError,
        match="Provide path= to a valid community catalog JSON file",
    ):
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


def test_whitespace_repository_is_treated_as_missing(tmp_path: Path) -> None:
    f = _write_catalog(tmp_path, {
        "foo": {"name": "Foo", "id": "foo", "description": "", "tags": [], "verified": False, "repository": "   "},
    })
    table = render_community_extensions_table(path=f)
    assert "Foo" in table
    assert "[Foo](" not in table


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


def test_tags_with_newlines_are_normalized(tmp_path: Path) -> None:
    f = _write_catalog(tmp_path, {
        "foo": {
            "name": "Foo",
            "description": "",
            "tags": ["foo\nbar", "baz\r\nqux", "quux\rquuz"],
            "verified": False,
            "repository": "",
        },
    })
    table = render_community_extensions_table(path=f)
    assert "`foo bar`" in table
    assert "`baz qux`" in table
    assert "`quux quuz`" in table
    foo_row = next(line for line in table.split("\n") if line.startswith("| ") and "Foo" in line)
    assert foo_row.count("|") == 6


def test_non_list_tags_renders_em_dash(tmp_path: Path) -> None:
    f = _write_catalog(tmp_path, {
        "foo": {"name": "Foo", "description": "", "tags": "not-a-list", "verified": False, "repository": ""},
    })
    table = render_community_extensions_table(path=f)
    assert "—" in table


def test_url_escaping_in_repository_links(tmp_path: Path) -> None:
    """Test that URLs with `)` and `|` are properly escaped in markdown links."""
    f = _write_catalog(tmp_path, {
        "foo": {
            "name": "Foo",
            "description": "",
            "tags": [],
            "verified": False,
            "repository": "https://example.com/repo?x=1)&y=2|bad",  # Contains ) and |
        },
    })
    table = render_community_extensions_table(path=f)
    # The URL should be escaped: ) → \) and | → \|
    assert "[Foo](https://example.com/repo?x=1\\)&y=2\\|bad)" in table


def test_link_text_is_escaped(tmp_path: Path) -> None:
    f = _write_catalog(tmp_path, {
        "foo": {
            "name": "Code [Buddy]",
            "description": "",
            "tags": [],
            "verified": False,
            "repository": "https://example.com/repo",
        },
    })
    table = render_community_extensions_table(path=f)
    assert "[Code \\[Buddy\\]](https://example.com/repo)" in table


def test_extension_id_is_sanitized(tmp_path: Path) -> None:
    f = _write_catalog(tmp_path, {
        "foo|bar": {
            "name": "Foo",
            "id": "foo|bar\n",
            "description": "",
            "tags": [],
            "verified": False,
            "repository": "",
        },
    })
    table = render_community_extensions_table(path=f)
    assert "`foo\\|bar `" in table
