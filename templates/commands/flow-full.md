---
description: Run the full Spec Kit flow end-to-end (constitution → specify → clarify → plan → checklist → tasks → analyze → implement → converge) with a single stop before implementation.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Model configuration gate (MANDATORY — before anything else)**:
- Check for a model configuration file, in this order:
  1. `.specify/models.json` in the project root
  2. `~/.specify/models.json` (user-level fallback)
- If NEITHER file exists, **STOP immediately**. Do not proceed with any other step. Output:

  ```
  ## Model Configuration Required

  No models.json found (.specify/models.json or ~/.specify/models.json).
  Spec Kit needs to know which models are available to this agent before running.

  Run `__SPECKIT_COMMAND_MODELS__` first, then re-run this command.
  ```

- If a file exists, read it (project file wins) and keep it in context for this command:
  - `manager` is the communicator/orchestrator: it classifies each task/step's level (1-5) and delegates; it never implements tasks.
  - `by_complexity` maps task complexity levels (`5` = critical, `4` = complex, `3` = moderate/workhorse, `2` = simple, `1` = trivial, plus optional specialized keys) to the models that should execute such tasks.
  - Level `5` models are reserved for very few cases (the manager role and rare exceptionally hard tasks).
- If the file exists but cannot be parsed as JSON, or is missing `manager` or `by_complexity`, STOP and tell the user to re-run `__SPECKIT_COMMAND_MODELS__` to regenerate it.

**Orchestrator dispatch (MANDATORY — applies to every phase below)**:
- You are the `manager` (communicator) for the whole flow. You never produce artifacts yourself; every phase runs through its own orchestrator dispatch block.
- When you execute a phase, apply that phase command's dispatch rules: classify each substantive step's level (`5` critical → `1` trivial), look it up in `by_complexity`, and dispatch it to the first candidate through its `executors` entry.
- Dispatch is optimistic: a failed invocation falls through to the next candidate in that level's list. If every candidate fails, report the attempts and only then continue in-session.
- Keep in the manager only: phase sequencing, gates, classification, user questions, merging worker output, and reporting.
- Report per phase which levels were dispatched and to which models, so the user can see the orchestrator working.

**Flag parsing**: extract flags from the user input before using the rest as the feature description:

- `--bypass` — skip the implementation gate ONLY (no stop before implement). It does NOT suppress user questions: every phase still asks the user whatever it needs.
- `--loop` — after implementing, loop implement ↔ converge until converged (max 5 iterations). Without it, converge runs exactly once.
- Everything else in the input is the **feature description** passed to the specify phase. If the description is empty, STOP and ask the user what to build.

## Goal

Execute the complete **full flow** (production quality gates included) automatically, chaining each Spec Kit phase as soon as the previous one finishes:

1. `__SPECKIT_COMMAND_CONSTITUTION__` (only if missing — see below)
2. `__SPECKIT_COMMAND_SPECIFY__` (feature description)
3. `__SPECKIT_COMMAND_CLARIFY__`
4. `__SPECKIT_COMMAND_PLAN__`
5. `__SPECKIT_COMMAND_CHECKLIST__`
6. `__SPECKIT_COMMAND_TASKS__`
7. `__SPECKIT_COMMAND_ANALYZE__`
8. **Implementation gate** (unless `--bypass`)
9. `__SPECKIT_COMMAND_IMPLEMENT__`
10. `__SPECKIT_COMMAND_CONVERGE__` (once, or looped with `--loop`)

## Execution Steps

Run each phase by **fully following the instructions of the corresponding Spec Kit command** available to you in this project (same commands the user would invoke manually). Do NOT reimplement or shortcut a phase: load that command's instructions and execute them completely, then move on.

### Phase rules (apply to every phase)

- Announce each phase before starting: `▶ Flow [N/10]: <command>`.
- **User questions are NEVER suppressed — in ANY phase, under ANY flag**: if a phase needs a user decision, clarification, or confirmation (per its own instructions), ASK and WAIT for the answer before continuing. Never auto-answer, never assume defaults for something the phase would normally ask about, never skip a question because the flow is "automatic" or because `--bypass` was passed. `--bypass` removes ONLY the implementation gate, nothing else. This applies especially to `clarify`, whose questions MUST be answered by the user. Automation chains phases; it does not silence questions.
- If a phase FAILS or its output is invalid, STOP the flow, report which phase failed and why, and tell the user how to resume (fix the issue, then re-run the individual command and continue manually, or re-run this flow).
- Do not skip phases (except constitution when it already exists). Do not reorder phases.

### 1. Constitution

Check `.specify/memory/constitution.md`:

- If it already contains real project principles (not just the unfilled template), **skip** this phase and note "constitution: already present".
- If it is missing or still the empty template, execute `__SPECKIT_COMMAND_CONSTITUTION__`. Use principles from the user input if provided; otherwise ask the user for their core principles (or explicit permission to generate sensible defaults).

### 2. Specify

Execute `__SPECKIT_COMMAND_SPECIFY__` with the feature description from the user input.

### 3. Clarify

Execute `__SPECKIT_COMMAND_CLARIFY__`. Ask the user its questions and wait for their answers; fold them into the spec per that command's instructions.

### 4. Plan

Execute `__SPECKIT_COMMAND_PLAN__`. If the user provided tech-stack guidance in the input, pass it along; otherwise derive sensible choices from the spec and existing codebase, and ask the user if the choice is genuinely ambiguous.

### 5. Checklist

Execute `__SPECKIT_COMMAND_CHECKLIST__`. If checklist items FAIL, fix the spec/plan at the source and re-validate before continuing.

### 6. Tasks

Execute `__SPECKIT_COMMAND_TASKS__`. Every task must carry its `[C:n<level>->model]` label per the models.json mapping.

### 7. Analyze

Execute `__SPECKIT_COMMAND_ANALYZE__`. If it reports CRITICAL issues, STOP, fix them at the source (spec/plan/tasks), re-run analyze, and only continue when no critical issues remain. Non-critical findings: report them and continue.

### 8. Implementation gate

- If `--bypass` was passed: skip this gate entirely and continue.
- Otherwise **STOP and ask the user for confirmation** before implementing. Show a compact summary:
  - Feature directory and branch
  - Task count by phase and by complexity/model
  - Checklist and analyze results (issues fixed / remaining non-critical findings)
  - The question: "Proceed with implementation? (yes / no / adjust)"
- Only continue after an explicit yes. If the user says no or asks for adjustments, stop the flow and apply what they ask.

### 9. Implement

Execute `__SPECKIT_COMMAND_IMPLEMENT__` (model-aware dispatch per task label applies).

### 10. Converge

Execute `__SPECKIT_COMMAND_CONVERGE__`:

- **Without `--loop`**: run converge once and report its result (converged or remaining tasks appended).
- **With `--loop`**: if converge appends new tasks, run `__SPECKIT_COMMAND_IMPLEMENT__` again and then converge again. Repeat until converge reports converged, up to a maximum of **5 iterations**. If still not converged after 5, STOP and report what remains.

## Completion report

At the end, output:

- Phases completed (and iterations used if `--loop`)
- Feature directory, spec/plan/tasks paths
- Quality gates summary: clarify questions answered, checklist result, analyze result
- Implementation summary: tasks completed / total
- Converge status: converged or remaining work
- Suggested next step (review, PR, or re-run with `--loop`)
