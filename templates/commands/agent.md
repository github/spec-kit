---
description: Create or update agent governance and refresh agent instruction projections.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

You are updating `.specify/memory/agent-governance.md`, the source of truth for how AI agents, skills, MCP tools, and integration adapters operate in this repository.

**Note**: If `.specify/memory/agent-governance.md` does not exist yet, copy `.specify/templates/agent-governance-template.md` first.

Follow this execution flow:

1. Load `.specify/memory/agent-governance.md`.
2. Load supporting context if present:
   - `.specify/memory/constitution.md` for project principles and quality gates.
   - `.specify/memory/architecture.md` for architecture boundaries.
   - `.specify/memory/uc.md` for business semantics.
   - `.specify/integration.json` for installed/default integrations.
   - Any `SKILL.md` files for skill-local contracts.
   - MCP configuration files such as `.mcp.json`, `mcp.json`, `mcp.yml`, or `mcp.yaml`.
   - `.specify/extensions.yml` for enabled extensions.
3. Update agent governance:
   - Keep the authority order explicit.
   - Keep source-of-truth boundaries between constitution, architecture, UC, skills, MCP, and feature artifacts.
   - Keep write boundaries testable and concrete.
   - Require explicit user intent for mutating MCP calls and external writes.
   - Preserve user-authored repo-specific rules unless they conflict with higher authority.
4. Refresh projections:
   - `AGENTS.md`
   - active integration context files such as `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, and other registered `context_file` paths.
   - Preserve content outside `<!-- SPECKIT AGENT PROJECTION START -->` and `<!-- SPECKIT AGENT PROJECTION END -->`.
5. Produce a Sync Impact Report in `.specify/memory/agent-governance.md`:
   - Active/default integration
   - Installed integrations
   - Skills scanned
   - MCP config files scanned
   - Projection files refreshed
   - Follow-up TODOs

## Validation

- No projection file should duplicate long governance text outside the generated projection markers.
- `AGENTS.md` is the repo-level agent governance projection.
- Agent-specific files are adapters that point back to `AGENTS.md`.
- Do not modify `.specify/memory/constitution.md`, `.specify/memory/architecture.md`, `.specify/memory/uc.md`, feature specs, plans, tasks, source code, tests, CI, MCP config, or secrets unless the user explicitly requested that separate change.

## Output

Report:

- Whether `.specify/memory/agent-governance.md` was created or updated.
- Projection files refreshed.
- Skills and MCP config files detected.
- Any unresolved governance risks.

