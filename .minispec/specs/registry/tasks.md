---
feature: registry
status: complete
created: 2026-02-15
chunk_size: adaptive
total_tasks: 10
estimated_lines: 520
---

# MiniSpec Registry Tasks

## Overview

Implement a local-first package system for distributing slash commands, skills, and hooks via Git repos. Registries are opt-in, project-level, and support both public and private sources.

## Task List

### Foundation

#### Task 1: Registry state model + YAML read/write

- **Estimate:** ~60 lines
- **Files:** `src/minispec_cli/registry.py`
- **Description:** Data classes for registry config (name, url), installed packages (name, version, type, registry, files), and package.yaml schema (name, version, type, description, agents, minispec, files, review). Functions to read/write `.minispec/registries.yaml`. Create file if it doesn't exist.
- **Depends on:** None
- **Acceptance:** Can round-trip read/write registries.yaml with registries and installed packages

#### Task 2: Registry cache manager

- **Estimate:** ~50 lines
- **Files:** `src/minispec_cli/registry.py`
- **Description:** Clone registry Git repos to `~/.cache/minispec/registries/<name>/` using shallow clone. Fetch/pull when refresh requested. Check if cache exists and is valid. Handle Git errors gracefully (auth failures, network issues).
- **Depends on:** Task 1
- **Acceptance:** Can clone a Git repo to cache, detect existing cache, refresh on demand

#### Task 3: Package discovery

- **Estimate:** ~40 lines
- **Files:** `src/minispec_cli/registry.py`
- **Description:** Scan cached registry for `packages/*/package.yaml`. Parse each package.yaml into data class. Return list of available packages with their registry source. Handle malformed package.yaml gracefully (skip with warning).
- **Depends on:** Task 2
- **Acceptance:** Given a cached registry, returns list of packages with parsed metadata

### Core CLI Commands

#### Task 4: `minispec registry` subcommands

- **Estimate:** ~80 lines
- **Files:** `src/minispec_cli/__init__.py`
- **Description:** Add `registry` command group with subcommands: `add <url> [--name]` (auto-derive name from URL if not provided), `list` (table of configured registries), `remove <name>`, `update [name]` (refresh cache, or all if no name). Rich output with status feedback.
- **Depends on:** Task 1, Task 2
- **Acceptance:** Can add/list/remove registries and refresh cache via CLI

#### Task 5: `minispec search`

- **Estimate:** ~50 lines
- **Parallel:** Can run with Task 4
- **Files:** `src/minispec_cli/__init__.py`
- **Description:** Search packages across all configured registries by name substring. Filter by `--type` (command/skill/hook) and `--agent`. Rich table output: name, version, type, description, registry, review status. Show "no registries configured" if none exist.
- **Depends on:** Task 3
- **Acceptance:** Can search and filter packages across registries with formatted output

#### Task 6: `minispec install`

- **Estimate:** ~80 lines
- **Files:** `src/minispec_cli/__init__.py`
- **Description:** Resolve package by name across registries. Error if found in multiple (suggest `--registry`). Support `name@version` syntax. Check minispec version compatibility. Check agent compatibility with current project. Copy files per explicit mapping. Deep merge for `merge: true` files. Update installed section in registries.yaml. Support `--refresh` flag to fetch before install. Support `--registry` flag for explicit source.
- **Depends on:** Task 3, Task 9
- **Acceptance:** Can install a package from a registry, files land in correct locations, state tracked

#### Task 7: `minispec list` (installed packages)

- **Estimate:** ~30 lines
- **Parallel:** Can run with Task 8
- **Files:** `src/minispec_cli/__init__.py`
- **Description:** Read installed packages from registries.yaml. Rich table: name, version, type, registry, installed date. Show "no packages installed" if empty.
- **Depends on:** Task 1
- **Acceptance:** Shows installed packages in formatted table

#### Task 8: `minispec uninstall`

- **Estimate:** ~40 lines
- **Parallel:** Can run with Task 7
- **Files:** `src/minispec_cli/__init__.py`
- **Description:** Remove files tracked in the installed package's file list. Update registries.yaml to remove from installed section. Warn if files were modified since install. Confirm before removing.
- **Depends on:** Task 1
- **Acceptance:** Removes installed files and updates state

### Integration & Polish

#### Task 9: File merge logic for JSON/YAML

- **Estimate:** ~50 lines
- **Files:** `src/minispec_cli/registry.py`
- **Description:** Deep merge for JSON files (reuse/adapt existing settings.json merge from init). Deep merge for YAML files. Handle `merge: true` flag from package.yaml file mapping. Create target file if it doesn't exist. Preserve existing content when merging.
- **Depends on:** None
- **Acceptance:** Can deep-merge a package's JSON/YAML into existing project files without data loss

#### Task 10: `minispec update`

- **Estimate:** ~40 lines
- **Files:** `src/minispec_cli/__init__.py`
- **Description:** Compare installed version against latest in registry. Re-install if newer version available. `--all` flag to update everything. Show what would be updated before proceeding. Refresh registry cache before checking.
- **Depends on:** Task 6
- **Acceptance:** Detects outdated packages and re-installs latest version

## Notes

- The existing `minispec init` flow is unchanged — registries are purely additive
- File merge logic in Task 9 should reuse the JSON deep merge already in `__init__.py` (used for `.vscode/settings.json`)
- Package dependencies between packages are deferred to a future iteration
- Pre/post install scripts are deferred (security implications need design)

## Progress

- [x] Task 1: Registry state model + YAML read/write
- [x] Task 2: Registry cache manager
- [x] Task 3: Package discovery
- [x] Task 4: `minispec registry` subcommands
- [x] Task 5: `minispec search`
- [x] Task 6: `minispec install`
- [x] Task 7: `minispec list` (installed packages)
- [x] Task 8: `minispec uninstall`
- [x] Task 9: File merge logic for JSON/YAML
- [x] Task 10: `minispec update`
