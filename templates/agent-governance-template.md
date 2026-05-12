# Agent Governance

<!--
Sync Impact Report
- Version: 0.1.0
- Active Integration: TODO(ACTIVE_INTEGRATION)
- Skills Scanned: TODO(SKILL_COUNT)
- MCP Servers Scanned: TODO(MCP_COUNT)
- Projections Updated: TODO(PROJECTION_FILES)
-->

## Authority Order

1. Current user instruction
2. This agent governance file
3. `.specify/memory/constitution.md`
4. `.specify/memory/architecture.md`
5. `.specify/memory/uc.md`
6. Active feature artifacts under `specs/<feature>/`
7. Skill-local `SKILL.md`
8. Tool/MCP defaults

## Source Of Truth

- Project principles: `.specify/memory/constitution.md`
- Business semantics: `.specify/memory/uc.md`
- Architecture boundaries: `.specify/memory/architecture.md`
- Feature work: `specs/<feature>/`
- Agent operations: `.specify/memory/agent-governance.md`
- Skill contracts: each `SKILL.md`
- MCP permissions: MCP configuration and allowlists

## Write Boundaries

- Do not edit governance, CI, MCP config, secrets, permissions, or tool settings unless explicitly requested.
- Do not modify files outside the active task scope.
- Do not overwrite user edits.
- Do not rewrite generated files unless the owning workflow requires it.

## Skill Contract

Each skill must declare:

- purpose
- trigger
- allowed read paths
- allowed write paths
- forbidden paths
- outputs
- validation command

## MCP Policy

- MCP tools are read-only by default.
- Mutating MCP calls require explicit user intent.
- External writes must report target, action, and result.
- Secrets and tokens must never be logged or written to repo files.

## Validation

Before handoff, report:

- changed files
- commands run
- tests/validation result
- unresolved risks

