---
description: "Generate or attach the code graph slice used by impact analysis, plan checks, task gates, and evidence."
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

Select exactly one context root:

- formal work: `.specify/ai-team/work/<work_slug>/`;
- pre-work-item analysis: `intake_mode=true`, `intake_slug=<slug>`, and
  `.specify/ai-team/intake/<intake_slug>/`.

Read when present under the selected root:

- `.specify/ai-team/work/<work_slug>/work-context.yml`;
- `.specify/ai-team/work/<work_slug>/permission-envelope.yml`;
- `.specify/ai-team/work/<work_slug>/context-pack.md`;
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

Write or attach the code graph slice under the selected root:

```text
.specify/ai-team/work/<work_slug>/codegraph/
or .specify/ai-team/intake/<intake_slug>/codegraph/
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

- work slug and work item;
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

1. Load the formal Work Context Package, or the Intake artifact when
   `intake_mode=true`. Never create formal context merely to analyze Intake.
2. Require an analysis-mode Permission Envelope. Verify that its repository,
   read paths, commands, network access, approval state, and enforcement mode
   cover the proposed graph operation. Do not treat a workflow gate as a
   runtime sandbox.
3. Determine whether the work is bug fix, feature, or template work.
4. Select the smallest source slice that can answer the work unit.
5. Run the configured code graph adapter or attach an existing code graph
   service result.
6. Normalize output to `nodes.jsonl`, `edges.jsonl`, `summary.md`, and
   `adapter-report.md`.
7. Update `work-context.yml` for formal work or `intake.yml` for Intake with
   the graph path, source snapshot, status, and next command.
8. Hand the graph artifact to `speckit.ai-team.impact`, `speckit.plan`,
   `speckit.ai-team.plan-check`, `speckit.analyze`, or `speckit.converge`
   (composite checks and evidence run inside converge when preset
   `ai-team-sdd-governance` is installed).

## Stop Conditions

Stop and ask when:

- neither a formal work unit nor a valid Intake unit can be resolved;
- the analysis Permission Envelope is missing, stale, not approved when
  approval is required, or does not cover the requested access;
- hard runtime confinement is required but the effective enforcement mode is
  only `policy-only`;
- the work changes SPI/API, class add/delete, dependency direction, or
  cross-module semantics and no code graph or owner-approved fallback exists;
- adapter output would include private requirement context in a coding
  repository;
- a selected adapter introduces a license or security risk that the team has
  not reviewed;
- graph evidence and source evidence contradict each other.
