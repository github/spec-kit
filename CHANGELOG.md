# Changelog

<!-- markdownlint-disable MD024 -->

Recent changes to the InfraKit CLI and templates are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Personas rewritten — first 50 lines load-bearing, all files ≤265 lines.** The five persona files (`cloud_solutions_engineer.md`, `cloud_architect.md`, `cloud_security_engineer.md`, `terraform_engineer.md`, `crossplane_engineer.md`) totalled 2,147 lines before — now 1,063 (cut in half). The first ~50 lines of each now packs everything the model conditions on hardest: identity, scope, what they DON'T own (with explicit hand-off targets), what files they must read, and the hard rules. Everything else is reference material. Removed: long table-of-contents lists, ASCII flow diagrams, duplicate examples, multi-paragraph rationale for every rule, and the `MUST` / `CRITICAL` / `WAIT` all-caps shouting that frontier models don't respond to better than calm prose.

- **Claude Code subagents are now real subagents, not role-play.** On Claude Code, the persona files are registered as **custom subagent types** at `.claude/agents/<persona-name>.md`. The multi-persona commands invoke them via `Task(subagent_type=cloud-architect, …)` with a one-paragraph delegation prompt; the persona file is the subagent's system prompt, the report contract is in the persona, and the orchestrator never sees the architect's reasoning steps — only the final report. New `claude_subagents` extras hook in `AGENT_CONFIG` drives the rendering; new tests cover the layout. Codex / Gemini / Copilot / generic agents keep the inline fallback as before (no custom-subagent primitive available there).

- **Scoped supported AI agents from 19 down to 5**. The supported set is now: **Claude Code**, **Codex CLI**, **Gemini CLI**, **GitHub Copilot**, and a **generic** fallback for bring-your-own-agent setups. Dropped: cursor-agent, qwen, opencode, windsurf, kilocode, auggie, codebuddy, qodercli, roo, q (Amazon Q), amp, shai, agy, bob. The wider agent matrix accumulated faster than it could be tested end-to-end; per-agent prompt quality drifted because no one was running the workflow against 19 harnesses. The cap is now five agents that are tested on every release. If you need first-class support for another agent, open an issue. Existing user projects on dropped agents continue to work — the prompts they already have don't move; only fresh `infrakit init` is constrained.

- **Multi-persona commands now invoke real subagents on agents that support them.** The four multi-persona commands (`/infrakit:create_terraform_code`, `/infrakit:new_composition`, `/infrakit:update_terraform_code`, `/infrakit:update_composition`) previously asked the parent agent to "adopt the X persona" inline — which produced role-play rather than real context isolation. On Claude Code, each read-only review phase (Cloud Architect, Cloud Security Engineer) now delegates to a fresh subagent via the `Task` tool, with the persona file as the subagent's system prompt and a structured-report return contract. The interactive Cloud Solutions Engineer phase still runs inline because subagents can't pause for user input. For Codex / Gemini / Copilot / generic agents (no `Task` primitive), the prompts include an explicit inline fallback that marks the persona-switch boundary in the agent's output. New `supports_subagents` field in `AGENT_CONFIG` is the source of truth.

- **Split `src/infrakit_cli/__init__.py` into focused modules**. The 1,837-line megafile is now 11 modules of 100–600 lines each (`cli.py`, `bootstrap.py`, `skills.py`, `mcp.py`, `git_utils.py`, `tools.py`, `tracker.py`, `interactive.py`, `banner.py`, `console.py`, `github_api.py`). `__init__.py` is now an explicit re-export shim with `__all__` so existing imports (`from infrakit_cli import app`, etc.) continue to work. No behaviour change.

