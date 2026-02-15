---
feature: registry-builder
status: planned
created: 2026-02-15
chunk_size: adaptive
total_tasks: 4
estimated_lines: 370
---

# Registry Builder Tasks

## Overview

Implement `minispec init-registry` CLI command and the `/minispec.registry` slash command skill for creating and managing MiniSpec package registries.

## Task List

### Foundation

#### Task 1: Skill template — `/minispec.registry`
- **Estimate:** ~200 lines
- **Files:** `templates/commands/registry.md`
- **Description:** Write the full slash command skill template. Covers context detection (empty registry vs. existing packages), create-package interactive flow, validate flow (three-tier), and update-metadata flow. Embeds knowledge of package.yaml schema, agent folder conventions, MiniSpec template patterns (frontmatter, $ARGUMENTS, phases), hook/command/skill content examples, and file mapping per agent.
- **Depends on:** None
- **Acceptance:** Skill template follows existing command template patterns (YAML frontmatter, $ARGUMENTS placeholder, phased execution). Contains all knowledge needed for a registry author to create packages without external documentation.

#### Task 2: `minispec init-registry` CLI command
- **Estimate:** ~80 lines
- **Files:** `src/minispec_cli/__init__.py`
- **Description:** Add top-level `init-registry` command. Args: `name` (optional if `--here`), `--ai` (with interactive picker), `--here`, `--no-git`, `--force`. Generates `registry.yaml`, `packages/` dir (with `.gitkeep`), `README.md`, and installs skill template into agent-specific folder. Runs `git init` when no existing repo detected. Shows success panel with next steps. Reuses existing `AGENT_CONFIG`, `select_with_arrows`, `is_git_repo`, `init_git_repo`.
- **Depends on:** Task 1
- **Acceptance:** `minispec init-registry my-registry --ai claude` creates correct directory structure with all files. Interactive picker works when `--ai` omitted. Git init runs when appropriate.

### Integration

#### Task 3: Tests for `init-registry`
- **Estimate:** ~60 lines
- **Files:** `tests/test_init_registry.py`
- **Description:** Test scaffold generation (correct files and structure created), `--here` mode, git init behavior (skipped when repo exists, runs when not), agent folder placement for different agents, `--force` flag with non-empty directory.
- **Depends on:** Task 2
- **Acceptance:** All tests pass. Core scaffold generation logic is covered.

#### Task 4: README and docs
- **Estimate:** ~30 lines
- **Parallel:** Can run with Task 3
- **Files:** `README.md`
- **Description:** Add `init-registry` to README commands table. Add brief section on creating registries (after the Package Registry section). Mention the `/minispec.registry` skill.
- **Depends on:** Task 1
- **Acceptance:** README documents the new command and the registry authoring workflow.

## Notes
- Task 1 is deliberately large because the skill template is a cohesive prompt document — splitting it would lose context
- The skill template goes in `templates/commands/registry.md` and gets installed by the CLI command (not via the release build pipeline)
- The build pipeline in `.github/workflows/` does NOT need changes — `init-registry` generates the skill inline
- Package testing/dry-run mode is deferred (noted as open question in design)

## Progress
- [x] Task 1: Skill template — `/minispec.registry`
- [x] Task 2: `minispec init-registry` CLI command
- [x] Task 3: Tests for `init-registry`
- [x] Task 4: README and docs
