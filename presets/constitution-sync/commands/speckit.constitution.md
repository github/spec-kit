---
description: Create or update the project constitution, then propagate the amended guidance into dependent templates and installed command files (opt-in template sync).
strategy: wrap
handoffs:
  - label: Build Specification
    agent: speckit.specify
    prompt: Implement the feature specification based on the updated constitution. I want to build...
---

{CORE_TEMPLATE}

## Constitution Template Sync

After you have written the updated constitution above, perform a consistency propagation pass
so the dependent artifacts reflect the amended principles:

1. Read `.specify/templates/plan-template.md` and ensure any "Constitution Check" or rules align
   with the updated principles. Only materialize concrete gate text here if your team intends to
   review it as committed content; otherwise leave the runtime pointer
   `[Gates determined based on constitution file]` in place so `/plan` fills it from the live
   constitution.
2. Read `.specify/templates/spec-template.md` for scope/requirements alignment — update if the
   constitution adds/removes mandatory sections or constraints.
3. Read `.specify/templates/tasks-template.md` and ensure task categorization reflects new or
   removed principle-driven task types (e.g., observability, versioning, testing discipline).
4. Read each installed Spec Kit command file for your agent (including this one) — named
   `speckit.*` or `speckit-*` (dot or hyphen depending on the agent), or laid out as
   `speckit-<name>/SKILL.md` for skills-based integrations, e.g. in `.github/agents/`,
   `.github/skills/`, `.claude/skills/`, or your agent's equivalent commands directory — to verify
   no outdated references (CLAUDE-only or other agent-specific names) remain when generic guidance
   is required.
5. Read any runtime guidance docs (e.g., `README.md`, `docs/quickstart.md`, or agent-specific
   guidance files if present) and update references to principles that changed.

Then extend the Sync Impact Report at the top of `.specify/memory/constitution.md` with:

- Templates requiring updates (✅ updated / ⚠ pending) with file paths.

**Do not edit versioned preset- or extension-provided template files directly.** Those artifacts
are owned by their packages and are recomposed on the package's next update — hand edits are
clobbered. Limit propagation to the project's own `.specify/templates/` scaffolds and installed
command files.
