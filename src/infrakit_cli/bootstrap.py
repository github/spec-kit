"""IaC project bootstrap — writes ``.infrakit/`` and ``.infrakit_tracks/``.

:func:`initialize_iac_config` is the single function called by
``infrakit init`` (and the corresponding tests) to materialise everything a
freshly-bootstrapped InfraKit project needs:

- ``.infrakit/config.yaml`` recording the selected IaC tool + AI assistant
- ``.infrakit/context.md`` + ``.infrakit/coding-style.md`` (from IaC-specific assets)
- ``.infrakit/tagging-standard.md`` (shared template)
- ``.infrakit/mcp-use.md`` (empty installed-MCP index)
- ``.infrakit/memory/`` (project memory directory)
- ``.infrakit_tracks/tracks.md`` (master resource registry)
- ``.infrakit_tracks/tracks/`` (per-track working directories)
- Rendered slash commands + personas via
  :func:`infrakit_cli.template_renderer.materialize_project`.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import yaml

from .agent_config import AGENT_CONFIG
from .iac_config import IAC_CONFIG
from .template_renderer import materialize_project, templates_root
from .tracker import StepTracker


def initialize_iac_config(
    project_path: Path,
    iac_tool: str,
    ai_assistant: str,
    *,
    tracker: Optional[StepTracker] = None,
) -> None:
    """Set up IaC-specific configuration, commands, agents, and documentation.

    Creates:

    - ``.infrakit/config.yaml`` — selected IaC tool and AI agent
    - ``.infrakit/context.md`` — project context template (copied if absent)
    - ``.infrakit/coding-style.md`` — default coding standards (copied if absent)
    - ``.infrakit/tagging-standard.md`` — shared tagging template (copied if absent)
    - ``.infrakit/mcp-use.md`` — installed MCP server index (created if absent)
    - ``.infrakit/memory/`` — per-project memory directory
    - ``.infrakit_tracks/tracks.md`` — master resource registry
    - ``.infrakit_tracks/tracks/`` — track working directories
    - Rendered IaC-native commands in the agent's commands directory
    - Rendered IaC + generic personas under ``.infrakit/agent_personas/``
    """
    iac_cfg = IAC_CONFIG.get(iac_tool, {})
    if not iac_cfg:
        if tracker:
            tracker.error("iac-config", f"unknown IaC tool: {iac_tool}")
        return

    tpl_root = templates_root()
    iac_templates_dir = tpl_root / "iac" / iac_tool

    # --- 1. Create .infrakit/ configuration directory --------------------

    if tracker:
        tracker.start("iac-config")

    infrakit_dir = project_path / ".infrakit"
    infrakit_dir.mkdir(parents=True, exist_ok=True)

    infrakit_tracks_dir = project_path / ".infrakit_tracks"
    infrakit_tracks_dir.mkdir(parents=True, exist_ok=True)

    # config.yaml — never overwritten on subsequent init runs.
    config_data = {
        "iac_tool": iac_tool,
        "iac_name": iac_cfg.get("name", iac_tool),
        "ai_assistant": ai_assistant,
        "resource_term": iac_cfg.get("resource_term", "composition"),
    }
    config_file = infrakit_dir / "config.yaml"
    if not config_file.exists():
        config_file.write_text(
            yaml.dump(config_data, sort_keys=False), encoding="utf-8"
        )

    # Copy assets (context.md, coding-style.md) from the IaC asset templates.
    assets_dir = iac_templates_dir / "assets"
    if assets_dir.is_dir():
        for asset_file in assets_dir.iterdir():
            if asset_file.is_file():
                dest = infrakit_dir / asset_file.name.replace(
                    "context_template", "context"
                ).replace("default_coding_style", "coding-style").replace(
                    "coding-style-template", "coding-style"
                )
                if not dest.exists():
                    shutil.copy2(asset_file, dest)

    # tracks.md — master resource registry.
    tracks_md = infrakit_tracks_dir / "tracks.md"
    if not tracks_md.exists():
        tracks_md.write_text(
            "# Infrastructure Resource Registry\n\n"
            "Track all infrastructure compositions and their current status.\n\n"
            "## Status Reference\n\n"
            "| Symbol | Meaning |\n"
            "|--------|---------|\n"
            "| 🔵 `initializing` | Track created, spec in progress |\n"
            "| 📝 `spec-generated` | Spec confirmed, ready for plan |\n"
            "| 📋 `planned` | Plan generated, ready for implementation |\n"
            "| ⚙️ `in-progress` | Implementation underway |\n"
            "| ✅ `done` | Implementation complete and reviewed |\n"
            "| ❌ `blocked` | Blocked, needs attention |\n\n"
            "---\n\n"
            "## Tracks\n\n"
            "| Track | Type | Directory | Status | Created |\n"
            "|-------|------|-----------|--------|---------|\n"
            "| (none yet) | — | — | — | — |\n",
            encoding="utf-8",
        )

    # tagging-standard.md — shared, IaC-agnostic tagging standard.
    tagging_std_md = infrakit_dir / "tagging-standard.md"
    if not tagging_std_md.exists():
        shared_tagging_template = tpl_root / "tagging-standard-template.md"
        if shared_tagging_template.is_file():
            shutil.copy2(shared_tagging_template, tagging_std_md)
        else:
            tagging_std_md.write_text(
                "# Tagging Standard\n\n"
                "> Run `/infrakit:setup` to configure your project-specific tagging requirements.\n",
                encoding="utf-8",
            )

    # mcp-use.md — installed MCP server index.
    mcp_use_md = infrakit_dir / "mcp-use.md"
    if not mcp_use_md.exists():
        mcp_use_md.write_text(
            "# Installed MCP Servers\n\n"
            "MCP servers configured for this project.\n"
            "Run `infrakit mcp` to add more.\n\n"
            "| MCP | Description | Tools | Usage |\n"
            "|-----|-------------|-------|-------|\n"
            "| — | — | — | — |\n",
            encoding="utf-8",
        )

    # Memory directory (for project context).
    (infrakit_dir / "memory").mkdir(parents=True, exist_ok=True)

    # Per-track working directories live under .infrakit_tracks/tracks/.
    tracks_dir = infrakit_tracks_dir / "tracks"
    tracks_dir.mkdir(parents=True, exist_ok=True)

    if tracker:
        tracker.complete("iac-config", f"{iac_tool} ({iac_cfg.get('name', '')})")

    # --- 2. Render commands + personas via the runtime renderer ---------

    if tracker:
        tracker.start("iac-commands")

    counts = materialize_project(
        project_path,
        ai_assistant=ai_assistant,
        iac_tool=iac_tool,
        overwrite=False,
    )

    agent_cfg = AGENT_CONFIG.get(ai_assistant, {})
    agent_folder = (agent_cfg.get("folder") or "").rstrip("/")
    commands_subdir = agent_cfg.get("commands_subdir", "commands")
    cmds_dest = (
        project_path / agent_folder / commands_subdir
        if agent_folder
        else project_path / commands_subdir
    )

    if tracker:
        tracker.complete(
            "iac-commands",
            f"{counts['generic_commands']} generic + {counts['iac_commands']} IaC commands → {cmds_dest.relative_to(project_path)}",
        )
