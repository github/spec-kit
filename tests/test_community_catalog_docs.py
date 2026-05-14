from __future__ import annotations

from specify_cli.community_catalog_docs import list_community_extensions, render_community_extensions_table


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
