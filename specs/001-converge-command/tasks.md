# Tasks: Implementation Convergence Command (`/speckit.converge`)

**Input**: Design documents from `/specs/001-converge-command/`

**Prerequisites**: [plan.md](plan.md) (required), [spec.md](spec.md) (user stories), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/)

**Tests**: This feature's deliverable is a prompt-template command plus registry edits; it has no unit-testable application logic, so no TDD test tasks are generated. The required updates to the integration `COMMAND_STEMS` lists and the existing `test_agent_config_consistency.py` are treated as implementation/verification tasks. End-to-end validation is the `quickstart.md` scenarios in the Polish phase.

**Organization**: Tasks are grouped by user story. The single command template (`templates/commands/converge.md`) is built incrementally — each user story adds the prompt logic for its behavior to that file.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- All paths are relative to the `spec-kit` repository root

## Path Conventions

This feature edits an existing Python CLI project at the `spec-kit` repo root: command
templates in `templates/commands/`, CLI code in `src/specify_cli/`, tests in `tests/`, docs
in `docs/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the command template file and its invocation plumbing.

- [X] T001 Create the command template skeleton at `templates/commands/converge.md` modeled on `templates/commands/analyze.md`: YAML frontmatter with a `description` and a `scripts:` block (`sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`, `ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`), a `## User Input` section echoing `$ARGUMENTS`, and empty section placeholders for the workflow.
- [X] T002 In `templates/commands/converge.md`, add the `## Execution Steps` initialization step that runs `{SCRIPT}` once, parses JSON for `FEATURE_DIR`/`AVAILABLE_DOCS`, derives `SPEC`/`PLAN`/`TASKS`/constitution paths, and aborts with a prerequisite message if `plan.md` or `tasks.md` is missing (per [contracts/command-interface.md](contracts/command-interface.md)).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Register `converge` as a core command everywhere the canonical command set is enumerated, so the template is installed, discoverable, and invocable across every integration. Per Constitution Principle III, all enumerations must change together.

**⚠️ CRITICAL**: Until registration is complete, the command cannot be installed or tested under any agent, and the integration test suite will fail.

- [X] T003 [P] Add `"converge"` with a one-line description to `SKILL_DESCRIPTIONS` in `src/specify_cli/__init__.py`.
- [X] T004 [P] Add `"converge"` to the `_FALLBACK_CORE_COMMAND_NAMES` frozenset in `src/specify_cli/extensions.py` (~L31; it is a frozenset, so simply append the entry — ordering is not significant).
- [X] T005 [P] Add a `"converge"` argument-hint entry to `ARGUMENT_HINTS` in `src/specify_cli/integrations/claude/__init__.py`.
- [X] T006 [P] Add `"converge"` to the `COMMAND_STEMS` list in `tests/integrations/test_integration_base_yaml.py`.
- [X] T007 [P] Add `"converge"` to the `COMMAND_STEMS` list in `tests/integrations/test_integration_base_toml.py`.
- [X] T008 [P] Add `"converge"` to the expected command-stems list in `tests/integrations/test_integration_base_markdown.py`.
- [X] T009 [P] Add `"converge"` to both command enumerations in `tests/integrations/test_integration_base_skills.py`: the `expected_commands` set (~L102) and the `_SKILL_COMMANDS` list (~L395).
- [X] T010 [P] Add `"converge"` to both command enumerations in `tests/integrations/test_integration_copilot.py`: the hardcoded `expected_commands` set (~L129) and the `_SKILL_COMMANDS` list (~L323).
- [X] T010a [P] Add `"converge"` to the `command_stem` parametrize list of `test_command_loads_constitution_context` in `tests/integrations/test_integration_generic.py` (~L211–L223) — converge reads the constitution, so it must reference `constitution.md` like its peer commands (Constitution III; the generic test enforces this).
- [X] T011 Run `uv run python -m pytest tests/test_agent_config_consistency.py tests/integrations -q` and confirm the new `converge` entries resolve and all command-set assertions pass (fix any enumeration missed in T003–T010a).

**Checkpoint**: `converge` is a recognized core command; the template installs across integrations and the suite is green. User-story behavior can now be added to the template.

---

## Phase 3: User Story 1 - Surface remaining work as new tasks (Priority: P1) 🎯 MVP

**Goal**: Reading spec/plan/tasks + constitution, assess the current codebase and append the remaining work as new, traceable tasks to `tasks.md` so `/speckit.implement` can complete it.

**Independent Test**: In a feature whose code omits one specified requirement, run the command and confirm a new task describing exactly that requirement is appended to `tasks.md`, with no other file changed (quickstart Scenario 1).

