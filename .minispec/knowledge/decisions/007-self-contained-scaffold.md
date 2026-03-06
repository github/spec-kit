# ADR-007: Self-contained scaffold for init-registry

## Status

Accepted

## Context

`minispec init` downloads templates from GitHub releases. The new `init-registry` command needs to create a registry repo scaffold. Options: download from releases (like `init`) or generate inline.

## Decision

Generate the registry scaffold inline from CLI code. No GitHub release dependency.

## Rationale

- The registry scaffold is tiny (registry.yaml, empty packages/ dir, one skill file, README)
- Works offline and in air-gapped enterprise environments
- No build pipeline complexity for a simple scaffold
- Faster — no network request needed

## Consequences

- Skill template content lives in the CLI source code (or as a bundled file)
- Updates to the skill template require a CLI release, not just a template release
