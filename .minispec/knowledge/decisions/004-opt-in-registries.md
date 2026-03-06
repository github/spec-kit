# ADR-004: Registries are opt-in, no defaults

## Status

Accepted

## Context

`minispec init` could configure a default official registry automatically, making `minispec search/install` work immediately. Alternatively, registries could be purely opt-in.

## Decision

`minispec init` does not configure any registry. Registries are purely opt-in via `minispec registry add`.

## Rationale

- MiniSpec works out of the box without external dependencies
- Air-gapped enterprise environments work without modification
- No assumption that users can reach external Git repos
- Reduces adoption friction — no unexpected network calls
- Security-conscious users aren't surprised by external sources

## Consequences

- Users must explicitly add registries before using `search/install`
- Official registry requires one extra command to set up
