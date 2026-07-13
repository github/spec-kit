---
description: "Open, update, or reconstruct the durable Work Context Package so interrupted AI Team SDD work can resume."
---

# AI Team Context

Create, load, update, or reconstruct the durable Work Context Package for an
AI Team SDD work unit after a stable Issue, charter, or handoff exists. Intake
uses its own provisional directory and never creates a formal Work Context.

## User Input

```text
$ARGUMENTS
```

## Goal

Make the current work item, phase, evidence, and next command recoverable from
repository files instead of hidden chat context. Use this command at work start,
before resuming interrupted work, and after each major SDD phase changes state.

This is not the Spec Kit workflow engine state and it is not long-term AI
memory. Workflow execution state stays under
`.specify/workflows/runs/<run-id>/state.json`. AI Team context stays under
`.specify/ai-team/work/<work_slug>/` and exists only to reconstruct the work
context that an AI coding tool should load.

## Durable Location

Store work context under the coding repository:

```text
.specify/ai-team/work/<work_slug>/
|-- work-context.yml
|-- context-pack.md
|-- permission-envelope.yml
|-- handoffs/
|-- codegraph/
|-- evidence/
```

Use a stable `work_slug`:

- for feature work: basename of the Spec Kit feature directory (`FEATURE_DIR`);
- for bug work: same as `bug_slug`;
- for new-project or template work: explicit slug at intake;
- explicit `work_slug=<value>` when the work item has no stable ID yet.

Use `extensions/ai-team/docs/work-field-spec.md` or the installed equivalent as
the field naming contract.

Do not store raw customer demand or private enhancement draft paths in public
coding repository context packs.

## Resume Modes

| Situation | Action |
|---|---|
| Same workflow run paused at a gate | run `specify workflow resume <run_id>` |
| Different terminal/session/tool, same work | run `speckit.ai-team.context work_slug=<work_slug> resume=true` |
| Only coding issue URL is known | reconstruct from the URL, feature artifacts, and context files |
| Only handoff requirement URL is known | reconstruct from the URL, allowed handoff content, feature artifacts, and context files |
| Only bug issue or bug slug is known | reconstruct from `.specify/bugs/<slug>/` and linked issue evidence |
| Context pack conflicts with current source or work item | stop and ask for human reconciliation |

Spec Kit workflow run state remains authoritative for the mechanics of a paused
workflow run. The Work Context Package is the AI Team bridge across chat loss,
tool switching, manual command execution, issue-driven re-entry, and context
insertion for chat-first tools.

## Required Fields

`context-pack.md` must include:

```text
Work Context Package:
- work slug:
- permission envelope path:
- permission enforcement mode:
- work type: bug fix / feature / new project / template change / unclear
- planning mode: standard / compact
- work item:
- work item type:
- coding issue URL:
- also resolves coding issue URLs:
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

`work-context.yml` must mirror the fields needed by tools:

```yaml
work_slug:
work_type:
planning_mode: standard
permission_envelope: .specify/ai-team/work/<work_slug>/permission-envelope.yml
work_item:
  coding_issue_url:
  also_resolves_issue_urls: []
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
plan_check:
  status:
  change_radius:
  work_type:
  summary:
updated_at:
```

## Workflow

1. Locate `.specify/extensions/ai-team/ai-team-config.yml` and integration
   metadata when present.
2. Resolve `work_slug`, `work_type`, `planning_mode`, `coding_issue_url`,
   `also_resolves_issue_urls`,
   `handoff_requirement_url`, deprecated `published_requirement_url`,
   `bug_slug`, and `workflow_run_id` from arguments and existing work context.
3. If `resume=true`, load `work-context.yml`, `context-pack.md`, and
   `permission-envelope.yml`; otherwise create the first two and leave
   permissions blocked until explicitly assessed.
4. Resolve native artifacts from the active feature directory or bug slug.
   Record missing artifacts as missing; do not invent paths.
5. Treat `coding_issue_url` as the primary coding issue. Accept
   `also_resolves_issue_urls` only when the linked issues describe different
   symptoms of the same root-cause change. Keep all linked issues the same work
   type and require separate evidence mapping for each one.
6. Update `phase`, `last_completed_command`, `next_command`, and artifact
   locations when arguments include newer phase evidence.
7. Return the resume summary, permission status, and next command.

## Output Shape

```text
AI Team Context:
- work slug:
- work type:
- planning mode:
- work item:
- context path:
- permission envelope:
- permission enforcement mode:
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

- the work cannot be mapped to a bug issue/slug, coding issue URL, handoff
  requirement URL, or explicit work slug;
- a feature or new project tries to enter formal SDD without a coding issue,
  charter, or handoff requirement;
- additional issue URLs are present without a primary coding issue, use another
  work type, or do not share one root-cause change;
- the context pack contains private enhancement content in a public coding
  repository;
- `work-context.yml` and `context-pack.md` disagree about work type, work item, or
  phase;
- the work context points at another work unit;
- the next command requires access outside the current Permission Envelope;
- current source or work item changed since the recorded source snapshot and
  the impact radius is unknown.
