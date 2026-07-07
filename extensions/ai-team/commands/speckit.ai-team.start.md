---
description: "Route a plain-language request to the correct AI Team bug, requirement, or template workflow and create a Task Context Package."
---

# AI Team Start

Classify a user's one-sentence request before editing code or requirements.

## User Input

```text
$ARGUMENTS
```

## Goal

Create a Task Context Package and choose the next command. Do not start from a
blank prompt and do not inspect private requirements unless the active
repository role allows it.

## Required Context

Read when present:

- `.specify/init-options.json` and `.specify/integration.json`;
- `.specify/extensions/ai-team/ai-team-config.yml`;
- `AGENTS.md`, `CLAUDE.md`, Cursor rules, Trae rules, or the active agent file;
- the published requirement URL named by the user;
- `requirements/` only when it is a Git submodule pointing at the published
  requirements repository;
- code graph or source-structure evidence when code, classes, SPI/API, or
  modules are named.
- `.specify/ai-team/tasks/<task-id>/state.yml` and `context-pack.md` when the
  request is resuming existing work.

## Routing

| Request type | Route | Required work item |
|---|---|---|
| existing behavior is broken, flaky, regressed, or throws errors | bug fix | coding issue or bug slug |
| new capability, scenario, integration, public behavior, or roadmap work | feature | published requirement URL |
| change AI Team rules, commands, templates, examples, or workflow | template change | this repository PR |
| unclear | ask one focused question | no edits |

Bug fixes use the bundled bug extension:

```text
speckit.bug.assess -> speckit.bug.fix -> speckit.bug.test
```

Features use the SDD path:

```text
published requirement URL -> speckit.specify -> speckit.ai-team.handoff
-> speckit.plan -> speckit.ai-team.plan-gate -> speckit.tasks
-> speckit.ai-team.task-gate -> speckit.implement
-> speckit.ai-team.evidence
```

If the user has only a private draft or raw customer request, route to
`speckit.ai-team.requirement` first. Code implementation must wait until there
is a published requirement URL.

## Task Context Package

Return this block and persist it through `speckit.ai-team.context` under
`.specify/ai-team/tasks/<task-id>/`.

```text
Task Context Package:
- task id:
- request:
- classification: bug fix / feature / template change / unclear
- required work item:
- coding issue URL or bug slug:
- published requirement URL:
- coding repository:
- requirements published repository:
- requirements submodule path:
- private requirements context used: no / yes, allowed because ...
- active AI integration:
- workflow run id:
- current phase:
- last completed command:
- source snapshot or code graph version:
- context path:
- state file:
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
- feature without a published requirement URL: `speckit.ai-team.requirement`;
- feature with a published requirement URL: `speckit.specify` or
  `speckit.ai-team.codegraph` when existing code is named;
- interrupted work: `speckit.ai-team.context task_id=<task-id> resume=true`.

## Stop Conditions

Stop and ask when:

- a feature has no published requirement URL;
- raw customer demand would enter the coding repository;
- a code change crosses module boundaries without code graph or source
  structure evidence;
- the request could be either a bug or a new product behavior and the expected
  behavior cannot be inferred.
