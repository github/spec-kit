# Interactive HTML Preview Extension

Generate self-contained interactive HTML prototypes from Spec Kit feature artifacts.

## Overview

This extension adds a review artifact between specification and implementation. It helps teams validate product flows, layout assumptions, UI states, and interaction details before production code is planned or built.

The generated prototype is intentionally standalone:

- one HTML file
- inline CSS and JavaScript
- no network dependencies
- no build step
- no production source changes

## Command

| Command | Description |
|---------|-------------|
| `speckit.preview.html` | Generate `specs/<feature>/preview/index.html` from the active feature artifacts |

## Usage

```text
/speckit.preview.html
```

Optional focus examples:

```text
/speckit.preview.html mobile onboarding flow
/speckit.preview.html admin dashboard empty and error states
/speckit.preview.html checkout review flow, desktop first
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
specs/<feature>/preview/index.html
```

The HTML file can be opened directly in a browser.

## Boundaries

This extension does not modify app source code, tests, build files, specs, plans, or tasks. The preview is not a production implementation and should not replace `/speckit.plan`, `/speckit.tasks`, or `/speckit.implement`.

## Installation

Install from the v1.0.0 release ZIP:

```bash
specify extension add preview --from https://github.com/bigsmartben/spec-kit-preview/archive/refs/tags/v1.0.0.zip
```

For local development from this repository root:

```bash
specify extension add --dev .
```

## Files Written

When the command runs in a Spec Kit project, it writes only:

```text
specs/<feature>/preview/index.html
```

Installing the extension copies this repository into:

```text
.specify/extensions/preview/
```
