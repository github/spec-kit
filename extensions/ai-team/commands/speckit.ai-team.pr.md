---
description: "Prepare a pull request in the correct repository with linked work item and evidence."
---

# AI Team Pull Request

Create a pull request containing only the intended changes in the correct
repository.

## User Input

```text
$ARGUMENTS
```

## Repository Routing

| Changed thing | Submit to |
|---|---|
| source code, tests, examples, public plan, tasks, evidence | coding repository |
| internal enhancement issue, handoff RFC, private drafts, raw demand, approval discussion | enhancement-internal repository |
| AI Team rules, commands, templates, workflows | this distribution repository |

Coding repository feature PRs must link the correct work item. Public feature
work links a coding issue or SDD feature request. Confidential enterprise work
links an allowed handoff requirement URL, or carries a public-safe summary when
the coding repository is public. Coding PRs must not link private enhancement
drafts or rely on local paths as the authoritative work item.

## Pre-Submit Checklist

1. Run `git status --short --branch`.
2. Confirm the current repository role.
3. Load the Work Context Package from `.specify/ai-team/work/<work_slug>/`
   when present.
4. Resolve `spec.md`, `plan.md`, `tasks.md`, bug reports, and evidence from
   their native locations. Load `permission-envelope.yml` and compare it with actual
   reads, writes, commands, dependency operations, and network access.
5. Exclude:
   - `.ai-local/`;
   - local prompts or scratch notes;
   - private enhancement drafts from coding repository PRs;
   - `spec.override.md`;
   - generated reports unless the repository explicitly tracks them.
6. Confirm links:
   - bug fix links a primary coding issue;
   - public feature links a coding issue;
   - confidential feature links an allowed handoff requirement or public-safe
     summary;
   - internal enhancement records link private source material only inside the
     internal repository;
   - additional coding issues are included only when they are different
     symptoms of the same root-cause change, and each has verification evidence.
7. Confirm evidence:
   - Work Context Package;
   - code graph impact when applicable;
   - `spec.override.md` is ignored when internal handoff context was used;
   - commands and tests;
   - Evidence Board or portable checks;
   - skipped verification.
8. Update the Work Context Package with PR URL, current phase, permission
   status, and next command when a PR is created.

## PR Description Shape

```text
AI Team PR:
- task id:
- context path:
- permission envelope:
- permission enforcement mode and gaps:
- repository role:
- work reason: bug fix / feature / requirement publication / template change
- linked coding issue:
- also resolves coding issues:
- handoff requirement URL:
- public-safe summary:
- target module:
- public interface impact:
- code graph impact:
- tests and commands:
- platform CI status:
- evidence:
- skipped verification:
- human reviewer expectations:
- private requirement leakage check:
```

## Stop Conditions

Stop before staging when:

- the current repo role is unclear;
- a coding feature PR lacks a coding issue, handoff requirement, or approved task ID;
- private requirement content is present in the coding repo diff;
- evidence is missing for changed behavior;
- work context and native SDD or bug artifacts identify different work items;
- actual operations exceeded the Permission Envelope;
- hard runtime confinement was required but only `policy-only` controls were
  available;
- the current branch is the repository default branch.
