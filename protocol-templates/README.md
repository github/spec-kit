# Protocol Templates

This directory contains **universal protocol files** that are copied to generated projects but **NOT** stored in `.specify/memory/`.

## Purpose

Protocol templates define how agents interact with Spec Kit projects in a standardized way. Unlike `memory/` templates which are project-specific and editable, protocol templates are:

- **Universal**: Apply to all Spec Kit projects
- **Non-editable**: Not meant to be customized per-project
- **Agent-agnostic**: Work across all AI coding assistants

## Files

### AGENTS.md

Standard agent documentation delivered to users. It now includes:

- System Instructions (10‑part prompt structure)
- Prompt Evaluation Flywheel (Analyze→Measure→Improve) with documentation hooks
- Default policies and execution contract
- Compact binary grader template (copy/paste)
- Automatic PHR creation rules and ADR suggestion workflow
- Spec‑Driven Development commands and project structure

**Destination in release packages**: Project root (`AGENTS.md`). It may also be transformed into per‑agent files during `specify init`:

- `GEMINI.md`, `QWEN.md`, `CLAUDE.md` (root)
- `.cursor/rules/guidelines.md` (Cursor)

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
4. Update per‑agent generation logic in `src/specify_cli/__init__.py` if needed
5. Document in this README
