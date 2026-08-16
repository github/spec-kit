---
description: Create a specification and store it in spec.md.
---

## User Input

```text
$ARGUMENTS
```

## Outline

If `.specify/feature.json` or the named directory already has a `spec.md` and the user stated a **concrete delta** (add, remove, or reword a named AC, FR, story, or success criterion), do **not** write anything. Recommend `/speckit.revise` and stop. Never overwrite an existing `spec.md`.

1. **Ask the user** for the feature directory path (e.g., `specs/my-feature`). Do not proceed until provided.

2. Create the directory and write `.specify/feature.json`:
   ```json
   { "feature_directory": "<feature_directory>" }
   ```

3. Create a specification from the user input and store it in `<feature_directory>/spec.md`.
   - If that path already has a `spec.md`, stop — do not overwrite it
   - Overview, functional requirements, user scenarios, success criteria
   - Every requirement must be testable
   - Make informed defaults for unspecified details
