---
description: Capture PRD intake for the active Spec Kit feature.
---

## User Input

```text
$ARGUMENTS
```

Classify the input before proceeding:

- `source`: PRD file, Markdown document, PDF, URL, exported doc, issue, epic, or section scope
- `intake_dir`: existing PRD intake artifact directory
- `validation_request`: validate, check, gate, or readiness request
- `review_guidance`: source precedence, extraction scope, or reviewer instructions

## Goal

Create, update, or validate PRD intake artifacts for the active Spec Kit feature. Intake preserves reachable source files, stable source refs, checksums or retrieval metadata, and schema-required source-backed product facts so downstream SDD workflows can project requirements, scope, acceptance criteria, and clarification items with traceability.

Default output directory:

```text
specs/<feature>/intake/prd/
```

Normative authority:

- `templates/schemas/*.json` defines machine-readable structure, required fields, types, and enums.
- `scripts/python/validate_prd_intake.py` defines readiness evaluation and blocker emission.
- `templates/intake-prd-contract.md` defines semantic extraction policy and source-domain terminology.
- This command only performs input routing, context loading, capture orchestration, validation invocation, and reporting.

## Operating Boundaries

- Preserve original PRD sources and record checksums or stable retrieval metadata before extraction.
- Extract source-backed product facts, not downstream-owned requirement IDs, implementation tasks, code component names, or unsupported product semantics.
- Keep ambiguous, missing, stale, or conflicting product facts explicit as `[NEEDS CLARIFICATION]`.
- Use stable provider-neutral evidence IDs and source refs that downstream workflows can map later.
- Do not mark intake ready unless source integrity, traceability, extraction completeness, and blocker review pass.
- Do not modify application source, tests, package manifests, feature implementation files, or existing Spec Kit core templates.

## Context Loading

1. Verify the current directory is a Spec Kit project by checking for `.specify/`.
2. Identify the active feature:
   - Prefer `SPECIFY_FEATURE` when set.
   - Otherwise use the current Git branch name when it matches a directory under `specs/`.
   - Otherwise inspect `specs/` and choose the most recent feature directory only if there is a single clear candidate.
   - If the feature cannot be identified, stop and ask the user to set `SPECIFY_FEATURE` or run from the feature branch.
3. Read `.specify/extensions/intake/intake-config.yml` when present.
4. Read `templates/intake-prd-contract.md` and the referenced JSON Schemas from this extension before creating or validating artifacts.
5. Read any existing PRD intake artifacts and preserve valid evidence unless the user explicitly asks to recapture it.

## Mode Routing

- Capture mode: use when `$ARGUMENTS` names a PRD file, Markdown document, PDF, URL, issue, exported doc, section scope, or asks to capture, ingest, update, or recapture product evidence.
- Validate mode: use when `$ARGUMENTS` includes `validate`, `check`, `gate`, `readiness`, or only names an existing PRD intake directory.
- Capture then validate: use when both a source and validation intent are present, or after capture artifacts are updated.

## Capture Procedure

1. Resolve the PRD source, document version, relevant sections, and target feature.
2. Preserve source identity and checksums in `source-manifest.yaml`.
3. Classify source-domain scenario coverage using `templates/intake-prd-contract.md`; do not define additional scenario categories in this command.
4. Extract source-backed facts into `prd-intake.yaml` according to `templates/schemas/prd-intake.schema.json` and the semantic policies in `templates/intake-prd-contract.md`.
5. For unavailable required evidence, record a structured gap or blocker instead of omitting the field.
6. Record conflicts, stale context, missing acceptance evidence, and unresolved decisions as explicit gaps instead of smoothing them into inferred requirements.
7. Create `evidence-packet.md` from `templates/intake-prd-evidence-packet-template.md` with readiness front matter and human-readable evidence notes; keep structured records in `prd-intake.yaml`.

## Validation Procedure

1. Resolve the PRD intake directory from `$ARGUMENTS` or the active feature.
2. Run:

```bash
python .specify/extensions/intake/scripts/python/validate_prd_intake.py <intake-dir>
```

3. Prefer `--json` when a machine-readable result is needed. Report the validator result exactly:
   - `PASS` means the PRD artifacts passed JSON Schema structure checks and are ready for downstream projection as traceable product input.
   - `BLOCKED` means downstream workflows must keep PRD-derived facts blocked, unresolved, or marked `[NEEDS CLARIFICATION]` instead of promoting unsupported product intent.

## Readiness Authority

Use this precedence when sources disagree:

1. JSON Schemas are canonical for structural validity.
2. `validate_prd_intake.py` is canonical for readiness status and blocker codes.
3. `templates/intake-prd-contract.md` is canonical for semantic extraction policy.

Do not restate, reinterpret, or override blocker codes in this command.

## Report

Return the mode executed, output or validated directory, source refs captured, extracted item counts, readiness result, blocker errors, next corrective action when blocked, and open clarification items.
