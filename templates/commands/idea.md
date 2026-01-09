---
description: Transform a raw idea into a structured vision document and decompose complex ideas into manageable features. Use this BEFORE /speckit.specify to enrich context and reduce ambiguity.
handoffs:
  - label: Specify Next Feature
    agent: speckit.specify
    prompt: Create a specification for the next unspecified feature
    send: true
  - label: Refine Idea Further
    agent: speckit.idea
    prompt: Continue refining the idea with additional context
  - label: Add More Features
    agent: speckit.idea
    prompt: Decompose additional features from the idea
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

The `/speckit.idea` command transforms a raw, often vague idea into a comprehensive vision document AND decomposes complex ideas into smaller, manageable features. This provides the rich context that `/speckit.specify` needs to generate precise specifications incrementally.

**Workflow position**: `idea` → `specify` (per feature) → `clarify` → `plan` → `tasks` → `implement`

**Key principle**: Complex ideas should NOT be specified as a single monolithic feature. Instead, break them into focused features that can be specified, planned, and implemented independently.

## Outline

The text the user typed after `/speckit.idea` is the raw idea. Your goal is to:
1. Enrich it through structured exploration
2. Assess complexity and identify natural boundaries
3. Decompose into features if complexity warrants it

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

### Phase 2: Complexity Analysis

After gathering context, assess whether the idea needs decomposition:

#### 2.1 Complexity Indicators

Check for these complexity signals:

| Signal | Description | Threshold |
|--------|-------------|-----------|
| **Multiple user types** | Different personas with distinct workflows | > 2 primary users |
| **Independent capabilities** | Features that could work alone | > 3 distinct capabilities |
| **Phased delivery** | Natural MVP → v2 → v3 progression | > 2 phases mentioned |
| **Domain boundaries** | Different technical/business domains | > 1 domain |
| **Integration points** | External systems or APIs | > 2 integrations |
| **Data entities** | Distinct data models with relationships | > 4 entities |

#### 2.2 Complexity Score

Calculate a complexity score (0-10):

```
Score = (user_types × 1) + (capabilities × 1.5) + (phases × 1) +
        (domains × 2) + (integrations × 1) + (entities × 0.5)
```

| Score | Complexity | Action |
|-------|------------|--------|
| 0-3 | Simple | Single `idea.md`, no decomposition |
| 4-6 | Moderate | `idea.md` + 2-3 feature files |
| 7-10 | Complex | `idea.md` + 4-6 feature files |
| 10+ | Very Complex | `idea.md` + features + suggest phased approach |

#### 2.3 Identify Feature Boundaries

If complexity score ≥ 4, identify natural feature boundaries:

1. **By User Journey**: Group capabilities by user workflow stages
   - Example: "Onboarding", "Core Usage", "Administration"

2. **By Domain**: Separate business domains
   - Example: "Authentication", "Payments", "Notifications"

3. **By Priority**: Separate MVP from future phases
   - Example: "Core Features (MVP)", "Advanced Features", "Nice-to-haves"

4. **By Independence**: Features that can be built/deployed independently
   - Example: "User Management", "Reporting", "Integrations"

**Feature Naming**: Each feature should have:
- A clear, action-oriented name (2-4 words)
- A one-sentence description
- Identified dependencies on other features

### Phase 3: Document Generation

After gathering context and analyzing complexity, generate the documents:

#### 3.1 Create Idea Directory

Determine a short name (2-4 words) for the idea and create the directory structure:

```bash
# Find next available idea number
NEXT_NUM=$(ls -d ideas/[0-9][0-9][0-9]-* 2>/dev/null | sed 's/.*\/\([0-9]*\)-.*/\1/' | sort -n | tail -1 | awk '{print $1+1}')
NEXT_NUM=${NEXT_NUM:-1}
IDEA_NUM=$(printf "%03d" $NEXT_NUM)

# Create idea directory with features subdirectory
mkdir -p "ideas/${IDEA_NUM}-<short-name>/features"
```

**Directory structure**:

```
ideas/###-<short-name>/
├── idea.md                    # High-level vision (always created)
└── features/                  # Feature files (if complexity ≥ 4)
    ├── 01-<feature-name>.md   # First feature
    ├── 02-<feature-name>.md   # Second feature
    └── ...

.speckit/                              # Created later by /speckit.specify
├── ###-<short-name>/                  # Spec for simple idea (complexity < 4)
│   ├── spec.md
│   ├── plan.md
│   └── ...
└── ###-01-<feature-name>/             # Spec for feature 1 (complexity ≥ 4)
    ├── spec.md
    ├── plan.md
    └── ...
```

**Note**: The `/speckit.specify` command will create the `.speckit/###-<name>/` directory structure when you specify the idea or each feature.

#### 3.2 Write Idea Document

