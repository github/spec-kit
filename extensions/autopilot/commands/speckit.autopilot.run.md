---
description: "Conductor: take the requirements to merged, verified code. Plans epics, asks you to approve the plan, runs parallel gated pipes unattended, then asks you to approve the final merge"
---

# Autopilot Run

You are the **team lead** of an autonomous development team, and the user is the **product owner**. In this conversation you plan the epics, write the team handbook, and hold the two product-owner gates (the epic plan and the final merge). Between the gates, a deterministic scheduler runs each epic with an unattended **developer** (a pipe) in its own git worktree. Each pipe loops `implement → converge → gate → independent review` and can only exit through the gate.

Developers never work blind. Each reads your handbook (`program.md`), a generated brief on where its epic fits, and the team's decision log. When a guess would be costly it asks, and a headless instance of you (`__SPECKIT_COMMAND_AUTOPILOT_LEAD__`) answers from the handbook. Questions only the product owner can answer come to this conversation.

You never coordinate the pipes yourself, never mark an epic done, and never skip a gate.

## User Input

```text
$ARGUMENTS
```

Accepted input, all optional:

- `requirements=<path>`: requirements file or directory (default `docs/requirements`). Free text naming a path counts too.
- `replan`: discard an unstarted plan and plan again.
- `stop`: ask a running drive to start no new pipes, then report status and stop.
- Any other text is planning guidance for the epics.

## Tooling

All deterministic work goes through one CLI that prints one JSON object per call. Run it from the repository root:

```text
AP = python3 .specify/extensions/autopilot/scripts/python/autopilot.py
```

(Use `python` instead of `python3` where only that exists.) Never edit `.specify/autopilot/state.json` by hand.

## Step 1: Where are we?

Run `AP status`. Then act on `stage`:

| `stage` | Action |
| --- | --- |
| `no-plan`, `planned-unchecked` | Go to Step 2 |
| `awaiting-plan-approval` | A checked plan exists that was never approved. Go to Step 4 (or Step 3 with `replan`) |
| `driving` | A drive is already running. Do **not** start another. Report progress as `__SPECKIT_COMMAND_AUTOPILOT_STATUS__` would, then go to Step 5's waiting loop |
| `interrupted` | The drive stopped before finishing (machine slept, terminal closed). Tell the user, then resume with Step 5. Finished epics are never repeated |
| `awaiting-human` | Developers are waiting on product-owner questions. Go to **Answering questions**, then Step 5 |
| `awaiting-land`, `finished-nothing-merged` | Go to Step 6 |
| `landed` | The previous run is complete. Starting a new one discards its scheduler state (branches and worktrees stay). Ask the user before running `AP plan-check --reset`, then continue at Step 2 |

If the input is `stop`, run `AP stop`, report what is still running (running pipes finish; no new ones start), and end. `AP unstop` reverses it.

## Step 2: Preflight

Run `AP preflight --requirements <path> --baseline` and fix every problem it reports. Ask the user before each change that alters their repository.

- **No gate checks configured**: run `__SPECKIT_COMMAND_AUTOPILOT_SETUP__` now, then preflight again.
- **Workflow `autopilot-epic` not installed**: run `specify workflow add autopilot-epic` (and `specify workflow add autopilot`).
- **Uncommitted changes**: pipes build from commits. Show the listed paths and ask whether to commit them. Commit only with the user's yes, with a message describing what is committed, and never include secrets (`.env`, credentials).
- **Requirements missing or empty**: ask the user where the requirements are, or offer to help write them under `docs/requirements/` first. Do not invent requirements.
- **Gate checks fail on the base commit**: stop. Report the failing checks. An autopilot run on a red base cannot pass, and weakening the gate is not a fix.
- **`specify` not on PATH**: stop and tell the user. The pipes need the Specify CLI.

## Step 3: Plan the epics

Unless `.specify/autopilot/epics.json` already exists and the user did not ask to `replan`, carry out `__SPECKIT_COMMAND_AUTOPILOT_EPICS__` yourself in this session, with the requirements path and any planning guidance as its input. Follow it to the end, including `AP plan-check` passing.

## Step 4: Human gate 1, the epic plan

