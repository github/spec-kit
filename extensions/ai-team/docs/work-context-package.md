# Work Context Package

The Work Context Package is the durable handoff unit for AI Team SDD work. It
ties one bug fix, feature, or template change to the current phase, source
snapshot, graph evidence, required human decisions, and next command.

It exists because AI agents may stop, switch tools, lose chat context, or enter
the work after a human approval step. Recovery must come from repository facts,
not from hidden conversation memory.

## Storage

Store work context in the coding repository:

```text
.specify/ai-team/work/<work_slug>/
|-- work-context.yml
|-- context-pack.md
|-- handoffs/
|-- codegraph/
|-- evidence/
```

Spec Kit SDD artifacts remain under `specs/<work_slug>/`. Bug extension artifacts
remain under `.specify/bugs/<bug_slug>/` when `work_type=bug`.

Use `.specify/workflows/runs/<run-id>/state.json` for Spec Kit's workflow
engine state. Use `.specify/ai-team/work/<work_slug>/` for AI Team work identity
and cross-session recovery.

## Work Identity

Use [work-field-spec.md](work-field-spec.md) for canonical field names,
`work_slug` rules, and bug `bug_slug` rules.

| Work type | Stable identity |
|---|---|
| bug fix | coding issue URL, issue number, or `.specify/bugs/<slug>/` |
| public feature | coding issue URL, issue number, or SDD feature directory basename |
| confidential enterprise feature | handoff requirement URL or requirement ID |
| new project | public project issue/charter, handoff requirement URL, or explicit work slug |
| template change | distribution repository issue or PR |
| unclear intake | explicit temporary `work_slug=<value>` until clarified |

Feature work must use a stable work item. Public feature work can use a coding
repository issue. Confidential enterprise work can use a sanitized handoff
requirement URL where visibility allows it, or a public-safe summary plus
private trace in approved channels.

## Phase Model

| Phase | Meaning | Typical next command |
|---|---|---|
| `intake` | request received and work identity is being resolved | `speckit.ai-team.context` (workflow) or `speckit.ai-team.start` (chat-first routing) |
| `specified` | requirement or bug intent is clear enough for planning | `speckit.ai-team.handoff` or `speckit.plan` |
| `planned` | architecture plan exists; plan check may be complete; awaits `review-plan` gate | `speckit.tasks` after approve, or `speckit.plan` on revise |
| `tasks-ready` | developer tasks are generated and await native analyze | `speckit.analyze` |
| `implementing` | code is being changed | `speckit.implement` or `speckit.converge` |
| `evidence` | implementation exists and evidence is being assembled | `speckit.converge` (composite checks + evidence via preset) or `speckit.ai-team.pr` |
| `pr` | PR is prepared or open | `speckit.ai-team.review` |
| `review` | human review is active | `speckit.ai-team.retrospect` if failure repeats |
| `done` | merged or intentionally closed with evidence | none |
| `blocked` | missing work item, owner decision, or evidence blocks progress | ask human |

## Plan check summary (`plan_check`)

After `speckit.ai-team.plan-check`, the command updates `work-context.yml`:

```yaml
plan_check:
  status: pass | revise | blocked
  change_radius: local | module | cross-module | architecture | not-applicable
  work_type: new-project | existing-project-feature | bug-driven | refactor | migration
  summary: "<one-line conclusion>"
```

The full Plan Check Report stays in **chat**. A short summary also goes to
`context-pack.md`. Native `speckit.analyze` covers cross-artifact consistency before
implementation — there is no `plan-check.md`, `plan-gate.md`, or preset task-gate overlay.

## Resume Protocol

1. Run `speckit.ai-team.context work_slug=<work_slug> resume=true`.
2. If a paused workflow run is recorded, inspect it with
   `specify workflow status <run-id>` and resume it with
   `specify workflow resume <run-id>` when appropriate.
3. If there is no usable workflow run, load `work-context.yml`, `context-pack.md`,
   current feature artifacts, bug artifacts, and code graph artifacts.
4. Compare the recorded source snapshot and work item or bug state to current
   repository state.
5. Run the `next_command` from `work-context.yml` only when the stop conditions are
   clear.

If the source, work item, or context pack changed while the work was paused,
run `speckit.ai-team.codegraph` and `speckit.ai-team.impact` again before
continuing implementation.

## Human Decisions

The context pack records decisions but does not replace decision owners.

- product or customer owner controls raw requirement intent;
- technical committee accepts or rejects feature readiness;
- architect owns plan-level architecture safety;
- maintainer or module owner owns code-level compatibility and quality;
- reviewer owns merge readiness.

AI-generated output is evidence for those roles, not a transfer of
accountability.
