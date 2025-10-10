# ADR-{{ID}}: {{TITLE}}

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Proposed | Accepted | Superseded | Rejected
- **Date:** {{DATE_ISO}}
- **Feature:** {{FEATURE_NAME}}
- **Context:** {{CONTEXT}}

<!-- Significance checklist (ALL must be true to justify this ADR)
     1) Impact: Long-term consequence for architecture/platform/security?
     2) Alternatives: Multiple viable options considered with tradeoffs?
     3) Scope: Cross-cutting concern (not an isolated detail)?
     If any are false, prefer capturing as a PHR note instead of an ADR. -->

## Decision

{{DECISION}}

<!-- For technology stacks, list all components:
     - Framework: Next.js 14 (App Router)
     - Styling: Tailwind CSS v3
     - Deployment: Vercel
     - State Management: React Context (start simple)
-->

## Consequences

### Positive

{{POSITIVE_CONSEQUENCES}}

<!-- Example: Integrated tooling, excellent DX, fast deploys, strong TypeScript support -->

### Negative

{{NEGATIVE_CONSEQUENCES}}

<!-- Example: Vendor lock-in to Vercel, framework coupling, learning curve -->

## Alternatives Considered

{{ALTERNATIVES}}

<!-- Group alternatives by cluster:
     Alternative Stack A: Remix + styled-components + Cloudflare
     Alternative Stack B: Vite + vanilla CSS + AWS Amplify
     Why rejected: Less integrated, more setup complexity
-->

## References

- Feature Spec: {{SPEC_LINK}}
- Implementation Plan: {{PLAN_LINK}}
- Related ADRs: {{RELATED_ADRS}}
- Evaluator Evidence: {{EVAL_NOTES_LINK}} <!-- link to eval notes/PHR showing graders and outcomes -->
