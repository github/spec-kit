"""Preset Markdown template helpers shared by the CLI and standalone scripts."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
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


def _validate_template_entries(entries: object) -> list[dict[str, str]]:
    if not isinstance(entries, list):
        raise ValueError("manifest templates must be a list")
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("manifest template entries must be mappings")
        if "type" not in entry or "name" not in entry or "file" not in entry:
            raise ValueError("manifest template entry missing type, name, or file")
        for field in ("type", "name", "file"):
            if not isinstance(entry[field], str):
                raise ValueError(f"manifest template {field} must be a string")
        if entry["type"] not in ("template", "command", "script"):
            raise ValueError(f"invalid manifest template type '{entry['type']}'")
        strategy = entry.get("strategy", "replace")
        if not isinstance(strategy, str):
            raise ValueError("manifest template strategy must be a string")
        strategy = strategy.lower()
        if strategy not in ("replace", "prepend", "append", "wrap", "replace-section"):
            raise ValueError(f"invalid manifest template strategy '{strategy}'")
        if entry["type"] == "script" and strategy not in ("replace", "wrap"):
            raise ValueError(f"invalid manifest script strategy '{strategy}'")
        validate_section_selector(strategy, entry.get("selector"), present="selector" in entry)
    return entries


def legacy_preset_template_entries(manifest: object) -> list[dict[str, str]]:
    """Validate template entries from a legacy installed YAML manifest."""
    if not isinstance(manifest, dict):
        raise ValueError("manifest root must be a mapping")
    if "provides" not in manifest:
        raise ValueError("manifest missing provides section")
    provides = manifest["provides"]
    if not isinstance(provides, dict):
        raise ValueError("manifest provides must be a mapping")
    if "templates" not in provides:
        raise ValueError("manifest provides missing templates")
    templates = _validate_template_entries(provides["templates"])
    if not templates:
        raise ValueError("manifest must provide at least one template")
    return templates


def preset_template_projection(
    manifest: Path, metadata: dict[str, object] | None = None,
) -> list[dict[str, str]]:
    """Read the installed template fields and verify their YAML source is current."""
    if sys.version_info < (3, 11):
        raise ValueError("Preset template resolution requires Python 3.11+ on the execution host")
    remedy = "Restore any missing preset files, then run 'specify integration upgrade'."
    if metadata is None:
        registry = manifest.parent.parent / ".registry"
        try:
            metadata = json.loads(registry.read_text(encoding="utf-8"))["presets"][manifest.parent.name]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise ValueError(f"Preset template data is missing. {remedy}") from exc
    if not isinstance(metadata, dict):
        raise ValueError(f"Preset template data is missing. {remedy}")
    entries = metadata.get("template_entries")
    if metadata.get("template_projection_version") != 1 or not isinstance(entries, list):
        raise ValueError(f"Preset template data is missing or unsupported. {remedy}")
    try:
        with manifest.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
    except OSError as exc:
        raise ValueError(f"Preset template manifest is unavailable. {remedy}") from exc
    if metadata.get("manifest_hash") != f"sha256:{digest}":
        raise ValueError(f"Preset template data is stale. {remedy}")
    return _validate_template_entries(entries)


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
    for number, line in enumerate(content.splitlines(keepends=True), 1):
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


def _print_preset_template(manifest: Path, name: str, projected: bool) -> int:
    if not projected:
        try:
            import yaml
        except ImportError:
            print("yaml_missing", file=sys.stderr)
            return 2
    try:
        if projected:
            templates = preset_template_projection(manifest)
        else:
            templates = legacy_preset_template_entries(yaml.safe_load(manifest.read_text(encoding="utf-8")))
        for entry in templates:
            if entry["name"] == name and entry["type"] == "template":
                selector = base64.b64encode(entry.get("selector", "").encode("utf-8")).decode("ascii")
                print("found", entry.get("strategy", "replace"), entry["file"], selector, sep="\t")
                return 0
        print("absent\treplace\t")
    except Exception as exc:
        # PowerShell 5.1 can turn native stderr into a terminating error.
        print(f"manifest_invalid: {exc}", file=sys.stdout if projected else sys.stderr)
        return 3
    return 0


def _main() -> int:
    import argparse

    if sys.argv[1:2] == ["--preset-template"]:
        manifest, name, mode = sys.argv[2:]
        return _print_preset_template(Path(manifest), name, mode == "projection")

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
