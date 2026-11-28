"""Shared, read-only application operation for installed step-type listing."""

from __future__ import annotations

import stat
from contextlib import ExitStack
from dataclasses import dataclass
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
    is imported. The registry is read through the retained project-files
    owner, so the read policy (including Windows junction rejection) applies
    at the read boundary the same way as for workflow listing, and registry
    input over ``StepRegistry.MAX_REGISTRY_BYTES`` is rejected before it is
    parsed. A missing registry still lists built-ins only; a corrupt,
    non-regular, unreadable, policy-rejected, or oversized registry is a
    ``step_registry_read_failed`` error. Result entries stop being built
    once the requested limit is filled.
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
            files = owners.enter_context(project_files(root))
            if not (root / ".specify").is_dir():
                raise WorkflowStepListError(
                    "not_a_spec_kit_project",
                    "Not a Spec Kit project (no .specify/ directory)",
                )
            validate_workflow_storage(root)
        except (ProjectPolicyError, WorkflowStorageError, OSError) as exc:
            raise WorkflowStepListError("unsafe_workflow_storage", str(exc)) from exc

        try:
            installed = StepRegistry(
                root,
                read_files=files,
                max_bytes=StepRegistry.MAX_REGISTRY_BYTES,
            ).list()
        except OSError as exc:
            raise WorkflowStepListError(
                "step_registry_read_failed", f"Failed to read step registry: {exc}"
            ) from exc

    builtin_ids = sorted(BUILTIN_STEP_TYPES)
    installed_ids = sorted(installed)
    total = len(builtin_ids) + len(installed_ids)
    truncated = limit is not None and total > limit
    # Each id yields exactly one item (an entry, or a warning for a
    # non-dict entry), so the total and the truncation flag are known
    # from the counts alone. Build entries only up to the limit.
    take = total if limit is None else min(limit, total)
    items: list[WorkflowStepListEntry | WorkflowStepListWarning] = []
    for key in builtin_ids:
        if len(items) >= take:
            break
        items.append(
            WorkflowStepListEntry(id=key, name=key, version=None, kind="builtin")
        )
    for step_id in installed_ids:
        if len(items) >= take:
            break
        metadata = installed[step_id]
        if not isinstance(metadata, dict):
            items.append(
                WorkflowStepListWarning(
                    step_id=step_id,
                    message=f"Skipping corrupted registry entry '{step_id}'.",
                )
            )
            continue
        items.append(
            WorkflowStepListEntry(
                id=step_id,
                name=str(metadata.get("name", step_id)),
                version=str(metadata.get("version", "?")),
                kind="custom",
            )
        )
    return WorkflowStepListResult(items=tuple(items), truncated=truncated)
