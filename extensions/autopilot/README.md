# Autopilot Extension

Autonomous Spec-Driven Development for Spec Kit, driven from your agent's chat. The agent acts as **conductor**: it plans **epics** from your requirements as a dependency DAG and holds two human gates in the conversation, the epic plan and the final merge. Between them, plain code runs each epic as an unattended **pipe** in its own git worktree. Each pipe loops `implement → converge → gate → review` until a **deterministic gate** and an **independent reviewer** pass. Passed epics merge one at a time into an integration branch.

It runs like a development team: you are the **product owner**, the agent is the **team lead**, each pipe is a **developer**. No developer works blind. Each reads the lead's team handbook (`program.md`), an onboarding brief generated for its epic (what is already built, who works in parallel on what, who waits on it), and the team's decision log before every step. When a guess would be costly it asks the lead, and only product decisions reach you.

Full reference: [Autopilot (autonomous SDD)](../../docs/reference/agentic-autopilot.md).

## Get started

Bootstrap (the only terminal step; your agent can run it for you):

```bash
specify init --here --force --integration claude --extension autopilot
```

Then, in the agent's chat:

```text
/speckit.autopilot.setup
/speckit.autopilot.run requirements=docs/requirements
```

## Commands

| Command | Purpose |
| --- | --- |
| `speckit.autopilot.setup` | Install the workflows, fill the gate from `AGENTS.md` / CI, prove it green, set limits, commit the setup |
| `speckit.autopilot.run` | Conductor: preflight, plan, gate 1 in chat, detached unattended drive, gate 2 in chat, land. Re-run to continue; `stop` halts new pipes |
| `speckit.autopilot.status` | Read-only: stage, epics, budget, recent events, cause of any failure |
| `speckit.autopilot.recover` | Diagnose failed or escalated epics, fix with your approval, reset and resume |
| `speckit.autopilot.epics` | Internal: plan epics into `.specify/autopilot/epics.json` and write the team handbook `program.md` |
| `speckit.autopilot.lead` | Internal: the team lead answering a developer's questions, or handing product questions to you |
| `speckit.autopilot.review` | Internal: independent read-only review of one epic's diff, as JSON |

Engine (used by the commands and the headless workflows, not by you): `scripts/python/autopilot.py`, stdlib-only Python 3.11+.

Config: `autopilot-config.yml` (gate checks, caps, scheduler settings), installed from `config-template.yml`.

Workflows (installed by setup): `autopilot-epic` (the headless pipe) and `autopilot` (the conductor for CI and terminals).

## What the gate checks

- `spec.md` has no `[NEEDS CLARIFICATION` markers.
- `tasks.md` has no unchecked tasks (so the last `/speckit.converge` appended nothing).
- Every configured project command (tests, lint, types, project-specific checks) exits 0.
- Every acceptance scenario `NNN-USx-ASy` appears in a test file.
- Then an independent reviewer's `blocker`/`major` findings fail the iteration, whatever verdict it declares.

Failures are appended to `tasks.md` as remediation tasks for the next `implement`. Hard caps (iterations, wall time, agent-call budget) and repeated-identical-failure detection stop runaway loops.
