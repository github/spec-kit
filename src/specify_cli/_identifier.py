"""Deterministic identifiers for Spec Kit contributions and resolved stack layers.

Every command, template, script, and hook contribution surfaced by a preset or
extension manifest carries a computed opaque ``id`` string, and provenance-backed
layers of a resolved artifact stack carry a matching ``lookupId``. The identifier
value is derived only from author-declared manifest data — it never depends on file
contents, timestamps, archive hashes, installation directory paths, install-time
random values, or list positions. That is what makes identifiers portable
across machines, project locations, and reinstalls, and what lets consumers use
them as stable join keys.

Grammar for provenance-backed named contributions (commands, templates, scripts)::

    id = "{layer}:{sourceId}:{kind}:{name}"

    layer    ∈ {"project", "preset", "extension"}
    sourceId = "_" when layer == "project"; the preset or extension id otherwise
    kind     ∈ {"command", "template", "script"}
    name     = the contribution's declared ``name``

Hook identifiers use ``{eventName}:{command}`` as the name component::

    id = "{layer}:{sourceId}:hook:{eventName}:{command}"

Built-in artifacts have no public layer or lookup identifier. Their public
identifier is source-agnostic: ``"{kind}:{name}"``.

The functions in this module are pure — inputs are strings or in-memory
mappings parsed from a manifest, outputs are strings. None of them read from
disk, look at ``os.environ``, call ``datetime``, or hash file contents. That
guarantee is what preserves portability, and it is enforced by inspection
rather than by runtime checks: any change here that adds an ambient input is a
change that breaks the identifier contract.
"""

from __future__ import annotations

from typing import Any


PROJECT_OVERRIDE_LAYER = "project"
"""Resolver-only layer label for project-local override layers.

Project overrides are a resolver feature — they are not backed by any manifest
contribution. When a resolved artifact stack contains a project-override layer,
its ``lookupId`` uses this label so the round-trip invariant (every layer
carries a ``lookupId``) still holds. No manifest ``iter_contributions()`` will
ever emit a matching ``id``, so consumers see "not found" for the lookup, which
is the correct outcome for a layer with no originating manifest entry.
"""

_LAYER_KINDS = frozenset({PROJECT_OVERRIDE_LAYER, "preset", "extension"})
_CONTRIBUTION_KINDS = frozenset({"command", "template", "script", "hook"})
_NAMED_CONTRIBUTION_KINDS = _CONTRIBUTION_KINDS - {"hook"}
_HOOK_LAYERS = frozenset({"preset", "extension"})


class IdentifierComponentError(ValueError):
    """Raised when a manifest component would break identifier grammar."""


def validate_component(value: Any, field_label: str) -> str:
    """Return ``value`` unchanged if it is a non-empty ``:``-free string.

    Manifest components that appear in an identifier (``layer``, ``sourceId``,
    ``kind``, ``name``, ``eventName``, ``command``) may not contain the ``:``
    delimiter — the grammar has no escape rule. This function is the guard used
    by manifest validators to reject offending values at load time with a clear
    message naming the field.
    """
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


def derive_named_id(layer: str, source_id: str, kind: str, name: str) -> str:
    """Build the identifier string for a named contribution kind.

    Each component is revalidated with :func:`validate_component` before the
    join. Manifest-load-time validators generally validate ahead of the join,
    but resolver callers can pass raw filesystem-derived names (POSIX permits
    ``:`` in filenames the way manifest validators do not), and every layer
    dict downstream relies on ``lookupId`` being a round-trippable string that
    :func:`layer_kind_from_lookup_id` can parse — so this is the shared
    derivation boundary that must enforce the grammar. Callers passing raw
    strings should either pre-validate or handle
    :class:`IdentifierComponentError`.
    """
    validate_component(layer, "layer")
    validate_component(source_id, "sourceId")
    validate_component(kind, "kind")
    if layer not in _LAYER_KINDS:
        raise IdentifierComponentError(f"Invalid layer '{layer}'")
    if kind not in _NAMED_CONTRIBUTION_KINDS:
        raise IdentifierComponentError(f"Invalid named contribution kind '{kind}'")
    validate_component(name, "name")
    return f"{layer}:{source_id}:{kind}:{name}"


def derive_public_id(kind: str, name: str) -> str:
    """Build the source-agnostic public identifier for an artifact."""
    validate_component(kind, "kind")
    if kind not in _NAMED_CONTRIBUTION_KINDS:
        raise IdentifierComponentError(f"Invalid public artifact kind '{kind}'")
    validate_component(name, "name")
    return f"{kind}:{name}"


def layer_kind_from_lookup_id(lookup_id: str) -> str | None:
    """Return the layer segment of a resolved-stack ``lookupId``, or ``None``.

    ``lookupId`` values on resolved stack layers follow the same
    ``"{layer}:..."`` grammar as manifest-contribution ``id`` values (see
    module docstring), including :data:`PROJECT_OVERRIDE_LAYER` for project-local
    override layers.
    This is the single place that knows the set of valid layer prefixes, so
    consumers can classify a lookupId without re-deriving the grammar via
    string-prefix checks of their own.

    Validates the complete shape, not just the presence of a layer prefix:
    named contributions require exactly the four ``{layer}:{sourceId}:{kind}:
    {name}`` components, and hook contributions require exactly the five
    ``{layer}:{sourceId}:hook:{eventName}:{command}`` components, with every
    component non-empty. A value such as ``"preset:x"`` has a recognized layer
    prefix but the wrong number of components, so it is malformed and returns
    ``None`` rather than being treated as authoritative. Hook IDs are only
    valid on preset/extension layers (see :data:`_HOOK_LAYERS`); a value such
    as ``"project:_:hook:some-event:some-command"`` is rejected even though it
    otherwise has the right shape, matching :func:`derive_hook_id`'s refusal
    to build hook IDs for other layers.
    """
    parts = lookup_id.split(":")
    if len(parts) < 4 or any(not part for part in parts):
        return None
    layer = parts[0]
    if layer not in _LAYER_KINDS:
        return None
    if parts[2] not in _CONTRIBUTION_KINDS:
        return None
    expected_len = 5 if parts[2] == "hook" else 4
    if len(parts) != expected_len:
        return None
    if parts[2] == "hook" and layer not in _HOOK_LAYERS:
        return None
    return layer


def is_dotted_command_name(value: str) -> bool:
    """Return ``True`` when ``value`` is a dotted command-style name.

    Command-style names allow lowercase alphanumerics and ``-`` in each segment
    and require at least one ``.`` separator.
    """
    if "." not in value:
        return False
    segments = value.split(".")
    return all(
        segment
        and all((("0" <= char <= "9") or ("a" <= char <= "z") or char == "-") for char in segment)
        for segment in segments
    )


def derive_hook_id(
    layer: str,
    source_id: str,
    event_name: str,
    command: str,
) -> str:
    """Build the identifier string for a hook contribution.

    Each component is revalidated with :func:`validate_component` — same
    contract as :func:`derive_named_id`.
    """
    validate_component(layer, "layer")
    validate_component(source_id, "sourceId")
    if layer not in _HOOK_LAYERS:
        raise IdentifierComponentError(f"Invalid layer '{layer}'")
    validate_component(event_name, "eventName")
    validate_component(command, "command")
    return f"{layer}:{source_id}:hook:{event_name}:{command}"
