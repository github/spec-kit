---
description: Transform a raw idea into a structured vision document ready for specification. Use this BEFORE /speckit.specify to enrich context and reduce ambiguity.
handoffs:
  - label: Create Specification
    agent: speckit.specify
    prompt: Create a specification from this idea document
    send: true
  - label: Refine Idea Further
    agent: speckit.idea
    prompt: Continue refining the idea with additional context
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

The `/speckit.idea` command transforms a raw, often vague idea into a comprehensive vision document. This document provides the rich context that `/speckit.specify` needs to generate precise, testable specifications.

**Workflow position**: `idea` → `specify` → `clarify` → `plan` → `tasks` → `implement`

## Outline

The text the user typed after `/speckit.idea` is the raw idea. Your goal is to enrich it through structured exploration.

### Phase 1: Idea Exploration (Interactive)

Conduct a focused discovery session with **5-7 questions maximum** across these dimensions:

#### 1.1 Problem & Context Discovery

First, acknowledge the idea and identify what's missing. Then ask questions ONE AT A TIME from these categories:

**Problem Space** (1-2 questions):
- What problem does this solve? Who experiences this problem today?
- What triggers the need for this solution? (pain point, opportunity, mandate)
- How is this problem currently addressed? (workarounds, competitors, manual processes)

**Users & Stakeholders** (1-2 questions):
- Who are the primary users? What are their roles/personas?
- Are there secondary users or stakeholders affected?
- What's the user's technical proficiency level?

**Goals & Success** (1-2 questions):
- What does success look like? How would you measure it?
- What's the MVP vs. the full vision?
- What's the timeline or urgency?

**Constraints & Context** (1-2 questions):
- Are there technical constraints? (platform, integrations, existing systems)
- Are there business constraints? (budget, team size, compliance)
- What's explicitly OUT of scope?

#### 1.2 Question Format

For each question:

1. **Provide context** for why you're asking (1 sentence)
2. **Ask the question** clearly
3. **Offer suggestions** when helpful:

   **Suggested answer**: [Your best guess based on the idea] - [brief reasoning]

   Or for choices:

   | Option | Description |
   |--------|-------------|
   | A | [Option description] |
   | B | [Option description] |
   | C | [Option description] |

   Reply with an option letter, "yes" to accept the suggestion, or your own answer.

4. **Accept short answers**: User can reply briefly; don't require long explanations

#### 1.3 Adaptive Questioning

- **Skip questions** if the initial idea already provides the answer
- **Infer reasonable defaults** for non-critical aspects (document them as assumptions)
- **Stop early** if you have enough context (user says "done", "that's all", etc.)
- **Prioritize** questions that most reduce ambiguity for specification

### Phase 2: Document Generation

After gathering context, generate the idea document:

#### 2.1 Create Feature Directory

Determine a short name (2-4 words) for the idea and create the directory structure:

```bash
# Find next available number
NEXT_NUM=$(ls -d specs/[0-9][0-9][0-9]-* 2>/dev/null | sed 's/.*\/\([0-9]*\)-.*/\1/' | sort -n | tail -1 | awk '{print $1+1}')
NEXT_NUM=${NEXT_NUM:-1}
FEATURE_NUM=$(printf "%03d" $NEXT_NUM)

# Create directory
mkdir -p "specs/${FEATURE_NUM}-<short-name>"
```

#### 2.2 Write Idea Document

Create `specs/###-<short-name>/idea.md` using this structure:

