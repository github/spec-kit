---
description: "Conduct a sprint retrospective to understand decisions, identify improvements, and clarify unclear choices. Similar to /speckit.clarify but focused on past sprint analysis."
---

# Sprint Retrospective Command

You are conducting a **sprint retrospective** to help the team understand decisions made during the sprint, identify improvements, and clarify any unclear choices or pivots.

## Context

This command is similar to `/speckit.clarify` but focused on **retrospective analysis** rather than forward-looking clarification. The goal is to:

1. **Understand past decisions** - Why were certain choices made?
2. **Identify patterns** - What worked well and what didn't?
3. **Clarify pivots** - Why did plans change and what was learned?
4. **Generate improvements** - What concrete actions will improve future sprints?
5. **Preserve knowledge** - Document context for future reference

## Prerequisites

Before running this command, ensure:

- [ ] Sprint has been completed or is near completion
- [ ] Sprint summary has been generated (via `/speckit.archive`)
- [ ] Team members are available for retrospective discussion
- [ ] Sprint artifacts exist in `sprints/active/` or `sprints/archive/sprint-NNN/`

## Input

**Arguments**: $ARGUMENTS

If arguments specify a sprint number (e.g., "sprint-001"), conduct retrospective for that archived sprint.
If no arguments, conduct retrospective for the most recently completed sprint.

## Process

### Step 1: Locate Sprint Artifacts

1. **Check for sprint specification**:
   - If `$ARGUMENTS` contains sprint number: Read `sprints/archive/sprint-NNN/`
   - Otherwise: Read `sprints/active/sprint.md` or most recent archive

2. **Gather sprint context**:
   - Read `sprint.md` - Original plan, goals, features
   - Read `summary.md` - What was actually accomplished
   - Read `decisions.md` - Key decisions made during sprint
   - Read feature specs from `specs/NNN-feature-name/` for completed features

3. **Identify areas needing clarification**:
   - Decisions that seem unclear or lack rationale
   - Pivots that changed the sprint direction
   - Features that were dropped or carried over
   - Unexpected challenges or blockers

### Step 2: Structured Retrospective Questions

Ask clarifying questions in these categories. **Similar to `/speckit.clarify`, ask questions sequentially and wait for answers before proceeding.**

#### Category 1: Sprint Goal & Outcomes

1. **Q: Was the sprint goal achieved? Why or why not?**
2. **Q: Which features were completed vs planned? What changed?**
3. **Q: What was the most valuable thing delivered this sprint?**

#### Category 2: Decision Clarification

For each major decision in `decisions.md`:

1. **Q: Why did we choose [X] over [Y]?**
2. **Q: What information did we have when making this decision?**
3. **Q: What were the consequences of this decision?**

#### Category 3: Pivot Analysis

For each pivot or course correction:

1. **Q: When did we realize we needed to pivot?**
2. **Q: What led to this pivot?**
3. **Q: How did the pivot affect the sprint?**

#### Category 4: Process & Workflow

1. **Q: What worked well in our process this sprint?**
2. **Q: What didn't work well in our process?**
3. **Q: Were there any surprises or unexpected challenges?**

#### Category 5: Technical Practices

1. **Q: What technical decisions are we happy with?**
2. **Q: What technical decisions are we questioning?**
3. **Q: What technical debt did we create and why?**

#### Category 6: Team & Collaboration

1. **Q: How was team morale and energy this sprint?**
2. **Q: How well did we collaborate?**
3. **Q: What did team members learn this sprint?**

### Step 3: Generate Retrospective Document

1. **Create retrospective file**:
   - If active sprint: `sprints/active/retrospective.md`
   - If archived sprint: `sprints/archive/sprint-NNN/retrospective.md`

2. **Use template**: Copy from `templates/retrospective-template.md`

3. **Fill in all sections** with answers from the structured questions

4. **Prioritize action items**:
   - High priority: Must do next sprint
   - Medium priority: Do within 2-3 sprints
   - Low priority: Nice to have

### Step 4: Update Sprint Summary

1. **Add retrospective highlights to summary**:
   - Update `summary.md` with key retrospective insights
   - Link to full retrospective document

2. **Update decisions.md with clarifications**:
   - Add clarifying context to unclear decisions
   - Document lessons learned for each decision

### Step 5: Create Action Items

1. **Generate actionable improvements**:
   - Each action item must have:
     - Specific description
     - Owner
     - Success criteria
     - Effort estimate

2. **Link to next sprint**:
   - High-priority actions should be added to next sprint planning

## Output Format

Generate a complete retrospective document with:

1. **Executive Summary**: Top 3 insights, action items, experiments
2. **Detailed Sections**: All questions, answers, and analysis
3. **Action Plan**: Prioritized action items and experiments
4. **Team Recognition**: Specific shout-outs and achievements

## Notes

- This is a **facilitated conversation**, not a one-shot generation
- Ask questions sequentially and wait for answers
- Dig deeper when answers are vague or unclear
- Focus on understanding "why" not just "what"
- Create psychological safety - focus on systems, not individuals
- Generate concrete, actionable improvements

{SCRIPT}
