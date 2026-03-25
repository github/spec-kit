---
description: Audit the current codebase and all feature specs against vision.md. Detect drift, contradiction, duplication, and orphaned implementation. Output a structured health report with prioritized recommendations.
handoffs:
  - label: Update Vision
    agent: speckit.vision
    prompt: Update the vision document to address coherence issues
  - label: Create Remediation Spec
    agent: speckit.specify
    prompt: Create a remediation spec for the coherence issues found
    send: true
---

# /speckit.coherence — Vision & Spec Coherence Audit

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Audit the current codebase and all feature specs against vision.md.
Detect drift, contradiction, duplication, and orphaned implementation.
Output a structured health report with prioritized recommendations.

## When to run this command

- Before starting a new feature (proactive check)
- After every 3 features are implemented (scheduled check)
- When something feels "off" in the codebase (reactive check)
- Before a release or major milestone

## Step 1 — Load all context

Read ALL of the following. Do not skip any file.

**Memory layer:**
- `.specify/memory/vision.md`
- `.specify/memory/constitution.md`

**Spec layer — for each directory under `.specify/specs/`:**
- `spec.md`
- `plan.md` (if exists)
- `tasks.md` (if exists)

**Code layer:**
- List all source files in the project (excluding node_modules, .git, build artifacts)
- Read files that appear central to the architecture (entry points, core modules, shared utilities)

## Step 2 — Build a coherence map

Construct a mental model with three layers:

**Vision layer**: What the project is trying to achieve (from vision.md)
**Spec layer**: What has been formally specified (from all spec.md files)
**Code layer**: What has actually been built (from source files)

## Step 3 — Run four checks

### Check A: Vision Alignment

For each feature spec, ask:
- Does this feature serve at least one Core User Journey in vision.md Section 3?
- Does it stay within the boundaries of vision.md Section 4 (What This Is NOT)?

Flag any spec that fails either test as **VISION DRIFT**.

### Check B: Spec-Code Parity

Compare each spec against the actual code:
- Is there code that implements something NOT in any spec? → **ORPHANED IMPLEMENTATION**
- Is there a spec with no corresponding implementation? → **UNIMPLEMENTED SPEC**
- Is there a spec that was implemented differently than planned? → **SPEC DEVIATION**

### Check C: Internal Consistency

Across all specs and code, look for:
- Two different implementations of the same concept → **DUPLICATION**
- A concept defined differently in two places → **CONTRADICTION**
- A hardcoded value that should be configuration → **HARDCODE RISK**
- A temporary workaround that was never revisited → **TECHNICAL DEBT MARKER**

### Check D: Constitutional Compliance

For each finding, verify it does not violate `.specify/memory/constitution.md`.
Flag violations as **CONSTITUTION BREACH** (highest severity).

## Step 4 — Output the health report

Format the report as follows:

---

### Coherence Report — {DATE}

**Overall health:** [GREEN / YELLOW / RED]
- GREEN: No critical issues, minor cleanup recommended
- YELLOW: Some drift detected, action recommended before next feature
- RED: Significant coherence breakdown, resolve before proceeding

**Vision alignment:** [X of Y features aligned]
**Spec-code parity:** [X orphaned, Y unimplemented, Z deviating]
**Internal consistency:** [X duplications, Y contradictions, Z hardcodes]
**Constitutional compliance:** [X breaches]

---

#### Critical Issues (resolve before next feature)

[List CONSTITUTION BREACH and VISION DRIFT items]
Each item: location → issue → recommended action

#### Moderate Issues (resolve within 2 features)

[List DUPLICATION, CONTRADICTION, SPEC DEVIATION items]

#### Minor Issues (clean up when convenient)

[List ORPHANED IMPLEMENTATION, HARDCODE RISK, TECHNICAL DEBT MARKER items]

---

**Recommended next action:**
[One sentence: the single most important thing to fix right now]

---

## Step 5 — Offer remediation

After delivering the report, ask:
"Would you like me to create a remediation spec for any of these issues?"

If yes, create a new spec entry under `.specify/specs/` using the standard spec template,
with the coherence issue as the driving requirement.
