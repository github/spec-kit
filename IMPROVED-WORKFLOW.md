# Improved Spec-Kit Workflow Guide

This document shows how the enhanced spec-kit works with new token optimization and AI experience improvements.

---

## Scenario 1: Creating a New Project from Scratch

### Step-by-Step Workflow

```bash
# 1. Initialize project
specify init my-app --ai claude

# 2. Navigate to project
cd my-app
claude

# 3. Establish project principles
/speckit.constitution
```
**Prompt:** "Create principles focused on simplicity, test-first development, and maintainability"

```bash
# 4. ✨ NEW: Validate constitution before proceeding
/speckit.validate --constitution
```
**Output:**
```
✓ Constitution exists and is complete
✓ All required sections present
✓ Ready to proceed with specifications
```

```bash
# 5. Create your first feature specification
/speckit.specify
```
**Prompt:** "Build a task management app where users can create tasks, mark them complete, and organize by projects"

```bash
# 6. ✨ NEW: Quick validation before clarification
/speckit.validate --spec
```
**Output:**
```
Specification: 001-task-management
✓ User scenarios defined
✓ Functional requirements present
⚠ 3 ambiguous requirements found
⚠ Missing non-functional requirements

Recommendation: Run /speckit.clarify to address ambiguities
```

```bash
# 7. Clarify underspecified areas
/speckit.clarify
```
**AI asks targeted questions, updates spec incrementally**

```bash
# 8. ✨ NEW: Check token budget before planning
/speckit.budget
```
**Output:**
```
Token Budget Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Session: ~45K tokens used
Remaining: ~155K tokens

Breakdown:
  Spec (001-task-management): 8.5K
  Constitution: 2.1K
  Conversation: 34.4K

💡 Tip: You have plenty of budget for planning
```

```bash
# 9. Create technical implementation plan
/speckit.plan
```
**Prompt:** "Use Next.js 14 with TypeScript, Prisma + PostgreSQL, and Tailwind CSS. Keep it simple."

```bash
# 10. ✨ NEW: Validate plan against constitution
/speckit.validate --plan
```
**Output:**
```
Plan Validation: 001-task-management
✓ Technology choices documented
✓ Aligns with constitution principles
✓ Project structure defined
⚠ No test strategy mentioned

Recommendation: Add testing approach before tasks
```

**Update plan with testing strategy**

```bash
# 11. Generate tasks
/speckit.tasks

# 12. ✨ NEW: Validate tasks before implementation
/speckit.validate --tasks
```
**Output:**
```
Task Validation: 001-task-management
✓ 42 tasks defined
✓ All requirements covered
✓ Dependencies properly ordered
⚠ 5 tasks have no file paths

Ready for implementation: Yes (with minor improvements)
```

```bash
# 13. ✨ NEW: Check budget before long implementation
/speckit.budget
```
**Output:**
```
Token Budget Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Session: ~78K tokens used
Remaining: ~122K tokens

💡 For implementation, consider:
  - Estimated tokens: ~60-80K
  - Use /speckit.prune if needed
  - Implementation will likely fit in budget
```

```bash
# 14. Implement the feature
/speckit.implement
```

**If interrupted during implementation:**
```bash
# ✨ NEW: Resume from checkpoint
/speckit.resume
```
**Output:**
```
Resuming Implementation: 001-task-management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Last checkpoint: Task 23 of 42 completed
Remaining: 19 tasks

Resuming from: "Create API endpoint for task updates"
```

```bash
# 15. ✨ NEW: Generate quick reference + full AI docs
/speckit.document
```
**Output:**
```
AI Documentation Generated
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Feature: 001-task-management

Created files:
  ✓ specs/001-task-management/quick-ref.md (180 tokens)
  ✓ specs/001-task-management/ai-doc.md (2.4K tokens)

Quick Reference includes:
  • 12 key files mapped
  • 4 entry points documented
  • 8 API endpoints listed

Future AI agents can now modify this feature efficiently!
```

```bash
# 16. Test and verify
npm run test
npm run build

# 17. ✨ NEW: Comprehensive project health check
/speckit.analyze --incremental
```
**Output:**
```
Project Analysis: 1 feature
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: Incremental (first run, analyzing all)

Feature: 001-task-management
  ✓ Specification complete
  ✓ Plan complete
  ✓ Tasks complete
  ✓ Implementation: 42/42 tasks (100%)
  ✓ Tests: 28 tests passing

Overall Health: Excellent ✓
Ready for next feature!
```

---

## Scenario 2: Adding New Feature to Existing Project

