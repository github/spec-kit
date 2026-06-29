---
description: Create or validate a Figma-derived HTML visual SSOT bundle for acceptance.
---

## User Input

```text
$ARGUMENTS
```

Classify the input before proceeding:

- `source`: Figma URL, file, page, frame, node, component set, or existing visual-design intake directory
- `output_dir`: existing or target figma2htmlssot artifact directory
- `validation_request`: validate, check, gate, coverage, diff, or readiness request
- `review_guidance`: target platform, viewport set, required states, capture scope, visual-diff threshold, or reviewer instructions

## Goal

Create, update, or validate a Figma-to-HTML visual single source of truth (SSOT) bundle for the active Spec Kit feature. The HTML bundle defines visual requirements and acceptance surfaces by preserving Figma traceability, source coverage, component-instance-state granularity, page-level composition, assets, responsive behavior, and known gaps.

Default output directory:

```text
specs/<feature>/intake/visual-design/figma2htmlssot/
```

Normative authority:

- `templates/intake-visual-design-contract.md` defines visual evidence semantics, fidelity policy, and provider evidence policy.
- `templates/schemas/figma-metadata-index.schema.json` and `templates/schemas/figma-node-inventory.schema.json` define required Figma metadata evidence when the source is Figma.
- `scripts/python/validate_visual_design_intake.py` defines source-side visual-design intake readiness before HTML SSOT projection.
- `templates/schemas/figma-map.schema.json`, `templates/schemas/assets-manifest.schema.json`, and `templates/schemas/html-ssot-coverage.schema.json` define machine-readable HTML SSOT bundle structure.
- `scripts/python/validate_html_ssot.py` defines HTML SSOT readiness, cross-file traceability checks, and blocker codes.
- This command owns HTML SSOT routing, capture orchestration, validation invocation, and report shape.

## Operating Boundaries

- Treat HTML as the visual requirements SSOT artifact only after Figma source evidence and coverage proof are recorded.
- Preserve the original Figma source refs, raw metadata refs, screenshots, asset refs, and node inventory refs.
- Do not convert visual facts into product behavior, API rules, implementation plans, implementation tasks, downstream-owned requirement IDs, or code component names.
- Do not mark the HTML SSOT ready when required Figma nodes, required component-instance states, required page surfaces, assets, or viewport captures are missing.
- Do not modify application source, tests, package manifests, feature implementation files, or existing Spec Kit core templates.
- If required Figma, screenshot, browser, or diff tooling is unavailable, create a blocked evidence report that records the missing tool and stop before claiming readiness.

## Completeness Units

The minimum visual acceptance unit is:

```text
component instance + state + content sample + container constraint + viewport
```

Use this hierarchy:

- Component-instance-state: minimum runnable screenshot and comparison unit for tokens, local layout, states, overflow, and local interaction surfaces.
- Section: composition unit for spacing, ordering, alignment, and local responsive behavior across multiple component instances.
- Page: final release gate for information completeness, cross-section layout, first-viewport experience, scrolling, and target runtime acceptance.

Component-level acceptance cannot replace page-level acceptance. Page-level acceptance cannot replace required component-instance-state coverage.

## Context Loading

1. Verify the current directory is a Spec Kit project by checking for `.specify/`, unless `$ARGUMENTS` points to a standalone artifact directory for extension development.
2. Identify the active feature:
   - Prefer `SPECIFY_FEATURE` when set.
   - Otherwise use the current Git branch name when it matches a directory under `specs/`.
   - Otherwise inspect `specs/` and choose the most recent feature directory only if there is a single clear candidate.
   - If the feature cannot be identified and no standalone artifact directory was provided, stop and ask the user to set `SPECIFY_FEATURE` or run from the feature branch.
3. Read `.specify/extensions/intake/intake-config.yml` when present.
4. Read `templates/intake-visual-design-contract.md`, Figma metadata schemas, and existing visual-design intake artifacts before creating or validating HTML SSOT artifacts.
5. For Figma sources, require existing or newly captured `figma-metadata.index.yaml`, `figma-node-inventory.yaml`, and `figma-metadata.part-*.xml` before deriving the HTML SSOT.
6. Read any existing figma2htmlssot artifacts and preserve valid evidence unless the user explicitly asks to recapture or regenerate it.

## Mode Routing

- Build mode: use when `$ARGUMENTS` names a Figma source, node scope, viewport set, state matrix, or asks to build, generate, convert, capture, update, or recapture the HTML SSOT.
- Validate mode: use when `$ARGUMENTS` includes `validate`, `check`, `gate`, `coverage`, `diff`, `readiness`, or only names an existing figma2htmlssot output directory.
- Build then validate: use when both a source and validation intent are present, or after build artifacts are updated.

