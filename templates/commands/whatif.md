---
description: Preview the downstream impact (complexity, effort, tasks, risks) of requirement changes before committing to them.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** use this input as the "What-if Scenario" to analyze. If empty, prompt the user for a scenario.

## Goal

Provide a detailed, read-only simulation of how the proposed requirement change would impact the project's specification, implementation plan, and task breakdown. Help the team make data-driven decisions about whether to proceed with the change.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. This is a pure in-memory simulation.

## Execution Steps

### 1. Initialize Simulation Context

Run `{SCRIPT}` once from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS.
Load core artifacts from FEATURE_DIR:
- **spec.md**: Current requirements and priorities.
- **plan.md**: Current architecture and technical choices.
- **tasks.md**: Current task list and effort markers.
- **constitution**: Project principles (from `/memory/constitution.md`).

### 2. Formulate Simulated State

In your context, model the project as it would look *after* the proposed change:
- **Requirements**: Which are added, removed, or modified?
- **Architecture**: What technical changes are required (new libraries, DB schema changes, API updates)?
- **Tasks**: What is the delta in the task list?

### 3. Calculate Impact Metrics

Derive the following deltas based on your assessment:

#### A. Complexity Score (1-100)
- **Current Score**: Based on requirement count, dependency depth, and technical risk.
- **Simulated Score**: Based on the project state after the change.
- **Delta**: (Simulated - Current).

#### B. Effort Delta (Hours)
- Estimate the total person-hours required to implement the change.
- Breakdown: Research, Development, Testing, Refactoring.

#### C. Task Count Delta
- Number of tasks to be added, removed, or significantly altered.

### 4. Risk Assessment

Identify potential pitfalls:
- **Breaking Changes**: Impact on existing APIs or data.
- **Architecture Drift**: Does the change move the project away from its original goal?
- **Constitution Conflicts**: Does the change violate any project principles?
- **Integration Debt**: New dependencies or maintenance overhead.

### 5. Generate Simulation Report

Output a structured Markdown report (no file writes) with the following structure:

# "What-if" Analysis: [Scenario Summary]

## Executive Summary

| Metric | Current | Simulated | Delta |
|--------|---------|-----------|-------|
| Complexity Score | [Score] | [Score] | [+/- Delta] |
| Total Tasks | [Count] | [Count] | [+/- Delta] |
| Estimated Effort | [Hours] | [Hours] | [+/- Hours] |

**Risk Level**: [LOW | MEDIUM | HIGH | CRITICAL]

---

## 🏗️ Impacted Artifacts

### 📋 Specification (spec.md)
- **Changes**: [Briefly list requirement alterations]
- **Impact**: [High-level impact on user value]

### 📐 Implementation Plan (plan.md)
- **Changes**: [Briefly list architectural updates]
- **Impact**: [Technological implications]

### ✅ Task Breakdown (tasks.md)
- **[ADDED]**: [T-NEW-1] Description...
- **[REMOVED]**: [T-OLD-4] Description...
- **[CHANGED]**: [T-MOD-12] Description...

---

## 🚦 Risk Assessment

| Potential Risk | Severity | Mitigation Suggestion |
|----------------|----------|-----------------------|
| [Risk Title] | [Severity] | [Strategy] |

---

## 📊 Side-by-Side Preview (Simulated)

Show a diff-like preview for the most significant file change (typically spec.md or plan.md).

```markdown
<<<< CURRENT
[Original Content Snippet]
==== SIMULATED
[New Content Snippet]
>>>>
```

## 🏁 Recommendation

Provide a clear "Go / No-Go" recommendation based on the data. Suggest follow-up commands (e.g., "/speckit.specify" to apply these changes) if the user decides to proceed.

## Context

{ARGS}
