# ADR Templates

> Choose the template that fits your team's needs.

## 1. MADR Format (Comprehensive)

Best for significant decisions requiring detailed analysis.

```markdown
# ADR-{number}: {Title}

## Status

{Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-XXX}

Date: YYYY-MM-DD

## Context and Problem Statement

{Describe the context and problem in 2-3 sentences}

## Decision Drivers

* {Driver 1, e.g., "Need to reduce latency by 50%"}
* {Driver 2, e.g., "Must support 10k concurrent users"}
* {Driver 3, e.g., "Team has expertise in Python"}

## Considered Options

1. {Option 1}
2. {Option 2}
3. {Option 3}

## Decision Outcome

Chosen option: "{Option X}", because {justification}.

### Positive Consequences

* {Positive consequence 1}
* {Positive consequence 2}

### Negative Consequences

* {Negative consequence 1}
* {Mitigation strategy if any}

## Pros and Cons of the Options

### {Option 1}

* Good, because {argument}
* Good, because {argument}
* Bad, because {argument}
* Bad, because {argument}

### {Option 2}

* Good, because {argument}
* Bad, because {argument}

### {Option 3}

* Good, because {argument}
* Bad, because {argument}

## Links

* {Link to related ADR or document}
* {Link to relevant discussion}
```

## 2. Lightweight Format

For simpler decisions or faster documentation.

```markdown
# ADR-{number}: {Title}

**Status:** {Status}
**Date:** YYYY-MM-DD
**Deciders:** {Names or roles}

## Context

{Brief context in 1-2 paragraphs}

## Decision

We will {decision}.

## Rationale

{Why this decision was made, 2-3 bullet points}

## Consequences

{What follows from this decision, both positive and negative}
```

## 3. Y-Statement Format

For very brief, inline documentation.

```markdown
# ADR-{number}: {Title}

In the context of {context},
facing {concern/challenge},
we decided {decision}
to achieve {goal},
accepting {trade-off/downside}.
```

**Example:**
> In the context of user authentication,
> facing the need for third-party login support,
> we decided to use Auth0
> to achieve faster implementation and better security,
> accepting vendor lock-in and monthly costs.

## 4. Deprecation Template

For retiring outdated decisions.

```markdown
# ADR-{number}: Deprecate {Original Decision}

## Status

Deprecated

Date: YYYY-MM-DD
Deprecates: ADR-{original}
Superseded by: ADR-{new} (if applicable)

## Context

{Why is the original decision being deprecated?}

## Decision

ADR-{original} is deprecated because:
* {Reason 1}
* {Reason 2}

## Migration Path

{How to migrate from old to new approach}

## Timeline

* Deprecation announced: YYYY-MM-DD
* New approach available: YYYY-MM-DD
* Migration deadline: YYYY-MM-DD
* Old approach removed: YYYY-MM-DD
```

## 5. RFC Style (For Larger Changes)

For significant changes requiring broader input.

```markdown
# RFC-{number}: {Title}

## Summary

{One paragraph summary}

## Motivation

{Why is this change needed? What problem does it solve?}

## Detailed Design

{Technical details of the proposed change}

### API Changes

{If applicable}

### Data Model Changes

{If applicable}

### Migration Strategy

{How to roll out the change}

## Drawbacks

{Why should we NOT do this?}

## Alternatives

{What other designs were considered?}

## Unresolved Questions

{What parts of the design are still TBD?}

## Implementation Plan

1. {Phase 1}
2. {Phase 2}
3. {Phase 3}
```

## Directory Structure

```
docs/
└── adr/
    ├── README.md           # Index of all ADRs
    ├── adr-0001-record-architecture-decisions.md
    ├── adr-0002-use-postgresql-for-persistence.md
    ├── adr-0003-adopt-event-sourcing.md
    └── templates/
        ├── madr-template.md
        └── lightweight-template.md
```

## ADR Index Template (README.md)

```markdown
# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for {Project Name}.

## Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-0001](adr-0001-record-architecture-decisions.md) | Record Architecture Decisions | Accepted | 2024-01-15 |
| [ADR-0002](adr-0002-use-postgresql.md) | Use PostgreSQL for Persistence | Accepted | 2024-01-20 |
| [ADR-0003](adr-0003-event-sourcing.md) | Adopt Event Sourcing | Proposed | 2024-02-01 |

## Process

1. Copy the appropriate template
2. Fill in all sections
3. Submit PR for review
4. Get approval from {reviewers}
5. Merge and update index
```
