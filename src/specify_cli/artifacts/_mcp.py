"""MCP registration and inventory for the ``specify artifact`` hierarchy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from mcp.server import MCPServer

from ._operation_info import ARTIFACT_INFO_OPERATION
from ._operation_list import ARTIFACT_LIST_OPERATION
from .mcp_list import register as register_list

ArtifactOperationId = Literal["artifact.list", "artifact.info", "artifact.lookup"]
ArtifactCliPath = Literal[
    "specify artifact list",
    "specify artifact info",
    "specify artifact lookup",
]
ArtifactToolName = Literal[
    "specify_artifact_list",
    "specify_artifact_info",
    "specify_artifact_lookup",
]
ArtifactDisposition = Literal["available", "unavailable"]


@dataclass(frozen=True)
class ArtifactToolInventory:
    """One authoritative MCP disposition for an artifact CLI leaf."""

    operation_id: ArtifactOperationId
    cli_path: ArtifactCliPath
    mcp_tool_name: ArtifactToolName
    contract_version: str | None
    disposition: ArtifactDisposition
    disposition_reason: str | None
    capabilities: frozenset[Literal["local-read"]]
    network_access: Literal["none"]


ARTIFACT_TOOLS = (
    ArtifactToolInventory(
        operation_id=ARTIFACT_LIST_OPERATION.operation_id,
        cli_path="specify artifact list",
        mcp_tool_name="specify_artifact_list",
        contract_version=ARTIFACT_LIST_OPERATION.contract_version,
        disposition="available",
        disposition_reason=None,
        capabilities=ARTIFACT_LIST_OPERATION.capabilities,
        network_access=ARTIFACT_LIST_OPERATION.network_access,
    ),
    ArtifactToolInventory(
        operation_id=ARTIFACT_INFO_OPERATION.operation_id,
        cli_path="specify artifact info",
        mcp_tool_name="specify_artifact_info",
        contract_version=ARTIFACT_INFO_OPERATION.contract_version,
        disposition="unavailable",
        disposition_reason=(
            "The artifact.info shared operation does not yet have an MCP adapter."
        ),
        capabilities=ARTIFACT_INFO_OPERATION.capabilities,
        network_access=ARTIFACT_INFO_OPERATION.network_access,
    ),
    ArtifactToolInventory(
        operation_id="artifact.lookup",
        cli_path="specify artifact lookup",
        mcp_tool_name="specify_artifact_lookup",
        contract_version=None,
        disposition="unavailable",
        disposition_reason=(
            "The artifact.lookup CLI leaf does not yet have a shared typed operation."
        ),
        capabilities=frozenset({"local-read"}),
        network_access="none",
    ),
)


def register(server: MCPServer, *, launch_directory: Path) -> None:
    """Register every available artifact tool from the explicit inventory."""
    available = {
        item.operation_id: item
        for item in ARTIFACT_TOOLS
        if item.disposition == "available"
    }
    list_tool = available[ARTIFACT_LIST_OPERATION.operation_id]
    register_list(
        server,
        launch_directory=launch_directory,
        tool_name=list_tool.mcp_tool_name,
    )
