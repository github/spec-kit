# Stage-Specific Prompts for Modernization Workflow

This directory contains **6 stage-specific prompts** that inject legacy code context
into each stage of the Toolkit workflow.

## How to Use These Prompts

After running the analyze-project command, you'll have:

1. `functional-spec.md` - WHAT the legacy system does
2. `technical-spec.md` - HOW to build the new system
3. `stage-prompts/` (this directory) - Guidance for each Toolkit stage

### Workflow Integration

When running each Toolkit stage, **prepend the corresponding stage prompt**
to your input. The prompt provides legacy code context and guidance.

**Example** (specify stage):

```text
Use the requirements from analysis/functional-spec.md section §5 (Functional Requirements).

Focus on CRITICAL features (FR-CRIT-*) for Phase 1:
- FR-CRIT-001: User Authentication (src/auth/login.js:34-89)
- FR-CRIT-002: Payment Processing (src/orders/payment.js:156-234)
- FR-CRIT-003: Audit Logging (src/audit/logger.js:12-34)

For detailed requirements, see functional-spec.md.
```

## Stage Prompts Available

| File | Toolkit Stage | Purpose |
|------|---------------|---------|
| `constitution-prompt.md` | /speckit.constitution | Extract principles from legacy |
| `specify-prompt.md` | /speckit.specify | Map legacy features to requirements |
| `plan-prompt.md` | /speckit.plan | Design architecture based on target stack |
| `clarify-prompt.md` | /speckit.clarify | Use legacy code as source of truth |
| `tasks-prompt.md` | /speckit.tasks | Break down with legacy complexity |
| `implement-prompt.md` | /speckit.implement | Reference legacy code during implementation |

## Key Principle: "Legacy Code as Source of Truth"

For `clarify` and `implement` stages, the prompts include explicit instruction:

> **Consult legacy app <<path>> as the source of truth if the specification
> is underspecified, ambiguous, or requires further clarification.**

This prevents hallucination and ensures accurate modernization.

## Auto-Generated Content

Each stage prompt is **auto-generated** during the analyze-project workflow.
They contain:

- **Legacy Code References**: Actual file paths and line numbers
- **Critical Behaviors**: Must-preserve functionality
- **Modernization Guidance**: Target stack context
- **Ready-to-Paste**: Copy into Toolkit stage input

## Manual Editing

You can edit these prompts before using them if needed. They are Markdown files
generated from templates + AI analysis.
