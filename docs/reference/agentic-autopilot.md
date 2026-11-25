# Autopilot (autonomous SDD)

The core `/speckit.*` process needs a person to run each step. The **autopilot** takes a set of requirements and drives them to merged, verified code without that: a conductor plans **epics**, parallel **pipes** build them in git worktrees, and each pipe can leave its loop only through a **deterministic gate**. People decide twice, on the epic plan and on the final merge. Everything between those two gates runs unattended.

The autopilot is a bundled, opt-in extension (`autopilot`) plus two workflows (`autopilot-epic`, `autopilot`). It reuses the core commands unchanged.

```text
requirements (docs/requirements)
      │
  CONDUCTOR   /speckit.autopilot.epics plans epics once → epics.json
      │       plan-check: validate DAG, serialize overlapping epics, assign specs/NNN-slug
  ◆ human gate: approve the epic plan (dag.md)
      │
  SCHEDULER   plain code: worktree + branch per epic, ≤ max_parallel pipes, caps
 ┌────┼────┐
 PIPE PIPE PIPE   specify → plan → tasks → ⟲ implement → converge → GATE → review ⟲
 └────┼────┘      exits only when the gate and an independent reviewer pass
  MERGE       one epic at a time into autopilot/integration, re-verified after each merge
      │
  ◆ human gate: approve the final merge (report.md) → land into the base branch
```

## Principles

These come from the autopilot's design and decide most of its behavior:

- **A deterministic scheduler.** The model plans the epics once and does the work inside a pipe. It never coordinates pipes. Ordering, worktrees, retries, caps and merges are plain Python (`.specify/extensions/autopilot/scripts/python/autopilot.py`).
- **A janitor gate.** The only exit from a pipe's loop is a concrete check: the project's tests, lint and type commands pass, every task is done, every acceptance scenario is traced to a test. The implementer's own opinion that it is done does not count.
- **The implementer never grades itself.** A separate reviewer agent, in a separate CLI process, optionally on a different model, judges the diff against `spec.md`. It is read-only, and the gate enforces that.
- **Constraints live in the environment.** Gate checks, commit hooks (never bypassed), the tree fingerprint around the reviewer and the stuck detector are code, not prompt instructions.
- **Nobody works blind.** The autopilot runs like a development team, and every developer knows the big picture and can ask before guessing.

## The team

| Role | Who | Does |
| --- | --- | --- |
| Product owner | You | Approve the plan and the team handbook (gate 1) and the final merge (gate 2); answer product questions |
| Team lead | The chat agent (`/speckit.autopilot.run`), plus headless `/speckit.autopilot.lead` while pipes run | Plan epics, write the team handbook, answer developers' questions, keep decisions consistent |
| Developers | One unattended pipe per epic | Specify, plan and build their epic within the handbook and the decisions |
| Code reviewer | `/speckit.autopilot.review`, a separate agent | Judge each epic's diff against its spec, the handbook and the decisions |
| CI | The gate (plain code) | Tests, lint, types, traced acceptance scenarios, completed tasks |
| Scheduler | `drive` (plain code) | Assign epics, isolate them in worktrees, merge one at a time, enforce caps |

**What every developer reads before every step** (`.specify/autopilot/context/` in its worktree):

- `program.md`, the **team handbook** the lead writes at planning time: product, architecture, conventions, the shared contracts between epics, glossary, ground rules. You review it at gate 1.
- `epic-context.md`, an **onboarding brief** the scheduler generates in code at every launch: the epic itself, what its dependencies already built (and what they `provide`), which teammates are working in parallel and on which files, which epics wait on this one and what they need, the files this epic owns, and how to ask the lead.
- `decisions.md`, the team's **decision log**: every answer given so far, binding on all epics.

