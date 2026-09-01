---
description: "Render evaluator results as a human-readable report, CI annotation, or release gate"
---

# Evaluator Report

Render evaluator results (individual or composed) into a human-readable report, CI annotation, or release gate decision.

This command consumes evaluator result JSON files and produces output suitable for different consumers: developers reading in-terminal, CI systems parsing annotations, or release pipelines checking gates.

## User Input

```text
$ARGUMENTS
```

The user input specifies **what to report** and **how**. Accept:

1. **Result files** — one or more evaluator result file paths, or a composed result path. If not provided, discover the latest composed result for the current phase, or the latest individual results.
2. **Format** — `terminal` (default), `markdown`, `json`, `ci-annotation`, or `gate`. See Output Formats below.
3. **Phase** — filter results to a specific phase.
4. **Severity threshold** — only show findings at or above this severity (`critical`, `high`, `medium`, `low`, `info`). Default: `low`.

## Prerequisites

- **Path safety (do this before any read or write)**: resolve the project root and the real, symlink-resolved path of `.specify/extensions/evaluator/results/` and every result file you touch. **Refuse and report — never follow —** if any path component is a symlink, or if the resolved path does not remain inside the project root.
- At least one result file MUST exist. If none exist, report "No evaluator results found" and exit.

## Execution

### 1. Load Results

Read the specified result files (or discover them). Each must be valid JSON conforming to the evaluator result schema.

### 2. Filter Findings

Apply the severity threshold. Findings below the threshold are excluded from the report but counted in the summary.

### 3. Render in Requested Format

#### `terminal` (default)

A color-coded terminal report:

```
═══════════════════════════════════════════════════════════
  EVALUATOR REPORT — after_plan
═══════════════════════════════════════════════════════════
  Outcome:  ITERATE
  Evaluators: 2 run, 1 passed, 1 requests iteration
  Findings: 3 total (0 critical, 2 high, 1 medium)
───────────────────────────────────────────────────────────

  [HIGH] EPI-001 — unsupported_claim
  Subject: REQ-014
  Evidence: none (unsupported)
  Recommendation: gather_evidence
  Rationale: Claim presented as fact without supporting evidence.

  [HIGH] EPI-002 — contradiction
  Subject: REQ-007
  Evidence: spec.md#REQ-007 (observed), constitution.md (observed)
  Recommendation: clarify
  Rationale: Requirement conflicts with constitution article IV.

  [MEDIUM] EPI-003 — ambiguous_requirement
  Subject: REQ-022
  Recommendation: clarify
  Rationale: Requirement uses undefined term "scalable".

───────────────────────────────────────────────────────────
  Next Action: iterate → plan
  "2 of 2 evaluators completed. 1 requests iteration."
═══════════════════════════════════════════════════════════
```

#### `markdown`

A Markdown document written to `.specify/extensions/evaluator/reports/report-<phase>-<timestamp>.md`. Suitable for PR comments, issue bodies, or documentation.

#### `json`

The raw JSON result(s) printed to stdout. Suitable for piping to other tools.

#### `ci-annotation`

GitHub Actions workflow commands (`::warning::`, `::error::`) or GitLab CI annotations emitted to stdout. Format:

```
::error file=spec.md,line=14,title=EPI-001::[unsupported_claim] Claim presented as fact without supporting evidence
::warning file=plan.md,line=42,title=EPI-003::[ambiguous_requirement] Requirement uses undefined term "scalable"
```

Findings with severity `critical` or `high` use `::error::`; `medium` and below use `::warning::`.

#### `gate`

A release-gate decision. Exit code 0 if the composed outcome is `pass` or `warn`; exit code 1 for `iterate`, `clarify`, or `gather_evidence`; exit code 2 for `block`. Prints the outcome and summary to stdout.

### 4. Write Report (markdown format only)

For `markdown` format, write the report to `.specify/extensions/evaluator/reports/report-<phase>-<timestamp>.md`.

## Output Formats Summary

| Format | Output | Use Case |
|--------|--------|----------|
| `terminal` | Color-coded stdout | Developer review in terminal |
| `markdown` | File + stdout path | PR comments, documentation |
| `json` | Raw JSON stdout | Piping to other tools |
| `ci-annotation` | Workflow commands stdout | CI/CD pipeline annotations |
| `gate` | Exit code + stdout | Release gates, pre-commit hooks |

## Guardrails

- Never modify result files — report reads them only.
- Never fabricate or summarize away findings — the report reflects exactly what the evaluators produced.
- For `ci-annotation` format, ensure file paths and line numbers are accurate — do not guess.
- For `gate` format, the exit code MUST be deterministic given the same input results.
- Reports are written under `.specify/extensions/evaluator/reports/` — never outside this directory.
