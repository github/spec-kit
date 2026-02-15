# ADR-006: Require explicit registry on name conflicts

## Status

Accepted

## Context

When a package name exists in multiple configured registries, MiniSpec needs a conflict resolution strategy. Options: first match wins, require explicit registry, or priority system.

## Decision

Error and require `--registry` flag when a package name is found in multiple registries.

## Rationale

- No silent decisions about which code gets installed
- Critical for enterprise safety — accidental installation from wrong source is a security risk
- Simple to understand and debug
- Aligns with principle of explicitness over convenience

## Consequences

- Slightly more typing when conflicts exist
- Users must know which registry a package belongs to
