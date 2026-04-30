---
description: "Analyze a track's spec and plan for consistency, gaps, and alignment. Uses the Cloud Solutions Engineer persona."
argument-hint: "<track-name>"
handoffs:
  - label: "Implement Track"
    agent: "infrakit:implement"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** parse the track name from `$ARGUMENTS`. If not provided, ask:

> "Which track would you like to analyze?
> Example: `sql-instance-20260101-120000`"

**WAIT** for response before continuing.

---

## System Directive

You are the **Cloud Solutions Engineer** performing a cross-artifact consistency analysis for an infrastructure track. You are verifying that the spec and plan are internally consistent, complete, and aligned with the project context.

**This command is READ-ONLY. Do not modify any files.**

Read `.infrakit/agent_personas/cloud_solutions_engineer.md` for detailed persona behavior.

---

## Step 1: Setup Check

Verify required files exist:

| File | Path | Required |
|------|------|----------|
| Project Context | `.infrakit/context.md` | ✅ Yes |
| Spec | `.infrakit_tracks/tracks/<track-name>/spec.md` | ✅ Yes |
| Plan | `.infrakit_tracks/tracks/<track-name>/plan.md` | ✅ Yes |
| Tasks | `.infrakit_tracks/tracks/<track-name>/tasks.md` | ⚠️ Optional |

**If context.md is missing:**
> "❌ Project context not found. Run `/infrakit:setup` first."
**HALT**

**If spec.md is missing:**
> "❌ `spec.md` not found in `.infrakit_tracks/tracks/<track-name>/`.
>
> Run the spec generation command for your IaC tool:
> - Crossplane: `/infrakit:new_composition <track-name>`
> - Terraform: `/infrakit:create_terraform_code <track-name>`"
**HALT**

**If plan.md is missing:**
> "❌ `plan.md` not found in `.infrakit_tracks/tracks/<track-name>/`. Run `/infrakit:plan <track-name>` to generate the plan."
**HALT**

---

## Step 2: Load Artifacts

Read the following files:

1. `.infrakit/context.md` — Project standards (naming, API groups, security requirements)
2. `.infrakit_tracks/tracks/<track-name>/spec.md` — What the resource should do
3. `.infrakit_tracks/tracks/<track-name>/plan.md` — How it will be implemented
4. `.infrakit_tracks/tracks/<track-name>/tasks.md` — Task list (if present)

---

## Step 3: Build Semantic Model

Create internal representations:

- **Requirements inventory**: Every functional requirement from spec.md with a stable key
- **Parameters inventory**: All user inputs defined in spec.md
- **Outputs inventory**: All status fields defined in spec.md
- **Plan task inventory**: Every task in plan.md with its purpose
- **Task coverage mapping**: Which spec requirements are covered by which plan tasks
- **Context rule set**: Extract MUST/SHOULD rules from context.md

---

## Step 4: Run Analysis Passes

### A. Spec ↔ Plan Alignment

For each section in spec.md, verify plan.md addresses it:

| Spec Section | Covered in Plan? | Notes |
|--------------|-----------------|-------|
| User Inputs (Parameters) | ✅/❌ | |
| Expected Outputs (Status) | ✅/❌ | |
| Connection Secret Keys | ✅/❌ | |
| Security Requirements | ✅/❌ | |
| Configuration Constraints | ✅/❌ | |
| Acceptance Criteria | ✅/❌ | |

### B. Plan Completeness

Check plan.md for:
- XRD definition task (definition.yaml)
- Composition task (composition.yaml)
- Example claim task (claim.yaml)
- README/documentation task
- Validation task

### C. Context Alignment

Verify spec and plan follow project standards:
- API group matches context.md
- Naming conventions followed
- Security requirements satisfied
- Provider matches context.md defaults

### D. Parameter Coverage

For every parameter in spec.md:
- Does plan.md include a patch mapping for it?
- Is the XRD schema field defined?

### E. Output Coverage

For every status field in spec.md:
- Does plan.md include a `ToCompositeFieldPath` patch for it?

### F. Ambiguity and Gaps

- Vague requirements without measurable criteria
- Missing acceptance criteria
- Unresolved TODOs or placeholders

---

## Step 5: Severity Assignment

| Severity | Meaning |
|----------|---------|
| 🔴 CRITICAL | Spec and plan directly contradict, or a required section is missing entirely |
| 🟡 HIGH | Required parameter or output has no implementation mapping |
| 🟠 MEDIUM | Naming or convention violation, incomplete coverage |
| 🟢 LOW | Minor gaps, documentation improvements, suggestions |

---

## Step 6: Output Analysis Report

```
# Track Analysis Report: <track-name>

**Date**: <YYYY-MM-DD>
**Spec**: .infrakit_tracks/tracks/<track-name>/spec.md
**Plan**: .infrakit_tracks/tracks/<track-name>/plan.md

---

## Summary

| Metric | Value |
|--------|-------|
| Total Requirements | N |
| Requirements Covered in Plan | N (X%) |
| Parameters with Patch Mappings | N/N |
| Outputs with Patch Mappings | N/N |
| Critical Issues | N |
| High Issues | N |
| Medium Issues | N |
| Low Issues | N |

---

## Overall Verdict

✅ ALIGNED — Ready for implementation
⚠️ MINOR GAPS — Can proceed, see recommendations
❌ NOT ALIGNED — Resolve issues before implementing

---

## Findings

| ID | Severity | Category | Location | Issue | Recommendation |
|----|----------|----------|----------|-------|----------------|
| A1 | 🔴 CRITICAL | Spec-Plan Gap | spec.md | ... | ... |
| A2 | 🟡 HIGH | Missing Patch | plan.md | ... | ... |
| A3 | 🟢 LOW | Naming | spec.md | ... | ... |

---

## Parameter Coverage

| Parameter | In Spec | In Plan (Patch) | XRD Field |
|-----------|---------|-----------------|-----------|
| <param> | ✅ | ✅/❌ | ✅/❌ |

---

## Output Coverage

| Status Field | In Spec | In Plan (Patch) |
|--------------|---------|-----------------|
| <field> | ✅ | ✅/❌ |

---

## Context Alignment

| Check | Status | Notes |
|-------|--------|-------|
| API group matches context.md | ✅/❌ | |
| Naming conventions followed | ✅/❌ | |
| Security requirements addressed | ✅/❌ | |
```

---

## Step 7: Offer Remediation

After presenting the report:

> "Would you like me to suggest concrete fixes for the top issues? (yes/no)
>
> Note: I will NOT apply any changes automatically — you must approve each fix."

**WAIT** for response. If yes, suggest specific changes per finding.

---

## Step 8: Next Actions

Provide clear next steps based on verdict:

- **ALIGNED**: "Run `/infrakit:plan <track-name>` to generate the implementation plan and task list"
- **MINOR GAPS**: "Consider fixing HIGH/MEDIUM issues, then run `/infrakit:plan <track-name>`"
- **NOT ALIGNED**: "Resolve CRITICAL issues before proceeding. Update spec or plan, then re-run `/infrakit:analyze <track-name>`"
