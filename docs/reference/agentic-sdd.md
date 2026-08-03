# Agentic SDD

The `/speckit.*` slash commands drive the core Spec-Driven Development (SDD) process — an **agentic process** your coding agent runs step by step. For a guided, end-to-end run see the [Quick Start Guide](../quickstart.md); this page is the detailed reference for each command — including arguments, output, and how they interact. For the philosophy behind the process, see [What is SDD?](../concepts/sdd.md). For bug triage, see [Agentic Bug Fix](agentic-bugfix.md).

The commands are designed to run in order, but only `/speckit.specify` is strictly required before `/speckit.plan`. The clarify, checklist, and analyze commands are quality gates you add for anything with meaningful ambiguity.

> [!NOTE]
> Commands are written in `/speckit.*` form throughout this page. The exact invocation depends on your agent — some skills-based agents use `$speckit-*` (e.g. Codex, ZCode) or `/skill:speckit-*` (e.g. Kimi). Substitute the form your agent exposes.

```text
/speckit.constitution -> /speckit.specify -> /speckit.clarify -> /speckit.plan -> /speckit.checklist -> /speckit.tasks -> /speckit.analyze -> /speckit.implement -> /speckit.converge
```

## `/speckit.constitution`

Creates or updates the project **constitution** — the guiding principles that every later phase is evaluated against — and keeps dependent templates in sync. Run it once up front and update it whenever your principles change. Pass the principles as arguments.

```text
/speckit.constitution This project follows a "Library-First" approach. All features must be implemented as standalone libraries first. We use TDD strictly. We prefer functional programming patterns.
```

## `/speckit.specify`

Creates or updates the feature **specification** from a natural-language description. Focus on the **what** and **why** — the user-facing behavior and goals — not the tech stack, which belongs in `/speckit.plan`.

```text
/speckit.specify Build an application that helps me organize photos into albums grouped by date, re-orderable by drag-and-drop on the main page, with a tile preview inside each album.
```

## `/speckit.clarify`

Asks up to five targeted questions about underspecified areas of the current spec and encodes your answers back into `spec.md`. Run it as many times as needed before planning, each time tackling a different area. Optionally pass a focus area as an argument.

```text
/speckit.clarify Focus on the task card behavior: status changes, comment limits, and who can be assigned.
```

Clarifying before planning keeps you from designing on top of ambiguity. If `/speckit.analyze` later surfaces requirement gaps, come back and run `/speckit.clarify` (or `/speckit.specify`) again.

## `/speckit.plan`

Runs the planning process to generate design artifacts from the spec. This is where implementation detail belongs — provide your tech stack, architecture, and technical constraints as arguments.

```text
/speckit.plan Use .NET Aspire with Postgres. The frontend is Blazor Server with drag-and-drop boards and real-time updates. Expose REST APIs for projects, tasks, and notifications.
```

## `/speckit.checklist`

Generates a quality checklist for the feature — think of it as **"unit tests for your requirements."** Rather than testing code, it checks whether the spec itself is complete, clear, unambiguous, and consistent (for example: "Are the drag-and-drop rules defined for every column?", "Is behavior specified for a deleted assigned user?").

Run it with no arguments for a broad pass, or pass a focus area to target one aspect:

```text
/speckit.checklist
```

```text
/speckit.checklist Focus on the Kanban board interactions and comment permissions.
```

Review the generated checklist. If it surfaces gaps, loop back to `/speckit.clarify` or `/speckit.specify` to tighten the spec before breaking the work down.

## `/speckit.tasks`

Generates an actionable, dependency-ordered `tasks.md` from the design artifacts. Tasks are organized into phases: **Setup**, **Foundational** (blocking prerequisites), then **one phase per user story** in priority order, and a final **Polish** phase for cross-cutting concerns. Tests are generated within a user story's phase when requested rather than as a separate phase, and tasks are marked for parallel execution where possible.

```text
/speckit.tasks
```

## `/speckit.analyze`

Performs a **read-only** cross-artifact consistency and quality analysis across `spec.md`, `plan.md`, and `tasks.md`, reporting conflicts, gaps, and ambiguities (for example a task with no matching requirement, or a plan choice that contradicts the spec). It never edits files — it produces a report and can optionally suggest remediations for you to approve.

```text
/speckit.analyze
```

Run it before implementing, while the artifacts can still be adjusted cheaply. If it surfaces issues, **return to the earlier step that owns them** and fix them at the source — `/speckit.specify` or `/speckit.clarify` for requirement problems, `/speckit.plan` for design problems, `/speckit.tasks` to regenerate the task list — then re-run `/speckit.analyze` until it comes back clean. You can also run `/speckit.analyze` again after implementation as an extra review.

## `/speckit.implement`

Executes the tasks in `tasks.md`, running each phase in dependency order and respecting parallel markers.

For a small feature, run it once to build everything:

```text
/speckit.implement
```

For a large feature, work in stages to avoid overwhelming the agent's context — scope each run with an argument, validate the result, then continue:

```text
/speckit.implement Implement only the Setup and Foundational phases: project scaffolding and the project/task data model with basic CRUD. Stop before the user-story features.
```

```text
/speckit.implement Now implement the Kanban board user story: drag-and-drop between columns.
```

Verify each stage works before moving to the next.

## `/speckit.converge`

Assesses the codebase against the feature's spec, plan, and tasks to confirm nothing was missed. It is **append-only**: it never edits or deletes code, and its only possible write is adding tasks to `tasks.md`. Run it only after `/speckit.implement` has run on the current `tasks.md`.

```text
/speckit.converge
```

It first prints a severity-graded findings summary, then resolves to one of two outcomes:

- **Converged** — no gaps found. `tasks.md` is left byte-for-byte unchanged and you'll see a clean result like `✅ Converged — the implementation satisfies the spec, plan, and tasks.` You're done; proceed to review or open a PR.
- **Tasks appended** — gaps found. Converge appends them as new tasks under a Convergence section in `tasks.md` and tells you how many. Run `/speckit.implement` again to complete them, then `/speckit.converge` once more. Each pass finds fewer items; repeat until it reports converged.
