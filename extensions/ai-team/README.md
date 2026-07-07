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
- private requirements, published requirements, and coding repository
  separation;
- URL-oriented requirement references, with the coding repository consuming only
  published requirement URLs and optional read-only submodule content;
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
extension assumes three logical repositories:

| Repository | Purpose |
|---|---|
| requirements-internal | private drafts, raw demand, approval discussion, wave plan, commercial context |
| requirements-published | sanitized public requirement/RFC documents with stable URLs |
| coding repository | source code, public plan, tasks, implementation PR, Evidence Board, optional read-only requirements submodule |

The coding repository may include `requirements/` as a Git submodule pointing to
`requirements-published`. Feature work links the published requirement URL as
the authoritative work item; local submodule paths are only a cache for reading
published content.

The coding repository must not record or depend on `requirements-internal`.
Private repository paths belong in private operator context or the internal
requirements repository, not in committed coding-repository files.

Use [docs/repository-boundary.md](docs/repository-boundary.md) for the full
repository model.

## Task Context and Resume

Every AI Team task should have a durable Task Context Package:

```text
.specify/ai-team/tasks/<task-id>/context-pack.md
.specify/ai-team/tasks/<task-id>/state.yml
```

For feature work, `<task-id>` comes from the published requirement URL or
requirement ID. For bug fixes, it comes from the coding issue or bug slug.

If the workflow pauses at a gate, resume the same run with
`specify workflow resume <run-id>`. If the terminal, AI tool, or chat context is
lost, reload the task with:

```bash
speckit.ai-team.context task_id=<task-id> resume=true
```

Use [docs/task-context-package.md](docs/task-context-package.md) for the
storage format, phase model, and resume protocol.

## User Journeys

Use [docs/user-journeys.md](docs/user-journeys.md) for the complete
step-by-step journeys. The short version:

| Journey | Work item | Main path |
|---|---|---|
| existing project bug fix | coding issue or bug slug | context -> code graph when needed -> impact -> bug assess/fix/test -> checks/evidence -> PR |
| existing project new feature | published requirement URL | requirement review -> context -> code graph -> specify/plan/tasks/implement -> evidence -> PR |
| new project from zero | published project charter or requirement URL | bootstrap -> workspace -> context -> specify/plan with strict build plan -> thin slice -> evidence |
| resume from middle | workflow run ID or task ID | workflow resume for paused runs, or `speckit.ai-team.context task_id=<task-id> resume=true` for cross-session recovery |
| failed review/check/incident | PR, check, incident, or repeated AI mistake | retrospect -> update command, gate, knowledge, memory, graph, or test evidence |

### Chat Aliases

When users work in a chat-first AI coding tool, use the same workflow name for
every path:

| Chat alias | Maps to |
|---|---|
| `ai-team-sdd feature path` | `work_type=feature` plus a published requirement URL |
| `ai-team-sdd bug path` | `work_type=bug` plus a coding issue URL or bug slug |
| `ai-team-sdd new-project path` | `work_type=new-project` plus a published project charter or requirement URL |
| `ai-team-sdd resume path` | `task_id=<task-id>` plus `resume_from=<phase>` or workflow run resume |

Recommended prompts:

```text
Use the ai-team-sdd feature path for this published requirement URL:
https://example.com/requirements/rfcs/REQ-2026-015

Use the ai-team-sdd bug path for this coding issue:
https://example.com/org/project/issues/123
```

### Existing Project Bug Fix

Bug fixes must link a coding repository issue or bug slug. The reporter may
describe only symptoms; the AI agent uses source evidence and code graph impact
to find the likely module. The actual bug lifecycle uses the bundled bug
extension:

```text
speckit.bug.assess -> speckit.bug.fix -> speckit.bug.test
```

AI Team adds the task context, code graph impact, portable checks, Evidence
Board, PR description, and review gates around that bug lifecycle.

### Existing Project New Feature

Feature work must link a published requirement URL from the
requirements-published repository. If the only available input is a private
draft or raw customer request, run `speckit.ai-team.requirement` and
`speckit.ai-team.feature-review` before coding.

The coding repository should not record requirements-internal paths or raw
customer demand.

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
| `speckit.ai-team.requirement` | publish or refine the sanitized requirement URL needed for feature work |
| `speckit.ai-team.codegraph` | generate or attach the code graph slice used for impact and gates |
| `speckit.ai-team.impact` | inspect code graph or source-structure impact before code edits |
| `speckit.ai-team.handoff` | create role-isolated handoff documents between phases |
| `speckit.ai-team.plan-gate` | review architecture plan readiness before tasks |
| `speckit.ai-team.task-gate` | review task readiness before implementation |
| `speckit.ai-team.feature-review` | help maintainers and the technical committee assess published requirement readiness |
| `speckit.ai-team.checks` | produce portable CI/CD evidence on any git platform |
| `speckit.ai-team.evidence` | produce Evidence Board after implementation |
| `speckit.ai-team.pr` | prepare a PR in the correct repository with linked work item and evidence |
| `speckit.ai-team.review` | help human reviewers assess boundary safety and evidence |
| `speckit.ai-team.retrospect` | turn failures into durable process improvements |
| `speckit.ai-team.support` | audit Skill, Knowledge, and Memory support layers |

## Workflow

The bundled `ai-team-sdd` workflow gives teams a resumable skeleton:

```text
optional Spec Kit init bootstrap -> workspace contract -> request routing
-> task context package -> code graph -> impact -> plan/task gates
-> Evidence Board
```

Workspace creation uses Spec Kit's own `init` step. AI Team does not copy
template repositories into product repositories.

The workflow accepts `task_id`, `work_type`, `coding_issue_url`, `bug_slug`,
`published_requirement_url`, and `resume_from` so a user can restart from the
middle after a requirement approval, bug triage, plan gate, task gate, or
implementation interruption.

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

```bash
specify extension add ai-team
```

For local development:

```bash
specify extension add --dev /path/to/spec-kit/extensions/ai-team
```
