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

Make the current work item, phase, evidence, and next command recoverable from
repository files instead of hidden chat context. Use this command at task start,
before resuming interrupted work, and after each major SDD phase changes state.

This is not the Spec Kit workflow engine state and it is not long-term AI
memory. Workflow execution state stays under
`.specify/workflows/runs/<run-id>/state.json`. AI Team context stays under
`.specify/ai-team/tasks/<task-id>/` and exists only to reconstruct the task
context that an AI coding tool should load.

## Durable Location

Store task context under the coding repository:

```text
.specify/ai-team/tasks/<task-id>/
|-- context-pack.md
|-- task-context.yml
`-- artifacts/
```

Use a stable `task-id`:

- coding issue number or URL slug for public feature work;
- handoff requirement ID or URL slug for confidential enterprise feature work;
- public project issue/charter or handoff requirement ID for new-project work;
- coding issue number, bug slug, or bug report slug for bug fixes;
- explicit `task_id=<value>` when the work item has no stable ID yet.

Use `extensions/ai-team/docs/task-field-spec.md` or the installed equivalent as
the field naming contract.

Do not store raw customer demand or private enhancement draft paths in public
coding repository context packs.

## Resume Modes

| Situation | Action |
|---|---|
| Same workflow run paused at a gate | run `specify workflow resume <run_id>` |
| Different terminal/session/tool, same task | run `speckit.ai-team.context task_id=<task-id> resume=true` |
| Only coding issue URL is known | reconstruct from the URL, feature artifacts, and context files |
| Only handoff requirement URL is known | reconstruct from the URL, allowed handoff content, feature artifacts, and context files |
| Only bug issue or bug slug is known | reconstruct from `.specify/bugs/<slug>/` and linked issue evidence |
| Context pack conflicts with current source or work item | stop and ask for human reconciliation |

Spec Kit workflow run state remains authoritative for the mechanics of a paused
workflow run. The Task Context Package is the AI Team bridge across chat loss,
tool switching, manual command execution, issue-driven re-entry, and context
insertion for chat-first tools.

## Required Fields

`context-pack.md` must include:

```text
Task Context Package:
- task id:
- work type: bug fix / feature / new project / template change / unclear
- work item:
- work item type:
- coding issue URL:
- bug slug:
- handoff requirement URL:
- published requirement URL, deprecated alias:
- coding repository:
- internal enhancement repository:
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

`task-context.yml` must mirror the fields needed by tools:

```yaml
task_id:
work_type:
work_item:
  coding_issue_url:
  handoff_requirement_url:
  published_requirement_url:
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
   metadata when present.
2. Resolve `task_id`, `work_type`, `coding_issue_url`,
   `handoff_requirement_url`, deprecated `published_requirement_url`,
   `bug_slug`, and `workflow_run_id` from arguments and existing task context.
3. If `resume=true`, load `task-context.yml` and `context-pack.md`; otherwise create
   them if missing.
4. Reconcile the context pack with current source, current work item, bug
   report, and active feature files.
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

- the task cannot be mapped to a bug issue/slug, coding issue URL, handoff
  requirement URL, or explicit task ID;
- a feature tries to resume without a coding issue, handoff requirement, or
  approved task ID;
- the context pack contains private enhancement content in a public coding
  repository;
- `task-context.yml` and `context-pack.md` disagree about work type, work item, or
  phase;
- current source or work item changed since the recorded source snapshot and
  the impact radius is unknown.
