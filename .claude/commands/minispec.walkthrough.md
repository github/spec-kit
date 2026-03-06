---
description: Guided tour of the codebase to build mental models before implementation.
---

## User Input

```text
$ARGUMENTS
```

You are giving a **guided tour** of the codebase to help the engineer build mental models. This is especially valuable when:

- Starting work on an unfamiliar codebase
- Onboarding to a project
- Before implementing a feature that touches many areas
- After being away from the codebase for a while

## Philosophy

The goal is **understanding**, not documentation. The engineer should finish this walkthrough with:

- A mental map of how the codebase is organized
- Understanding of key patterns and conventions
- Knowledge of where to find things
- Confidence to navigate and modify the code

This is a conversation, not a lecture.

## Prerequisites

Check what context exists:

1. **Knowledge base** at `.minispec/knowledge/`
   - `architecture.md` - System overview
   - `conventions.md` - Code patterns
   - `patterns/` - Documented patterns
   - `modules/` - Module documentation

2. **Constitution** at `.minispec.minispec/memory/constitution.md`
   - Check `Walkthrough Depth` preference (quick/standard/deep)

3. **Codebase** - The actual source code

If knowledge base is sparse, that's okay—build understanding from the code itself.

## Walkthrough Depths

Based on constitution preference:

| Depth | Duration | Coverage |
| --- | --- | --- |
| Quick | 5-10 min | Architecture overview, key entry points |
| Standard | 15-20 min | Architecture + patterns + conventions |
| Deep | 30+ min | Full tour with all modules explained |

If no preference set, ask:
> "How deep would you like to go?
>
> - **Quick** (5-10 min): High-level architecture, where to start
> - **Standard** (15-20 min): Architecture plus key patterns and conventions
> - **Deep** (30+ min): Comprehensive tour of all major modules
>
> You can also ask for a focused walkthrough: 'just the auth system' or 'how data flows from API to database'"

## Execution Flow

### Phase 1: Assess the Codebase

Before starting, quickly explore:

1. **Project structure**: What's in the root? How are files organized?
2. **Entry points**: Where does execution start?
3. **Package/dependency info**: What frameworks and libraries are used?
4. **Existing documentation**: README, docs/, inline comments
5. **Knowledge base**: What's already documented in `.minispec/knowledge/`

### Phase 2: Start with the Big Picture

Begin with architecture overview:

> "Let me give you the big picture of this codebase.
>
> **Project:** [Name] - [one sentence description]
>
> **Tech Stack:**
>
> - [Language/Framework]
> - [Database]
> - [Key libraries]
>
> **Structure:**
>
> ```text
> [directory tree of key folders]
> ```
>
> **How it works (high level):**
> [2-3 sentences on the main flow]
>
> Questions so far, or shall I go deeper?"

### Phase 3: Explain Key Concepts

Based on the codebase, explain the core concepts:

**For a web app:**
> "The app follows [pattern] architecture:
>
> 1. **[Layer 1]**: [What it does, where it lives]
> 2. **[Layer 2]**: [What it does, where it lives]
> 3. **[Layer 3]**: [What it does, where it lives]
>
> Data flows like this:
> [Request] → [Component A] → [Component B] → [Response]"

**For a library:**
> "This library exposes:
>
> - **Main API**: `[function/class]` - [what it does]
> - **Configuration**: [how to configure]
> - **Extension points**: [how to extend]"

### Phase 4: Patterns and Conventions

Explain how things are done in this codebase:

> "Here are the patterns you'll see throughout:
>
> **[Pattern 1 Name]:**
> When [situation], we [approach].
> Example: `path/to/example.ts`
>
> **[Pattern 2 Name]:**
> [Explanation]
>
> **Naming conventions:**
>
> - Files: [convention]
> - Functions: [convention]
> - Components: [convention]
>
> **Code organization:**
>
> - [Convention about file placement]
> - [Convention about imports]"

### Phase 5: Module Deep Dives (for Standard/Deep)

For each major module:

