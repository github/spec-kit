# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to the Specify CLI will be documented in this file.

The format is based on Keep a Changelog (https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning (https://semver.org/spec/v2.0.0.html).

## [LATEST_VERSION] - RELEASE_DATE

### Added

- Support for using `.` as a shorthand for current directory in `specify init .` command, equivalent to `--here` flag but more intuitive for users

### Notes

- This release note reflects upstream improvements; your local fork also includes `.specs/.specify` consolidation and template source override features below.

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

## [0.0.17] - 2025-09-22

### Added

- New `/clarify` command template to surface up to 5 targeted clarification questions for an existing spec and persist answers into a Clarifications section in the spec.

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
### Changed

- Warning displayed to ensure that folks are aware that they might need to add their agent folder to `.gitignore`.
## [0.0.12] - 2025-09-21

### Changed

- Added additional context for OpenAI Codex users - they need to set an additional environment variable, as described in [#417](https://github.com/github/spec-kit/issues/417).
## [0.0.11] - 2025-09-20

### Added

- Codex CLI support (thank you [@honjo-hiroaki-gtt](https://github.com/honjo-hiroaki-gtt) for the contribution in [#14](https://github.com/github/spec-kit/pull/14))
## [0.0.10] - 2025-09-20

### Fixed

- Addressed [#378](https://github.com/github/spec-kit/issues/378) where a GitHub token may be attached to the request when it was empty.
## [0.0.9] - 2025-09-19

### Changed

- Improved agent selector UI with cyan highlighting for agent keys and gray parentheses for full names
## [0.0.8] - 2025-09-19

### Added

- Windsurf IDE support as additional AI assistant option (thank you [@raedkit](https://github.com/raedkit) for the work in [#151](https://github.com/github/spec-kit/pull/151))
### Changed

- Updated README with Windsurf examples and GitHub token usage
## [0.0.7] - 2025-09-18

### Changed

- Updated command instructions in the CLI.

## [0.0.6] - 2025-09-17

### Added


## [0.0.5] - 2025-09-17

### Added


## [0.0.4] - 2025-09-14

### Added


### Fixed

N/A

### Changed

N/A
