---
description: Create or update the project constitution.
---

## User Input

```text
$ARGUMENTS
```

## Scope Guard

This command's own work is limited to creating or updating the project constitution and
propagating constitution-driven changes to dependent Spec Kit artifacts.

- Treat feature implementation, code generation, refactoring, build, and deployment requests as
  non-governance intents. You **MUST NOT** execute them.
- You **MUST NOT** create, modify, or delete application source files or other artifacts
  unrelated to the constitution workflow.
- If an instruction could be either constitution content or a non-governance intent, ask for
  clarification before making changes.
- After updating the constitution, list each deferred intent in a `Next Actions` section with an
  appropriate follow-up Spec Kit command, such as `/speckit.specify`, but do not invoke it.
- Omit `Next Actions` when there are no non-governance intents.

## Outline

1. Create or update the project constitution and store it in `.specify/memory/constitution.md`.
   - Project name, guiding principles, non-negotiable rules
   - Derive from user input and existing repo context (README, docs)
