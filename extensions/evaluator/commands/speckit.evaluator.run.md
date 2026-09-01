---
description: "Run an evaluator against one or more artifacts and produce a versioned machine-readable result conforming to the evaluator result contract"
scripts:
  sh: ../../scripts/bash/compose-results.sh
  ps: ../../scripts/powershell/compose-results.ps1
  py: ../../scripts/python/compose_results.py
---

# Evaluator Run

Execute an evaluator against specified artifacts and produce a result conforming to the **evaluator result contract** defined in `.specify/extensions/evaluator/schemas/evaluator-result.schema.json`.

This command is the execution entry point for any evaluator — deterministic linters, model-backed reviewers, security scanners, policy checkers, provenance verifiers, or custom governance checks. The evaluator receives artifact references and returns a versioned, machine-readable result that downstream composition and reporting can consume.

## User Input

```text
$ARGUMENTS
```

The user input specifies **what to evaluate** and **which evaluator(s) to run**. Accept:

1. **Phase context** — the lifecycle phase this evaluation runs under (e.g., `phase=after_plan`). If not provided, infer from the hook event or ask.
2. **Artifact references** — one or more artifact paths to evaluate (e.g., `spec.md`, `plan.md`, `tasks.md`). If not provided, discover artifacts for the current phase from `.specify/` and the feature directory.
3. **Evaluator selection** — which evaluator(s) to run. If not provided, discover registered evaluators from `.specify/extensions/evaluator/` config.

## Prerequisites

- **Path safety (do this before any read or write)**: resolve the project root and the real, symlink-resolved path of `.specify/extensions/evaluator/` and every artifact you touch. **Refuse and report — never follow —** if any path component is a symlink, or if the resolved path does not remain inside the project root.
- The evaluator result schema MUST exist at `.specify/extensions/evaluator/schemas/evaluator-result.schema.json`. If missing, report the path and instruct the user to reinstall the evaluator extension.
- Each artifact to evaluate MUST exist and be readable. Report missing artifacts; do not fabricate evaluations for absent files.

## Execution

### 1. Load the Evaluator Contract

Read the schema from `.specify/extensions/evaluator/schemas/evaluator-result.schema.json`. Every result produced MUST validate against this schema.

### 2. Discover Evaluators

Look for evaluator configurations in `.specify/extensions/evaluator/`. An evaluator is any extension that declares it produces evaluator results. Discovery order:

1. Check `.specify/extensions/evaluator/evaluators.yml` for a list of registered evaluator IDs.
2. For each registered evaluator, locate its configuration.
3. If no evaluators are registered, produce a single result with `outcome: "pass"` and a note that no evaluators are configured.

### 3. Run Each Evaluator

For each discovered evaluator, in priority order (lower `priority` value first, default 10):

1. **Deterministic evaluators first**: run deterministic checks (schema validation, linting, static analysis) before model-backed evaluators.
2. **Invoke the evaluator** with the artifact references.
3. **Collect the result** — it MUST be valid JSON conforming to the evaluator result schema.
4. **Validate the result** against the schema. If validation fails, wrap the raw output in an error finding and set `outcome: "block"`.

### 4. Produce the Result

Write the result to `.specify/extensions/evaluator/results/<evaluator-id>-<phase>-<timestamp>.json`.

Each result file MUST contain exactly one evaluator result object. The filename pattern is:

```
<evaluator-id>-<phase>-<ISO8601-basic-timestamp>.json
```

Example: `epistemic-after_plan-20260715T143022Z.json`

### 5. Report

Output a summary to the user:

- The evaluator ID and version
- The phase evaluated
- The outcome (`pass`, `warn`, `iterate`, `clarify`, `gather_evidence`, `block`)
- The number of findings by severity
- The recommended next action
- The path to the result file

## Evaluator Result Contract

Every result MUST conform to this structure (see the schema for full details):

```json
{
  "schema_version": "1.0",
  "evaluator": {
    "id": "<unique-id>",
    "version": "<semver>"
  },
  "phase": "<lifecycle-phase>",
  "outcome": "pass|warn|iterate|clarify|gather_evidence|block",
  "summary": "<one-paragraph summary>",
  "findings": [
    {
      "id": "<finding-id>",
      "severity": "critical|high|medium|low|info",
      "kind": "<finding-kind>",
      "subject": "<artifact-reference>",
      "evidence_refs": [
        {
          "ref": "<reference>",
          "kind": "observed|inferred|asserted|contradicted|unsupported"
        }
      ],
      "provenance_refs": ["<artifact>#<element>"],
      "uncertainty": "none|low|medium|high|insufficient_evidence",
      "recommended_action": "none|gather_evidence|clarify|revise|iterate|escalate|accept_risk|block"
    }
  ],
  "next_action": {
    "kind": "pass|warn|iterate|clarify|gather_evidence|block",
    "target_phase": "<phase-to-iterate-to>",
    "message": "<human-readable>"
  },
  "metadata": {
    "timestamp": "<ISO-8601>",
    "duration_ms": 0,
    "artifacts_evaluated": ["<path>"],
    "deterministic": true
  },
  "state": {}
}
```

### Outcome Semantics

| Outcome | Meaning | Workflow Effect |
|---------|---------|----------------|
| `pass` | All checks passed; no issues found | Continue to next phase |
| `warn` | Issues found but not blocking | Continue with warnings recorded |
| `iterate` | Issues require revisiting a prior phase | Return to `target_phase` |
| `clarify` | Ambiguities need human resolution | Pause for human input |
| `gather_evidence` | Insufficient evidence to decide | Pause for evidence collection |
| `block` | Hard blocker; cannot proceed | Stop the workflow |

### Evidence Kinds

| Kind | Meaning |
|------|---------|
| `observed` | Directly observed from an artifact or command output |
| `inferred` | Logically derived from observed evidence |
| `asserted` | Claimed by a model or agent without direct observation |
| `contradicted` | Conflicts with other observed evidence |
| `unsupported` | No evidence found to support or refute |

### Key Design Rules

1. **Generated assertions MUST remain distinguishable from observed evidence.** A model saying "the test passed" is `asserted`; a command exit code 0 with captured stdout is `observed`.
2. **Model self-attestation MUST NOT satisfy an evidence gate by itself.** An evaluator cannot certify its own output as evidence.
3. **Contradictions MUST be preserved**, not collapsed into a single synthesized answer. Conflicting findings from different evaluators are both recorded.
4. **Insufficient evidence MUST be represented explicitly** (`uncertainty: "insufficient_evidence"`) rather than inventing certainty.
5. **Deterministic checks SHOULD run before probabilistic review** where appropriate.
6. **Higher-risk work MAY require evaluator independence** — the same model/family SHOULD NOT both generate and certify the result.

## Guardrails

- Never modify source files — write only under `.specify/extensions/evaluator/results/`.
- Never treat a model-generated assertion as observed evidence — always classify it as `asserted`.
- Never collapse contradictory findings — preserve both and let composition resolve.
- Never fabricate evidence references — if no evidence exists, mark it `unsupported`.
- Never overwrite an existing result file without confirmation (interactive) or appending a disambiguating suffix (automated).
- The `state` object is evaluator-defined opaque data for pause/resume — do not interpret or modify another evaluator's state.
