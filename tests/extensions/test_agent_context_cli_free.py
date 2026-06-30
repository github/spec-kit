"""Static guard: the Specify CLI source must contain no agent-context lifecycle code.

The ``agent-context`` extension is a full opt-in and owns its own lifecycle. The
Python codebase (``src/specify_cli/**``) must therefore not reference any of the
removed context-section management helpers, the extension config helpers, the
context markers, or the obsolete deprecation message.

Maps to contract C5 / FR-002 / FR-003 / FR-006 / SC-002 / SC-003.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src" / "specify_cli"

FORBIDDEN_SYMBOLS = [
    "upsert_context_section",
    "remove_context_section",
    "_agent_context_extension_enabled",
    "_resolve_context_markers",
    "_resolve_context_files",
    "_resolve_context_file_values",
    "_build_context_section",
    "_AGENT_CTX_EXT_CONFIG",
    "_load_agent_context_config",
    "_save_agent_context_config",
    "_update_agent_context_config_file",
    "CONTEXT_MARKER_START",
    "CONTEXT_MARKER_END",
    "agent-context-config",
    "agent_context_config",
    "__CONTEXT_FILE__",
    "_context_file_display",
    "Inline agent-context updates",
    "v0.12.0",
]


@pytest.fixture(scope="module")
def cli_source_texts() -> list[tuple[str, str]]:
    """Read every CLI source file once, shared across all parametrized cases."""
    return [
        (str(path.relative_to(PROJECT_ROOT)), path.read_text(encoding="utf-8"))
        for path in SRC_ROOT.rglob("*.py")
    ]


@pytest.mark.parametrize("symbol", FORBIDDEN_SYMBOLS)
def test_symbol_absent_from_cli_source(symbol, cli_source_texts):
    offenders = [rel for rel, text in cli_source_texts if symbol in text]
    assert not offenders, (
        f"Forbidden agent-context symbol {symbol!r} still present in: {offenders}"
    )
