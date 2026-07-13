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
- contributor/maintainer-controlled memory consolidation so completed work does
  not leave unbounded context behind;
- release-scoped archive as a batch view of the same memory consolidation flow.
- external Skill, Knowledge, and Memory support layers around the project.
- durable Work Context Packages so interrupted work can resume from a work item
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

## Work Context and Resume

Every AI Team work unit should have a durable Work Context Package:

```text
.specify/ai-team/work/<work_slug>/context-pack.md
.specify/ai-team/work/<work_slug>/work-context.yml
.specify/ai-team/work/<work_slug>/handoffs/
.specify/ai-team/work/<work_slug>/codegraph/
.specify/ai-team/work/<work_slug>/evidence/
```

For feature work, `<work_slug>` is the basename of the Spec Kit feature directory
(for example `003-user-auth` under `specs/`). For bug fixes, `<work_slug>` equals
`bug_slug`.

If the workflow pauses at a gate, resume the same run with
`specify workflow resume <run-id>`. If the terminal, AI tool, or chat context is
lost, reload the work with:

```bash
speckit.ai-team.context work_slug=<work_slug> resume=true
```

Use [docs/work-context-package.md](docs/work-context-package.md) for the
storage format, phase model, and resume protocol. Use
[docs/work-field-spec.md](docs/work-field-spec.md) for canonical `work_slug`,
`bug_slug`, `coding_issue_url`, and `handoff_requirement_url` rules.

## User Journeys

Use [docs/user-journeys.md](docs/user-journeys.md) for the complete
step-by-step journeys. The short version:

| Journey | Work item | Main path |
|---|---|---|
| existing project bug fix | coding issue or bug slug | `ai-team-bugfix`: context -> context gate -> code graph -> impact gate -> bug assess -> assessment gate -> bug fix -> fix gate -> `speckit.bug.test` (composite checks/evidence) -> PR |
| existing project new feature | coding issue URL or handoff requirement URL | optional requirement review -> context -> code graph -> native SDD with plan check, task gate, and converge evidence -> PR |
| new project from zero | public project issue/charter or handoff requirement URL | bootstrap -> workspace -> context -> native SDD with plan-check, task gate (preset), and converge evidence -> thin slice -> PR |
| resume from middle | workflow run ID or work slug | workflow resume for paused runs, or `speckit.ai-team.context work_slug=<work_slug> resume=true` for cross-session recovery |
| failed review/check/incident | PR, check, incident, or repeated AI mistake | retrospect -> update command, gate, knowledge, memory, graph, or test evidence |
| memory consolidation | work slug, bug slug, PR, incident, release id, or manual lesson | sanitize -> choose local/department/enterprise tier -> sync/index -> promote to skill, knowledge, test, gate, or playbook |
| release archive | release id, tag range, release issue, or work slugs | release-scoped memory consolidation -> bugfix lessons -> feature decisions -> migration playbook -> support memory/knowledge update |

### Chat Aliases

When users work in a chat-first AI coding tool, use these stable workflow
aliases instead of asking the user to remember command details:

| Chat alias | Maps to |
|---|---|
| `ai-team-sdd feature path` | `work_type=feature` plus a coding issue URL or handoff requirement URL |
| `ai-team-bugfix path` | `work_slug=bug-<repo-slug>-<issue-number>` and an optional coding issue URL |
| `ai-team-sdd new-project path` | `work_type=new-project` plus a public project issue/charter or handoff requirement URL |
| `ai-team-sdd resume path` | `work_slug=<work_slug>` plus `resume_from=<phase>` or workflow run resume |
| `ai-team-memory consolidate path` | completed work source plus `target_tier=local|department|enterprise` |
| `ai-team-release archive path` | release id plus tag range, release issue, or shipped work slugs |

Recommended prompts:

```text
Use the ai-team-sdd feature path for this public coding issue:
https://example.com/org/project/issues/456

Use the ai-team-sdd feature path for this internal handoff requirement:
https://example.com/enhancements/rfcs/REQ-2026-015

Use the ai-team-bugfix path with work_slug=bug-project-alpha-123 for this coding issue:
https://example.com/org/project/issues/123

Use the ai-team-memory consolidate path for bug_slug=bug-project-alpha-123
target_tier=department. Summarize the bugfix lesson after sanitizing private
details.

Use the ai-team-release archive path for release_id=v1.4.0 since_tag=v1.3.0.
Focus on bugfix lessons and reusable design patterns.
```

