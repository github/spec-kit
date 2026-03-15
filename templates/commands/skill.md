---
name: "speckit"
description: "Full Spec-Driven Development (SDD) workflow powered by github/spec-kit. Use speckit-specify to start a feature, then speckit-plan, speckit-tasks, and speckit-implement in sequence."
metadata:
  author: "github-spec-kit"
  source: "https://github.com/github/spec-kit"
  version: "1.0.0"
---

# Spec Kit — Spec-Driven Development

This skill provides the complete Spec-Driven Development workflow from [github/spec-kit](https://github.com/github/spec-kit).
Individual commands are available as separate skills in this directory — each one maps to a phase of the SDD process.

## Workflow Order

Always follow this sequence — never skip phases:

1. **speckit-constitution** — Establish project governing principles *(run once per project)*
2. **speckit-specify** — Turn a feature description into a structured spec
3. **speckit-clarify** — Resolve ambiguities before planning *(optional but recommended)*
4. **speckit-plan** — Create a phased technical implementation plan
5. **speckit-analyze** — Cross-artifact consistency check *(optional, run after tasks)*
6. **speckit-tasks** — Break the plan into ordered, executable tasks
7. **speckit-implement** — Execute tasks one by one
8. **speckit-checklist** — Post-implementation quality checklist

## Core Rules

- Read `.specify/memory/constitution.md` before every coding decision
- Show the spec summary to the user and wait for approval before planning
- Show task count to the user and wait for approval before implementing
- Use `.specify/scripts/bash/` (Linux/macOS) or `.specify/scripts/powershell/` (Windows) for all file and branch operations
- Never create, move, or delete files in `specs/` without explicit user instruction

## Key File Locations

| File | Purpose |
|------|---------|
| `.specify/memory/constitution.md` | Project governing principles — read before every decision |
| `specs/<feature>/spec.md` | Feature specification created by `speckit-specify` |
| `specs/<feature>/plan.md` | Implementation plan created by `speckit-plan` |
| `specs/<feature>/tasks.md` | Task breakdown created by `speckit-tasks` |
| `.specify/templates/` | Base templates for spec, plan, tasks, and checklist artifacts |
| `.specify/scripts/` | Automation scripts for branch and file management |
