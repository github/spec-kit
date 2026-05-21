# Changelog

## Unreleased

## [1.2.0] - 2026-05-19

### Changed

- Initialize the missing governance evidence cache from repository evidence instead of copying the bundled template verbatim.
- Document captured repository evidence and manifest-backed commands in the initial governance evidence cache.
- Clarify that the extension generates active agent platform repository governance files from Spec Kit metadata.
- Simplify command semantics to one generate/update command: missing target governance files are generated, existing target governance files are updated.
- Include repository evidence and development commands in generated agent platform governance files.
- Add `uv`/`pytest` development configuration so the repository test suite has a reproducible runner.
- Treat the generated active agent platform section as the repository governance SSOT and `.specify/memory/agent-governance.md` as a first-run evidence cache.
- Preserve reviewed governance content from an existing active generated section during refresh instead of re-reading rules from the memory cache.
- Clarify that users review only the resolved active agent governance file; no separate memory review or second refresh is required.
- Distill detected repository areas into generated action rules with depth limited to two directory levels, including hidden and cache directories.
- Add generic directory responsibility governance without platform or project examples.
- Tighten governance template wording to preserve managed markers, scope broad linked-file updates, and limit skill-spec field requirements to repository-local skills.

## [1.1.0] - 2026-05-15

### Changed

- Decoupled the agent governance domain from specific project-governance source files.
- Updated generated projections to describe project governance as an independent domain.

### Added

- Tests for template and projection domain boundaries.

## [1.0.0] - 2026-05-14

### Added

- Initial `speckit.agent-governance.refresh` command.
- Agent governance memory template.
- Python helper to project managed governance sections into active agent context files.
- Optional hooks after constitution, plan, and tasks workflows.
