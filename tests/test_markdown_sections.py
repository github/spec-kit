"""Contract cases for bounded Markdown section replacement."""

from __future__ import annotations

import pytest

from specify_cli.markdown_sections import SectionReplacementError, replace_section


@pytest.mark.parametrize(
    "heading,selector",
    [
        ("Review & Approval!", "review--approval"),
        ("API_v2 - Notes", "api_v2---notes"),
        ("**Café** Guide", "café-guide"),
        ("[Review](https://example.test/other) `Guide`", "review-guide"),
        ("__Review__ _Guide_", "review-guide"),
        ("日本語 123", "日本語-123"),
        ("Keep__these_words", "keep__these_words"),
        ("Review ###", "review"),
    ],
)
def test_heading_anchors(heading: str, selector: str) -> None:
    content = f"## {heading}\nold\n## Next\nunchanged"
    assert replace_section(
        content, "new\n", selector,
        preset="team", contribution="body.md", artifact="spec-template",
    ) == f"## {heading}\nnew\n## Next\nunchanged"


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
@pytest.mark.parametrize("replacement", ["", "\nnew\n\n"])
@pytest.mark.parametrize("tail", ["## Next\nkeep", ""])
def test_preserves_everything_outside_body(
    newline: str, replacement: str, tail: str,
) -> None:
    prefix = "---\ndescription: |\n  ## Target\n---\n\n# Doc\n## Target\n"
    body = "old\n### Child\nnested\n"
    content = (prefix + body + tail).replace("\n", newline)
    expected = prefix.replace("\n", newline) + replacement + tail.replace("\n", newline)
    assert replace_section(
        content, replacement, "target",
        preset="team", contribution="body.md", artifact="spec-template",
    ) == expected


@pytest.mark.parametrize(
    "fence,close",
    [("```md", "```"), ("~~~~ text", "~~~~~"), ("   ```", "   ````")],
)
def test_fenced_headings_neither_match_nor_end_section(fence: str, close: str) -> None:
    content = f"# Doc\n{fence}\n## Target\n{close}\n## Target\nold\n{fence}\n# Fake end\n{close}\n## Next\nkeep\n"
    assert replace_section(
        content, "new\n", "target",
        preset="team", contribution="body.md", artifact="spec-template",
    ) == f"# Doc\n{fence}\n## Target\n{close}\n## Target\nnew\n## Next\nkeep\n"


@pytest.mark.parametrize(
    "content,code,count,lines",
    [
        ("# No target\n", "SECTION_NOT_FOUND", 0, []),
        ("```\n## Target\n", "SECTION_NOT_FOUND", 0, []),
        ("~~~\n## Target\n```\n## Target\n", "SECTION_NOT_FOUND", 0, []),
        ("````\n```\n## Target\n", "SECTION_NOT_FOUND", 0, []),
        ("## Target\nold\n### TARGET!\n", "SECTION_AMBIGUOUS", 2, [1, 3]),
        ("    ## Target\nnot ATX\n", "SECTION_NOT_FOUND", 0, []),
        ("##Target\nnot ATX\n", "SECTION_NOT_FOUND", 0, []),
        ("Target\n------\n", "SECTION_NOT_FOUND", 0, []),
    ],
)
def test_selection_diagnostics(
    content: str, code: str, count: int, lines: list[int],
) -> None:
    with pytest.raises(SectionReplacementError) as caught:
        replace_section(
            content, "new\n", "target",
            preset="team", contribution="body.md", artifact="spec-template",
        )
    details = caught.value.details
    assert details["code"] == code
    assert details["match_count"] == count
    assert details["preset"] == "team"
    assert details["contribution"] == "body.md"
    assert details["artifact"] == "spec-template"
    assert details["selector"] == "target"
    assert [candidate["line"] for candidate in details["candidates"]] == lines
    assert details["remediation"]


def test_unclosed_fence_cannot_end_selected_body() -> None:
    assert replace_section(
        "## Target\nold\n```\n# Fake end\n", "", "target",
        preset="team", contribution="body.md", artifact="spec-template",
    ) == "## Target\n"
