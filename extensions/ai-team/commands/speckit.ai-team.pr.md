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
| published requirement or RFC text | requirements-published repository |
| private drafts, raw demand, approval discussion | requirements-internal repository |
| AI Team rules, commands, templates, workflows | this distribution repository |

Coding repository feature PRs must link the published requirement URL. They
must not link private requirement drafts or rely on local paths such as
`requirements/rfcs/REQ-...md` as the authoritative work item.

## Pre-Submit Checklist

1. Run `git status --short --branch`.
2. Confirm the current repository role.
3. Load the Task Context Package from `.specify/ai-team/tasks/<task-id>/`
   when present.
4. Exclude:
   - `.ai-local/`;
   - local prompts or scratch notes;
   - private requirements drafts from coding repository PRs;
   - generated reports unless the repository explicitly tracks them.
5. Confirm links:
   - bug fix links a coding issue or bug slug;
   - feature links a published requirement URL;
   - requirement publication links the internal source only in the private
     repository.
6. Confirm evidence:
   - Task Context Package;
   - code graph impact when applicable;
   - commands and tests;
   - Evidence Board or portable checks;
   - skipped verification.
7. Update the Task Context Package with PR URL, current phase, and next
   command when a PR is created.

## PR Description Shape

```text
AI Team PR:
- task id:
- context path:
- repository role:
- work reason: bug fix / feature / requirement publication / template change
- linked coding issue:
- published requirement URL:
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
- a coding feature PR lacks a published requirement URL;
- private requirement content is present in the coding repo diff;
- evidence is missing for changed behavior;
- the current branch is the repository default branch.
