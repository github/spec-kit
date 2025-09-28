# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to the Specify CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.22] - 2025-09-27

## [0.0.23] - 2025-09-28

### Added

- Smoke test automation script `scripts/bash/smoke-copilot.sh` to provision a temporary Copilot project and assert required prompt and internal template files exist.
- CI workflow `ci-smoke.yml` to build release template archives for all agents/script variants and verify each archive contains its expected command files and core internal templates.

### Changed

- Bumped CLI version to 0.0.23 to align with release template assets (previous run fetched v0.0.23 archives while CLI still reported 0.0.22).

### Notes

- Future enhancements: extend smoke script to cover additional agents and JSON output assertions; optionally add a matrix strategy job to exercise `specify init --template-path <archive>` against freshly built artifacts.

### Changed

- Default template repository now points to `Jrakru/spec-kit` instead of upstream `github/spec-kit`.
	- You can still override via `--template-repo` or `SPEC_KIT_TEMPLATE_REPO`.
	- Help text updated to reflect the new default.

## [0.0.24] - 2025-09-28

### Added

- Dynamic command discovery in post-init "Next Steps": the CLI now scans the selected agent's commands folder and lists all available slash commands (e.g., `/pprd`, `/pprd-clarify`, `/fprds`) with descriptions when present, instead of a hardcoded subset.

### Changed

- Bumped CLI version to 0.0.24.

## [0.0.21] - 2025-09-27

### Changed

- Curated prior local work into focused PRs for reviewability and safety.
	- CLI entrypoint: help/UX alignment and messaging consistency (no functional changes intended).
	- Scripts: Bash and PowerShell helpers updated for parity and declarative layout alignment.
	- Templates/Docs: synced wording and examples with the new layout and packaging flow.
	- Workflows: curated release packaging script to align agent list, rewrite paths for .specs/.specify, and improve extraction robustness.

### Internal

- Version bumped to 0.0.21 to track the curated updates. Follow-on PRs will continue workflow packaging alignment.

## [0.0.20] - 2025-09-27

### Added

- Declarative layout support via `.specs/.specify/layout.yaml` defining `spec_roots`, `folder_strategy` (`flat`/`epic`/`product`), and canonical file names (e.g., `design.md`, `fprd.md`, `tasks.md`, `pprd.md`).
- Runtime template resolver with assets override precedence (`.specs/.specify/templates/assets/*-template.md` before defaults).
- New helper scripts (Bash/PowerShell): `read-layout`, `resolve-template`, `spec-root`.

### Changed

- Plan output renamed to `design.md`; FPRD is `fprd.md`; optional legacy stub `spec.md` retained via compatibility setting.
- Packaging script relocates and rewrites prompts to the consolidated `.specs/.specify` structure and promotes `templates/layout.yaml` into packages.
- Cross-shell parity for all core helpers (`check-prerequisites`, `create-new-feature`, `setup-plan`) with JSON outputs for agent orchestration.

### Docs

- Updated README and docs/agent-assets.md to describe the new layout, overrides, and packaging workflow.

## [0.0.19] - 2025-09-24

### Added

- `--template-repo` CLI option (and `SPEC_KIT_TEMPLATE_REPO`) to pull release assets from a fork or alternate repository.
- `--template-path` CLI option (and `SPEC_KIT_TEMPLATE_PATH`) to scaffold directly from a local template ZIP or directory without hitting GitHub.

### Changed

- Template download/extraction pipeline now honors local overrides while preserving `.specs/.specify` relocation and tracker output.

## [0.0.18] - 2025-09-24

### Changed

- Consolidated all non-agent project assets under a new `/.specs/.specify` hierarchy while keeping agent folders at the repository root for IDE autodiscovery.
- Updated the Specify CLI, packaging scripts, shell/PowerShell helpers, and command templates to reference the relocated directories.
- Added migration logic and legacy fallbacks so existing projects using `.specify/` or top-level `specs/` continue to function.

## [0.0.17] - 2025-09-22

### Added

- New `/clarify` command template to surface up to 5 targeted clarification questions for an existing spec and persist answers into a Clarifications section in the spec.
- New `/analyze` command template providing a non-destructive cross-artifact discrepancy and alignment report (spec, clarifications, plan, tasks, constitution) inserted after `/tasks` and before `/implement`.
	- Note: Constitution rules are explicitly treated as non-negotiable; any conflict is a CRITICAL finding requiring artifact remediation, not weakening of principles.

## [0.0.16] - 2025-09-22

### Added

- `--force` flag for `init` command to bypass confirmation when using `--here` in a non-empty directory and proceed with merging/overwriting files.

## [0.0.15] - 2025-09-21

### Added

- Support for Roo Code.

## [0.0.14] - 2025-09-21

### Changed

- Error messages are now shown consistently.

## [0.0.13] - 2025-09-21

### Added

- Support for Kilo Code. Thank you [@shahrukhkhan489](https://github.com/shahrukhkhan489) with [#394](https://github.com/github/spec-kit/pull/394).
- Support for Auggie CLI. Thank you [@hungthai1401](https://github.com/hungthai1401) with [#137](https://github.com/github/spec-kit/pull/137).
- Agent folder security notice displayed after project provisioning completion, warning users that some agents may store credentials or auth tokens in their agent folders and recommending adding relevant folders to `.gitignore` to prevent accidental credential leakage.

### Changed

- Warning displayed to ensure that folks are aware that they might need to add their agent folder to `.gitignore`.
- Cleaned up the `check` command output.

## [0.0.12] - 2025-09-21

### Changed

- Added additional context for OpenAI Codex users - they need to set an additional environment variable, as described in [#417](https://github.com/github/spec-kit/issues/417).

## [0.0.11] - 2025-09-20

### Added

- Codex CLI support (thank you [@honjo-hiroaki-gtt](https://github.com/honjo-hiroaki-gtt) for the contribution in [#14](https://github.com/github/spec-kit/pull/14))
- Codex-aware context update tooling (Bash and PowerShell) so feature plans refresh `AGENTS.md` alongside existing assistants without manual edits.

## [0.0.10] - 2025-09-20

### Fixed

- Addressed [#378](https://github.com/github/spec-kit/issues/378) where a GitHub token may be attached to the request when it was empty.

## [0.0.9] - 2025-09-19

### Changed

- Improved agent selector UI with cyan highlighting for agent keys and gray parentheses for full names

## [0.0.8] - 2025-09-19

### Added

- Windsurf IDE support as additional AI assistant option (thank you [@raedkit](https://github.com/raedkit) for the work in [#151](https://github.com/github/spec-kit/pull/151))
- GitHub token support for API requests to handle corporate environments and rate limiting (contributed by [@zryfish](https://github.com/@zryfish) in [#243](https://github.com/github/spec-kit/pull/243))

### Changed

- Updated README with Windsurf examples and GitHub token usage
- Enhanced release workflow to include Windsurf templates

## [0.0.7] - 2025-09-18

### Changed

- Updated command instructions in the CLI.
- Cleaned up the code to not render agent-specific information when it's generic.


## [0.0.6] - 2025-09-17

### Added

- opencode support as additional AI assistant option

## [0.0.5] - 2025-09-17

### Added

- Qwen Code support as additional AI assistant option

## [0.0.4] - 2025-09-14

### Added

- SOCKS proxy support for corporate environments via `httpx[socks]` dependency

### Fixed

N/A

### Changed

N/A