- [X] T012 [US1] In `templates/commands/converge.md`, add the artifact-loading step that reads `spec.md` (requirements FR-/SC-, acceptance scenarios), `plan.md` (decisions/constraints), `tasks.md` (existing tasks + referenced files), and `.specify/memory/constitution.md` — skipping constitution checks gracefully if it is an unfilled template (per [data-model.md](data-model.md) and FR-001, FR-002).
- [X] T013 [US1] Add the assessment step that scans the code paths named by the artifacts and produces `Finding` records classified as `missing`/`partial`/`contradicts`/`unrequested` with a severity, bounding scope to the feature artifacts only (FR-003, FR-004; [data-model.md](data-model.md) Finding entity).
- [X] T014 [US1] Add the task-append step implementing the [contracts/tasks-output.md](contracts/tasks-output.md) format: compute the next phase number and next task IDs from the current max, write a `## Phase N — Convergence` section at the end of `tasks.md`, one checklist item per actionable finding (FR-005, FR-006).
- [X] T015 [US1] Add explicit read-only guardrail instructions to the template: MUST NOT modify `spec.md` or `plan.md`, MUST NOT rewrite/delete existing tasks, MUST NOT modify application code — the only write is the appended Convergence phase (FR-008, FR-009, FR-010).
- [X] T016 [US1] Add the in-session findings summary output (severity-graded list/table of what was checked and what remains) ahead of the append (FR-012).

**Checkpoint**: Running the command on a feature with a gap appends a correct, traceable Convergence task and touches nothing else — MVP is functional.

---

## Phase 4: User Story 2 - Confirm convergence is complete (Priority: P2)

**Goal**: When the code already satisfies everything, report a clean "converged" result with summary counts and leave `tasks.md` unchanged.

**Independent Test**: Run against a feature whose code fully satisfies its artifacts and confirm a clean result is reported and `tasks.md` is unchanged (quickstart Scenario 3).

- [X] T017 [US2] In `templates/commands/converge.md`, add the converged-state branch: when there are no actionable findings, emit a clean "converged" summary with counts of requirements, acceptance criteria, and plan decisions checked, and explicitly do NOT modify `tasks.md` (no empty phase header) (FR-011; [contracts/tasks-output.md](contracts/tasks-output.md) clean case).
- [X] T018 [US2] Add the next-step handoff guidance to the template: on `converged` suggest proceeding to review/PR; on `tasks_appended` suggest running `/speckit.implement` to continue (FR-014).

**Checkpoint**: Both the gap path and the clean path produce correct, distinct outcomes.

---

## Phase 5: User Story 3 - Trace each remaining task to its source (Priority: P3)

**Goal**: Every appended task names the requirement/criterion/decision/constraint it satisfies and its gap type.

**Independent Test**: Run against a feature with several distinct gaps and confirm each appended task names its originating reference and gap-type label (quickstart Scenario 1 trace assertions).

- [X] T019 [US3] In `templates/commands/converge.md`, refine the append step so each task line carries its `source-ref` (e.g. `FR-003`, `SC-002`, `US1/AC2`, `plan: …`, `Constitution II`) and a `(gap-type)` label, and so constitution violations are emitted as `CRITICAL` (FR-007; [data-model.md](data-model.md) Convergence Task entity).

**Checkpoint**: Appended tasks are fully traceable and prioritized.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Hooks, cross-integration discoverability, docs, and full validation.

