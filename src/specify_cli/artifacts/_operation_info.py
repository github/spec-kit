"""Shared application operation for ``artifact.info``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ..presets import PresetError
from . import (
    AmbiguousArtifactError,
    ArtifactCatalog,
    ArtifactError,
    ArtifactKind,
    ArtifactNotFoundError,
    ArtifactResolutionError,
    NotASpecKitProjectError,
)
from ._identifiers import (
    IdentifierComponentError,
    derive_hook_public_id,
    derive_public_id,
    parse_hook_artifact_name,
    validate_component,
)
from .models import HookStackEntry, StackLayer

NamedArtifactKind = Literal["command", "template", "script"]


@dataclass(frozen=True)
class ArtifactInfoRequest:
    """Explicit project context and artifact selection for ``artifact.info``."""

    project_directory: Path
    identifier: str
    kind: ArtifactKind | None = None


@dataclass(frozen=True)
class ArtifactInfoNamedArtifact:
    """One named artifact and its complete ordered composition stack."""

    id: str
    name: str
    kind: NamedArtifactKind
    description: str
    stack: tuple[StackLayer, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "description": self.description,
            "stack": [entry.to_json_dict() for entry in self.stack],
        }


@dataclass(frozen=True)
class ArtifactInfoHookArtifact:
    """One hook artifact and its additive declaration stack."""

    id: str
    name: str
    kind: Literal["hook"]
    description: str
    eventName: str
    targetCommand: str
    registered: bool
    stack: tuple[HookStackEntry, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "description": self.description,
            "eventName": self.eventName,
            "targetCommand": self.targetCommand,
            "registered": self.registered,
            "stack": [entry.to_json_dict() for entry in self.stack],
        }


ArtifactInfoArtifact = ArtifactInfoNamedArtifact | ArtifactInfoHookArtifact


@dataclass(frozen=True)
class ArtifactInfoResult:
    """Transport-neutral typed artifact information."""

    artifact: ArtifactInfoArtifact

    def to_json_dict(self) -> dict[str, Any]:
        return self.artifact.to_json_dict()


class ArtifactInfoError(ArtifactError):
    """Expected transport-neutral failure from ``artifact.info``."""

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


class ArtifactInfoProjectDirectoryError(ArtifactInfoError):
    """The supplied project directory is not an absolute path."""

    def __init__(self, project_directory: Path) -> None:
        super().__init__(
            code="invalid_project_directory",
            message="project_directory must be an absolute path",
            details={"project_directory": str(project_directory)},
        )


class ArtifactInfoProjectError(ArtifactInfoError):
    """The supplied directory is not a Spec Kit project root."""

    def __init__(self, project_directory: Path) -> None:
        super().__init__(
            code="not_a_spec_kit_project",
            message="not a Spec Kit project: no .specify/ directory found",
            details={"project_directory": str(project_directory)},
        )


class ArtifactInfoKindError(ArtifactInfoError):
    """The requested artifact family is not supported."""

    def __init__(self, kind: object) -> None:
        super().__init__(
            code="invalid_artifact_kind",
            message=(
                f"invalid artifact kind {kind!r}: expected one of "
                "command, template, script, hook"
            ),
            details={"kind": kind},
        )


class ArtifactInfoIdentifierError(ArtifactInfoError):
    """The artifact identifier is structurally invalid."""

    def __init__(self, identifier: object) -> None:
        super().__init__(
            code="invalid_artifact_identifier",
            message=f"unknown artifact {identifier}",
            details={"identifier": identifier},
        )


class ArtifactInfoNotFoundError(ArtifactInfoError):
    """No named artifact matched the request."""

    def __init__(self, identifier: str) -> None:
        super().__init__(
            code="unknown_artifact",
            message=f"unknown artifact {identifier}",
            details={"identifier": identifier},
        )


class ArtifactInfoHookNotFoundError(ArtifactInfoError):
    """No hook artifact matched the request."""

    def __init__(self, identifier: str) -> None:
        super().__init__(
            code="unknown_hook",
            message=f"unknown artifact {identifier}",
            details={"identifier": identifier},
        )


class ArtifactInfoAmbiguousError(ArtifactInfoError):
    """A bare artifact name matched more than one artifact family."""

    def __init__(self, identifier: str, message: str) -> None:
        super().__init__(
            code="ambiguous_artifact",
            message=message,
            details={"identifier": identifier},
        )


class ArtifactInfoResolutionError(ArtifactInfoError):
    """Artifact composition could not be resolved."""

    def __init__(self, project_directory: Path, identifier: str) -> None:
        super().__init__(
            code="artifact_resolution_failed",
            message="artifact resolution failed",
            details={
                "project_directory": str(project_directory),
                "identifier": identifier,
            },
        )


class ArtifactInfoInvalidResultError(ArtifactInfoError):
    """The catalog returned an incomplete or inconsistent result."""

    def __init__(self, project_directory: Path, identifier: str) -> None:
        super().__init__(
            code="invalid_operation_result",
            message="artifact resolution failed",
            details={
                "project_directory": str(project_directory),
                "identifier": identifier,
            },
        )


@dataclass(frozen=True)
class ArtifactInfoOperationDescriptor:
    """Stable metadata shared by delivery adapters for ``artifact.info``."""

    operation_id: Literal["artifact.info"]
    contract_version: Literal["1"]
    request_type: type[ArtifactInfoRequest]
    result_type: type[ArtifactInfoResult]
    warning_types: tuple[type[object], ...]
    error_types: tuple[type[ArtifactInfoError], ...]
    capabilities: frozenset[Literal["local-read"]]
    network_access: Literal["none"]


ARTIFACT_INFO_OPERATION = ArtifactInfoOperationDescriptor(
    operation_id="artifact.info",
    contract_version="1",
    request_type=ArtifactInfoRequest,
    result_type=ArtifactInfoResult,
    warning_types=(),
    error_types=(
        ArtifactInfoProjectDirectoryError,
        ArtifactInfoProjectError,
        ArtifactInfoKindError,
        ArtifactInfoIdentifierError,
        ArtifactInfoNotFoundError,
        ArtifactInfoHookNotFoundError,
        ArtifactInfoAmbiguousError,
        ArtifactInfoResolutionError,
        ArtifactInfoInvalidResultError,
    ),
    capabilities=frozenset({"local-read"}),
    network_access="none",
)

_NAMED_RESULT_KEYS = {"id", "name", "kind", "description", "stack"}
_HOOK_RESULT_KEYS = {
    "id",
    "name",
    "kind",
    "description",
    "eventName",
    "targetCommand",
    "registered",
    "stack",
}
_STACK_KEYS = {
    "id",
    "layer",
    "sourceId",
    "presetId",
    "presetName",
    "strategy",
    "active",
    "hidden",
    "manifestPath",
    "lookupId",
    "sourcePath",
}
_HOOK_STACK_KEYS = {
    *_STACK_KEYS,
    "priority",
    "optional",
}


def _is_optional_string(value: object) -> bool:
    return value is None or isinstance(value, str)


def _invalid_result(request: ArtifactInfoRequest) -> ArtifactInfoInvalidResultError:
    return ArtifactInfoInvalidResultError(
        Path(request.project_directory),
        request.identifier,
    )


def _convert_named_stack(
    value: object,
    *,
    artifact_id: str,
    request: ArtifactInfoRequest,
) -> tuple[StackLayer, ...]:
    if not isinstance(value, list) or not value:
        raise _invalid_result(request)

    entries: list[StackLayer] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != _STACK_KEYS:
            raise _invalid_result(request)
        if (
            item["id"] != artifact_id
            or item["layer"] not in (None, "project", "preset", "extension")
            or not _is_optional_string(item["sourceId"])
            or not _is_optional_string(item["presetId"])
            or not _is_optional_string(item["presetName"])
            or item["strategy"] not in ("replace", "wrap", "prepend", "append")
            or not isinstance(item["active"], bool)
            or not isinstance(item["hidden"], bool)
            or not _is_optional_string(item["manifestPath"])
            or not _is_optional_string(item["lookupId"])
            or not _is_optional_string(item["sourcePath"])
        ):
            raise _invalid_result(request)
        entries.append(StackLayer(**item))
    return tuple(entries)


def _convert_hook_stack(
    value: object,
    *,
    artifact_id: str,
    request: ArtifactInfoRequest,
) -> tuple[HookStackEntry, ...]:
    if not isinstance(value, list) or not value:
        raise _invalid_result(request)

    entries: list[HookStackEntry] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != _HOOK_STACK_KEYS:
            raise _invalid_result(request)
        priority = item["priority"]
        if (
            item["id"] != artifact_id
            or item["layer"] not in ("preset", "extension")
            or not isinstance(item["sourceId"], str)
            or not _is_optional_string(item["presetId"])
            or not _is_optional_string(item["presetName"])
            or item["strategy"] != "additive"
            or not isinstance(item["active"], bool)
            or not isinstance(item["hidden"], bool)
            or not isinstance(item["manifestPath"], str)
            or not isinstance(item["lookupId"], str)
            or item["sourcePath"] is not None
            or isinstance(priority, bool)
            or not isinstance(priority, int)
            or not isinstance(item["optional"], bool)
        ):
            raise _invalid_result(request)
        entries.append(HookStackEntry(**item))
    return tuple(entries)


def _convert_catalog_result(
    payload: object,
    request: ArtifactInfoRequest,
) -> ArtifactInfoResult:
    if not isinstance(payload, dict):
        raise _invalid_result(request)

    kind = payload.get("kind")
    if kind == "hook":
        if set(payload) != _HOOK_RESULT_KEYS:
            raise _invalid_result(request)
        artifact_id = payload["id"]
        name = payload["name"]
        description = payload["description"]
        event_name = payload["eventName"]
        target_command = payload["targetCommand"]
        if (
            not isinstance(artifact_id, str)
            or not isinstance(name, str)
            or not isinstance(description, str)
            or not isinstance(event_name, str)
            or not isinstance(target_command, str)
            or not isinstance(payload["registered"], bool)
        ):
            raise _invalid_result(request)
        try:
            expected_id = derive_hook_public_id(event_name, target_command)
        except IdentifierComponentError as exc:
            raise _invalid_result(request) from exc
        if artifact_id != expected_id or name != artifact_id.removeprefix("hook:"):
            raise _invalid_result(request)
        return ArtifactInfoResult(
            artifact=ArtifactInfoHookArtifact(
                id=artifact_id,
                name=name,
                kind="hook",
                description=description,
                eventName=event_name,
                targetCommand=target_command,
                registered=payload["registered"],
                stack=_convert_hook_stack(
                    payload["stack"],
                    artifact_id=artifact_id,
                    request=request,
                ),
            )
        )

    if kind not in ("command", "template", "script"):
        raise _invalid_result(request)
    if set(payload) != _NAMED_RESULT_KEYS:
        raise _invalid_result(request)
    artifact_id = payload["id"]
    name = payload["name"]
    description = payload["description"]
    if (
        not isinstance(artifact_id, str)
        or not isinstance(name, str)
        or not isinstance(description, str)
    ):
        raise _invalid_result(request)
    try:
        expected_id = derive_public_id(kind, name)
    except IdentifierComponentError as exc:
        raise _invalid_result(request) from exc
    if artifact_id != expected_id:
        raise _invalid_result(request)
    return ArtifactInfoResult(
        artifact=ArtifactInfoNamedArtifact(
            id=artifact_id,
            name=name,
            kind=kind,
            description=description,
            stack=_convert_named_stack(
                payload["stack"],
                artifact_id=artifact_id,
                request=request,
            ),
        )
    )


def _validate_identifier(identifier: str, kind: ArtifactKind | None) -> None:
    if kind == "hook":
        if identifier.startswith("hook:"):
            try:
                parse_hook_artifact_name(identifier.removeprefix("hook:"))
            except IdentifierComponentError:
                pass
            else:
                return
        try:
            parse_hook_artifact_name(identifier)
        except IdentifierComponentError as exc:
            raise ArtifactInfoIdentifierError(identifier) from exc
        return

    if ":" not in identifier:
        return

    prefix, _, bare = identifier.partition(":")
    if prefix in ("command", "template", "script"):
        try:
            validate_component(bare, f"{prefix} name")
        except IdentifierComponentError as exc:
            raise ArtifactInfoIdentifierError(identifier) from exc
        return
    if prefix == "hook":
        try:
            parse_hook_artifact_name(bare)
        except IdentifierComponentError as exc:
            raise ArtifactInfoIdentifierError(identifier) from exc
        return
    raise ArtifactInfoIdentifierError(identifier)


def _requests_hook(identifier: str, kind: ArtifactKind | None) -> bool:
    return kind == "hook" or (kind is None and identifier.startswith("hook:"))


def get_artifact_info(request: ArtifactInfoRequest) -> ArtifactInfoResult:
    """Return typed artifact information for an explicit Spec Kit project."""
    project_directory = Path(request.project_directory)
    if not project_directory.is_absolute():
        raise ArtifactInfoProjectDirectoryError(project_directory)

    if request.kind is not None and request.kind not in (
        "command",
        "template",
        "script",
        "hook",
    ):
        raise ArtifactInfoKindError(request.kind)
    if not isinstance(request.identifier, str) or not request.identifier:
        raise ArtifactInfoIdentifierError(request.identifier)
    if not (project_directory / ".specify").is_dir():
        raise ArtifactInfoProjectError(project_directory)
    _validate_identifier(request.identifier, request.kind)

    try:
        payload = ArtifactCatalog(project_directory).get_artifact_info(
            request.identifier,
            kind=request.kind,
        )
    except NotASpecKitProjectError as exc:
        raise ArtifactInfoProjectError(project_directory) from exc
    except AmbiguousArtifactError as exc:
        raise ArtifactInfoAmbiguousError(request.identifier, exc.message) from exc
    except ArtifactNotFoundError as exc:
        if _requests_hook(request.identifier, request.kind):
            raise ArtifactInfoHookNotFoundError(request.identifier) from exc
        raise ArtifactInfoNotFoundError(request.identifier) from exc
    except (ArtifactResolutionError, OSError, PresetError) as exc:
        raise ArtifactInfoResolutionError(
            project_directory,
            request.identifier,
        ) from exc

    return _convert_catalog_result(payload, request)
