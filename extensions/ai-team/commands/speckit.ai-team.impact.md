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

Impact interprets graph/source facts for one request; it does not generate the
normalized graph owned by `speckit.ai-team.codegraph`.

## Workflow

1. Select formal work context, or
   `.specify/ai-team/intake/<intake_slug>/` when `intake_mode=true`. Locate the
   coding repository and request from that selected context.
2. Verify the analysis-mode `permission-envelope.yml` covers the source and
   code graph reads, commands, and network access needed for impact analysis.
3. Run or load `speckit.ai-team.codegraph` output for the task. If the graph is
   missing, create a source-structure fallback and record confidence.
4. Load the smallest source/code graph slice that includes:
   - likely owner module;
   - public interfaces and abstract base classes;
   - callers and callees;
   - tests;
   - dependency direction;
   - adjacent modules.
5. Identify reuse candidates before proposing new abstractions.
6. Identify high-risk nodes:
   - SPI/API;
   - config;
   - wire/event schema;
   - state owner;
   - database or middleware dependency;
   - examples;
   - generated code.
7. Estimate change radius and likely changed files or classes.
8. For Intake, write `impact-summary.md` under the Intake directory. For formal
   work, write or return the impact note for plan, implementation, checks, PR,
   or review.
9. Update `intake.yml` or the formal Work Context with the impact artifact,
   source snapshot, current phase, and recommended next command.

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
- the analysis Permission Envelope is missing, stale, or does not authorize the
  required source/code graph access;
- hard runtime confinement is required but no verified `agent-native` or
  `wrapper-enforced` adapter is active;
- required code graph or equivalent structure evidence is missing;
- the change crosses module boundaries without owner review;
- the request depends on another component's private database, middleware, or
  internal state;
- the implementation would create a parallel abstraction without checking reuse
  candidates.
