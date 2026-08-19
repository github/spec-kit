---
description: Create a specification and store it in spec.md.
---

## User Input

```text
$ARGUMENTS
```

## Outline

If `plan.md`, `tasks.md`, or implementation already exist and the user stated a **concrete delta** (add, remove, or reword a named AC, FR, SC, or story), recommend `/speckit.revise` and stop. If only `spec.md` exists, this command may **update** it.

1. **Ask the user** for the feature directory path (e.g., `specs/my-feature`). Do not proceed until provided.

2. Create the directory and write `.specify/feature.json`:
   ```json
   { "feature_directory": "<feature_directory>" }
   ```

3. Create or update the specification from the user input and store it in `<feature_directory>/spec.md`.
   - If that path already has a `spec.md` and `plan.md` or `tasks.md` exist, stop — recommend `/speckit.revise`. Otherwise you may update the existing spec.
   - Overview, functional requirements, user scenarios, success criteria
   - Every requirement must be testable
   - Make informed defaults for unspecified details
