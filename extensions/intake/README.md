# Spec Kit Intake Extension

Extract, normalize, and validate SDD-ready intake artifacts from PRDs, visual designs, test cases, and other software sources before downstream Spec Kit workflows project them into requirements.

The first goal of intake is not to generate requirements. It is to preserve as much input information as possible and turn it into structured material that SDD `specify` can consume accurately.

The intake goal is high-information source restoration: extracted facts must be usable as provider-neutral engineering input, and every downstream projection should remain traceable to the original artifact.

Intake artifacts are validated in two layers: JSON Schema checks enforce the required structure, field types, and enums; readiness validators then check source integrity, traceability, hashes, gaps, and cross-file parity.

## Supported Intake Sources

- PRDs, product briefs, Markdown documents, PDFs, and exported docs
- Low-fidelity, medium-fidelity, and high-fidelity design drafts
- Static images such as PNG, JPG, WebP, and exported screens
- PDF design packs and annotated review documents
- Figma files, pages, frames, nodes, components, variables, and exported screenshots
- Existing test cases, Gherkin files, QA exports, and test management spreadsheets

## Intake Scenario Coverage

Intake commands are organized by vertical source domain. Each domain uses the same evidence pattern: preserve the original source, normalize source-backed facts, keep uncertainty explicit, and report readiness before downstream Spec Kit workflows project the evidence.

| Domain | Vertical scenarios | Normalized artifact | Primary readiness focus |
| --- | --- | --- | --- |
| PRD | product briefs, Markdown PRDs, exported docs, PDFs, issue or epic links, mixed stakeholder notes | `prd-intake.yaml` | source identity, product intent traceability, scope boundaries, acceptance evidence, clarification gaps |
| Visual design | static images, wireframes, PDF design packs, Markdown design briefs, Figma files or selected nodes | `visual-requirements.yaml` | source integrity, fidelity rules, visual requirement traceability, parity planning, Figma metadata completeness when relevant |
| Test cases | automated tests, Gherkin files, manual QA cases, spreadsheets, test management exports, bug or issue repro steps | `test-case-intake.yaml` | scenario traceability, assertion extraction, fixture evidence, coverage gaps, flaky or skipped case reporting |

Vertical instructions should never convert source evidence directly into downstream-owned requirement IDs, implementation tasks, or code component names. They produce provider-neutral intake facts that downstream workflows can consume with source refs intact.

## Commands

- `/speckit.intake.visual-design` captures or validates visual design evidence, source manifests, Figma metadata when available, inventories, and readiness for the active feature.
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
│   └── visual-evidence-packet.md
└── test-cases/
    ├── source-manifest.yaml
    ├── source-files/
    ├── test-case-intake.yaml
    └── evidence-packet.md
```

Figma metadata artifacts are required for Figma visual-design sources. Image, PDF, and Markdown visual-design sources use `design-source-manifest.yaml`, source-file checksums, extracted visual requirements, and visual parity evidence instead. PRD and test-case domains use their own source manifests and normalized intake files.

Machine-readable JSON Schemas live under `templates/schemas/` and are used by the validators before readiness rules run.

All intake commands provide capture instructions, evidence contracts, and readiness validation. Visual design validation additionally checks visual fidelity and Figma metadata parity.

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
specify extension add intake --from https://github.com/bigsmartben/spec-kit-intake/archive/refs/tags/v0.1.2.zip
```

Then run:

```text
/speckit.intake.visual-design capture <image|pdf|markdown|figma source and scope>
/speckit.intake.visual-design validate
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
- parity evidence explains how implementation output will be compared with the original design artifact
- Figma sources also pass raw metadata completeness and node-inventory parity
- no blocker lint errors exist

## Development

Validate the manifest from the local `spec-kit` checkout:

```bash
python -c "from pathlib import Path; from specify_cli.extensions import ExtensionManifest; ExtensionManifest(Path('extension.yml')); print('manifest ok')"
```

Validate visual-design artifacts:

```bash
python scripts/python/validate_visual_design_intake.py specs/<feature>/intake/visual-design
```

Validate PRD artifacts:

```bash
python scripts/python/validate_prd_intake.py specs/<feature>/intake/prd
```

Validate test-case artifacts:

```bash
python scripts/python/validate_test_cases_intake.py specs/<feature>/intake/test-cases
```
