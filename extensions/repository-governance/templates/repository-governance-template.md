# Repository Governance Framework Cache

<!--
Sync Impact Report
-->

## Final Output

- active repository governance file
- managed `SPECKIT GOVERNANCE` section
- cache: internal

## Scope

- Repository Governance Framework
- top-level SSOT registry and routing
- vertical SSOT discovery and read order
- missing SSOT handling from repository evidence
- conflict priority and handoff requirements
- architecture methodology: owned by Architecture SSOT

## Vertical SSOT Registry

- Architecture SSOT: owns architecture boundaries, interfaces, dependencies, runtime constraints, deployment assumptions, and scenario-level architecture decisions.
- Engineering SSOT: owns branch, version, release, CI/CD, and collaboration process.
- Code Style SSOT: owns naming, formatting, comments, error handling, logging, tests, and quality standards.
- Directory Structure SSOT: owns directory layout, file placement, module organization, and configuration locations.
- Toolchain SSOT: owns standard tools, command entrypoints, configuration templates, and execution constraints.
- Agent Harness SSOT: owns agent task boundaries, tool usage, permissions, audit, validation, and failure handling.

## SSOT Read Order

1. Current user instruction
2. Safety and permission constraints
3. Active `SPECKIT GOVERNANCE` section
4. Vertical SSOT documents
5. Current repository code and configuration facts
6. Tests and CI results
7. Historical documents
8. Agent inference

## Missing SSOT Handling

- If a vertical SSOT is missing or incomplete, infer temporary guidance from current repository evidence.
- Mark inferred guidance as pending SSOT solidification.
- Do not present inferred guidance as an approved repository rule.
- Do not let inference override explicit SSOT content.

## Vertical SSOT Evidence

- Architecture evidence: none detected
- Engineering evidence: none detected
- Code Style evidence: none detected
- Directory Structure evidence: none detected
- Toolchain evidence: none detected
- Agent Harness evidence: none detected

## Directory Governance

- Responsibility: one primary purpose per directory.
- Depth: 2.
- Coverage: include visible, hidden, generated, cache, config/env, tool, and agent directories.
- Mixed concerns: follow existing repo convention or split responsibility.
- Change impact: review linked code, tests, docs, config/env, data, assets, generated files, and tool outputs; update only when in scope and authorized.

## Write Boundaries

- Scope: active task only
- Preserve: user-authored edits
- Preserve managed markers verbatim: `<!-- SPECKIT GOVERNANCE START -->` and `<!-- SPECKIT GOVERNANCE END -->`
- Protected files: implementation, CI, MCP config, secrets, permissions, tool settings
- Protected-file writes: explicit user request only

## Agent Platform Adapter

- Repository Capability: abstract repository-local skill and MCP evidence into scenario capabilities.
- Spec Kit Agent Adapter: map integration metadata to the active agent context target and supported discovery behavior.
- Platform Projection: emit only the rules the active agent context file can safely apply.

## Capability Index

- Repository-local skills: use when the task matches a declared skill name, description, or trigger.
- MCP-backed external tools: use when the task needs external tool or resource access; enumerate runtime tools before use.
- Repository config candidates are evidence only unless the active adapter supports them.

## Skill Contract

- Repository-local skill specs should declare name, description or trigger, allowed read paths, allowed write paths, forbidden paths, outputs, and validation command.
- Read matching `SKILL.md` files before planning or editing.

## MCP Policy

- Default: read-only
- Mutation: explicit user intent
- Runtime discovery: enumerate available servers, resources, and tools before use.
- Config candidates: evidence only, not proof of active tools.
- External writes: target, action, result
- Secrets: never log, never write

## Validation

- changed files
- commands run
- tests/validation result
- unresolved risks
