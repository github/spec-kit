"""Deterministic identifiers for Spec Kit contributions and resolved stack layers.

Every command, template, script, and hook contribution surfaced by a preset or
extension manifest carries a computed opaque ``id`` string, and every layer of a
resolved artifact stack carries a matching ``lookupId``. The identifier value is
derived only from author-declared manifest data — it never depends on file
contents, timestamps, archive hashes, installation directory paths, install-time
random values, or list positions. That is what makes identifiers portable
across machines, project locations, and reinstalls, and what lets consumers use
them as stable join keys.

Grammar for named contributions (commands, templates, scripts)::

    id = "{layer}:{sourceId}:{kind}:{name}"

    layer    ∈ {"core", "preset", "extension"}
    sourceId = "_" when layer == "core"; the preset id or extension id otherwise
    kind     ∈ {"command", "template", "script", "hook"}
    name     = the contribution's declared ``name``

Hook identifiers use ``{eventName}:{command}`` as the name component::

    id = "{layer}:{sourceId}:hook:{eventName}:{command}[:{discriminator}]"

The 12-lowercase-hex discriminator is appended only when at least one sibling
hook in the same source shares the same ``(eventName, command)`` pair, and it is
computed by SHA-256 of a canonical JSON serialization of the hook entry's
declared fields (with ``eventName`` and ``command`` removed, since they already
appear in the identifier prefix). Two hook entries in the same source whose
declared fields produce byte-identical canonical JSON are rejected at manifest
load time — they are semantically identical listeners.

The functions in this module are pure — inputs are strings or in-memory
mappings parsed from a manifest, outputs are strings. None of them read from
disk, look at ``os.environ``, call ``datetime``, or hash file contents. That
guarantee is what preserves portability, and it is enforced by inspection
rather than by runtime checks: any change here that adds an ambient input is a
change that breaks the identifier contract.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping


PROJECT_OVERRIDE_LAYER = "project"
"""Resolver-only layer label for project-local override layers.

Project overrides are a resolver feature — they are not backed by any manifest
contribution. When a resolved artifact stack contains a project-override layer,
its ``lookupId`` uses this label so the round-trip invariant (every layer
carries a ``lookupId``) still holds. No manifest ``iter_contributions()`` will
ever emit a matching ``id``, so consumers see "not found" for the lookup, which
is the correct outcome for a layer with no originating manifest entry.
"""

_DISCRIMINATOR_LENGTH = 12


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

    Callers are expected to have already validated each component with
    :func:`validate_component` at manifest-load time; this function does not
    revalidate — it is a pure string join so the identifier can be computed
    cheaply on every read.
    """
    return f"{layer}:{source_id}:{kind}:{name}"


_LAYER_KINDS = frozenset({"core", PROJECT_OVERRIDE_LAYER, "preset", "extension"})


def layer_kind_from_lookup_id(lookup_id: str) -> str | None:
    """Return the layer segment of a resolved-stack ``lookupId``, or ``None``.

    ``lookupId`` values on resolved stack layers follow the same
    ``"{layer}:..."`` grammar as manifest-contribution ``id`` values (see
    module docstring), with ``layer`` additionally taking on
    :data:`PROJECT_OVERRIDE_LAYER` for resolver-only project-override layers.
    This is the single place that knows the set of valid layer prefixes, so
    consumers can classify a lookupId without re-deriving the grammar via
    string-prefix checks of their own.
    """
    layer, _, rest = lookup_id.partition(":")
    if not rest or layer not in _LAYER_KINDS:
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


def canonical_json(value: Any) -> bytes:
    """Serialize ``value`` to a canonical UTF-8 JSON byte string.

    Mapping keys are sorted lexicographically at every depth, list order is
    preserved (author intent), whitespace is stripped, and non-ASCII characters
    are emitted verbatim. This is the byte string that the hook discriminator
    hashes and that the manifest loader uses to detect byte-identical duplicate
    hook entries.
    """
    normalized = _normalize_for_canonical_json(value)
    return json.dumps(
        normalized,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _normalize_for_canonical_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _normalize_for_canonical_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_for_canonical_json(v) for v in value]
    return value


def _has_hook_sibling_collision(
    event_name: str,
    command: str,
    siblings: Iterable[Mapping[str, Any]],
) -> bool:
    """Return True when at least one sibling shares the same event/command pair.

    ``siblings`` is the full same-source hook entry list including the entry
    whose identifier is being derived. A collision therefore means at least two
    entries share the pair.
    """
    seen = 0
    for entry in siblings:
        if entry.get("eventName") == event_name and entry.get("command") == command:
            seen += 1
            if seen >= 2:
                return True
    return False


def hook_discriminator(declared_fields: Mapping[str, Any]) -> str:
    """Compute the 12-hex-char SHA-256 discriminator for a hook entry.

    ``declared_fields`` is the entry as parsed from the manifest with
    ``eventName`` and ``command`` removed — those two values already appear in
    the identifier prefix, so hashing them would only reflect information the
    consumer can already read.
    """
    return hashlib.sha256(canonical_json(declared_fields)).hexdigest()[:_DISCRIMINATOR_LENGTH]


def derive_hook_id(
    layer: str,
    source_id: str,
    event_name: str,
    command: str,
    siblings: Iterable[Mapping[str, Any]],
    own_declared_fields: Mapping[str, Any],
) -> str:
    """Build the identifier string for a hook contribution.

    The discriminator suffix is appended only when at least one sibling in the
    same source shares the same ``(event_name, command)`` prefix. That keeps the
    common case terse and the collision case unambiguous. ``siblings`` must
    include every hook entry declared under this source (including the one
    whose identifier is being derived); the function decides on its own whether
    a collision exists.
    """
    base = f"{layer}:{source_id}:hook:{event_name}:{command}"
    if _has_hook_sibling_collision(event_name, command, siblings):
        return f"{base}:{hook_discriminator(own_declared_fields)}"
    return base
