# Work Context Package

The Work Context Package is the durable handoff unit for AI Team SDD work. It
ties one bug fix, feature, or template change to the current phase, source
snapshot, graph evidence, required human decisions, and next command.

Create it only after a stable Issue, charter, or handoff exists. Pre-work-item
Intake remains under `.specify/ai-team/intake/<intake_slug>/` and must not create
a formal Work Context Package.

It exists because AI agents may stop, switch tools, lose chat context, or enter
the work after a human approval step. Recovery must come from repository facts,
not from hidden conversation memory.

## Storage

Store work context in the coding repository:

```text
.specify/ai-team/work/<work_slug>/
|-- work-context.yml
|-- context-pack.md
|-- permission-envelope.yml
|-- handoffs/
|-- codegraph/
|-- evidence/
```

Spec Kit SDD artifacts remain under `specs/<work_slug>/`. Bug extension artifacts
remain under `.specify/bugs/<bug_slug>/` when `work_type=bug`.

Use `.specify/workflows/runs/<run-id>/state.json` for Spec Kit's workflow
engine state. Use `.specify/ai-team/work/<work_slug>/` for AI Team work identity
and cross-session recovery.

The files have separate responsibilities:

- `work-context.yml` is the compact cross-session index: work item, native
  artifact locations, phase, last command, and next command;
- `context-pack.md` is the human-readable resume summary;
- `permission-envelope.yml` records task-scoped access and its real enforcement
  mode.

See [permission-envelope.md](permission-envelope.md) for the access contract.
Do not create a second artifact ledger: `spec.md`, `plan.md`, `tasks.md`, bug
reports, workflow state, and the Evidence Board remain authoritative.

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

One work unit may resolve several coding issues when they describe different
symptoms of the same root cause. Record one primary issue and an
`also_resolves_issue_urls` list. Use separate work units when root cause,
change boundary, rollback, or release risk differs, and map every linked issue
to its own reproduction and verification evidence.

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
| `archived` | memory consolidation or release archive has summarized this work and marked remaining raw traces by retention policy | none |
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
implementation; there is no `plan-check.md`, `plan-gate.md`, or preset task-gate overlay.

## Resume Protocol

1. Run `speckit.ai-team.context work_slug=<work_slug> resume=true`.
2. If a paused workflow run is recorded, inspect it with
   `specify workflow status <run-id>` and resume it with
   `specify workflow resume <run-id>` when appropriate.
3. If there is no usable workflow run, load `work-context.yml`,
   `context-pack.md`, the permission envelope, and only the native artifacts
   required by the current phase.
4. Compare the recorded source snapshot and work item or bug state to current
   repository state.
5. Run the `next_command` from `work-context.yml` only when the stop conditions
   are clear and the Permission Envelope allows the required operation.

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

## Memory And Release Archive Status

When a feature, bugfix, review cycle, or incident produces a reusable lesson,
contributors or maintainers may run `speckit.ai-team.memory-consolidate` and
choose local, department, or enterprise memory. After a release candidate,
final release, milestone, or maintainer-chosen checkpoint, maintainers may run
`speckit.ai-team.release-archive` to summarize many completed work items into
`.specify/ai-team/releases/private/<release_id>/`; only reviewed, sanitized
enterprise summaries are promoted to `docs/ai-team/memory/releases/<release_id>/`.

The memory or release archive record should mark each `work_slug` or `bug_slug`
as one of:

- `archived`: summarized in the release package and no longer active;
- `kept-active`: still relevant to an unfinished follow-up;
- `private-only`: raw material stays outside the public coding repository;
- `superseded`: detailed process artifact is replaced by release-level
  summary;
- `blocked`: cannot archive until a missing owner, evidence, or privacy
  decision is resolved.

Archiving does not mean deleting evidence. Default behavior is to keep raw
evidence available under the repository's retention policy while future AI
tasks load the smaller memory card, release summary, bugfix lessons, and
migration playbook.

## Change And Permission Control

Work context points to the standard SDD and bug artifacts instead of copying
their content or status into a parallel manifest. It does not automatically
change team governance, architecture rules, or enterprise guidance.

Before code graph or source analysis, create an analysis Permission Envelope.
Before implementation, revise it to the smallest approved write paths and
commands. Record `policy-only` unless native or wrapper enforcement is actually
configured and verified. If hard confinement is required and only policy
controls exist, stop rather than claiming the task is sandboxed.
