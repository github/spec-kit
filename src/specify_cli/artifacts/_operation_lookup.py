"""Shared application operation for ``artifact.lookup``."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypeAlias

from .._file_policy import ProjectPolicyError, project_files
from ..extensions import ExtensionRegistry
from ..integrations import installer
from ..presets import PresetError
from . import (
    ArtifactCatalog,
    ArtifactError,
    ArtifactResolutionError,
    ContributionNotFoundError,
    NotASpecKitProjectError,
)
from ._identifiers import IdentifierComponentError, parse_lookup_id

JsonScalar: TypeAlias = None | bool | int | float | str
JsonProjection: TypeAlias = (
    JsonScalar | list["JsonProjection"] | dict[str, "JsonProjection"]
)


@dataclass(frozen=True)
class ArtifactLookupJsonObject:
    """Immutable string-keyed JSON object used at the operation boundary."""

    entries: tuple[tuple[str, JsonValue], ...]

    def to_json_dict(self) -> dict[str, JsonProjection]:
        return {key: _project_json_value(value) for key, value in self.entries}


JsonValue: TypeAlias = JsonScalar | tuple["JsonValue", ...] | ArtifactLookupJsonObject


@dataclass(frozen=True)
class ArtifactLookupRequest:
    """Explicit project context and contribution identifier."""

    project_directory: Path
    lookup_id: str


@dataclass(frozen=True)
class ArtifactLookupResult:
    """One validated preset or extension manifest contribution."""

    id: str
    layer: Literal["preset", "extension"]
    sourceId: str
    kind: Literal["command", "template", "script", "hook"]
    name: str
    manifestPath: str
    sourcePath: str | None
    contribution: ArtifactLookupJsonObject

    def to_json_dict(self) -> dict[str, JsonProjection]:
        """Return the exact legacy JSON projection used by the CLI."""
        return {
            "id": self.id,
            "layer": self.layer,
            "sourceId": self.sourceId,
            "kind": self.kind,
            "name": self.name,
            "manifestPath": self.manifestPath,
            "sourcePath": self.sourcePath,
            "contribution": self.contribution.to_json_dict(),
        }


class ArtifactLookupError(ArtifactError):
    """Expected transport-neutral failure from ``artifact.lookup``."""

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


class ArtifactLookupProjectDirectoryError(ArtifactLookupError):
    """The supplied project directory is not an absolute path."""

    def __init__(self, project_directory: Path) -> None:
        super().__init__(
            code="invalid_project_directory",
            message="project_directory must be an absolute path",
            details={"project_directory": str(project_directory)},
        )


class ArtifactLookupProjectPolicyError(ArtifactLookupError):
    """The selected project cannot establish its persisted path policy."""

    def __init__(self, project_directory: Path, message: str) -> None:
        super().__init__(
            code="project_policy_error",
            message=message,
            details={"project_directory": str(project_directory)},
        )


class ArtifactLookupProjectError(ArtifactLookupError):
    """The supplied directory is not a Spec Kit project root."""

    def __init__(self, project_directory: Path) -> None:
        super().__init__(
            code="not_a_spec_kit_project",
            message="not a Spec Kit project: no .specify/ directory found",
            details={"project_directory": str(project_directory)},
        )


class ArtifactLookupIdentifierError(ArtifactLookupError):
    """The contribution lookup identifier is structurally invalid."""

    def __init__(self, lookup_id: object) -> None:
        super().__init__(
            code="invalid_lookup_id",
            message=f"unknown contribution {lookup_id}",
            details={"lookup_id": lookup_id},
        )


class ArtifactLookupNotFoundError(ArtifactLookupError):
    """No contribution matched a valid lookup identifier."""

    def __init__(self, lookup_id: str) -> None:
        super().__init__(
            code="unknown_contribution",
            message=f"unknown contribution {lookup_id}",
            details={"lookup_id": lookup_id},
        )


class ArtifactLookupRegistryError(ArtifactLookupError):
    """The extension registry is corrupt or unreadable."""

    def __init__(self, project_directory: Path, lookup_id: str) -> None:
        super().__init__(
            code="corrupt_extension_registry",
            message="artifact resolution failed",
            details={
                "project_directory": str(project_directory),
                "lookup_id": lookup_id,
            },
        )


class ArtifactLookupIntegrationError(ArtifactLookupError):
    """Installed integration loading failed before catalog resolution."""

    def __init__(
        self,
        project_directory: Path,
        lookup_id: str,
        detail: str,
    ) -> None:
        super().__init__(
            code="integration_resolution_failed",
            message=f"artifact resolution failed: {detail}",
            details={
                "project_directory": str(project_directory),
                "lookup_id": lookup_id,
            },
        )


class ArtifactLookupPresetError(ArtifactLookupError):
    """Preset resolution failed while resolving the contribution."""

    def __init__(self, project_directory: Path, lookup_id: str) -> None:
        super().__init__(
            code="preset_resolution_failed",
            message="artifact resolution failed",
            details={
                "project_directory": str(project_directory),
                "lookup_id": lookup_id,
            },
        )


class ArtifactLookupFilesystemError(ArtifactLookupError):
    """A filesystem operation failed while resolving the contribution."""

    def __init__(self, project_directory: Path, lookup_id: str) -> None:
        super().__init__(
            code="filesystem_error",
            message="artifact resolution failed",
            details={
                "project_directory": str(project_directory),
                "lookup_id": lookup_id,
            },
        )


class ArtifactLookupResolutionError(ArtifactLookupError):
    """Artifact catalog resolution failed."""

    def __init__(
        self,
        project_directory: Path,
        lookup_id: str,
        *,
        message: str = "artifact resolution failed",
    ) -> None:
        super().__init__(
            code="artifact_resolution_failed",
            message=message,
            details={
                "project_directory": str(project_directory),
                "lookup_id": lookup_id,
            },
        )


class ArtifactLookupInvalidResultError(ArtifactLookupError):
    """The catalog returned an incomplete or non-JSON-safe result."""

    def __init__(self, project_directory: Path, lookup_id: str) -> None:
        super().__init__(
            code="invalid_operation_result",
            message="artifact resolution failed",
            details={
                "project_directory": str(project_directory),
                "lookup_id": lookup_id,
            },
        )


@dataclass(frozen=True)
class ArtifactLookupOperationDescriptor:
    """Stable metadata shared by delivery adapters for ``artifact.lookup``."""

    operation_id: Literal["artifact.lookup"]
    contract_version: Literal["1"]
    request_type: type[ArtifactLookupRequest]
    result_type: type[ArtifactLookupResult]
    warning_types: tuple[type[object], ...]
    error_types: tuple[type[ArtifactLookupError], ...]
    capabilities: frozenset[Literal["local-read"]]
    network_access: Literal["none"]


ARTIFACT_LOOKUP_OPERATION = ArtifactLookupOperationDescriptor(
    operation_id="artifact.lookup",
    contract_version="1",
    request_type=ArtifactLookupRequest,
    result_type=ArtifactLookupResult,
    warning_types=(),
    error_types=(
        ArtifactLookupProjectDirectoryError,
        ArtifactLookupProjectPolicyError,
        ArtifactLookupProjectError,
        ArtifactLookupIdentifierError,
        ArtifactLookupNotFoundError,
        ArtifactLookupRegistryError,
        ArtifactLookupIntegrationError,
        ArtifactLookupPresetError,
        ArtifactLookupFilesystemError,
        ArtifactLookupResolutionError,
        ArtifactLookupInvalidResultError,
    ),
    capabilities=frozenset({"local-read"}),
    network_access="none",
)

_RESULT_KEYS = {
    "id",
    "layer",
    "sourceId",
    "kind",
    "name",
    "manifestPath",
    "sourcePath",
    "contribution",
}


def _invalid_result(request: ArtifactLookupRequest) -> ArtifactLookupInvalidResultError:
    return ArtifactLookupInvalidResultError(
        Path(request.project_directory),
        request.lookup_id,
    )


def _validate_json_string(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _freeze_json_value(
    value: object,
    request: ArtifactLookupRequest,
) -> JsonValue:
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is int:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise _invalid_result(request)
        return value
    if type(value) is str:
        if not _validate_json_string(value):
            raise _invalid_result(request)
        return value
    if type(value) is list:
        try:
            return tuple(_freeze_json_value(item, request) for item in value)
        except RecursionError as exc:
            raise _invalid_result(request) from exc
    if type(value) is dict:
        entries: list[tuple[str, JsonValue]] = []
        try:
            for key, item in value.items():
                if not _validate_json_string(key):
                    raise _invalid_result(request)
                entries.append((key, _freeze_json_value(item, request)))
        except RecursionError as exc:
            raise _invalid_result(request) from exc
        return ArtifactLookupJsonObject(tuple(entries))
    raise _invalid_result(request)


def _project_json_value(value: JsonValue) -> JsonProjection:
    if isinstance(value, ArtifactLookupJsonObject):
        return value.to_json_dict()
    if isinstance(value, tuple):
        return [_project_json_value(item) for item in value]
    return value


def _convert_catalog_result(
    payload: object,
    request: ArtifactLookupRequest,
    parsed_lookup_id: tuple[str, str, str, str],
) -> ArtifactLookupResult:
    if type(payload) is not dict or set(payload) != _RESULT_KEYS:
        raise _invalid_result(request)

    layer, source_id, kind, name = parsed_lookup_id
    if (
        layer not in ("preset", "extension")
        or kind not in ("command", "template", "script", "hook")
        or payload["id"] != request.lookup_id
        or payload["layer"] != layer
        or payload["sourceId"] != source_id
        or payload["kind"] != kind
        or payload["name"] != name
        or not _validate_json_string(payload["id"])
        or not _validate_json_string(payload["sourceId"])
        or not _validate_json_string(payload["name"])
        or not _validate_json_string(payload["manifestPath"])
        or (
            payload["sourcePath"] is not None
            and not _validate_json_string(payload["sourcePath"])
        )
    ):
        raise _invalid_result(request)

    contribution = _freeze_json_value(payload["contribution"], request)
    if not isinstance(contribution, ArtifactLookupJsonObject):
        raise _invalid_result(request)

    return ArtifactLookupResult(
        id=payload["id"],
        layer=layer,
        sourceId=source_id,
        kind=kind,
        name=name,
        manifestPath=payload["manifestPath"],
        sourcePath=payload["sourcePath"],
        contribution=contribution,
    )


def lookup_artifact(request: ArtifactLookupRequest) -> ArtifactLookupResult:
    """Resolve one manifest contribution for an explicit Spec Kit project."""
    project_directory = Path(request.project_directory)
    if not project_directory.is_absolute():
        raise ArtifactLookupProjectDirectoryError(project_directory)

    try:
        if project_directory.is_dir():
            project_files(project_directory)
    except ProjectPolicyError as exc:
        raise ArtifactLookupProjectPolicyError(
            project_directory,
            str(exc),
        ) from exc
    if not (project_directory / ".specify").is_dir():
        raise ArtifactLookupProjectError(project_directory)

    try:
        installer.load_installed_integrations(project_directory)
    except (installer.IntegrationInstallError, OSError) as exc:
        raise ArtifactLookupIntegrationError(
            project_directory,
            request.lookup_id,
            str(exc),
        ) from exc

    extensions_directory = project_directory / ".specify" / "extensions"
    try:
        if (
            extensions_directory.exists()
            and ExtensionRegistry(extensions_directory).is_corrupt()
        ):
            raise ArtifactLookupRegistryError(
                project_directory,
                request.lookup_id,
            )
    except ArtifactLookupRegistryError:
        raise
    except OSError as exc:
        raise ArtifactLookupFilesystemError(
            project_directory,
            request.lookup_id,
        ) from exc

    if not _validate_json_string(request.lookup_id):
        raise ArtifactLookupIdentifierError(request.lookup_id)
    try:
        parsed_lookup_id = parse_lookup_id(request.lookup_id)
    except IdentifierComponentError as exc:
        raise ArtifactLookupIdentifierError(request.lookup_id) from exc

    if parsed_lookup_id[0] == "project":
        raise ArtifactLookupNotFoundError(request.lookup_id)

    try:
        payload = ArtifactCatalog(project_directory).get_contribution_info(
            request.lookup_id
        )
    except NotASpecKitProjectError as exc:
        raise ArtifactLookupProjectError(project_directory) from exc
    except ContributionNotFoundError as exc:
        raise ArtifactLookupNotFoundError(request.lookup_id) from exc
    except ArtifactResolutionError as exc:
        raise ArtifactLookupResolutionError(
            project_directory,
            request.lookup_id,
            message=exc.message,
        ) from exc
    except PresetError as exc:
        raise ArtifactLookupPresetError(
            project_directory,
            request.lookup_id,
        ) from exc
    except OSError as exc:
        raise ArtifactLookupFilesystemError(
            project_directory,
            request.lookup_id,
        ) from exc

    return _convert_catalog_result(payload, request, parsed_lookup_id)