### Workflow with Token Optimization

```bash
# You're in an existing project with 5 features already built
cd my-app
claude

# 1. ✨ NEW: Quick health check before starting
/speckit.validate --all
```
**Output:**
```
Project Validation Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total features: 5
Status:
  ✓ 001-task-management: Complete
  ✓ 002-user-auth: Complete
  ✓ 003-project-tags: Complete
  ✓ 004-notifications: Complete
  ⚠ 005-file-uploads: Missing AI docs

Constitution: ✓ Present
Overall: Ready for new feature
```

```bash
# 2. ✨ NEW: Find existing code related to new feature
/speckit.find "Where is task data stored and validated?"
```
**Output:**
```
Search Results: task data storage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ranked by relevance:

1. src/lib/prisma/schema.prisma:15
   📄 Task model definition with validation rules

2. src/app/api/tasks/route.ts:34
   🔧 Task creation endpoint with Zod validation

3. specs/001-task-management/ai-doc.md:87
   📝 Data model documentation

4. specs/001-task-management/quick-ref.md:12
   📝 Quick reference - Data layer

💡 Tip: Check quick-ref.md first (180 tokens vs 2.4K)
```

```bash
# 3. ✨ NEW: Load quick reference instead of full docs
# (AI agent automatically uses quick-ref.md - 180 tokens vs 2.4K)

# Read quick-ref for related features
cat specs/001-task-management/quick-ref.md
cat specs/003-project-tags/quick-ref.md
```
**Token savings: 4.2K → 360 tokens (92% reduction)**

```bash
# 4. Create new feature specification
/speckit.specify
```
**Prompt:** "Add task dependencies - users can mark tasks as blocking/blocked by other tasks, with visual graph"

```bash
# 5. ✨ NEW: Check for conflicts with existing features
/speckit.validate --spec --check-conflicts
```
**Output:**
```
Specification Validation: 006-task-dependencies
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Basic checks:
  ✓ User scenarios defined
  ✓ Requirements complete

Conflict Analysis:
  ⚠ Related to: 001-task-management (shared Task entity)
  ⚠ Related to: 003-project-tags (may affect UI layout)
  ✓ No breaking changes detected

Recommendations:
  • Review quick-ref.md for features: 001, 003
  • Consider data migration for existing tasks
  • Plan UI integration carefully
```

```bash
# 6. ✨ NEW: Check current token usage
/speckit.budget
```
**Output:**
```
Token Budget Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Session: ~67K tokens used
Remaining: ~133K tokens

💡 Large context loaded. Consider:
  /speckit.prune - Compress session (save ~40-50K tokens)
  Continue - You have sufficient budget
```

```bash
# 7. ✨ NEW: Prune context to optimize for planning
/speckit.prune
```
**Output:**
```
Context Pruning Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Session compressed: 67K → 23K tokens
Tokens saved: 44K (66% reduction)

Preserved:
  ✓ Constitution principles
  ✓ Current feature spec (006-task-dependencies)
  ✓ Related feature summaries (001, 003)
  ✓ Key decisions from conversation

Removed:
  • Redundant clarifications
  • Resolved questions
  • Detailed exploration logs

New context file created:
  .speckit/memory/session-summary-2025-11-07.md
```

```bash
# 8. Create plan respecting existing codebase
/speckit.plan
```
**Prompt:** "Extend existing Task model in Prisma. Add new API endpoints. Create React dependency graph component. Integrate with existing task UI."

**During planning, AI references quick-ref.md files automatically**

```bash
# 9. ✨ NEW: Validate plan doesn't break existing features
/speckit.validate --plan --check-breaking-changes
```
**Output:**
```
Plan Validation: 006-task-dependencies
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Technical checks:
  ✓ Architecture consistent with existing features
  ✓ Database migrations planned
  ✓ API versioning considered

Breaking Change Analysis:
  ✓ No breaking changes to public APIs
  ✓ Database changes are additive only
  ⚠ UI changes may affect task card layout

Affected Features:
  001-task-management: Minor (UI integration)
  003-project-tags: None

Recommendation: Safe to proceed with noted UI coordination
```

```bash
# 10. Generate tasks
/speckit.tasks

# 11. ✨ NEW: Check implementation order
/speckit.validate --tasks --check-dependencies
```
**Output:**
```
Task Validation: 006-task-dependencies
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task breakdown:
  • 38 tasks defined
  • 12 tasks marked parallel [P]
  • 3 tasks touch existing code

Dependency Order Validation:
  ✓ Database migration before API changes
  ✓ API changes before UI integration
  ✓ Tests ordered correctly

Integration Points:
  Task 8: Modify src/lib/prisma/schema.prisma (existing)
  Task 15: Update src/components/TaskCard.tsx (existing)
  Task 31: Update src/app/api/tasks/route.ts (existing)

💡 Tip: Review existing files before starting
```

