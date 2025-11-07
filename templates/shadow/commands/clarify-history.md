---
description: Track and review clarification decisions
---

# Clarification History

Track important clarifications and decisions made during development.

## Run Clarification History

```bash
{SHADOW_PATH}/scripts/bash/clarify-history{SCRIPT_EXT}
```

## What This Tracks

- Questions asked during specification
- Answers and decisions made
- Rationale for technical choices
- Alternatives considered
- Trade-offs accepted

## Use Cases

### Before Implementation
Review past decisions to ensure consistency

### During Code Review
Understand context behind implementation choices

### After Release
Document decisions for future reference

### When Onboarding
Help new team members understand "why"

## Format

Each entry includes:
- **Date** - When the decision was made
- **Question** - What was unclear
- **Answer** - What was decided
- **Rationale** - Why this decision
- **Related** - Links to specs, issues, PRs

## Best Practices

- Record decisions as they're made
- Include "why" not just "what"
- Link to relevant discussions
- Update if decisions change
- Review before major changes

## Adding Entries

New clarifications are automatically added when using `/clarify` command or can be manually added to `.memory/clarifications.md`
