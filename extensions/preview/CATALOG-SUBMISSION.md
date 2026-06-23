# Spec Kit Extension Submission

Extension ID: preview
Name: Spec Kit Preview
Version: 1.1.0
Description: Generate evidence-backed low, mid, or high fidelity previews from Spec Kit artifacts as Markdown or self-contained HTML
Author: bigsmartben
Repository URL: https://github.com/bigsmartben/spec-kit-preview
Download URL: https://github.com/bigsmartben/spec-kit-preview/archive/refs/tags/v1.1.0.zip
Documentation URL: https://github.com/bigsmartben/spec-kit-preview/blob/main/README.md
License: MIT
Required Spec Kit version: >=0.8.10.dev0
Commands count: 6
Hooks count: 0
Tags: preview, prototype, html, markdown, wireflow, ux

## Key Features

- Adds `speckit.preview.low-md` and `speckit.preview.low-html`.
- Adds `speckit.preview.mid-md` and `speckit.preview.mid-html`.
- Adds `speckit.preview.high-md` and `speckit.preview.high-html`.
- Generates `specs/<feature>/preview/wireflow-low.md`, `wireflow-mid.md`, or `wireflow-high.md`.
- Generates matching `wireflow-low.html`, `wireflow-mid.html`, or `wireflow-high.html`.
- Uses fixed templates under `templates/preview/` for output sections, table schemas, HTML shells, and preserved-review slots.
- Uses `schemas/preview/contract.json` and `schemas/preview/contract.schema.json` as the structural validation source.
- Keeps previews self-contained with inline CSS and fidelity-appropriate JavaScript.
- Explicitly avoids production source, spec, plan, and task file changes.
- Captures coverage evidence, inferred assumptions, unsupported items, and unresolved questions.

## Testing Performed

- `python3 -m py_compile tests/validate-extension.py`
- `python3 tests/validate-extension.py`
- Installed locally with `specify extension add --dev /home/administrator/github/spec-kit-preview` in a fresh Spec Kit project.
- Verified six `.qwen/commands/speckit.preview.*.md` commands were registered.
- Verified installed extension contents excluded `tests/` via `.extensionignore`.
## Release Checklist

- Create release `v1.1.0` from this revision.
- Install release ZIP in a fresh Spec Kit project:
  `specify extension add preview --from https://github.com/bigsmartben/spec-kit-preview/archive/refs/tags/v1.1.0.zip`