**Asking before guessing.** Small choices a developer decides and records as assumptions. When a wrong guess would be costly (a contract another epic uses, the data model, public behavior, security, requirements that seem to conflict) it writes a question file and carries on with other work. An unresolved `[NEEDS CLARIFICATION]` marker in a spec becomes a question too.

After specify, after design, and in every build iteration, a `consult → lead → record` trio runs:

1. `consult` (code) files new questions and answers repeats straight from the decision log.
2. The **team lead** agent answers from the handbook, requirements, constitution and earlier decisions, or marks the question `needs_human` when it is a product decision (scope, conflicting requirements, security or legal, cost). It is read-only, enforced by the same tree fingerprint as the reviewer.
3. `record` (code) publishes each answer to the program-wide decision log and hands it back: as an edit replacing the spec marker, or as a `Team Decisions` task for the next `implement`.

A question for you pauses **only that developer** (`awaiting-human`). Its slot frees and the rest of the team keeps working. `/speckit.autopilot.run` presents the question with options and the lead's recommendation; your answer becomes a decision, and the drive resumes that epic where it left off. Caps: `pipe.max_questions` per epic (more means the epic is under-specified and is escalated), and a question the lead fails to answer twice goes to you.

## Commands

You drive the whole autopilot from your agent's chat:

| Command | Purpose |
| --- | --- |
| `/speckit.autopilot.setup` | Once per project: install the workflows, fill the gate from `AGENTS.md` / CI, prove it is green, set limits, commit the setup |
| `/speckit.autopilot.run` | The conductor: preflight, plan epics, **gate 1** (approve the plan in chat), start the unattended drive, **gate 2** (approve the final merge), land. Run it again at any time to continue an interrupted run. `stop` halts new pipes |
| `/speckit.autopilot.status` | Read-only: stage, epic table, budget, recent events, and the evidence-based cause of any failure |
| `/speckit.autopilot.recover` | Act as the human in the loop: diagnose failed or escalated epics, fix them with your approval, reset them and resume |

Used internally, and also callable on their own:

| Command | Called by | Purpose |
| --- | --- | --- |
| `/speckit.autopilot.epics` | `run` | Plan epics as a dependency DAG and write the team handbook |
| `/speckit.autopilot.lead` | each pipe | Team lead: answer a developer's questions or hand product questions to you |
| `/speckit.autopilot.review` | each pipe | Independent review of one epic's diff; writes a JSON verdict |

Core commands used by each pipe: `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`, `/speckit.converge`.

