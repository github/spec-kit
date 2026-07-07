# AI Team SDD Collaboration Extension

This extension adapts Spec Kit's Spec-Driven Development workflow for
enterprise AI Team Coding.

It keeps the core SDD phases:

```text
specify -> plan -> tasks -> implement
```

and adds enterprise collaboration constraints:

- role isolation across SDD phases;
- document handoffs between roles;
- public coding-repository issues, internal enhancement records, and coding
  repository separation;
- URL-oriented work-item references, with public features starting from coding
  issues and confidential enterprise features using sanitized handoff URLs only
  where visibility allows;
- code graph and scope control for existing projects;
- strict build planning for new projects;
- self-test and Evidence Board output;
- failure evolution after review, test, incident, or repeated AI mistakes.
- external Skill, Knowledge, and Memory support layers around the project.
- durable Task Context Packages so interrupted work can resume from a work item
  instead of hidden chat context.
- replaceable code graph adapters for source-grounded impact analysis.

## Role Model

| SDD phase | AI role | Responsibility | Context rule |
|---|---|---|---|
| specify | product manager / customer manager | problem, user scenario, acceptance intent | does not share raw chat context with architect |
| plan | architect | technical plan, public/private boundary, code graph impact, build strategy | reads only spec and handoff documents |
| tasks + implement | developer | task breakdown, implementation, self-test, PR evidence | reads only approved spec, plan, tasks, and gate notes |

Roles communicate through documents, not hidden conversation state.

## Repository Boundary

Enterprise customers often do not want raw demand publicly visible. This
extension assumes two primary repository roles:

| Repository | Purpose |
|---|---|
| enhancement-internal | internal-only traceability for confidential enterprise feature demand, approval discussion, wave plan, commercial context, sanitized handoff URLs |
| coding repository | source code, public issues, public-safe plan, tasks, implementation PR, Evidence Board |

Public feature requests can start directly as coding repository issues.
Enhancement-internal issues are internal-only and must be `type/feature`; bug
fixes are filed in the coding repository. Coding repository PRs should link
internal handoff URLs only where repository visibility allows it; public
repositories should carry public-safe summaries.

Use [docs/repository-boundary.md](docs/repository-boundary.md) for the full
repository model and [docs/issue-workflow.md](docs/issue-workflow.md) for issue
type/state labels.

## Task Context and Resume

Every AI Team task should have a durable Task Context Package:

```text
.specify/ai-team/tasks/<task-id>/context-pack.md
.specify/ai-team/tasks/<task-id>/task-context.yml
```

For feature work, `<task-id>` comes from the coding issue, handoff requirement
URL, or requirement ID. For bug fixes, it comes from the coding issue or bug
slug.

If the workflow pauses at a gate, resume the same run with
`specify workflow resume <run-id>`. If the terminal, AI tool, or chat context is
lost, reload the task with:

```bash
speckit.ai-team.context task_id=<task-id> resume=true
```

Use [docs/task-context-package.md](docs/task-context-package.md) for the
storage format, phase model, and resume protocol. Use
[docs/task-field-spec.md](docs/task-field-spec.md) for canonical `task_id`,
`bug_slug`, `coding_issue_url`, and `handoff_requirement_url` rules.

## User Journeys

Use [docs/user-journeys.md](docs/user-journeys.md) for the complete
step-by-step journeys. The short version:

| Journey | Work item | Main path |
|---|---|---|
| existing project bug fix | coding issue or bug slug | `ai-team-bugfix`: context -> route gate -> code graph -> impact gate -> bug assess -> assessment gate -> bug fix -> fix gate -> bug test -> checks/evidence -> PR |
| existing project new feature | coding issue URL or handoff requirement URL | optional requirement review -> context -> code graph -> native SDD -> AI Team gates -> checks/evidence -> PR |
| new project from zero | public project issue/charter or handoff requirement URL | bootstrap -> workspace -> context -> native SDD with strict build plan -> thin slice -> checks/evidence |
| resume from middle | workflow run ID or task ID | workflow resume for paused runs, or `speckit.ai-team.context task_id=<task-id> resume=true` for cross-session recovery |
| failed review/check/incident | PR, check, incident, or repeated AI mistake | retrospect -> update command, gate, knowledge, memory, graph, or test evidence |