### Existing Project Bug Fix

Bug fixes should use the dedicated `ai-team-bugfix` workflow. Bug work should
link a coding repository issue when possible and must provide a stable
`work_slug` (equal to `bug_slug`). The reporter may describe only
symptoms; the AI agent uses source evidence and code graph impact to find the
likely module. The actual bug lifecycle uses the bundled bug extension:

```text
speckit.bug.assess -> speckit.bug.fix -> speckit.bug.test
```

AI Team adds work context, route review, code graph impact, architecture impact
review, assessment review, fix-scope review, and composite checks/Evidence Board
(via preset inside `speckit.bug.test`), plus PR description and review support
around that bug lifecycle.

### Existing Project New Feature

Feature work must link a work item. Public feature work can use a coding
repository issue. Confidential enterprise feature work should use
`speckit.ai-team.requirement` and `speckit.ai-team.feature-review` to produce a
sanitized handoff requirement before coding.

The coding repository should not record raw customer demand or private
enhancement draft paths.

### New Project From Zero

New projects use `work_type=new-project`. They still follow SDD, but
`speckit.ai-team.plan-check` is stricter: it must establish the project skeleton,
architecture spine, dependency strategy, runnable thin slice, self-test strategy,
and evidence strategy before broad feature construction.

### Resume From Middle

Use Spec Kit workflow state for the same paused workflow run:

```bash
specify workflow status <run-id>
specify workflow resume <run-id>
```

Use the AI Team Work Context Package when switching terminal, AI tool, or chat:

