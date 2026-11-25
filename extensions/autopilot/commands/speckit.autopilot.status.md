---
description: "Report the autopilot run: stage, each epic's progress, recent events, and why any epic failed or needs a human. Read-only"
---

# Autopilot Status

Report where the current autopilot run stands and what, if anything, needs the user. This command is **read-only**: it never starts, stops, resets or merges anything.

## User Input

```text
$ARGUMENTS
```

Optional: an epic id (for example `E2`) to report on that epic in depth.

## Steps

1. Run `python3 .specify/extensions/autopilot/scripts/python/autopilot.py status` from the repository root (`python` where `python3` is unavailable) and read the JSON.

2. Report, briefly:
   - **Stage** in plain words: no plan yet; plan waiting for approval; running (with the drive's pid); interrupted (drive not running, work left); waiting for the final-merge approval; landed. Mention a pending stop request.
   - **Epics**: a table of id, status, iterations and a short note. Statuses mean: `pending` (waiting for dependencies or a free slot), `running`, `awaiting-human` (the developer asked a product question and waits; the others continue), `merged`, `failed` (cap or timeout), `escalated` (needs a human), `blocked` (a dependency did not merge).
   - **Questions for the product owner** (`questions_for_human`): each question with its options and the lead's recommendation. Say they are answered with `__SPECKIT_COMMAND_AUTOPILOT_RUN__`.
   - **Team decisions**: how many decisions `.specify/autopilot/decisions.md` holds, and the latest few in one line each.
   - **Budget**: `agent_calls_used` against `run.max_agent_calls` from `.specify/extensions/autopilot/autopilot-config.yml`, and any `halted` reason.
   - **Recent events**: only the meaningful ones (start, merged, escalated, blocked, retry, halt).

3. For each `failed` or `escalated` epic, or the epic named in the input, explain **why** from the evidence. Do not guess.
   - The epic's worktree is in `.specify/autopilot/state.json` under `epics.<id>.worktree`. Its pipe files are in `<worktree>/.specify/autopilot/pipes/<feature-dir-name>/`. Read `pipe.json`, the latest `gate-N.md`, and `review-N.json` if present.
   - Scheduler-side causes (merge conflict, checks failing after merge, commit hook failure, worktree setup) are in the epic's `reason` and in `.specify/autopilot/logs/<id>-*.log`.
   - Summarize the cause in one or two sentences and quote the decisive failure line.

4. End with the single most useful next step:
   - Running: nothing to do. Check back later.
   - Interrupted, questions waiting for the product owner, or the plan or final merge is waiting: `__SPECKIT_COMMAND_AUTOPILOT_RUN__`.
   - Failed or escalated epics: `__SPECKIT_COMMAND_AUTOPILOT_RECOVER__ <id>`.
