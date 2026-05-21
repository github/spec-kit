# Spec Kit Extension Submission

Extension ID: preview
Name: Interactive HTML Preview
Version: 1.0.0
Description: Generate self-contained interactive HTML prototypes from Spec Kit artifacts
Author: bigsmartben
Repository URL: https://github.com/bigsmartben/spec-kit-preview
Download URL: https://github.com/bigsmartben/spec-kit-preview/archive/refs/tags/v1.0.0.zip
Documentation URL: https://github.com/bigsmartben/spec-kit-preview/blob/main/README.md
License: MIT
Required Spec Kit version: >=0.8.10.dev0
Commands count: 1
Hooks count: 0
Tags: preview, prototype, html, ux

## Key Features

- Adds `speckit.preview.html`.
- Generates `specs/<feature>/preview/index.html`.
- Keeps prototypes self-contained with inline CSS and JavaScript.
- Explicitly avoids production source, spec, plan, and task file changes.
- Captures prototype assumptions and unresolved questions.

## Testing Performed

- `python3 -m py_compile tests/validate-extension.py`
- `python3 tests/validate-extension.py`
- Installed locally with `specify extension add --dev /home/administrator/github/spec-kit-preview` in a fresh Spec Kit project.
- Verified `.qwen/commands/speckit.preview.html.md` was registered.
- Verified installed extension contents excluded `tests/` via `.extensionignore`.
- Created release `v1.0.0`.
- Installed release ZIP in a fresh Spec Kit project:
  `specify extension add preview --from https://github.com/bigsmartben/spec-kit-preview/archive/refs/tags/v1.0.0.zip`
