"""Rendering & parsing of injected constitution block in AGENTS.md."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Optional

from .constants import (
    CONSTITUTION_MARKER_BEGIN,
    CONSTITUTION_MARKER_END,
    CONSTITUTION_RELATIVE_PATH,
)


HASH_PREFIX = "hash:"


def compute_constitution_hash(content: str) -> str:
    """Compute stable truncated SHA256 hash of full constitution content."""
    sha = hashlib.sha256(content.encode("utf-8"))
    return sha.hexdigest()[:12]


def render_block(constitution_content: str) -> str:
    """Render full constitution block with markers and hash line.

    The block mirrors spec requirement: entire file as-is within markers.
    """
    h = compute_constitution_hash(constitution_content)
    header_meta = f"{HASH_PREFIX} {h} path: {CONSTITUTION_RELATIVE_PATH}"
    # Ensure trailing newline for clean separation from compiled content
    body = constitution_content.rstrip() + "\n"
    return (
        f"{CONSTITUTION_MARKER_BEGIN}\n"
        f"{header_meta}\n"
        f"{body}"
        f"{CONSTITUTION_MARKER_END}\n"
        "\n"  # blank line after block
    )


@dataclass
class ExistingBlock:
    raw: str
    hash: Optional[str]
    start_index: int
    end_index: int


BLOCK_REGEX = re.compile(
    rf"({re.escape(CONSTITUTION_MARKER_BEGIN)})(.*?)({re.escape(CONSTITUTION_MARKER_END)})",
    re.DOTALL,
)

HASH_LINE_REGEX = re.compile(r"hash:\s*([0-9a-fA-F]{6,64})")


def find_existing_block(content: str) -> Optional[ExistingBlock]:
    """Locate existing constitution block and extract its hash if present."""
    match = BLOCK_REGEX.search(content)
    if not match:
        return None
    block_text = match.group(0)
    hash_match = HASH_LINE_REGEX.search(block_text)
    h = hash_match.group(1) if hash_match else None
    return ExistingBlock(raw=block_text, hash=h, start_index=match.start(), end_index=match.end())


def inject_or_update(existing_agents: str, new_block: str, place_top: bool = True) -> tuple[str, str]:
    """Insert or update constitution block in existing AGENTS.md content.

    Args:
        existing_agents: Current AGENTS.md text (may be empty).
        new_block: Rendered constitution block (already ends with newline).
        place_top: Always True for Phase 0 (prepend at top).
    Returns:
        (updated_text, status) where status in CREATED|UPDATED|UNCHANGED.
    """
    existing_block = find_existing_block(existing_agents)
    if existing_block:
        if existing_block.raw == new_block.rstrip():  # exclude trailing blank block newline
            return existing_agents, "UNCHANGED"
        # Replace existing block span with new block
        updated = existing_agents[: existing_block.start_index] + new_block.rstrip() + existing_agents[existing_block.end_index :]
        # Ensure trailing newline after block + rest
        if not updated.startswith(new_block):
            # If markers were not at top previously and we want top placement, move them
            if place_top:
                body_without_block = updated.replace(new_block.rstrip(), "").lstrip("\n")
                updated = new_block + body_without_block
        return updated, "UPDATED"
    # No existing block
    if place_top:
        return new_block + existing_agents.lstrip("\n"), "CREATED"
    return existing_agents + ("\n" if not existing_agents.endswith("\n") else "") + new_block, "CREATED"
