---
description: Identify underspecified areas in feature spec, ask up to 5 targeted clarification questions, encode answers back into spec.
handoffs: 
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
scripts:
   sh: scripts/bash/check-prerequisites.sh --json --paths-only
   ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

## Input

```text
$ARGUMENTS
```

Consider user input before proceeding (if not empty).

## Workflow

1. Run `{SCRIPT}`, parse FEATURE_DIR and FEATURE_SPEC. Abort if JSON fails.

2. **Scan spec** using taxonomy (mark Clear/Partial/Missing):
   - Functional scope, domain/data model, UX flow, non-functional (perf/scale/security/observability), integrations, edge cases, constraints, terminology, completion signals, placeholders

3. **Generate max 5 questions** (prioritized by Impact*Uncertainty):
   - Must be answerable via multiple-choice (2-5 options) or short answer (<=5 words)
   - Only include if answer materially impacts architecture, testing, UX, or compliance
   - Balance category coverage

4. **Ask one at a time**:
   - Multiple-choice: show **Recommended** option with reasoning + options table. User can pick letter, say "yes"/"recommended", or custom answer
   - Short-answer: show **Suggested** answer. User can accept or provide own
   - Stop when: all resolved, user signals done, or 5 questions asked

5. **Integrate each answer** immediately:
   - Add `## Clarifications` > `### Session YYYY-MM-DD` if missing
   - Append `- Q: <question> → A: <answer>`
   - Update appropriate spec section (requirements, stories, data model, success criteria, edge cases)
   - Replace obsolete statements, save after each integration

6. **Validate**: No duplicates, <=5 questions, no lingering placeholders, consistent terminology.

7. **Report**: Questions asked/answered, path to updated spec, sections touched, coverage summary, next command suggestion.

## Rules

- Never exceed 5 questions | Present one at a time | Never reveal future questions
- If no ambiguities: report "No critical ambiguities" and suggest proceeding
- If spec missing: instruct to run `/speckit.specify` first
- Respect early termination ("done", "stop", "proceed")
