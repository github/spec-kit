"""High-level constitution injection workflow used by compile command."""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Literal

from .constitution import read_constitution
from .constitution_block import render_block, find_existing_block
from .constants import CONSTITUTION_MARKER_BEGIN, CONSTITUTION_MARKER_END

InjectionStatus = Literal["CREATED", "UPDATED", "UNCHANGED", "SKIPPED", "MISSING"]


class ConstitutionInjector:
    """Encapsulates constitution detection + injection logic."""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

    def inject(self, compiled_content: str, with_constitution: bool, output_path: Path) -> tuple[str, InjectionStatus, Optional[str]]:
        """Return final AGENTS.md content after optional injection.

        Args:
            compiled_content: Newly compiled content (without constitution block).
            with_constitution: Whether to perform injection (True) or preserve existing block (False).
            output_path: Existing AGENTS.md path (may not exist) for preservation logic.
        Returns:
            (final_content, status, hash_or_none)
        """
        existing_content = ""
        if output_path.exists():
            try:
                existing_content = output_path.read_text(encoding="utf-8")
            except OSError:
                existing_content = ""

        # Helper to split header/body from freshly compiled content.
        def _split_header(content: str) -> tuple[str, str]:
            # Header ends at the first double newline (blank line separating header from body)
            marker = "\n\n"
            if marker in content:
                idx = content.index(marker)
                return content[: idx + len(marker)], content[idx + len(marker) :]
            # Fallback: treat whole content as header
            return content, ""

        header_part, body_part = _split_header(compiled_content)

        if not with_constitution:
            # If skipping, we preserve existing block if present but enforce ordering: header first, block (if any), then body.
            existing_block = find_existing_block(existing_content)
            if existing_block:
                final = header_part + existing_block.raw.rstrip() + "\n\n" + body_part.lstrip("\n")
                return final, "SKIPPED", None
            return compiled_content, "SKIPPED", None

        constitution_text = read_constitution(self.base_dir)
        if constitution_text is None:
            existing_block = find_existing_block(existing_content)
            if existing_block:
                final = header_part + existing_block.raw.rstrip() + "\n\n" + body_part.lstrip("\n")
                return final, "MISSING", None
            return compiled_content, "MISSING", None

        new_block = render_block(constitution_text)
        existing_block = find_existing_block(existing_content)

        if existing_block:
            # Compare raw block bodies (strip trailing newlines for stable compare)
            if existing_block.raw.rstrip() == new_block.rstrip():
                status = "UNCHANGED"
                block_to_use = existing_block.raw.rstrip()
            else:
                status = "UPDATED"
                block_to_use = new_block.rstrip()
        else:
            status = "CREATED"
            block_to_use = new_block.rstrip()

        hash_line = new_block.splitlines()[1] if len(new_block.splitlines()) > 1 else ""
        hash_value = None
        if hash_line.startswith("hash:"):
            parts = hash_line.split()
            if len(parts) >= 2:
                hash_value = parts[1]

        final_content = header_part + block_to_use + "\n\n" + body_part.lstrip("\n")
        # Ensure single trailing newline
        if not final_content.endswith("\n"):
            final_content += "\n"
        return final_content, status, hash_value
