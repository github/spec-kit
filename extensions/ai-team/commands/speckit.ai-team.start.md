---
description: "Route a plain-language request to the correct AI Team bug, feature, requirement, or template workflow and create a Task Context Package."
---

# AI Team Start

Classify a user's one-sentence request before editing code or requirements.

## User Input

```text
$ARGUMENTS
```

## Goal

Create a Task Context Package and choose the next command. Do not start from a
blank prompt and do not inspect private enhancement context unless the active
repository role allows it.

## Required Context

Read when present:

- `.specify/init-options.json` and `.specify/integration.json`;
- `.specify/extensions/ai-team/ai-team-config.yml`;
- `extensions/ai-team/docs/issue-workflow.md` or installed equivalent;
- `extensions/ai-team/docs/task-field-spec.md` or installed equivalent;
- `AGENTS.md`, `CLAUDE.md`, Cursor rules, Trae rules, or the active agent file;
- the coding issue URL, bug slug, or handoff requirement URL named by the user;
- internal enhancement handoff content only when the active repository and
  operator are allowed to read it;
- code graph or source-structure evidence when code, classes, SPI/API, or
  modules are named;
- `.specify/ai-team/tasks/<task-id>/task-context.yml` and `context-pack.md` when the
  request is resuming existing work.

## Routing

| Request type | Route | Required work item |
|---|---|---|
| existing behavior is broken, flaky, regressed, or throws errors | bug fix | coding issue or bug slug with `type/bug` |
| new public capability, scenario, integration, or public behavior in an existing project | feature | coding issue URL or SDD feature request with `type/feature` |
| confidential enterprise feature or roadmap work in an existing project | feature | accepted enhancement-internal issue or handoff URL with `type/feature` |
| create a new product, service, repository, or application from zero | new project | public project issue/charter or handoff requirement URL |
| change AI Team rules, commands, templates, examples, or workflow | template change | this repository PR |
| unclear | ask one focused question | no edits |

Bug fixes should use the dedicated `ai-team-bugfix` workflow when the user wants
an end-to-end bug path. This start command only routes and records context; the
workflow adds route review, impact review, assessment review, and fix-scope
gates around the bundled bug extension:

```text
speckit.bug.assess -> speckit.bug.fix -> speckit.bug.test
```

For deterministic bug workflows, require both:

- `task_id=BUG-<repo-slug>-<issue-number>` for AI Team task context;
- `bug_slug=bug-<repo-slug>-<issue-number>` for `.specify/bugs/<bug_slug>/`.

Features use the SDD path:

```text
coding issue or handoff requirement URL -> speckit.specify
-> review-spec gate -> speckit.ai-team.handoff -> speckit.plan
-> speckit.checklist -> speckit.ai-team.plan-gate -> review-plan gate
-> speckit.tasks -> speckit.analyze -> speckit.ai-team.task-gate
-> review-tasks gate -> speckit.implement -> speckit.converge
-> speckit.ai-team.checks -> speckit.ai-team.evidence
```

If the user has only a private draft or raw customer request, route to
`speckit.ai-team.requirement` first. Code implementation must wait until there
is an accepted handoff requirement or a public-safe coding issue/summary.
When `handoff_requirement_url` is passed to `speckit.plan`, the mandatory
`before_plan` hook (`speckit.ai-team.handoff-spec-sync`) fetches the URL,
bootstraps or preserves `spec.md`, merges into ignored `spec.override.md`, and
downstream commands read the effective spec per preset `ai-team-handoff-spec`.

New projects use the same SDD path but must set `work_type=new-project` and
must keep a stricter build-from-zero plan:

```text
project charter, coding issue, or handoff requirement URL -> specify init/bootstrap
-> speckit.ai-team.workspace -> speckit.ai-team.context
-> speckit.specify -> speckit.ai-team.handoff -> speckit.plan
-> speckit.checklist -> speckit.ai-team.plan-gate -> review-plan gate
-> speckit.tasks -> speckit.analyze -> speckit.ai-team.task-gate
-> review-tasks gate -> speckit.implement -> speckit.converge
-> speckit.ai-team.checks -> speckit.ai-team.evidence
```

The first implementation wave should produce a runnable thin slice before
adding breadth.

## Task Context Package

Return this block and persist it through `speckit.ai-team.context` under
`.specify/ai-team/tasks/<task-id>/`.

```text
Task Context Package:
- task id:
- request:
- classification: bug fix / feature / new project / template change / unclear
- required work item:
- issue type label:
- issue state label:
- work item type:
- coding issue URL:
- bug slug:
- handoff requirement URL:
- published requirement URL, deprecated alias:
- coding repository:
- internal enhancement repository:
- private enhancement context used: no / yes, allowed because ...
- active AI integration:
- workflow run id:
- current phase:
- last completed command:
- source snapshot or code graph version:
- context path:
- task context file:
- likely modules:
- reusable components:
- required commands:
- expected evidence:
- stop conditions:
- next command:
- resume command:
```

After creating or updating the package, return the next command:

- bug fix with enough issue context: `speckit.bug.assess` or
  `speckit.ai-team.codegraph` when source impact is not trivial;
- public feature with a coding issue URL: `speckit.specify` or
  `speckit.ai-team.codegraph` when existing code is named;
- confidential feature without an accepted handoff: `speckit.ai-team.requirement`;
- confidential feature with a handoff requirement URL: `speckit.specify` or
  `speckit.ai-team.codegraph` when existing code is named;
- new project with an approved charter, coding issue, or handoff requirement
  URL: `speckit.specify` after workspace bootstrap;
- interrupted work: `speckit.ai-team.context task_id=<task-id> resume=true`.

## Stop Conditions

Stop and ask when:

- a feature has no coding issue, handoff requirement, or approved task ID;
- an enhancement-internal issue is not `type/feature` or is a bug fix;
- raw customer demand would enter the coding repository;
- a code change crosses module boundaries without code graph or source
  structure evidence;
- the request could be either a bug or a new product behavior and the expected
  behavior cannot be inferred.
