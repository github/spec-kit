---
description: Audit all feature specs against vision.md across six dimensions of vision alignment. Answer "are we building the right thing?" with a structured health report.
handoffs:
  - label: Update Vision
    agent: speckit.vision
    prompt: Update the vision document to address coherence issues
  - label: Create Remediation Spec
    agent: speckit.specify
    prompt: Create a remediation spec for the coherence issues found
    send: true
---

# /speckit.coherence — Vision-Spec Coherence Audit

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Answer the question: **"Are we building the right thing?"**

Audit all feature specs against `.specify/memory/vision.md` across six dimensions.
This command is about vision alignment only — not code quality or implementation details.

## When to run this command

- Before starting a new feature (proactive check)
- After every 3 features are implemented (scheduled check)
- When the team questions whether they're working on the right things
- Before a release or major milestone

## Step 1 — Load all context

Read ALL of the following. Do not skip any file.

**Vision document (primary reference):**
- `.specify/memory/vision.md`
  - Section 1: The Problem We're Solving
  - Section 2: The World After This Project Exists
  - Section 3: Core User Journeys
  - Section 4: What This Project Is NOT
  - Section 5: Quality Bar
  - Section 6: Vision Health Check

**Spec layer — read every spec under `.specify/specs/`:**
- `spec.md` for each feature (mandatory)
- `plan.md` if it exists (for implementation intent)

If vision.md does not exist or is still marked DRAFT with no content filled in,
stop here and output:
> "⚠️ vision.md is missing or incomplete. Run `/speckit.vision` first."

## Step 2 — Build the alignment map

For each spec, extract:
- **Feature name** and one-sentence summary of what it does for users
- **The user journey(s) it claims to serve** (if stated)
- **The success criteria** defined in the spec
- **Scope signals**: what it explicitly includes and excludes

Then extract from vision.md:
- The list of all named Core User Journeys (Section 3)
- The explicit scope exclusions (Section 4)
- The quality standards (Section 5)
- The "next most important thing to build" (Section 6)

## Step 3 — Run six vision alignment checks

### Check 1: Journey Coverage (per spec)

For each spec, ask:
- Does this feature directly serve at least one named Core User Journey in vision.md Section 3?
- If yes: which journey, and how concretely does it advance that journey?
- If no: can a plausible connection be inferred? If not, flag as **JOURNEY MISMATCH**.

A feature is **not** automatically aligned just because it sounds useful.
It must trace to a specific named journey or be challenged.

### Check 2: Scope Boundary Compliance (per spec)

For each spec, ask:
- Does any part of this feature's scope overlap with items listed in vision.md Section 4
  ("What This Project Is NOT")?
- If yes: flag as **SCOPE VIOLATION** with the specific conflicting item quoted from vision.md.

### Check 3: Journey Coverage (across all specs)

For each named Core User Journey in vision.md Section 3, ask:
- Is there at least one spec that directly addresses this journey?
- If no: flag as **UNCOVERED JOURNEY**.

An uncovered journey is a gap in the product — something the vision promises
but the spec portfolio has never formally addressed.

### Check 4: Problem-Solution Fit

Read vision.md Section 1 (The Problem We're Solving) and Section 2 (The World After).
Look at all specs collectively and ask:
- If every spec were fully implemented, would the problem in Section 1 be meaningfully solved?
- Would the "World After" described in Section 2 actually be achievable?
- Are there critical capabilities missing from the spec portfolio that Section 2 requires?

Flag missing capabilities as **SOLUTION GAP**.

### Check 5: Success Criteria vs Quality Bar

For each spec that defines measurable success criteria, compare against vision.md Section 5:
- Does the spec's success criteria meet or exceed the quality bar defined in vision.md?
- Is any spec defining a lower quality standard than the vision requires?

Flag mismatches as **QUALITY BAR MISMATCH** (note only — does not block).

### Check 6: Priority Alignment

Read vision.md Section 6 ("Next most important thing to build").
Compare against the current spec portfolio:
- Is the most important thing already specced?
- If there are unstarted specs, are the highest-priority ones aligned with Section 6?
- Are there specs that consume effort on low-priority areas while high-priority journeys remain uncovered?

Flag misaligned priorities as **PRIORITY DRIFT** (note only — does not block).

## Step 4 — Output the health report

---

### Vision Coherence Report — {DATE}

**Overall health:** [GREEN / YELLOW / RED]
- GREEN: All specs align with vision; no critical gaps
- YELLOW: Some drift or gaps detected; address before next 2 features
- RED: Significant misalignment; resolve before adding new features

**Journey coverage (per spec):** [X of Y specs serve a named journey]
**Scope compliance:** [X violations found]
**Journey coverage (across specs):** [X of Y journeys covered]
**Problem-solution fit:** [X solution gaps found]
**Quality bar alignment:** [X mismatches found]
**Priority alignment:** [X priority drifts found]

---

#### Critical — resolve before next feature

[List JOURNEY MISMATCH and SCOPE VIOLATION items]

Format per item:
> **[spec name]** → [issue type] → [specific conflict or missing link] → [recommended action]

#### Gaps — features the vision requires but no spec covers

[List UNCOVERED JOURNEY and SOLUTION GAP items]

Format per item:
> **[journey or capability]** → not addressed by any spec → [suggested scope for a new spec]

#### Advisory — worth noting, does not block

[List QUALITY BAR MISMATCH and PRIORITY DRIFT items]

---

**Single most important action:**
[One sentence: the highest-leverage fix or missing spec to create right now]

---

## Step 5 — Offer remediation

After delivering the report, ask:
"Would you like me to create a spec for any of the gaps or issues found?"

If yes, invoke `/speckit.specify` with the gap or issue as the feature description.
