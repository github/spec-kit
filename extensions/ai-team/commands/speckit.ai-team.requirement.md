---
description: "Create or refine the private requirement work item and publish the sanitized requirement URL required before feature implementation."
---

# AI Team Requirement Publication

Use this before feature implementation when the user has a feature idea,
private draft, or internal approval discussion but no published requirement URL.

## User Input

```text
$ARGUMENTS
```

## Goal

Move feature intent through the requirements repositories without leaking private
customer demand into the coding repository.

## Repository Model

```text
requirements-internal     private drafts, raw demand, approval discussion
requirements-published    public/read-only RFCs or requirement specs
coding repository         source, public SDD plan/tasks, evidence, PR
```

The coding repository may include `requirements/` as a Git submodule pointing to
`requirements-published`. It must not record or depend on
`requirements-internal`.

Feature implementation references the published requirement URL, not a local
submodule path.

## Required Reading

- `.specify/extensions/ai-team/ai-team-config.yml`;
- private requirement issue or draft only when the current operator has access;
- published requirements conventions under the published repository;
- coding repository module index only enough to name likely affected modules.

## Workflow

1. Confirm the request is a new feature or public behavior, not a bug.
2. Work in `requirements-internal` when raw demand, commercial context, or
   unapproved acceptance discussion is needed.
3. Produce a sanitized published requirement with:
   - problem or goal;
   - user scenario and value;
   - scope and non-goals;
   - affected coding repository and likely modules;
   - approval route: maintainer, technical committee, architecture reviewer,
     release owner, or delegated owner;
   - wave plan;
   - acceptance expectations;
   - privacy note describing what was intentionally excluded.
4. Publish to `requirements-published` and capture the stable URL.
5. Return the URL and hand off to `speckit.ai-team.feature-review` or
   `speckit.specify`.

## Output Shape

```text
Requirement publication:
- private source used: no / yes
- published requirement URL:
- status: draft / accepted / working / rejected / closed / superseded
- approval route:
- current wave:
- affected coding repository:
- likely modules:
- privacy exclusions:
- next command:
```

## Stop Conditions

Stop before coding when:

- no published requirement URL exists;
- raw customer demand would be copied into the coding repository;
- the published requirement has no status or approval route;
- public SPI/API, dependency, license, security, compatibility, or migration
  impact is unresolved.
