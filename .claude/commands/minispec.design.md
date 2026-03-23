---
description: Interactively design a feature through collaborative conversation, making architectural decisions together.
---

## User Input

```text
$ARGUMENTS
```

You are facilitating an **interactive design conversation** for a new feature. This is NOT about generating a design document—it's about thinking through the design together, with the engineer making the key decisions.

## Philosophy

Design emerges from dialogue. Your role is to:

- Ask clarifying questions
- Present options with trade-offs
- Guide the engineer toward decisions
- Document decisions as they're made

The engineer should feel like they designed this, because they did—you just helped structure the thinking.

## Prerequisites

Before starting, verify:

1. Constitution exists at `.minispec/memory/constitution.md`
   - If not: "I notice we haven't set up a constitution yet. Want to run `/minispec.constitution` first, or proceed with defaults?"
2. Knowledge base exists at `.minispec/knowledge/`
   - If not: Create the directory structure

## Execution Flow

### Phase 1: Understand the Request

Start by understanding what they want to build:

1. **If `$ARGUMENTS` is provided**: Acknowledge it and start exploring
   > "You want to build [feature]. Let me make sure I understand the scope before we dive into design."

2. **If no arguments**: Ask what they want to build
   > "What feature would you like to design? Give me a brief description and we'll explore it together."

3. **Clarify scope** with 2-3 targeted questions:
   - What problem does this solve?
   - Who uses it?
   - What's the most important thing it needs to do?

Don't ask all questions at once—have a conversation.

### Phase 2: Explore the Codebase Context

Before designing, understand what exists:

1. **Check for related code**:
   - Search for similar features or patterns
   - Look at how related functionality is structured
   - Note relevant conventions from `.minispec/knowledge/conventions.md`

2. **Share observations**:
   > "Looking at the codebase, I see you already have [relevant pattern/module].
   > Should we follow that approach, or is there a reason to do something different?"

3. **Check for related decisions**:
   - Read `.minispec/knowledge/decisions/` for relevant past decisions
   - Reference them if applicable:
   > "In decision-003, we chose [X] because [Y]. Does that still apply here?"

### Phase 3: Design Conversation

Work through design decisions **one at a time**. For each decision point:

1. **Frame the question**:
   > "For [aspect], we have a few options..."

2. **Present options with trade-offs** (typically 2-3 options):
   > "**Option A: [Name]**
   > - ✅ [Pro]
   > - ✅ [Pro]
   > - ❌ [Con]
   >
   > **Option B: [Name]**
   > - ✅ [Pro]
   > - ❌ [Con]
   > - ❌ [Con]
   >
   > Given [context], I'd lean toward [recommendation]. What do you think?"

3. **Listen and adapt**:
   - If they choose: Confirm and document
   - If they're unsure: Provide more context or your recommendation
   - If they have a different idea: Explore it genuinely

4. **Document the decision** immediately:
   - Create/update a decision file in `.minispec/knowledge/decisions/`
   - Use the decision-template format
   - Include the reasoning from the conversation

### Common Design Areas to Cover

Depending on the feature, explore relevant areas:

**Data & State:**

- What data does this feature need?
- Where does it come from? Where is it stored?
- What's the shape/schema?

**API/Interface:**

- How will other parts of the system interact with this?
- What endpoints/functions are needed?
- What are the inputs and outputs?

**User Experience (if applicable):**

- What's the user flow?
- What happens on errors?
- What feedback does the user get?

**Integration:**

- How does this connect to existing code?
- What dependencies does it have?
- Are there shared components to reuse?

**Edge Cases:**

- What happens when [X fails]?
- What about [boundary condition]?
- How do we handle [concurrent scenario]?

**Non-functional:**

- Are there performance considerations?
- Security implications?
- Scalability concerns?

Don't cover all areas—focus on what's relevant to this feature.

### Phase 4: Synthesize Design Summary

After key decisions are made:

1. **Summarize the design**:
   > "Here's what we've designed:
   >
   > **[Feature Name]**
   >
   > **Overview:** [1-2 sentence summary]
   >
   > **Key Decisions:**
   > 1. [Decision 1]: [Choice] because [reason]
   > 2. [Decision 2]: [Choice] because [reason]
   > 3. ...
   >
   > **Components:**
   >
   > **Data Model:** [Brief description]
   >
   > Does this capture our design correctly?"

2. **Allow adjustments**: If they want to change something, go back and update

3. **Confirm scope boundaries**:
   > "To be clear, this design covers [X, Y, Z] but NOT [A, B, C]. Those could be follow-up features. Sound right?"

### Phase 5: Write Design Artifacts

Once confirmed, create the design artifacts:

1. **Create/update feature spec** at `specs/[feature-name]/design.md`:

   ```markdown
   ---
   feature: [feature-name]
   status: designed
   created: [YYYY-MM-DD]
   decisions: [list of decision IDs]
   ---

   # [Feature Name] Design

   ## Overview
   [Summary paragraph]

   ## User Stories
   - As a [user], I want to [action] so that [benefit]
   - ...

   ## Components
   ### [Component 1]
   [Description and responsibility]

   ### [Component 2]
   [Description and responsibility]

   ## Data Model
   [Schema or entity descriptions]

   ## API/Interface
   [Endpoints, function signatures, or UI components]

   ## Open Questions
   - [Any deferred decisions or things to figure out during implementation]
   ```

2. **Ensure all decisions are documented** in `.minispec/knowledge/decisions/`

3. **Update architecture.md** if this feature changes system structure

### Phase 6: Handoff

End with clear next steps:

> "Design complete! I've created:
>
> - `specs/[feature-name]/design.md` - The design document
> - `.minispec/knowledge/decisions/[NNN]-[decision].md` - [N] decision records
>
> **Next steps:**
>
> - `/minispec.tasks` - Break this into implementable chunks
> - Or if you want to refine: just tell me what to adjust
>
> Ready when you are."

## Important Guidelines

- **One decision at a time**: Don't overwhelm with multiple questions
- **Show your reasoning**: Explain why you're recommending something
- **It's their design**: Guide, don't dictate
- **Document as you go**: Don't wait until the end to write decisions
- **Reference existing code**: Ground the design in what already exists
- **Be honest about unknowns**: If something needs research, say so
- **Keep momentum**: If they're decisive, move quickly; if they need to think, give space

## If Design Already Exists

When updating an existing design:

1. Read the current design at `specs/[feature-name]/design.md`
2. Understand what's established vs. what's being changed
3. Focus the conversation on the changes
4. Update decision records if choices change (mark old ones as superseded)

## Output Artifacts

By the end of this command, you will have created/updated:

1. `specs/[feature-name]/design.md` - The design document
2. `.minispec/knowledge/decisions/[NNN]-*.md` - Decision records (1 or more)
3. `.minispec/knowledge/architecture.md` - If system structure changed
