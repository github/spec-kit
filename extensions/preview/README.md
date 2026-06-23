# Spec Kit Preview Extension

Generate evidence-backed low, mid, or high fidelity previews from Spec Kit feature artifacts as Markdown or self-contained HTML.

## Overview

This extension adds review artifacts between specification and implementation. It helps teams validate product flows, page/state structure, coverage evidence, layout assumptions, UI states, and interaction details before production code is planned or built.

Commands act as execution orchestrators: they resolve the active feature, load Spec Kit artifacts, apply evidence policy, and fill fixed templates under `templates/preview/`. The templates are the source of truth for output sections, table schemas, HTML shells, and preserved-review slots. Structural validation is driven by `schemas/preview/contract.json`, validated against `schemas/preview/contract.schema.json`.

Generated HTML previews are intentionally standalone:

- one HTML file
- inline CSS
- JavaScript only where the selected fidelity allows it
- no network dependencies
- no build step
- no production source changes

Markdown previews are evidence-backed wireflows with requirement coverage, unknowns, and review questions.

## Commands

| Command | Description |
|---------|-------------|
| `speckit.preview.low-md` | Generate `specs/<feature>/preview/wireflow-low.md` |
| `speckit.preview.low-html` | Generate `specs/<feature>/preview/wireflow-low.html` |
| `speckit.preview.mid-md` | Generate `specs/<feature>/preview/wireflow-mid.md` |
| `speckit.preview.mid-html` | Generate `specs/<feature>/preview/wireflow-mid.html` |
| `speckit.preview.high-md` | Generate `specs/<feature>/preview/wireflow-high.md` |
| `speckit.preview.high-html` | Generate `specs/<feature>/preview/wireflow-high.html` |

## Usage

```text
/speckit.preview.low-md
/speckit.preview.mid-html
/speckit.preview.high-html
```

Optional focus examples:

```text
/speckit.preview.low-md onboarding happy path
/speckit.preview.low-html onboarding happy path
/speckit.preview.mid-md admin dashboard empty and error states
/speckit.preview.mid-html admin dashboard empty and error states
/speckit.preview.high-md checkout review flow, desktop first
/speckit.preview.high-html checkout review flow, desktop first
```

## Inputs

The command reads the active feature under `specs/<feature>/`:

- `spec.md` (required)
- `plan.md` (optional)
- `research.md` (optional)
- `data-model.md` (optional)
- `contracts/` (optional)
- `quickstart.md` (optional)

It also reads `.specify/memory/constitution.md` when present.

## Output

```text
specs/<feature>/preview/wireflow-low.md
specs/<feature>/preview/wireflow-low.html
specs/<feature>/preview/wireflow-mid.md
specs/<feature>/preview/wireflow-mid.html
specs/<feature>/preview/wireflow-high.md
specs/<feature>/preview/wireflow-high.html
```

HTML files can be opened directly in a browser.

## Fidelity

- Low fidelity: early feasibility review, abstract nodes, core path, branch points, and major missing scope.
- Mid fidelity: product, UX, and engineering review with source-defined labels, page/state inventory, basic layout relationships, and state coverage.
- High fidelity: final confirmation with interaction matrix, state matrix, validation feedback, permissions, responsive states, and clickable HTML simulation in the `.html` command.

## Boundaries

This extension does not modify app source code, tests, build files, specs, plans, or tasks. Previews are not production implementation and should not replace `/speckit.plan`, `/speckit.tasks`, or `/speckit.implement`.

## Installation

Install from the v1.1.0 release ZIP:

```bash
specify extension add preview --from https://github.com/bigsmartben/spec-kit-preview/archive/refs/tags/v1.1.0.zip
```

For local development from this repository root:

```bash
specify extension add --dev .
```

## Files Written

When the command runs in a Spec Kit project, it writes only:

```text
specs/<feature>/preview/wireflow-*.md
specs/<feature>/preview/wireflow-*.html
```

Installing the extension copies this repository into:

```text
.specify/extensions/preview/
```

## Template Sources

Command prompts load one matching template per output:

```text
templates/preview/low.md
templates/preview/low.html
templates/preview/mid.md
templates/preview/mid.html
templates/preview/high.md
templates/preview/high.html
```

The command layer owns context loading, evidence policy, and file-write boundaries. The template layer owns sections, required tables, HTML structure, and the preserved review records slot.

## Validation Contract

Repository validation uses a schema-backed JSON contract:

```text
schemas/preview/contract.schema.json
schemas/preview/contract.json
```

`tests/validate-extension.py` validates the contract shape with a standard-library JSON Schema subset, then uses the contract to verify manifest command mappings, command/template files, required slots, forbidden legacy phrases, and documentation alignment.
