# Phase 0 Research: `/speckit.converge`

This document resolves the open questions from the Technical Context. There were no
`NEEDS CLARIFICATION` markers in the spec; the research below records the key decisions
that shape the design, with rationale and rejected alternatives.

## R1. Delivery mechanism: command template vs. CLI subcommand

- **Decision**: Deliver converge as a Markdown command template at
  `templates/commands/converge.md`, processed by the existing template pipeline for every
  integration — exactly like `analyze`, `implement`, `tasks`, etc.
- **Rationale**: The assessment is an agent-driven reasoning task (read artifacts, read
  code, judge completeness), not deterministic Python logic. Every existing core command
  of this nature is a template. This automatically gives cross-integration support via the
  `__SPECKIT_COMMAND_*__` and `{SCRIPT}` processing already in place.
- **Alternatives considered**:
  - *Pure Python CLI subcommand* — rejected: completeness assessment is not deterministic
    and would duplicate the agent-reasoning model the other commands rely on.
  - *Extension rather than core* — rejected: the spec requires it to ship across all
    integrations as a first-class step after implement (FR-016, FR-017); the proposal's
    explicit goal is to absorb the most-reinvented community capability into core.

## R2. Path / prerequisite resolution without git

- **Decision**: Reuse `check-prerequisites.sh --json --require-tasks --include-tasks`
  (and the `.ps1` equivalent) in the command frontmatter `scripts:` block to resolve
  `FEATURE_DIR` and confirm `plan.md` + `tasks.md` exist.
- **Rationale**: This is the same mechanism `analyze` and `implement` use. It already
  resolves the feature directory via `SPECIFY_FEATURE_DIRECTORY` → `.specify/feature.json`
  and otherwise exits with a clear prerequisite error, so converge keeps the same
  no-git behavior (Constitution Principle II). No new script is introduced, preserving
  cross-platform parity by construction.
- **Alternatives considered**:
  - *New `converge`-specific helper script* — rejected: would require Bash + PowerShell
    parity maintenance for no added capability, violating the "focused contribution"
    principle.
  - *git diff against a base branch* (as the original proposal hinted) — rejected per
    explicit product direction and Constitution Principle II: converge does not track
    changes or depend on git. Scope is the current state of the code relative to the
    artifacts.

## R3. Scope of the code scan

- **Decision**: Bound the assessment to the feature's artifacts — the requirements,
  acceptance criteria, and plan decisions in `spec.md`/`plan.md`, plus the files and
  components named by existing tasks in `tasks.md`. The command reads the current state of
  those code paths and judges completeness.
- **Rationale**: Matches the proposal's "Deterministic scope" principle and the spec's
  FR-001 ("sole source of intent … MUST NOT infer scope beyond"). Keeps runs focused and
  repeatable.
- **Alternatives considered**:
  - *Whole-repository scan* — rejected: noisy, slow, and prone to flagging unrelated code;
    contradicts FR-001.

## R4. Output behavior — append vs. confirmation gate

- **Decision**: Generate the findings summary in-session and append the remaining work as
  a new "Convergence" phase to `tasks.md` as part of the normal run (no separate approval
  step). The command never modifies `spec.md`, `plan.md`, existing tasks, or code.
- **Rationale**: The product direction is explicit — converge's purpose is to "come up
  with the additional tasks and add them" so implement can complete them. The append-only,
  never-touch-other-artifacts constraints are the safety boundary (FR-005, FR-008–FR-010).
  Recorded as an Assumption in the spec.
- **Alternatives considered**:
  - *Read-only report + manual confirmation before append* (original proposal principle 6)
    — superseded by product direction; converge would otherwise stall the loop it exists
    to drive.
  - *Write a separate `converge-report.md` artifact* — rejected: adds a persisted artifact
    the spec deliberately scopes out; findings are surfaced in-session instead.

## R5. Finding classification and traceability

- **Decision**: Classify each finding as one of: **missing** (gap), **partial**,
  **contradicts intent** (drift), or **unrequested addition**. Each appended task names the
  requirement / acceptance criterion / plan decision / constraint it traces to and its gap
  type. Constitution violations are highest severity.
- **Rationale**: Mirrors the vocabulary already used by `analyze` (severity-graded,
  constitution conflicts CRITICAL) and satisfies FR-004 and FR-007. Reuse keeps the agent
  guidance consistent across commands.
- **Alternatives considered**:
  - *Single undifferentiated "TODO" list* — rejected: loses the traceability and
    prioritization the spec requires (FR-007, SC-003).

## R6. Task numbering and placement

- **Decision**: Append a new phase header (e.g. `## Phase N — Convergence`) at the bottom
  of `tasks.md`, continuing the existing numeric task IDs from the highest existing number.
- **Rationale**: Satisfies FR-006; keeps appended tasks consumable by `/speckit.implement`
  with no special handling (SC-005). Bottom-append preserves existing tasks as historical
  record (FR-009).
- **Alternatives considered**:
  - *Interleaving convergence tasks into existing phases* — rejected: mutates existing
    structure and risks renumbering, violating FR-009.

## R7. Registration surface (command-set enumerations)

- **Decision**: Add `"converge"` to every place that enumerates the canonical core command
  set: `SKILL_DESCRIPTIONS` (`src/specify_cli/__init__.py`), `_FALLBACK_CORE_COMMAND_NAMES`
  (`src/specify_cli/extensions.py`), the Claude `ARGUMENT_HINTS`, the post-init guidance in
  `commands/init.py`, the integration test `COMMAND_STEMS` lists, and the command reference
  docs.
- **Rationale**: Constitution Principle III requires command-set changes to update every
  enumeration in the same change set; `test_agent_config_consistency.py` and the
  per-integration tests enforce this.
- **Alternatives considered**:
  - *Add the template only* — rejected: would fail the integration tests and leave the
    command undiscoverable in onboarding.

## Summary of resolved unknowns

| Topic | Resolution |
|-------|-----------|
| Delivery form | Markdown command template (R1) |
| Path resolution | Reuse `check-prerequisites` (R2) |
| Scan scope | Bounded to feature artifacts + task-referenced code (R3) |
| Output | In-session summary + append-only tasks (R4) |
| Classification | missing / partial / contradicts / unrequested, traceable (R5) |
| Numbering | Bottom-append, continue existing IDs (R6) |
| Registration | All command-set enumerations updated (R7) |

No `NEEDS CLARIFICATION` items remain.