## Build Procedure

1. Resolve the Figma source, selected page/frame/node scope, target viewport set, required component-instance states, and target output directory.
2. Ensure the upstream visual-design intake for the Figma source passes readiness:

```bash
python .specify/extensions/intake/scripts/python/validate_visual_design_intake.py <visual-design-intake-dir>
```

3. Create or update these HTML SSOT bundle artifacts:
   - `visual-spec.html`: runnable HTML visual SSOT with required surfaces and states.
   - `figma-map.json`: mapping from Figma node IDs to HTML selectors and acceptance units.
   - `assets-manifest.json`: fonts, images, icons, media, and exported asset refs with source refs.
   - `coverage-report.md`: required node, state, section, page, asset, and viewport coverage.
   - `known-gaps.md`: accepted exceptions, missing evidence, blocked captures, and owner or next action.
   - `screenshots/`: Figma source screenshots, HTML screenshots, and diff outputs when tooling is available.
4. Add traceability attributes to required HTML elements:

```html
data-figma-node-id="<figma-node-id>"
data-spec-role="<provider-neutral-role>"
data-acceptance-unit="<component-state|section|page>"
data-required="true"
```

5. Preserve design tokens and visual facts in CSS custom properties or documented token mappings when available. Record unmapped tokens as gaps instead of silently flattening them.
6. Export or reference assets through `assets-manifest.json`; do not embed untraceable base64 assets unless the source ref and checksum are recorded.
7. Capture target runtime screenshots for every required component-instance-state, section, and page surface across the declared viewport set.
8. Compare Figma and HTML screenshots when tooling is available. Record thresholds, accepted exceptions, and blocking difference categories in `coverage-report.md`.
9. Validate the HTML SSOT bundle before reporting readiness:

```bash
python .specify/extensions/intake/scripts/python/validate_html_ssot.py <figma2htmlssot-dir>
```

10. For unavailable required evidence, write a structured blocker in `known-gaps.md` and report `ready_gate: BLOCKED`.

## Validation Procedure

1. Resolve the figma2htmlssot output directory from `$ARGUMENTS` or the active feature.
2. Run:

```bash
python .specify/extensions/intake/scripts/python/validate_html_ssot.py <figma2htmlssot-dir>
```

3. The validator confirms required bundle artifacts exist and are internally consistent:
   - every required Figma node is covered by `figma-map.json` or recorded as an accepted exclusion
   - every required component-instance-state has a runnable HTML selector, viewport, content sample, container constraint, and screenshot
   - every required section and page has a runnable HTML selector, viewport coverage, and screenshot
   - every referenced asset appears in `assets-manifest.json` with source refs and checksum
   - every required HTML element has a stable Figma source ref
4. Apply these blocker codes when validation fails:
   - `HTML_SSOT_SOURCE_INTAKE_BLOCKED`
   - `HTML_SSOT_REQUIRED_ARTIFACT_MISSING`
   - `HTML_SSOT_FIGMA_NODE_COVERAGE_INCOMPLETE`
   - `HTML_SSOT_COMPONENT_STATE_COVERAGE_INCOMPLETE`
   - `HTML_SSOT_PAGE_COVERAGE_INCOMPLETE`
   - `HTML_SSOT_ASSET_TRACEABILITY_INCOMPLETE`
   - `HTML_SSOT_VIEWPORT_CAPTURE_INCOMPLETE`
   - `HTML_SSOT_VISUAL_DIFF_BLOCKED`
   - `HTML_SSOT_KNOWN_GAP_UNRESOLVED`
5. Mark readiness:
   - `PASS` only when required artifacts exist, required coverage is complete, screenshots are captured, blockers are empty, and accepted exceptions are explicit.
   - `BLOCKED` when any blocker code is present or any required coverage item lacks traceable evidence.

## Readiness Authority

Use this precedence when sources disagree:

1. Upstream Figma metadata and visual-design intake readiness are canonical for source evidence.
2. `figma-map.json`, `assets-manifest.json`, and screenshot captures are canonical for HTML SSOT traceability and runtime coverage.
3. `coverage-report.md` and `known-gaps.md` explain readiness, accepted exceptions, and blockers for human review.

Do not promote HTML as the visual SSOT when upstream Figma evidence is incomplete or when coverage cannot prove the minimum component-instance-state and page-level gates.

## Report

Return:

- mode executed: build, validate, or build_then_validate
- output or validated directory
- Figma source scope and upstream visual-design intake readiness
- required viewport set
- component-instance-state, section, and page coverage counts
- asset count and unresolved asset gaps
- screenshot and visual-diff status
- readiness result
- blocker codes
- known accepted exceptions
- next corrective action when blocked
