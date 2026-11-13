"""Shared, read-only application operation for configured workflow catalogs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import stat
from typing import Literal

from ..._file_policy import ProjectPolicyError, project_files
from ...file_helper import FileHelperError
from .._storage import WorkflowStorageError, validate_workflow_storage
from ._domain import WorkflowCatalog, WorkflowCatalogError

WORKFLOW_CATALOG_LIST_MAX_LIMIT = 1000


@dataclass(frozen=True)
class WorkflowCatalogListRequest:
    project_directory: Path
    # CLI retains its complete listing. MCP supplies an explicit bounded limit.
    limit: int | None = None


@dataclass(frozen=True)
class WorkflowCatalogSource:
    name: str
    # Exactly as configured, so adapters decide what they may disclose.
    url: str
    priority: int
    install_allowed: bool
    description: str | None


@dataclass(frozen=True)
class WorkflowCatalogListResult:
    items: tuple[WorkflowCatalogSource, ...]
    truncated: bool = False


class WorkflowCatalogListError(Exception):
    """Expected operation failure; adapters own presentation and sanitization."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.details: dict[str, str] = {}
        self.retryable = False
        super().__init__(message)


@dataclass(frozen=True)
class WorkflowCatalogListOperationDescriptor:
    operation_id: Literal["workflow.catalog.list"]
    contract_version: Literal["1"]
    request_type: type[WorkflowCatalogListRequest]
    result_type: type[WorkflowCatalogListResult]
    warning_types: tuple[type[object], ...]
    error_types: tuple[type[WorkflowCatalogListError], ...]
    capabilities: frozenset[Literal["local-read"]]
    network_access: Literal["none"]


WORKFLOW_CATALOG_LIST_OPERATION = WorkflowCatalogListOperationDescriptor(
    operation_id="workflow.catalog.list",
    contract_version="1",
    request_type=WorkflowCatalogListRequest,
    result_type=WorkflowCatalogListResult,
    warning_types=(),
    error_types=(WorkflowCatalogListError,),
    capabilities=frozenset({"local-read"}),
    network_access="none",
)


def list_catalog_sources(
    request: WorkflowCatalogListRequest,
) -> WorkflowCatalogListResult:
    """Resolve the active catalog stack without fetching or caching catalogs."""
    root = request.project_directory
    if not isinstance(root, Path) or not root.is_absolute():
        raise WorkflowCatalogListError(
            "invalid_project_directory", "project_directory must be an absolute path"
        )
    limit = request.limit
    if limit is not None and (
        type(limit) is not int or not 1 <= limit <= WORKFLOW_CATALOG_LIST_MAX_LIMIT
    ):
        raise WorkflowCatalogListError(
            "invalid_limit",
            f"limit must be between 1 and {WORKFLOW_CATALOG_LIST_MAX_LIMIT}",
        )
    try:
        # Unlike is_dir(), stat() preserves permission errors on Python 3.14.
        try:
            root_is_directory = stat.S_ISDIR(root.stat().st_mode)
        except (FileNotFoundError, NotADirectoryError, ValueError):
            root_is_directory = False
        if not root_is_directory:
            raise WorkflowCatalogListError(
                "not_a_spec_kit_project",
                "Not a Spec Kit project (no .specify/ directory)",
            )
        files = project_files(root)
        if not (root / ".specify").is_dir():
            raise WorkflowCatalogListError(
                "not_a_spec_kit_project",
                "Not a Spec Kit project (no .specify/ directory)",
            )
        validate_workflow_storage(root)
        configs = WorkflowCatalog(root, read_files=files).get_catalog_configs()
    except (ProjectPolicyError, WorkflowStorageError, FileHelperError, OSError) as exc:
        raise WorkflowCatalogListError("unsafe_workflow_storage", str(exc)) from exc
    except WorkflowCatalogError as exc:
        # Parser and URL diagnostics can quote a configured URL with its credentials.
        raise WorkflowCatalogListError(
            "invalid_catalog_config", "The workflow catalog configuration is invalid."
        ) from exc

    selected = configs if limit is None else configs[:limit]
    return WorkflowCatalogListResult(
        items=tuple(
            WorkflowCatalogSource(
                name=config["name"],
                url=config["url"],
                priority=config["priority"],
                install_allowed=config["install_allowed"],
                description=config["description"] or None,
            )
            for config in selected
        ),
        truncated=limit is not None and len(configs) > limit,
    )
