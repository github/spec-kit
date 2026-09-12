"""Identifier helpers private to the artifact JSON surface."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, unquote_to_bytes

from .._contribution_ids import (
    PROJECT_OVERRIDE_LAYER,
    IdentifierComponentError,
    derive_lookup_id,
    validate_component,
)

_ARTIFACT_KINDS = frozenset({"command", "template", "script"})
_HOOK_LAYERS = frozenset({"preset", "extension"})
_INVALID_PERCENT_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")


def derive_public_id(kind: str, name: str) -> str:
    """Build the source-agnostic identifier exposed by ``specify artifact``."""
    validate_component(kind, "kind")
    if kind not in _ARTIFACT_KINDS:
        raise IdentifierComponentError(f"Invalid public artifact kind '{kind}'")
    validate_component(name, "name")
    return f"{kind}:{name}"


def derive_hook_public_id(event_name: str, command: str) -> str:
    """Build the source-agnostic identifier for a hook artifact."""
    encoded_event = _encode_hook_component(event_name, "eventName")
    encoded_command = _encode_hook_component(command, "command")
    return f"hook:{encoded_event}:{encoded_command}"


def derive_hook_lookup_id(
    layer: str, source_id: str, event_name: str, command: str
) -> str:
    """Build the artifact-private lookup identifier for a hook declaration."""
    validate_component(layer, "layer")
    validate_component(source_id, "sourceId")
    encoded_event = _encode_hook_component(event_name, "eventName")
    encoded_command = _encode_hook_component(command, "command")
    if layer not in _HOOK_LAYERS:
        raise IdentifierComponentError(f"Invalid hook layer '{layer}'")
    if source_id == "_":
        raise IdentifierComponentError(
            "Invalid sourceId '_': hooks require a preset or extension source"
        )
    return f"{layer}:{source_id}:hook:{encoded_event}:{encoded_command}"


def parse_hook_artifact_name(name: str) -> tuple[str, str]:
    """Decode the ``{eventName}:{targetCommand}`` portion of a hook artifact ID."""
    encoded_event, separator, encoded_command = name.partition(":")
    if not separator or ":" in encoded_command:
        raise IdentifierComponentError("Invalid hook artifact name")
    return (
        _decode_hook_component(encoded_event, "eventName"),
        _decode_hook_component(encoded_command, "command"),
    )


def _encode_hook_component(value: Any, field_label: str) -> str:
    """Encode one hook ID component without narrowing manifest syntax."""
    if not isinstance(value, str):
        raise IdentifierComponentError(
            f"Invalid {field_label}: expected a string, got {type(value).__name__}"
        )
    if not value:
        raise IdentifierComponentError(
            f"Invalid {field_label}: value must not be empty"
        )
    try:
        return quote(value, safe="")
    except UnicodeEncodeError as exc:
        raise IdentifierComponentError(
            f"Invalid {field_label}: value cannot be UTF-8 encoded"
        ) from exc


def _decode_hook_component(value: str, field_label: str) -> str:
    """Decode one hook ID component, rejecting malformed percent escapes."""
    validate_component(value, field_label)
    if _INVALID_PERCENT_ESCAPE.search(value):
        raise IdentifierComponentError(
            f"Invalid {field_label}: malformed percent escape"
        )
    try:
        decoded = unquote_to_bytes(value).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IdentifierComponentError(
            f"Invalid {field_label}: value is not valid UTF-8"
        ) from exc
    if not decoded:
        raise IdentifierComponentError(
            f"Invalid {field_label}: value must not be empty"
        )
    return decoded
