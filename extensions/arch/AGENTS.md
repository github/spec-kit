# Architecture Workflow Extension

This repository is a Spec Kit community extension source project for `arch`.

## Project Shape

- `extension.yml` is the extension manifest and must stay aligned with declared files.
- `commands/` contains Spec Kit command templates.
- `templates/` contains architecture artifact templates.
- `schemas/` contains architecture artifact schemas.
- `scripts/` contains setup helpers.
- `tests/repository-first-contract.sh` is the main contract test.
- `presets/arch-governance/` is a nested source preset owned by this repository.

## Source Workflow

- Develop extension and nested preset source changes in this repository.
- Release versioned source artifacts from this repository.
- Keep `README.md`, `CHANGELOG.md`, `CATALOG-SUBMISSION.md`, manifests, and tests aligned.
- Run `bash tests/repository-first-contract.sh` after behavior, command, template, schema, or setup-script changes.

## Integration Boundary

- This repository owns source development and release artifacts only.
- Do not open pull requests from this repository directly to `github/spec-kit`.
- Do not push branches to `github/spec-kit` or add workflow automation that targets `github/spec-kit` for pull requests, repository dispatches, or direct writes.
- If a Spec Kit catalog or bundled snapshot update is needed, target the `bigsmartben/spec-kit` integration fork first. The integration fork owns any downstream pull request to `github/spec-kit`.
- Source releases must provide source-backed metadata for the integration fork: repository URL, release version, source commit SHA, download URL, and validation evidence.

## Handoff

- changed files
- commands run
- validation result
- unresolved risks
