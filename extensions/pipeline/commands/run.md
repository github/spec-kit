---
description: "Run the full Spec Kit pipeline (specify → clarify → plan → tasks → analyze → implement) from one feature description, with a single interactive clarify checkpoint and a deterministic, tailorable phase order."
scripts:
  sh: scripts/bash/resolve-phases.sh
  ps: scripts/powershell/resolve-phases.ps1
---

# Pipeline: run

Carry one feature from a plain-language description to an implemented change by chaining the existing Spec Kit phase commands into a single guided run. You (the agent) **are** the orchestrator: you follow this procedure turn by turn, invoking each `/speckit.*` command in order and verifying its artifact landed before moving on. This replaces hand-running `/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.analyze`, and `/speckit.implement` one at a time and hand-resolving analyze findings.

## Input

`$ARGUMENTS` — the feature description, optionally followed by flags:

- `--skip <csv>` — drop default phases (e.g. `--skip clarify,analyze`). Cannot drop `specify` or `implement`.
- `--add <csv>` — insert optional phases: `constitution` (before specify), `checklist` (after tasks).
- `--yes` — unattended run. Does **not** skip clarification; instead you answer the clarify questions yourself, grounded in the spec and repo conventions, and halt before `plan` if a question is too consequential to answer without a human (see Step 4). Use `--skip clarify` if you genuinely want zero clarification.

If the feature description is empty, report the missing input and stop — do not start.

## Step 1 — Resolve the phase plan (deterministic)

Run the resolver once and branch on its exit code:

```
{SCRIPT}  --skip "<skip csv>" --add "<add csv>" --json
```

(`{SCRIPT}` is this command's configured `scripts.sh` / `scripts.ps`.)

Exit codes: `0` OK · `10` unknown phase name · `11` skip/add name conflict · `12` add-name not insertable · `13` skip targets a required phase · `14` dependency break. On any non-zero code, report the resolver's stderr message verbatim and stop — do not run a partial or incoherent pipeline. The order is deterministic: the resolver consumes skip/add as sets and derives order from one fixed key, so flag ordering never changes the plan.

## Step 2 — Preflight

Confirm the project is Spec Kit-initialized (a `.specify/` directory exists) and that every `/speckit.*` command named in the resolved plan is available in this agent's command set. Report anything missing now — never mid-pipeline. If `--add constitution` or `--add checklist` was requested but that command isn't installed, report and stop.

## Step 3 — Execute each phase in order

For each phase in the resolved plan, invoke its `/speckit.*` command (the `command` field from the resolver output). After each phase:

- **Verify the artifact.** Confirm the expected file was written (`spec.md`, `plan.md`, `tasks.md`, etc.) before proceeding. A phase reporting success is not enough — check the artifact is on disk.
- **Halt on failure.** If a phase fails and the failure is not something you can safely resolve, stop and name the phase and reason. Never proceed past a broken artifact.

Keep a short running ledger (which phases ran, which were skipped, outcome of each) so the run survives a context reset.

## Step 4 — The clarify gate

`clarify` is the single interactive checkpoint; everything after it runs unattended.

**Default (no `--yes`)** — run `/speckit.clarify`, present its questions to the human, and **end your turn to wait** for answers. This is the one human checkpoint.

**`--yes` set** — no human is present, so `--yes` does not mean "skip clarification", it means "answer it responsibly yourself":

1. Run `/speckit.clarify`'s question generation as normal, but don't present the questions to a human.
2. Answer each question as the operator plausibly would, grounded strictly in the spec's own content, the project's constitution/conventions, and established repo patterns. Integrate each answer into the spec exactly as `/speckit.clarify` integrates a human's answer.
3. Emit one line noting that clarify was answered unattended, not by a human, so the audit trail is honest.
4. **If any question is too consequential to answer without a human** — insufficient grounding, security/scope/privacy stakes, or a materially shape-changing decision the spec leaves open — do **not** guess. Halt before `plan`, name the unresolved question and why. This is a correct outcome, not a failure: it means the run recognized it should not proceed unattended past this point.

## Step 5 — The analyze → resolve loop

After `/speckit.analyze` reports findings, fix each finding (edit the spec/plan/tasks as needed), then re-run `/speckit.analyze`. Repeat **up to 3 cycles**. If findings remain unresolved after the third cycle, halt and report them rather than implementing against a known-inconsistent spec.

## Step 6 — Unattended discipline (clarify-satisfied → implement)

From the moment clarify is satisfied through `implement`, run without acknowledgment chatter between phases, but:

- **Log every skip and every fallback.** Silent deviation from the plan is not allowed — if you skip or work around something, say so in the ledger.
- **Halt on destructive or irreversible actions** during `implement` (deleting data, force-pushing, rewriting shared history) and ask, rather than proceeding blindly.
- Any phase failure that isn't auto-resolvable, or is unsafe to continue past, halts **before** `implement`, naming the phase and reason.

## Hard stops

| Condition | Behavior |
|---|---|
| Empty feature description | Report missing input; do not start. |
| Resolver returns non-zero | Report its message; run no phase. |
| `.specify/` or a required `/speckit.*` command missing at preflight | Report; do not start. |
| Expected artifact absent after a phase | Halt, name the phase; do not proceed. |
| Analyze findings unresolved after 3 cycles | Halt; report the unresolved findings. |
| A clarify question too consequential to answer unattended (`--yes`) | Halt before `plan`, name the question and why; never guess. |
| Destructive/irreversible action during implement | Halt and ask. |

## Notes

- **Agent-neutral.** This command drives only stock `/speckit.*` commands and ships no dependency on any specific AI agent, model, or vendor tooling. In an agent that renders Spec Kit commands as skills, the same phases appear as `speckit-plan`, `speckit-tasks`, etc. — invoke whichever form your agent exposes.
- **Preview first.** Run `/speckit.pipeline.preview` with the same flags to see the resolved plan before committing to a full run.
