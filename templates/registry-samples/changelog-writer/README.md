# changelog-writer

A Claude Code skill that generates changelogs from git history.

## Usage

```
/changelog-writer              # Generates changelog from last tag to HEAD
/changelog-writer v1.0.0       # From a specific tag to HEAD
/changelog-writer v1.0.0..v2.0.0  # Specific range
```

## What it does

1. Analyzes git commits in the specified range
2. Categorizes them by conventional commit prefixes (feat, fix, docs, etc.)
3. Fills in the changelog template with grouped entries
4. Writes or prepends to `CHANGELOG.md`

## How it works

This is a **skill** (not a command), which means:

- It runs in a **forked context** — isolated from your main conversation
- It has **restricted tools** — can only use Bash, Read, Write, Edit, Glob, Grep
- It includes a **supporting file** (`template.md`) that defines the changelog format

## Installed files

| File | Purpose |
|------|---------|
| `.claude/skills/changelog-writer/SKILL.md` | The skill definition |
| `.claude/skills/changelog-writer/template.md` | Changelog format template |

## Customization

- Edit `template.md` to change the changelog format
- Edit `SKILL.md` to adjust commit categorization rules or add custom categories
