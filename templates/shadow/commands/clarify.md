---
description: Ask structured clarifying questions about requirements
---

# Clarify Requirements

Ask structured clarifying questions to de-risk ambiguous areas before planning.

## When to Use

- Requirements are vague or incomplete
- Multiple interpretations possible
- Assumptions need validation
- Edge cases are unclear
- Performance requirements undefined

## Process

1. **Identify ambiguities** - What's unclear in the specification?
2. **Formulate questions** - Create specific, actionable questions
3. **Categorize** - Group related questions
4. **Prioritize** - Focus on high-impact clarifications
5. **Document answers** - Record decisions in clarification history

## Question Categories

### Functional Behavior
- What should happen in scenario X?
- How should the system handle edge case Y?
- What's the expected outcome for input Z?

### Non-Functional Requirements
- What performance targets must be met?
- What are the scalability requirements?
- What security constraints apply?

### Integration & Dependencies
- How does this integrate with system X?
- What's the contract with service Y?
- What happens if dependency Z fails?

### User Experience
- What's the expected user workflow?
- How should errors be presented?
- What feedback should users receive?

## Output

Questions are saved to:
```
.clarifications/<feature-name>-questions.md
```

Answers are added to:
```
.memory/clarifications.md
```

## Best Practices

- Ask before implementing, not after
- Be specific and concrete
- Focus on high-impact unknowns
- Include examples in questions
- Validate assumptions explicitly

## Run Before

Run this command **before** `/plan` to ensure the specification is complete.
