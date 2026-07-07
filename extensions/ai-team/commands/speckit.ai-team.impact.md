---
description: "Produce code graph or source-structure impact evidence before source edits."
---

# AI Team Impact

Make source code the first truth and the code graph the first projection before
an AI agent edits production code.

## User Input

```text
$ARGUMENTS
```

## Goal

Create impact evidence for maintainers, module owners, architects, and PR
reviewers. This command does not approve architecture changes.

## Workflow

1. Locate the coding repository and active requirement or bug work item from
   `.specify/ai-team/work/<work_slug>/work-context.yml` when present.
2. Run or load `speckit.ai-team.codegraph` output for the task. If the graph is
   missing, create a source-structure fallback and record confidence.
3. Load the smallest source/code graph slice that includes:
   - likely owner module;
   - public interfaces and abstract base classes;
   - callers and callees;
   - tests;
   - dependency direction;
   - adjacent modules.
4. Identify reuse candidates before proposing new abstractions.
5. Identify high-risk nodes:
   - SPI/API;
   - config;
   - wire/event schema;
   - state owner;
   - database or middleware dependency;
   - examples;
   - generated code.
6. Estimate change radius and likely changed files or classes.
7. Write or return the impact note for plan check, implementation, checks, PR,
   or review.
8. Update the Work Context Package with the impact artifact path, source
   snapshot, current phase, and recommended next command.

## Fallback Rule

If code graph tooling is unavailable, record the attempted tool, fallback
sources, confidence, and missing evidence. Fallback evidence is not enough for
public SPI/API changes, class add/delete, dependency direction changes, or
cross-module semantic changes unless a human owner accepts the risk.

## Output Shape

```text
Code graph impact:
- task id:
- work item:
- coding issue, handoff requirement URL, or bug slug:
- context path:
- code graph version or fallback snapshot:
- code graph artifact:
- likely owner module:
- adjacent modules:
- public contracts touched:
- classes or files likely to change:
- callers/callees affected:
- tests related to touched nodes:
- reuse candidates:
- change radius: local / module / cross-module / architecture
- required human review:
- stop conditions:
- recommended next command:
```

## Stop Conditions

Stop and ask when:

- the owner module cannot be identified;
- required code graph or equivalent structure evidence is missing;
- the change crosses module boundaries without owner review;
- the request depends on another component's private database, middleware, or
  internal state;
- the implementation would create a parallel abstraction without checking reuse
  candidates.
