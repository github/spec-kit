---
feature: registry
status: implemented
created: 2026-02-15
decisions:
  - 001-package-per-directory
  - 002-explicit-file-mapping
  - 003-project-level-state
  - 004-opt-in-registries
  - 005-cache-with-refresh
  - 006-explicit-on-ambiguity
---

# MiniSpec Registry Design

## Overview

A local-first package system for distributing slash commands, skills, and hooks via Git repos. Registries are opt-in — MiniSpec works out of the box without them. Teams that want to share custom extensions add Git-based registries (public or private) and install individual packages.

## User Stories

- As an enterprise engineer, I want to install approved slash commands from my company's internal registry so that my team uses consistent workflows
- As a security team lead, I want to publish vetted hooks to an internal registry so that all teams get our guardrails
- As a MiniSpec user, I want to search for community commands so that I can extend my workflow
- As an enterprise admin, I want to audit which packages are installed in a project so that I can verify compliance
- As a team in an air-gapped environment, I want to use MiniSpec without any external registry dependencies

## CLI Surface

### Registry Management

```bash
# Add a registry (Git repo URL)
minispec registry add https://github.com/acme-corp/minispec-registry.git
minispec registry add git@internal.acme.com:security/minispec-hooks.git --name acme-internal

# List configured registries
minispec registry list

# Remove a registry
minispec registry remove acme-internal

# Refresh registry cache (fetch latest from remote)
minispec registry update
minispec registry update acme-internal
```

### Package Operations

```bash
# Search across all registries
minispec search protect-main
minispec search --type hook
minispec search --type command --agent claude

# Install a package
minispec install protect-main
minispec install protect-main --registry acme-internal
minispec install protect-main@1.0.0
minispec install protect-main --refresh    # force-fetch registry before install

# List installed packages
minispec list

# Uninstall a package
minispec uninstall protect-main

# Update packages
minispec update protect-main
minispec update --all
```

## Components

### Registry Repo Structure

A registry is a Git repo with this layout:

```
my-registry/
├── registry.yaml              # registry metadata
└── packages/
    ├── protect-main/
    │   ├── package.yaml        # package metadata
    │   ├── hook.sh             # package files
    │   └── README.md
    └── my-command/
        ├── package.yaml
        ├── command.md
        └── README.md
```

#### `registry.yaml`

```yaml
name: acme-internal
description: ACME Corp approved MiniSpec extensions
maintainers:
  - security-team@acme.com
```

#### `package.yaml`

```yaml
name: protect-main
version: 1.0.0
type: hook                      # command | skill | hook
description: Blocks commits to protected branches
author: security-team
license: MIT

# AI agent compatibility
agents:
  - claude
  - cursor
  - copilot

# MiniSpec version requirement
minispec: ">=0.0.3"

# File installation mapping
files:
  - source: hook.sh
    target: .minispec/hooks/scripts/protect-main.sh
  - source: settings.json
    target: .claude/settings.json
    merge: true                 # merge into existing, don't overwrite

# Audit trail
review:
  status: approved              # approved | pending | rejected
  reviewed-by: security-team
  reviewed-at: 2026-02-01
```

### Project State File

`.minispec/registries.yaml` — committed to version control, shared across team.

```yaml
registries:
  - name: acme-internal
    url: git@internal.acme.com:security/minispec-hooks.git
    added-at: 2026-02-15

installed:
  - name: protect-main
    version: 1.0.0
    type: hook
    registry: acme-internal
    installed-at: 2026-02-15
    files:
      - .minispec/hooks/scripts/protect-main.sh
      - .claude/settings.json
```

### Registry Cache

Location: `~/.cache/minispec/registries/<registry-name>/`

Shallow Git clones of registry repos, cached between sessions. Refreshed explicitly via `--refresh` flag or `minispec registry update`.

## Installation Flow

1. User runs `minispec install protect-main`
2. Read `.minispec/registries.yaml` for configured registries
3. For each registry, check cache (clone/fetch if missing or `--refresh`)
4. Search `packages/*/package.yaml` for matching name
5. If found in multiple registries — error, require `--registry` flag
6. ~~Validate `minispec` version compatibility~~ (deferred — field is stored but not enforced)
7. ~~Check `agents` compatibility with current project~~ (deferred — field is stored but not enforced)
8. Copy files per `files` mapping (merge where `merge: true`)
9. Update `installed` section in `.minispec/registries.yaml`

## Relationship to `minispec init`

- `minispec init` bundles core commands and works without registries
- Registries are opt-in — no default registry configured
- Air-gapped environments work without any registry
- Registries extend, they don't replace the core

## Open Questions

- Should `package.yaml` support dependencies between packages?
- Should there be a `minispec validate` command that checks installed packages against their registry versions?
- ~~How should `merge: true` handle conflicts in JSON/YAML files?~~ **Resolved**: Uses deep merge with "last writer wins" — nested dicts are merged recursively, scalars and lists from the package overwrite existing values. See `_deep_merge()` in `registry.py`.
- Should packages support pre/post install scripts, or is that a security risk?