- **Dropped the "Constraint-Driven Development" branding**. InfraKit is now described as "spec-kit for IaC, with a multi-persona pipeline" — a more honest framing that credits [spec-kit](https://github.com/github/spec-kit) for the workflow shape and reserves InfraKit's claims for its actual contribution (the four-persona Cloud Solutions Engineer → Architect → Security → IaC Engineer pipeline). The CDD name appeared only in marketing and docs; prompts and runtime code were already neutral. The methodology document at `constraint-driven.md` keeps its filename (URL stability) but reads as Spec-Driven Development with InfraKit-specific additions.

- **Single-artifact release**. Templates and prompts now ship inside the `infrakit-cli` PyPI wheel instead of as 76 per-agent GitHub release ZIPs (19 agents × 2 IaC × 2 scripts). `infrakit init` performs all per-agent layout transformations (folder placement, TOML wrapping, Copilot prompt pairs, VS Code settings) at install time from the bundled prompts. **Effects**:
  - `infrakit init` now runs entirely offline; no network calls.
  - `--github-token` and `--skip-tls` flags are removed (templates no longer download).
  - Existing user projects continue to work — the prompts they already have in `.claude/commands/` (or equivalent) are unchanged. Re-running `infrakit init --here` will re-materialize the latest in-package prompts.

- **Full walkthrough examples**. `examples/terraform/` and `examples/crossplane/` now contain complete end-to-end runs (config, spec, plan, tasks, reviews, generated code) for an AWS S3 secure-bucket module and an `XPostgreSQLInstance` composition respectively.

### Removed

- Per-agent GitHub release ZIPs (`infrakit-template-<agent>-<iac>-<script>-vX.Y.Z.zip`). Install the CLI from PyPI (`pip install infrakit-cli` or `uv pip install infrakit-cli`) and run `infrakit init`.
- The `--github-token` and `--skip-tls` flags on `infrakit init` (templates are now bundled in the wheel).
- Six unused root template files (`plan-template.md`, `spec-template.md`, `tasks-template.md`, `agent-file-template.md`, `checklist-template.md`, `tagging-constraint-template.md`) and ten helper scripts (`setup-plan.sh/.ps1`, `create-new-feature.sh/.ps1`, `update-agent-context.sh/.ps1`, `check-prerequisites.sh/.ps1`, `common.sh/.ps1`) that fed them. None were referenced by any current InfraKit prompt.

### Added

- **Auto-generated Task Lists**: `/infrakit:plan` now automatically generates `tasks.md` after the user accepts the plan. Tasks are checkbox items (`- [ ]`) that `/infrakit:implement` marks off as it executes. No separate `/infrakit:tasks` command needed.

- **Post-Implementation Artifacts**: `/infrakit:implement` now writes three artifacts after all tasks complete:
  - `.infrakit_context.md` — records the resource interface (variables, outputs, resources provisioned)
  - `.infrakit_changelog.md` — appends a structured entry (change type, summary, ADD/MODIFY/REMOVE breakdown, state impact)
  - `infrakit_composition_contract.md` / `.infrakit_terraform_contract.md` — regenerated from the freshly-written code and presented for review

- **Contract File Bootstrapping**: `/infrakit:update_composition` and `/infrakit:update_terraform_code` now check for `.infrakit_context.md`, `.infrakit_changelog.md`, and the resource contract file at the start. If any are missing but the implementation code exists, they are generated from the code and presented for user review before the spec update begins.

- **Iterative Requirements Clarification**: The Cloud Solutions Engineer in update commands now asks clarifying questions iteratively until requirements are fully understood before writing `spec.md`. A completion gate ("Are these requirements fully clear?") must pass before handing off to the Cloud Architect.

- **Multi-Option Architecture Review**: The Cloud Architect now presents 2–3 named design options with trade-off tables (complexity, cost, flexibility, risk) for the user to choose from, rather than a single recommendation.

- **Track Path Migration**: All track directories now live under `.infrakit_tracks/tracks/<track-name>/` and the registry is at `.infrakit_tracks/tracks.md`. Previously these were under `.infrakit/tracks/`. Projects initialized with an older version should move these directories manually.

### Removed

- **`/infrakit:tasks` command**: Removed as a standalone command. Task generation is now integrated into `/infrakit:plan` — after the user accepts the plan, `tasks.md` is auto-generated with no extra step required. The workflow is now `plan → implement` instead of `plan → tasks → implement`.

### Changed

- **Changelog timing**: The changelog (`infrakit_changelog.md`) is now written by `/infrakit:implement` after successful implementation, not by the update commands during spec registration. This ensures the changelog only records what was actually built.

- **Implement prereq checks**: `/infrakit:implement` now requires all three track artifacts — `spec.md`, `plan.md`, and `tasks.md`. If any are missing, it halts with a clear error directing to the right command to generate the missing file.

- **`/infrakit:security-review` verdict messages**: Updated to direct users to `/infrakit:plan` instead of the removed `/infrakit:tasks` command.

- **`/infrakit:status` output**: Planned tracks now show `→ Run /infrakit:implement <track-name>` (tasks.md note added inline).

### Fixed

- **Terraform Release Artifacts**: Fixed Terraform zip packages not being uploaded to GitHub Releases
  - `create-github-release.sh` was hard-coded with 38 Crossplane-only file paths; Terraform packages
    built by `create-release-packages.sh` were silently omitted from every release since v0.1.7
  - Replaced hard-coded list with dynamic discovery: uploads all `infrakit-template-*-$VERSION.zip`
    files from `.genreleases/`, covering all agents × IaC tools × script types automatically
  - Added guard that exits with a clear error if no packages are found in `.genreleases/`

- **Test Coverage**: Added `implement.md` to all parametrized test lists in `TestTerraformCommandFilesExist`
  and `TestTerraformCommandFileFrontmatter` — the file existed and was registered in `iac_config.py`
  but was absent from the test suite

## [0.1.9] - 2026-04-07

### Added

- **Roo Code Support**: Added `roo` (Roo Code) to the supported AI assistants list
- **Documentation Updates**: Synchronized all documentation (README, AGENTS.md, and docs/) with the latest code features
  - Updated `README.md` and `AGENTS.md` with latest agent directories and formats
  - Updated `docs/index.md` and others to reflect full Terraform support
  - Updated `infrakit init` help text with all supported agents

## [0.1.8] - 2026-04-07

### Changed

- **Release Script Cleanup**: Removed dead `technical-reference` copy blocks from release scripts
  (PR #11) — technical reference docs no longer exist in the repository

## [0.1.7] - 2026-04-07

### Added

- **Terraform IaC Support**: Added full Terraform support as a second IaC tool alongside Crossplane
  - New `--iac terraform` option in `infrakit init` bootstraps projects with Terraform-specific workflows
  - New commands: `create_terraform_code`, `update_terraform_code`, `plan`, `review`
  - `create_terraform_code`: Multi-phase Cloud Solutions Engineer → Architect Review → Security Review → spec confirmation workflow for new Terraform modules
  - `update_terraform_code`: Scans existing `.tf` files to reconstruct context, classifies changes (Additive/Behavioral/Breaking), generates `spec.md` and `migration.md` for breaking changes
  - `plan`: Looks up resource arguments on `registry.terraform.io`, designs variable→resource and output→attribute mappings, writes `plan.md`
  - `review`: Reviews HCL for hardcoded secrets, encryption, tagging completeness, version pinning, variable/output descriptions, and file structure
  - New `terraform_engineer.md` agent persona for the `/implement` command
  - New `coding-style-template.md` with Terraform conventions (naming, tagging, backend, security defaults)
  - New `terraform.md` technical reference documentation
  - Updated `create-release-packages.sh` to include terraform in release packages

## [0.1.6] - 2026-02-23

### Fixed

- **Parameter Ordering Issues (#1641)**: Fixed CLI parameter parsing issue where option flags were incorrectly consumed as values for preceding options
  - Added validation to detect when `--ai` or `--ai-commands-dir` incorrectly consume following flags like `--here` or `--ai-skills`
  - Now provides clear error messages: "Invalid value for --ai: '--here'"
  - Includes helpful hints suggesting proper usage and listing available agents
  - Commands like `infrakit init --ai-skills --ai --here` now fail with actionable feedback instead of confusing "Must specify project name" errors
  - Added comprehensive test suite (5 new tests) to prevent regressions

  ## [0.1.5] - 2026-02-21

  ### Fixed

  - **AI Skills Installation Bug (#1658)**: Fixed `--ai-skills` flag not generating skill files for GitHub Copilot and other agents with non-standard command directory structures
  - Added `commands_subdir` field to `AGENT_CONFIG` to explicitly specify the subdirectory name for each agent
  - Affected agents now work correctly: copilot (`.github/agents/`), opencode (`.opencode/command/`), windsurf (`.windsurf/workflows/`), codex (`.codex/prompts/`), kilocode (`.kilocode/workflows/`), q (`.amazonq/prompts/`), and agy (`.agent/workflows/`)
  - The `install_ai_skills()` function now uses the correct path for all agents instead of assuming `commands/` for everyone

  ## [0.1.4] - 2026-02-20

  ### Fixed

  - **Qoder CLI detection**: Renamed `AGENT_CONFIG` key from `"qoder"` to `"qodercli"` to match the actual executable name, fixing `infrakit check` and `infrakit init --ai` detection failures

  ## [0.1.3] - 2026-02-20

  ### Added

  - **Generic Agent Support**: Added `--ai generic` option for unsupported AI agents ("bring your own agent")
  - Requires `--ai-commands-dir <path>` to specify where the agent reads commands from
  - Generates Markdown commands with `$ARGUMENTS` format (compatible with most agents)
  - Example: `infrakit init my-project --ai generic --ai-commands-dir .myagent/commands/`
  - Enables users to start with InfraKit immediately while their agent awaits formal support

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
