# Evaluator Contract Extension

Standard evaluator result contract for evidence, provenance, uncertainty, and recovery — a provider-neutral protocol for extensions that evaluate artifact quality between Spec-Driven Development phases.

## Overview

Spec Kit has a strong lifecycle and extensible hook system, but there is no common contract for extensions that evaluate the quality or trustworthiness of artifacts between phases. This extension defines that contract.

The evaluator contract lets any extension:

1. **Register** for one or more lifecycle events via hooks
2. **Receive** the relevant resolved artifacts plus stable source/provenance references
3. **Return** a versioned machine-readable result conforming to a shared schema
4. **Distinguish** observed evidence from generated assertions
5. **Preserve** contradictory findings instead of forcing false consensus
6. **Represent** insufficient evidence or unresolved uncertainty explicitly
7. **Request** a bounded next action: `pass`, `warn`, `iterate`, `clarify`, `gather_evidence`, or `block`
8. **Persist** enough compact state to survive pause/resume
9. **Compose** deterministically with other evaluators
10. **Remain** implementation-neutral: deterministic, model-backed, local, remote, private, paid, or hybrid

## Installation

```bash
specify extension add evaluator
```

Or for local development:

```bash
specify extension add --dev /path/to/spec-kit/extensions/evaluator
```

## Commands

### `/speckit.evaluator.run`

Run an evaluator against one or more artifacts and produce a versioned machine-readable result.

```bash
/speckit.evaluator.run phase=after_plan artifacts=spec.md,plan.md
```

Results are written to `.specify/extensions/evaluator/results/<evaluator-id>-<phase>-<timestamp>.json`.

### `/speckit.evaluator.compose`

Compose multiple evaluator results at a lifecycle point with deterministic precedence.

```bash
/speckit.evaluator.compose phase=after_plan strategy=strict
```

Composed results are written to `.specify/extensions/evaluator/results/composed-<phase>-<timestamp>.json`.

### `/speckit.evaluator.report`

Render evaluator results as a human-readable report, CI annotation, or release gate.

```bash
/speckit.evaluator.report phase=after_plan format=terminal
/speckit.evaluator.report phase=after_plan format=ci-annotation
/speckit.evaluator.report phase=after_plan format=gate
```

## Evaluator Result Schema

The full JSON Schema is at `schemas/evaluator-result.schema.json`. Every evaluator result MUST conform to this schema.

### Minimal Valid Result

```json
{
  "schema_version": "1.0",
  "evaluator": {
    "id": "my-evaluator",
    "version": "0.1.0"
  },
  "phase": "after_plan",
  "outcome": "pass",
  "findings": []
}
```

### Outcome Semantics

| Outcome | Meaning | Workflow Effect |
|---------|---------|----------------|
| `pass` | All checks passed | Continue to next phase |
| `warn` | Issues found but not blocking | Continue with warnings |
| `iterate` | Issues require revisiting a prior phase | Return to target phase |
| `clarify` | Ambiguities need human resolution | Pause for human input |
| `gather_evidence` | Insufficient evidence | Pause for evidence collection |
| `block` | Hard blocker | Stop the workflow |

### Evidence Kinds

| Kind | Meaning |
|------|---------|
| `observed` | Directly observed from an artifact or command output |
| `inferred` | Logically derived from observed evidence |
| `asserted` | Claimed by a model or agent without direct observation |
| `contradicted` | Conflicts with other observed evidence |
| `unsupported` | No evidence found to support or refute |

## Composition Strategies

When multiple evaluators run at the same phase, their results are composed:

| Strategy | Behavior |
|----------|----------|
| `strict` (default) | Most severe outcome wins |
| `majority` | Most common outcome wins; ties break toward severity |
| `optimistic` | Least severe outcome wins |

## Hooks

The extension registers hooks at key lifecycle points:

- `after_specify` — Evaluate spec quality, evidence, and provenance
- `after_plan` — Evaluate plan assumptions, risks, and coverage
- `after_tasks` — Evaluate task completeness and traceability
- `after_implement` — Evaluate implementation against spec, plan, and tasks

All hooks are optional (prompt before executing) with priority 20.

## Writing an Evaluator

To write an evaluator that conforms to this contract:

1. Create an extension that depends on `evaluator`
2. Register hooks at the lifecycle points you want to evaluate
3. In your command, read the relevant artifacts
4. Produce a result JSON file conforming to `evaluator-result.schema.json`
5. Write it to `.specify/extensions/evaluator/results/`

See `templates/evaluator-result-template.json` for a starting point.

## Design Rules

1. **Generated assertions MUST remain distinguishable from observed evidence.**
2. **Model self-attestation MUST NOT satisfy an evidence gate by itself.**
3. **Contradictions MUST be preserved**, not collapsed into a single synthesized answer.
4. **Insufficient evidence MUST be represented explicitly** rather than inventing certainty.
5. **Deterministic checks SHOULD run before probabilistic review** where appropriate.
6. **Higher-risk work MAY require evaluator independence** — the same model/family SHOULD NOT both generate and certify the result.

## File Structure

```
.specify/extensions/evaluator/
├── schemas/
│   └── evaluator-result.schema.json   # JSON Schema for evaluator results
├── templates/
│   └── evaluator-result-template.json # Template for new evaluator results
├── results/                            # Individual evaluator result files
│   ├── <evaluator-id>-<phase>-<ts>.json
│   └── composed-<phase>-<ts>.json
├── reports/                            # Human-readable reports (markdown format)
│   └── report-<phase>-<ts>.md
└── evaluators.yml                      # Registered evaluator configuration
```

## License

MIT — see the [Spec Kit license](../../LICENSE).
