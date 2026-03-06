# ADR-002: Explicit file mapping in package.yaml

## Status

Accepted

## Context

Packages need to declare where their files get installed. Two options: infer from package type (e.g., `command` type always goes to `.claude/commands/`) or let packages explicitly declare source-to-target mappings.

## Decision

Use explicit file mapping in `package.yaml` where each file declares its source and target path, plus optional merge behavior.

## Rationale

- Packages can target multiple AI agents with different file locations
- Authors have full control over installation layout
- No hidden conventions to learn or debug
- Supports merge behavior for config files (e.g., merging into existing `settings.json`)

## Consequences

- More verbose `package.yaml` compared to inferred mapping
- Package authors must know target paths for each agent
