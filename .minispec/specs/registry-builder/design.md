---
feature: registry-builder
status: planned
created: 2026-02-15
decisions:
  - 007-self-contained-scaffold
  - 008-single-agent-picker
  - 009-full-authoring-partner
  - 010-top-level-init-registry
---

# Registry Builder Design

## Overview

A CLI command (`minispec init-registry`) and slash command skill (`/minispec.registry`) that together enable users to create, populate, and maintain MiniSpec package registries. The CLI scaffolds the repo structure, and the skill acts as an interactive pair programming partner for authoring packages.

## User Stories

- As a team lead, I want to quickly scaffold a registry repo so my team can start publishing internal extensions
- As a package author, I want guided help creating well-structured packages so I don't have to memorize the package.yaml schema
- As a registry maintainer, I want to validate my registry's integrity so I catch issues before consumers hit them
- As a security engineer, I want to create hook packages with proper review metadata so they pass enterprise compliance

## Components

### CLI: `minispec init-registry`

Top-level command (not a subcommand of `registry`). Generates the registry scaffold inline — no GitHub release download required.

**Arguments:**

- `name` — registry directory name (optional if `--here`)
- `--ai` — AI agent to install skill for (interactive picker if omitted)
- `--here` — initialize in current directory
- `--no-git` — skip git init
- `--force` — skip confirmation when directory not empty

**Generated structure:**

```text
my-registry/
├── registry.yaml              # name, description, maintainers
├── packages/                  # empty directory
├── README.md                  # explains registry structure and usage
└── .claude/commands/          # (or .cursor/, .gemini/, etc.)
    └── minispec.registry.md   # the registry builder skill
```

**Behavior:**

- If no git repo detected and `--no-git` not set, runs `git init`
- Uses `AGENT_CONFIG` for agent folder paths (reuse existing mapping)
- Shows success panel with next steps (open AI agent, run `/minispec.registry`)

### Skill: `/minispec.registry`

A slash command template installed into the registry repo. Context-aware with argument override.

**Modes:**

#### 1. Create Package (`/minispec.registry create-package` or auto-detected)

Interactive flow:

1. Ask for package name
2. Ask for type (command / skill / hook)
3. Ask for version (default: 1.0.0)
4. Ask for description
5. Ask which agents to support — generates correct file mappings per agent
6. Walk through file mappings (source files in package dir, target paths in consumer project)
7. Ask about review metadata (status, reviewer)
8. Ask about minispec version requirement
9. Create `packages/<name>/package.yaml`
10. **Write the actual content** — the skill knows MiniSpec template patterns:
    - For commands: frontmatter, `$ARGUMENTS`, phase-based structure
    - For hooks: shell script patterns, common guardrails
    - For skills: similar to commands but with different scope
11. Create README.md for the package

#### 2. Validate (`/minispec.registry validate` or auto-detected)

Three-tier validation:

**Tier 1 — Schema (always check):**

- `registry.yaml` exists with required fields (name, description)
- Every `packages/*/package.yaml` has required fields (name, version, type)
- Source files referenced in file mappings exist in package directory
- No duplicate package names

**Tier 2 — Quality (suggest):**

- Packages have descriptions
- Packages declare agent compatibility
- Review metadata is populated
- README exists per package
- Version follows semver

**Tier 3 — Cross-agent (if multi-agent):**

- File mappings cover all declared agents
- Target paths match agent conventions (`.claude/commands/`, `.cursor/commands/`, etc.)

#### 3. Update Metadata (`/minispec.registry` with existing registry)

- Edit `registry.yaml` fields (name, description, maintainers)
- Detected when registry exists and has packages — offer as option alongside create/validate

**Context Detection Logic:**

- No `registry.yaml` → guide through initial setup (shouldn't happen after `init-registry`, but handle gracefully)
- Empty `packages/` → suggest creating first package
- Has packages → offer create another, validate, or update metadata

### Agent Folder Conventions (embedded in skill)

The skill contains knowledge of where each agent expects files:

| Agent | Commands Path | Notes |
| ----- | --------------------- | ------------- |
| Claude | `.claude/commands/` | Markdown |
| Cursor | `.cursor/commands/` | Markdown |
| Copilot | `.github/prompts/` | Markdown |
| Gemini | `.gemini/commands/` | TOML-wrapped |
| Qwen | `.qwen/commands/` | TOML-wrapped |
| Others | `.<agent>/commands/` | Markdown |

This knowledge is baked into the skill prompt so it can generate correct `files:` mappings in `package.yaml`.

## Data Model

No new data structures needed. The skill operates on the existing `registry.yaml` and `package.yaml` schemas defined in the registry design spec.

**`registry.yaml`** (generated by CLI):

```yaml
name: my-registry
description: ""
maintainers: []
```

**`package.yaml`** (generated by skill):

```yaml
name: protect-main
version: 1.0.0
type: hook
description: Blocks commits to protected branches
agents:
  - claude
  - cursor
minispec: ">=0.1.0"
files:
  - source: hook.sh
    target: .minispec/hooks/scripts/protect-main.sh
review:
  status: pending
```

## CLI Surface

```bash
# Create a new registry repo
minispec init-registry my-registry --ai claude

# Create in current directory
minispec init-registry --here --ai claude

# Non-interactive (CI/automation)
minispec init-registry my-registry --ai claude --no-git

# Then inside the registry repo:
/minispec.registry                    # context-aware: detects state
/minispec.registry create-package     # jump directly to package creation
/minispec.registry validate           # run validation checks
```

## Relationship to Existing Features

- `minispec init` — bootstraps coding projects. `init-registry` bootstraps registry repos. No overlap.
- `minispec registry add/list/remove/update` — consumer-side registry management. Operates inside coding projects.
- `minispec install/search` — consumes packages from registries. The builder creates what install consumes.
- `/minispec.design`, `/minispec.tasks`, `/minispec.next` — NOT installed in registry repos. The registry builder skill is the only slash command needed.

## Open Questions

- Should the skill support a "test locally" mode that simulates `minispec install` from the local registry without publishing?
- Should `init-registry` support a `--template` flag to start from an existing registry structure?
