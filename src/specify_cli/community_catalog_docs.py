"""Helpers for generating community extension reference docs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
COMMUNITY_CATALOG_PATH = ROOT_DIR / "extensions" / "catalog.community.json"
COMMUNITY_INDEX_PATH = ROOT_DIR / "docs" / "community" / "extensions.md"

GENERATED_START_MARKER = "<!-- BEGIN GENERATED COMMUNITY EXTENSIONS TABLE -->"
GENERATED_END_MARKER = "<!-- END GENERATED COMMUNITY EXTENSIONS TABLE -->"


def load_community_catalog(path: Path = COMMUNITY_CATALOG_PATH) -> dict[str, Any]:
    """Load and validate the community catalog JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected {path} to contain a JSON object")
    extensions = data.get("extensions")
    if not isinstance(extensions, dict):
        raise ValueError(f"Expected {path} to contain an 'extensions' object")
    return data


def _render_cell(value: str) -> str:
    return value.replace("\n", " ")


def _format_tags(tags: Any) -> str:
    if not isinstance(tags, list) or not tags:
        return "—"
    cleaned = [f"`{str(tag)}`" for tag in tags if str(tag).strip()]
    return ", ".join(cleaned) if cleaned else "—"


def iter_community_extensions(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    """Return community extensions ordered for the generated index."""
    extensions = catalog.get("extensions", {})
    if not isinstance(extensions, dict):
        raise ValueError("Community catalog must contain an 'extensions' object")

    rows: list[dict[str, Any]] = []
    for ext_id, ext in extensions.items():
        if not isinstance(ext, dict):
            raise ValueError(f"Community extension {ext_id!r} must be a mapping")
        rows.append(
            {
                "name": str(ext.get("name") or ext_id),
                "id": str(ext.get("id") or ext_id),
                "description": str(ext.get("description") or ""),
                "tags": _format_tags(ext.get("tags")),
                "verified": "Yes" if bool(ext.get("verified")) else "No",
                "repository": str(ext.get("repository") or ""),
            }
        )

    return sorted(rows, key=lambda row: (row["name"].casefold(), row["id"].casefold()))


def render_community_extensions_table(catalog: dict[str, Any]) -> str:
    """Render the community extensions index table from catalog data."""
    rows = iter_community_extensions(catalog)
    if not rows:
        raise ValueError("Community catalog has no extensions")

    table_rows: list[list[str]] = []
    for row in rows:
        name = (
            f"[{row['name']}]({row['repository']})"
            if row["repository"]
            else row["name"]
        )
        table_rows.append(
            [
                name,
                f"`{row['id']}`",
                row["description"],
                row["tags"],
                row["verified"],
            ]
        )

    widths = [
        max(len(header), *(len(_render_cell(row[index])) for row in table_rows))
        for index, header in enumerate(("Extension", "ID", "Description", "Tags", "Verified"))
    ]

    def render_row(values: list[str]) -> str:
        return "| " + " | ".join(
            _render_cell(value).ljust(widths[index]) for index, value in enumerate(values)
        ) + " |"

    lines = [
        render_row(["Extension", "ID", "Description", "Tags", "Verified"]),
        "| " + " | ".join("-" * width for width in widths) + " |",
    ]
    lines.extend(render_row(row) for row in table_rows)
    return "\n".join(lines)


def render_community_extensions_index(
    catalog_path: Path = COMMUNITY_CATALOG_PATH,
    doc_path: Path = COMMUNITY_INDEX_PATH,
) -> str:
    """Return the community extensions index markdown with the generated table updated."""
    catalog = load_community_catalog(catalog_path)
    table = render_community_extensions_table(catalog)

    content = doc_path.read_text(encoding="utf-8")
    start = content.find(GENERATED_START_MARKER)
    end = content.find(GENERATED_END_MARKER)
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"Could not find generated table markers in {doc_path}")

    start_end = start + len(GENERATED_START_MARKER)
    before = content[:start_end]
    after = content[end:]
    generated_block = f"\n\n{table}\n"
    return before + generated_block + after


def update_community_extensions_index(
    catalog_path: Path = COMMUNITY_CATALOG_PATH,
    doc_path: Path = COMMUNITY_INDEX_PATH,
) -> str:
    """Rewrite the community extensions index markdown file and return the new content."""
    updated = render_community_extensions_index(catalog_path, doc_path)
    doc_path.write_text(updated, encoding="utf-8")
    return updated
