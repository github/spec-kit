"""Regression test for duplicate top-level step numbers in specify.md.

Covers #2407: two consecutive items were both labelled ``6.``, which caused
a self-referencing ``proceed to step 7`` inside the section already numbered 7.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SPECIFY_MD = REPO_ROOT / "templates" / "commands" / "specify.md"


def _main_execution_ordinals(text: str) -> list[int]:
    """Return ordinals from the main execution list (items 1-N at column 0).

    The file contains several distinct numbered lists; we only care about the
    primary execution steps that span the first ~250 lines and whose first item
    starts with ``1. **Generate``.
    """
    ordinals: list[int] = []
    in_main_list = False
    for line in text.splitlines():
        m = re.match(r"^(\d+)\. ", line)
        if m:
            n = int(m.group(1))
            if n == 1 and not in_main_list:
                # Start of the main execution list
                in_main_list = True
                ordinals = [n]
            elif in_main_list:
                if n == 1:
                    # A new list restarts — stop here
                    break
                ordinals.append(n)
    return ordinals


def test_no_duplicate_top_level_ordinals():
    """The main numbered list in specify.md must have no duplicate ordinals."""
    text = SPECIFY_MD.read_text(encoding="utf-8")
    ordinals = _main_execution_ordinals(text)
    duplicates = [n for n in ordinals if ordinals.count(n) > 1]
    assert not duplicates, (
        f"Duplicate top-level ordinals found in templates/commands/specify.md: "
        f"{sorted(set(duplicates))}"
    )


def test_main_execution_list_is_sequential():
    """The main execution steps must run 1, 2, 3, … without gaps or duplicates."""
    text = SPECIFY_MD.read_text(encoding="utf-8")
    ordinals = _main_execution_ordinals(text)
    assert ordinals, "Could not find the main execution list in specify.md"
    expected = list(range(1, len(ordinals) + 1))
    assert ordinals == expected, (
        f"Main execution steps are not sequential in templates/commands/specify.md. "
        f"Got: {ordinals}, expected: {expected}"
    )
