"""Helpers for installing MCP server recipes into an InfraKit project.

These helpers split two responsibilities:

1. **Native config path** (Claude, Cursor) — merge an entry into a JSON
   ``mcp.json`` file at the agent's known location.
2. **Markdown fallback** (every other agent) — append a ready-to-paste JSON
   block to ``.infrakit/mcp-servers.md`` so the user can manually wire the
   server into their agent's global settings.

Both paths also update the ``.infrakit/mcp-use.md`` index so other commands
can see which servers are installed.
"""

from __future__ import annotations

import json
from pathlib import Path

from .mcp_config import MCP_RECIPES


def _read_mcp_json(path: Path) -> dict:
    """Read an existing ``mcp.json``, returning a minimal valid skeleton on
    missing or invalid input. Never raises.
    """
    if not path.exists():
        return {"mcpServers": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"mcpServers": {}}
        if "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
            data["mcpServers"] = {}
        return data
    except (json.JSONDecodeError, OSError):
        return {"mcpServers": {}}


def _build_mcp_server_entry(recipe_key: str) -> dict:
    """Convert a recipe entry from :data:`MCP_RECIPES` into the
    ``mcpServers`` entry shape expected by the agent's ``mcp.json``.
    """
    recipe = MCP_RECIPES[recipe_key]
    entry = {"type": recipe["type"]}
    if recipe["type"] == "stdio":
        entry["command"] = recipe["command"]
        entry["args"] = recipe["args"]
    elif recipe["type"] == "sse":
        entry["url"] = recipe["url"]
    return entry


def _build_mcp_markdown_block(recipe_key: str, recipe: dict, agent_name: str) -> str:
    """Build a markdown block (heading + description + JSON snippet) for
    agents without native MCP file support."""
    lines = [
        f"## {recipe_key}",
        "",
        f"**{recipe['display_name']}**",
        "",
        recipe["description"],
        "",
        f"Configure in your {agent_name} global MCP settings:",
        "",
    ]
    if recipe["type"] == "stdio":
        lines += [
            "```json",
            f'"{recipe_key}": {{',
            '  "type": "stdio",',
            f'  "command": "{recipe["command"]}",',
            f'  "args": {json.dumps(recipe["args"])}',
            "}",
            "```",
            "",
        ]
    elif recipe["type"] == "sse":
        lines += [
            "```json",
            f'"{recipe_key}": {{',
            '  "type": "sse",',
            f'  "url": "{recipe["url"]}"',
            "}",
            "```",
            "",
        ]
    return "\n".join(lines)


def _update_mcp_use_table(project_root: Path, recipe_key: str) -> None:
    """Append a row to ``.infrakit/mcp-use.md`` if ``recipe_key`` isn't already listed."""
    md_path = project_root / ".infrakit" / "mcp-use.md"
    recipe = MCP_RECIPES[recipe_key]

    existing = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    if f"| {recipe_key} |" in existing:
        return

    tools_str = ", ".join(f"`{t}`" for t in recipe.get("tools", []))
    new_row = f"| {recipe_key} | {recipe['description']} | {tools_str} | {recipe['usage']} |\n"

    if md_path.exists():
        # Try to replace the placeholder row; if that row was already removed
        # (e.g. by a previous install), append at the end.
        updated = existing.replace("| — | — | — | — |\n", new_row)
        if updated == existing:
            updated = existing + new_row
        md_path.write_text(updated, encoding="utf-8")
    else:
        md_path.write_text(
            "# Installed MCP Servers\n\n"
            "| MCP | Description | Tools | Usage |\n"
            "|-----|-------------|-------|-------|\n" + new_row,
            encoding="utf-8",
        )
