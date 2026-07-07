---
description: "Run or reconstruct portable CI/CD evidence when platform CI is unavailable or insufficient."
---

# AI Team Checks

Produce the evidence expected from CI/CD even when the git hosting platform has
no usable pipeline.

## User Input

```text
$ARGUMENTS
```

## Check Levels

| Level | When | Evidence |
|---|---|---|
| repository governance | every PR | no private requirement leakage, no local AI scratch files |
| project build | source or tests changed | project build command from docs or profile |
| developer self-test | behavior changed | affected unit/self-tests and self-test map |
| contract or boundary | SPI/API, config, schema, class add/delete, cross-module behavior | code graph impact and contract tests when available |
| release scoped | release notes, deployment, dependency/security impact | release verification or explicit deferral |

## Workflow

1. Identify the target repository role: coding, enhancement-internal, or
   template.
2. Load `.specify/ai-team/tasks/<task-id>/state.yml` and `context-pack.md`
   when present.
3. Identify changed files and PR base.
4. Confirm feature PRs link the correct work item: coding issue for public
   work, or allowed handoff requirement/public-safe summary for confidential
   enterprise work.
5. Run repository governance checks.
6. Run build and self-tests for touched source/test/example/module docs.
7. Run boundary evidence when public contracts or cross-module behavior changed.
8. Record skipped checks with concrete reasons.
9. Update the Task Context Package with checks, skipped checks, current phase,
   and next command.
10. Hand evidence to `speckit.ai-team.pr` or `speckit.ai-team.review`.

## Evidence Board Output

```text
Evidence Board:
- task id:
- context path:
- repository:
- role:
- task goal:
- linked work item:
- coding issue or handoff requirement URL:
- base:
- code graph location or fallback:
- reused components:
- changed nodes:
- change radius:
- commands run:
- tests run:
- self-test mapping:
- uncovered paths:
- security or dependency impact:
- rollback or recovery note:
- human review points:
- checks not run:
- reason for each skipped check:
- platform CI status: available / unavailable / not trusted / not applicable
- residual risk:
```

## Stop Conditions

Stop and ask when:

- the target repository or base branch is unknown;
- required build commands are missing;
- feature evidence lacks a coding issue, handoff requirement, or approved task ID;
- public interface changes lack owner or contract evidence;
- dependency, license, or security-impact changes lack review evidence.
