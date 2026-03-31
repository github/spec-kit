---
description: Create or update project constitution from interactive or provided principle inputs.
handoffs: 
  - label: Build Specification
    agent: speckit.specify
    prompt: Implement the feature specification based on the updated constitution. I want to build...
---

## Input

```text
$ARGUMENTS
```

Consider user input before proceeding (if not empty).

## Workflow

1. **Load** `.specify/memory/constitution.md`. Identify all `[PLACEHOLDER]` tokens. Respect user's desired principle count.

2. **Collect values**: From user input, repo context, or inference. Version: semver (MAJOR=breaking, MINOR=additions, PATCH=clarifications). LAST_AMENDED_DATE=today if changes made.

3. **Draft**: Replace all placeholders with concrete text. Each principle: name + non-negotiable rules + rationale. Governance: amendment procedure + versioning + compliance expectations.

4. **Propagate**: Check alignment with plan-template.md, spec-template.md, tasks-template.md, commands/*.md. Update references if needed.

5. **Sync Report**: Add HTML comment at top: version change, modified/added/removed sections, templates needing updates.

6. **Validate**: No unexplained brackets, version matches report, dates ISO, principles are declarative+testable (MUST/SHOULD not vague "should").

7. **Write** to `.specify/memory/constitution.md`.

8. **Report**: Version + bump rationale, files needing follow-up, suggested commit message.

## Rules

- Use exact template heading hierarchy
- Single blank line between sections
- If partial updates: still validate and version-decide
- Missing info: insert `TODO(<FIELD>): explanation`
- Always operate on existing file, never create new template
