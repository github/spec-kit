"""Identifier helpers private to the artifact JSON surface."""

from __future__ import annotations

from typing import Any

PROJECT_OVERRIDE_LAYER = "project"
_ARTIFACT_KINDS = frozenset({"command", "template", "script"})
_LAYER_KINDS = frozenset({PROJECT_OVERRIDE_LAYER, "preset", "extension"})
_HOOK_LAYERS = frozenset({"preset", "extension"})


class IdentifierComponentError(ValueError):
    """Raised when a value cannot be represented in an artifact identifier."""


def validate_component(value: Any, field_label: str) -> str:
    """Return a non-empty string that does not contain the ID delimiter."""
    if not isinstance(value, str):
        raise IdentifierComponentError(
            f"Invalid {field_label}: expected a string, got {type(value).__name__}"
        )
    if not value:
        raise IdentifierComponentError(
            f"Invalid {field_label}: value must not be empty"
        )
    if ":" in value:
        raise IdentifierComponentError(
            f"Invalid {field_label} '{value}': ':' is reserved as an identifier delimiter"
        )
    return value


def derive_public_id(kind: str, name: str) -> str:
    """Build the source-agnostic identifier exposed by ``specify artifact``."""
    validate_component(kind, "kind")
    if kind not in _ARTIFACT_KINDS:
        raise IdentifierComponentError(f"Invalid public artifact kind '{kind}'")
    validate_component(name, "name")
    return f"{kind}:{name}"


def derive_lookup_id(layer: str, source_id: str, kind: str, name: str) -> str:
    """Build an artifact-stack lookup identifier."""
    validate_component(layer, "layer")
    validate_component(source_id, "sourceId")
    validate_component(kind, "kind")
    validate_component(name, "name")
    if layer not in _LAYER_KINDS:
        raise IdentifierComponentError(f"Invalid layer '{layer}'")
    if kind not in _ARTIFACT_KINDS:
        raise IdentifierComponentError(f"Invalid artifact kind '{kind}'")
    if layer == PROJECT_OVERRIDE_LAYER and source_id != "_":
        raise IdentifierComponentError(
            f"Invalid sourceId '{source_id}': project layer requires '_'"
        )
    if layer != PROJECT_OVERRIDE_LAYER and source_id == "_":
        raise IdentifierComponentError(
            "Invalid sourceId '_': reserved for project layer"
        )
    return f"{layer}:{source_id}:{kind}:{name}"


def derive_hook_public_id(event_name: str, command: str) -> str:
    """Build the source-agnostic identifier for a hook artifact."""
    validate_component(event_name, "eventName")
    validate_component(command, "command")
    return f"hook:{event_name}:{command}"


def derive_hook_lookup_id(
    layer: str, source_id: str, event_name: str, command: str
) -> str:
    """Build the artifact-private lookup identifier for a hook declaration."""
    validate_component(layer, "layer")
    validate_component(source_id, "sourceId")
    validate_component(event_name, "eventName")
    validate_component(command, "command")
    if layer not in _HOOK_LAYERS:
        raise IdentifierComponentError(f"Invalid hook layer '{layer}'")
    if source_id == "_":
        raise IdentifierComponentError(
            "Invalid sourceId '_': hooks require a preset or extension source"
        )
    return f"{layer}:{source_id}:hook:{event_name}:{command}"
