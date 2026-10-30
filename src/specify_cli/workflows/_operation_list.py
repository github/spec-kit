"""Shared, read-only application operation for installed workflow listing."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
from pathlib import Path
import stat
from typing import Literal

from .._file_policy import ProjectPolicyError, project_files
from ._storage import WorkflowStorageError, validate_workflow_storage
from .catalog import WorkflowRegistry

WORKFLOW_LIST_MAX_LIMIT = 1000


@dataclass(frozen=True)
class WorkflowListRequest:
    project_directory: Path
    # CLI retains its complete listing. MCP supplies an explicit bounded limit.
    limit: int | None = None


@dataclass(frozen=True)
class WorkflowListEntry:
    id: str
    name: str
    version: str
    description: str | None
    enabled: bool
    kind: Literal["workflow"] = "workflow"


@dataclass(frozen=True)
class WorkflowListWarning:
    workflow_id: str
    message: str
    code: Literal["invalid_registry_entry"] = "invalid_registry_entry"
    kind: Literal["warning"] = "warning"


@dataclass(frozen=True)
class WorkflowListResult:
    # Warnings stay in registry order, including an all-invalid registry.
    items: tuple[WorkflowListEntry | WorkflowListWarning, ...]
    truncated: bool = False


class WorkflowListError(Exception):
    """Expected operation failure; adapters own presentation and sanitization."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.details: dict[str, str] = {}
        self.retryable = False
        super().__init__(message)


@dataclass(frozen=True)
class WorkflowListOperationDescriptor:
    operation_id: Literal["workflow.list"]
    contract_version: Literal["1"]
    request_type: type[WorkflowListRequest]
    result_type: type[WorkflowListResult]
    warning_types: tuple[type[WorkflowListWarning], ...]
    error_types: tuple[type[WorkflowListError], ...]
    capabilities: frozenset[Literal["local-read"]]
    network_access: Literal["none"]


WORKFLOW_LIST_OPERATION = WorkflowListOperationDescriptor(
    operation_id="workflow.list",
    contract_version="1",
    request_type=WorkflowListRequest,
    result_type=WorkflowListResult,
    warning_types=(WorkflowListWarning,),
    error_types=(WorkflowListError,),
    capabilities=frozenset({"local-read"}),
    network_access="none",
)


def list_workflows(request: WorkflowListRequest) -> WorkflowListResult:
    """Read the registry without importing custom steps or repairing its contents."""
    root = request.project_directory
    if not isinstance(root, Path) or not root.is_absolute():
        raise WorkflowListError(
            "invalid_project_directory", "project_directory must be an absolute path"
        )
    limit = request.limit
    if limit is not None and (
        type(limit) is not int or not 1 <= limit <= WORKFLOW_LIST_MAX_LIMIT
    ):
        raise WorkflowListError(
            "invalid_limit", f"limit must be between 1 and {WORKFLOW_LIST_MAX_LIMIT}"
        )
    try:
        # Unlike is_dir(), stat() preserves permission errors on Python 3.14.
        try:
            root_is_directory = stat.S_ISDIR(root.stat().st_mode)
        except (FileNotFoundError, NotADirectoryError, ValueError):
            root_is_directory = False
        if not root_is_directory:
            raise WorkflowListError(
                "not_a_spec_kit_project",
                "Not a Spec Kit project (no .specify/ directory)",
            )
        files = project_files(root)
        if not (root / ".specify").is_dir():
            raise WorkflowListError(
                "not_a_spec_kit_project",
                "Not a Spec Kit project (no .specify/ directory)",
            )
        validate_workflow_storage(root)
    except (ProjectPolicyError, WorkflowStorageError, OSError) as exc:
        raise WorkflowListError("unsafe_workflow_storage", str(exc)) from exc

    try:
        installed = WorkflowRegistry(root, read_files=files).list()
    except OSError as exc:
        raise WorkflowListError(
            "workflow_registry_read_failed", f"Failed to read workflow registry: {exc}"
        ) from exc

    items: list[WorkflowListEntry | WorkflowListWarning] = []
    selected = installed.items() if limit is None else islice(installed.items(), limit)
    for workflow_id, metadata in selected:
        if not isinstance(metadata, dict):
            items.append(
                WorkflowListWarning(
                    workflow_id=workflow_id,
                    message=f"Skipping corrupted registry entry '{workflow_id}'.",
                )
            )
            continue
        description = metadata.get("description", "")
        items.append(
            WorkflowListEntry(
                id=workflow_id,
                name=str(metadata.get("name", workflow_id)),
                version=str(metadata.get("version", "?")),
                description=str(description) if description else None,
                enabled=bool(metadata.get("enabled", True)),
            )
        )
    return WorkflowListResult(
        items=tuple(items), truncated=limit is not None and len(installed) > limit
    )
