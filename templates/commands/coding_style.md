---
description: Specify and update the project coding style standards using the coding-style-template.md.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

You are updating the project coding style at `.infrakit/coding-style.md`. This file is responsible for establishing the standardized conventions, naming rules, and formatting guidelines for code and configuration across the project. 

**Note**: If `.infrakit/coding-style.md` does not exist yet, you should initialize it using `.infrakit/templates/coding-style-template.md`.

Follow this execution flow:

1. Load the existing coding style at `.infrakit/coding-style.md`. If it does not exist, load the template from `.infrakit/templates/coding-style-template.md`.
2. Based on the user input and the current project context, derive concrete rules, styling expectations, and naming conventions to fill in any gaps or placeholders.
3. Replace any bracketed tokens or template instructions with concrete guidelines that fit the chosen technologies.
4. Maintain a clear and prioritized structure (e.g., General Principles, Language-Specific Guidelines, File Naming, etc.).
5. Produce a summary of changes applied to the coding style guidelines.
6. Write the completed file back to `.infrakit/coding-style.md` (overwrite).
7. Output a final summary to the user outlining the new or updated coding style rules.
