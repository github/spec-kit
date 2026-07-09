#!/usr/bin/env python3
"""Refresh the managed Spec Kit section in the coding agent's context file(s).

Python port of ``update-agent-context.sh`` / ``update-agent-context.ps1``.

Reads ``context_files`` or ``context_file``, plus ``context_markers.{start,end}``,
from the agent-context extension config:
    .specify/extensions/agent-context/agent-context-config.yml

Usage: update_agent_context.py [plan_path]

When ``plan_path`` is omitted, the script derives it from
``.specify/feature.json`` (written by /speckit-specify). Falls back to the most
recently modified ``specs/*/plan.md`` only when feature.json is absent or its
plan does not exist yet.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

DEFAULT_START = "<!-- SPECKIT START -->"
DEFAULT_END = "<!-- SPECKIT END -->"


def _err(message: str) -> None:
    print(message, file=sys.stderr)


def _get_str(obj: object, *keys: str) -> str:
    node = obj
    for key in keys:
        if isinstance(node, dict) and key in node:
            node = node[key]
        else:
            return ""
    return node if isinstance(node, str) else ""


def _collect_context_files(data: dict, project_root: str) -> list[str]:
    """Resolve the managed context files from config, mirroring the bash logic."""
    context_files: list[str] = []
    seen: set[str] = set()
    case_insensitive = sys.platform.startswith(("win32", "cygwin", "msys"))

    def add(value: object) -> None:
        if not isinstance(value, str):
            return
        candidate = value.strip()
        if not candidate:
            return
        key = candidate.casefold() if case_insensitive else candidate
        if key in seen:
            return
        context_files.append(candidate)
        seen.add(key)

    raw_files = data.get("context_files")
    if isinstance(raw_files, list):
        for value in raw_files:
            add(value)
    if not context_files:
        add(_get_str(data, "context_file"))
    if not context_files:
        # Self-seed: when the config declares no target, derive one from the
        # active integration recorded in init-options.json, mapped through the
        # bundled agent-context-defaults.json file. Independent of the Specify
        # CLI by design.
        integration_key = ""
        try:
            with open(
                f"{project_root}/.specify/init-options.json", "r", encoding="utf-8"
            ) as fh:
                opts = json.load(fh)
            if isinstance(opts, dict):
                value = opts.get("integration") or opts.get("ai") or ""
                integration_key = value if isinstance(value, str) else ""
        except Exception:
            integration_key = ""
        if integration_key:
            defaults_path = (
                f"{project_root}/.specify/extensions/agent-context/"
                "agent-context-defaults.json"
            )
            mapping = {}
            try:
                with open(defaults_path, "r", encoding="utf-8") as fh:
                    loaded = json.load(fh)
                agents = loaded.get("agents", {}) if isinstance(loaded, dict) else {}
                mapping = agents if isinstance(agents, dict) else {}
            except Exception:
                _err(
                    "agent-context: unable to read %s; cannot self-seed the context "
                    "file. Set context_file in the extension config." % defaults_path
                )
                mapping = {}
            add(mapping.get(integration_key, "") or "")
            if not context_files:
                _err(
                    "agent-context: no default context file is known for integration "
                    "%s. Set context_file in the extension config to choose one."
                    % integration_key
                )
    return context_files


def _validate_context_file(project_root: str, context_file: str) -> str | None:
    """Return an error message when the path escapes the project root."""
    if context_file.startswith("/") or re.match(r"^[A-Za-z]:", context_file):
        return (
            "agent-context: context files must be project-relative paths; "
            f"got '{context_file}'."
        )
    if "\\" in context_file:
        return (
            "agent-context: context files must not contain backslash separators; "
            f"got '{context_file}'."
        )
    if ".." in context_file.split("/"):
        return (
            "agent-context: context files must not contain '..' path segments; "
            f"got '{context_file}'."
        )
    root = Path(project_root).resolve()
    target = (root / context_file).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return (
            "agent-context: context file path resolves outside the project root; "
            f"got '{context_file}'."
        )
    return None


def _resolve_plan_path(project_root: str) -> str:
    """Derive the plan path: feature.json first, then the mtime fallback."""
    plan_path = ""
    feature_json = Path(project_root) / ".specify" / "feature.json"
    if feature_json.is_file():
        feature_dir = ""
        try:
            with open(feature_json, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            value = data.get("feature_directory", "")
            feature_dir = value if isinstance(value, str) else ""
        except Exception:
            feature_dir = ""
        # Normalize backslashes (written by PS on Windows) before path ops.
        feature_dir = feature_dir.replace("\\", "/").rstrip("/")
        if feature_dir:
            # feature_directory may be relative or absolute (absolute paths
            # outside the project root are preserved as-is), including
            # drive-qualified paths (C:/...) written by PowerShell on Windows.
            if feature_dir.startswith("/") or re.match(r"^[A-Za-z]:/", feature_dir):
                candidate = Path(feature_dir) / "plan.md"
            else:
                candidate = Path(project_root) / feature_dir / "plan.md"
            if candidate.is_file():
                # Resolve symlinks before comparing so paths like /var/… vs
                # /private/var/… (macOS) are treated as equivalent.
                root = Path(project_root).resolve()
                resolved = candidate.resolve()
                try:
                    plan_path = resolved.relative_to(root).as_posix()
                except ValueError:
                    plan_path = resolved.as_posix()

    if not plan_path:
        root = Path(project_root).resolve()
        plans = sorted(
            (root / "specs").glob("*/plan.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if plans:
            try:
                plan_path = plans[0].relative_to(root).as_posix()
            except ValueError:
                plan_path = ""
    return plan_path


def _build_section(marker_start: str, marker_end: str, plan_path: str) -> str:
    lines = [
        marker_start,
        "For additional context about technologies to be used, project structure,",
        "shell commands, and other important information, read the current plan",
    ]
    if plan_path:
        lines.append(f"at {plan_path}")
    lines.append(marker_end)
    return "\n".join(lines) + "\n"


def ensure_mdc_frontmatter(content: str) -> str:
    """Ensure ``.mdc`` content has YAML frontmatter with ``alwaysApply: true``.

    Cursor only auto-loads ``.mdc`` rule files that carry frontmatter with
    ``alwaysApply: true``. Prepend it when missing, or repair the value while
    preserving any existing frontmatter comments/formatting.
    """
    leading_ws = len(content) - len(content.lstrip())
    leading = content[:leading_ws]
    stripped = content[leading_ws:]

    if not stripped.startswith("---"):
        return "---\nalwaysApply: true\n---\n\n" + content

    match = re.match(
        r"^(---[ \t]*\r?\n)(.*?)(\r?\n---[ \t]*)(\r?\n|$)(.*)",
        stripped,
        re.DOTALL,
    )
    if not match:
        return "---\nalwaysApply: true\n---\n\n" + content

    opening, fm_text, closing, sep, rest = match.groups()
    newline = "\r\n" if "\r\n" in opening else "\n"

    if re.search(r"(?m)^[ \t]*alwaysApply[ \t]*:[ \t]*true[ \t]*(?:#.*)?$", fm_text):
        return content

    if re.search(r"(?m)^[ \t]*alwaysApply[ \t]*:", fm_text):
        fm_text = re.sub(
            r"(?m)^([ \t]*)alwaysApply[ \t]*:.*?([ \t]*(?:#.*)?)$",
            r"\1alwaysApply: true\2",
            fm_text,
            count=1,
        )
    elif fm_text.strip():
        fm_text = fm_text + newline + "alwaysApply: true"
    else:
        fm_text = "alwaysApply: true"

    return f"{leading}{opening}{fm_text}{closing}{sep}{rest}"


def _upsert_section(
    ctx_path: str, marker_start: str, marker_end: str, section: str
) -> None:
    """Insert or replace the managed section, then normalize and write."""
    if os.path.exists(ctx_path):
        with open(ctx_path, "r", encoding="utf-8-sig") as fh:
            content = fh.read()
        s = content.find(marker_start)
        e = content.find(marker_end, s if s != -1 else 0)
        if s != -1 and e != -1 and e > s:
            end_of_marker = e + len(marker_end)
            if end_of_marker < len(content) and content[end_of_marker] == "\r":
                end_of_marker += 1
            if end_of_marker < len(content) and content[end_of_marker] == "\n":
                end_of_marker += 1
            new_content = content[:s] + section + content[end_of_marker:]
        elif s != -1:
            new_content = content[:s] + section
        elif e != -1:
            end_of_marker = e + len(marker_end)
            if end_of_marker < len(content) and content[end_of_marker] == "\r":
                end_of_marker += 1
            if end_of_marker < len(content) and content[end_of_marker] == "\n":
                end_of_marker += 1
            new_content = section + content[end_of_marker:]
        else:
            if content and not content.endswith("\n"):
                content += "\n"
            new_content = (content + "\n" + section) if content else section
    else:
        new_content = section

    new_content = new_content.replace("\r\n", "\n").replace("\r", "\n")
    if ctx_path.casefold().endswith(".mdc"):
        new_content = ensure_mdc_frontmatter(new_content)
    with open(ctx_path, "wb") as fh:
        fh.write(new_content.encode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    project_root = os.getcwd()
    ext_config = (
        f"{project_root}/.specify/extensions/agent-context/agent-context-config.yml"
    )

    if not os.path.isfile(ext_config):
        _err(f"agent-context: {ext_config} not found; nothing to do.")
        return 0

    try:
        import yaml
    except ImportError:
        _err(
            "agent-context: PyYAML is required to parse extension config but is "
            "not available in the current Python environment.\n"
            "  To resolve: pip install pyyaml (or install it into the environment "
            "used by python3).\n"
            "  Context file will not be updated until PyYAML is importable."
        )
        _err("agent-context: skipping update (see above for details).")
        return 0

    try:
        with open(ext_config, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except Exception as exc:
        _err(
            f"agent-context: unable to parse {ext_config} ({exc}); "
            "cannot update context."
        )
        _err("agent-context: skipping update (see above for details).")
        return 0
    if not isinstance(data, dict):
        data = {}

    context_files = _collect_context_files(data, project_root)
    if not context_files:
        _err(
            "agent-context: context_files/context_file not set in extension config; "
            "nothing to do."
        )
        return 0

    for context_file in context_files:
        error = _validate_context_file(project_root, context_file)
        if error:
            _err(error)
            return 1

    marker_start = _get_str(data, "context_markers", "start") or DEFAULT_START
    marker_end = _get_str(data, "context_markers", "end") or DEFAULT_END

    plan_path = args[0] if args else ""
    if not plan_path:
        plan_path = _resolve_plan_path(project_root)

    section = _build_section(marker_start, marker_end, plan_path)

    for context_file in context_files:
        ctx_path = os.path.join(project_root, context_file)
        os.makedirs(os.path.dirname(ctx_path) or ".", exist_ok=True)
        _upsert_section(ctx_path, marker_start, marker_end, section)
        print(f"agent-context: updated {context_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
