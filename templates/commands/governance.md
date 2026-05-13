---
description: Create or update agent governance and refresh agent instruction projections.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

You are updating repository-level agent governance for this project. The source file is `.specify/memory/agent-governance.md`. Generated agent instruction projections such as `AGENTS.md` and active integration context files are owned by `__SPECKIT_COMMAND_GOVERNANCE__`.

This command governs agent collaboration, skill usage, MCP/tool permissions, and integration adapter behavior. It MUST NOT redefine project principles or feature requirements.

**Note**: If `.specify/memory/agent-governance.md` does not exist yet, copy `.specify/templates/agent-governance-template.md` first.

Follow this execution flow:

1. Load `.specify/memory/agent-governance.md`.
2. Load supporting context if present:
   - `.specify/memory/constitution.md` for project principles and quality gates.
   - `.specify/integration.json` for installed/default integrations.
   - Any `SKILL.md` files for skill-local contracts.
   - MCP configuration files such as `.mcp.json`, `mcp.json`, `mcp.yml`, or `mcp.yaml`.
   - `.specify/extensions.yml` for enabled extensions.
3. Update agent governance:
   - Keep the authority order explicit.
   - Keep source-of-truth boundaries between agent governance, constitution, skills, MCP, and feature artifacts.
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
- `AGENTS.md` is the repo-level agent governance projection owned by `__SPECKIT_COMMAND_GOVERNANCE__`.
- Agent-specific files are adapters that point back to `AGENTS.md`.
- Specify governance files keep their own authority and must not be rewritten by this command unless the user explicitly requests that separate change.
- Do not modify `.specify/memory/constitution.md`, feature specs, plans, tasks, source code, tests, CI, MCP config, or secrets unless the user explicitly requested that separate change.

## Output

Report:

- Whether `.specify/memory/agent-governance.md` was created or updated.
- Projection files refreshed.
- Skills and MCP config files detected.
- Any unresolved governance risks.