Create `ideas/###-<short-name>/idea.md` using this structure:

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

## Features Overview

<!--
  This section is populated when complexity analysis identifies multiple features.
  Leave empty for simple ideas (complexity score < 4).
-->

**Complexity Score**: [X]/10 - [Simple|Moderate|Complex|Very Complex]

### Feature Breakdown

| # | Feature | Description | Priority | Dependencies | Status |
|---|---------|-------------|----------|--------------|--------|
| 01 | [feature-name] | [One sentence description] | P1/MVP | None | 🔲 Not specified |
| 02 | [feature-name] | [One sentence description] | P1/MVP | 01 | 🔲 Not specified |
| 03 | [feature-name] | [One sentence description] | P2 | 01, 02 | 🔲 Not specified |

**Status Legend**: 🔲 Not specified → 📝 Specified → ✅ Implemented

### Feature Dependencies Graph

```
[01-core-feature]
    └── [02-dependent-feature]
         └── [03-another-feature]
[04-independent-feature]
```

### Implementation Order

Recommended order based on dependencies and priority:
1. **Phase 1 (MVP)**: 01, 02, ...
2. **Phase 2**: 03, 04, ...
3. **Phase 3**: ...

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

## Technical Hints

<!--
  IMPORTANT: Capture technical requirements that MUST be preserved
  throughout specification, planning, and implementation.
  This section is critical for downstream alignment.
-->

### Required Commands/Scripts

| Order | Command/Script | Purpose |
|-------|----------------|---------|
| 1 | [command] | [what it does] |

### Required Tools & Versions

- **[Tool/Library]**: [version] - [why required]

### Integration Sequences

[Describe integration patterns or protocols if applicable]

### Implementation Notes

- [Technical note that must be preserved]
```

#### 3.3 Generate Feature Files (if complexity ≥ 4)

For each identified feature, create a feature file in `ideas/###-<short-name>/features/`:

**File naming**: `##-feature-short-name.md` (e.g., `01-user-authentication.md`)

Use the feature template structure:

```markdown
# Feature: [FEATURE TITLE]

**Parent Idea**: [Link to idea.md]
**Feature ID**: ##
**Priority**: P1/P2/P3
**Status**: Not Specified

## Summary

[2-3 sentences describing this specific feature and its value]

## User Value

**Who benefits**: [Specific user persona from idea.md]
**What they gain**: [Concrete benefit]
**Success metric**: [How to measure this feature's success]

## Scope

### This Feature Includes
- [Capability 1]
- [Capability 2]
- [Capability 3]

### This Feature Does NOT Include
- [Explicitly excluded - may be in another feature]
- [Explicitly excluded - out of scope entirely]

## Key Use Cases

### Use Case 1: [Title]
**Actor**: [Who]
**Goal**: [What they want]
**Flow**:
1. [Step]
2. [Step]
3. [Expected outcome]

## Dependencies

### Requires
- [Feature ##]: [What this feature needs from it]

### Enables
- [Feature ##]: [What this feature provides to it]

## Technical Hints

<!--
  CRITICAL: Capture technical requirements that MUST be preserved.
  These will be validated during planning and traced to tasks.
-->

### Required Commands/Scripts

| Order | Command/Script | Purpose |
|-------|----------------|---------|
| 1 | [command] | [what it does] |

### Required Tools & Versions

- **[Tool/Library]**: [version] - [why required]

### Implementation Notes

- [Technical constraint]

## Open Questions

- [Questions specific to this feature]

## Notes

[Any additional context for specification]
```

#### 3.5 Validation Checklist

Before completing, verify:

**For idea.md**:
- [ ] Vision is clear and compelling (could explain to a stranger)
- [ ] Problem is well-defined (not solution-first thinking)
- [ ] Target users are identified with their needs
- [ ] At least 2-3 concrete use cases sketched
- [ ] MVP scope is defined and bounded
- [ ] Out-of-scope items are explicit
- [ ] Known constraints documented
- [ ] Success metrics are measurable
- [ ] Complexity score calculated

**For feature files (if complexity ≥ 4)**:
- [ ] Each feature has a clear, focused scope
- [ ] Dependencies between features are documented
- [ ] No overlap between feature scopes
- [ ] Implementation order is logical (dependencies respected)
- [ ] Each feature could be specified independently

### Phase 4: Completion

1. **Save** all documents:
   - `ideas/###-<short-name>/idea.md` (always)
   - `ideas/###-<short-name>/features/*.md` (if complexity ≥ 4)

