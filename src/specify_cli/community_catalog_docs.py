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
    # Strip | from tag values so they don't break table syntax inside backtick spans
    cleaned = [f"`{str(tag).replace('|', '').strip()}`" for tag in tags if str(tag).strip()]
    return ", ".join(cleaned) if cleaned else "—"


def list_community_extensions() -> list[dict[str, Any]]:
    """Return community extensions sorted alphabetically by name then ID."""
    if not COMMUNITY_CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"Community catalog not found: {COMMUNITY_CATALOG_PATH}. "
            "The --markdown flag requires a spec-kit source checkout."
        )
    data = json.loads(COMMUNITY_CATALOG_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected {COMMUNITY_CATALOG_PATH} to contain a JSON object")
    extensions = data.get("extensions")
    if not isinstance(extensions, dict):
        raise ValueError(f"Expected {COMMUNITY_CATALOG_PATH} to contain an 'extensions' object")

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


def render_community_extensions_table() -> str:
    """Render the community extensions table from catalog.community.json."""
    rows = list_community_extensions()
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
                _format_tags(row["tags"]),
                row["verified"],
            ]
        )

    headers = ("Extension", "ID", "Description", "Tags", "Verified")

    def render_row(values: list[str]) -> str:
        return "| " + " | ".join(_render_cell(value) for value in values) + " |"

    separator = "| " + " | ".join("---" for _ in headers) + " |"
    lines = [render_row(list(headers)), separator]
    lines.extend(render_row(row) for row in table_rows)
    return "\n".join(lines)
