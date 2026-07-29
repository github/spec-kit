---
description: Run the short Spec Kit flow end-to-end (specify → plan → tasks → implement → converge) with a single stop before implementation.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Model configuration gate (MANDATORY — before anything else)**:
- Read `.specify/models.json` in the project root **first**. If that read succeeds, this is the configuration: use it and move on. Do **not** read, stat, or mention any other path.
- Only when the project file does not exist, try `~/.specify/models.json`. That path is outside the project, so the host may deny access: a permission denial or any read error there means "not found" - never abort the command because of it.
- Never abort this command because a configuration read failed while another configuration source already succeeded.
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

**Orchestrator dispatch (MANDATORY - this is a procedure you execute, not advice)**:

You are the `manager` (communicator). **You have no permission to create or edit project artifacts in this command.** Every substantive step is performed by a worker agent that you dispatch.

**Phases**: each phase applies its own command's dispatch procedure; classify every substantive step of the phase you are running.

__SPECKIT_DISPATCH_BLOCK__

**Self-check before every `write`/`edit` call**: if you are about to create or modify a project file and you did not print a `DISPATCH` line for it, you are violating this command. Stop and dispatch instead. Reading files, running the prerequisite scripts, asking the user questions, merging worker output, and reporting are the only things you may do yourself.

At the end of the command, list every `DISPATCH` line you emitted, so the user can see which levels and models did the work.

**Flag parsing**: extract flags from the user input before using the rest as the feature description:

- `--bypass` — skip the implementation gate ONLY (no stop before implement). It does NOT suppress user questions: every phase still asks the user whatever it needs.
- `--loop` — after implementing, loop implement ↔ converge until converged (max 5 iterations). Without it, converge runs exactly once.
- Everything else in the input is the **feature description** passed to the specify phase. If the description is empty, STOP and ask the user what to build.

## Goal

Execute the complete **short flow** automatically, chaining each Spec Kit phase as soon as the previous one finishes:

1. `__SPECKIT_COMMAND_SPECIFY__` (feature description)
2. `__SPECKIT_COMMAND_PLAN__`
3. `__SPECKIT_COMMAND_TASKS__`
4. **Implementation gate** (unless `--bypass`)
5. `__SPECKIT_COMMAND_IMPLEMENT__`
6. `__SPECKIT_COMMAND_CONVERGE__` (once, or looped with `--loop`)

## Execution Steps

Run each phase by **fully following the instructions of the corresponding Spec Kit command** available to you in this project (same commands the user would invoke manually). Do NOT reimplement or shortcut a phase: load that command's instructions and execute them completely, then move on.

### Phase rules (apply to every phase)

- Announce each phase before starting: `▶ Flow [N/6]: <command>`.
- **User questions are NEVER suppressed — in ANY phase, under ANY flag**: if a phase needs a user decision, clarification, or confirmation (per its own instructions), ASK and WAIT for the answer before continuing. Never auto-answer, never assume defaults for something the phase would normally ask about, never skip a question because the flow is "automatic" or because `--bypass` was passed. `--bypass` removes ONLY the implementation gate, nothing else. Automation chains phases; it does not silence questions.
- If a phase FAILS or its output is invalid, STOP the flow, report which phase failed and why, and tell the user how to resume (fix the issue, then re-run the individual command and continue manually, or re-run this flow).
- Do not skip phases. Do not reorder phases.

### 1. Specify

Execute `__SPECKIT_COMMAND_SPECIFY__` with the feature description from the user input.

### 2. Plan

Execute `__SPECKIT_COMMAND_PLAN__`. If the user provided tech-stack guidance in the input, pass it along; otherwise derive sensible choices from the spec and existing codebase, and ask the user if the choice is genuinely ambiguous.

### 3. Tasks

Execute `__SPECKIT_COMMAND_TASKS__`. Every task must carry its `[C:n<level>->model]` label per the models.json mapping.

### 4. Implementation gate

- If `--bypass` was passed: skip this gate entirely and continue.
- Otherwise **STOP and ask the user for confirmation** before implementing. Show a compact summary:
  - Feature directory and branch
  - Task count by phase and by complexity/model
  - Anything flagged during planning
  - The question: "Proceed with implementation? (yes / no / adjust)"
- Only continue after an explicit yes. If the user says no or asks for adjustments, stop the flow and apply what they ask.

### 5. Implement

Execute `__SPECKIT_COMMAND_IMPLEMENT__` (model-aware dispatch per task label applies).

### 6. Converge

Execute `__SPECKIT_COMMAND_CONVERGE__`:

- **Without `--loop`**: run converge once and report its result (converged or remaining tasks appended).
- **With `--loop`**: if converge appends new tasks, run `__SPECKIT_COMMAND_IMPLEMENT__` again and then converge again. Repeat until converge reports converged, up to a maximum of **5 iterations**. If still not converged after 5, STOP and report what remains.

## Completion report

At the end, output:

- Phases completed (and iterations used if `--loop`)
- Feature directory, spec/plan/tasks paths
- Implementation summary: tasks completed / total
- Converge status: converged or remaining work
- Suggested next step (review, PR, or re-run with `--loop`)
