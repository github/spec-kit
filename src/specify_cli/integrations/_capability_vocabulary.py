"""Standard capability vocabulary for cross-agent extension portability.

Defines the canonical capability names and their expected structure.
Used for validation warnings when integrations declare capabilities
outside the known vocabulary.  The vocabulary is open (not enforced),
so integrations MAY declare custom capabilities.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CapabilitySpec:
    """Describes a canonical capability in the standard vocabulary.

    Attributes:
        description: Human-readable explanation of the capability.
        expected_sub_properties: Sub-property keys expected for this
            capability (e.g., ``["structured", "multi_select"]``).
    """

    description: str
    expected_sub_properties: list[str] = field(default_factory=list)


#: The standard vocabulary of canonical capability names.
#: Extension authors reference these names in ``{{#if name}}`` and
#: ``{{tool:name}}`` syntax.  Integrations declare values for these
#: keys in their ``capabilities`` class attribute.
STANDARD_CAPABILITIES: dict[str, CapabilitySpec] = {
    "interactive_prompts": CapabilitySpec(
        description="User-facing question/selection tools",
        expected_sub_properties=["structured", "multi_select"],
    ),
    "subagents": CapabilitySpec(
        description="Parallel or background agent dispatch",
        expected_sub_properties=["background", "worktree_isolation"],
    ),
    "process_enforcement": CapabilitySpec(
        description="Workflow state and gate enforcement",
        expected_sub_properties=["hooks", "pre_tool_gate"],
    ),
    "context_clearing": CapabilitySpec(
        description="Conversation or context reset tools",
        expected_sub_properties=[],
    ),
    "script_discovery": CapabilitySpec(
        description="Locating bundled scripts at runtime (resolved via __PLUGIN_ROOT__)",
        expected_sub_properties=[],
    ),
}


def validate_capabilities(
    capabilities: dict[str, Any],
    vocabulary: dict[str, CapabilitySpec] | None = None,
) -> list[str]:
    """Check *capabilities* against the standard vocabulary.

    Returns a list of warning messages for capability keys not present
    in *vocabulary* (defaults to ``STANDARD_CAPABILITIES``).  An empty
    list means all keys are known.

    Unknown keys are **not** errors; the vocabulary is open.
    """
    if vocabulary is None:
        vocabulary = STANDARD_CAPABILITIES

    warnings_list: list[str] = []
    for key in capabilities:
        if key not in vocabulary:
            msg = (
                f"Capability '{key}' is not in the standard vocabulary. "
                f"Known capabilities: {', '.join(sorted(vocabulary))}"
            )
            warnings_list.append(msg)
            logger.warning(msg)
    return warnings_list