```bash
# 12. ✨ NEW: Load only the files to be modified
/speckit.find "TaskCard component implementation"
```
**Output:**
```
Search Results: TaskCard component
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. src/components/TaskCard.tsx:1
   🔧 Main component (254 lines)

2. specs/001-task-management/ai-doc.md:145
   📝 Component architecture docs

Quick Summary from ai-doc.md:
  • Props: task, onUpdate, onDelete
  • State: local editing state
  • Key methods: handleStatusChange, handleTagUpdate
  • Modify here for: visual changes, new task actions
```

```bash
# 13. ✨ NEW: Differential analysis (only changed code)
/speckit.analyze --diff-only
```
**Output:**
```
Differential Analysis: 006-task-dependencies
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: Diff-only (analyzing git changes only)
Tokens used: 3.2K (vs 28K for full analysis)

Changed files analyzed: 8
  ✓ schema.prisma: Migration looks good
  ✓ route.ts: New endpoints follow conventions
  ✓ TaskCard.tsx: Props extended correctly
  ⚠ DependencyGraph.tsx: Consider memoization

Issues found: 1 medium (performance)
Overall: Good to merge
```

```bash
# 14. Implement the feature
/speckit.implement

# 15. ✨ NEW: Incremental analysis (only new feature)
/speckit.analyze --incremental
```
**Output:**
```
Project Analysis (Incremental)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: Incremental
Tokens used: 4.8K (vs 45K for full analysis)
Time saved: 87%

Changed: 1 feature (006-task-dependencies)
Unchanged: 5 features (using cached results)

Feature: 006-task-dependencies
  ✓ Specification complete
  ✓ Plan complete
  ✓ Implementation: 38/38 tasks
  ✓ Tests: 15 new tests passing
  ✓ No breaking changes detected

Cache hit rate: 83%
Overall Health: Excellent ✓
```

```bash
# 16. ✨ NEW: Document new feature
/speckit.document
```
**Output:**
```
AI Documentation Generated
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Feature: 006-task-dependencies

Created:
  ✓ specs/006-task-dependencies/quick-ref.md (195 tokens)
  ✓ specs/006-task-dependencies/ai-doc.md (2.8K tokens)

Integration notes added:
  • Links to modified files in features 001, 003
  • Dependency graph entry points
  • Migration guide for existing data
```

```bash
# 17. ✨ NEW: Batch update all feature docs
/speckit.document --all
```
**Output:**
```
Batch Documentation Update
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processing 6 features...

  ✓ 001-task-management: Updated (modified integration points)
  ✓ 002-user-auth: Unchanged (skipped)
  ✓ 003-project-tags: Updated (UI changes noted)
  ✓ 004-notifications: Unchanged (skipped)
  ✓ 005-file-uploads: Generated missing docs
  ✓ 006-task-dependencies: Already current

Updated: 3 features
Skipped: 2 features (no changes)
Time saved: 65% (incremental detection)
```

```bash
# 18. Final validation
/speckit.validate --all
```
**Output:**
```
Project Validation Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total features: 6
Status:
  ✓ All features complete
  ✓ All features documented
  ✓ No conflicts detected
  ✓ Constitution followed

Overall: Excellent ✓
Ready to commit and deploy!
```

---

## Token Savings Comparison

### Traditional Workflow (Without Improvements)
```
Creating new project:
  Constitution + Spec + Plan + Clarify + Implement
  Total tokens: ~120-150K
  Risk: Context overflow on large features

Adding feature to existing project:
  Load all feature docs + Create new + Implement
  Total tokens: ~180-220K (5 features × 35K + new 50K)
  Risk: Frequently exceeds limits, requires restarts
```

### Improved Workflow (With New Commands)
```
Creating new project:
  + Quick validations: +2K tokens
  + Budget tracking: +0.5K tokens
  + Quick refs instead of full docs: -8K tokens
  - Context pruning: -40K tokens (when needed)
  Total tokens: ~75-95K
  Savings: 37-55% reduction

Adding feature to existing project:
  + Quick refs (360 tokens vs 17.5K): -17K tokens
  + Differential analysis (3K vs 28K): -25K tokens
  + Incremental analysis (4.8K vs 45K): -40K tokens
  + Context pruning: -44K tokens
  Total tokens: ~85-110K
  Savings: 52-63% reduction

With session pruning during long sessions:
  Additional savings: 40-60K tokens
  Total possible savings: Up to 85% for complex projects
```

