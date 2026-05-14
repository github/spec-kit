"""Claude-specific skill post-processing helpers."""

from __future__ import annotations

import re
from pathlib import Path

# Note injected into hook sections so Claude maps dot-notation command
# names (from extensions.yml) to the hyphenated skill names it uses.
_HOOK_COMMAND_NOTE = (
    "- When constructing slash commands from hook command names, "
    "replace dots (`.`) with hyphens (`-`). "
    "For example, `speckit.git.commit` -> `/speckit-git-commit`.\n"
)

# Mapping of command template stem -> argument-hint text shown inline
# when a user invokes the slash command in Claude Code.
ARGUMENT_HINTS: dict[str, str] = {
    "specify": "Describe the feature you want to specify",
    "plan": "Optional guidance for the planning phase",
    "tasks": "Optional task generation constraints",
    "implement": "Optional implementation guidance or task filter",
    "analyze": "Optional focus areas for analysis",
    "clarify": "Optional areas to clarify in the spec",
    "constitution": "Principles or values for the project constitution",
    "checklist": "Domain or focus area for the checklist",
    "taskstoissues": "Optional filter or label for GitHub issues",
}


def inject_hook_command_note(content: str) -> str:
    """Insert a dot-to-hyphen note before each hook output instruction."""
    if "replace dots" in content:
        return content

    def repl(m: re.Match[str]) -> str:
        indent = m.group(1)
        instruction = m.group(2)
        eol = m.group(3)
        return (
            indent
            + _HOOK_COMMAND_NOTE.rstrip("\n")
            + eol
            + indent
            + instruction
            + eol
        )

    return re.sub(
        r"(?m)^(\s*)(- For each executable hook, output the following[^\r\n]*)(\r\n|\n|$)",
        repl,
        content,
    )


def inject_argument_hint(content: str, hint: str) -> str:
    """Insert ``argument-hint`` after the first ``description:`` in YAML frontmatter."""
    lines = content.splitlines(keepends=True)

    dash_count = 0
    for line in lines:
        stripped = line.rstrip("\n\r")
        if stripped == "---":
            dash_count += 1
            if dash_count == 2:
                break
            continue
        if dash_count == 1 and stripped.startswith("argument-hint:"):
            return content

    out: list[str] = []
    in_fm = False
    dash_count = 0
    injected = False
    for line in lines:
        stripped = line.rstrip("\n\r")
        if stripped == "---":
            dash_count += 1
            in_fm = dash_count == 1
            out.append(line)
            continue
        if in_fm and not injected and stripped.startswith("description:"):
            out.append(line)
            if line.endswith("\r\n"):
                eol = "\r\n"
            elif line.endswith("\n"):
                eol = "\n"
            else:
                eol = ""
            escaped = hint.replace("\\", "\\\\").replace('"', '\\"')
            out.append(f'argument-hint: "{escaped}"{eol}')
            injected = True
            continue
        out.append(line)
    return "".join(out)


def inject_frontmatter_flag(content: str, key: str, value: str = "true") -> str:
    """Insert ``key: value`` before the closing ``---`` if not already present."""
    lines = content.splitlines(keepends=True)

    dash_count = 0
    for line in lines:
        stripped = line.rstrip("\n\r")
        if stripped == "---":
            dash_count += 1
            if dash_count == 2:
                break
            continue
        if dash_count == 1 and stripped.startswith(f"{key}:"):
            return content

    out: list[str] = []
    dash_count = 0
    injected = False
    for line in lines:
        stripped = line.rstrip("\n\r")
        if stripped == "---":
            dash_count += 1
            if dash_count == 2 and not injected:
                if line.endswith("\r\n"):
                    eol = "\r\n"
                elif line.endswith("\n"):
                    eol = "\n"
                else:
                    eol = ""
                out.append(f"{key}: {value}{eol}")
                injected = True
        out.append(line)
    return "".join(out)


def set_frontmatter_key(content: str, key: str, value: str) -> str:
    """Ensure ``key: value`` in the first frontmatter block; replace if key exists."""
    lines = content.splitlines(keepends=True)
    dash_count = 0
    for i, line in enumerate(lines):
        stripped = line.rstrip("\n\r")
        if stripped == "---":
            dash_count += 1
            if dash_count == 2:
                break
            continue
        if dash_count == 1 and stripped.startswith(f"{key}:"):
            if line.endswith("\r\n"):
                eol = "\r\n"
            elif line.endswith("\n"):
                eol = "\n"
            else:
                eol = ""
            lines[i] = f"{key}: {value}{eol}"
            return "".join(lines)
    return inject_frontmatter_flag(content, key, value)


def apply_claude_skill_postprocess(content: str, skill_path: Path) -> str:
    """Apply Claude-specific transforms in sequence for generated SKILL.md."""
    from .question_transformer import transform_question_block

    updated = transform_question_block(content)
    updated = inject_frontmatter_flag(updated, "user-invocable")
    updated = set_frontmatter_key(updated, "disable-model-invocation", "false")
    updated = inject_hook_command_note(updated)

    skill_dir_name = skill_path.parent.name
    stem = skill_dir_name[len("speckit-") :] if skill_dir_name.startswith("speckit-") else skill_dir_name
    hint = ARGUMENT_HINTS.get(stem, "")
    if hint:
        updated = inject_argument_hint(updated, hint)
    return updated
