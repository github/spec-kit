"""Explicit MCP inventory disposition for project destruction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class DestroyToolInventory:
    operation_id: Literal["destroy"] = "destroy"
    cli_path: Literal["specify destroy"] = "specify destroy"
    mcp_tool_name: Literal["specify_destroy"] = "specify_destroy"
    contract_version: Literal["1"] = "1"
    disposition: Literal["unavailable"] = "unavailable"
    disposition_reason: str = (
        "Project destruction is CLI-only until a dedicated MCP destructive-consent adapter is implemented."
    )
    capabilities: frozenset[str] = frozenset({"local-read", "project-write", "execution", "self-modifying"})
    network_access: Literal["none"] = "none"


DESTROY_TOOL = DestroyToolInventory()
