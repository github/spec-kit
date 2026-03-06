# ADR-008: Single agent selection for registry repos

## Status

Accepted

## Context

Registry repos need the builder skill installed for an AI agent. Options: require one agent, support multiple, or install for all agents.

## Decision

Support a single `--ai` flag with an interactive picker (same UX as `minispec init`). One agent folder per registry repo.

## Rationale

- Registry authors typically use one primary AI agent
- Keeps the scaffold clean — no unused agent folders
- Consistent with `minispec init` UX
- Authors can manually copy the skill to another agent folder if needed

## Consequences

- Switching agents requires manually moving/copying the skill file
- No multi-agent skill installation in one command