The commands call a deterministic engine, `.specify/extensions/autopilot/scripts/python/autopilot.py`, which prints one JSON object per call. You never need to run it yourself. It is also what the headless `autopilot` workflow uses (see [Headless and CI](#headless-and-ci)).

## Get started

Bootstrapping takes two terminal commands. They are the only ones, because no skill exists before Spec Kit is installed. You can also ask your agent to run them.

```bash
uv tool install specify-cli --from <spec-kit checkout or git URL with the autopilot>
cd your-project
specify init --here --force --integration claude --extension autopilot
```

`--here --force` initializes an existing, non-empty project without touching its files. Pick your integration key. From here on, work in the agent's chat:

```text
/speckit.autopilot.setup
/speckit.autopilot.run requirements=docs/requirements
```

Requirements: `git`, a `python3` on PATH (the engine is stdlib-only), and an integration with CLI dispatch for the headless pipes (for example Claude Code, Copilot CLI, Codex). On Windows, make sure `python3` resolves (for example through the `py` launcher alias).

## Setup

`/speckit.autopilot.setup` installs the `autopilot-epic` and `autopilot` workflows, then reads `AGENTS.md`, contributor docs, build manifests and CI to fill `gate.checks` in `.specify/extensions/autopilot/autopilot-config.yml`, and runs them. **A working, green test and lint environment is a prerequisite**: if the base is red, no epic can ever pass, and the run refuses to start. It then reviews the limits with you, flags agent instructions that would stop an unattended pipe, and offers to commit the setup (pipes build from commits).

```yaml
gate:
  checks:
    - name: test
      run: "uv run pytest -q"
    - name: lint
      run: "uv run ruff check ."
pipe:
  max_iterations: 5      # implement→gate iterations per epic
  stuck_after: 2         # identical failures in a row before escalating
  timeout_minutes: 120   # per epic
run:
  max_parallel: 2
  timeout_minutes: 480   # no new pipe starts after this
  max_agent_calls: 200   # cost ceiling for the run
  setup: "uv sync"       # run once in each new worktree
```

## A run, in chat

`/speckit.autopilot.run` reads the run's stage first, so the same command starts, continues and finishes a run:

1. **Preflight.** It checks git, a clean tree, the configured gate (running it on `HEAD`), `specify` on PATH and the installed workflow. It fixes what it can with your permission: running setup, committing your requirements, installing the workflow.
2. **Plan.** The chat agent is the conductor. It plans the epics itself (`/speckit.autopilot.epics`) and validates them into `.specify/autopilot/dag.md`.
3. **Gate 1.** It shows the epic table, dependencies (including any the scheduler added), requirement coverage, assumptions and the worst-case agent-call cost. You approve, ask for changes (it edits and re-validates), or cancel. Only your explicit approval in the conversation counts.
4. **Drive.** It starts the scheduler detached from the chat (`drive --detach`), so the run survives the session. One drive per checkout, guarded by a lock. If the agent can wait it reports changes as they happen; otherwise run `/speckit.autopilot.status` whenever you like.
5. **Gate 2.** When the drive finishes it writes `.specify/autopilot/report.md` and shows it with the integration branch's log and diffstat, plus any epic that needs you (offering `/speckit.autopilot.recover`). You approve the merge or hold.
6. **Land.** It merges `autopilot/integration` into your base branch with a merge commit, then offers to clean up epic branches and worktrees.

To halt new work: `/speckit.autopilot.run stop` (running pipes finish). To check in: `/speckit.autopilot.status`.

## Headless and CI

The same run without a chat is the `autopilot` workflow. Its gates pause until a verdict input is supplied:

```bash
specify workflow run autopilot --input requirements=docs/requirements
specify workflow resume <run_id> --input autopilot_review_epics_verdict=approve
specify workflow resume <run_id> --input autopilot_review_land_verdict=approve
```

Its steps are the engine calls the chat commands make: `preflight --baseline`, the `speckit.autopilot.epics` command, `plan-check`, gate, `drive`, `report`, gate, `land`.

## The epic plan

Each epic in `epics.json` has an `id`, a kebab-case `slug`, a `title`, `goal`, `scope`, `out_of_scope`, the `requirements` it covers, `acceptance` criteria, `depends_on` and `touches` (paths or globs it will change). `plan-check`:

- rejects unknown or self dependencies, duplicates, missing acceptance criteria and cycles;
- **serializes overlapping epics**: when two independent epics' `touches` may overlap (or one declares none), the later epic gets a dependency on the earlier one, and `dag.md` marks it `(added)`;
- assigns `specs/NNN-<slug>` directories and `autopilot/NNN-<slug>` branches up front, in dependency order, so parallel pipes never race for the next feature number.

## One pipe

The scheduler runs `autopilot-epic` headlessly inside the epic's worktree with `SPECIFY_FEATURE_DIRECTORY` pre-set. For a single feature from chat, give `/speckit.autopilot.run` a one-feature requirement. It plans one epic and keeps both gates and the isolated worktree. Headless, the pipe also runs alone on the current checkout:

```bash
specify workflow run autopilot-epic --input brief="Add CSV export to reports"
```

Every agent step first reads the team context (handbook, brief, decisions).

| Step | Kind | What happens |
| --- | --- | --- |
| `specify` | agent | Writes `spec.md` from the brief, fitting the handbook; leaves a `[NEEDS CLARIFICATION]` marker only for a costly question |
| `consult → lead → record` | code, agent, code | Spec questions answered by the team lead and written into the spec (or sent to you) |
| `check-spec` | code | Stops the pipe on a spec still waiting for you, or without acceptance scenarios; derives scenario IDs |
| `plan`, `tasks` | agent | Plan within the handbook's architecture and contracts; tasks are told the scenario IDs and that tests are required |
| `consult → lead → record` | code, agent, code | Design questions answered before any code is written |
| `implement` | agent | Completes every open task, including converge, team-decision and remediation tasks; asks instead of guessing |
| `converge` | agent | Appends any unbuilt work to `tasks.md` |
| `consult → lead → record` | code, agent, code | Questions raised while building |
| `gate` | code | Runs the checks; on failure appends remediation tasks; on success prepares the review |
| `review` | agent | Independent review against the spec, handbook and decisions (only when the checks pass) |
| `decide` | code | Reads the verdict, appends blocking findings as tasks, ends or continues the loop |
| `result` | code | Exits non-zero unless the pipe passed |

### The gate

All must pass for the pipe to reach review:

| Check | Passes when |
| --- | --- |
| `spec-clarity` | `spec.md` has no `[NEEDS CLARIFICATION` marker |
| `tasks-complete` | `tasks.md` has no unchecked task, so the last converge pass appended nothing |
| each `gate.checks` entry | the command exits 0 |
| `acceptance-coverage` | every acceptance scenario ID appears in a test file (and `scenario_command`, when set, passes per scenario) |

**Scenario IDs** are derived from `spec.md` structure: scenario *y* of `### User Story x` in feature `NNN` is `NNN-USx-ASy`. A test covers it when a test file (`gate.acceptance.test_globs`) contains the ID with `-` or `_` separators in any case, so `test_003_us1_as2_empty_report` and `// 003-US1-AS2` both count. Set `scenario_command` (for example `uv run pytest -q -k {tag_underscore}`) to also require each scenario's own tests to pass. Without it, a traced test passes when the whole test command passes; the reviewer is asked to reject tests that only mention an ID.

Failures are appended to `tasks.md` as a new `## Phase N: Autopilot Remediation (iteration k, gate)` section, append-only like converge, so the next `implement` picks them up. Each iteration writes a report to `.specify/autopilot/pipes/<feature>/gate-<k>.md`.

### The reviewer

When the checks pass, the gate stages the epic's work, writes its full diff against the base commit, fingerprints the working tree, and passes `feature_dir`, `diff_file`, `review_file` and `base` to `/speckit.autopilot.review`. The reviewer writes:

```json
{ "verdict": "fail", "summary": "…", "findings": [
  { "id": "R1", "severity": "major", "requirement": "FR-004", "file": "src/x.py",
    "summary": "Empty report crashes", "fix": "Emit the header row" } ] }
```

`decide` then applies these rules:

- `blocker` or `major` findings fail the iteration **whatever verdict the reviewer declared**, and become remediation tasks.
- A missing, malformed or invalid review never passes.
- If the working tree changed during the review, the epic is escalated: a reviewer must not edit code.

Use `run.reviewer_model` (or the workflow's `reviewer_model` input) to review with a different model from the implementer.

### Ending the loop

| Outcome | Cause |
| --- | --- |
| `passed` | gate checks and review passed |
| `failed` | `pipe.max_iterations` reached, or the pipe timed out |
| `awaiting-human` | a question only you can answer; resumes by itself once you answer |
| `escalated` | the same gate failure (normalized) `stuck_after` times in a row, the same blocking review findings repeated, too many questions, a reviewer or lead that edited files, a merge conflict, or checks failing after merge |

## Scheduling and merging

`drive` is event-driven, not wave-based: a pipe starts as soon as its dependencies are **merged** and a slot is free, so a slow epic only delays its own dependents.

- Each epic gets branch `autopilot/NNN-slug` and a worktree under `<repo-parent>/<repo>.worktrees/autopilot/`, branched from the integration branch's current head. Untracked Spec Kit and agent files (`run.sync_paths`) are copied in; `run.setup` runs once.
- When a pipe passes, its work is committed (commit hooks run; autopilot state, synced files and workflow run state are never committed) and merged into `autopilot/integration` with `--no-ff`, **one at a time**.
- On a merge conflict the epic branch is rebased onto the integration branch, re-verified, and merged again; if the rebase conflicts the epic is escalated. Nothing is force-resolved.
- After every merge the gate checks run again on the integration branch. If they fail, the merge is reverted and the epic is escalated.
- Epics depending on an epic that did not merge become `blocked`.
- Your base branch and working tree are not touched until `land`.

## Controls

| Control | Setting | Effect |
| --- | --- | --- |
| Iterations per epic | `pipe.max_iterations` | Pipe fails when reached |
| Repeated identical failure | `pipe.stuck_after` | Pipe escalates |
| Wall time per epic | `pipe.timeout_minutes` | Pipe process is killed and the epic fails |
| Wall time per run | `run.timeout_minutes` | No new pipe starts; running pipes finish |
| Cost ceiling | `run.max_agent_calls` | A pipe reserves its worst case (`5 + 4 × max_iterations` agent calls, including the lead's consults) before starting; no pipe starts that would exceed the budget |
| Parallelism | `run.max_parallel` | Concurrent pipes |
| Infrastructure retries | `pipe.max_attempts` | Re-launch after an agent CLI crash (not after a gate failure) |
| Emergency stop | `/speckit.autopilot.run stop` | No new pipe starts; running pipes finish |

The agent-call budget is a proxy for cost: integration CLIs do not report spend uniformly. Set it from the price of a typical agent call on your integration.

## State and recovery

| Path | Contents |
| --- | --- |
| `.specify/autopilot/epics.json`, `epics.md` | The conductor's plan |
| `.specify/autopilot/dag.md` | Validated DAG shown at the plan gate |
| `.specify/autopilot/state.json` | Scheduler state (owned by plain code) |
| `.specify/autopilot/log.jsonl`, `logs/` | Events and each pipe's CLI output |
| `.specify/autopilot/report.md` | Run report shown at the final gate |
| `<worktree>/.specify/autopilot/pipes/<feature>/` | `pipe.json`, `gate-N.md`, `review-N.diff`, `review-N.json` |

- **Interrupted run** (machine slept, terminal closed): `/speckit.autopilot.run` sees the `interrupted` stage and resumes. Running pipes resume their workflow run; finished pipes are not repeated.
- **Escalated or failed epic**: `/speckit.autopilot.recover <EPIC>` diagnoses the cause from the gate reports, reviews and logs. It agrees a fix with you (answer a spec question, fix the gate config, a targeted code fix, or resolve a merge conflict) and applies it in the epic's worktree. Then it resets the epic and the epics it blocked, which grants a fresh iteration allowance and restarts the pipe at its build loop without re-running `specify` over the spec, and resumes the drive.
- **Start over**: after a landed run, `/speckit.autopilot.run` asks before discarding the scheduler state for a new run. Branches and worktrees are left in place until you agree to remove them.

## Limitations

- Merges are local. The integration branch is the review surface; open a pull request from it yourself if you want CI and review on GitHub.
- A traced acceptance test passes when the whole test command passes unless `scenario_command` is set, so skipped tests are caught only by the reviewer.
- `touches` overlap is computed from glob prefixes and is conservative: it may serialize epics that could have run in parallel, never the reverse. Epics that change files they did not declare can still conflict at merge time, and the scheduler escalates them rather than resolving the conflict.
- Agent-facing instructions ("do not ask questions") are still prompts. The gate decides whether the result is acceptable; it cannot make an agent productive.
