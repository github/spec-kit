"""Capability processor for cross-agent extension command templates.

Resolves Handlebars-style capability syntax at install time:

- ``{{#if capability_name}}...{{else}}...{{/if}}`` conditionals
- ``{{#if capability_name.sub_property}}`` nested checks
- ``{{tool:capability_name}}`` tool name substitutions

This module is deliberately separate from the Jinja2-based workflow
expressions engine (``expressions.py``).  Command templates use simpler
syntax and operate on a different file type.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class CapabilitySyntaxError(Exception):
    """Raised when capability template syntax is malformed.

    Attributes:
        errors: List of human-readable error descriptions.
    """

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(
            "Malformed capability syntax:\n" + "\n".join(f"  - {e}" for e in errors)
        )


# ---------------------------------------------------------------------------
# Tool reference substitution
# ---------------------------------------------------------------------------

#: Matches ``{{tool:capability_name}}`` tokens.
_TOOL_REF_RE = re.compile(r"\{\{tool:(\w+)\}\}")


def resolve_tool_references(content: str, capabilities: dict[str, Any]) -> str:
    """Replace ``{{tool:capability_name}}`` with agent-specific tool names.

    For each match, looks up *capabilities[name]* and extracts the
    ``"tool"`` value.  If the capability is missing or has no ``tool``
    key, the reference is replaced with an empty string and a warning
    is emitted.
    """

    def _replace(match: re.Match[str]) -> str:
        cap_name = match.group(1)
        cap = capabilities.get(cap_name)
        if isinstance(cap, dict) and "tool" in cap:
            return str(cap["tool"])
        logger.warning(
            "Capability '%s' not found or has no tool name; "
            "replacing {{tool:%s}} with empty string.",
            cap_name,
            cap_name,
        )
        return ""

    return _TOOL_REF_RE.sub(_replace, content)


# ---------------------------------------------------------------------------
# Conditional block processing
# ---------------------------------------------------------------------------

#: Matches the innermost ``{{#if}}...{{/if}}`` block (content contains
#: neither nested ``{{#if`` nor ``{{/if}}``).  Used iteratively to
#: resolve nested blocks inside-out.
_INNER_IF_RE = re.compile(
    r"\{\{#if\s+([\w.]+)\}\}"  # opening tag with capability path
    r"((?:(?!\{\{#if\s)(?!\{\{/if\}\}).)*?)"  # true-branch (no nested if/endif)
    r"(?:\{\{else\}\}"  # optional else
    r"((?:(?!\{\{#if\s)(?!\{\{/if\}\}).)*?))?"  # false-branch
    r"\{\{/if\}\}",  # closing tag
    re.DOTALL,
)


def _lookup_capability(path: str, capabilities: dict[str, Any]) -> bool:
    """Evaluate a dotted capability path against *capabilities*.

    ``"subagents"`` checks that the key exists and the value is truthy
    (non-empty dict).  ``"subagents.background"`` additionally checks
    the boolean sub-property.
    """
    parts = path.split(".", 1)
    cap_name = parts[0]
    cap = capabilities.get(cap_name)
    if not cap or not isinstance(cap, dict):
        return False
    if len(parts) == 1:
        # Top-level check: capability exists and is non-empty
        return bool(cap)
    # Sub-property check
    sub_key = parts[1]
    return bool(cap.get(sub_key, False))


def resolve_conditionals(content: str, capabilities: dict[str, Any]) -> str:
    """Process ``{{#if}}`` / ``{{else}}`` / ``{{/if}}`` blocks.

    Supports nested conditionals and dotted sub-property paths.
    Uses an iterative inside-out approach: repeatedly resolves the
    innermost ``{{#if}}...{{/if}}`` block until none remain.
    """
    max_iterations = 100  # safety guard against infinite loops
    for _ in range(max_iterations):
        match = _INNER_IF_RE.search(content)
        if not match:
            break
        cap_path = match.group(1)
        true_branch = match.group(2)
        false_branch = match.group(3) if match.group(3) is not None else ""

        if _lookup_capability(cap_path, capabilities):
            replacement = true_branch
        else:
            replacement = false_branch

        content = content[: match.start()] + replacement + content[match.end() :]
    else:
        if _INNER_IF_RE.search(content):
            logger.warning(
                "Capability conditional resolution hit iteration limit (%d); "
                "some {{#if}} blocks remain unresolved.",
                max_iterations,
            )

    return content


# ---------------------------------------------------------------------------
# Syntax validation
# ---------------------------------------------------------------------------

_IF_OPEN_RE = re.compile(r"\{\{#if\s+([\w.]+)\}\}")
_IF_CLOSE_RE = re.compile(r"\{\{/if\}\}")
_ELSE_RE = re.compile(r"\{\{else\}\}")


def validate_syntax(content: str) -> list[str]:
    """Pre-flight check for well-formed capability conditional blocks.

    Returns a list of error messages.  An empty list means the syntax
    is valid.  Each error includes approximate line context.
    """
    errors: list[str] = []
    lines = content.splitlines()

    # Track nesting with a stack of (line_number, capability_name)
    stack: list[tuple[int, str]] = []
    else_seen: list[bool] = []  # parallel stack tracking {{else}} per block

    for line_num, line in enumerate(lines, start=1):
        # Process all tokens on this line in order
        pos = 0
        while pos < len(line):
            # Find the next token on this line
            best_match = None
            best_kind = None
            for kind, pattern in (
                ("open", _IF_OPEN_RE),
                ("close", _IF_CLOSE_RE),
                ("else", _ELSE_RE),
            ):
                m = pattern.search(line, pos)
                if m and (best_match is None or m.start() < best_match.start()):
                    best_match = m
                    best_kind = kind

            if best_match is None:
                break

            if best_kind == "open":
                cap_name = best_match.group(1)
                stack.append((line_num, cap_name))
                else_seen.append(False)
            elif best_kind == "else":
                if not stack:
                    errors.append(
                        f"Line {line_num}: {{{{else}}}} without matching {{{{#if}}}}"
                    )
                elif else_seen[-1]:
                    open_line, open_cap = stack[-1]
                    errors.append(
                        "Line %d: duplicate {{else}} in "
                        "{{#if %s}} block (opened at line %d)"
                        % (line_num, open_cap, open_line)
                    )
                else:
                    else_seen[-1] = True
            elif best_kind == "close":
                if not stack:
                    errors.append(
                        f"Line {line_num}: {{{{/if}}}} without matching {{{{#if}}}}"
                    )
                else:
                    stack.pop()
                    else_seen.pop()

            pos = best_match.end()

    # Any remaining open blocks are unmatched
    for line_num, cap_name in stack:
        errors.append(
            f"Line {line_num}: {{{{#if {cap_name}}}}} has no matching {{{{/if}}}}"
        )

    return errors


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def resolve_capabilities(content: str, capabilities: dict[str, Any]) -> str:
    """Resolve all capability syntax in *content*.

    Pipeline order:
    1. Validate syntax (raise ``CapabilitySyntaxError`` on errors)
    2. Resolve conditional blocks (``{{#if}}`` / ``{{else}}`` / ``{{/if}}``)
    3. Resolve tool references (``{{tool:name}}``)

    Returns the fully resolved content string.
    """
    errors = validate_syntax(content)
    if errors:
        raise CapabilitySyntaxError(errors)

    content = resolve_conditionals(content, capabilities)
    content = resolve_tool_references(content, capabilities)
    return content
