<a id="quick-start-guide"></a>

# Spec-Driven Development Quickstart

This guide will help you get started with Spec-Driven Development using Spec Kit. Throughout, we illustrate each step with a running example: **Taskify**, a small team productivity platform.

Use SDD to build a feature or application from a specification. For a repair,
follow the [bug-fixing quickstart](guides/bugfix.md); to decide whether an idea
deserves investment, follow the [idea assessment quickstart](guides/assessment.md).
These are independent processes, not prerequisites for this guide.

> [!NOTE]
> Automation scripts are provided as Bash (`.sh`), PowerShell (`.ps1`), and Python (`.py`) variants. Interactive `specify init` prompts you to choose one; non-interactive runs (no TTY, or `--non-interactive`) default to a shell variant for your OS. Pass `--script sh|ps|py` to select explicitly.

The process steps here use GitHub Copilot's default skills mode (`/speckit-*`).
For other agents or modes, see
[Command invocation](reference/integrations.md#command-invocation).
Invoke each `/speckit-*` skill separately in your agent's chat and review the
result before moving to the next step. These are agent skills, not terminal
commands; only CLI installation and project setup use the terminal.

## Recommended Process

> [!TIP]
> **Context Awareness**: Spec Kit tracks the active feature by the feature directory recorded in `.specify/feature.json` (overridable with the `SPECIFY_FEATURE_DIRECTORY` environment variable). Commands resolve the feature from that state, **not** from the checked-out Git branch — no Git required. The opt-in **git** extension adds numbered feature branches (e.g. `001-feature-name`) for organizing work in version control, but the active feature is still whichever directory that state points to; `git checkout` alone does not change it. To point commands at a different feature, update `.specify/feature.json` (or set `SPECIFY_FEATURE_DIRECTORY`).

After installing Spec Kit, each skill below is a step in the process. Two paths are common:

Establish a constitution once per project with `/speckit-constitution` before
starting either path.

**Shorter path** — for smaller features:

1. `/speckit-specify`
2. `/speckit-plan`
3. `/speckit-tasks`
4. `/speckit-implement`
5. `/speckit-converge`

**Full path** — for production features, adding `/speckit-clarify`, `/speckit-checklist`, and `/speckit-analyze` as quality gates:

1. `/speckit-constitution` (once per project)
2. `/speckit-specify`
3. `/speckit-clarify`
4. `/speckit-plan`
5. `/speckit-checklist`
6. `/speckit-tasks`
7. `/speckit-analyze`
8. `/speckit-implement`
9. `/speckit-converge`

### Install Specify

**In your terminal**, install the CLI from PyPI (requires [uv](install/uv.md)), then initialize your project:

```bash
uv tool install specify-cli
specify init taskify --integration copilot
cd taskify
```

`init` lets you pick your coding agent interactively, or pass it explicitly with `--integration` (e.g. `--integration copilot`). For CI and AI agent harnesses, add `--non-interactive` so unspecified choices use documented defaults instead of hanging on an arrow-key picker.

> [!NOTE]
> Prefer `pipx`, one-time `uvx` runs, a pinned release, or an offline/air-gapped setup? See the [Installation Guide](installation.md) for all supported methods.
> Adding Spec Kit to a repository that already contains code? Follow
> [Adopting Spec Kit in an Existing Project](guides/existing-projects.md) before
> starting the workflow below.

Launch your coding agent in the project directory. Invoke the following skills
in its chat, one at a time.

<a id="step-1-speckitconstitution--set-the-ground-rules"></a>

### Step 1: `/speckit-constitution` — set the ground rules

Establishes the project's guiding principles, which every later step is evaluated against. Run it once up front, passing your principles as arguments.

```text
/speckit-constitution Taskify is a "Security-First" application. All user inputs must be validated. We use a microservices architecture. Code must be fully documented.
```

<a id="step-2-speckitspecify--describe-what-to-build"></a>

### Step 2: `/speckit-specify` — describe what to build

Creates the feature specification from a natural-language description. Focus on the **what** and **why**, not the tech stack.

```text
/speckit-specify Develop Taskify, a team productivity platform where predefined users create projects, assign tasks, comment, and move tasks across Kanban columns (To Do, In Progress, In Review, Done). Five users (one product manager, four engineers), three sample projects, no login for this first phase.
```

<a id="step-3-speckitclarify--resolve-ambiguities"></a>

### Step 3: `/speckit-clarify` — resolve ambiguities

Asks targeted questions about anything underspecified and folds your answers back into the spec, so you're not planning on top of ambiguity. Run it before planning, optionally with a focus area.

```text
/speckit-clarify Focus on task card behavior — status changes, comment permissions, and user assignment.
```

<a id="step-4-speckitplan--choose-the-tech-stack"></a>

### Step 4: `/speckit-plan` — choose the tech stack

Generates the design artifacts from the spec. This is where implementation detail belongs — provide your tech stack and architecture.

```text
/speckit-plan Use .NET Aspire with Postgres. The frontend is Blazor Server with drag-and-drop boards and real-time updates. Expose REST APIs for projects, tasks, and notifications.
```

<a id="step-5-speckitchecklist--validate-the-spec"></a>

### Step 5: `/speckit-checklist` — validate the spec

Generates a custom quality checklist — "unit tests for your requirements" — to confirm the spec is complete, clear, and consistent before you break the work down. These custom checklists are reviewer-owned requirements-quality review artifacts: mark an item `[x]` only when the reviewer determines that requirement-quality criterion is satisfied. Checked custom items do not mean implementation work is complete.

```text
/speckit-checklist
```

<a id="step-6-speckittasks--break-the-work-down"></a>

### Step 6: `/speckit-tasks` — break the work down

Generates an actionable, dependency-ordered `tasks.md` from the design artifacts.

```text
/speckit-tasks
```

<a id="step-7-speckitanalyze--check-consistency"></a>

### Step 7: `/speckit-analyze` — check consistency

Reports conflicts, gaps, and ambiguities across `spec.md`, `plan.md`, and `tasks.md`. It's read-only — if it flags issues, fix them at the source and re-run before implementing.

```text
/speckit-analyze
```

<a id="step-8-speckitimplement--build-it"></a>

### Step 8: `/speckit-implement` — build it

Executes the tasks in `tasks.md` in dependency order. Before implementation, it reads checklist checkbox state as a gate and asks before proceeding if any checklist items are unchecked; it does not change any checklist files or markers. The built-in `checklists/requirements.md` checklist is maintained by `/speckit-specify` and `/speckit-clarify`, while custom checklists remain reviewer-owned. Run it once to build everything, or scope it to one phase at a time for large features.

```text
/speckit-implement
```

<a id="step-9-speckitconverge--verify-completeness"></a>

### Step 9: `/speckit-converge` — verify completeness

Checks the codebase against the spec, plan, and tasks. If it finds gaps, it appends new tasks to `tasks.md`; run `/speckit-implement` and converge again until it reports **Converged**. Otherwise you're done — proceed to review or open a PR.

```text
/speckit-converge
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
- Learn how to [customize the process](guides/customization.md) with extensions, presets, workflows, and bundles
- Read the [complete methodology](https://github.com/github/spec-kit/blob/main/spec-driven.md) for in-depth guidance
- Compare the [core templates](https://github.com/github/spec-kit/tree/main/templates) with
  [community walkthroughs](community/walkthroughs.md) to see how Spec-Driven Development is used in real projects
- Explore the [source code on GitHub](https://github.com/github/spec-kit)

## Video Overview

For a visual introduction, watch the
[Spec Kit video overview](https://www.youtube.com/watch?v=a9eR1xsfvHg).
Use the commands in this guide for the current workflow and invocation syntax.

[![Spec Kit video overview](https://raw.githubusercontent.com/github/spec-kit/main/media/spec-kit-video-header.jpg)](https://www.youtube.com/watch?v=a9eR1xsfvHg)
