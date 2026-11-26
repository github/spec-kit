"""Shared, read-only application operation for installed step-type listing."""

from __future__ import annotations

import stat
from contextlib import ExitStack
from dataclasses import dataclass
from itertools import islice
from pathlib import Path
from typing import Literal

from ..._file_policy import ProjectPolicyError, project_files
from .. import BUILTIN_STEP_TYPES
from .._storage import WorkflowStorageError, validate_workflow_storage
from .catalog import StepRegistry

WORKFLOW_STEP_LIST_MAX_LIMIT = 1000


@dataclass(frozen=True)
class WorkflowStepListRequest:
    project_directory: Path
    # CLI retains its complete listing. MCP supplies an explicit bounded limit.
    limit: int | None = None


@dataclass(frozen=True)
class WorkflowStepListEntry:
    id: str
    name: str
    version: str | None
    kind: Literal["builtin", "custom"]


@dataclass(frozen=True)
class WorkflowStepListWarning:
    step_id: str
    message: str
    code: Literal["invalid_registry_entry"] = "invalid_registry_entry"
    kind: Literal["warning"] = "warning"


@dataclass(frozen=True)
class WorkflowStepListResult:
    # Built-ins first (sorted), then installed entries (sorted by id).
    items: tuple[WorkflowStepListEntry | WorkflowStepListWarning, ...]
    truncated: bool = False


class WorkflowStepListError(Exception):
    """Expected operation failure; adapters own presentation and sanitization."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.details: dict[str, str] = {}
        self.retryable = False
        super().__init__(message)


@dataclass(frozen=True)
class WorkflowStepListOperationDescriptor:
    operation_id: Literal["workflow.step.list"]
    contract_version: Literal["1"]
    request_type: type[WorkflowStepListRequest]
    result_type: type[WorkflowStepListResult]
    warning_types: tuple[type[WorkflowStepListWarning], ...]
    error_types: tuple[type[WorkflowStepListError], ...]
    capabilities: frozenset[Literal["local-read"]]
    network_access: Literal["none"]


WORKFLOW_STEP_LIST_OPERATION = WorkflowStepListOperationDescriptor(
    operation_id="workflow.step.list",
    contract_version="1",
    request_type=WorkflowStepListRequest,
    result_type=WorkflowStepListResult,
    warning_types=(WorkflowStepListWarning,),
    error_types=(WorkflowStepListError,),
    capabilities=frozenset({"local-read"}),
    network_access="none",
)


def list_step_types(request: WorkflowStepListRequest) -> WorkflowStepListResult:
    """Read built-in and installed step types without importing custom steps.

    Built-ins come from the immutable ``BUILTIN_STEP_TYPES`` snapshot, not the
    live ``STEP_REGISTRY``: in a long-lived MCP server process a custom step
    loaded for one project would otherwise look built-in for the next.
    Installed entries come from the step registry file only; no step package
    is imported. The registry loader is read-only and refuses symlinked
    parents and registry files, and the project-files owner is entered first
    so the project policy boundary (e.g. ``allow_symlinks``) is enforced the
    same way as for workflow listing.
    """
    root = request.project_directory
    if not isinstance(root, Path) or not root.is_absolute():
        raise WorkflowStepListError(
            "invalid_project_directory", "project_directory must be an absolute path"
        )
    limit = request.limit
    if limit is not None and (
        type(limit) is not int or not 1 <= limit <= WORKFLOW_STEP_LIST_MAX_LIMIT
    ):
        raise WorkflowStepListError(
            "invalid_limit",
            f"limit must be between 1 and {WORKFLOW_STEP_LIST_MAX_LIMIT}",
        )
    with ExitStack() as owners:
        try:
            # Unlike is_dir(), stat() preserves permission errors on Python 3.14.
            try:
                root_is_directory = stat.S_ISDIR(root.stat().st_mode)
            except (FileNotFoundError, NotADirectoryError, ValueError):
                root_is_directory = False
            if not root_is_directory:
                raise WorkflowStepListError(
                    "not_a_spec_kit_project",
                    "Not a Spec Kit project (no .specify/ directory)",
                )
            owners.enter_context(project_files(root))
            if not (root / ".specify").is_dir():
                raise WorkflowStepListError(
                    "not_a_spec_kit_project",
                    "Not a Spec Kit project (no .specify/ directory)",
                )
            validate_workflow_storage(root)
        except (ProjectPolicyError, WorkflowStorageError, OSError) as exc:
            raise WorkflowStepListError("unsafe_workflow_storage", str(exc)) from exc

        try:
            installed = StepRegistry(root).list()
        except OSError as exc:
            raise WorkflowStepListError(
                "step_registry_read_failed", f"Failed to read step registry: {exc}"
            ) from exc

    ordered: list[WorkflowStepListEntry | WorkflowStepListWarning] = [
        WorkflowStepListEntry(id=key, name=key, version=None, kind="builtin")
        for key in sorted(BUILTIN_STEP_TYPES)
    ]
    for step_id in sorted(installed):
        metadata = installed[step_id]
        if not isinstance(metadata, dict):
            ordered.append(
                WorkflowStepListWarning(
                    step_id=step_id,
                    message=f"Skipping corrupted registry entry '{step_id}'.",
                )
            )
            continue
        ordered.append(
            WorkflowStepListEntry(
                id=step_id,
                name=str(metadata.get("name", step_id)),
                version=str(metadata.get("version", "?")),
                kind="custom",
            )
        )
    selected = ordered if limit is None else list(islice(ordered, limit))
    return WorkflowStepListResult(
        items=tuple(selected), truncated=limit is not None and len(ordered) > limit
    )
