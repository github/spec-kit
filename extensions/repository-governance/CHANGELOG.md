# Changelog

## Unreleased

## [2.0.6] - 2026-06-24

### Fixed

- Keep spec-kit integration PR validation aligned with current spec-kit test node names.

## [2.0.5] - 2026-06-24

### Fixed

- Update the release smoke install command to use Spec Kit's current `--integration codex` option.

## [2.0.4] - 2026-06-24

### Changed

- Lock local GitHub Actions verification commands with `uv run --locked` and keep the extension install smoke test on the GitHub runner.
- Broaden repository fact detection for extension assets, Spec Kit metadata, project policy files, feature specs, build/runtime config, and Python/uv test commands.
- Replace the local `zip` shell command with a cross-platform Python package builder shared by docs and the release workflow.

### Fixed

- Keep spec-kit integration PR sync aligned with the runtime extension package boundary and current spec-kit test node ids.

## [2.0.2] - 2026-06-03

### Fixed

- Fix release workflow smoke installation after `v2.0.1` failed before artifact publication when Spec Kit already installs the bundled repository-governance extension and projects Codex commands as `.agents/skills`.
- Allow tag release artifact publication to complete when the optional spec-kit integration PR token is unavailable.

## [2.0.1] - 2026-06-03

### Added

- Add GitHub Actions contract CI for repository governance validation.
- Add a release artifact workflow that builds a deterministic runtime extension zip, smoke-installs the extension, and can open the bundled `bigsmartben/spec-kit` integration PR.
- Document the local extension package build command for `dist/repository-governance.zip`.
- Add repository extension governance documentation for command, template, script, path-safety, package-boundary, and verification rules.
- Add a Spec Kit Agent Adapter layer and scenario capability index for repository-local skills and MCP-backed external tool evidence, with MCP config candidates treated as evidence only and runtime enumeration required before use.

## [2.0.0] - 2026-05-25

### Changed

- Reposition the extension as a Repository Governance Framework generator.
- Rename runtime command, template, and helper files to repository-governance while preserving the Spec Kit command/template/script separation.
- Add a top-level vertical SSOT registry and missing-SSOT handling rules without embedding architecture methodology in the top-level governance layer.
- Capture repository facts as vertical SSOT evidence for Architecture, Engineering, Code Style, Directory Structure, Toolchain, and Agent Harness coverage.

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