---

## Command Quick Reference

### New Commands

```bash
# Validation
/speckit.validate                    # Validate current feature
/speckit.validate --spec             # Validate only spec
/speckit.validate --plan             # Validate only plan
/speckit.validate --tasks            # Validate only tasks
/speckit.validate --all              # Validate entire project
/speckit.validate --check-conflicts  # Check for feature conflicts
/speckit.validate --check-breaking-changes  # Check breaking changes

# Token Management
/speckit.budget                      # Show current token usage
/speckit.prune                       # Compress session context
/speckit.compress                    # Compress specifications

# Code Discovery
/speckit.find "query"                # Semantic code search

# Implementation
/speckit.resume                      # Resume interrupted implementation

# Documentation
/speckit.document                    # Generate AI docs for current feature
/speckit.document --all              # Generate/update all feature docs

# Analysis
/speckit.analyze --incremental       # Analyze only changed features
/speckit.analyze --diff-only         # Analyze only changed lines
/speckit.analyze --summary           # Quick summary (90% faster)
```

### Existing Commands (Enhanced)

```bash
/speckit.constitution               # Create project principles
/speckit.specify                    # Create feature specification
/speckit.clarify                    # Clarify ambiguous requirements
/speckit.plan                       # Create implementation plan
/speckit.tasks                      # Generate task breakdown
/speckit.implement                  # Execute implementation
/speckit.project-analysis           # Full project analysis (enhanced)
```

---

## Best Practices with New Commands

### 1. Always Validate Early
```bash
# Good: Catch issues early
/speckit.specify
/speckit.validate --spec
/speckit.clarify  # Fix issues
/speckit.plan

# Bad: Find issues late
/speckit.specify
/speckit.plan
/speckit.tasks
/speckit.implement  # Issues discovered here = wasted tokens
```

### 2. Use Quick References First
```bash
# Good: Fast comprehension (180 tokens)
cat specs/001-feature/quick-ref.md
# Then load full docs only if needed

# Bad: Always load full docs (2.4K tokens)
cat specs/001-feature/ai-doc.md
```

### 3. Prune Long Sessions
```bash
# After 60-80K tokens of conversation:
/speckit.budget     # Check usage
/speckit.prune      # Save 40-50K tokens
# Continue working with clean context
```

### 4. Use Incremental Analysis
```bash
# First analysis: Full
/speckit.analyze

# Subsequent analyses: Incremental (70-90% faster)
/speckit.analyze --incremental

# Quick check: Summary (90% faster)
/speckit.analyze --summary
```

### 5. Batch Document Updates
```bash
# After major refactoring across features:
/speckit.document --all

# Updates only changed features automatically
# Skips unchanged features (saves time)
```

### 6. Use Semantic Search
```bash
# Instead of manual grepping:
/speckit.find "authentication flow"
/speckit.find "where are tasks validated"
/speckit.find "database schema for users"

# Gets ranked results across code + specs + docs
```

---

## Workflow Decision Tree

```
Starting new feature?
├─ Yes: Is this your first feature?
│   ├─ Yes: Use "Scenario 1: New Project" workflow
│   └─ No:  Use "Scenario 2: Existing Project" workflow
│
└─ No: Are you debugging/modifying?
    ├─ Use /speckit.find to locate code
    ├─ Check quick-ref.md for overview
    └─ Use /speckit.validate before committing

Token usage > 80K?
├─ Yes: Run /speckit.prune
└─ No:  Continue normally

Implementation interrupted?
├─ Yes: Use /speckit.resume
└─ No:  Continue normally

Ready to commit?
├─ Run /speckit.validate --all
├─ Run /speckit.analyze --incremental
└─ Commit if all pass
```

---

## Summary

The improved spec-kit workflow provides:

✅ **Token Efficiency**
- 37-63% reduction in typical workflows
- Up to 85% with aggressive pruning
- Incremental analysis reuses cached results

✅ **Faster Development**
- Quick validations catch issues early
- Semantic search finds code instantly
- Resume capability prevents lost work

✅ **Better AI Experience**
- Quick references load in <200 tokens
- Context pruning keeps sessions clean
- Clear error messages with recommendations

✅ **Existing Codebase Respect**
- Conflict detection prevents breaking changes
- Differential analysis focuses on changes
- Cross-feature coordination tools

The workflow remains familiar while adding powerful optimization and quality gates at each step.
