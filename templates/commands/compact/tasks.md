---
description: Generate actionable, dependency-ordered tasks.md from design artifacts.
handoffs: 
  - label: Analyze For Consistency
    agent: speckit.analyze
    prompt: Run a project analysis for consistency
    send: true
  - label: Implement Project
    agent: speckit.implement
    prompt: Start the implementation in phases
    send: true
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## Input

```text
$ARGUMENTS
```

Consider user input before proceeding (if not empty).

## Pre-Execution

Check `.specify/extensions.yml` for `hooks.before_tasks`. Run mandatory hooks, show optional. Skip silently if missing/invalid.

## Workflow

1. **Setup**: Run `{SCRIPT}`, parse FEATURE_DIR and AVAILABLE_DOCS.

2. **Load docs**: Required: plan.md, spec.md. Optional: data-model.md, contracts/, research.md, quickstart.md.

3. **Generate tasks**:
   - Extract tech stack/structure from plan.md, user stories (P1,P2,P3) from spec.md
   - Map entities from data-model.md and contracts to user stories
   - Organize by user story for independent implementation/testing
   - Use `templates/compact/tasks-template.md` structure

4. **Write tasks.md** with phases:
   - Phase 1: Setup | Phase 2: Foundation (blocks all stories)
   - Phase 3+: One per user story (priority order)
   - Final: Polish & cross-cutting

5. **Report**: Path, task count per story, parallel opportunities, MVP scope.

6. Check `.specify/extensions.yml` for `hooks.after_tasks`. Run mandatory, show optional. Skip silently if missing.

## Task Format

```
- [ ] [TaskID] [P?] [Story?] Description with file path
```

- Checkbox `- [ ]` required | TaskID: T001, T002.. | [P]=parallel | [Story]=US1,US2 (story phases only)
- Include exact file paths | Tests optional (only if requested)

## Task Organization

- From stories (PRIMARY): each story gets own phase with models→services→endpoints
- From contracts: map to serving story
- From data model: map entities to stories, shared→Setup
- Phase order: Setup→Foundation→Stories(P1→P2→P3)→Polish
