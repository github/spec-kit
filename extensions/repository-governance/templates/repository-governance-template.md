# Project Governance Projection Template

<!--
Sync Impact Report
-->

## Final Output

- active agent platform project-governance projection
- generated active agent platform target file

## Repository-Wide Instructions

- Framework: Project Governance Projection Framework.
- Generate and review only the resolved active agent platform target.
- Use the Copilot instruction model for layering only; do not emit Copilot path-specific companion files.
- Keep instructions short, self-contained, and free of conflicting rules.
- Legacy managed-section cleanup: non-active context files enumerated by `CONTEXT_FILES`.
- architecture methodology: owned by Architecture SSOT.

### Authority

1. Current user instruction
2. Safety and permission constraints
3. Vertical SSOT documents
4. Current repository code and configuration facts
5. Active `PROJECT GOVERNANCE` projection
6. Tests and CI results
7. Historical documents
8. Agent inference

- Active projection is generated routing guidance and is subordinate to explicit vertical SSOT documents or source-backed repository facts on substantive conflicts.

## SSOT Routing

- Architecture SSOT: owns architecture boundaries, interfaces, dependencies, runtime constraints, deployment assumptions, and scenario-level architecture decisions.
- Engineering SSOT: owns branch, version, release, CI/CD, collaboration process, standard tools, command entrypoints, configuration templates, and execution constraints.
- Code Style SSOT: owns naming, formatting, comments, error handling, logging, tests, and quality standards.
- Directory Structure SSOT: owns directory layout, file placement, module organization, and configuration locations.
- Agent Harness SSOT: owns agent task boundaries, tool usage, permissions, audit, validation, and failure handling.
- Architecture evidence: none detected
- Engineering evidence: none detected
- Code Style evidence: none detected
- Directory Structure evidence: none detected
- Agent Harness evidence: none detected

### Missing SSOT Handling

- If a vertical SSOT is missing or incomplete, infer temporary guidance from current repository evidence.
- Mark inferred guidance as pending SSOT solidification.
- Do not present inferred guidance as an approved repository rule.
- Do not let inference override explicit SSOT content.

## Repository Evidence

- Repository facts are descriptive source-backed evidence.
- Repository facts do not override explicit vertical SSOT content.

## Path And Task Scope Rules

- Source, API, route, runtime, infra, or dependency-boundary changes: read Architecture SSOT before planning edits.
- Build, release, CI, manifest, lockfile, command, template, or runtime configuration changes: read Engineering SSOT before edits.
- Formatting, linting, typing, testing, logging, comments, naming, or error-handling changes: read Code Style SSOT before edits.
- New files, moved files, generated assets, or directory responsibility changes: read Directory Structure SSOT before edits.
- Agent instructions, permissions, MCP, external tools, skills, validation, or failure-handling changes: read Agent Harness SSOT before edits.
- If multiple rules match, read every matched SSOT and apply the highest authority non-conflicting rule.

### Directory Governance

- Responsibility: one primary purpose per directory.
- Depth: 2.
- Coverage: include visible, hidden, generated, cache, config/env, tool, and agent directories.
- Mixed concerns: follow existing repo convention or split responsibility.
- Change impact: review linked code, tests, docs, config/env, data, assets, generated files, and tool outputs; update only when in scope and authorized.

## Agent Harness

- Repository Capability: abstract repository-local skill and MCP evidence into scenario capabilities.
- Spec Kit Agent Adapter: map integration metadata to the active agent platform target and supported discovery behavior.
- Platform Projection: emit only the rules the active agent platform target can safely apply.
- Repository-local skills: use when the task matches a declared skill name, description, or trigger.
- MCP-backed external tools: use when the task needs external tool or resource access; enumerate runtime tools before use.
- Repository config candidates are evidence only unless the active adapter supports them.
- Repository-local skill specs should declare name, description or trigger, allowed read paths, allowed write paths, forbidden paths, outputs, and validation command.
- Read matching `SKILL.md` files before planning or editing.
- MCP default: read-only.
- MCP mutation: explicit user intent with target, action, and expected effect.
- Secrets: never log, never write.

## Write Boundaries

- Scope: active task only.
- Active agent platform target: generated output, overwritten on generation.
- Legacy managed-section cleanup: non-active context files enumerated by `CONTEXT_FILES`.
- Protected files: implementation paths, CI configuration, MCP configuration, secrets, permissions, tool settings, and arbitrary repository paths outside the resolved write surface.
- Protected-file writes: explicit user request, named matching contract or regression test, and passing validation commands.

## Development Commands

- none recorded

## Handoff

- changed files
- commands run
- validation result
- unresolved risks
