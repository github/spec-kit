---
description: "Create or refine an internal enhancement record and sanitized handoff requirement for confidential enterprise feature work."
---

# AI Team Requirement Handoff

Use this before feature or new-project implementation when the user has
confidential enterprise demand, a private draft, a project charter, or internal
approval discussion that should not start in the public coding repository.

Public feature requests do not need this command by default. They can start as
coding repository issues or SDD feature requests.

## User Input

```text
$ARGUMENTS
```

## Goal

Move confidential feature intent through the internal enhancement repository
without leaking raw customer demand into the coding repository.

## Repository Model

```text
enhancement-internal    private demand, approval discussion, wave plan, handoff RFCs
coding repository       source, public issues, public-safe plans, evidence, PRs
```

Feature implementation references either:

- a public coding issue URL for public work; or
- a sanitized handoff requirement URL for confidential enterprise work.

## Required Reading

- `.specify/extensions/ai-team/ai-team-config.yml`;
- `.specify/ai-team/tasks/<task-id>/state.yml` and `context-pack.md` when
  the feature was already routed from a coding workspace;
- private enhancement issue or draft only when the current operator has access;
- handoff RFC conventions under the internal enhancement repository;
- coding repository module index only enough to name likely affected modules.

## Workflow

1. Confirm the request is a new feature, new project, or public behavior, not a
   bug.
2. If the feature is public, prefer a coding repository issue and return to
   `speckit.ai-team.start`.
3. Work in `enhancement-internal` when raw demand, commercial context, or
   unapproved acceptance discussion is needed.
4. Produce a sanitized handoff requirement with:
   - problem or goal;
   - user scenario and value;
   - scope and non-goals;
   - affected coding repository and likely modules;
   - target repository or project creation intent when the work is a new
     project;
   - approval route: maintainer, Technical Committee, release owner, or
     delegated owner;
   - wave plan;
   - acceptance expectations;
   - privacy note describing what was intentionally excluded;
   - whether the coding repository may link the handoff URL or must use a
     public-safe summary.
5. Update or create the Task Context Package with the handoff requirement URL,
   status, approval route, current wave, and next command.
6. Return the handoff URL and hand off to `speckit.ai-team.feature-review` or
   `speckit.specify`.

## Output Shape

```text
Requirement handoff:
- task id:
- context path:
- private source used: no / yes
- handoff requirement URL:
- public-safe summary:
- coding repository may link handoff URL: yes / no / not applicable
- status: draft / accepted / working / rejected / closed / superseded
- approval route:
- current wave:
- affected coding repository:
- new project target:
- likely modules:
- privacy exclusions:
- next command:
```

## Stop Conditions

Stop before coding when:

- confidential enterprise work has no accepted handoff requirement or
  public-safe summary;
- raw customer demand would be copied into the coding repository;
- the handoff requirement has no status or approval route;
- public SPI/API, dependency, license, security, compatibility, or migration
  impact is unresolved.
