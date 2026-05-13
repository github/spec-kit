# Repository Agent Governance

This file is the source of truth for repository-level agent collaboration and generated agent instruction projections such as `AGENTS.md` and active integration context files.

It does not define project principles, architecture decisions, or feature requirements. Those remain governed by their own source files.

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
2. This repository agent governance file
3. User-authored repository instructions preserved outside generated projection markers
4. `.specify/memory/constitution.md`
5. Active feature artifacts under `specs/<feature>/`
6. Skill-local `SKILL.md`
7. Tool/MCP defaults

## Source Of Truth

- Project principles: `.specify/memory/constitution.md`
- Feature work: `specs/<feature>/`
- Repository-level agent governance: `.specify/memory/agent-governance.md`
- Agent instruction projections: `AGENTS.md` and active integration context files
- Skill contracts: each `SKILL.md`
- MCP permissions: MCP configuration and allowlists

## Write Boundaries

- Agent code writes are allowed only while executing the generated Spec Kit implement command or integration-equivalent implement skill/alias, such as `/speckit.implement` or `/speckit-implement`.
- Before any agent writes source code, tests, build configuration, migrations, runtime assets, or other implementation files, the active change MUST have `spec.md`, `plan.md`, and `tasks.md` under `specs/<feature>/`.
- Bug fixes, refactors, and small code changes are not exceptions. If the required spec artifacts do not exist, first create or update the spec artifacts through the Spec Kit workflow, then stop before implementation.
- Direct user requests to "just edit code" or similar are treated as requests to run the required spec workflow; they are not permission to bypass the code-write gate.
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
