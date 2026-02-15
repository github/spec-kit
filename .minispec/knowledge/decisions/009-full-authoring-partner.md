# ADR-009: Registry skill as full authoring partner

## Status

Accepted

## Context

The `/minispec.registry` skill could be a metadata-only scaffold tool (creates package.yaml with stubs) or a full authoring partner that also writes package content (hook scripts, command templates, skill prompts).

## Decision

Full authoring partner. The skill helps write actual package content, not just metadata.

## Rationale

- Fits MiniSpec's pair programming philosophy — the skill IS the expert
- Package authors may not know MiniSpec template patterns (frontmatter, $ARGUMENTS, phases)
- Hooks require shell scripting knowledge the skill can provide
- Users can always modify generated content afterward
- Reduces barrier to entry for first-time registry authors

## Consequences

- Skill template is larger (contains knowledge of command/hook/skill patterns)
- Generated content is a starting point, not a final product
- Skill quality directly impacts package quality
