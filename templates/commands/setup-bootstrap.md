---
description: Initialize project foundation by running constitution, docs, and learn sub-agents
---

## User Input

```text
$ARGUMENTS
```

Options: `--skip-constitution`, `--skip-docs`, `--skip-learn`, `from-code`, `from-docs`, `from-specs`

## Purpose

Orchestrate the project foundation setup by running sub-agents:
1. `/speckit.setup-constitution` → Create/update constitution
2. `/speckit.setup-docs` → Initialize /docs domain structure
3. `/speckit.learn` → Extract patterns + create module CLAUDE.md files

---

## Step 1: Constitution

Run `/speckit.setup-constitution` as a sub-agent.

This will:
- Create `/memory/constitution.md` if missing
- Guide user through principles setup

**Skip if**: `--skip-constitution` flag provided or constitution already exists

---

## Step 2: Docs

Run `/speckit.setup-docs` as a sub-agent.

Pass through any mode arguments: `from-code`, `from-docs`, `from-specs`

This will:
- Detect project state
- Discover/suggest domains
- Generate `/docs/{domain}/spec.md` structure

**Skip if**: `--skip-docs` flag provided

---

## Step 3: Learn

Run `/speckit.learn` as a sub-agent.

This will:
- Create/update `/memory/architecture-registry.md`
- Create `{module}/CLAUDE.md` files for local conventions

**Skip if**: `--skip-learn` flag provided

---

## Completion Report

```markdown
## Bootstrap Complete

### Constitution
- Status: ✓ Created / Already exists / Skipped
- See /speckit.setup-constitution output for details

### Docs
- Status: ✓ Initialized / Skipped
- See /speckit.setup-docs output for details

### Learn
- Status: ✓ Patterns extracted / Skipped
- See /speckit.learn output for details

### Next Steps
1. Review /memory/constitution.md
2. Review /docs/{domain}/spec.md files
3. Run /speckit.setup-agents if needed
4. Start first feature: /speckit.specify "your feature"
```
