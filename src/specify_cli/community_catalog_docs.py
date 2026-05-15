"""Helpers for rendering the community extensions reference table."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
COMMUNITY_CATALOG_PATH = ROOT_DIR / "extensions" / "catalog.community.json"


def _render_cell(value: str) -> str:
    return value.replace("\r\n", " ").replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def _format_tags(tags: Any) -> str:
    if not isinstance(tags, list) or not tags:
        return "—"
    # Clean first, then filter: a tag of "  |  " would pass str(tag).strip() but produce
    # an empty backtick span after pipe removal, so filter on the cleaned value.
    cleaned = [f"`{c}`" for tag in tags if (c := str(tag).replace("|", "").strip())]
    return ", ".join(cleaned) if cleaned else "—"


def list_community_extensions(path: Path = COMMUNITY_CATALOG_PATH) -> list[dict[str, Any]]:
    """Return community extensions sorted alphabetically by name then ID."""
    if not path.exists():
        raise FileNotFoundError(
            f"Community catalog not found: {path}. "
            "The --markdown flag requires a spec-kit source checkout."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected {path} to contain a JSON object")
    extensions = data.get("extensions")
    if not isinstance(extensions, dict):
        raise ValueError(f"Expected {path} to contain an 'extensions' object")

    rows: list[dict[str, Any]] = []
    for ext_id, ext in extensions.items():
        if not isinstance(ext, dict):
            raise ValueError(f"Community extension {ext_id!r} must be a mapping")
        rows.append(
            {
                "name": str(ext.get("name") or ext_id),
                "id": str(ext.get("id") or ext_id),
                "description": str(ext.get("description") or ""),
                "tags": ext.get("tags") or [],
                "verified": "Yes" if bool(ext.get("verified")) else "No",
                "repository": str(ext.get("repository") or ""),
            }
        )

    return sorted(rows, key=lambda row: (row["name"].casefold(), row["id"].casefold()))


def render_community_extensions_table(path: Path = COMMUNITY_CATALOG_PATH) -> str:
    """Render the community extensions table from catalog.community.json."""
    rows = list_community_extensions(path=path)
    if not rows:
        raise ValueError("Community catalog has no extensions")

    table_rows: list[list[str]] = []
    for row in rows:
        # Escape raw field values *before* composing Markdown syntax so that
        # a pipe inside a name or description doesn't break a link target.
        safe_name = _render_cell(row["name"])
        link = (
            f"[{safe_name}]({row['repository']})"
            if row["repository"]
            else safe_name
        )
        table_rows.append(
            [
                link,
                f"`{row['id']}`",
                _render_cell(row["description"]),
                _format_tags(row["tags"]),
                row["verified"],
            ]
        )

    headers = ("Extension", "ID", "Description", "Tags", "Verified")

    def render_row(values: list[str]) -> str:
        # Values are already escaped; do not re-apply _render_cell here.
        return "| " + " | ".join(values) + " |"

    separator = "| " + " | ".join("---" for _ in headers) + " |"
    lines = [render_row(list(headers)), separator]
    lines.extend(render_row(row) for row in table_rows)
    return "\n".join(lines) + "\n"
