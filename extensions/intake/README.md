# Spec Kit Intake Extension

Extract, normalize, and validate SDD-ready intake artifacts from PRDs, visual designs, Figma-derived HTML visual SSOT bundles, test cases, and other software sources before downstream Spec Kit workflows project them into requirements.

The first goal of intake is not to generate requirements. It is to preserve as much input information as possible and turn it into structured material that SDD `specify` can consume accurately.

The intake goal is high-information source restoration: extracted facts must be usable as provider-neutral engineering input, and every downstream projection should remain traceable to the original artifact.

Intake artifacts are validated in two layers: JSON Schema checks enforce the required structure, field types, and enums; readiness validators then check source integrity, traceability, hashes, gaps, and cross-file parity.

## Supported Intake Sources

- PRDs, product briefs, Markdown documents, PDFs, and exported docs
- Low-fidelity, medium-fidelity, and high-fidelity design drafts
- Static images such as PNG, JPG, WebP, and exported screens
- PDF design packs and annotated review documents
- Figma files, pages, frames, nodes, components, variables, and exported screenshots
- Figma-derived HTML visual SSOT bundles with traceable component-state and page coverage
- Existing test cases, Gherkin files, QA exports, and test management spreadsheets

## Intake Scenario Coverage

Intake commands are organized by vertical source domain. Each domain uses the same evidence pattern: preserve the original source, normalize source-backed facts, keep uncertainty explicit, and report readiness before downstream Spec Kit workflows project the evidence.

| Domain | Vertical scenarios | Normalized artifact | Primary readiness focus |
| --- | --- | --- | --- |
| PRD | product briefs, Markdown PRDs, exported docs, PDFs, issue or epic links, mixed stakeholder notes | `prd-intake.yaml` | source identity, product intent traceability, scope boundaries, acceptance evidence, clarification gaps |
| Visual design | static images, wireframes, PDF design packs, Markdown design briefs, Figma files or selected nodes | `visual-requirements.yaml` | source integrity, fidelity rules, visual requirement traceability, parity planning, Figma metadata completeness when relevant |
| Figma to HTML SSOT | Figma files or selected nodes projected into runnable HTML visual acceptance surfaces | `visual-spec.html` | Figma node coverage, component-instance-state coverage, page coverage, asset traceability, viewport screenshots, known gaps |
| Test cases | automated tests, Gherkin files, manual QA cases, spreadsheets, test management exports, bug or issue repro steps | `test-case-intake.yaml` | scenario traceability, assertion extraction, fixture evidence, coverage gaps, flaky or skipped case reporting |

Vertical instructions should never convert source evidence directly into downstream-owned requirement IDs, implementation tasks, or code component names. They produce provider-neutral intake facts that downstream workflows can consume with source refs intact.

## Commands

- `/speckit.intake.visual-design` captures or validates visual design evidence, source manifests, Figma metadata when available, inventories, and readiness for the active feature.
- `/speckit.intake.figma2htmlssot` creates or validates a Figma-derived HTML visual SSOT bundle with node, component-state, page, asset, viewport, and screenshot coverage.
- `/speckit.intake.prd` captures or validates PRD evidence and normalizes product intent, scope, business rules, acceptance criteria, and clarification items.
- `/speckit.intake.test-cases` captures or validates test case evidence and normalizes scenarios, assertions, fixtures, and coverage gaps.

## Artifact Layout

```text
specs/<feature>/intake/
├── prd/
│   ├── source-manifest.yaml
│   ├── source-files/
│   ├── prd-intake.yaml
│   └── evidence-packet.md
├── visual-design/
│   ├── design-source-manifest.yaml
│   ├── source-files/
│   ├── visual-requirements.yaml
│   ├── figma-metadata.part-001.xml
│   ├── figma-metadata.index.yaml
│   ├── figma-node-inventory.yaml
│   ├── visual-evidence-packet.md
│   └── figma2htmlssot/
│       ├── visual-spec.html
│       ├── figma-map.json
│       ├── assets-manifest.json
│       ├── coverage-report.md
│       ├── known-gaps.md
│       └── screenshots/
└── test-cases/
    ├── source-manifest.yaml
    ├── source-files/
    ├── test-case-intake.yaml
    └── evidence-packet.md
```

Figma metadata artifacts are required for Figma visual-design sources. Image, PDF, and Markdown visual-design sources use `design-source-manifest.yaml`, source-file checksums, extracted visual requirements, and visual parity evidence instead. PRD and test-case domains use their own source manifests and normalized intake files.

Machine-readable JSON Schemas live under `templates/schemas/` and are used by the validators before readiness rules run. HTML SSOT bundles use `figma-map.schema.json`, `assets-manifest.schema.json`, and `html-ssot-coverage.schema.json`.