2. **Report** completion:

   **For simple ideas (complexity < 4)**:
   ```
   ## Idea Document Created

   📄 **File**: ideas/###-<short-name>/idea.md

   ### Summary
   - **Vision**: [1-line summary]
   - **Primary users**: [list]
   - **MVP scope**: [key items]
   - **Complexity**: Simple ([X]/10)
   - **Open questions**: [count]

   ### Next Step
   → `/speckit.specify ideas/###-<short-name>` to create formal specification
   ```

   **For complex ideas (complexity ≥ 4)**:
   ```
   ## Idea Document & Features Created

   📄 **Idea**: ideas/###-<short-name>/idea.md
   📁 **Features**: ideas/###-<short-name>/features/

   ### Summary
   - **Vision**: [1-line summary]
   - **Complexity**: [Moderate|Complex|Very Complex] ([X]/10)

   ### Features Identified

   | # | Feature | Priority | Status |
   |---|---------|----------|--------|
   | 01 | [name] | P1/MVP | 🔲 Ready to specify |
   | 02 | [name] | P1/MVP | 🔲 Ready to specify |
   | 03 | [name] | P2 | 🔲 Ready to specify |

   ### Recommended Implementation Order
   1. **Start with**: Feature 01 - [name]
   2. **Then**: Feature 02 - [name] (depends on 01)
   3. **Later**: Feature 03 - [name]

   ### Next Step
   → `/speckit.specify ideas/###-<short-name>/features/01-feature-name.md` to specify first feature
   → Or `/speckit.specify ideas/###-<short-name>` to specify entire idea as one spec
   ```

3. **Handoff options**:
   - **Specify next feature**: `/speckit.specify` with feature number or path
   - **Refine idea further**: `/speckit.idea` to add more features or details
   - **Review manually**: Edit the idea or feature documents directly

## Guidelines

### Do's
- **Be conversational**: This is exploration, not interrogation
- **Make suggestions**: Offer your best guesses - user can accept or override
- **Infer sensible defaults**: Don't ask about everything; assume industry standards
- **Focus on the "what" and "why"**: Not the "how" (that comes in planning)
- **Keep it concise**: The idea doc should be 1-3 pages, not a novel
- **Decompose complexity**: Break large ideas into focused, independent features
- **Identify dependencies**: Map which features need others to work

### Don'ts
- **Don't ask too many questions**: 5-7 max, stop if you have enough
- **Don't require perfect answers**: Rough is fine, can refine later
- **Don't include implementation details**: No tech stack, architecture, code
- **Don't create the spec**: That's `/speckit.specify`'s job
- **Don't skip the MVP definition**: This is critical for scope control
- **Don't create monolithic features**: If scope is large, decompose it
- **Don't force decomposition**: Simple ideas don't need feature files

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

### Handling Complex Ideas

When an idea has high complexity score (≥ 4):

1. **Explain the decomposition**: "This idea has several distinct parts. Let me break it down into focused features."

2. **Present the feature breakdown**: Show the proposed features in a table and ask for confirmation:
   ```
   Based on your idea, I've identified these features:

   | Feature | Description | Priority |
   |---------|-------------|----------|
   | 01-user-auth | User registration and login | P1 |
   | 02-dashboard | Main user interface | P1 |
   | 03-reporting | Generate and export reports | P2 |

   Does this breakdown make sense? Should I adjust any features?
   ```

3. **Confirm dependencies**: "Feature 02 needs Feature 01 to be done first. Is that correct?"

4. **Suggest phasing**: For very complex ideas, recommend MVP vs. later phases

5. **Generate incrementally**: Create idea.md first, then each feature file

### Feature Decomposition Strategies

Use these strategies to identify feature boundaries:

| Strategy | When to Use | Example |
|----------|-------------|---------|
| **By User Flow** | Sequential workflows | Onboarding → Core → Admin |
| **By Domain** | Distinct business areas | Auth, Payments, Inventory |
| **By Priority** | Clear MVP vs. extras | Must-have vs. Nice-to-have |
| **By Independence** | Can deploy separately | API, UI, Notifications |
| **By User Type** | Different personas | Customer, Admin, Support |

### Examples

**Simple idea** (no decomposition):
> "Add a dark mode toggle to the settings page"

Complexity: ~2 (single capability, one user type, no integrations)
→ Create idea.md only

**Moderate idea** (2-3 features):
> "Build a contact form with email notifications and admin dashboard"

Complexity: ~5 (3 capabilities, 2 user types, 1 integration)
→ Features: `01-contact-form`, `02-email-notifications`, `03-admin-dashboard`

**Complex idea** (4+ features):
> "Create an e-commerce platform with product catalog, shopping cart, checkout, user accounts, order management, and analytics"

Complexity: ~9 (6 capabilities, 2 user types, multiple integrations)
→ Features: `01-user-accounts`, `02-product-catalog`, `03-shopping-cart`, `04-checkout`, `05-order-management`, `06-analytics`
→ Recommend phased approach: MVP (01-04), Phase 2 (05-06)
