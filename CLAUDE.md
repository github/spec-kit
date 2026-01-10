# CLAUDE.md

> **Lightweight bridge** → See `AGENTS.md` for full spec-kit-max architecture, development guidelines, and upstream sync procedures.

## Quick Reference

### This is spec-kit-max

A fork of `github/spec-kit` with parallel subagent orchestration for Claude Code. Key file: `templates/commands/tasks.md`.

### Dogfooding Active

This repo manages itself:
- `.claude/commands/` → symlinks to `templates/commands/`
- Changes to templates immediately affect `/speckit.*` commands
- Use the spec-kit workflow to develop spec-kit

### Critical Paths

| Task | Key Files |
|------|-----------|
| Modify commands | `templates/commands/*.md` |
| CLI changes | `src/specify_cli/__init__.py` + bump `pyproject.toml` |
| Add agent support | See AGENTS.md "Adding New Agent Support" |
| Shell scripts | `scripts/bash/`, `scripts/powershell/` |

### Commands Available

```
/speckit.constitution  - Establish project principles
/speckit.specify       - Create feature specification
/speckit.plan          - Technical implementation plan
/speckit.tasks         - Generate parallel task batches (MODIFIED)
/speckit.implement     - Execute implementation
/speckit.analyze       - Cross-artifact consistency check
/speckit.checklist     - Quality validation checklist
/speckit.clarify       - De-risk ambiguous requirements
/speckit.taskstoissues - Convert tasks to GitHub issues
```

### Before Committing

1. Test CLI: `uv run specify check`
2. Test init: `uv run specify init /tmp/test-project --ai claude --force`
3. Version bump if touching `src/`: update `pyproject.toml` + `CHANGELOG.md`
