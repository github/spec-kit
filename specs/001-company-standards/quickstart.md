# Quickstart: Testing Company Standards & AGENTS.md

## Prerequisites
- `specify` CLI installed (or running from source).
- Python environment active.

## 1. Verify Template Generation
1.  Run `specify init test-project --no-git`.
2.  Check that `templates/company-standards/` is NOT created by default (it's a library feature, usually added via `specify add` or manual copy? *Correction*: The requirement says "System must provide...". If it's part of the default template, it should appear. *Clarification*: The spec implies these are templates *available* in the kit, likely copied during init or a specific command. For now, we assume they are part of the standard template set copied to `.specify/templates` or `templates/` in the new project).
3.  Check `AGENTS.md` is created in `test-project/AGENTS.md`.

## 2. Verify Agent Specifics
1.  Run `specify init cursor-project --ai cursor --no-git`.
2.  Check `cursor-project/AGENTS.md` exists.
3.  Check `cursor-project/.cursor/rules/specify-rules.mdc` exists and links to `AGENTS.md`.

## 3. Verify Context Update
1.  In `cursor-project/`, run `.specify/scripts/bash/update-agent-context.sh cursor`.
2.  Verify `AGENTS.md` is updated (check timestamp or content).
