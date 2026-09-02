---
description: "Compose multiple evaluator results at a lifecycle point with deterministic precedence"
scripts:
  sh: ../../scripts/bash/compose-results.sh
  ps: ../../scripts/powershell/compose-results.ps1
  py: ../../scripts/python/compose_results.py
---

# Evaluator Compose

Compose multiple independent evaluator results at a single lifecycle point into one aggregate result with deterministic precedence.

When multiple evaluators run at the same phase (e.g., a schema validator, a security scanner, and an epistemic checker all after `plan`), their results must be composed into a single actionable verdict. This command applies deterministic composition rules so the outcome is reproducible.

## User Input

```text
$ARGUMENTS
```

The user input specifies **which results to compose**. Accept:

1. **Phase** — the lifecycle phase to compose results for (e.g., `phase=after_plan`). Required.
2. **Result files** — explicit list of result file paths. If not provided, discover all result files for the given phase from `.specify/extensions/evaluator/results/`.
3. **Composition strategy** — `strict` (default), `majority`, or `optimistic`. See Composition Strategies below.

## Prerequisites

- **Path safety (do this before any read or write)**: resolve the project root and the real, symlink-resolved path of `.specify/extensions/evaluator/results/` and every result file you touch. **Refuse and report — never follow —** if any path component is a symlink, or if the resolved path does not remain inside the project root.
- At least one result file MUST exist for the specified phase. If none exist, produce a composed result with `outcome: "pass"` and a note that no evaluators ran.
- Each result file MUST be valid JSON conforming to the evaluator result schema. Skip and report invalid files; do not compose invalid data.

## Execution

### 1. Collect Results

Read all result files for the specified phase from `.specify/extensions/evaluator/results/`. Filter to files matching the pattern `<evaluator-id>-<phase>-<timestamp>.json`.

### 2. Validate Each Result

For each result file:
1. Parse as JSON.
2. Validate against `.specify/extensions/evaluator/schemas/evaluator-result.schema.json`.
3. Skip invalid results and report them.

### 3. Apply Composition Strategy

#### `strict` (default)

The most severe outcome wins. Precedence order (most severe first):

1. `block` — any evaluator blocks → composed outcome is `block`
2. `gather_evidence` — any evaluator needs evidence → `gather_evidence`
3. `iterate` — any evaluator requests iteration → `iterate`
4. `clarify` — any evaluator needs clarification → `clarify`
5. `warn` — any evaluator warns → `warn`
6. `pass` — all evaluators pass → `pass`

#### `majority`

The outcome with the most evaluators supporting it wins. Ties break toward the more severe outcome (using strict precedence).

#### `optimistic`

The least severe outcome wins. Use only when evaluators are advisory and blocking is explicitly not desired.

### 4. Merge Findings

All findings from all evaluators are preserved in the composed result. Each finding retains its original `id`, `evaluator` origin, and all fields. Findings are ordered by:

1. Severity (critical → high → medium → low → info)
2. Evaluator priority (lower first)
3. Original finding order within each evaluator

Contradictory findings are **preserved, not collapsed**. If evaluator A says "REQ-014 is supported" and evaluator B says "REQ-014 is unsupported", both findings appear in the composed result with their respective evidence.

### 5. Determine Next Action

The composed `next_action` is derived from the composed outcome:

| Composed Outcome | Next Action Kind | Target Phase |
|-----------------|-----------------|--------------|
| `pass` | `pass` | null |
| `warn` | `warn` | null |
| `iterate` | `iterate` | Most common `target_phase` among iterate findings |
| `clarify` | `clarify` | null |
| `gather_evidence` | `gather_evidence` | null |
| `block` | `block` | null |

### 6. Write Composed Result

Write to `.specify/extensions/evaluator/results/composed-<phase>-<timestamp>.json`.

### 7. Report

Output a summary:
- The phase
- The composition strategy used
- The number of evaluator results composed
- The composed outcome
- Total findings by severity
- Any contradictory findings flagged
- The recommended next action
- The path to the composed result file

## Composition Rules

1. **Deterministic**: same inputs + same strategy = same composed result.
2. **Contradiction-preserving**: conflicting findings are both recorded, not resolved.
3. **Evidence-respecting**: `observed` evidence from one evaluator is not downgraded by another evaluator's `asserted` claim.
4. **State-isolated**: each evaluator's `state` object is preserved under its evaluator ID in the composed result's `evaluator_states` map.
5. **Priority-ordered**: when evaluators declare a `priority` (in their config), lower values run first and their findings appear first at equal severity.

## Composed Result Format

```json
{
  "schema_version": "1.0",
  "composed": true,
  "phase": "after_plan",
  "composition_strategy": "strict",
  "composed_outcome": "iterate",
  "composed_summary": "2 evaluators ran: 1 pass, 1 iterate. 3 findings total.",
  "evaluator_results": [
    { "evaluator_id": "schema-validate", "outcome": "pass", "findings_count": 0 },
    { "evaluator_id": "epistemic", "outcome": "iterate", "findings_count": 3 }
  ],
  "findings": [
    "... all findings from all evaluators, ordered by severity ..."
  ],
  "next_action": {
    "kind": "iterate",
    "target_phase": "plan",
    "message": "2 of 2 evaluators completed. 1 requests iteration. See findings for details."
  },
  "evaluator_states": {
    "schema-validate": {},
    "epistemic": { "... opaque evaluator state ..." }
  },
  "metadata": {
    "timestamp": "<ISO-8601>",
    "evaluator_count": 2,
    "contradictory_findings": [
      { "finding_a": "EPI-001", "finding_b": "SCH-003", "subject": "REQ-014" }
    ]
  }
}
```

## Guardrails

- Never modify individual evaluator result files — compose reads them, writes a new composed file.
- Never resolve contradictions by dropping findings — preserve both.
- Never change another evaluator's evidence classification.
- Never merge `state` objects across evaluators — keep them isolated under evaluator IDs.
- The composed result is a new artifact; it does not replace individual evaluator results.
