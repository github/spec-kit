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
- private enhancement repository and project coding repository separation;
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
extension assumes two logical repositories:

| Repository | Purpose |
|---|---|
| enhancement repository | private feature issues, customer context, approval history, wave plan |
| coding repository | source code, public plan, tasks, implementation PR, Evidence Board |

The repositories may be physically the same for a small team, but the role must
still be explicit in `.specify/extensions/ai-team/ai-team-config.yml`.

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
| `speckit.ai-team.handoff` | create role-isolated handoff documents between phases |
| `speckit.ai-team.plan-gate` | review architecture plan readiness before tasks |
| `speckit.ai-team.task-gate` | review task readiness before implementation |
| `speckit.ai-team.evidence` | produce Evidence Board after implementation |
| `speckit.ai-team.support` | audit Skill, Knowledge, and Memory support layers |

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
