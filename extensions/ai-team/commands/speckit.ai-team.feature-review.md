---
description: "Help maintainers and the technical committee assess feature work-item readiness before coding."
---

# AI Team Feature Review

Help a maintainer or technical committee review a feature work item before it
is accepted for implementation. Public work may start from a coding issue.
Confidential enterprise work should start from an internal enhancement handoff.
This command does not approve on behalf of humans.

## User Input

```text
$ARGUMENTS
```

## Role Rule

The technical committee is the small decision-making group for whether a new
feature should exist and how it fits product direction. A SIG or working group
may include development, test, and maintenance participants, but it is not the
feature approval authority unless explicitly delegated.

## Review Questions

- Is there a Work Context Package tying this review to the requirement and
  intended coding repository?
- Is the user problem or product goal concrete?
- Is the work item stable: public coding issue, allowed handoff URL, or
  public-safe summary?
- Does the issue use `type/feature` and exactly one valid state label?
- If the work item is in enhancement-internal, confirm it is not a bug fix.
- Is private customer demand excluded from public artifacts?
- Are scope and non-goals explicit?
- Are likely modules, maintainers, owners, and reviewers named?
- Is the approval route clear?
- Does the feature fit current module boundaries?
- Does it affect SPI/API, config, wire schema, metrics, examples, dependencies,
  compatibility, migration, release, or operations?
- Is the first wave small enough to implement and verify?
- Are developer self-test and evidence expectations clear?

## Decision Options

| Decision | Meaning |
|---|---|
| accept | clear enough for the named wave and approved by the required authority |
| revise | valuable but missing scope, owner, evidence, or compatibility detail |
| split | valuable but too large or crosses too many modules |
| reject | not aligned, duplicate, unsafe, or not a product goal |
| architecture review | changes boundaries, state ownership, or public contracts |

## Output Shape

```text
Feature review:
- task id:
- context path:
- coding issue or handoff requirement URL:
- issue type label:
- issue state label:
- public-safe summary:
- recommended decision:
- reason:
- affected coding repository:
- likely modules:
- architecture fit:
- public interface impact:
- approval route:
- dependency/security impact:
- wave plan quality:
- acceptance evidence:
- required human approver:
- required edits before acceptance:
```

## Stop Conditions

Stop instead of recommending acceptance when:

- the coding repository or modules are unknown;
- the approval route is missing;
- the issue is not labeled `type/feature`, has multiple state labels, or is an
  enhancement-internal bug fix;
- the feature asks "should we build this?" with no technical committee or
  delegated product authority;
- the first wave requires invented semantics;
- public interface, dependency, license, security, compatibility, or migration
  impact is unresolved;
- required code graph or source-structure evidence is missing.
