---
description: Update project tagging requirements using the tagging-constraint-template.md.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

You are updating the project tagging requirements at `.infrakit/tagging.md` (or the location corresponding to the tagging strategy of the project). This document defines the exact tagging schema, required tags, optional tags, and tagging conventions for all managed infrastructure resources.

**Note**: Use the `.infrakit/templates/tagging-constraint-template.md` as the foundation for the requirements.

Follow this execution flow:

1. Load the existing tagging constraints file or initialize it from `.infrakit/templates/tagging-constraint-template.md`.
2. Apply any updates or user input specifying exact key-value pairs, mandatory/optional rules, or naming formats for tags.
3. Clearly define the enforcement mechanisms, acceptable values, and rationale for each required tag.
4. Replace any template placeholders with concrete tagging requirements for the specific environments and resources.
5. Produce a summary of the new tagging constraints.
6. Write the completed file back to `.infrakit/tagging.md` (overwrite).
7. Output a final summary to the user highlighting the updated tagging schema and validation rules.
