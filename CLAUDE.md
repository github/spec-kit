# CLAUDE.md

> **Lightweight bridge** → See `AGENTS.md` for full spec-kit-max architecture, development guidelines, and upstream sync procedures.

## Quick Reference

### This is spec-kit-max

A fork of `github/spec-kit` with parallel subagent orchestration for Claude Code. Key file: `.claude/commands/speckit.tasks.md`.

### Dogfooding Active

This repo manages itself:
- `.claude/commands/` → actual command files (Claude Code reads these)
- `templates/commands/` → symlinks to `.claude/commands/` (for distribution)
- Changes to `.claude/commands/speckit.*.md` immediately affect `/speckit.*` commands
- Use the spec-kit workflow to develop spec-kit

### Critical Paths

| Task | Key Files |
|------|-----------|
| Modify commands | `.claude/commands/speckit.*.md` |
| CLI changes | `src/specify_cli/__init__.py` + bump `pyproject.toml` |
| Add agent support | See AGENTS.md "Adding New Agent Support" |
| Shell scripts | `scripts/bash/`, `scripts/powershell/` |

### Commands Available

```
/speckit.constitution  - Establish project principles
/speckit.specify       - Create feature specification
/speckit.plan          - Technical implementation plan
/speckit.tasks         - Generate parallel task batches (ENHANCED)
                         Always emits tasks.execution.yaml
                         --no-orchestration → skip YAML (not recommended)
/speckit.implement     - Execute implementation (ENHANCED)
                         Auto-spawns parallel subagents when YAML exists
                         --sequential → force single-agent mode
                         --max-parallel N → limit concurrent (default: 10)
/speckit.analyze       - Cross-artifact consistency check
/speckit.checklist     - Quality validation checklist
/speckit.clarify       - De-risk ambiguous requirements
/speckit.taskstoissues - Convert tasks to GitHub issues
```

### Parallel Execution Workflow

```bash
# 1. Generate tasks (YAML is auto-generated)
/speckit.tasks

# 2. Run parallel implementation (auto-detects YAML)
/speckit.implement

# Or force sequential mode
/speckit.implement --sequential
```

### Before Committing

1. Test CLI: `uv run specify check`
2. Test init: `uv run specify init /tmp/test-project --ai claude --force`
3. Version bump if touching `src/`: update `pyproject.toml` + `CHANGELOG.md`

## Active Technologies
- Markdown command files (Claude Code native) + Claude Code Task tool, Claude Code CLI (001-parallel-commands)
- File-based workspace at `.claude/workspace/` (context.md, results/, gates/) (001-parallel-commands)

## Recent Changes
- 001-parallel-commands: Added Markdown command files (Claude Code native) + Claude Code Task tool, Claude Code CLI
