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

## Existing Project vs New Project

Existing project work must start from code graph and impact radius:

- owner module;
- public contracts;
- callers/callees;
- reuse candidates;
- changed nodes;
- self-test mapping.

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
| `speckit.ai-team.requirement` | publish or refine the sanitized requirement URL needed for feature work |
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
-> code graph impact -> plan/task gates -> Evidence Board
```

Workspace creation uses Spec Kit's own `init` step. AI Team does not copy
template repositories into product repositories.

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
