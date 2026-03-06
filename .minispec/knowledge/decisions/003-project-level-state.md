# ADR-003: Project-level registry state only

## Status

Accepted

## Context

Registry configuration and installed package state could live at user level (`~/.minispec/`), project level (`.minispec/`), or both.

## Decision

All registry state lives at project level in `.minispec/registries.yaml`. No user-level registry configuration.

## Rationale

- Everything is explicit, shareable, and auditable
- Team members see the same registries and installed packages
- Version-controlled — changes are tracked in Git
- No hidden user-level configuration that could differ between team members
- Simplifies the mental model — one place for everything

## Consequences

- Must re-add registries per project (no global registry list)
- Team onboarding requires cloning the repo to get registry config
