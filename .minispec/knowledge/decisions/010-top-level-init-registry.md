# ADR-010: Top-level init-registry command

## Status

Accepted

## Context

The new command to scaffold registry repos could be a subcommand of `registry` (`minispec registry init`) or a top-level command (`minispec init-registry`).

## Decision

Top-level `minispec init-registry` command, distinct from the `registry` subcommand group.

## Rationale

- `minispec registry add/list/remove/update` operates inside a coding project that consumes registries
- `minispec init-registry` creates a registry repo itself — fundamentally different context
- Parallel to `minispec init` (both are bootstrapping commands)
- Avoids semantic confusion: "registry init" could be misread as "initialize registry state in this project"

## Consequences

- Two `init*` commands at top level (`init` and `init-registry`)
- Clear separation between registry authoring and registry consumption
