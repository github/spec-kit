---
description: Create or update feature specification from natural language description.
handoffs: 
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
  - label: Clarify Spec Requirements
    agent: speckit.clarify
    prompt: Clarify specification requirements
    send: true
scripts:
  sh: scripts/bash/create-new-feature.sh "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 "{ARGS}"
---

## Input

```text
$ARGUMENTS
```

Consider user input before proceeding (if not empty).

## Pre-Execution

Check `.specify/extensions.yml` for `hooks.before_specify`. For enabled hooks: run mandatory ones (EXECUTE_COMMAND), show optional ones. Skip silently if file missing/invalid.

## Workflow

1. **Generate branch short name** (2-4 words, action-noun format, e.g. "user-auth", "fix-payment-timeout")

2. **Create feature branch**: Run script with `--short-name` and `--json`. Check `.specify/init-options.json` for `branch_numbering` - add `--timestamp` if "timestamp". Never pass `--number`. Run script only once. Parse BRANCH_NAME and SPEC_FILE from JSON output.

3. **Load** `templates/spec-template.md` for structure.

4. **Generate spec**:
   - Parse feature description, extract actors/actions/data/constraints
   - Make informed guesses for unclear aspects using industry defaults
   - Mark max 3 [NEEDS CLARIFICATION] only for high-impact ambiguities (scope > security > UX > technical)
   - Fill: Scenarios (prioritized user stories with independent tests), Requirements (testable FRs), Success Criteria (measurable, tech-agnostic), Entities (if data involved), Assumptions
   - Write to SPEC_FILE

5. **Validate** against quality checklist at `FEATURE_DIR/checklists/requirements.md`:
   - No implementation details, focused on user value, all mandatory sections complete
   - Requirements testable, success criteria measurable+tech-agnostic, scenarios cover primary flows
   - If items fail: fix and re-validate (max 3 iterations)
   - If [NEEDS CLARIFICATION] remain (max 3): present options table to user, wait for response, update spec

6. **Report** completion with branch, spec path, checklist results, next steps (`/speckit.clarify` or `/speckit.plan`).

7. Check `.specify/extensions.yml` for `hooks.after_specify`. Run mandatory, show optional. Skip silently if missing.

## Rules

- Focus on WHAT users need and WHY - avoid HOW (no tech stack, APIs, code)
- Written for business stakeholders, not developers
- Remove N/A sections entirely
- Success criteria: measurable, tech-agnostic, user-focused, verifiable