```markdown
# Idea: [CONCISE TITLE]

**Created**: [DATE]
**Status**: Exploration
**Short Name**: [short-name]

## Vision

[One paragraph elevator pitch: What is this? Who is it for? Why does it matter?]

## Problem Statement

### The Problem
[Clear description of the problem being solved]

### Current Situation
[How users currently deal with this - workarounds, pain points, gaps]

### Why Now?
[What triggers the need for this solution - pain point, opportunity, mandate]

## Target Users

### Primary Users
- **[Persona 1]**: [Role, needs, technical level, key motivations]
- **[Persona 2]**: [Role, needs, technical level, key motivations]

### Secondary Stakeholders
- [Other affected parties and their interests]

## Goals & Success Metrics

### Primary Goals
1. [Goal with measurable outcome]
2. [Goal with measurable outcome]

### Success Indicators
- [How you'll know this succeeded - quantitative if possible]
- [User behavior or business metric changes expected]

### MVP Definition
[What's the minimum viable version that delivers value?]

## Scope

### In Scope (MVP)
- [Feature/capability 1]
- [Feature/capability 2]
- [Feature/capability 3]

### In Scope (Future)
- [Features for later phases]

### Explicitly Out of Scope
- [What this will NOT do - important boundaries]

## Key Use Cases (Sketches)

### Use Case 1: [Title]
**Actor**: [Who]
**Goal**: [What they want to achieve]
**Flow**:
1. [Step 1]
2. [Step 2]
3. [Expected outcome]

### Use Case 2: [Title]
[Same structure]

## Constraints & Assumptions

### Known Constraints
- **Technical**: [Platform, integration, existing system constraints]
- **Business**: [Budget, timeline, team, compliance constraints]
- **User**: [Accessibility, language, device constraints]

### Assumptions
- [Assumption 1 - things we're assuming to be true]
- [Assumption 2 - defaults we've chosen]

## Open Questions & Risks

### Questions to Resolve
- [Question that needs answering before or during specification]

### Identified Risks
- [Risk 1]: [Potential mitigation]

## Discovery Notes

### Session [DATE]
[Summary of key decisions made during exploration]
- Q: [Question asked] → A: [Answer given]
- Q: [Question asked] → A: [Answer given]
```

#### 2.3 Validation Checklist

Before completing, verify:

- [ ] Vision is clear and compelling (could explain to a stranger)
- [ ] Problem is well-defined (not solution-first thinking)
- [ ] Target users are identified with their needs
- [ ] At least 2-3 concrete use cases sketched
- [ ] MVP scope is defined and bounded
- [ ] Out-of-scope items are explicit
- [ ] Known constraints documented
- [ ] Success metrics are measurable

### Phase 3: Completion

1. **Save** the idea document to `specs/###-<short-name>/idea.md`

2. **Report** completion:
   ```
   Idea document created: specs/###-<short-name>/idea.md

   Summary:
   - Vision: [1-line summary]
   - Primary users: [list]
   - MVP scope: [key items]
   - Open questions: [count]

   Next step: /speckit.specify to create formal specification
   ```

3. **Handoff options**:
   - Proceed to `/speckit.specify` to create formal spec from this idea
   - Continue `/speckit.idea` to explore further
   - Review and manually edit the idea document

## Guidelines

### Do's
- **Be conversational**: This is exploration, not interrogation
- **Make suggestions**: Offer your best guesses - user can accept or override
- **Infer sensible defaults**: Don't ask about everything; assume industry standards
- **Focus on the "what" and "why"**: Not the "how" (that comes in planning)
- **Keep it concise**: The idea doc should be 1-3 pages, not a novel

### Don'ts
- **Don't ask too many questions**: 5-7 max, stop if you have enough
- **Don't require perfect answers**: Rough is fine, can refine later
- **Don't include implementation details**: No tech stack, architecture, code
- **Don't create the spec**: That's `/speckit.specify`'s job
- **Don't skip the MVP definition**: This is critical for scope control

### Question Priority

If limited to few questions, prioritize in this order:
1. **Problem/need validation** - Is this solving a real problem?
2. **Primary user identification** - Who is this for?
3. **Success definition** - How do we know it worked?
4. **Scope boundaries** - What's explicitly out?
5. **Constraints** - What limits do we have?

### Handling Vague Ideas

If the initial idea is very vague (e.g., "an app for photos"):

1. Start with the problem: "What frustrates you about managing photos today?"
2. Identify the user: "Is this for personal use, a team, or public?"
3. Find the hook: "What's the one thing this MUST do well?"
4. Build from there

### Handling Detailed Ideas

If the user provides lots of detail:

1. Summarize what you understood
2. Ask only for missing critical pieces
3. Confirm assumptions explicitly
4. Move quickly to document generation
