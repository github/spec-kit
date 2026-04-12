"""Question block transformer for Claude Code integration."""

from __future__ import annotations

import json
import re

_FENCE_RE = re.compile(
    r"<!-- speckit:question-render:begin -->\s*\n(.*?)\n\s*<!-- speckit:question-render:end -->",
    re.DOTALL,
)
_SEPARATOR_RE = re.compile(r"^\|[-| :]+\|$")

# Markers that promote an option to the top of the list.
_RECOMMENDED_RE = re.compile(r"\bRecommended\b\s*[\u2014\-]", re.IGNORECASE)


def _parse_table_rows(block: str) -> list[list[str]]:
    """Return data rows from a Markdown table, skipping header and separator.

    Handles leading indentation (as found in clarify.md / checklist.md).
    Rows with pipe characters inside cell values are not supported by
    standard Markdown tables, so no special handling is needed.
    """
    rows: list[list[str]] = []
    header_seen = False
    separator_seen = False

    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if not header_seen:
            header_seen = True
            continue
        if not separator_seen:
            if _SEPARATOR_RE.match(stripped):
                separator_seen = True
            continue
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if cells:
            rows.append(cells)

    return rows


def parse_clarify(block: str) -> list[dict]:
    """Parse clarify.md schema: | Option | Description |

    - Rows matching ``Recommended —`` / ``Recommended -`` (case-insensitive)
      are placed first.
    - Duplicate labels are deduplicated (first occurrence wins).
    """
    options: list[dict] = []
    recommended: dict | None = None
    seen_labels: set[str] = set()

    for cells in _parse_table_rows(block):
        if len(cells) < 2:
            continue
        label = cells[0]
        description = cells[1]
        if label in seen_labels:
            continue
        seen_labels.add(label)
        entry = {"label": label, "description": description}
        if _RECOMMENDED_RE.search(description):
            if recommended is None:
                recommended = entry
        else:
            options.append(entry)

    if recommended:
        options.insert(0, recommended)

    return options


def parse_checklist(block: str) -> list[dict]:
    """Parse checklist.md schema: | Option | Candidate | Why It Matters |

    Candidate → label, Why It Matters → description.
    Duplicate labels are deduplicated (first occurrence wins).
    """
    options: list[dict] = []
    seen_labels: set[str] = set()

    for cells in _parse_table_rows(block):
        if len(cells) < 3:
            continue
        label = cells[1]
        description = cells[2]
        if label in seen_labels:
            continue
        seen_labels.add(label)
        options.append({"label": label, "description": description})

    return options


def _build_payload(options: list[dict]) -> str:
    """Serialise options into a validated AskUserQuestion JSON code block."""
    # Append "Other" only if not already present.
    if not any(o["label"].lower() == "other" for o in options):
        options = options + [
            {
                "label": "Other",
                "description": "Provide my own short answer (\u226410 words)",
            }
        ]

    payload: dict = {
        "question": "Please select an option:",
        "multiSelect": False,
        "options": options,
    }

    # Validate round-trip before returning — raises ValueError on bad data.
    raw = json.dumps(payload, ensure_ascii=False, indent=2)
    json.loads(raw)  # round-trip check
    return f"```json\n{raw}\n```"


def transform_question_block(content: str) -> str:
    """Replace fenced question blocks with AskUserQuestion JSON payloads.

    Content without markers is returned byte-identical — safe for all
    non-Claude integrations.
    """

    def _replace(match: re.Match) -> str:
        block = match.group(1)
        is_checklist = "| Candidate |" in block or "|Candidate|" in block
        options = parse_checklist(block) if is_checklist else parse_clarify(block)
        return _build_payload(options)

    return _FENCE_RE.sub(_replace, content)
