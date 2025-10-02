# Protocol Templates

This directory contains **universal protocol files** that are copied to generated projects but **NOT** stored in `.specify/memory/`.

## Purpose

Protocol templates define how agents interact with Spec Kit projects in a standardized way. Unlike `memory/` templates which are project-specific and editable, protocol templates are:

- **Universal**: Apply to all Spec Kit projects
- **Non-editable**: Not meant to be customized per-project
- **Agent-agnostic**: Work across all AI coding assistants

## Files

### AGENTS.md

Standard agent documentation file (see https://agents.md/) that explains:

- Automatic PHR creation (comprehensive knowledge capture)
- ADR suggestion workflow (architectural decision records)
- Spec-Driven Development commands
- Project structure and workflow patterns

**Destination in release packages**: Project root (`AGENTS.md`)  
**NOT copied to**: `.specify/memory/` (keeps it clean)

## Why Separate from memory/?

| Directory               | Purpose                                                  | Destination        | User Editable     |
| ----------------------- | -------------------------------------------------------- | ------------------ | ----------------- |
| **memory/**             | Project-specific templates (constitution, command-rules) | `.specify/memory/` | Yes (per project) |
| **protocol-templates/** | Universal agent protocols (AGENTS.md)                    | Project root       | No (standardized) |

This separation ensures:

1. `.specify/memory/` only contains project-customizable files
2. AGENTS.md at project root is recognized by all agents
3. No confusion about which files are templates vs protocols
4. Clean, purposeful directory structure

## Adding New Protocol Templates

When adding new universal protocol files:

1. Place them in this directory
2. Update `create-release-packages.sh` to copy them
3. Choose appropriate destination (project root or subdirectory)
4. Document in this README
