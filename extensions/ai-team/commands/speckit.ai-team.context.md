---
description: "Open, update, or reconstruct the durable Task Context Package so interrupted AI Team SDD work can resume."
---

# AI Team Context

Create, load, update, or reconstruct the durable Task Context Package for an
AI Team SDD task.

## User Input

```text
$ARGUMENTS
```

## Goal

Make the current requirement, bug fix, phase, evidence, and next command
recoverable from repository files instead of hidden chat context. Use this
command at task start, before resuming interrupted work, and after each major
SDD phase changes state.

## Durable Location

Store task context under the coding repository:

```text
.specify/ai-team/tasks/<task-id>/
|-- context-pack.md
|-- state.yml
`-- artifacts/
```

Use a stable `task-id`:

- published requirement ID or URL slug for feature work;
- coding issue number, bug slug, or bug report slug for bug fixes;
- explicit `task_id=<value>` when the work item has no stable ID yet.

Do not store private requirements repository paths or raw customer demand in
the coding repository context pack.

## Resume Modes

| Situation | Action |
|---|---|
| Same workflow run paused at a gate | run `specify workflow resume <run_id>` |
| Different terminal/session/tool, same task | run `speckit.ai-team.context task_id=<task-id> resume=true` |
| Only published requirement URL is known | reconstruct from the URL, feature artifacts, and state files |
| Only bug issue or bug slug is known | reconstruct from `.specify/bugs/<slug>/` and linked issue evidence |
| Context pack conflicts with current source or requirement | stop and ask for human reconciliation |

Spec Kit workflow run state remains authoritative for the mechanics of a paused
workflow run. The Task Context Package is the AI Team bridge across chat loss,
tool switching, manual command execution, and issue-driven re-entry.

## Required Fields

`context-pack.md` must include:

```text
Task Context Package:
- task id:
- work type: bug fix / feature / template change / unclear
- work item:
- coding issue URL or bug slug:
- published requirement URL:
- coding repository:
- requirements published repository:
- requirements submodule path:
- active AI integration:
- workflow run id:
- current phase: intake / specified / planned / tasks-ready / implementing / evidence / pr / review / done / blocked
- last completed command:
- next command:
- source snapshot:
- code graph artifact:
- likely modules:
- public contracts at risk:
- reusable components:
- required commands:
- expected evidence:
- stop conditions:
- resume command:
```

`state.yml` must mirror the fields needed by tools:

```yaml
task_id:
work_type:
work_item:
  published_requirement_url:
  coding_issue_url:
  bug_slug:
repository_role:
active_integration:
workflow_run_id:
phase:
last_completed_command:
next_command:
artifacts:
  spec:
  plan:
  tasks:
  code_graph:
  impact:
  evidence:
updated_at:
```

## Workflow

1. Locate `.specify/extensions/ai-team/ai-team-config.yml` and integration
   state when present.
2. Resolve `task_id`, `work_type`, `published_requirement_url`,
   `coding_issue_url`, `bug_slug`, and `workflow_run_id` from arguments and
   existing state.
3. If `resume=true`, load `state.yml` and `context-pack.md`; otherwise create
   them if missing.
4. Reconcile the context pack with current source, current published
   requirement, bug report, and active feature files.
5. Update `phase`, `last_completed_command`, `next_command`, and artifact
   locations when arguments include newer phase evidence.
6. Return the resume summary and next command.

## Output Shape

```text
AI Team Context:
- task id:
- work type:
- work item:
- context path:
- workflow run id:
- current phase:
- last completed command:
- next command:
- source snapshot:
- code graph artifact:
- missing evidence:
- stop conditions:
- resume command:
```

## Stop Conditions

Stop and ask when:

- the task cannot be mapped to a bug issue/slug, published requirement URL, or
  explicit task ID;
- a feature tries to resume without a published requirement URL;
- the context pack contains private requirement content in a coding repository;
- `state.yml` and `context-pack.md` disagree about work type, work item, or
  phase;
- current source or published requirement has changed since the recorded source
  snapshot and the impact radius is unknown.
