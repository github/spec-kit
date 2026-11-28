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
        ("[API](https://example.test/a_(b)/guide)", "api"),
        ("[API](https://example.test/a_(b_(c))/guide) Next", "api-next"),
        (r"[API](https://example.test/a_\)/guide) Next", "api-next"),
        ("`__init__`", "__init__"),
        ("``__init__``", "__init__"),
        ("__Review `__init__`__", "review-__init__"),
        ("[`__init__`](https://example.test/a_(b)/guide)", "__init__"),
        ("`[API](url)`", "apiurl"),
        ("_Guide_`__init__`", "guide__init__"),
        ("__Review__ _Guide_", "review-guide"),
        ("___Target___", "target"),
        ("____Target____", "target"),
        ("__Outer _Target_ end__", "outer-target-end"),
        ("Keep___Target___words", "keep___target___words"),
        ("`___Target___`", "___target___"),
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


@pytest.mark.parametrize("closing", ["---", "--- ", "---\t"])
def test_front_matter_end_with_trailing_whitespace(closing: str) -> None:
    front = "---\ndescription: |\n  ## Target\n" + closing + "\n"
    body = "\n# Doc\n## Target\nold\n## Next\nkeep\n"
    assert replace_section(
        front + body, "new\n", "target",
        preset="team", contribution="body.md", artifact="spec-template",
    ) == front + "\n# Doc\n## Target\nnew\n## Next\nkeep\n"


@pytest.mark.parametrize("closing", ["---- ", "--- text"])
def test_front_matter_end_rejects_non_delimiter_lines(closing: str) -> None:
    front = "---\ndescription: |\n  ## Target\n" + closing + "\n"
    body = "\n# Doc\n## Target\nold\n## Next\nkeep\n"
    with pytest.raises(SectionReplacementError) as caught:
        replace_section(
            front + body, "new\n", "target",
            preset="team", contribution="body.md", artifact="spec-template",
        )
    details = caught.value.details
    assert details["code"] == "SECTION_NOT_FOUND"
    assert details["match_count"] == 0
    assert details["candidates"] == []


@pytest.mark.parametrize(
    "content,replacement,expected",
    [
        ("## Target", "new body\n", "## Target\nnew body\n"),
        ("# Doc\r\n## Target", "new body\r\n", "# Doc\r\n## Target\r\nnew body\r\n"),
        ("## Target", "\nnew body\n", "## Target\nnew body\n"),
        ("## Target", "\r\nnew body\r\n", "## Target\r\nnew body\r\n"),
        ("## Target", "", "## Target"),
    ],
)
def test_unterminated_heading_keeps_body_on_a_separate_line(content, replacement, expected):
    assert replace_section(
        content, replacement, "target",
        preset="team", contribution="body.md", artifact="spec-template",
    ) == expected


def test_unterminated_heading_remains_selectable_for_later_replacements():
    first = replace_section(
        "## Target", "first\n", "target",
        preset="first", contribution="first.md", artifact="spec-template",
    )
    assert replace_section(
        first, "second\n", "target",
        preset="second", contribution="second.md", artifact="spec-template",
    ) == "## Target\nsecond\n"


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
        ("## Target\nold\n## ___Target___\n", "SECTION_AMBIGUOUS", 2, [1, 3]),
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


# Characters str.splitlines() treats as line breaks that Markdown does not.
NON_MARKDOWN_LINE_SEPARATORS = ["\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"]


@pytest.mark.parametrize("separator", NON_MARKDOWN_LINE_SEPARATORS)
def test_non_markdown_line_separators_do_not_end_selected_body(separator: str) -> None:
    content = f"## Notes\nSee page{separator}## Fake\nmore\n## Next\nkeep\n"
    assert replace_section(
        content, "new\n", "notes",
        preset="team", contribution="body.md", artifact="spec-template",
    ) == "## Notes\nnew\n## Next\nkeep\n"


@pytest.mark.parametrize("separator", NON_MARKDOWN_LINE_SEPARATORS)
def test_non_markdown_line_separators_do_not_open_fences(separator: str) -> None:
    content = f"# Notes\ntext{separator}```\n## Target\nold\n## Next\nkeep\n"
    assert replace_section(
        content, "new\n", "target",
        preset="team", contribution="body.md", artifact="spec-template",
    ) == f"# Notes\ntext{separator}```\n## Target\nnew\n## Next\nkeep\n"


@pytest.mark.parametrize("separator", NON_MARKDOWN_LINE_SEPARATORS)
def test_non_markdown_line_separators_do_not_create_headings(separator: str) -> None:
    content = f"## Notes\nSee page{separator}## Fake\nmore\n## Next\nkeep\n"
    with pytest.raises(SectionReplacementError, match="SECTION_NOT_FOUND"):
        replace_section(
            content, "new\n", "fake",
            preset="team", contribution="body.md", artifact="spec-template",
        )


def test_non_markdown_line_separator_does_not_shift_diagnostic_lines() -> None:
    content = "intro\u2028still intro\n## Target\nold\n## Target\nagain\n"
    with pytest.raises(SectionReplacementError) as caught:
        replace_section(
            content, "new\n", "target",
            preset="team", contribution="body.md", artifact="spec-template",
        )
    assert caught.value.details["code"] == "SECTION_AMBIGUOUS"
    assert [candidate["line"] for candidate in caught.value.details["candidates"]] == [2, 4]


@pytest.mark.parametrize("newline", ["\r", "\r\n"])
def test_carriage_return_line_endings_remain_supported(newline: str) -> None:
    content = f"## Notes{newline}old{newline}## Next{newline}keep"
    assert replace_section(
        content, f"new{newline}", "notes",
        preset="team", contribution="body.md", artifact="spec-template",
    ) == f"## Notes{newline}new{newline}## Next{newline}keep"


def test_code_underscores_do_not_match_emphasis_anchor() -> None:
    with pytest.raises(SectionReplacementError, match="SECTION_NOT_FOUND"):
        replace_section(
            "## `__init__`\nold\n", "new\n", "init",
            preset="team", contribution="body.md", artifact="spec-template",
        )


def test_unclosed_link_destination_does_not_match_label_only() -> None:
    with pytest.raises(SectionReplacementError, match="SECTION_NOT_FOUND"):
        replace_section(
            "## [API](https://example.test/a_(b)\nold\n", "new\n", "api",
            preset="team", contribution="body.md", artifact="spec-template",
        )
