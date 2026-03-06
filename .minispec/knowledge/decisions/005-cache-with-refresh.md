# ADR-005: User-level cache with explicit refresh

## Status

Accepted

## Context

When MiniSpec fetches registry repos, it needs to decide where to cache them and how to handle staleness.

## Decision

Cache registry repos at `~/.cache/minispec/registries/<name>/`. Cache persists across sessions. Refresh explicitly via `--refresh` flag or `minispec registry update`.

## Rationale

- Fast installs — no network fetch on every operation
- Stable — installations don't break because someone pushed to the registry
- Works well with slow/restricted enterprise networks (VPN, air-gapped)
- Explicit refresh gives users control over when they pull updates
- Cache is user-level because it's just a performance optimization, not state

## Consequences

- Cache can become stale — users must remember to refresh
- First install for a new registry requires network access