- [X] T020 [P] In `templates/commands/converge.md`, add the `before_converge` pre-execution hook block and the `after_converge` post-execution hook block (copied from the `analyze.md` pattern, keys renamed), ensuring `after_converge` receives the `converged` vs `tasks_appended` outcome (FR-015; [contracts/hooks.md](contracts/hooks.md)).
- [X] T021 [P] Add `converge` to the post-init guidance in `src/specify_cli/commands/init.py` (the "Next Steps" panel, ~L576–L582) as a step shown after `implement` (~L580) — using the existing `_display_cmd('converge')` helper so it renders correctly across skill/slash modes (FR-017).
- [X] T022 [P] Add a `/speckit.converge` row to the **README Core Commands table** in `README.md` (~L158–L165) — the only canonical slash-command enumeration in the repo — describing purpose, scope (code → spec), and append-only behavior (Constitution Principles III & V). Note: `docs/reference/core.md` is the `specify` CLI reference and `docs/reference/workflows.md` only defines the Full SDD Cycle workflow (which converge is not part of), so neither requires edits.
- [X] T023 Mentally apply `process_template` to `templates/commands/converge.md` and confirm no leftover `{SCRIPT}`, `$ARGUMENTS`, or `__SPECKIT_COMMAND_*__` tokens remain unresolvable and that the frontmatter is valid (FR-016).
- [X] T024 Run `uv run python -m pytest tests/test_agent_config_consistency.py tests/integrations -q` again to confirm the full suite passes after all edits.
- [X] T025 Execute the [quickstart.md](quickstart.md) scenarios 1–6 manually through a coding agent and capture agent/OS/shell + pass/fail per scenario for the PR (Constitution Principle IV — manual slash-command validation). **Validated 2026-06-10 — GitHub Copilot agent, macOS/zsh:** S1 PASS (gap→appended traceable `(missing)` task tracing FR-003); S2 PASS (implement completed T004, re-converge found 0 new); S3 PASS (converged → `tasks.md` byte-identical hash); S4 PASS (`spec.md`/`plan.md`/source unchanged, `tasks.md` append-only); S5 PASS (no `tasks.md` → non-zero exit with prerequisite message, nothing written); S6 PASS (installed + tokens resolved + post-init guidance for copilot `.agent.md` and windsurf `.md`). Automated: 2343 passed. **Re-verified 2026-06-16 — GitHub Copilot + Gemini, macOS/zsh:** Automated 2343 passed; template tokens resolve for copilot+gemini × sh+ps (no leftover `{SCRIPT}`/`__SPECKIT_COMMAND_*__`); S1 PASS (FR-002 gap → `## Phase 2 — Convergence` T003 `(missing)` appended); S2 PASS (implement closed gap, re-converge found 0); S3 PASS (converged → `tasks.md` hash unchanged); S4 PASS (spec/plan/code hashes byte-identical on append); S5 PASS (no `tasks.md` → exit 1 "Run /speckit.tasks first"); S6 PASS (converge installed for copilot `.github/prompts` + `.github/agents` and gemini `.gemini/commands/*.toml`, post-init guidance step 2.6 after implement).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately. T002 depends on T001 (same file).
- **Foundational (Phase 2)**: Depends on Setup. T003–T010a are parallelizable; T011 depends on T003–T010a. BLOCKS all user stories (command must be registered to be testable).
- **User Stories (Phase 3–5)**: All depend on Foundational completion. They edit the same template file, so within the template they are sequential, but each story is independently testable once present.
- **Polish (Phase 6)**: Depends on the desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Depends only on Foundational. The MVP.
- **US2 (P2)**: Depends on Foundational; logically builds on the assessment from US1 (the converged state is "US1 found nothing"), so implement after US1.
- **US3 (P3)**: Depends on Foundational; refines the US1 append step, so implement after US1.

### Within the command template

- T012 (load) → T013 (assess) → T014 (append) → T015 (guardrails) → T016 (summary).
- T017/T018 (US2) and T019 (US3) modify the same file after US1 — apply sequentially.

### Parallel Opportunities

- **Phase 2**: T003, T004, T005, T006, T007, T008, T009, T010, T010a all touch different files → run in parallel; then T011.
- **Phase 6**: T020 (template), T021 (init.py), T022 (docs) touch different files → run in parallel; then T023/T024/T025.
- The template-body tasks (T001–T002, T012–T019) all edit `templates/commands/converge.md` and must be sequential.

---

## Parallel Example: Phase 2 Foundational

```bash
# These edit different files and can be done together:
Task: T003 Add "converge" to SKILL_DESCRIPTIONS in src/specify_cli/__init__.py
Task: T004 Add "converge" to _FALLBACK_CORE_COMMAND_NAMES in src/specify_cli/extensions.py
Task: T005 Add "converge" hint in src/specify_cli/integrations/claude/__init__.py
Task: T006 Add "converge" to COMMAND_STEMS in tests/integrations/test_integration_base_yaml.py
Task: T007 Add "converge" to COMMAND_STEMS in tests/integrations/test_integration_base_toml.py
Task: T008 Add "converge" to tests/integrations/test_integration_base_markdown.py
Task: T009 Add "converge" to tests/integrations/test_integration_base_skills.py
Task: T010 Add "converge" to tests/integrations/test_integration_copilot.py
Task: T010a Add "converge" to tests/integrations/test_integration_generic.py
# Then:
Task: T011 Run the integration + agent-config test suite
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Setup (T001–T002).
2. Complete Phase 2: Foundational registration (T003–T011) — CRITICAL, blocks everything. (Includes T010a.)
3. Complete Phase 3: User Story 1 (T012–T016).
4. **STOP and VALIDATE**: Run quickstart Scenario 1 — confirm a gap becomes a traceable appended task and nothing else changes. This is a usable, shippable increment.

### Incremental Delivery

- Add US2 (T017–T018) for the clean-converged experience and handoffs.
- Add US3 (T019) for full traceability.
- Finish with Polish (T020–T025): hooks, discoverability, docs, and full validation.
