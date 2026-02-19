---
description: Import a SpecKit/OpenSpec specification and convert it to the MiniSpec pair-programming workflow.
---

## User Input

```text
$ARGUMENTS
```

You are helping an engineer **import an existing specification** (from SpecKit, OpenSpec, or similar) into the MiniSpec pair-programming workflow. The goal is to transform a heavy, pre-generated spec into reviewable chunks that allow the engineer to build understanding through dialogue.

## Philosophy

Heavy specs are useful for planning, but they create a disconnect: the engineer didn't make the decisions, so they don't fully understand them. This import process bridges that gap by:

- Walking through the spec together
- Highlighting key decisions that need engineer buy-in
- Breaking large tasks into MiniSpec-sized chunks (20-80 lines)
- Creating opportunities for the engineer to ask "why?" and adjust

The engineer should finish this process feeling like they understand and own the design, not just inherited it.

## Prerequisites

Before starting, verify:

1. Constitution exists at `.minispec.minispec/memory/constitution.md`
   - If not: "Let's set up your MiniSpec preferences first. Run `/minispec.constitution` or I can use defaults (medium chunks, always confirm)."
2. Knowledge base exists at `.minispec/knowledge/`
   - If not: Create the directory structure

## Execution Flow

### Phase 1: Locate the Specification

1. **If `$ARGUMENTS` is provided**: Treat it as the path to the spec directory
   > "I'll look for a specification at `[path]`..."

2. **If no arguments**: Ask for the location
   > "Where is the specification you want to import? Give me the path to the directory (e.g., `./specs/auth-feature` or `.speckit/`)."

3. **Scan the directory** for common spec artifacts:
   - `plan.md`, `planning.md`, `specification.md`
   - `research.md`, `context.md`
   - `tasks.md`, `implementation.md`
   - `design.md`, `architecture.md`
   - Any numbered files like `01-research.md`, `02-plan.md`
   - Subdirectories with additional context

4. **Report what you found**:
   > "Found the following artifacts:
   > - `plan.md` (2,400 lines) - Main specification
   > - `research.md` (800 lines) - Background research
   > - `tasks.md` (45 tasks) - Implementation plan
   >
   > Ready to walk through this together?"

### Phase 2: Extract and Review Design Decisions

Walk through the spec and surface decisions that need engineer buy-in:

1. **Read the main planning document(s)** and identify:
   - Architectural decisions (technology choices, patterns)
   - Trade-offs that were made
   - Assumptions about requirements
   - Dependencies on external systems

2. **Present decisions one at a time** for review:
   > "The spec chose **JWT tokens** for authentication because:
   > - Stateless (good for scaling)
   > - Works with your Kubernetes setup
   >
   > Does this make sense for your context, or should we reconsider?"

3. **For each decision the engineer approves**:
   - Create an ADR in `.minispec/knowledge/decisions/NNN-[decision-name].md`
   - Note: "Imported from [original spec], reviewed on [date]"

4. **For decisions that need adjustment**:
   - Discuss alternatives
   - Update the approach
   - Document the new decision with rationale

5. **Track progress**:
   > "Reviewed 3/7 major decisions. Next: database choice..."

### Phase 3: Analyze Task Structure

Examine the existing tasks and prepare to restructure them:

1. **Read the tasks/implementation plan** and analyze:
   - Total number of tasks
   - Estimated size of each (if available)
   - Dependencies between tasks
   - Groupings/phases

2. **Compare against MiniSpec chunk preferences** (from constitution):
   - Small: 20-40 lines per chunk
   - Medium: 40-80 lines per chunk
   - Large: 80-150 lines per chunk

3. **Identify tasks that need splitting**:
   > "The spec has 15 tasks, but several are too large for your 'medium chunk' preference:
   > - Task 3: 'User authentication flow' (~200 lines) → split into 3 chunks
   > - Task 7: 'Dashboard components' (~180 lines) → split into 2 chunks
   >
   > Want me to propose how to split these?"

### Phase 4: Create MiniSpec Artifacts

Generate the MiniSpec workflow files:

1. **Determine feature name**:
   - Extract from spec if clear
   - Or ask: "What should we call this feature? (e.g., 'user-auth', 'payment-flow')"

2. **Create design.md** at `.minispec/specs/[feature]/design.md`:
   - Summarize the design (not copy the entire spec)
   - Reference the original spec location
   - List the reviewed decisions
   - Include component overview
   - Use the design template format

3. **Create tasks.md** at `.minispec/specs/[feature]/tasks.md`:
   - Break down into MiniSpec-sized chunks
   - Maintain logical dependencies
   - Each task should have:
     - Clear scope (what files, what functionality)
     - Estimated lines
     - Dependencies on other tasks
   - Use the tasks template format

4. **Preserve the original spec**:
   > "I've kept the original spec at `[path]` for reference. The MiniSpec artifacts link back to it."

### Phase 5: Summary and Next Steps

Provide a clear summary:

```markdown
## Import Complete

**Feature**: [name]
**Source**: [original spec path]

### Decisions Reviewed
- [N] architectural decisions documented as ADRs
- [M] decisions adjusted during review

### Tasks Created
- [X] tasks total (restructured from [Y] original tasks)
- Estimated [Z] pair-programming sessions

### Files Created
- `.minispec/specs/[feature]/design.md`
- `.minispec/specs/[feature]/tasks.md`
- `.minispec/knowledge/decisions/NNN-*.md` (N new ADRs)

### Next Steps
1. Review the generated `design.md` - does it capture the essence?
2. Check `tasks.md` - are the chunks sized right for you?
3. Run `/minispec.next` to start implementing together
```

## Handling Edge Cases

### Incomplete Specifications

If the spec is missing key elements:
> "The specification doesn't include [X]. Before we proceed:
>
> - Should we design this part together now? (run `/minispec.design`)
> - Or do you want to add it to the original spec first?"

### Very Large Specifications

For specs with 50+ tasks or multiple features:
> "This is a large specification covering multiple areas:
>
> - User authentication (12 tasks)
> - Payment processing (18 tasks)
> - Admin dashboard (15 tasks)
>
> I recommend importing one area at a time. Which should we start with?"

### No Clear Tasks

If the spec has design but no implementation breakdown:
> "The spec describes what to build but doesn't break it into tasks.
> Want me to analyze the design and propose a task breakdown?
> Or we can run `/minispec.tasks` after import for a more interactive breakdown."

## Output Artifacts

By the end of this command, the following should exist:

1. `.minispec/specs/[feature]/design.md` - Summarized, reviewed design
2. `.minispec/specs/[feature]/tasks.md` - MiniSpec-sized implementation chunks
3. `.minispec/knowledge/decisions/*.md` - ADRs for key decisions (marked as imported)
4. Original spec preserved at its location

The engineer is now ready to use `/minispec.next` for pair-programming implementation.
