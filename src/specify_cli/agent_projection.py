"""Agent governance memory and projection helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .integration_state import (
    INTEGRATION_JSON,
    default_integration_key,
    installed_integration_keys,
    normalize_integration_state,
)


AGENT_GOVERNANCE_MEMORY = ".specify/memory/agent-governance.md"
AGENT_GOVERNANCE_TEMPLATE = ".specify/templates/agent-governance-template.md"

PROJECTION_MARKER_START = "<!-- SPECKIT AGENT PROJECTION START -->"
PROJECTION_MARKER_END = "<!-- SPECKIT AGENT PROJECTION END -->"


@dataclass(frozen=True)
class AgentProjectionResult:
    """Files updated by an agent projection refresh."""

    memory_path: Path | None
    projection_paths: list[Path]


def ensure_agent_governance_from_template(project_root: Path) -> Path | None:
    """Copy agent-governance template to memory if missing."""
    memory_path = project_root / AGENT_GOVERNANCE_MEMORY
    if memory_path.exists():
        return memory_path

    template_path = project_root / AGENT_GOVERNANCE_TEMPLATE
    if not template_path.exists():
        return None

    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_bytes(template_path.read_bytes())
    return memory_path


def refresh_agent_projection(project_root: Path) -> AgentProjectionResult:
    """Refresh repo-level and agent-specific governance projections.

    The source of truth is ``.specify/memory/agent-governance.md`` plus the
    repository's current integration, skill, MCP, and extension state. Existing
    text outside the generated projection markers is preserved.
    """
    memory_path = ensure_agent_governance_from_template(project_root)
    if memory_path is None:
        return AgentProjectionResult(None, [])

    state = _read_integration_state(project_root)
    installed = installed_integration_keys(state)
    default_key = default_integration_key(state)
    projection_paths = _projection_targets(project_root, state)
    projection = _render_projection(project_root, memory_path, state)
    updated: list[Path] = []

    for path in projection_paths:
        content = _adapter_prelude(path, default_key, installed)
        if path.exists():
            existing = path.read_text(encoding="utf-8-sig")
            new_content = _upsert_marked_section(existing, projection)
            if new_content == existing:
                continue
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            new_content = content + "\n" + projection

        path.write_text(_normalize_newlines(new_content), encoding="utf-8")
        updated.append(path)

    return AgentProjectionResult(memory_path, updated)


def _read_integration_state(project_root: Path) -> dict[str, Any]:
    path = project_root / INTEGRATION_JSON
    if not path.exists():
        return normalize_integration_state({})
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return normalize_integration_state({})
    return normalize_integration_state(data if isinstance(data, dict) else {})


def _projection_targets(project_root: Path, state: dict[str, Any]) -> list[Path]:
    targets: list[Path] = [project_root / "AGENTS.md"]

    try:
        from .integrations import get_integration
    except Exception:
        get_integration = None  # type: ignore[assignment]

    for key in installed_integration_keys(state):
        integration = get_integration(key) if get_integration else None
        context_file = getattr(integration, "context_file", None)
        if isinstance(context_file, str) and context_file.strip():
            targets.append(project_root / context_file)

    # Common adapter files. They are created when the corresponding
    # integration is installed, and refreshed whenever they already exist so
    # uninstall/switch operations do not leave stale generated projections.
    for key, path in {
        "claude": "CLAUDE.md",
        "gemini": "GEMINI.md",
        "copilot": ".github/copilot-instructions.md",
    }.items():
        target = project_root / path
        if key in installed_integration_keys(state) or target.exists():
            targets.append(target)

    deduped: list[Path] = []
    seen: set[str] = set()
    for path in targets:
        rel = path.resolve().as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        deduped.append(path)
    return deduped


def _render_projection(
    project_root: Path,
    memory_path: Path,
    state: dict[str, Any],
) -> str:
    installed = installed_integration_keys(state)
    default_key = default_integration_key(state)
    skills = _scan_skills(project_root)
    mcp_configs = _scan_mcp_configs(project_root)
    extensions = _scan_extensions(project_root)

    lines = [
        PROJECTION_MARKER_START,
        "# Agent Governance Projection",
        "",
        "Generated from repository state. Do not edit this section directly; update",
        f"`{AGENT_GOVERNANCE_MEMORY}`, integrations, skills, MCP config, or extensions instead.",
        "",
        "## Governing Source",
        f"- Agent governance SSOT: `{AGENT_GOVERNANCE_MEMORY}`",
        "- Project principles: `.specify/memory/constitution.md`",
        "- Business semantics: `.specify/memory/uc.md`",
        "- Architecture boundaries: `.specify/memory/architecture.md`",
        "",
        "## Active Integrations",
        f"- Default integration: `{default_key or 'none'}`",
        f"- Installed integrations: {', '.join(f'`{key}`' for key in installed) if installed else '`none`'}",
        "",
        "## Active Skills",
    ]

    if skills:
        for skill in skills:
            lines.append(f"- `{skill}`")
    else:
        lines.append("- `none detected`")

    lines.extend(["", "## MCP Configuration"])
    if mcp_configs:
        for config in mcp_configs:
            lines.append(f"- `{config}`")
    else:
        lines.append("- `none detected`")

    lines.extend(["", "## Extensions"])
    if extensions:
        for extension in extensions:
            lines.append(f"- `{extension}`")
    else:
        lines.append("- `none detected`")

    lines.extend([
        "",
        "## Required Operating Rules",
        "- Follow current user instructions first.",
        "- Treat `.specify/memory/agent-governance.md` as the source of truth for agent, skill, and MCP behavior.",
        "- Treat `.specify/memory/constitution.md` as the source of truth for project principles and quality gates.",
        "- Do not edit governance, CI, MCP config, secrets, permissions, or tool settings unless explicitly requested.",
        "- Do not overwrite user edits or modify files outside the active task scope.",
        "- Report changed files, commands run, validation results, and unresolved risks before handoff.",
        "",
        f"_Projection source file: `{memory_path.relative_to(project_root).as_posix()}`_",
        PROJECTION_MARKER_END,
        "",
    ])
    return "\n".join(lines)


def _upsert_marked_section(content: str, projection: str) -> str:
    start = content.find(PROJECTION_MARKER_START)
    end = content.find(PROJECTION_MARKER_END, start if start != -1 else 0)
    if start != -1 and end != -1 and end > start:
        end += len(PROJECTION_MARKER_END)
        if end < len(content) and content[end] == "\r":
            end += 1
        if end < len(content) and content[end] == "\n":
            end += 1
        return content[:start] + projection + content[end:]

    if content and not content.endswith("\n"):
        content += "\n"
    return content + ("\n" if content else "") + projection


def _adapter_prelude(path: Path, default_key: str | None, installed: list[str]) -> str:
    name = path.name
    if name == "AGENTS.md":
        return "# Repo Agent Governance\n\nThis file is the repository-level agent governance projection."
    if name == "CLAUDE.md":
        return "# Claude Instructions\n\nRead `AGENTS.md` first; it is the repository-level agent governance projection."
    if name == "GEMINI.md":
        return "# Gemini Instructions\n\nRead `AGENTS.md` first; it is the repository-level agent governance projection."
    if name == "copilot-instructions.md":
        return "# GitHub Copilot Instructions\n\nRead `AGENTS.md` first; it is the repository-level agent governance projection."
    installed_text = ", ".join(installed) if installed else "none"
    return (
        "# Agent Instructions\n\n"
        "Read `AGENTS.md` first; it is the repository-level agent governance projection.\n\n"
        f"Default integration: `{default_key or 'none'}`. Installed integrations: `{installed_text}`."
    )


def _scan_skills(project_root: Path) -> list[str]:
    skills: list[str] = []
    for skill_file in project_root.rglob("SKILL.md"):
        if any(part in {".git", "__pycache__", ".venv", "node_modules"} for part in skill_file.parts):
            continue
        try:
            rel = skill_file.relative_to(project_root).as_posix()
        except ValueError:
            rel = skill_file.as_posix()
        skills.append(rel)
    return sorted(skills)


def _scan_mcp_configs(project_root: Path) -> list[str]:
    candidates: list[str] = []
    names = {
        ".mcp.json",
        "mcp.json",
        "mcp.yml",
        "mcp.yaml",
        "mcp.config.json",
    }
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", "__pycache__", ".venv", "node_modules"} for part in path.parts):
            continue
        if path.name in names or "mcp" in path.name.lower():
            try:
                candidates.append(path.relative_to(project_root).as_posix())
            except ValueError:
                candidates.append(path.as_posix())
    return sorted(candidates)


def _scan_extensions(project_root: Path) -> list[str]:
    registry = project_root / ".specify" / "extensions.yml"
    if not registry.exists():
        return []
    try:
        data = yaml.safe_load(registry.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError, UnicodeDecodeError):
        return [".specify/extensions.yml"]
    if not isinstance(data, dict):
        return [".specify/extensions.yml"]
    extensions = data.get("extensions")
    if isinstance(extensions, dict):
        return sorted(str(key) for key in extensions)
    if isinstance(extensions, list):
        names = []
        for item in extensions:
            if isinstance(item, dict) and item.get("id"):
                names.append(str(item["id"]))
            elif isinstance(item, str):
                names.append(item)
        return sorted(names) or [".specify/extensions.yml"]
    return [".specify/extensions.yml"]


def _normalize_newlines(content: str) -> str:
    return content.replace("\r\n", "\n").replace("\r", "\n")
