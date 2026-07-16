"""Helpers for rendering the community extensions reference table."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._assets import _repo_root
from .catalog_docs import (
    escape_markdown_link_text,
    escape_url_for_markdown_link,
    render_cell,
)


ROOT_DIR = _repo_root()
COMMUNITY_CATALOG_PATH = ROOT_DIR / "extensions" / "catalog.community.json"



def list_community_extensions(
    path: Path = COMMUNITY_CATALOG_PATH,
) -> list[dict[str, Any]]:
    """Return community extensions sorted alphabetically by name then ID."""
    if not path.exists():
        if path == COMMUNITY_CATALOG_PATH:
            message = (
                f"Community catalog not found at {path}. "
                "Ensure the repository checkout includes the extensions/ directory."
            )
        else:
            message = (
                f"Community catalog not found at {path}. "
                "Provide path= to a valid community catalog JSON file."
            )
        raise FileNotFoundError(message)
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
                "category": str(ext.get("category") or "").strip(),
                "effect": str(ext.get("effect") or "").strip(),
                "repository": str(ext.get("repository") or "").strip(),
            }
        )

    return sorted(
        rows,
        key=lambda row: (
            row["name"].lstrip(". ").casefold(),
            row["id"].casefold(),
        ),
    )


def render_community_extensions_table(path: Path = COMMUNITY_CATALOG_PATH) -> str:
    """Render the community extensions table from catalog.community.json."""
    rows = list_community_extensions(path=path)
    if not rows:
        raise ValueError("Community catalog has no extensions")

    table_rows: list[list[str]] = []
    for row in rows:
        # Escape raw field values *before* composing Markdown syntax so that
        # a pipe inside a name or description doesn't break a link target.
        safe_name = render_cell(row["name"])
        safe_description = render_cell(row["description"])
        category = render_cell(row["category"])
        category_cell = f"`{category}`" if category else "—"
        effect = {
            "read-only": "Read-only",
            "read-write": "Read+Write",
        }.get(row["effect"], render_cell(row["effect"]) or "—")
        repository = row["repository"]
        if repository:
            safe_repo = escape_url_for_markdown_link(repository)
            safe_id = escape_markdown_link_text(render_cell(row["id"]))
            link = f"[{safe_id}]({safe_repo})"
        else:
            link = render_cell(row["id"]) or "—"
        table_rows.append(
            [
                safe_name,
                safe_description,
                category_cell,
                effect,
                link,
            ]
        )

    headers = ("Extension", "Purpose", "Category", "Effect", "URL")

    def render_row(values: list[str]) -> str:
        # Values are already escaped; do not re-apply render_cell here.
        return "| " + " | ".join(values) + " |"

    separator = "| " + " | ".join("---" for _ in headers) + " |"
    lines = [render_row(list(headers)), separator]
    lines.extend(render_row(row) for row in table_rows)
    return "\n".join(lines) + "\n"
