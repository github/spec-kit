# RFC: [TITLE]

**RFC ID**: [TEAM-NNN]
**Status**: Draft
**Author**: [Name]
**Reviewers**: [Names]
**Created**: [DATE]
**Updated**: [DATE]
**Spec Reference**: [Link to spec.md]
**Branch**: `[###-feature-name]`

## Decision Summary

<!--
  2-3 sentences MAX. A reviewer short on time reads ONLY this.
  State the problem in one line, the chosen approach, and the key trade-off.
-->

[We need X because Y. We chose approach A over B because Z.
The main trade-off is ...]

## Background

<!--
  TECHNICAL landscape only: current architecture, prior work, existing systems.
  The spec already covers business context — do not repeat it here.
  1-2 paragraphs. Link to prior work, don't summarize it.
-->

[Technical context, current state of the system, prior work or related efforts]

## Problem

<!--
  Why the CURRENT SYSTEM cannot meet the spec's requirements.
  This is NOT the business problem (that's in the spec).
  1-3 paragraphs. Reference spec requirements (FR-xxx) where relevant.
-->

[Technical problem and why the current system cannot satisfy the spec]

## Proposal

<!--
  The core of the RFC. WHAT technical approach was chosen and WHY.
  Prefer diagrams over prose. Prefer bullets over paragraphs.
  Focus on decisions and trade-offs, not exhaustive implementation detail —
  the plan handles that.
-->

[Proposed technical solution]

### Architecture

<!--
  System design, component interaction, data flow.
  A diagram replaces 500 words of prose — draw it.
-->

```text
[Architecture diagram]
```

### Alternatives Considered

<!--
  MANDATORY. Every alternative must have a verdict.
  If you can't articulate why an alternative was rejected,
  you haven't made a decision yet.
-->

| Alternative | Pros | Cons | Verdict |
|-------------|------|------|---------|
| [Option A — chosen] | ... | ... | **Selected** because ... |
| [Option B] | ... | ... | Rejected because ... |
| [Option C] | ... | ... | Rejected because ... |

## Rollout Strategy

<!--
  OPTIONAL — Include when the change affects production systems.
  How will this be deployed? Feature flags? Phased rollout?
  Migration path from current state?
-->

[Rollout plan, migration steps, feature flags, backward compatibility]

## Metrics & Definition of Success

<!--
  Business metrics come from the spec's success criteria (SC-xxx).
  Technical metrics are specific to this implementation.
-->

### Business Metrics

- [Metric from spec success criteria and how this RFC achieves it]

### Technical Metrics

- [Technical performance, reliability, or operational metrics]

## Known Limitations

<!--
  Bullet list. Compromises, trade-offs, and scope boundaries.
  What does this solution deliberately NOT do?
-->

- [Limitation 1]
- [Limitation 2]

## Dependencies

<!--
  OPTIONAL — Include when there are cross-team or external dependencies.
-->

- [Dependency 1]: [What is needed and from whom]

## Security & Compliance

<!--
  OPTIONAL — Include when the change involves authentication, PII,
  external APIs, or changes to trust boundaries.
-->

[Security implications, PII/GDPR considerations, auth changes]

## Outstanding Questions

<!--
  MAX 5. Every question must be BLOCKING — if it doesn't block
  the decision or implementation, it doesn't belong here.
  Tag questions with owners.
-->

1. [Question] — *Owner: [Name/Team]*