### Chat Aliases

When users work in a chat-first AI coding tool, use these stable workflow
aliases instead of asking the user to remember command details:

| Chat alias | Maps to |
|---|---|
| `ai-team-sdd feature path` | `work_type=feature` plus a coding issue URL or handoff requirement URL |
| `ai-team-bugfix path` | `task_id=BUG-<repo-slug>-<issue-number>`, `bug_slug=bug-<repo-slug>-<issue-number>`, and an optional coding issue URL |
| `ai-team-sdd new-project path` | `work_type=new-project` plus a public project issue/charter or handoff requirement URL |
| `ai-team-sdd resume path` | `task_id=<task-id>` plus `resume_from=<phase>` or workflow run resume |

Recommended prompts:

```text
Use the ai-team-sdd feature path for this public coding issue:
https://example.com/org/project/issues/456

Use the ai-team-sdd feature path for this internal handoff requirement:
https://example.com/enhancements/rfcs/REQ-2026-015

Use the ai-team-bugfix path with task_id=BUG-project-alpha-123 and bug_slug=bug-project-alpha-123 for this coding issue:
https://example.com/org/project/issues/123
```

### Existing Project Bug Fix

Bug fixes should use the dedicated `ai-team-bugfix` workflow. Bug work should
link a coding repository issue when possible and must provide both a stable
`task_id` and a deterministic `bug_slug`. The reporter may describe only
symptoms; the AI agent uses source evidence and code graph impact to find the
likely module. The actual bug lifecycle uses the bundled bug extension:

```text
speckit.bug.assess -> speckit.bug.fix -> speckit.bug.test
```

AI Team adds task context, route review, code graph impact, architecture impact
review, assessment review, fix-scope review, portable checks, Evidence Board,
PR description, and review support around that bug lifecycle.

### Existing Project New Feature

Feature work must link a work item. Public feature work can use a coding
repository issue. Confidential enterprise feature work should use
`speckit.ai-team.requirement` and `speckit.ai-team.feature-review` to produce a
sanitized handoff requirement before coding.

The coding repository should not record raw customer demand or private
enhancement draft paths.

### New Project From Zero

New projects use `work_type=new-project`. They still follow SDD, but the plan
gate is stricter: it must establish the project skeleton, architecture spine,
dependency strategy, runnable thin slice, self-test strategy, and evidence
strategy before broad feature construction.

### Resume From Middle

Use Spec Kit workflow state for the same paused workflow run:

```bash
specify workflow status <run-id>
specify workflow resume <run-id>
```

Use the AI Team Task Context Package when switching terminal, AI tool, or chat:

```text
speckit.ai-team.context task_id=<task-id> resume=true
```

## Existing Project vs New Project

Existing project work must start from code graph and impact radius:

- owner module;
- public contracts;
- callers/callees;
- reuse candidates;
- changed nodes;
- self-test mapping.

The code graph can come from a local generator, hosted service, MCP tool, or
fallback source-structure scan, but it must normalize to the AI Team artifact
contract. Use [docs/code-graph-adapters.md](docs/code-graph-adapters.md) for the
adapter contract and open source candidates.

New project work needs a stricter build-from-zero plan:

- project skeleton;
- architecture spine;
- module ownership;
- runnable thin slice;
- self-test strategy;
- evidence strategy;
- release/operations owner when relevant.

## Commands

