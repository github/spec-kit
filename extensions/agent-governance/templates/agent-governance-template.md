# Agent Governance Cache

<!--
Sync Impact Report
-->

## Final Output

- active agent platform governance file
- managed `SPECKIT GOVERNANCE` section
- cache: internal

## Directory Governance

- Responsibility: one primary purpose per directory.
- Depth: 2.
- Coverage: include visible, hidden, generated, cache, config/env, tool, and agent directories.
- Mixed concerns: follow existing repo convention or split responsibility.
- Change impact: review linked code, tests, docs, config/env, data, assets, generated files, and tool outputs; update only when in scope and authorized.

## Scope

- agent collaboration rules
- tool and MCP permissions
- write boundaries
- skill invocation contracts
- project governance: external

## Write Boundaries

- Scope: active task only
- Preserve: user-authored edits
- Preserve managed markers verbatim: `<!-- SPECKIT GOVERNANCE START -->` and `<!-- SPECKIT GOVERNANCE END -->`
- Protected files: implementation, CI, MCP config, secrets, permissions, tool settings
- Protected-file writes: explicit user request only

## Skill Contract

- Repository-local skill specs should declare purpose, trigger, allowed read paths, allowed write paths, forbidden paths, outputs, and validation command.

## MCP Policy

- Default: read-only
- Mutation: explicit user intent
- External writes: target, action, result
- Secrets: never log, never write

## Validation

- changed files
- commands run
- tests/validation result
- unresolved risks
