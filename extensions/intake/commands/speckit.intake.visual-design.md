---
description: Capture or validate visual design intake for the active Spec Kit feature.
---

## User Input

```text
$ARGUMENTS
```

Classify the input before proceeding:

- `source`: image, PDF, Markdown design brief, Figma URL, file, page, frame, node, or exported design asset
- `intake_dir`: existing visual-design intake artifact directory
- `validation_request`: validate, check, gate, or readiness request
- `review_guidance`: target platform, required fidelity, capture scope, source precedence, or reviewer instructions

## Goal

Create, update, or validate provider-neutral visual design intake artifacts for the active Spec Kit feature. Intake preserves reachable design sources, raw provider evidence, stable source refs, checksums or retrieval metadata, and schema-required visual facts so downstream SDD workflows can project requirements and define their own visual verification criteria with traceability.

Default artifact directory:

```text
specs/<feature>/intake/visual-design/
```

Normative authority:

- `templates/schemas/*.json` defines machine-readable structure, required fields, types, and enums.
- `scripts/python/validate_visual_design_intake.py` defines readiness evaluation and blocker emission.
- `templates/intake-visual-design-contract.md` defines semantic extraction policy, fidelity policy, and provider evidence policy.
- This command only performs input routing, context loading, capture orchestration, validation invocation, and reporting.

## Operating Boundaries

- Preserve original design sources and record checksums before extraction.
- Extract visual requirements as traceable engineering input, not as unsupported prose summaries or downstream-specific schema projections.
- Mark low, medium, or high fidelity explicitly and apply the matching extraction rules.
- Use stable provider-neutral evidence IDs and source refs. Do not invent downstream-owned item IDs, requirement IDs, schema fields, code component names, or product semantics.
- Do not mark intake ready unless source integrity, requirement traceability, fidelity proof, and intake parity planning pass.
- Preserve raw Figma metadata exactly in `figma-metadata.part-*.xml` for Figma sources.
- Do not modify application source, tests, package manifests, feature implementation files, or existing Spec Kit core templates.
- If required tooling is unavailable, create a blocked evidence packet that records the missing tool and stop before claiming readiness.

## Context Loading

1. Verify the current directory is a Spec Kit project by checking for `.specify/`, unless `$ARGUMENTS` points to a standalone artifact directory for extension development.
2. Identify the active feature:
   - Prefer `SPECIFY_FEATURE` when set.
   - Otherwise use the current Git branch name when it matches a directory under `specs/`.
   - Otherwise inspect `specs/` and choose the most recent feature directory only if there is a single clear candidate.
   - If the feature cannot be identified and no standalone artifact directory was provided, stop and ask the user to set `SPECIFY_FEATURE` or run from the feature branch.
3. Read `.specify/extensions/intake/intake-config.yml` when present.
4. Read `templates/intake-visual-design-contract.md` and the referenced JSON Schemas from this extension before creating or validating artifacts.
5. Read any existing intake artifacts and preserve valid evidence unless the user explicitly asks to recapture it.

## Mode Routing

- Capture mode: use when `$ARGUMENTS` names an image, PDF, Markdown design brief, Figma URL, frame, node, platform, fidelity level, or asks to capture, ingest, update, or recapture visual evidence.
- Validate mode: use when `$ARGUMENTS` includes `validate`, `check`, `gate`, `readiness`, or only names an existing visual-design intake directory.
- Capture then validate: use when both a source and validation intent are present, or after capture artifacts are updated.

## Capture Procedure

1. Resolve the source from `$ARGUMENTS` or existing artifact metadata:
   - source type: `image`, `pdf`, `markdown`, or `figma`
   - source path, URL, file key, page, frame, node, region, or Markdown section scope
   - required fidelity: `low`, `medium`, or `high`
   - design version or timestamp
2. Create `design-source-manifest.yaml` with contract-required source identity, integrity, coverage, capture method, and fidelity fields.
3. Preserve file-based originals under `source-files/`; for remote or Figma sources, record stable URLs and exported screenshots or assets, or record a structured gap/blocker when unavailable.
4. For Figma sources, preserve raw provider evidence before deriving normalized requirements:
   - write raw metadata shards as `figma-metadata.part-NNN.xml`
   - build `figma-metadata.index.yaml`
   - build `figma-node-inventory.yaml`
   - validate metadata and inventory parity before deriving visual requirements
5. Extract source-specific evidence:
   - image: dimensions, regions, OCR status, visual hierarchy, assets, and region coverage
   - pdf: original file hash, page count, rendered page refs, text extraction status, and page coverage
   - markdown: heading structure, design notes, embedded or linked assets, and visual requirement mappings
   - figma: complete descendant metadata, node inventory, variables/styles/components, screenshots, and assets
6. Classify source-domain scenario coverage using `templates/intake-visual-design-contract.md`; do not define additional scenario categories in this command.
7. Build `visual-requirements.yaml` according to `templates/schemas/visual-requirements.schema.json` and the semantic policies in `templates/intake-visual-design-contract.md`.
8. For unavailable required evidence, record a structured gap or blocker instead of omitting the field.
9. Create or update `visual-evidence-packet.md` from `templates/intake-visual-design-evidence-packet-template.md` with readiness front matter and human-readable evidence notes; keep structured records in `visual-requirements.yaml`. Preserve an existing `figma-evidence-packet.md` only as a legacy compatibility alias when already configured by the host project.
10. Add an intake parity plan that records source-side comparison targets, methods, thresholds, accepted exceptions, and blocking difference categories without defining implementation capture artifacts or downstream delivery approval.
11. Run validation before reporting readiness.

## Validation Procedure

1. Resolve the visual-design intake directory from `$ARGUMENTS` or the active feature.
2. Run:

```bash
python .specify/extensions/intake/scripts/python/validate_visual_design_intake.py <intake-dir>
```

3. Prefer `--json` when a machine-readable result is needed. Report the validator result exactly:
   - `PASS` means the evidence passed JSON Schema structure checks and is ready for downstream projection as traceable visual engineering input.
   - `BLOCKED` means downstream workflows must keep design-derived requirements blocked, unresolved, or marked `[NEEDS CLARIFICATION]` instead of promoting unsupported design facts.

## Readiness Authority

Use this precedence when sources disagree:

1. JSON Schemas are canonical for structural validity.
2. `validate_visual_design_intake.py` is canonical for readiness status and blocker codes.
3. `templates/intake-visual-design-contract.md` is canonical for semantic extraction, fidelity, and provider evidence policy.

Do not restate, reinterpret, or override blocker codes in this command.

## Report

Return:

- mode executed: capture, validate, or capture_then_validate
- output or validated directory
- source type and source refs captured, or the recorded gap/blocker
- required fidelity, or the recorded gap/blocker
- source file count and processed count, or the recorded gap/blocker
- visual requirement count
- readiness result
- blocker lint errors
- next corrective action when blocked
- open questions that must remain `[NEEDS CLARIFICATION]`
