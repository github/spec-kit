# Guided SDD Pipeline Workflow

A comprehensive workflow that chains the core Spec Kit commands into a single, guided execution with optional phases and a post-implement convergence loop.

## Overview

This workflow orchestrates the full SDD (Software Design Document) pipeline:

```
[Constitution] → Specify → [Clarify Gate] → Plan → [Checklist] → Tasks 
    ↓
    Analyze → Implement → Converge → [Convergence Loop]
```

## Features

- **Modular phases**: Enable/disable constitution and checklist phases as needed
- **Clarify gate**: Optional human checkpoint after clarification
- **Analyze pass**: Single pre-implement consistency check across spec, plan, and tasks
- **Convergence loop**: Post-implement loop using `speckit.converge` to append remaining work as tasks and re-implement (up to 3 cycles)
- **Integration agnostic**: Works with Claude, Copilot, Gemini, OpenCode
- **Resumable**: Full workflow state persistence for interrupted runs

## Inputs

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `spec` | string | required | Describe what you want to build |
| `integration` | string | `auto` | Integration to use (e.g. claude, copilot, gemini) |
| `with_constitution` | boolean | `false` | Include the constitution phase |
| `with_checklist` | boolean | `false` | Include the checklist phase |
| `skip_clarify` | boolean | `false` | Skip the clarify gate |

## Usage

### Run with defaults
```bash
specify workflow run pipeline "build a todo app"
```

### Run with all optional phases
```bash
specify workflow run pipeline \
  "build a todo app" \
  --with-constitution \
  --with-checklist
```

### Run with a specific integration
```bash
specify workflow run pipeline \
  "build a todo app" \
  --integration claude
```

### Skip clarify gate
```bash
specify workflow run pipeline \
  "build a todo app" \
  --skip-clarify
```

## Step Details

### 1. Constitution (Optional)
Generates or validates project constitution if `with_constitution` is enabled.

### 2. Specify
Generates the specification from your feature description.

### 3. Clarify (Optional Gate)
Provides clarifications on the spec, then pauses for human review/approval before proceeding to planning.

Can be skipped entirely with `--skip-clarify`.

### 4. Plan
Generates the implementation plan based on the spec.

### 5. Checklist (Optional)
Generates a task checklist if `with_checklist` is enabled.

### 6. Tasks
Breaks the plan into actionable tasks.

### 7. Analyze
Performs a single pre-implement consistency check across spec, plan, and tasks. Findings are surfaced but do not block progress; artifacts are updated as needed before implementation.

### 8. Implement
Generates the implementation code based on the spec, plan, and tasks.

### 9. Convergence Loop
- **Converge**: Runs `speckit.converge` to assess code against spec, plan, and tasks
- **Append tasks**: If convergence finds remaining work, appends new tasks to tasks.md
- **Re-implement**: Runs implement again to address the appended tasks
- **Repeats** up to 3 cycles
- **Converged pass**: When converge finds no remaining work, tasks.md is left unchanged (no-op iteration)

## Prerequisites

- Spec Kit >= 0.8.5
- Initialized project with one of: Claude, Copilot, Gemini, OpenCode

## Notes

### Convergence Loop Behavior
The convergence loop is bounded to 3 iterations rather than condition-driven, since prompt-template commands don't reliably signal findings via exit codes. A converged pass leaves tasks.md byte-for-byte unchanged, so extra iterations are safe no-ops.

## Related Workflows

- **speckit**: Full SDD cycle with review gates (simpler, no convergence loop)
- See `specify workflow search` for more options

## Contributing

To improve this workflow:

1. Test changes locally with `specify workflow run`
2. Update version in `workflow.yml`
3. Add entry to `CHANGELOG.md`
4. Submit PR to the Spec Kit repository

## License

MIT
