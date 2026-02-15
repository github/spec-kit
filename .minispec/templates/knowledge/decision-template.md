---
type: decision
id: [DECISION_ID]
date: [YYYY-MM-DD]
status: [proposed | accepted | deprecated | superseded]
supersedes: [null | decision-id]
superseded_by: [null | decision-id]
impacts:
  - [file/path/or/pattern/*]
tags: [tag1, tag2]
participants: [who was involved in this decision]
---

# [Decision Title]

## Context

[What is the issue that we're seeing that is motivating this decision or change?]
[What constraints do we have? What forces are at play?]

## Options Considered

### Option 1: [Name]
[Description]
- ✅ [Pro]
- ✅ [Pro]
- ❌ [Con]

### Option 2: [Name]
[Description]
- ✅ [Pro]
- ❌ [Con]
- ❌ [Con]

### Option 3: [Name] (if applicable)
[Description]

## Decision

We chose **[Option Name]** because [primary reasoning].

[Elaborate on why this option best fits the constraints and context.]

## Consequences

### Positive
- ✅ [Benefit 1]
- ✅ [Benefit 2]

### Negative
- ⚠️ [Trade-off or risk 1]
- ⚠️ [Trade-off or risk 2]

### Neutral
- [Side effect that's neither good nor bad]

## Code References

- [Description]: `path/to/file.ts:functionName()`
- [Description]: `path/to/another/file.ts`

## Related Decisions

- [Link to related decision if applicable]

## Notes

[Any additional context, links to discussions, or follow-up items]
