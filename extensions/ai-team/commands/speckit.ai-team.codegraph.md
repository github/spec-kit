---
description: "Generate or attach the code graph slice used by impact analysis, plan gates, task gates, and evidence."
---

# AI Team Code Graph

Generate or attach a code graph slice before source edits, architecture
planning, task generation, or evidence review.

## User Input

```text
$ARGUMENTS
```

## Goal

Give AI agents a source-grounded project projection before they change code.
This command may call a configured code graph service, run a local generator, or
record a fallback source-structure slice. It does not approve design changes.

## Required Inputs

Read when present:

- `.specify/ai-team/tasks/<task-id>/task-context.yml`;
- `.specify/ai-team/tasks/<task-id>/context-pack.md`;
- `.specify/extensions/ai-team/ai-team-config.yml`;
- coding issue or handoff requirement URL for feature work;
- coding issue or bug slug for bug fixes;
- project source files, build files, module docs, and existing tests.

## Adapter Order

Use the configured adapter order first. If no adapter is configured, prefer:

1. SCIP-compatible index when a language indexer is available;
2. Joern for Code Property Graph, data-flow, or security-sensitive analysis;
3. CodeQL when a CodeQL database is already available or security queries are
   part of the evidence;
4. jQAssistant only after license review, mainly for Java/Maven architecture
   rules in teams that accept its license;
5. tree-sitter or source-structure fallback for file/module/symbol dependency
   slices.

Record every attempted adapter, the reason it was selected or skipped, the
license review status, and the confidence level.

## Required Output

Write or attach the code graph slice under:

```text
.specify/ai-team/codegraph/<task-id>/
|-- nodes.jsonl
|-- edges.jsonl
|-- summary.md
`-- adapter-report.md
```

`nodes.jsonl` should use stable IDs and include at least these kinds when they
exist in the project:

```text
repository, module, package, file, class, interface, function, method, config, test
```

`edges.jsonl` should include at least these kinds when the adapter can infer
them:

```text
contains, imports, calls, implements, extends, reads_config, tests, depends_on
```

`summary.md` must include:

- task ID and work item;
- source snapshot or commit;
- adapter and version;
- likely owner module;
- adjacent modules;
- public contracts;
- callers/callees;
- tests tied to affected nodes;
- reuse candidates;
- missing graph evidence.

## Workflow

1. Load the active Task Context Package or create one with
   `speckit.ai-team.context` if needed.
2. Determine whether the task is bug fix, feature, or template work.
3. Select the smallest source slice that can answer the task.
4. Run the configured code graph adapter or attach an existing code graph
   service result.
5. Normalize output to `nodes.jsonl`, `edges.jsonl`, `summary.md`, and
   `adapter-report.md`.
6. Update `.specify/ai-team/tasks/<task-id>/task-context.yml` with the code graph
   artifact path and next command.
7. Hand the graph artifact to `speckit.ai-team.impact`, `speckit.plan`,
   `speckit.ai-team.plan-gate`, `speckit.ai-team.task-gate`, or
   `speckit.ai-team.evidence`.

## Stop Conditions

Stop and ask when:

- no task ID or work item can be resolved;
- the work changes SPI/API, class add/delete, dependency direction, or
  cross-module semantics and no code graph or owner-approved fallback exists;
- adapter output would include private requirement context in a coding
  repository;
- a selected adapter introduces a license or security risk that the team has
  not reviewed;
- graph evidence and source evidence contradict each other.
