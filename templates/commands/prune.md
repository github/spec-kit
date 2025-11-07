---
description: Compress session context by creating an ultra-compact summary, saving 40-60K tokens in long sessions
scripts:
  sh: scripts/bash/session-prune.sh --json
  ps: scripts/powershell/session-prune.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Analyze the current conversation and create an ultra-compact session summary that preserves critical information while removing redundant context. This frees up 40-60K tokens for continued work.

## Operating Constraints

- **Analysis-only**: Does not modify project files
- **Session-scoped**: Only affects current conversation context
- **Reversible**: Original conversation history remains (just compressed)
- **Smart preservation**: Keeps decisions, current state, and active work

## When to Use

Run `/speckit.prune` when:
- Token usage exceeds 80-100K
- Before starting implementation on large features
- After extensive exploration/research phases
- When `/speckit.budget` shows >60% usage

## Execution Steps

### 1. Analyze Current Session

The command will:
1. Review conversation history
2. Identify key information to preserve
3. Detect redundant/resolved discussions
4. Calculate potential token savings

### 2. Generate Session Summary

Create compressed summary containing **ONLY**:

#### ✅ PRESERVE (Critical Information)
- **Current feature**: Name, number, status
- **Key decisions made**: Technology choices, architectural decisions
- **Active specifications**: Current spec/plan/tasks state
- **Unresolved issues**: Open questions, blockers
- **Next steps**: What to do next

#### ❌ REMOVE (Redundant Context)
- **Resolved questions**: Already answered clarifications
- **Exploration logs**: "Let me search...", "I found...", intermediate steps
- **Successful completions**: Tasks already done and verified
- **Redundant explanations**: Repeated information
- **Historical context**: Earlier feature work (if not relevant)

### 3. Create Summary File

Generate `.speckit/memory/session-summary-YYYY-MM-DD.md`:

```markdown
# Session Summary
**Created**: 2025-11-07 14:30
**Original tokens**: ~98K
**Compressed tokens**: ~35K
**Savings**: 63K tokens (64%)

## Current Work
Feature: 006-task-dependencies
Status: Planning complete, ready for implementation

## Key Decisions
1. Using Prisma schema extension for task relations
2. React Flow library for dependency graph visualization
3. Additive DB migrations only (no breaking changes)

## Active Context
Specifications:
- spec.md: Complete (42 requirements)
- plan.md: Complete, validated
- tasks.md: 38 tasks defined, dependencies mapped

Integration points identified:
- Modifies: src/lib/prisma/schema.prisma
- Extends: src/components/TaskCard.tsx
- New: src/components/DependencyGraph.tsx

## Important Notes
- Task 15 touches existing UI - coordinate with feature 001
- Database migration must run before API changes
- Test data setup requires at least 5 interconnected tasks

## Next Steps
1. Run /speckit.implement
2. Start with database migration (tasks 1-8)
3. Monitor for UI integration issues

## Reference Links
Quick refs loaded:
- specs/001-task-management/quick-ref.md
- specs/003-project-tags/quick-ref.md
```

### 4. Display Pruning Results

```
Session Context Pruned
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Original session: ~98K tokens
Compressed to: ~35K tokens
Tokens saved: 63K (64% reduction)

Preserved:
✓ Current feature state (006-task-dependencies)
✓ Key technical decisions (3 major choices)
✓ Integration points and gotchas
✓ Next action items

Removed:
• Resolved clarification questions (15 exchanges)
• Exploration and search logs
• Redundant explanations
• Completed validation steps

Summary saved to:
.speckit/memory/session-summary-2025-11-07.md

You can now continue with ~150K tokens available for implementation!
```

### 5. Continue Conversation

After pruning, the AI agent should:
1. Load the session summary
2. Resume from where it left off
3. Reference summary for context when needed
4. Continue with fresh token budget

## Pruning Strategy

### What Gets Preserved

