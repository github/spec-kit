# What-if Analysis Extension

Preview the downstream impact of requirement changes before committing to them.

## Overview

The What-if Analysis extension provides a read-only simulation tool for spec-driven development. It allows teams to preview how a proposed change will affect:

- **Complexity**: Heuristic scoring of project difficulty.
- **Effort**: Estimated person-hours for implementation.
- **Tasks**: Delta in the task list (added, removed, changed).
- **Risks**: Potential technical debt, breaking changes, or conflicts.

## Installation

```bash
specify extension add whatif
```

Or for development:

```bash
specify extension add --dev path/to/whatif
```

## Usage

Invoke the command through your AI assistant:

```bash
/speckit.whatif.analyze "Change the database from SQLite to PostgreSQL"
```

The agent will analyze your current artifacts (`spec.md`, `plan.md`, `tasks.md`, `constitution.md`) and generate a detailed impact report without modifying any files.

## Commands

### `speckit.whatif.analyze`

Performs the simulation and generates the report.

**Arguments**: The hypothetical scenario or requirement change to analyze.
