---
description: "Shape a concept: solution options, scope, appetite, and trade-offs (no implementation design)"
---

# Shape a Concept

Take the defined problem and shape a **concept** at `.specify/assessments/<slug>/concept.md`: the rough solution options, the scope/appetite, and the trade-offs between them. This is where the assessment crosses from problem space into solution space — but only at the *concept* level. Detailed design (architecture, data models, APIs, tasks) stays with `__SPECKIT_COMMAND_SPECIFY__` and the rest of the SDD lifecycle.

Shape **outlines options at the boundaries; it does not produce a spec or a plan.** Think Shape Up "pitch," not blueprint.

## User Input

```text
$ARGUMENTS
```

Resolve the slug: explicit `slug=…` → conversation context (a slug reported earlier this session, confirmed by an existing `.specify/assessments/<slug>/` directory) → ask (interactive) → single existing directory (automated) → otherwise stop and ask. Set `ASSESS_SLUG` and `ASSESS_DIR = .specify/assessments/<ASSESS_SLUG>`.

## Prerequisites

- `ASSESS_DIR/problem.md` **MUST** exist. If it does not, stop and instruct the user to run `__SPECKIT_COMMAND_ASSESS_DEFINE__` first — shaping without a defined problem invites solutionizing in a vacuum.
- Read `ASSESS_DIR/problem.md`, and `research.md`/`intake.md` if present, so options address the stated goals, respect the non-goals, and are grounded in evidence.
- If `ASSESS_DIR/concept.md` already exists, ask whether to overwrite (interactive); in automated mode, refuse.

## Execution

1. **Generate 2–3 distinct options**, spanning the trade-off space. Always include a lightweight "smallest thing that could work" option and, where relevant, a "do nothing / buy instead of build" option. Each option:
   - **Sketch**: one paragraph describing the approach at concept level (what the user experiences / what changes), not how it is engineered.
   - **Appetite**: a rough size — `small` (days) | `medium` (weeks) | `large` (months) — as a budget, not an estimate.
   - **Trade-offs**: what it wins and what it sacrifices; key risks and unknowns.
   - **Rabbit holes**: the parts most likely to blow up scope, so `__SPECKIT_COMMAND_ASSESS_DECIDE__` sees them.
2. **Recommend one option** with a short rationale tied to the problem's goals and metrics — or explicitly recommend *not proceeding* if no option clears the bar.
3. **Bound the concept**: restate what is explicitly out of scope for the recommended option (inherited from non-goals plus anything newly excluded).
4. **List the assumptions** the recommendation depends on, so they can be validated during specification.

Write `ASSESS_DIR/concept.md`:

```markdown
# Concept: <short title>

- **Slug**: <ASSESS_SLUG>
- **Created**: <ISO 8601 date>
- **Recommended option**: <name> | none

## Options

### Option A — <name>
- **Sketch**: <concept-level description>
- **Appetite**: small | medium | large
- **Trade-offs**: <wins vs. sacrifices, risks>
- **Rabbit holes**: <scope-blowout risks>

### Option B — <name>
...

### Option C — <name> (optional)
...

## Recommendation

<Which option, and why — tied to goals and success metrics. Or: recommend not proceeding, with reason.>

## Out of Scope (for the recommended option)

- <excluded>

## Assumptions to Validate

- <assumption the recommendation depends on>
```

**Report back** with the slug (own line), the path to `concept.md`, the recommended option (or "none"), and the next step: `__SPECKIT_COMMAND_ASSESS_DECIDE__ slug=<ASSESS_SLUG>`.

## Guardrails

- Never modify source files — read only, and write inside `.specify/assessments/<slug>/`.
- Never produce a specification, architecture, data model, API design, or task breakdown — options stay at concept level. That work belongs to `__SPECKIT_COMMAND_SPECIFY__` onward.
- Never invent an appetite the evidence cannot support — mark uncertainty plainly.
- Never overwrite an existing `concept.md` without confirmation.
- It is a valid outcome to recommend that **no** option is worth building; say so rather than manufacturing a winner.