| Command | Use |
|---|---|
| `speckit.ai-team.workspace` | create or update repository role and privacy boundary config |
| `speckit.ai-team.start` | route a plain request to bug, feature, or template workflow |
| `speckit.ai-team.context` | open, update, or reconstruct a durable Task Context Package |
| `speckit.ai-team.requirement` | create or refine internal enhancement context and sanitized handoff requirements |
| `speckit.ai-team.codegraph` | generate or attach the code graph slice used for impact and gates |
| `speckit.ai-team.impact` | inspect code graph or source-structure impact before code edits |
| `speckit.ai-team.handoff` | create role-isolated handoff documents between phases |
| `speckit.ai-team.feature-review` | help maintainers and the technical committee assess internal enhancement handoff readiness |
| `speckit.ai-team.pr` | prepare a PR in the correct repository with linked work item and evidence |
| `speckit.ai-team.review` | help human reviewers assess boundary safety and evidence |
| `speckit.ai-team.retrospect` | turn failures into durable process improvements |
| `speckit.ai-team.support` | audit Skill, Knowledge, and Memory support layers |

## Workflow

The bundled `ai-team-sdd` workflow gives feature and new-project work a
resumable path that reuses Spec Kit's native SDD commands:

```text
optional Spec Kit init bootstrap -> workspace contract -> request routing
-> task context package -> route gate -> code graph -> impact
-> speckit.specify -> review-spec gate -> AI Team handoff -> speckit.plan
-> speckit.checklist (native + composite plan gate via preset) -> review-plan gate
-> speckit.tasks -> speckit.analyze (native + composite task gate via preset)
-> review-tasks gate -> speckit.implement -> speckit.converge (native + checks + evidence via preset)
```

The bundled `ai-team-bugfix` workflow gives bug work a deterministic path:

```text
optional Spec Kit init bootstrap -> workspace contract -> task context package
-> request routing -> route gate -> code graph -> impact -> impact gate
-> bug assessment -> assessment gate -> bug fix -> fix gate -> speckit.bug.test (composite checks + evidence via preset)
```

Workspace creation uses Spec Kit's own `init` step. AI Team does not copy
template repositories into product repositories.

`ai-team-sdd` accepts `task_id`, `work_type`, `coding_issue_url`,
`handoff_requirement_url`, backward-compatible `published_requirement_url`, and
`resume_from` so a user can restart feature or new-project work from the
middle. `ai-team-bugfix` accepts `task_id`, `bug_slug`, `coding_issue_url`, and
`resume_from` so a user can restart after route review, impact review, bug
assessment, fix review, testing, evidence, PR, or final review.

## Skill, Knowledge, Memory Support

AI Team work is supported by three external layers:

| Layer | Purpose | Default artifact |
|---|---|---|
| Skill | reusable procedures and tool recipes | skill inventory and reuse review |
| Knowledge | project facts, terminology, boundaries, code graph, impact model | knowledge map |
| Memory | approved historical decisions and curated attempt lessons | memory index |

These layers are external supports, not a single giant prompt. Skills are
loaded when needed, knowledge is sliced by task, and memory is lower precedence
than current source, spec, plan, issue, and owner decisions.

Use [docs/skill-knowledge-memory.md](docs/skill-knowledge-memory.md) for the
full model and `speckit.ai-team.support` to audit a project.

## Installation

AI Team handoff spec behavior requires **three** installs (extension, preset, workflow):

```bash
specify extension add ai-team
specify preset add ai-team-handoff-spec
specify workflow add ai-team-sdd
specify workflow add ai-team-bugfix
```

The `ai-team-handoff-spec` preset appends to native SDD and bug commands:

- effective spec (`spec.override.md`) reading rules for handoff URLs
- plan gate inside `speckit.checklist`, task gate inside `speckit.analyze`
- checks and Evidence Board inside `speckit.converge` (feature) or `speckit.bug.test` (bugfix)

Without the preset, core commands do not know about `spec.override.md` or AI Team gates.
Install the `bug` extension for bugfix composite evidence on `speckit.bug.test`.

For local development:

```bash
specify extension add --dev /path/to/spec-kit/extensions/ai-team
specify preset add --dev /path/to/spec-kit/extensions/ai-team/preset
specify workflow add /path/to/spec-kit/workflows/ai-team-sdd
specify workflow add /path/to/spec-kit/workflows/ai-team-bugfix
```
