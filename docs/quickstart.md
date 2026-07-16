# Quick Start Guide

This guide will help you get started with Spec-Driven Development using Spec Kit. Throughout, we illustrate each step with a running example: **Taskify**, a small team productivity platform.

> [!NOTE]
> Automation scripts are provided as both Bash (`.sh`) and PowerShell (`.ps1`) variants. The `specify` CLI auto-selects based on your OS unless you pass `--script sh|ps`.

> [!NOTE]
> Commands are shown here in `/speckit.*` form, but the exact invocation depends on your agent. Some skills-based agents use `$speckit-*` (e.g. Codex, ZCode) or `/skill:speckit-*` (e.g. Kimi). Use whichever form your agent exposes — the steps are otherwise identical.

## Recommended Process

> [!TIP]
> **Context Awareness**: Spec Kit tracks the active feature by the feature directory recorded in `.specify/feature.json` (overridable with the `SPECIFY_FEATURE_DIRECTORY` environment variable). Commands resolve the feature from that state, **not** from the checked-out Git branch — no Git required. The opt-in **git** extension adds numbered feature branches (e.g. `001-feature-name`) for organizing work in version control, but the active feature is still whichever directory that state points to; `git checkout` alone does not change it. To point commands at a different feature, update `.specify/feature.json` (or set `SPECIFY_FEATURE_DIRECTORY`).

After installing Spec Kit, each command below is a step in the process. Two paths are common:

**Shorter path** — for smaller features:

1. `/speckit.specify`
2. `/speckit.plan`
3. `/speckit.tasks`
4. `/speckit.implement`
5. `/speckit.converge`

**Full path** — for production features, adding `/speckit.clarify`, `/speckit.checklist`, and `/speckit.analyze` as quality gates:

1. `/speckit.constitution`
2. `/speckit.specify`
3. `/speckit.clarify`
4. `/speckit.plan`
5. `/speckit.checklist`
6. `/speckit.tasks`
7. `/speckit.analyze`
8. `/speckit.implement`
9. `/speckit.converge`

### Install Specify

**In your terminal**, install the CLI from PyPI (requires [uv](install/uv.md)), then initialize your project:

```bash
uv tool install specify-cli
specify init taskify   # or: specify init .   to use the current directory
```

`init` lets you pick your coding agent interactively, or pass it explicitly with `--integration` (e.g. `--integration copilot`).

> [!NOTE]
> Prefer `pipx`, one-time `uvx` runs, a pinned release, or an offline/air-gapped setup? See the [Installation Guide](installation.md) for all supported methods.

### Step 1: `/speckit.constitution` — set the ground rules

Establishes the project's guiding principles, which every later step is evaluated against. Run it once up front, passing your principles as arguments.

```text
/speckit.constitution Taskify is a "Security-First" application. All user inputs must be validated. We use a microservices architecture. Code must be fully documented.
```

### Step 2: `/speckit.specify` — describe what to build

Creates the feature specification from a natural-language description. Focus on the **what** and **why**, not the tech stack.

```text
/speckit.specify Develop Taskify, a team productivity platform where predefined users create projects, assign tasks, comment, and move tasks across Kanban columns (To Do, In Progress, In Review, Done). Five users (one product manager, four engineers), three sample projects, no login for this first phase.
```

### Step 3: `/speckit.clarify` — resolve ambiguities

Asks targeted questions about anything underspecified and folds your answers back into the spec, so you're not planning on top of ambiguity. Run it before planning, optionally with a focus area.

```text
/speckit.clarify Focus on task card behavior — status changes, comment permissions, and user assignment.
```

### Step 4: `/speckit.plan` — choose the tech stack

Generates the design artifacts from the spec. This is where implementation detail belongs — provide your tech stack and architecture.

```text
/speckit.plan Use .NET Aspire with Postgres. The frontend is Blazor Server with drag-and-drop boards and real-time updates. Expose REST APIs for projects, tasks, and notifications.
```

### Step 5: `/speckit.checklist` — validate the spec

Generates a quality checklist — "unit tests for your requirements" — to confirm the spec is complete, clear, and consistent before you break the work down.

```text
/speckit.checklist
```

### Step 6: `/speckit.tasks` — break the work down

Generates an actionable, dependency-ordered `tasks.md` from the design artifacts.

```text
/speckit.tasks
```

### Step 7: `/speckit.analyze` — check consistency

Reports conflicts, gaps, and ambiguities across `spec.md`, `plan.md`, and `tasks.md`. It's read-only — if it flags issues, fix them at the source and re-run before implementing.

```text
/speckit.analyze
```

### Step 8: `/speckit.implement` — build it

Executes the tasks in `tasks.md` in dependency order. Run it once to build everything, or scope it to one phase at a time for large features.

```text
/speckit.implement
```

### Step 9: `/speckit.converge` — verify completeness

Checks the codebase against the spec, plan, and tasks. If it finds gaps, it appends new tasks to `tasks.md`; run `/speckit.implement` and converge again until it reports converged. Otherwise you're done — proceed to review or open a PR.

```text
/speckit.converge
```

> [!TIP]
> For a full reference on each command — arguments, output, phased implementation, and how they interact — see [Agentic SDD](reference/agentic-sdd.md).

## Key Principles

- **Be explicit** about what you're building and why
- **Don't focus on tech stack** during specification phase
- **Iterate and refine** your specifications before implementation
- **Validate** requirements and plans before coding begins
- **Let the coding agent handle** the implementation details

## Next Steps

- See the [Agentic SDD](reference/agentic-sdd.md) reference for full detail on every command
- Read the [complete methodology](https://github.com/github/spec-kit/blob/main/spec-driven.md) for in-depth guidance
- Check out [more examples](https://github.com/github/spec-kit/tree/main/templates) in the repository
- Explore the [source code on GitHub](https://github.com/github/spec-kit)
