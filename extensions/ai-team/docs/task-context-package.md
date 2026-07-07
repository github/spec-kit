# Task Context Package

The Task Context Package is the durable handoff unit for AI Team SDD work. It
ties one bug fix, feature, or template change to the current phase, source
snapshot, graph evidence, required human decisions, and next command.

It exists because AI agents may stop, switch tools, lose chat context, or enter
the task after a human approval step. Recovery must come from repository facts,
not from hidden conversation memory.

## Storage

Store task context in the coding repository:

```text
.specify/ai-team/tasks/<task-id>/
|-- context-pack.md
|-- state.yml
`-- artifacts/
```

Use `.specify/workflows/runs/<run-id>/` for Spec Kit's workflow engine state.
Use `.specify/ai-team/tasks/<task-id>/` for AI Team task identity and
cross-session recovery.

## Task Identity

| Work type | Stable identity |
|---|---|
| bug fix | coding issue URL, issue number, or `.specify/bugs/<slug>/` |
| feature | published requirement URL or requirement ID |
| template change | distribution repository issue or PR |
| unclear intake | explicit temporary `task_id=<value>` until clarified |

Feature work must use a published requirement URL. A local `requirements/`
submodule path may be used for reading, but it is not the authoritative work
item.

## Phase Model

| Phase | Meaning | Typical next command |
|---|---|---|
| `intake` | request received and task identity is being resolved | `speckit.ai-team.start` |
| `specified` | requirement or bug intent is clear enough for planning | `speckit.ai-team.handoff` or `speckit.plan` |
| `planned` | architecture plan exists and awaits task generation | `speckit.ai-team.plan-gate` |
| `tasks-ready` | developer tasks are generated and gated | `speckit.implement` |
| `implementing` | code is being changed | `speckit.ai-team.checks` |
| `evidence` | implementation exists and evidence is being assembled | `speckit.ai-team.evidence` |
| `pr` | PR is prepared or open | `speckit.ai-team.review` |
| `review` | human review is active | `speckit.ai-team.retrospect` if failure repeats |
| `done` | merged or intentionally closed with evidence | none |
| `blocked` | missing work item, owner decision, or evidence blocks progress | ask human |

## Resume Protocol

1. Run `speckit.ai-team.context task_id=<task-id> resume=true`.
2. If a paused workflow run is recorded, inspect it with
   `specify workflow status <run-id>` and resume it with
   `specify workflow resume <run-id>` when appropriate.
3. If there is no usable workflow run, load `state.yml`, `context-pack.md`,
   current feature artifacts, bug artifacts, and code graph artifacts.
4. Compare the recorded source snapshot and requirement or bug state to current
   repository state.
5. Run the `next_command` from `state.yml` only when the stop conditions are
   clear.

If the source, requirement, or context pack changed while the work was paused,
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
