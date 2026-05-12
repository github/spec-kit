"""Install InfraKit prompt templates as agent skills.

When ``infrakit init --ai-skills`` is set, the per-command prompt files in
``templates/commands/`` are converted into agent "skills" under the agent's
skills directory (e.g. ``.claude/skills/``) following the
`agentskills.io <https://agentskills.io/specification>`_ spec.

This module also exposes :func:`ensure_project_context_from_template`, which
seeds ``.infrakit/memory/project-context.md`` from the bundled template on
fresh inits.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import yaml

from .agent_config import AGENT_CONFIG
from .console import console
from .template_renderer import templates_root
from .tracker import StepTracker

# Agent-specific overrides for agents whose skills directory does not follow
# the standard ``<agent_folder>/skills/`` pattern.
AGENT_SKILLS_DIR_OVERRIDES = {
    "codex": ".agents/skills",  # Codex agent layout override
}

# Default skills directory for agents not in AGENT_CONFIG.
DEFAULT_SKILLS_DIR = ".agents/skills"

# Enhanced descriptions for each infrakit command skill.
SKILL_DESCRIPTIONS = {
    "specify_composition": "Create or update infrastructure resource specifications from natural language descriptions. Use when starting new Crossplane compositions. Generates a structured spec following spec-driven methodology.",
    "plan_composition": "Generate architecture review and implementation plans for Crossplane compositions. Use after creating a spec to define the XRD, Composition, and Claim structure. Produces a detailed plan before any YAML is written.",
    "implement_composition": "Generate XRD, Composition, and example Claim YAML from an approved plan. Use after planning to produce production-ready Crossplane manifests.",
    "review_composition": "Review generated Crossplane YAML against best practices and project coding standards. Checks Pipeline mode usage, patch paths, providerConfigRef patterns, and tagging requirements.",
    "validate_composition": "Run crossplane render validation against generated Composition and Claim manifests. Use to verify the output is syntactically and structurally correct.",
    "analyze": "Perform cross-artifact consistency analysis across spec, plan, and implementation artifacts. Use to identify gaps or inconsistencies before or after implementation.",
    "clarify": "Structured clarification workflow for underspecified infrastructure requirements. Use before planning to resolve ambiguities through targeted questioning.",
    "project_context": "Create or update project context and standards. Use at project start to establish encryption policies, tagging requirements, network topology standards, and compliance rules.",
    "checklist": "Generate quality checklists for validating infrastructure resource completeness and Crossplane best-practice compliance.",
    "taskstoissues": "Convert tasks from tasks.md into GitHub issues. Use after task breakdown to track work items in GitHub project management.",
    "coding_style": "Specify and update the project coding style standards using the coding-style-template.md.",
    "tagging": "Update project tagging requirements using the tagging-standard-template.md.",
}


def _get_skills_dir(project_path: Path, selected_ai: str) -> Path:
    """Resolve the agent-specific skills directory for ``selected_ai``.

    Resolution order:

    1. :data:`AGENT_SKILLS_DIR_OVERRIDES` (per-agent escape hatch).
    2. ``AGENT_CONFIG[agent]["folder"] + "skills"``.
    3. :data:`DEFAULT_SKILLS_DIR`.
    """
    if selected_ai in AGENT_SKILLS_DIR_OVERRIDES:
        return project_path / AGENT_SKILLS_DIR_OVERRIDES[selected_ai]

    agent_config = AGENT_CONFIG.get(selected_ai, {})
    agent_folder = agent_config.get("folder", "")
    if agent_folder:
        return project_path / agent_folder.rstrip("/") / "skills"

    return project_path / DEFAULT_SKILLS_DIR


def ensure_project_context_from_template(
    project_path: Path, tracker: Optional[StepTracker] = None
) -> None:
    """Seed ``.infrakit/memory/project-context.md`` from the bundled template
    if it doesn't exist yet. Existing user content is always preserved.
    """
    memory_context = project_path / ".infrakit" / "memory" / "project-context.md"
    template_context = templates_root() / "project-context-template.md"

    if memory_context.exists():
        if tracker:
            tracker.add("project_context", "Project Context setup")
            tracker.skip("project_context", "existing file preserved")
        return

    if not template_context.exists():
        if tracker:
            tracker.add("project_context", "Project Context setup")
            tracker.error("project_context", "template not found")
        return

    try:
        memory_context.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_context, memory_context)
        if tracker:
            tracker.add("project_context", "Project Context setup")
            tracker.complete("project_context", "copied from template")
        else:
            console.print("[cyan]Initialized project context from template[/cyan]")
    except Exception as e:
        if tracker:
            tracker.add("project_context", "Project Context setup")
            tracker.error("project_context", str(e))
        else:
            console.print(
                f"[yellow]Warning: Could not initialize project context: {e}[/yellow]"
            )


def install_ai_skills(
    project_path: Path,
    selected_ai: str,
    tracker: Optional[StepTracker] = None,
) -> bool:
    """Install prompt-template files from ``templates/commands/`` as agent skills.

    Skills are written to the agent-specific skills directory following the
    `agentskills.io <https://agentskills.io/specification>`_ specification.
    Installation is additive — existing skill files are never overwritten
    and prompt command files in the agent's commands directory are left
    untouched.

    Args:
        project_path: Target project directory.
        selected_ai: AI assistant key from :data:`AGENT_CONFIG`.
        tracker: Optional progress tracker.

    Returns:
        ``True`` if at least one skill was installed or all skills were
        already present (idempotent re-run), ``False`` otherwise.
    """
    # Locate command templates. They were just rendered by ``materialize_project``
    # into the agent's folder; for agents whose rendered commands are not .md
    # (e.g. gemini emits .toml), fall back to the bundled source templates so
    # we install skills from the canonical markdown.
    agent_config = AGENT_CONFIG.get(selected_ai, {})
    agent_folder = agent_config.get("folder", "")
    commands_subdir = agent_config.get("commands_subdir", "commands")
    if agent_folder:
        rendered_dir = project_path / agent_folder.rstrip("/") / commands_subdir
    else:
        rendered_dir = project_path / commands_subdir

    if not rendered_dir.exists() or not any(rendered_dir.glob("*.md")):
        fallback_dir = templates_root() / "commands"
        if fallback_dir.exists() and any(fallback_dir.glob("*.md")):
            rendered_dir = fallback_dir

    if not rendered_dir.exists() or not any(rendered_dir.glob("*.md")):
        if tracker:
            tracker.error("ai-skills", "command templates not found")
        else:
            console.print(
                "[yellow]Warning: command templates not found, skipping skills installation[/yellow]"
            )
        return False

    command_files = sorted(rendered_dir.glob("*.md"))
    if not command_files:
        if tracker:
            tracker.skip("ai-skills", "no command templates found")
        else:
            console.print("[yellow]No command templates found to install[/yellow]")
        return False

    skills_dir = _get_skills_dir(project_path, selected_ai)
    skills_dir.mkdir(parents=True, exist_ok=True)

    if tracker:
        tracker.start("ai-skills")

    installed_count = 0
    skipped_count = 0
    for command_file in command_files:
        try:
            content = command_file.read_text(encoding="utf-8")

            # Parse YAML frontmatter.
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    if not isinstance(frontmatter, dict):
                        frontmatter = {}
                    body = parts[2].strip()
                else:
                    # File starts with --- but has no closing ---
                    console.print(
                        f"[yellow]Warning: {command_file.name} has malformed frontmatter (no closing ---), treating as plain content[/yellow]"
                    )
                    frontmatter = {}
                    body = content
            else:
                frontmatter = {}
                body = content

            command_name = command_file.stem
            # Normalize: extracted commands may be named "infrakit:<cmd>.md";
            # strip the "infrakit:" prefix so skill names stay clean and
            # ``SKILL_DESCRIPTIONS`` lookups work.
            if command_name.startswith("infrakit:"):
                command_name = command_name[len("infrakit:"):]
            skill_name = f"infrakit-{command_name}"

            skill_dir = skills_dir / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)

            original_desc = frontmatter.get("description", "")
            enhanced_desc = SKILL_DESCRIPTIONS.get(
                command_name,
                original_desc or f"InfraKit workflow command: {command_name}",
            )

            # ``yaml.safe_dump`` to safely serialise the frontmatter and avoid
            # YAML injection from descriptions containing colons, quotes, or
            # newlines.
            source_name = command_file.name
            if source_name.startswith("infrakit:"):
                source_name = source_name[len("infrakit:"):]

            frontmatter_data = {
                "name": skill_name,
                "description": enhanced_desc,
                "compatibility": "Requires InfraKit project structure with .infrakit/ directory",
                "metadata": {
                    "author": "neelneelpurk",
                    "source": f"templates/commands/{source_name}",
                },
            }
            frontmatter_text = yaml.safe_dump(frontmatter_data, sort_keys=False).strip()
            skill_content = (
                f"---\n"
                f"{frontmatter_text}\n"
                f"---\n\n"
                f"# InfraKit {command_name.title()} Skill\n\n"
                f"{body}\n"
            )

            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                # Do not overwrite user-customised skills on re-runs.
                skipped_count += 1
                continue
            skill_file.write_text(skill_content, encoding="utf-8")
            installed_count += 1

        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to install skill {command_file.stem}: {e}[/yellow]"
            )
            continue

    if tracker:
        if installed_count > 0 and skipped_count > 0:
            tracker.complete(
                "ai-skills",
                f"{installed_count} new + {skipped_count} existing skills in {skills_dir.relative_to(project_path)}",
            )
        elif installed_count > 0:
            tracker.complete(
                "ai-skills",
                f"{installed_count} skills → {skills_dir.relative_to(project_path)}",
            )
        elif skipped_count > 0:
            tracker.complete("ai-skills", f"{skipped_count} skills already present")
        else:
            tracker.error("ai-skills", "no skills installed")
    else:
        if installed_count > 0:
            console.print(
                f"[green]✓[/green] Installed {installed_count} agent skills to {skills_dir.relative_to(project_path)}/"
            )
        elif skipped_count > 0:
            console.print(
                f"[green]✓[/green] {skipped_count} agent skills already present in {skills_dir.relative_to(project_path)}/"
            )
        else:
            console.print("[yellow]No skills were installed[/yellow]")

    return installed_count > 0 or skipped_count > 0