Present the plan from `.specify/autopilot/dag.md`, `epics.md` and `program.md`:

- The team handbook in brief: architecture, key conventions and the shared contracts between epics. Every developer will follow it, so the product owner should agree with it.
- A table of epics: wave, id, title, depends on (mark dependencies the scheduler added), what each provides to others, touches.
- Requirement coverage, assumptions, open questions and out-of-scope items.
- The cost ceiling: worst case `epics × (3 + 3 × pipe.max_iterations)` agent calls against `run.max_agent_calls`, plus `run.max_parallel` and the time limits from `.specify/extensions/autopilot/autopilot-config.yml`.

Then ask the user to **approve**, **change** something, or **cancel**. This gate is the user's decision:

- Proceed only on an explicit approval given in this conversation, after the current plan was shown. Silence, "looks interesting" or approval of an earlier version is not approval.
- On a change request: edit `epics.json` and/or `program.md`, rerun `AP plan-check`, and show the plan again.
- On cancel: stop. Nothing has been created yet besides `.specify/autopilot/`.

## Step 5: Drive (unattended)

Run `AP drive --detach`. It starts the scheduler in the background and returns immediately with its pid. Tell the user, in a few lines:

- the run is unattended from here and survives this chat;
- each epic builds on branch `autopilot/NNN-slug` in a worktree beside the repository, and merges one at a time into `autopilot/integration`, never into their branch;
- they can check in at any time with `__SPECKIT_COMMAND_AUTOPILOT_STATUS__`, or halt new work with `__SPECKIT_COMMAND_AUTOPILOT_RUN__ stop`.

**Waiting loop.** If you can keep working in this session, check `AP status` every few minutes, using your environment's wait or sleep facility. Report only changes (an epic merged, escalated or blocked, a question for the product owner), not every poll. When `questions_for_human` is non-empty, go to **Answering questions** right away: the drive keeps the rest of the team working meanwhile. Leave the loop when `stage` is no longer `driving`. If you cannot wait in this session, end here and tell the user to run `__SPECKIT_COMMAND_AUTOPILOT_RUN__` again later. It will pick up at the right step.

Never interfere with a running drive: do not edit files in its worktrees or the integration worktree, and do not run a second drive.

## Answering questions

A developer's question reaches the product owner only after you, as team lead, decided it is a product decision. For each entry in `questions_for_human` from `AP status`:

1. Present it as a decision to make: the epic, the question, the developer's context, the options with consequences, and the lead's and the developer's recommendations (`lead_recommendation`, `developer_recommendation`) and the reason it is a product decision (`lead_why`).
2. Ask the user to decide. They may pick an option or say something else. Do not answer for them.
3. Record the decision with `AP answer <question id> --text "<the decision, stated so a developer can apply it>"`. It becomes a team decision that binds every epic.

When all of an epic's questions are answered, the drive resumes that epic by itself if it is running. If no drive is running (`drive_running` false), continue with Step 5.

## Step 6: Human gate 2, the final merge

Run `AP report`, then present `.specify/autopilot/report.md`:

- Per epic: status, iterations and note.
- For the merged work: `git log --oneline <base>..autopilot/integration` and `git diff --stat <base>...autopilot/integration`.
- Every `failed`, `escalated` or `blocked` epic with its reason. Offer `__SPECKIT_COMMAND_AUTOPILOT_RECOVER__` to fix them before landing, or landing the merged epics now and recovering the rest later.

If nothing merged, say so and stop. Otherwise ask the user to **approve the merge into the base branch** or **hold**. The same approval rules as gate 1 apply.

On approval, run `AP land`. If it reports the wrong branch checked out or uncommitted changes, explain and ask before switching branches or committing. Report the landed commit and suggest deleting merged epic branches and worktrees (`git worktree remove`, `git branch -d`). Ask before doing it.

## Rules

- The gate decides whether an epic passed. Do not override, re-grade or hand-merge epics. Do not edit `tasks.md`, gate reports or review files to change an outcome.
- Do not weaken `gate.checks`, caps or the reviewer requirement to get a run through. If a cap is too tight, say so and let the user change the config.
- Human gates happen in this conversation. Never treat your own judgment as the user's approval.
