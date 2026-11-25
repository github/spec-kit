"""Bounded Markdown section replacement, also shipped with standalone helpers."""

from __future__ import annotations

import base64
import json
import re
import unicodedata
from pathlib import Path
from typing import TypedDict


class SectionCandidate(TypedDict):
    heading: str
    line: int


class SectionDiagnostic(TypedDict):
    code: str
    preset: str
    contribution: str
    artifact: str
    selector: str
    match_count: int
    candidates: list[SectionCandidate]
    remediation: str


class SectionReplacementError(ValueError):
    """A section selector did not identify exactly one eligible heading."""

    def __init__(self, details: SectionDiagnostic):
        self.details = details
        super().__init__(json.dumps(details, ensure_ascii=True))


def validate_section_selector(strategy: str, selector: object, *, present: bool) -> None:
    """Validate opt-in selector metadata without silently changing strategies."""
    if strategy != "replace-section":
        if present:
            raise ValueError("selector is only valid with strategy 'replace-section'")
        return
    if (
        not isinstance(selector, str)
        or not selector
        or selector != selector.lower()
        or any(
            char not in "-_" and unicodedata.category(char)[0] not in "LN"
            for char in selector
        )
    ):
        raise ValueError(
            "replace-section selector must be a non-empty lowercase anchor "
            "(letters, numbers, hyphens, underscores; no leading #)"
        )


_CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(.*?)(?<!`)\1(?!`)")
_INLINE_LINK = re.compile(r"\[([^\]]*)\]\(")


def _link_labels(text: str) -> str:
    parts: list[str] = []
    cursor = 0
    while cursor < len(text):
        code = _CODE_SPAN.match(text, cursor)
        if code:
            parts.append(code[0])
            cursor = code.end()
            continue
        link = _INLINE_LINK.match(text, cursor)
        if link:
            depth = 1
            end = link.end()
            while end < len(text) and depth:
                if text[end] == "\\":
                    end += 2
                    continue
                if text[end] == "(":
                    depth += 1
                elif text[end] == ")":
                    depth -= 1
                end += 1
            if depth == 0:
                parts.append(link[1])
                cursor = end
                continue
        parts.append(text[cursor])
        cursor += 1
    return "".join(parts)


def _anchor(text: str) -> str:
    text = _link_labels(text)
    # Stripping markup cannot create a token with more NULs than the input contains.
    prefix = "\0" * (text.count("\0") + 1)
    code_contents: list[str] = []

    def protect_code(match: re.Match[str]) -> str:
        code_contents.append(match[2])
        return f"{prefix}{len(code_contents) - 1}Z"

    text = _CODE_SPAN.sub(protect_code, text)
    text = re.sub(r"(\*{1,2}|~~)(.*?)\1", r"\2", text)
    while True:
        normalized = re.sub(r"(?<!\w)(_+)(?!_)(.*?)(?<!_)\1(?!\w)", r"\2", text)
        if normalized == text:
            break
        text = normalized
    text = re.sub(
        re.escape(prefix) + r"(\d+)Z",
        lambda match: code_contents[int(match[1])],
        text,
    )
    return "".join(
        "-" if char == " " else char
        for char in text.lower()
        if char in " -_" or unicodedata.category(char)[0] in "LN"
    )


def replace_section(
    content: str,
    replacement: str,
    selector: str,
    *,
    preset: str,
    contribution: str,
    artifact: str,
) -> str:
    """Replace one ATX section body without rewriting any surrounding text."""
    validate_section_selector("replace-section", selector, present=True)
    headings: list[tuple[int, str, int, int, int]] = []
    fence_marker = ""
    fence_length = 0
    metadata = content.startswith(("---\n", "---\r\n"))
    offset = 0
    for number, line in enumerate(
        re.findall(r"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+", content), 1
    ):
        start = offset
        offset += len(line)
        text = line.rstrip("\r\n")
        if metadata:
            if number > 1 and text == "---":
                metadata = False
            continue
        if fence_marker:
            closing = re.fullmatch(r" {0,3}(`+|~+)[ \t]*", text)
            if closing and closing[1][0] == fence_marker and len(closing[1]) >= fence_length:
                fence_marker = ""
            continue
        opening = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", text)
        if opening and not (opening[1][0] == "`" and "`" in opening[2]):
            fence_marker, fence_length = opening[1][0], len(opening[1])
            continue
        heading = re.fullmatch(r" {0,3}(#{1,6})(?:[ \t]+(.*?)|)[ \t]*", text)
        if heading:
            title = re.sub(r"[ \t]+#+[ \t]*$", "", heading[2] or "").strip(" \t")
            headings.append((len(heading[1]), title, number, start, offset))

    matches = [index for index, heading in enumerate(headings) if _anchor(heading[1]) == selector]
    if len(matches) != 1:
        raise SectionReplacementError({
            "code": "SECTION_NOT_FOUND" if not matches else "SECTION_AMBIGUOUS",
            "preset": preset,
            "contribution": contribution,
            "artifact": artifact,
            "selector": selector,
            "match_count": len(matches),
            "candidates": [
                {"heading": headings[index][1], "line": headings[index][2]}
                for index in matches
            ],
            "remediation": (
                "Check the selector and current target headings."
                if not matches else "Make the target heading anchors unique."
            ),
        })

    index = matches[0]
    level, _, _, _, body_start = headings[index]
    body_end = next(
        (heading[3] for heading in headings[index + 1:] if heading[0] <= level),
        len(content),
    )
    if (
        replacement
        and body_start == len(content)
        and not content.endswith(("\n", "\r"))
        and not replacement.startswith(("\n", "\r"))
    ):
        last_newline = content.rfind("\n")
        separator = "\r\n" if last_newline > 0 and content[last_newline - 1] == "\r" else "\n"
        replacement = separator + replacement
    return content[:body_start] + replacement + content[body_end:]


def _main() -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selector")
    parser.add_argument("replacement", type=Path)
    parser.add_argument("--preset", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--selector-base64", action="store_true")
    args = parser.parse_args()
    try:
        content = args.input.read_bytes() if args.input else sys.stdin.buffer.read()
        result = replace_section(
            content.decode("utf-8"), args.replacement.read_bytes().decode("utf-8"),
            base64.b64decode(args.selector, validate=True).decode("utf-8")
            if args.selector_base64 else args.selector,
            preset=args.preset, contribution=str(args.replacement),
            artifact=args.artifact,
        ).encode("utf-8")
        if args.output:
            args.output.write_bytes(result)
        else:
            sys.stdout.buffer.write(result)
    except (OSError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
