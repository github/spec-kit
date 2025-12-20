---
name: architecture-decision-records
description: |
  Create and maintain Architecture Decision Records (ADRs) to document significant technical decisions, their context, and consequences.
  Use when: making architectural decisions, documenting technology choices, recording design trade-offs, onboarding team members.
triggers: ["ADR", "architecture decision", "decision record", "why did we choose", "document decision", "RFC"]
---

# Architecture Decision Records

> Document significant technical decisions with context, rationale, and consequences.

## Core Principles

- **Capture the WHY**: Document rationale, not just the decision
- **Record early**: Write ADRs before implementation, not after
- **Keep it brief**: One page, focused on one decision
- **Immutable history**: Never modify accepted ADRs, create new ones to supersede
- **Living documents**: Keep an index, update statuses

## Quick Reference

| Status | Meaning |
|--------|---------|
| Proposed | Under discussion |
| Accepted | Decision made, being implemented |
| Rejected | Considered but not adopted |
| Deprecated | Was accepted, no longer recommended |
| Superseded | Replaced by another ADR |

## When to Write an ADR

**Significant Decisions:**
- New framework or library adoption
- Database or data store selection
- API design choices (REST vs GraphQL)
- Security architecture decisions
- Breaking changes to existing systems
- Integration patterns between services

**NOT Needed For:**
- Minor version updates
- Bug fixes
- Configuration changes
- Routine refactoring

## Standard Format

```markdown
# ADR-{number}: {Title}

## Status
{Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-XXX}

## Context
{What is the issue? What forces are at play?}

## Decision
{What is the change being proposed/made?}

## Consequences
{What becomes easier or harder because of this decision?}
```

## Decision Checklist

Before accepting an ADR:
- [ ] Is the context clear to someone unfamiliar with the project?
- [ ] Are alternatives documented with trade-offs?
- [ ] Are consequences (positive and negative) listed?
- [ ] Is the decision reversible? What's the cost?
- [ ] Who are the stakeholders? Have they reviewed it?

## When to Load References

- For templates: `Read references/templates.md`
- For examples: `Read references/examples.md`

## External Resources

- [ADR GitHub Organization](https://adr.github.io/)
- [adr-tools CLI](https://github.com/npryce/adr-tools)