> "**[Module Name]** (`path/to/module/`)
>
> **Purpose:** [What problem it solves]
>
> **Key files:**
>
> - `file.ts` - [What it does]
> - `another.ts` - [What it does]
>
> **How it connects:**
>
> - Used by: [What depends on it]
> - Depends on: [What it needs]
>
> **Pattern to note:**
> [Any specific pattern used here]
>
> Want to dive into the code, or move to the next module?"

### Phase 6: Focused Exploration

If engineer asks about something specific:

> "Let me show you how [specific thing] works.
>
> [Walk through the relevant code paths, explaining as you go]
>
> The key insight is: [main takeaway]"

If engineer wants to see code:

- Show relevant snippets
- Explain what each part does
- Point out non-obvious things
- Reference patterns or decisions

### Phase 7: Interactive Q&A

Throughout, encourage questions:

> "What would you like to explore next?
>
> Some options:
>
> - How [specific flow] works
> - The testing setup
> - How to add a new [component type]
> - Where [specific functionality] lives"

### Phase 8: Wrap Up

End with actionable summary:

> "**Walkthrough complete.** Here's your quick reference:
>
> **To add a new [feature type]:**
>
> 1. Create [file] in [location]
> 2. Follow the [pattern] pattern
> 3. Register in [location]
>
> **Key files to know:**
>
> - `path/to/main.ts` - Entry point
> - `path/to/config.ts` - Configuration
> - `path/to/routes.ts` - API routes
>
> **When you're stuck:**
>
> - Check `patterns/` for examples
> - Look at similar features in [location]
>
> **Next steps:**
>
> - `/minispec.design` to start designing your feature
> - Ask me anything about the codebase anytime
>
> What questions do you have?"

## Handling Different Scenarios

### Greenfield Project

If codebase is mostly empty:

> "This is a fresh project. Not much to walk through yet!
>
> **Current state:**
>
> - [What exists so far]
>
> **Conventions established:**
>
> - [Any from constitution]
>
> As we build, I'll document patterns in `.minispec/knowledge/`.
>
> Ready to `/minispec.design` your first feature?"

### Large/Complex Codebase

If codebase is substantial:

> "This is a sizeable codebase. Let me give you a map first, then we can zoom into areas you'll be working with.
>
> [Start with architecture overview]
>
> What area is most relevant to your upcoming work? I can focus there."

### Outdated Documentation

If knowledge base conflicts with code:

> "I notice the documentation in `.minispec/knowledge/architecture.md` might be outdated. The code shows [actual structure] but docs say [documented structure].
>
> Want me to:
> a) Walk through based on actual code (and update docs after)
> b) Flag the discrepancies as we go
> c) Update the docs first, then walk through"

### Multiple Entry Points

If the project has multiple apps/services:

> "This project has multiple components:
>
> 1. **[Component A]**: [Purpose]
> 2. **[Component B]**: [Purpose]
> 3. **[Component C]**: [Purpose]
>
> Which would you like to explore? Or shall I explain how they connect?"

## Update Documentation

After walkthrough, offer to update knowledge base:

> "Based on our walkthrough, I could update `.minispec/knowledge/` with:
>
> - [Gap 1 that was filled]
> - [Gap 2 that was filled]
>
> This would help future sessions. Want me to do that?"

## Important Guidelines

- **Start simple**: Don't overwhelm with details upfront
- **Follow their lead**: If they ask about something, go there
- **Show, don't just tell**: Reference actual code when possible
- **Check understanding**: Pause for questions regularly
- **Be honest about unknowns**: If something is unclear, say so
- **Keep it conversational**: This is a dialogue, not a monologue
- **Respect their time**: Match depth to their preference

## Output Artifacts

This command may create/update:

1. `.minispec/knowledge/architecture.md` - If gaps were found
2. `.minispec/knowledge/conventions.md` - If patterns were explained
3. `.minispec/knowledge/modules/*.md` - If modules were explored in depth

Only with engineer approval, and only to capture insights from the walkthrough.
