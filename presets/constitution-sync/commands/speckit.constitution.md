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

> **This section supersedes the "Scope Guard" above for template and command propagation.**
> The core Scope Guard states that dependent templates and commands "are not modified here" —
> that restriction is intentionally lifted by this preset. Propagating amended guidance into the
> project's own dependent scaffolds and installed command files (as described below) **is in
> scope** whenever this preset is installed. The Scope Guard's other constraints still apply:
> do not implement features, generate application code, or touch artifacts unrelated to the
> constitution/template workflow.

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
   is required. **Only hand-edit a command file if it is a project-local file not managed by a
   preset or extension.** Command files that are composed from the resolution stack (anything
   provided or wrapped by a preset/extension) must be regenerated through the stack — do **not**
   edit them in place, because reconciliation (`specify integration use`, `specify integration
   upgrade`, or any preset/extension install/remove) will clobber the edits.
5. Read any runtime guidance docs (e.g., `README.md`, `docs/quickstart.md`, or agent-specific
   guidance files if present) and update references to principles that changed.

Then extend the Sync Impact Report at the top of `.specify/memory/constitution.md` with:

- Templates requiring updates (✅ updated / ⚠ pending) with file paths.

**Do not edit versioned preset- or extension-provided template or command files directly.** Those
artifacts are owned by their packages and are recomposed on the package's next update or on stack
reconciliation — hand edits are clobbered. Limit propagation to the project's own
`.specify/templates/` scaffolds and to command files that are not managed by a preset or extension.
