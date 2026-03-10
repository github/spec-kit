# Changelog

<!-- markdownlint-disable MD024 -->

Recent changes to the Specify CLI and templates are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-03-10

### Added

- feat(presets): Pluggable preset system with preset catalog and template resolver
- Preset manifest (`preset.yml`) with validation for artifact, command, and script types
- `PresetManifest`, `PresetRegistry`, `PresetManager`, `PresetCatalog`, `PresetResolver` classes in `src/specify_cli/presets.py`
- CLI commands: `specify preset search`, `specify preset add`, `specify preset list`, `specify preset remove`, `specify preset resolve`, `specify preset info`
- CLI commands: `specify preset catalog list`, `specify preset catalog add`, `specify preset catalog remove` for multi-catalog management
- `PresetCatalogEntry` dataclass and multi-catalog support mirroring the extension catalog system
- `--preset` option for `specify init` to install presets during initialization
- Priority-based preset resolution: presets with lower priority number win (`--priority` flag)
- `resolve_template()` / `Resolve-Template` helpers in bash and PowerShell common scripts
- Template resolution priority stack: overrides → presets → extensions → core
- Preset catalog files (`presets/catalog.json`, `presets/catalog.community.json`)
- Preset scaffold directory (`presets/scaffold/`)
- Scripts updated to use template resolution instead of hardcoded paths
- feat(presets): Preset command overrides now propagate to agent skills when `--ai-skills` was used during init
- feat: `specify init` persists CLI options to `.specify/init-options.json` for downstream operations
- feat(extensions): support `.extensionignore` to exclude files/folders during `specify extension add` (#1781)

## [0.2.0] - 2026-03-09

### Changed

- fix: sync agent list comments with actual supported agents (#1785)
- feat(extensions): support multiple active catalogs simultaneously (#1720)
- Pavel/add tabnine cli support (#1503)
- Add Understanding extension to community catalog (#1778)
- Add ralph extension to community catalog (#1780)
- Update README with project initialization instructions (#1772)
- feat: add review extension to community catalog (#1775)
- Add fleet extension to community catalog (#1771)
- Integration of Mistral vibe support into speckit (#1725)
- fix: Remove duplicate options in specify.md (#1765)
- fix: use global branch numbering instead of per-short-name detection (#1757)
- Add Community Walkthroughs section to README (#1766)
- feat(extensions): add Jira Integration to community catalog (#1764)
- Add Azure DevOps Integration extension to community catalog (#1734)
- Fix docs: update Antigravity link and add initialization example (#1748)
- fix: wire after_tasks and after_implement hook events into command templates (#1702)
- make c ignores consistent with c++ (#1747)
- chore: bump version to 0.1.13 (#1746)
- feat: add kiro-cli and AGENT_CONFIG consistency coverage (#1690)
- feat: add verify extension to community catalog (#1726)
- Add Retrospective Extension to community catalog README table (#1741)
- fix(scripts): add empty description validation and branch checkout error handling (#1559)
- fix: correct Copilot extension command registration (#1724)
- fix(implement): remove Makefile from C ignore patterns (#1558)
- Add sync extension to community catalog (#1728)
- fix(checklist): clarify file handling behavior for append vs create (#1556)
- fix(clarify): correct conflicting question limit from 10 to 5 (#1557)
- chore: bump version to 0.1.12 (#1737)
- fix: use RELEASE_PAT so tag push triggers release workflow (#1736)
- fix: release-trigger uses release branch + PR instead of direct push to main (#1733)
- fix: Split release process to sync pyproject.toml version with git tags (#1732)

## [0.1.14] - 2026-03-09

### Added

- feat: add Tabnine CLI agent support
- **Multi-Catalog Support (#1707)**: Extension catalog system now supports multiple active catalogs simultaneously via a catalog stack
  - New `specify extension catalog list` command lists all active catalogs with name, URL, priority, and `install_allowed` status
  - New `specify extension catalog add` and `specify extension catalog remove` commands for project-scoped catalog management
  - Default built-in stack includes `catalog.json` (default, installable) and `catalog.community.json` (community, discovery only) — community extensions are now surfaced in search results out of the box
  - `specify extension search` aggregates results across all active catalogs, annotating each result with source catalog
  - `specify extension add` enforces `install_allowed` policy — extensions from discovery-only catalogs cannot be installed directly
  - Project-level `.specify/extension-catalogs.yml` and user-level `~/.specify/extension-catalogs.yml` config files supported, with project-level taking precedence
  - `SPECKIT_CATALOG_URL` environment variable still works for backward compatibility (replaces full stack with single catalog)
  - All catalog URLs require HTTPS (HTTP allowed for localhost development)
  - New `CatalogEntry` dataclass in `extensions.py` for catalog stack representation
  - Per-URL hash-based caching for non-default catalogs; legacy cache preserved for default catalog
  - Higher-priority catalogs win on merge conflicts (same extension id in multiple catalogs)
  - 13 new tests covering catalog stack resolution, merge conflicts, URL validation, and `install_allowed` enforcement
  - Updated RFC, Extension User Guide, and Extension API Reference documentation

## [0.1.13] - 2026-03-03

### Changed

- feat: add kiro-cli and AGENT_CONFIG consistency coverage (#1690)
- feat: add verify extension to community catalog (#1726)
- Add Retrospective Extension to community catalog README table (#1741)
- fix(scripts): add empty description validation and branch checkout error handling (#1559)
- fix: correct Copilot extension command registration (#1724)
- fix(implement): remove Makefile from C ignore patterns (#1558)
- Add sync extension to community catalog (#1728)
- fix(checklist): clarify file handling behavior for append vs create (#1556)
- fix(clarify): correct conflicting question limit from 10 to 5 (#1557)
- chore: bump version to 0.1.12 (#1737)
- fix: use RELEASE_PAT so tag push triggers release workflow (#1736)
- fix: release-trigger uses release branch + PR instead of direct push to main (#1733)
- fix: Split release process to sync pyproject.toml version with git tags (#1732)


## [0.1.13] - 2026-03-03

### Fixed

- **Copilot Extension Commands Not Visible**: Fixed extension commands not appearing in GitHub Copilot when installed via `specify extension add --dev`
  - Changed Copilot file extension from `.md` to `.agent.md` in `CommandRegistrar.AGENT_CONFIGS` so Copilot recognizes agent files
  - Added generation of companion `.prompt.md` files in `.github/prompts/` during extension command registration, matching the release packaging behavior
  - Added cleanup of `.prompt.md` companion files when removing extensions via `specify extension remove`
- Fixed a syntax regression in `src/specify_cli/__init__.py` in `_build_ai_assistant_help()` that broke `ruff` and `pytest` collection in CI.
## [0.1.12] - 2026-03-02

### Changed

- fix: use RELEASE_PAT so tag push triggers release workflow (#1736)
- fix: release-trigger uses release branch + PR instead of direct push to main (#1733)
- fix: Split release process to sync pyproject.toml version with git tags (#1732)


## [0.1.10] - 2026-03-02

### Fixed

- **Version Sync Issue (#1721)**: Fixed version mismatch between `pyproject.toml` and git release tags
  - Split release process into two workflows: `release-trigger.yml` for version management and `release.yml` for artifact building
  - Version bump now happens BEFORE tag creation, ensuring tags point to commits with correct version
  - Supports both manual version specification and auto-increment (patch version)
  - Git tags now accurately reflect the version in `pyproject.toml` at that commit
  - Prevents confusion when installing from source

## [0.1.9] - 2026-02-28

### Changed

- Updated dependency: bumped astral-sh/setup-uv from 6 to 7

## [0.1.8] - 2026-02-28

### Changed

- Updated dependency: bumped actions/setup-python from 5 to 6

## [0.1.7] - 2026-02-27

### Changed

- Updated outdated GitHub Actions versions
- Documented dual-catalog system for extensions

### Fixed

- Fixed version command in documentation

### Added

- Added Cleanup Extension to README
- Added retrospective extension to community catalog

## [0.1.6] - 2026-02-23

### Fixed

- **Parameter Ordering Issues (#1641)**: Fixed CLI parameter parsing issue where option flags were incorrectly consumed as values for preceding options
  - Added validation to detect when `--ai` or `--ai-commands-dir` incorrectly consume following flags like `--here` or `--ai-skills`
  - Now provides clear error messages: "Invalid value for --ai: '--here'"
  - Includes helpful hints suggesting proper usage and listing available agents
  - Commands like `specify init --ai-skills --ai --here` now fail with actionable feedback instead of confusing "Must specify project name" errors
  - Added comprehensive test suite (5 new tests) to prevent regressions

## [0.1.5] - 2026-02-21

### Fixed

- **AI Skills Installation Bug (#1658)**: Fixed `--ai-skills` flag not generating skill files for GitHub Copilot and other agents with non-standard command directory structures
  - Added `commands_subdir` field to `AGENT_CONFIG` to explicitly specify the subdirectory name for each agent
  - Affected agents now work correctly: copilot (`.github/agents/`), opencode (`.opencode/command/`), windsurf (`.windsurf/workflows/`), codex (`.codex/prompts/`), kilocode (`.kilocode/workflows/`), q (`.amazonq/prompts/`), and agy (`.agent/workflows/`)
  - The `install_ai_skills()` function now uses the correct path for all agents instead of assuming `commands/` for everyone

## [0.1.4] - 2026-02-20

### Fixed

- **Qoder CLI detection**: Renamed `AGENT_CONFIG` key from `"qoder"` to `"qodercli"` to match the actual executable name, fixing `specify check` and `specify init --ai` detection failures

## [0.1.3] - 2026-02-20

### Added

- **Generic Agent Support**: Added `--ai generic` option for unsupported AI agents ("bring your own agent")
  - Requires `--ai-commands-dir <path>` to specify where the agent reads commands from
  - Generates Markdown commands with `$ARGUMENTS` format (compatible with most agents)
  - Example: `specify init my-project --ai generic --ai-commands-dir .myagent/commands/`
  - Enables users to start with Spec Kit immediately while their agent awaits formal support

## [0.0.102] - 2026-02-20

- fix: include 'src/**' path in release workflow triggers (#1646)

## [0.0.101] - 2026-02-19

- chore(deps): bump github/codeql-action from 3 to 4 (#1635)

## [0.0.100] - 2026-02-19

- Add pytest and Python linting (ruff) to CI (#1637)
- feat: add pull request template for better contribution guidelines (#1634)

## [0.0.99] - 2026-02-19

- Feat/ai skills (#1632)

## [0.0.98] - 2026-02-19

- chore(deps): bump actions/stale from 9 to 10 (#1623)
- feat: add dependabot configuration for pip and GitHub Actions updates (#1622)

## [0.0.97] - 2026-02-18

- Remove Maintainers section from README.md (#1618)

## [0.0.96] - 2026-02-17

- fix: typo in plan-template.md (#1446)

## [0.0.95] - 2026-02-12

- Feat: add a new agent: Google Anti Gravity (#1220)

## [0.0.94] - 2026-02-11

- Add stale workflow for 180-day inactive issues and PRs (#1594)
