---
description: "Act as the human in the loop for failed or escalated autopilot epics: diagnose the cause, fix it with the user's approval, reset the epic and resume the run"
---

# Autopilot Recover

Some epics ended `failed` or `escalated`, or were `blocked` by one that did. The gate stops exactly where an unattended agent should not guess. This command brings the user in: find the cause, agree a fix, apply it, then hand the epic back to the scheduler.

## User Input

```text
$ARGUMENTS
```

Optional: one or more epic ids (for example `E2 E5`). Empty means every `failed` and `escalated` epic.

## Tooling

```text
AP = python3 .specify/extensions/autopilot/scripts/python/autopilot.py
```

## Steps

1. **Check that nothing is running.** Run `AP status`. If `drive_running` is true, recover nothing: changing a worktree under a live drive corrupts the run. Tell the user to wait or halt new work with `__SPECKIT_COMMAND_AUTOPILOT_RUN__ stop`, then end.

2. **Diagnose each target epic** from evidence, as `__SPECKIT_COMMAND_AUTOPILOT_STATUS__` does: its `reason`, then the pipe's `pipe.json`, latest `gate-N.md`, `review-N.json`, and `.specify/autopilot/logs/<id>-*.log`. Classify the cause:

   | Cause | Typical evidence | Fix |
   | --- | --- | --- |
   | **Ambiguous spec** | clarification markers in `spec.md`; the reviewer and implementer disagree on intent | Ask the user the open question. Edit `spec.md` in the epic's worktree to record the answer |
   | **Environment or gate config** | the same check fails identically every iteration with an environment error (missing tool, dependency not installed, wrong command) | Fix `gate.checks` or `run.setup` in `.specify/extensions/autopilot/autopilot-config.yml`, or install the missing tool, with the user's approval |
   | **Implementation stuck** | the same test or review finding repeats; the cap was reached | With the user's approval, make the minimal fix in the epic's worktree yourself, or add a precise task to `tasks.md` in a new phase so the next pipe iteration does it |
   | **Merge conflict** | reason mentions a conflict with the integration branch | In the epic's worktree, rebase onto `autopilot/integration`, resolve the conflict with the user, and commit. The scheduler verifies again on merge |
   | **Plan problem** | the epic is too big to converge, or depends on work no epic does | Say so. Re-planning means a new run, so offer to land what merged first |
   | **Infrastructure** | agent CLI crashed, timed out, or a permissions prompt blocked it | Report it. Often it can just be reset |

3. **Agree the fix.** Present the cause and the proposed fix per epic, and get the user's yes before changing anything. Never weaken a gate check, delete or skip a test, or raise a cap without the user explicitly choosing that.

4. **Apply** the agreed fixes. Work in the epic's worktree (`epics.<id>.worktree` in `.specify/autopilot/state.json`), never in the integration worktree. Run the relevant gate check yourself afterwards (`AP checks` from that worktree) to confirm the fix.

5. **Hand back.** For each fixed epic run `AP reset <id>`. This returns the epic and the epics it blocked to `pending`, grants a fresh iteration allowance, and restarts its pipe at the build loop without re-running specify. If a stop request is pending and the user wants to continue, run `AP unstop`. Then resume with `AP drive --detach`, or tell the user to run `__SPECKIT_COMMAND_AUTOPILOT_RUN__`, which resumes and later holds the final-merge gate.

6. Report what was fixed, what was reset, and what still needs a decision.
