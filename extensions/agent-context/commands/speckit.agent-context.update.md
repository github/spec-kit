---
description: "Refresh the managed Spec Kit section in coding agent context file(s)"
---

# Update Coding Agent Context

Refresh the managed Spec Kit section inside the active coding agent's context/instruction file (e.g. `CLAUDE.md`, `.github/copilot-instructions.md`, `AGENTS.md`).

## Behavior

The script reads the agent-context extension config at
`.specify/extensions/agent-context/agent-context-config.yml` to discover:

- `context_file` — the path of the coding agent context file to manage.
- `context_files` — optional project-relative paths for multiple coding agent context files. When non-empty, the script updates each listed file and the list takes precedence over `context_file`.
- `context_markers.start` / `.end` — the delimiters surrounding the managed section. Defaults to `<!-- SPECKIT START -->` and `<!-- SPECKIT END -->` when the field is missing.

It then creates, replaces, or appends the managed block so that the section points at the most recent plan path when one can be discovered (`specs/<feature>/plan.md`).

If `context_files` and `context_file` are empty, the command reports nothing to do and exits successfully. Context file paths must stay project-relative; absolute paths, Windows drive paths, backslash separators, and `..` path segments are rejected.

## Execution

- **Bash**: `.specify/extensions/agent-context/scripts/bash/update-agent-context.sh [plan_path]`
- **PowerShell**: `.specify/extensions/agent-context/scripts/powershell/update-agent-context.ps1 [plan_path]`

When `plan_path` is omitted, the script auto-detects the most recently modified `specs/*/plan.md`.