All intake commands provide capture instructions, evidence contracts, and readiness validation. Visual design validation additionally checks visual fidelity and Figma metadata parity.
HTML SSOT validation is owned by `scripts/python/validate_html_ssot.py`, including cross-file checks for selectors, assets, screenshots, coverage, and known gaps.

## Requirements

- Spec Kit `>=0.8.10.dev0`
- Python validator dependencies: `PyYAML` and `jsonschema`
- Optional: `figma-mcp` for Figma metadata capture

## Install for Local Development

From a Spec Kit project:

```bash
specify extension add --dev C:/Users/24598/Documents/github/spec-kit-intake
```

## Install from Release

From a Spec Kit project:

```bash
specify extension add intake --from https://github.com/bigsmartben/spec-kit-intake/archive/refs/tags/v0.1.3.zip
```

Then run:

```text
/speckit.intake.visual-design capture <image|pdf|markdown|figma source and scope>
/speckit.intake.visual-design validate
/speckit.intake.figma2htmlssot build <figma source or visual-design intake scope>
/speckit.intake.figma2htmlssot validate
/speckit.intake.prd capture <prd source and scope>
/speckit.intake.prd validate
/speckit.intake.test-cases capture <test source and scope>
/speckit.intake.test-cases validate
```

## Visual Design Readiness Gate

Visual design intake passes only when:

- source identity, fidelity level, and source-file integrity are proven
- low, medium, or high-fidelity extraction rules are applied consistently
- extracted requirements preserve layout hierarchy, spacing, typography, color, assets, states, responsive behavior, and accessibility evidence at the fidelity level supplied
- non-observed visual claims use bounded inference fields and stay auditable
- candidate completions remain reference-only and unsupported claims emit blocker codes
- parity evidence explains how implementation output will be compared with the original design artifact
- Figma sources also pass raw metadata completeness and node-inventory parity
- no blocker lint errors exist

Visual design claims use these evidence types:

- `observed`: source-backed fact from preserved files, rendered evidence, Figma metadata, screenshots, or prototype metadata.
- `inferred`: high-confidence derived claim that includes an inference rule, confidence method, score breakdown, and blocking conditions.
- `candidate`: low- or medium-confidence completion with `downstream_use: reference_only`.
- `unsupported`: rejected or blocked claim with a stable blocker code.
- `missing` or `out_of_scope`: explicit absence or excluded surface.

For irregular Figma sources, intake may generate bounded candidate completions, but it must not infer business rules, permissions, form validation, error copy, loading or disabled states, data sources, analytics, security, or compliance behavior from visual appearance alone.

## Figma to HTML SSOT Readiness Gate

Figma-derived HTML SSOT passes only when:

- upstream Figma visual-design intake is ready
- every required Figma node is mapped to HTML or recorded as an accepted exclusion
- the minimum acceptance grain is covered: component instance, state, content sample, container constraint, and viewport
- required sections and pages have runnable HTML selectors and screenshots
- all referenced assets are recorded in `assets-manifest.json`
- screenshot coverage and visual-diff status are recorded
- known gaps are explicit and no blocking gap remains unresolved

The HTML SSOT validator emits blocker codes such as `HTML_SSOT_REQUIRED_ARTIFACT_MISSING`, `HTML_SSOT_FIGMA_NODE_COVERAGE_INCOMPLETE`, `HTML_SSOT_COMPONENT_STATE_COVERAGE_INCOMPLETE`, `HTML_SSOT_PAGE_COVERAGE_INCOMPLETE`, `HTML_SSOT_ASSET_TRACEABILITY_INCOMPLETE`, `HTML_SSOT_VIEWPORT_CAPTURE_INCOMPLETE`, `HTML_SSOT_VISUAL_DIFF_BLOCKED`, and `HTML_SSOT_KNOWN_GAP_UNRESOLVED`.

## Development

Validate the manifest from the local `spec-kit` checkout:

```bash
python -c "from pathlib import Path; from specify_cli.extensions import ExtensionManifest; ExtensionManifest(Path('extension.yml')); print('manifest ok')"
```

Validate visual-design artifacts:

```bash
python scripts/python/validate_visual_design_intake.py specs/<feature>/intake/visual-design
```

Validate HTML SSOT bundles:

```bash
python scripts/python/validate_html_ssot.py specs/<feature>/intake/visual-design/figma2htmlssot
```

Validate PRD artifacts:

```bash
python scripts/python/validate_prd_intake.py specs/<feature>/intake/prd
```

Validate test-case artifacts:

```bash
python scripts/python/validate_test_cases_intake.py specs/<feature>/intake/test-cases
```