```text
speckit.ai-team.context work_slug=<work_slug> resume=true
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
| `speckit.ai-team.start` | chat-first routing to bug, feature, or template workflow (not a bundled workflow step) |
| `speckit.ai-team.context` | open, update, or reconstruct a durable Work Context Package |
| `speckit.ai-team.requirement` | create or refine internal enhancement context and sanitized handoff requirements |
| `speckit.ai-team.codegraph` | generate or attach the code graph slice used for impact and gates |
| `speckit.ai-team.impact` | inspect code graph or source-structure impact before code edits |
| `speckit.ai-team.plan-check` | assess plan readiness after `speckit.plan`; chat report only (no gate file) |
| `speckit.ai-team.handoff` | create role-isolated handoff documents between phases |
| `speckit.ai-team.feature-review` | help maintainers and the technical committee assess internal enhancement handoff readiness |
| `speckit.ai-team.pr` | prepare a PR in the correct repository with linked work item and evidence |
| `speckit.ai-team.review` | help human reviewers assess boundary safety and evidence |
| `speckit.ai-team.retrospect` | turn failures into durable process improvements |
| `speckit.ai-team.memory-consolidate` | consolidate completed work into local, department, or enterprise memory |
| `speckit.ai-team.release-archive` | archive a release and distill feature, bugfix, migration, and operations knowledge |
| `speckit.ai-team.support` | audit Skill, Knowledge, and Memory support layers |

## Workflow

The bundled `ai-team-sdd` workflow gives feature and new-project work a
resumable path that reuses Spec Kit's native SDD commands:

```text
optional Spec Kit init bootstrap -> workspace contract -> request routing
-> work context package -> context gate -> code graph -> impact
-> speckit.specify -> review-spec gate -> AI Team handoff -> speckit.plan
-> speckit.ai-team.plan-check -> review-plan gate
-> speckit.tasks -> speckit.analyze (native cross-artifact report)
-> review-tasks gate -> speckit.implement -> speckit.converge (native + checks + evidence via preset)
```

### Plan check, preset, and workflow gates

| Step | Type | Writes files? | Human decision |
|---|---|---|---|
| `speckit.ai-team.plan-check` | extension command | Updates `work-context.yml` (`plan_check`) and `context-pack.md` only | No; produces chat report |
| `review-plan` | workflow gate | No | Yes; approve / revise / reject before `tasks` |
| `speckit.analyze` | native cross-artifact check | Read-only chat report | No; produces analyze report |
| `review-tasks` | workflow gate | No | Yes; approve / revise / reject before `implement` |

Plan check does **not** run core `speckit.checklist` and does **not** create
`checklists/*.md` or `plan-check.md`. Cross-artifact consistency before
implementation is covered by native `speckit.analyze`.

At `review-plan`, choose **revise** when the Plan Check Report recommends changes;
the workflow **re-runs** `speckit.plan` and `speckit.ai-team.plan-check` automatically
(`plan-cycle` do-while loop). On revise, `speckit.plan` receives a fixed revision
prompt (work slug only) to patch `plan.md` from `plan_check` and `context-pack.md`,
not the original spec/request args. At `review-tasks`, **revise** re-runs
`speckit.tasks` and `speckit.analyze` (`task-cycle` loop) with the same pattern for
`tasks.md` and native analyze findings.

The bundled `ai-team-bugfix` workflow gives bug work a deterministic path:

```text
optional Spec Kit init bootstrap -> workspace contract -> work context package
-> work context package -> context gate -> code graph -> impact -> impact gate
-> bug assessment -> assessment gate -> bug fix -> fix gate -> speckit.bug.test (composite checks + evidence via preset)
```

Workspace creation uses Spec Kit's own `init` step. AI Team does not copy
template repositories into product repositories.

Memory consolidation is deliberately a contributor/maintainer-controlled command,
not a required feature or bugfix workflow step. Run
`speckit.ai-team.memory-consolidate` whenever a useful lesson is ready. Use
`speckit.ai-team.release-archive` at release-candidate, final release, milestone,
or maintainer-chosen checkpoint time to batch the same process across many work
items. Use [docs/memory-tiers.md](docs/memory-tiers.md) for the three-tier memory
model and [docs/release-archive.md](docs/release-archive.md) for the
release-scoped artifact contract.

`ai-team-sdd` accepts `work_slug`, `work_type`, `coding_issue_url`,
`handoff_requirement_url`, backward-compatible `published_requirement_url`, and
`resume_from` so a user can restart feature or new-project work from the
middle. `ai-team-bugfix` accepts `work_slug`, `coding_issue_url`, and
`resume_from` so a user can restart after context review, impact review, bug
assessment, fix review, testing, evidence, PR, or final review.

## Skill, Knowledge, Memory Support

AI Team work is supported by three external layers:

| Layer | Purpose | Default artifact |
|---|---|---|
| Skill | reusable procedures and tool recipes | skill inventory and reuse review |
| Knowledge | project facts, terminology, boundaries, code graph, impact model | knowledge map |
| Memory | local, department, and enterprise historical decisions and curated attempt lessons | memory index or mem0-like service |

These layers are external supports, not a single giant prompt. Skills are
loaded when needed, knowledge is sliced by task, and memory is lower precedence
than current source, spec, plan, issue, and owner decisions.

Memory consolidation feeds this support layer. Bugfix lessons usually start as
local or department attempt memory; release-level architecture or compatibility
choices become enterprise decision memory only when a human owner accepted them.
Reusable designs move into the migration playbook and knowledge map so similar
projects can start from reviewed patterns rather than old chat or PR archaeology.

Use [docs/skill-knowledge-memory.md](docs/skill-knowledge-memory.md) for the
full model, [docs/memory-tiers.md](docs/memory-tiers.md) for the three memory
tiers, [docs/release-archive.md](docs/release-archive.md) for release-scoped
knowledge consolidation, and `speckit.ai-team.support` to audit a project.

## Installation

AI Team handoff spec and composite gates require **extension + preset + workflow**
installs (plus `bug` for bugfix):

```bash
specify extension add ai-team
specify extension add bug
specify preset add ai-team-handoff-spec
specify workflow add ai-team-sdd
specify workflow add ai-team-bugfix
```

The `ai-team-handoff-spec` preset composes into native SDD and bug commands:

- **prepend** on `plan`, `tasks`, `plan-template`: prefer `spec.override.md` when reading requirements
- **wrap** on `converge`: handoff spec before core steps, composite checks / evidence after
- **append** on `bug.test`: checks and evidence board after bug verification

Plan check is **`speckit.ai-team.plan-check`** (extension command, chat report only).
It is **not** part of the preset and is **not** core `speckit.checklist`.

Without the preset, core commands do not know about `spec.override.md` or AI Team
checks / evidence rules.
The `bug` extension supplies `speckit.bug.test`, which receives composite checks
and Evidence Board rules from the preset during bugfix workflows.

For local development:

```bash
specify extension add --dev /path/to/spec-kit/extensions/ai-team
specify preset add --dev /path/to/spec-kit/extensions/ai-team/preset
specify workflow add /path/to/spec-kit/workflows/ai-team-sdd
specify workflow add /path/to/spec-kit/workflows/ai-team-bugfix
```
