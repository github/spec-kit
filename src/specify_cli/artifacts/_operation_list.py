"""Shared application operation for the ``artifact.list`` inventory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypedDict, cast

from ..presets import PresetError
from . import (
    ArtifactCatalog,
    ArtifactError,
    ArtifactResolutionError,
    NotASpecKitProjectError,
)


class ArtifactListStackEntry(TypedDict):
    """Transport-neutral composition entry for a named artifact."""

    id: str
    layer: Literal["project", "preset", "extension"] | None
    sourceId: str | None
    presetId: str | None
    presetName: str | None
    strategy: Literal["replace", "wrap", "prepend", "append"]
    active: bool
    hidden: bool
    manifestPath: str | None
    lookupId: str | None
    sourcePath: str | None


class ArtifactListHookStackEntry(TypedDict):
    """Transport-neutral composition entry for a hook artifact."""

    id: str
    layer: Literal["preset", "extension"]
    sourceId: str
    presetId: str | None
    presetName: str | None
    strategy: Literal["additive"]
    active: bool
    hidden: bool
    manifestPath: str
    lookupId: str
    sourcePath: None
    priority: int
    optional: bool


class ArtifactListRow(TypedDict):
    """One artifact inventory row shared by delivery adapters."""

    id: str
    name: str
    kind: Literal["command", "template", "script"]
    description: str
    stack: list[ArtifactListStackEntry]


class ArtifactListHookRow(TypedDict):
    """One hook inventory row shared by delivery adapters."""

    id: str
    name: str
    kind: Literal["hook"]
    description: str
    eventName: str
    targetCommand: str
    registered: bool
    stack: list[ArtifactListHookStackEntry]


ArtifactListItem = ArtifactListRow | ArtifactListHookRow


@dataclass(frozen=True)
class ArtifactListRequest:
    """Explicit project context for the ``artifact.list`` operation."""

    project_directory: Path


@dataclass(frozen=True)
class ArtifactListResult:
    """Transport-neutral artifact inventory."""

    rows: tuple[ArtifactListItem, ...]


class ArtifactListError(ArtifactError):
    """Expected transport-neutral failure from ``artifact.list``."""

    code: str
    details: dict[str, Any]
    retryable: bool

    def __init__(
        self,
        *,
        code: str,
        message: str,
        details: dict[str, Any],
        retryable: bool = False,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details
        self.retryable = retryable
        super().__init__(message)


class ArtifactListProjectError(ArtifactListError):
    """The supplied directory is not a Spec Kit project root."""

    def __init__(self, project_directory: Path) -> None:
        super().__init__(
            code="not_a_spec_kit_project",
            message="not a Spec Kit project: no .specify/ directory found",
            details={"project_directory": str(project_directory)},
        )


class ArtifactListResolutionError(ArtifactListError):
    """The artifact inventory could not be resolved."""

    def __init__(self, project_directory: Path) -> None:
        super().__init__(
            code="artifact_resolution_failed",
            message="artifact resolution failed",
            details={"project_directory": str(project_directory)},
        )


@dataclass(frozen=True)
class ArtifactListOperationDescriptor:
    """Stable metadata shared by delivery adapters for ``artifact.list``."""

    operation_id: Literal["artifact.list"]
    contract_version: Literal["1"]
    request_type: type[ArtifactListRequest]
    result_type: type[ArtifactListResult]
    warning_types: tuple[type[object], ...]
    error_types: tuple[type[ArtifactListError], ...]
    capabilities: frozenset[Literal["local-read"]]
    network_access: Literal["none"]


ARTIFACT_LIST_OPERATION = ArtifactListOperationDescriptor(
    operation_id="artifact.list",
    contract_version="1",
    request_type=ArtifactListRequest,
    result_type=ArtifactListResult,
    warning_types=(),
    error_types=(ArtifactListProjectError, ArtifactListResolutionError),
    capabilities=frozenset({"local-read"}),
    network_access="none",
)


def list_artifacts(request: ArtifactListRequest) -> ArtifactListResult:
    """Return the complete typed artifact inventory for an explicit project."""
    project_directory = Path(request.project_directory)
    if not project_directory.is_absolute():
        raise ArtifactListProjectError(project_directory)

    try:
        rows = ArtifactCatalog(project_directory).list_artifacts_with_stack()
    except NotASpecKitProjectError as exc:
        raise ArtifactListProjectError(project_directory) from exc
    except (ArtifactResolutionError, OSError, PresetError) as exc:
        raise ArtifactListResolutionError(project_directory) from exc

    return ArtifactListResult(
        rows=tuple(cast(ArtifactListItem, row) for row in rows),
    )
