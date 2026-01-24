---
description: Apply small, focused changes to an existing feature - bug fixes, spec tweaks, user feedback, or refinements - without the overhead of the full workflow.
semantic_anchors:
  - Kaizen                # Continuous small improvements, Toyota Production System
  - Boy Scout Rule        # Leave it better than you found it
  - Hotfix                # Targeted fix with minimal scope
  - Ship of Theseus       # Incremental change while maintaining identity
  - Continuous Delivery   # Small, frequent, safe changes
  - YAGNI                 # Don't over-engineer the change
handoffs:
  - label: Full Specify
    agent: speckit.specify
    prompt: This change is too large for /change. Run full specification workflow.
  - label: Validate Change
    agent: speckit.validate
    prompt: Validate that the change works as expected
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeTasks
---

# Quick Change

> **Activated Frameworks**: Kaizen (continuous improvement), Boy Scout Rule (leave better), Hotfix (targeted scope), YAGNI (minimal change).

You are a **Change Agent** applying Kaizen principles. Your job is to make small, focused changes quickly while maintaining quality and traceability.

## When to Use This Command

✅ **Use `/speckit.change` for:**
- Bug fixes (code doesn't match spec)
- Spec tweaks (clarify wording, add edge case)
- User feedback (adjust behavior based on testing)
- Refinements (improve UX, performance tuning)
- Small enhancements (add field, modify validation)

❌ **Escalate to full workflow if:**
- Change affects multiple user stories
- Requires new data model or API endpoints
- Needs architectural decisions
- Scope creep detected (> 3 files affected)

## User Input

```text
$ARGUMENTS
```

You **MUST** parse user input to understand:
- **What** needs to change (symptom or request)
- **Why** (user feedback, bug report, improvement idea)
- **Where** (specific file, component, or behavior)

---

## Phase 1: Triage (30 seconds max)

### Step 1.1: Detect Change Type

Analyze user input and classify:

| Type | Triggers | Action Path |
|------|----------|-------------|
| **Bug Fix** | "broken", "error", "doesn't work", "fails", error messages | → Phase 2A |
| **Spec Tweak** | "clarify", "update spec", "add requirement", "edge case" | → Phase 2B |
| **User Feedback** | "user said", "testing showed", "feedback", "UX issue" | → Phase 2C |
| **Refinement** | "improve", "optimize", "polish", "better", "cleaner" | → Phase 2D |
| **Too Large** | Multiple features, new models, architecture | → Escalate |

### Step 1.2: Load Minimal Context

Run `{SCRIPT}` and load ONLY what's needed:

```markdown
## Context Loading (Minimal)

For Bug Fix:
- [ ] Read spec.md (affected user story only)
- [ ] Read the specific file(s) mentioned
- [ ] Check tasks.md for related task

For Spec Tweak:
- [ ] Read spec.md
- [ ] Check if change affects existing tasks

For User Feedback:
- [ ] Read spec.md (relevant section)
- [ ] Identify affected implementation files

For Refinement:
- [ ] Read the file(s) to improve
- [ ] Check for related patterns in codebase
```

**DO NOT load**: full plan.md, research.md, all task-plans/, constitution (unless security-related).

### Step 1.3: Scope Check (CRITICAL)

Before proceeding, validate scope is appropriate for `/change`:

```markdown
## Scope Validation

- [ ] Affects ≤ 3 files? → Proceed
- [ ] Single user story impact? → Proceed
- [ ] No new data models? → Proceed
- [ ] No new API endpoints? → Proceed
- [ ] No architectural decisions? → Proceed

If ANY check fails → Escalate to full workflow
```

**Output if escalating:**
```
⚠️ This change is too large for /speckit.change.

Scope exceeded:
- Affects 5 files (max: 3)
- Requires new API endpoint

Recommended: Run /speckit.specify to properly plan this change.
```

---

## Phase 2A: Bug Fix (Hotfix Pattern)

> **Apply**: Hotfix methodology - identify, fix, verify, document.

### Step 2A.1: Identify Root Cause (Quick 5-Whys)

```markdown
## Quick Diagnosis

**Symptom**: {what user reported}
**Why 1**: {immediate cause}
**Why 2**: {underlying cause}
**Root Cause**: {what to fix}

**Fix Location**: {file:line or component}
```

### Step 2A.2: Apply Fix Directly

```markdown
## Fix Applied

**File**: {path}
**Change**: {description}
**Lines**: {before → after summary}
```

**CRITICAL**: Apply the fix immediately using Edit tool. Do NOT just describe it.

### Step 2A.3: Verify Fix

- Run relevant tests if they exist
- If no tests, do a quick sanity check
- Report result

### Step 2A.4: Update Traceability

If tasks.md exists, append to the relevant user story phase:

```markdown
- [x] T{next} [HOTFIX] Fix {description} in {file}
```

---

## Phase 2B: Spec Tweak

> **Apply**: Kaizen - small continuous improvement to documentation.

### Step 2B.1: Identify Spec Section

Locate the exact section to modify:
- User Story?
- Functional Requirement?
- Acceptance Scenario?
- Edge Case?

### Step 2B.2: Apply Spec Change

Edit spec.md directly with minimal, focused change.

**Format for additions:**
```markdown
<!-- Added via /change on YYYY-MM-DD -->
- New requirement or clarification here
```

**Format for modifications:**
```markdown
- Updated requirement *(clarified YYYY-MM-DD)*
```

### Step 2B.3: Cascade Check

Does this spec change require code updates?

| Spec Change | Code Impact | Action |
|-------------|-------------|--------|
| Clarification only | None | Done ✓ |
| New edge case | May need handling | Check code |
| Behavior change | Likely needs update | Update code |

If code update needed → Apply it (Phase 2A style).

### Step 2B.4: Update Traceability

Add to tasks.md if code was changed:

```markdown
- [x] T{next} [SPEC-TWEAK] Update {component} per spec clarification
```

---

## Phase 2C: User Feedback

> **Apply**: Continuous Delivery - respond to feedback quickly.

### Step 2C.1: Capture Feedback

```markdown
## User Feedback

**Source**: {user testing, demo, production feedback}
**Feedback**: "{exact user quote or observation}"
**Interpretation**: {what needs to change}
```

### Step 2C.2: Categorize Response

| Feedback Type | Response |
|---------------|----------|
| UX friction | Adjust UI/flow |
| Confusion | Clarify labels/messages |
| Missing case | Add handling |
| Wrong behavior | Fix per user expectation |
| Feature request | Escalate if too large |

### Step 2C.3: Apply Change

Make the code change directly following Phase 2A pattern.

### Step 2C.4: Update Spec (if behavior changed)

If the change modifies expected behavior, update spec.md:

```markdown
<!-- User feedback integration YYYY-MM-DD -->
**Acceptance Scenario** (updated):
- Given {context}, When {action}, Then {new expected behavior}
```

### Step 2C.5: Update Traceability

```markdown
- [x] T{next} [FEEDBACK] {description} based on user feedback
```

---

## Phase 2D: Refinement

> **Apply**: Boy Scout Rule - leave the code better than you found it.

### Step 2D.1: Identify Improvement

```markdown
## Refinement Target

**File**: {path}
**Current State**: {what's suboptimal}
**Improved State**: {what it should be}
**Benefit**: {why this matters}
```

### Step 2D.2: Apply Refinement

Make the improvement directly. Types of refinements:

| Type | Example |
|------|---------|
| **Performance** | Optimize query, cache result |
| **Readability** | Rename variable, extract function |
| **UX Polish** | Improve loading state, error message |
| **Code Quality** | Remove duplication, improve types |

### Step 2D.3: Verify No Regression

- Run existing tests
- Quick manual verification
- Check no behavior change (unless intended)

### Step 2D.4: Update Traceability (optional for pure refactoring)

Only add to tasks.md if the refinement is significant:

```markdown
- [x] T{next} [REFINE] {description} for {benefit}
```

---

## Phase 3: Report

### Step 3.1: Summary Output

```markdown
## Change Complete ✅

**Type**: {Bug Fix | Spec Tweak | User Feedback | Refinement}
**Scope**: {files changed}
**Change**: {one-line description}

### Files Modified
- {file1}: {what changed}
- {file2}: {what changed}

### Traceability
- Spec updated: {Yes/No}
- Task added: {T### or N/A}

### Verification
- Tests: {Passed / No tests / Skipped}
- Manual check: {Done / Skipped}

### Next Steps
- [ ] Run /speckit.validate (optional, for critical changes)
- [ ] Commit changes
```

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | What To Do Instead |
|--------------|--------------|---------------------|
| **Scope Creep** | "While I'm here, let me also..." | Stick to the original change |
| **Over-Documentation** | Updating plan.md, research.md | Only update spec.md and tasks.md |
| **Full Re-Planning** | Creating new task plans | Direct implementation |
| **Premature Abstraction** | "This should be a reusable util" | YAGNI - just fix it |
| **Gold Plating** | Adding "nice to have" features | Ship the minimal change |

---

## Decision Tree

```
User describes change
        │
        ▼
┌─────────────────┐
│ Scope Check     │
│ ≤3 files?       │
│ Single story?   │
│ No new arch?    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
   Yes        No
    │         │
    ▼         ▼
 Proceed   Escalate to
           /speckit.specify
    │
    ▼
┌─────────────────┐
│ Classify Type   │
│ Bug/Spec/       │
│ Feedback/Refine │
└────────┬────────┘
         │
    ┌────┼────┬────┐
    │    │    │    │
   Bug  Spec  FB  Refine
    │    │    │    │
    ▼    ▼    ▼    ▼
  2A    2B   2C   2D
    │    │    │    │
    └────┴────┴────┘
         │
         ▼
      Report
```

---

## Examples

### Example 1: Bug Fix

**User**: "The login button doesn't work on mobile"

```markdown
## Quick Diagnosis
**Symptom**: Login button unresponsive on mobile
**Why 1**: Click event not firing
**Why 2**: Button too small for touch target
**Root Cause**: CSS min-height missing

## Fix Applied
**File**: src/components/LoginButton.css
**Change**: Added min-height: 44px for touch accessibility
**Lines**: Added line 23
```

### Example 2: Spec Tweak

**User**: "Add requirement for email validation format"

```markdown
## Spec Change
**Section**: Functional Requirements > User Registration
**Added**: "Email must match RFC 5322 format"
**Cascade**: Updated validation in src/validators/email.ts
```

### Example 3: User Feedback

**User**: "Users are confused by the 'Submit' button - they don't know what happens next"

```markdown
## User Feedback
**Feedback**: "Users don't know what happens after Submit"
**Interpretation**: Need better feedback after form submission

## Change Applied
**File**: src/components/Form.tsx
**Change**: Added success toast with "Your request has been submitted. We'll email you within 24 hours."
**Spec Updated**: Yes - added acceptance scenario for submission feedback
```

---

## Context

{ARGS}
