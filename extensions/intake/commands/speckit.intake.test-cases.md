---
description: Capture test-case intake for the active Spec Kit feature.
---

## User Input

```text
$ARGUMENTS
```

Classify the input before proceeding:

- `source`: test files, test management exports, QA spreadsheets, Gherkin feature files, issue links, or bug repros
- `intake_dir`: existing test-case intake artifact directory
- `validation_request`: validate, check, gate, or readiness request
- `review_guidance`: execution scope, framework/export format, source precedence, or reviewer instructions

## Goal

Create, update, or validate test-case intake artifacts for the active Spec Kit feature. Intake preserves reachable test sources, stable source refs, checksums or retrieval metadata, and schema-required behavioral evidence so downstream SDD workflows can project scenarios, assertions, fixtures, and coverage gaps without treating tests as the only source of truth.

Default output directory:

```text
specs/<feature>/intake/test-cases/
```

Normative authority:

- `templates/schemas/*.json` defines machine-readable structure, required fields, types, and enums.
- `scripts/python/validate_test_cases_intake.py` defines readiness evaluation and blocker emission.
- `templates/intake-test-cases-contract.md` defines semantic extraction policy and source-domain terminology.
- This command only performs input routing, context loading, capture orchestration, validation invocation, and reporting.

## Operating Boundaries

- Preserve original test sources and record checksums, stable links, or export metadata before extraction.
- Treat tests as behavioral evidence, not as the sole product source of truth.
- Extract scenarios, assertions, fixtures, and coverage signals without inventing downstream-owned requirement IDs or implementation tasks.
- Keep skipped, flaky, obsolete, contradictory, or missing behavior explicit.
- Do not mark intake ready unless source integrity, traceability, scenario extraction, assertion capture, and gap reporting pass.
- Do not modify application source, tests, package manifests, feature implementation files, or existing Spec Kit core templates.

## Context Loading

1. Verify the current directory is a Spec Kit project by checking for `.specify/`.
2. Identify the active feature:
   - Prefer `SPECIFY_FEATURE` when set.
   - Otherwise use the current Git branch name when it matches a directory under `specs/`.
   - Otherwise inspect `specs/` and choose the most recent feature directory only if there is a single clear candidate.
   - If the feature cannot be identified, stop and ask the user to set `SPECIFY_FEATURE` or run from the feature branch.
3. Read `.specify/extensions/intake/intake-config.yml` when present.
4. Read `templates/intake-test-cases-contract.md` and the referenced JSON Schemas from this extension before creating or validating artifacts.
5. Read any existing test-case intake artifacts and preserve valid evidence unless the user explicitly asks to recapture it.

## Mode Routing

- Capture mode: use when `$ARGUMENTS` names test files, a Gherkin feature, QA spreadsheet, test management export, issue link, framework, suite scope, or asks to capture, ingest, update, or recapture test evidence.
- Validate mode: use when `$ARGUMENTS` includes `validate`, `check`, `gate`, `readiness`, or only names an existing test-case intake directory.
- Capture then validate: use when both a source and validation intent are present, or after capture artifacts are updated.

## Capture Procedure

1. Resolve test sources, framework or export format, feature scope, and execution context.
2. Preserve source identity and checksums in `source-manifest.yaml`.
3. Classify source-domain scenario coverage using `templates/intake-test-cases-contract.md`; do not define additional scenario categories in this command.
4. Extract source-backed facts into `test-case-intake.yaml` according to `templates/schemas/test-case-intake.schema.json` and the semantic policies in `templates/intake-test-cases-contract.md`.
5. For unavailable required evidence, record a structured gap or blocker instead of omitting the field.
6. Record skipped tests, flaky cases, obsolete coverage, missing assertions, and product-intent inference as explicit gaps.
7. Create `evidence-packet.md` from `templates/intake-test-cases-evidence-packet-template.md` with readiness front matter and human-readable evidence notes; keep structured records in `test-case-intake.yaml`.

## Validation Procedure

1. Resolve the test-case intake directory from `$ARGUMENTS` or the active feature.
2. Run:

```bash
python .specify/extensions/intake/scripts/python/validate_test_cases_intake.py <intake-dir>
```

3. Prefer `--json` when a machine-readable result is needed. Report the validator result exactly:
   - `PASS` means the test-case artifacts passed JSON Schema structure checks and are ready for downstream projection as traceable behavioral input.
   - `BLOCKED` means downstream workflows must keep test-derived scenarios blocked, unresolved, or marked `[NEEDS CLARIFICATION]` instead of promoting unsupported behavior.

## Readiness Authority

Use this precedence when sources disagree:

1. JSON Schemas are canonical for structural validity.
2. `validate_test_cases_intake.py` is canonical for readiness status and blocker codes.
3. `templates/intake-test-cases-contract.md` is canonical for semantic extraction policy.

Do not restate, reinterpret, or override blocker codes in this command.

## Report

Return the mode executed, output or validated directory, source refs captured, scenario counts, readiness result, blocker errors, next corrective action when blocked, and coverage gaps.
