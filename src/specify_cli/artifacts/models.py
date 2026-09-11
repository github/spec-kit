"""Public data contracts and errors for artifact inspection."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Literal

ArtifactKind = Literal["command", "template", "script", "hook"]
LayerName = Literal["project", "preset", "extension"]
Strategy = Literal["replace", "wrap", "prepend", "append"]
HookLayerName = Literal["preset", "extension"]


@dataclass(frozen=True)
class Artifact:
    """One row in the flat artifact inventory."""

    id: str
    name: str
    kind: ArtifactKind
    description: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "description": self.description,
        }


@dataclass(frozen=True)
class StackLayer:
    """One row in an artifact's ordered composition stack.

    ``id`` is the source-agnostic round-trip key for the artifact this stack
    row belongs to. ``lookupId`` identifies a specific non-core contribution
    when one exists.
    """

    id: str
    layer: LayerName | None
    sourceId: str | None
    presetId: str | None
    presetName: str | None
    strategy: Strategy
    active: bool
    hidden: bool
    manifestPath: str | None
    lookupId: str | None
    sourcePath: str | None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "layer": self.layer,
            "sourceId": self.sourceId,
            "presetId": self.presetId,
            "presetName": self.presetName,
            "strategy": self.strategy,
            "active": self.active,
            "hidden": self.hidden,
            "manifestPath": self.manifestPath,
            "lookupId": self.lookupId,
            "sourcePath": self.sourcePath,
        }


@dataclass(frozen=True)
class HookArtifact:
    """One hook row keyed by its event and target command."""

    id: str
    name: str
    kind: Literal["hook"]
    description: str
    eventName: str
    targetCommand: str
    registered: bool

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "description": self.description,
            "eventName": self.eventName,
            "targetCommand": self.targetCommand,
            "registered": self.registered,
        }


@dataclass(frozen=True)
class HookStackEntry:
    """One additive hook declaration in a hook artifact stack."""

    id: str
    layer: HookLayerName
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

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "layer": self.layer,
            "sourceId": self.sourceId,
            "presetId": self.presetId,
            "presetName": self.presetName,
            "strategy": self.strategy,
            "active": self.active,
            "hidden": self.hidden,
            "manifestPath": self.manifestPath,
            "lookupId": self.lookupId,
            "sourcePath": self.sourcePath,
            "priority": self.priority,
            "optional": self.optional,
        }


class ArtifactError(Exception):
    """Base class for artifact command errors with stable messages."""

    message: str


class ArtifactNotFoundError(ArtifactError):
    def __init__(self, name: str) -> None:
        self.message = f"unknown artifact {name}"
        super().__init__(self.message)


class AmbiguousArtifactError(ArtifactError):
    def __init__(self, name: str, kinds: Iterable[str]) -> None:
        kinds_list = sorted(kinds)
        self.message = f"ambiguous artifact {name}: matches kinds {kinds_list}"
        super().__init__(self.message)


class NotASpecKitProjectError(ArtifactError):
    def __init__(self) -> None:
        self.message = "not a Spec Kit project: no .specify/ directory found"
        super().__init__(self.message)


class ArtifactResolutionError(ArtifactError):
    def __init__(self) -> None:
        self.message = "artifact resolution failed"
        super().__init__(self.message)


__all__ = [
    "AmbiguousArtifactError",
    "Artifact",
    "ArtifactError",
    "ArtifactKind",
    "ArtifactNotFoundError",
    "ArtifactResolutionError",
    "HookArtifact",
    "HookLayerName",
    "HookStackEntry",
    "LayerName",
    "NotASpecKitProjectError",
    "StackLayer",
    "Strategy",
]
