"""Explicit MCP dispositions for the complete ``specify workflow`` hierarchy.

No workflow adapter is registered yet. These records describe the conservative
union of the current CLI paths, not a promise of a future MCP contract.

Effect boundaries worth retaining when adapters are introduced:

* Project resolution does not load integrations by default
  (``specify_cli._require_specify_project``).
* Run/resume explicitly load integrations and custom steps before execution.
  Add/update also import custom steps while validating workflow definitions.
* Catalog search/info can write project caches. Authenticated HTTP can invoke
  ``az account get-access-token`` through the configured Azure CLI provider,
  so even discovery/download paths may require execution capability.
* Catalog configuration and overlay operations are local; step installation
  copies/validates Python packages without importing them. Its HTTP source
  paths can nevertheless invoke the authentication provider.

Unavailable entries retain prospective tool names for parity checks only;
they do not expand MCP discovery or the legacy server command catalog.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WorkflowDisposition = Literal["available", "unavailable", "excluded"]
WorkflowCapability = Literal[
    "local-read", "project-write", "execution", "self-modifying"
]
WorkflowNetworkAccess = Literal["none", "optional", "required"]


@dataclass(frozen=True)
class WorkflowToolInventory:
    """One hierarchy-owned MCP disposition for a registered workflow CLI leaf."""

    operation_id: str
    cli_path: str
    mcp_tool_name: str
    disposition_reason: str | None
    capabilities: frozenset[WorkflowCapability]
    network_access: WorkflowNetworkAccess
    contract_version: str | None = None
    disposition: WorkflowDisposition = "unavailable"


_LOCAL_READ: frozenset[WorkflowCapability] = frozenset({"local-read"})
_LOCAL_WRITE: frozenset[WorkflowCapability] = frozenset({"local-read", "project-write"})
_WRITE_AND_EXECUTION: frozenset[WorkflowCapability] = frozenset(
    {"local-read", "project-write", "execution"}
)

WORKFLOW_TOOLS = (
    WorkflowToolInventory(
        operation_id="workflow.add",
        cli_path="specify workflow add",
        mcp_tool_name="specify_workflow_add",
        disposition_reason=(
            "Source selection, custom-step loading, trust prompts and transactional "
            "installation remain CLI-owned; no shared typed add operation or MCP adapter."
        ),
        capabilities=_WRITE_AND_EXECUTION,
        network_access="optional",
    ),
    WorkflowToolInventory(
        operation_id="workflow.disable",
        cli_path="specify workflow disable",
        mcp_tool_name="specify_workflow_disable",
        disposition_reason=(
            "The registry mutation uses _commands._set_workflow_enabled with CLI "
            "errors/output; no shared typed disable operation or MCP adapter."
        ),
        capabilities=_LOCAL_WRITE,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.enable",
        cli_path="specify workflow enable",
        mcp_tool_name="specify_workflow_enable",
        disposition_reason=(
            "The registry mutation uses _commands._set_workflow_enabled with CLI "
            "errors/output; no shared typed enable operation or MCP adapter."
        ),
        capabilities=_LOCAL_WRITE,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.info",
        cli_path="specify workflow info",
        mcp_tool_name="specify_workflow_info",
        disposition_reason=(
            "Installed-definition/catalog selection and result rendering remain in "
            "command_info; no shared typed info operation or MCP adapter."
        ),
        capabilities=_WRITE_AND_EXECUTION,
        network_access="optional",
    ),
    WorkflowToolInventory(
        operation_id="workflow.list",
        cli_path="specify workflow list",
        mcp_tool_name="specify_workflow_list",
        disposition_reason=(
            "WorkflowRegistry.list returns registry dictionaries rendered by the CLI; "
            "no shared typed list outcome or MCP adapter."
        ),
        capabilities=_LOCAL_READ,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.remove",
        cli_path="specify workflow remove",
        mcp_tool_name="specify_workflow_remove",
        disposition_reason=(
            "Staged directory removal and attempted directory recovery after registry "
            "failure remain in command_remove; no shared typed remove operation or MCP adapter."
        ),
        capabilities=_LOCAL_WRITE,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.resolve",
        cli_path="specify workflow resolve",
        mcp_tool_name="specify_workflow_resolve",
        disposition_reason=(
            "overlay.operations.workflow_resolve renders CLI diagnostics and returns "
            "a dictionary or None; no shared typed resolve outcome or MCP adapter."
        ),
        capabilities=_LOCAL_READ,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.resume",
        cli_path="specify workflow resume",
        mcp_tool_name="specify_workflow_resume",
        disposition_reason=(
            "Owner-root resolution, integration loading and CLI input/error mapping "
            "surround WorkflowEngine.resume; no shared typed resume contract or MCP adapter."
        ),
        capabilities=_WRITE_AND_EXECUTION,
        network_access="optional",
    ),
    WorkflowToolInventory(
        operation_id="workflow.run",
        cli_path="specify workflow run",
        mcp_tool_name="specify_workflow_run",
        disposition_reason=(
            "Integration/custom-step loading, inputs and CLI error handling surround "
            "WorkflowEngine.execute; no shared typed run contract or MCP adapter."
        ),
        capabilities=_WRITE_AND_EXECUTION,
        network_access="optional",
    ),
    WorkflowToolInventory(
        operation_id="workflow.search",
        cli_path="specify workflow search",
        mcp_tool_name="specify_workflow_search",
        disposition_reason=(
            "WorkflowCatalog.search supplies catalog data but command_search owns "
            "mapping/rendering; no shared typed search outcome or MCP adapter."
        ),
        capabilities=_WRITE_AND_EXECUTION,
        network_access="optional",
    ),
    WorkflowToolInventory(
        operation_id="workflow.status",
        cli_path="specify workflow status",
        mcp_tool_name="specify_workflow_status",
        disposition_reason=(
            "RunState.load/list_runs results and JSON/error mapping are assembled in "
            "command_status; no shared typed status operation or MCP adapter."
        ),
        capabilities=_LOCAL_READ,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.update",
        cli_path="specify workflow update",
        mcp_tool_name="specify_workflow_update",
        disposition_reason=(
            "Custom-step loading, version selection, confirmation and installation "
            "remain CLI-owned; no shared typed update operation or MCP adapter."
        ),
        capabilities=_WRITE_AND_EXECUTION,
        network_access="optional",
    ),
    # Catalog configuration reads/writes URLs; it does not fetch their contents.
    WorkflowToolInventory(
        operation_id="workflow.catalog.add",
        cli_path="specify workflow catalog add",
        mcp_tool_name="specify_workflow_catalog_add",
        disposition_reason=(
            "WorkflowCatalog.add_catalog mutates configuration, but its command-level "
            "request/error/outcome contract and MCP adapter are not defined."
        ),
        capabilities=_LOCAL_WRITE,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.catalog.list",
        cli_path="specify workflow catalog list",
        mcp_tool_name="specify_workflow_catalog_list",
        disposition_reason=(
            "WorkflowCatalog.get_catalog_configs returns dictionaries rendered by the "
            "CLI; no shared typed catalog-list outcome or MCP adapter."
        ),
        capabilities=_LOCAL_READ,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.catalog.remove",
        cli_path="specify workflow catalog remove",
        mcp_tool_name="specify_workflow_catalog_remove",
        disposition_reason=(
            "WorkflowCatalog.remove_catalog owns configuration edits, but the CLI "
            "maps arguments/errors; no shared typed removal contract or MCP adapter."
        ),
        capabilities=_LOCAL_WRITE,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.overlay.add",
        cli_path="specify workflow overlay add",
        mcp_tool_name="specify_workflow_overlay_add",
        disposition_reason=(
            "workflow_overlay_add stages overlay files but prints CLI diagnostics and "
            "returns Path or None; no shared typed add contract or MCP adapter."
        ),
        capabilities=_LOCAL_WRITE,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.overlay.disable",
        cli_path="specify workflow overlay disable",
        mcp_tool_name="specify_workflow_overlay_disable",
        disposition_reason=(
            "workflow_overlay_disable uses CLI-bound overlay mutation/error helpers; "
            "no shared typed disable outcome or MCP adapter."
        ),
        capabilities=_LOCAL_WRITE,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.overlay.enable",
        cli_path="specify workflow overlay enable",
        mcp_tool_name="specify_workflow_overlay_enable",
        disposition_reason=(
            "workflow_overlay_enable uses CLI-bound overlay mutation/error helpers; "
            "no shared typed enable outcome or MCP adapter."
        ),
        capabilities=_LOCAL_WRITE,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.overlay.list",
        cli_path="specify workflow overlay list",
        mcp_tool_name="specify_workflow_overlay_list",
        disposition_reason=(
            "workflow_overlay_list prints CLI diagnostics and returns dictionaries "
            "or None; no shared typed list outcome or MCP adapter."
        ),
        capabilities=_LOCAL_READ,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.overlay.remove",
        cli_path="specify workflow overlay remove",
        mcp_tool_name="specify_workflow_overlay_remove",
        disposition_reason=(
            "workflow_overlay_remove deletes local files with CLI-bound error reporting; "
            "no shared typed remove outcome or MCP adapter."
        ),
        capabilities=_LOCAL_WRITE,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.overlay.set-priority",
        cli_path="specify workflow overlay set-priority",
        mcp_tool_name="specify_workflow_overlay_set_priority",
        disposition_reason=(
            "workflow_overlay_set_priority uses CLI-bound YAML mutation/error helpers; "
            "no shared typed priority-change outcome or MCP adapter."
        ),
        capabilities=_LOCAL_WRITE,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.step.add",
        cli_path="specify workflow step add",
        mcp_tool_name="specify_workflow_step_add",
        disposition_reason=(
            "Package validation/install helpers exist, but source/trust selection and "
            "command-level outcomes remain CLI-owned; no typed add contract or MCP adapter."
        ),
        capabilities=_WRITE_AND_EXECUTION,
        network_access="optional",
    ),
    WorkflowToolInventory(
        operation_id="workflow.step.info",
        cli_path="specify workflow step info",
        mcp_tool_name="specify_workflow_step_info",
        disposition_reason=(
            "Builtin/installed/catalog selection and result rendering remain in "
            "command_info; no shared typed step-info outcome or MCP adapter."
        ),
        capabilities=_WRITE_AND_EXECUTION,
        network_access="optional",
    ),
    WorkflowToolInventory(
        operation_id="workflow.step.list",
        cli_path="specify workflow step list",
        mcp_tool_name="specify_workflow_step_list",
        disposition_reason=(
            "The CLI combines STEP_REGISTRY and StepRegistry dictionaries for display; "
            "no shared typed step-list outcome or MCP adapter."
        ),
        capabilities=_LOCAL_READ,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.step.remove",
        cli_path="specify workflow step remove",
        mcp_tool_name="specify_workflow_step_remove",
        disposition_reason=(
            "Registry removal, direct package deletion and attempted registry restoration "
            "on deletion failure remain in command_remove; no shared typed step-remove "
            "operation or MCP adapter."
        ),
        capabilities=_LOCAL_WRITE,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.step.search",
        cli_path="specify workflow step search",
        mcp_tool_name="specify_workflow_step_search",
        disposition_reason=(
            "StepCatalog.search supplies catalog data but the CLI maps/renders it; "
            "no shared typed step-search outcome or MCP adapter."
        ),
        capabilities=_WRITE_AND_EXECUTION,
        network_access="optional",
    ),
    WorkflowToolInventory(
        operation_id="workflow.step.catalog.add",
        cli_path="specify workflow step catalog add",
        mcp_tool_name="specify_workflow_step_catalog_add",
        disposition_reason=(
            "StepCatalog.add_catalog mutates configuration, but its command-level "
            "request/error/outcome contract and MCP adapter are not defined."
        ),
        capabilities=_LOCAL_WRITE,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.step.catalog.list",
        cli_path="specify workflow step catalog list",
        mcp_tool_name="specify_workflow_step_catalog_list",
        disposition_reason=(
            "StepCatalog.get_catalog_configs returns dictionaries rendered by the CLI; "
            "no shared typed step-catalog-list outcome or MCP adapter."
        ),
        capabilities=_LOCAL_READ,
        network_access="none",
    ),
    WorkflowToolInventory(
        operation_id="workflow.step.catalog.remove",
        cli_path="specify workflow step catalog remove",
        mcp_tool_name="specify_workflow_step_catalog_remove",
        disposition_reason=(
            "StepCatalog.remove_catalog edits configuration, but the CLI maps "
            "arguments/errors; no shared typed removal contract or MCP adapter."
        ),
        capabilities=_LOCAL_WRITE,
        network_access="none",
    ),
)
