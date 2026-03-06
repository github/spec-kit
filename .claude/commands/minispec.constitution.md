---
description: Interactively establish project principles and MiniSpec pairing preferences through guided conversation.
---

## User Input

```text
$ARGUMENTS
```

You are helping establish the project constitution through an **interactive conversation**. This is NOT a form-filling exercise—it's a collaborative discussion to understand the project's values and working preferences.

## Philosophy

MiniSpec constitutions serve two purposes:

1. **Project Principles**: The non-negotiable standards for this codebase
2. **Pairing Preferences**: How you and the AI will collaborate

Both should emerge from dialogue, not templates.

## Execution Flow

### Phase 1: Context Gathering

First, understand the project:

1. **Check for existing constitution** at `.minispec.minispec/memory/constitution.md`
   - If exists: Read it, acknowledge what's established, ask what they want to change
   - If not: Start fresh

2. **Explore the codebase** (if not greenfield):
   - Check for README.md, existing docs, package.json/pyproject.toml
   - Look for existing patterns, conventions, tech stack
   - Note what you observe—this informs your questions

3. **Consider user input**: If `$ARGUMENTS` contains guidance, incorporate it into the conversation

### Phase 2: Conversational Principle Discovery

Guide the engineer through establishing principles. **Ask questions, don't present forms.**

Start with an opening like:
> "Let's establish the principles that will guide development on this project. I'll ask you some questions to understand what matters most. Feel free to be brief—we can always refine later.
>
> First, what's the most important quality you want to maintain in this codebase? (e.g., readability, performance, security, test coverage, simplicity)"

Then explore based on their answers:

**If they mention testing:**
> "How strict should we be about testing? Some teams want TDD, others prefer tests after implementation. What works for you?"

**If they mention code quality:**
> "When you say code quality, what does that look like concretely? Are there specific patterns you want to enforce or avoid?"

**If they mention security:**
> "What's your security posture? Are there compliance requirements (SOC2, HIPAA, PCI) or is it more about general best practices?"

**If they're unsure:**
> "That's fine—we can start simple. Most projects benefit from a few basics: readable code, reasonable test coverage, and documented decisions. Should we start there and add more as we go?"

**Probe for 3-5 principles**, but don't force it. Quality over quantity.

For each principle they mention:

- Clarify what it means concretely
- Ask if it's a MUST (non-negotiable) or SHOULD (preferred)
- Confirm with a summary before moving on

### Phase 3: MiniSpec Preferences

After principles, transition to pairing preferences:

> "Now let's set up how we'll work together. MiniSpec uses a pair programming model where you navigate and I drive. A few preferences will shape our collaboration."

**Chunk Size:**
> "When I implement code, how much do you want to review at once?
>
> - **Small chunks** (20-40 lines): Maximum engagement, great if you're learning this codebase
> - **Medium chunks** (40-80 lines): Balanced pace, good default
> - **Large chunks** (80-150 lines): If you're comfortable with bigger reviews
> - **Adaptive**: I'll suggest based on complexity
>
> What feels right for you?"

**Documentation:**
> "I'll document decisions and patterns as we work. Should I:
>
> - Ask you to review all doc changes
> - Just ask about architectural decisions, handle the rest myself
> - Handle all documentation autonomously (you can always review in git)"

**Autonomy:**
> "When can I proceed without asking for confirmation?
>
> - **Always confirm**: I pause after every chunk
> - **Tests passing**: If tests pass, I continue automatically
> - **Familiar areas**: I proceed in areas you've already reviewed this session
> - **Explicit batch**: Only when you say 'next 3' or similar"

**Design Evolution:**
> "During implementation, I might discover the original design needs adjustment. Should I:
>
> - Always stop and discuss any deviation
> - Flag it and continue if it's minor, stop for major issues
> - Update specs automatically and tell you after (for experienced teams)"

### Phase 4: Synthesis and Writing

Once you have the information:

1. **Summarize back** what you heard before writing:
   > "Here's what I captured:
   >
   > **Principles:**
   > 1. [Principle]: [Brief description]
   > 2. ...
   >
   > **MiniSpec Preferences:**
   > - Chunk size: [choice]
   > - Doc review: [choice]
   > - Autonomy: [choice]
   > - Design evolution: [choice]
   >
   > Does this look right, or should we adjust anything?"

2. **Create directory structure** if needed:

   ```text
   .minispec/
   ├── .minispec/memory/
   │   └── constitution.md
   └── knowledge/
       ├── architecture.md (placeholder)
       ├── conventions.md (placeholder)
       ├── glossary.md (placeholder)
       ├── decisions/ (empty dir)
       ├── patterns/ (empty dir)
       └── modules/ (empty dir)
   ```

3. **Write the constitution** to `.minispec.minispec/memory/constitution.md`:
   - Fill in all placeholders with concrete values
   - Remove HTML comments (they were just guidance)
   - Use clear, declarative language
   - Version: 1.0.0 for new constitutions
   - Dates in ISO format (YYYY-MM-DD)

4. **Create placeholder knowledge files**:
   - `architecture.md`: "# Architecture\n\n*This document will be populated as the codebase develops.*"
   - `conventions.md`: "# Conventions\n\n*Code conventions will be documented here as patterns emerge.*"
   - `glossary.md`: "# Glossary\n\n*Domain terms and definitions will be added during development.*"

### Phase 5: Confirmation

End with a clear summary:

> "Constitution established at `.minispec.minispec/memory/constitution.md`
>
> **Your Principles:**
> [List them]
>
> **Pairing Setup:**
>
> - I'll implement in [chunk size] chunks
> - [Doc review approach]
> - [Autonomy level]
> - [Design evolution handling]
>
> The knowledge base is ready at `.minispec/knowledge/`.
>
> **Next steps:**
>
> - `/minispec.walkthrough` - If you want a tour of the existing codebase
> - `/minispec.design` - To start designing a feature
>
> Ready when you are."

## Important Guidelines

- **Be conversational**: This is a dialogue, not a questionnaire
- **Listen and adapt**: If they want to skip something, let them
- **Don't overwhelm**: Ask one thing at a time
- **Suggest defaults**: For undecided engineers, recommend: medium chunks, trust-ai docs, always-confirm autonomy
- **It's not permanent**: Remind them preferences can be adjusted anytime
- **Probe gently**: If answers are vague, ask one clarifying question, then move on

## If Constitution Already Exists

When updating an existing constitution:

1. Show what's currently established
2. Ask specifically what they want to change
3. Preserve unchanged sections
4. Increment version appropriately:
   - MAJOR: Principle removed or fundamentally changed
   - MINOR: New principle or preference added
   - PATCH: Wording clarification, typo fix

## Output Artifacts

By the end of this command, you will have created/updated:

1. `.minispec.minispec/memory/constitution.md` - The completed constitution
2. `.minispec/knowledge/architecture.md` - Placeholder
3. `.minispec/knowledge/conventions.md` - Placeholder
4. `.minispec/knowledge/glossary.md` - Placeholder
5. `.minispec/knowledge/decisions/` - Empty directory for future ADRs
6. `.minispec/knowledge/patterns/` - Empty directory for patterns
7. `.minispec/knowledge/modules/` - Empty directory for module docs
