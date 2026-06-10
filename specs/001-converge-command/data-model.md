# Phase 1 Data Model: `/speckit.converge`

This feature has no database. The "entities" are conceptual structures the command reasons
about and the textual artifacts it reads/writes. They are documented here so the command
template and tests share a precise vocabulary.

## Entity: Finding

A single assessed gap between specified intent and the current codebase. Produced during
assessment; rendered into the in-session summary and (when actionable) into a Convergence
task.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable in-report identifier (e.g. `C1`, `C2`). |
| `source_ref` | string | The intent it traces to: a requirement (`FR-###`), success criterion (`SC-###`), acceptance scenario (`US#/AC`), plan decision, or constitution principle. |
| `gap_type` | enum | One of `missing`, `partial`, `contradicts`, `unrequested`. |
| `severity` | enum | `CRITICAL` (constitution violation or blocking gap), `HIGH`, `MEDIUM`, `LOW`. |
| `description` | string | Human-readable statement of what is wrong or absent. |
| `evidence` | string (optional) | Where in the code the assessment looked (file/component), to justify the verdict. |

**Validation rules**:
- `source_ref` MUST reference an item that exists in `spec.md`, `plan.md`, `tasks.md`, or
  the constitution. The command MUST NOT invent requirements (FR-001).
- A constitution violation MUST be `severity = CRITICAL`.
- `gap_type = unrequested` findings describe code not called for by the artifacts; they are
  reported but MUST NOT result in deletion of code (only a task noting the discrepancy).

## Entity: Convergence Task

A new task appended to `tasks.md` to close a `Finding` whose `gap_type` represents work to
do (`missing`, `partial`, `contradicts`, and optionally `unrequested`).

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Continues existing numbering, incremented from the highest existing task ID. |
| `description` | string | Imperative statement of the work to perform. |
| `source_ref` | string | Same trace reference as the originating `Finding`. |
| `gap_type` | enum | Carried from the `Finding`, shown as a parenthetical label. |

**Validation rules**:
- `task_id` MUST be unique and greater than every pre-existing task ID (FR-006).
- The task MUST be placed under the Convergence phase header at the end of `tasks.md`
  (FR-006, FR-009).
- The task MUST be expressed so `/speckit.implement` can execute it without reformatting
  (SC-005).

**State transition**: A Convergence Task follows the same lifecycle as any task —
unchecked `[ ]` → checked `[X]` once `/speckit.implement` completes it. Converge does not
check tasks off itself.

## Entity: Convergence Result

The outcome of a single command run.

| Field | Type | Description |
|-------|------|-------------|
| `status` | enum | `converged` (no remaining work) or `tasks_appended`. |
| `checked` | counts | Requirements, acceptance criteria, and plan decisions assessed. |
| `appended_count` | integer | Number of Convergence tasks added (0 when `converged`). |
| `findings` | list[Finding] | The findings rendered in the in-session summary. |

**Validation rules**:
- `status = converged` ⇒ `appended_count = 0` and `tasks.md` is unchanged (FR-011).
- `status = tasks_appended` ⇒ `appended_count ≥ 1`.
- The result MUST be surfaced to the post-assessment hook so extensions can branch on it
  (FR-015).

## Artifacts (filesystem)

| Artifact | Access | Notes |
|----------|--------|-------|
| `spec.md` | read-only | Source of requirements, acceptance criteria, success criteria. |
| `plan.md` | read-only | Source of plan decisions / technical constraints. |
| `tasks.md` | read + **append-only** | The only mutated artifact; Convergence phase appended. |
| `.specify/memory/constitution.md` | read-only | Governing constraints; may be an unfilled template (skip gracefully). |
| feature source code | read-only | The implementation under assessment; never modified by converge. |
