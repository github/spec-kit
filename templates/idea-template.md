# Idea: [CONCISE TITLE]

**Created**: [DATE]
**Status**: Exploration
**Short Name**: [short-name]

## Vision

<!--
  Write a one-paragraph elevator pitch that answers:
  - What is this?
  - Who is it for?
  - Why does it matter?

  Keep it under 3 sentences. This should be understandable by anyone.
-->

[One paragraph elevator pitch]

## Problem Statement

### The Problem

<!--
  Describe the problem clearly. Focus on the pain, not the solution.
  What is broken, missing, or frustrating today?
-->

[Clear description of the problem being solved]

### Current Situation

<!--
  How do users currently deal with this problem?
  - Workarounds they use
  - Competitors or alternatives
  - Manual processes
  - Pain points with current solutions
-->

[How users currently cope - workarounds, pain points, gaps]

### Why Now?

<!--
  What triggers the need for this solution?
  - A specific pain point that became urgent
  - A new opportunity (technology, market, regulation)
  - A mandate (compliance, executive decision)
-->

[What triggers the need for this solution]

## Target Users

### Primary Users

<!--
  Who will use this directly? Be specific about:
  - Role or persona name
  - What they need to accomplish
  - Their technical proficiency
  - Key motivations or frustrations
-->

- **[Persona 1]**: [Role, needs, technical level, key motivations]
- **[Persona 2]**: [Role, needs, technical level, key motivations]

### Secondary Stakeholders

<!--
  Who else is affected but won't use this directly?
  - Managers who need reports
  - IT teams who maintain it
  - Customers of the users
-->

- [Other affected parties and their interests]

## Goals & Success Metrics

### Primary Goals

<!--
  What must this achieve? Each goal should be:
  - Specific and actionable
  - Measurable (even if rough)
  - User or business focused (not technical)
-->

1. [Goal with measurable outcome]
2. [Goal with measurable outcome]

### Success Indicators

<!--
  How will you know this succeeded?
  - Quantitative metrics (time saved, error reduction, adoption rate)
  - Qualitative signals (user feedback, task completion)
  - Business outcomes (revenue, cost reduction, compliance)
-->

- [How you'll know this succeeded - quantitative if possible]
- [User behavior or business metric changes expected]

### MVP Definition

<!--
  What's the minimum viable version that delivers value?
  This should be:
  - Usable end-to-end for the core use case
  - Valuable enough that users would actually use it
  - Small enough to build and validate quickly
-->

[What's the minimum viable version that delivers value?]

## Scope

### In Scope (MVP)

<!--
  What features/capabilities are essential for the first release?
  Be specific and bounded.
-->

- [Feature/capability 1]
- [Feature/capability 2]
- [Feature/capability 3]

### In Scope (Future)

<!--
  What's planned for later phases?
  This helps set expectations and avoid scope creep.
-->

- [Features for later phases]

### Explicitly Out of Scope

<!--
  What will this NOT do? Being explicit prevents misunderstandings.
  Include things that might be assumed but won't be built.
-->

- [What this will NOT do - important boundaries]

## Key Use Cases (Sketches)

<!--
  Sketch 2-4 concrete use cases. These don't need to be formal user stories yet.
  Just describe the flow at a high level to make the idea tangible.
-->

### Use Case 1: [Title]

**Actor**: [Who performs this]
**Goal**: [What they want to achieve]
**Flow**:
1. [Step 1]
2. [Step 2]
3. [Expected outcome]

### Use Case 2: [Title]

**Actor**: [Who]
**Goal**: [What they want]
**Flow**:
1. [Step 1]
2. [Step 2]
3. [Expected outcome]

## Constraints & Assumptions

### Known Constraints

<!--
  What limits or requirements must be respected?
-->

- **Technical**: [Platform, integration, existing system constraints]
- **Business**: [Budget, timeline, team, compliance constraints]
- **User**: [Accessibility, language, device constraints]

### Assumptions

<!--
  What are we assuming to be true without explicit confirmation?
  Document defaults chosen and reasoning.
-->

- [Assumption 1 - things we're assuming to be true]
- [Assumption 2 - defaults we've chosen]

## Features Overview

<!--
  This section is populated when the idea is decomposed into multiple features.
  Leave empty for simple ideas (complexity score < 4).
  The complexity score helps determine if decomposition is needed.
-->

**Complexity Score**: [X]/10 - [Simple|Moderate|Complex|Very Complex]

<!--
  Complexity is calculated from:
  - Multiple user types (> 2)
  - Independent capabilities (> 3)
  - Phased delivery (> 2 phases)
  - Domain boundaries (> 1)
  - Integration points (> 2)
  - Data entities (> 4)
-->

### Feature Breakdown

<!--
  If complexity >= 4, list each feature here.
  Each feature has its own file in the features/ subdirectory.
-->

| # | Feature | Description | Priority | Dependencies | Status |
|---|---------|-------------|----------|--------------|--------|
| 01 | [feature-name] | [One sentence description] | P1/MVP | None | 🔲 Not specified |
| 02 | [feature-name] | [One sentence description] | P1/MVP | 01 | 🔲 Not specified |
| 03 | [feature-name] | [One sentence description] | P2 | 01, 02 | 🔲 Not specified |

**Status Legend**: 🔲 Not specified → 📝 Specified → ✅ Implemented

### Feature Dependencies Graph

<!--
  Visual representation of how features depend on each other.
  Helps determine implementation order.
-->

```
[01-core-feature]
    └── [02-dependent-feature]
         └── [03-another-feature]
[04-independent-feature]
```

### Implementation Order

<!--
  Recommended order for specifying and implementing features.
  Based on dependencies and priority.
-->

1. **Phase 1 (MVP)**: 01, 02, ...
2. **Phase 2**: 03, 04, ...
3. **Phase 3**: ...

## Open Questions & Risks

### Questions to Resolve

<!--
  What needs to be answered before or during specification?
  These will inform /speckit.specify and /speckit.clarify.
-->

- [Question that needs answering]

### Identified Risks

<!--
  What could go wrong? What are the unknowns?
  Include potential mitigations if known.
-->

- [Risk 1]: [Potential mitigation]

## Discovery Notes

<!--
  Record the exploration session(s) that shaped this idea.
  This provides context for future reference.
-->

### Session [DATE]

[Summary of key decisions made during exploration]

- Q: [Question asked] → A: [Answer given]
- Q: [Question asked] → A: [Answer given]
