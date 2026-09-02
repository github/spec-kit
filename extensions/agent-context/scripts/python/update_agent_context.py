#!/usr/bin/env python3
"""Refresh the managed Spec Kit section in the coding agent's context file(s).

Python port of ``update-agent-context.sh`` / ``update-agent-context.ps1``.

Reads ``context_files`` or ``context_file``, plus ``context_markers.{start,end}``,
from the agent-context extension config:
    .specify/extensions/agent-context/agent-context-config.yml

Usage: update_agent_context.py [plan_path]

When ``plan_path`` is omitted, the script derives it from
``.specify/feature.json`` (written by /speckit-specify). Falls back to the most
recently modified ``plan.md`` found anywhere under ``specs/`` — scoped layouts
nest it as ``specs/<scope>/<feature>/plan.md`` — only when feature.json is
absent or its plan does not exist yet.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

DEFAULT_START = "<!-- SPECKIT START -->"
DEFAULT_END = "<!-- SPECKIT END -->"

# Any SPECKIT marker comment (the outer managed-section markers or the
# per-preset ``PRESET:<id> START/END`` sub-markers). Instruction payloads that
# embed one would collide with the find/replace in _upsert_section, so they are
# rejected.
_SPECKIT_MARKER_RE = re.compile(r"<!--\s*SPECKIT\b")

# Deliberately small budget for always-on instruction payloads. The composed
# managed section is re-sent as agent context on every request, so an oversized
# preset file (a bundled archive member or an unbounded ``--dev`` source) must
# not be allowed to bloat it. A single file over the per-file cap is skipped
# with a warning; once the aggregate cap across all presets is reached, the
# remaining entries are skipped too.
_MAX_INSTRUCTION_FILE_BYTES = 32 * 1024
_MAX_INSTRUCTION_TOTAL_BYTES = 64 * 1024


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
        specs = root / "specs"

        def _resolved_rel(p: Path) -> Path | None:
            # Resolve symlinks before checking containment: relative_to() is
            # lexical and would otherwise accept a plan reached through a specs/
            # symlink that points outside the project, emitting an
            # in-project-looking path for an out-of-project file (or picking it
            # as "most recent").
            try:
                return p.resolve().relative_to(root)
            except (OSError, ValueError):
                return None

        # Recurse (rather than the old one-level specs/*/plan.md glob) so scoped
        # layouts created via SPECIFY_FEATURE_DIRECTORY, e.g.
        # specs/<scope>/<feature>/plan.md, are still discovered when
        # feature.json is absent (#3024). Mirrors the bash and PowerShell twins.
        candidates = []
        for p in specs.rglob("plan.md"):
            rel = _resolved_rel(p)
            if rel is not None:
                candidates.append((p, rel))
        candidates.sort(key=lambda pr: pr[0].stat().st_mtime, reverse=True)
        if candidates:
            plan_path = candidates[0][1].as_posix()
    return plan_path


def _build_section(
    marker_start: str,
    marker_end: str,
    plan_path: str,
    preset_blocks: list[str] | None = None,
) -> str:
    lines = [
        marker_start,
        "For additional context about technologies to be used, project structure,",
        "shell commands, and other important information, read the current plan",
    ]
    if plan_path:
        lines.append(f"at {plan_path}")
    # Always-on instruction blocks contributed by explicitly-enabled presets,
    # each in its own namespaced sub-block so multiple presets coexist and each
    # can be regenerated or dropped independently on the next update.
    lines.extend(preset_blocks or [])
    lines.append(marker_end)
    return "\n".join(lines) + "\n"


def _collect_preset_instruction_blocks(
    project_root: str,
    marker_start: str = DEFAULT_START,
    marker_end: str = DEFAULT_END,
) -> list[tuple[str, str]]:
    """Collect always-on instruction blocks from installed + enabled presets.

    A preset the user explicitly added (``specify preset add``) that declares
    ``provides.instructions`` gets its rule block composed into the managed
    section. Reads ``.specify/presets/.registry`` and each preset's
    ``preset.yml`` directly, with no dependency on the Specify CLI (mirrors this
    extension's by-design independence). Returns ``(preset_id, content)`` in
    deterministic id order. Each referenced file must resolve inside its own
    preset directory; path-unsafe, unreadable, non-UTF-8, oversized (per-file or
    aggregate budget), or marker-colliding entries are skipped (fail closed).
    Fails closed on an unreadable registry.
    """
    presets_dir = Path(project_root) / ".specify" / "presets"
    registry = presets_dir / ".registry"
    if not registry.is_file():
        return []
    try:
        import yaml
    except ImportError:
        return []
    try:
        with open(registry, "r", encoding="utf-8") as fh:
            reg = json.load(fh)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return []
    if not isinstance(reg, dict) or not isinstance(reg.get("presets"), dict):
        return []

    presets_root = presets_dir.resolve()
    blocks: list[tuple[str, str]] = []
    total_bytes = 0
    for preset_id in sorted(reg["presets"]):
        # The registry lives on disk and is untrusted. Reject ids that are not
        # simple names (no path separators, '..' traversal, or absolute/drive
        # forms), then confirm the resolved directory stays inside
        # .specify/presets, so a crafted key or a symlink cannot read a manifest
        # or payload outside it.
        if not isinstance(preset_id, str) or not re.match(r"^[a-z0-9][a-z0-9._-]*$", preset_id):
            continue
        preset_root = (presets_dir / preset_id).resolve()
        try:
            preset_root.relative_to(presets_root)
        except ValueError:
            continue
        meta = reg["presets"][preset_id]
        if not isinstance(meta, dict) or not meta.get("enabled", True):
            continue
        manifest = preset_root / "preset.yml"
        if not manifest.is_file():
            continue
        try:
            with open(manifest, "r", encoding="utf-8") as fh:
                pdata = yaml.safe_load(fh)
        except Exception:
            continue
        provides = pdata.get("provides") if isinstance(pdata, dict) else None
        instructions = provides.get("instructions") if isinstance(provides, dict) else None
        if not isinstance(instructions, list):
            continue
        parts: list[str] = []
        for entry in instructions:
            if not isinstance(entry, dict):
                continue
            rel = entry.get("file")
            if not isinstance(rel, str) or not rel.strip():
                continue
            if rel.startswith("/") or "\\" in rel or ".." in rel.split("/"):
                continue
            target = (preset_root / rel).resolve()
            try:
                target.relative_to(preset_root)
            except ValueError:
                continue
            if not target.is_file():
                continue
            # Reject an oversized file by its on-disk size before reading it, so
            # a huge member never gets allocated into memory.
            try:
                size = target.stat().st_size
            except OSError:
                continue
            if size > _MAX_INSTRUCTION_FILE_BYTES:
                _err(
                    f"agent-context: skipping instructions from preset '{preset_id}': "
                    f"file '{rel}' is {size} bytes (per-file limit "
                    f"{_MAX_INSTRUCTION_FILE_BYTES})."
                )
                continue
            try:
                text = target.read_text(encoding="utf-8").strip()
            except (OSError, UnicodeDecodeError):
                continue
            entry_bytes = len(text.encode("utf-8"))
            if total_bytes + entry_bytes > _MAX_INSTRUCTION_TOTAL_BYTES:
                _err(
                    f"agent-context: skipping instructions from preset '{preset_id}': "
                    f"aggregate instruction budget ({_MAX_INSTRUCTION_TOTAL_BYTES} "
                    "bytes) exceeded."
                )
                continue
            if marker_start in text or marker_end in text or _SPECKIT_MARKER_RE.search(text):
                _err(
                    f"agent-context: skipping instructions from preset '{preset_id}': "
                    "content contains a managed section marker."
                )
                continue
            total_bytes += entry_bytes
            parts.append(text)
        if parts:
            blocks.append((preset_id, "\n\n".join(parts)))
    return blocks


def _render_preset_block_lines(
    project_root: str,
    marker_start: str = DEFAULT_START,
    marker_end: str = DEFAULT_END,
) -> list[str]:
    """Render the namespaced sub-block lines for all enabled presets' instruction
    blocks, to be embedded inside the managed section.
    """
    lines: list[str] = []
    for preset_id, content in _collect_preset_instruction_blocks(
        project_root, marker_start, marker_end
    ):
        lines.append("")
        lines.append(f"<!-- SPECKIT PRESET:{preset_id} START -->")
        lines.append(content)
        lines.append(f"<!-- SPECKIT PRESET:{preset_id} END -->")
    return lines


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

    # --emit-preset-blocks: print only the composed preset instruction sub-block
    # lines and exit. Used by the bash/PowerShell twins so all three produce
    # identical output from this single implementation. Does not require the
    # agent-context config (the twin already validated it before calling).
    if "--emit-preset-blocks" in args:
        def _opt(name: str, default: str) -> str:
            if name in args:
                i = args.index(name)
                if i + 1 < len(args):
                    return args[i + 1]
            return default
        marker_start = _opt("--marker-start", DEFAULT_START)
        marker_end = _opt("--marker-end", DEFAULT_END)
        block_lines = _render_preset_block_lines(project_root, marker_start, marker_end)
        if block_lines:
            sys.stdout.buffer.write("\n".join(block_lines).encode("utf-8"))
        return 0

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

    preset_blocks = _render_preset_block_lines(project_root, marker_start, marker_end)
    section = _build_section(marker_start, marker_end, plan_path, preset_blocks)

    for context_file in context_files:
        ctx_path = os.path.join(project_root, context_file)
        os.makedirs(os.path.dirname(ctx_path) or ".", exist_ok=True)
        _upsert_section(ctx_path, marker_start, marker_end, section)
        print(f"agent-context: updated {context_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