**1. State Information** (10-15K tokens)
- Current feature name and number
- Spec/plan/tasks completion status
- Files modified/created so far

**2. Decisions & Rationale** (5-10K tokens)
- Technology choices and why
- Architectural patterns selected
- Trade-offs considered

**3. Active Work** (10-15K tokens)
- Current task being worked on
- Open issues or blockers
- Dependencies between tasks

**4. Reference Data** (5-8K tokens)
- Quick ref file locations
- Key file paths and line numbers
- Important function/class names

### What Gets Removed

**1. Exploration** (20-30K tokens typically)
- "Let me search for..."
- "I found X files..."
- Multiple search attempts
- File listing outputs

**2. Completed Work** (15-25K tokens)
- Successfully finished tasks
- Passing test outputs
- Successful build logs
- Resolved questions

**3. Redundancy** (10-20K tokens)
- Repeated explanations
- Multiple clarifications of same point
- Duplicate information

**4. Meta-discussion** (5-10K tokens)
- Process discussions
- Tool usage explanations
- Historical context

## Best Practices

### Timing
```bash
# Check token usage first
/speckit.budget

# If > 80K tokens, consider pruning
/speckit.prune

# Continue working with fresh budget
/speckit.implement
```

### Frequency
- **First prune**: Around 80-100K tokens
- **Subsequent prunes**: Every 60-80K after first
- **Not too early**: Wait until >60K (pruning <60K not worth it)

### Before Major Operations
```bash
# Before long implementation
/speckit.budget  # Check: 95K tokens
/speckit.prune   # Compress to ~40K
/speckit.implement  # Now have room for implementation
```

## Example Scenarios

### Scenario 1: After Extensive Planning
```
Session at 92K tokens after:
- Constitution creation
- Spec writing with multiple clarifications
- Plan creation with research
- Task breakdown

Prune saves: ~50K tokens
Result: Continue with implementation in same session
```

### Scenario 2: Mid-Implementation
```
Session at 145K tokens after:
- Planning (40K)
- Implementation of 20 tasks (85K)
- Several error fixes (20K)

Prune saves: ~55K tokens
Result: Compress completed work, continue with remaining tasks
```

### Scenario 3: Multi-Feature Session
```
Session at 120K tokens after:
- Feature 1 complete (45K)
- Feature 2 planning (35K)
- Feature 3 started (40K)

Prune saves: ~60K tokens
Result: Preserve Feature 3 context, archive Features 1-2
```

## Output Format

### Success
```
Session Context Pruned Successfully
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before: 98,234 tokens
After: 35,128 tokens
Saved: 63,106 tokens (64.2%)

Current state preserved:
✓ Feature 006-task-dependencies
✓ 3 key technical decisions
✓ 4 integration points
✓ 5 next action items

Session summary: .speckit/memory/session-summary-2025-11-07.md
```

### Minimal Savings
```
Session Pruning Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before: 45,128 tokens
After: 38,245 tokens
Saved: 6,883 tokens (15.3%)

⚠️ Limited savings possible
Reason: Session already fairly compact

Recommendation: Pruning most effective at >80K tokens
Continue working - you have sufficient budget
```

## Integration with Budget Tracker

The budget tracker will recommend pruning:

```bash
/speckit.budget
```

```
Token Budget Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Session: ~92K tokens used
Remaining: ~108K tokens

⚠️  Recommendations:
  • Run /speckit.prune to free ~50K tokens
  • Estimated after prune: ~42K tokens (150K available)
  • Recommended before implementation
```

## Limitations

### Current Version
- **Manual trigger**: Must run command explicitly
- **Estimation-based**: Savings are approximate
- **No auto-pruning**: Doesn't automatically trigger at thresholds
- **Single summary**: Only keeps latest summary

### Future Enhancements
- Auto-prune at threshold
- Multiple summary versions
- Selective preservation (keep specific discussions)
- Incremental pruning (prune in stages)

## Context

{ARGS}
