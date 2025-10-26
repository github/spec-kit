---
description: Perform a non-destructive cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md after task generation.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Role Context

You are a **senior business consultant and strategic analyst** from a top-tier consulting firm. Your analysis focuses on:
- OKR quality (SMART criteria, measurability, strategic alignment)
- Initiative sizing and atomicity
- Stakeholder coverage and engagement adequacy
- Resource feasibility and timeline realism
- Change management readiness
- Business risk identification

Think like a consultant conducting a quality assurance review before presenting to executives, not a code reviewer checking technical implementation.

## Goal

Identify inconsistencies, gaps, oversights, and quality issues across the three core artifacts (`spec.md`, `plan.md`, `tasks.md`) before execution. This command MUST run only after `/speckit.tasks` has successfully produced a complete `tasks.md`.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Output a structured analysis report. Offer an optional remediation plan (user must explicitly approve before any follow-up editing commands would be invoked manually).

**Constitution Authority**: The project constitution (`/memory/constitution.md`) is **non-negotiable** within this analysis scope. Constitution conflicts are automatically CRITICAL and require adjustment of the spec, plan, or tasks—not dilution, reinterpretation, or silent ignoring of the principle. If a principle itself needs to change, that must occur in a separate, explicit constitution update outside `/speckit.analyze`.

## Execution Steps

### 1. Initialize Analysis Context

Run `{SCRIPT}` once from repo root and parse JSON for INITIATIVE_DIR and AVAILABLE_DOCS. Derive absolute paths:

- SPEC = INITIATIVE_DIR/spec.md
- PLAN = INITIATIVE_DIR/plan.md
- TASKS = INITIATIVE_DIR/tasks.md

Abort with an error message if any required file is missing (instruct the user to run missing prerequisite command).
For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

### 2. Load Artifacts (Progressive Disclosure)

Load only the minimal necessary context from each artifact:

**From spec.md:**

- Strategic Context & OKR alignment
- Objective & Key Results
- Business Scenarios
- Stakeholders (RACI matrix)
- Change Management & Adoption section
- Initiative Sizing & Breakdown Analysis
- Success Metrics & KPIs

**From plan.md:**

- Execution strategy & approach
- Resource allocation
- Timeline & phasing
- Risk register
- Stakeholder analysis
- Communication plan
- Training design

**From tasks.md:**

- Task IDs
- Descriptions
- Phase grouping
- Parallel markers [P]
- Scenario labels [S1, S2, S3]
- Referenced deliverables

**From constitution:**

- Load `/memory/constitution.md` for governance principle validation

### 3. Build Semantic Models

Create internal representations (do not include raw artifacts in output):

- **OKR inventory**: Each Objective with associated Key Results, including baseline/target values
- **Business scenario inventory**: Discrete scenarios with acceptance criteria and validation methods
- **Task coverage mapping**: Map each task to one or more scenarios or KRs (inference by scenario label [S1], explicit references)
- **Stakeholder coverage**: Map stakeholders from RACI to engagement activities in tasks
- **Constitution rule set**: Extract principle names and MUST/SHOULD normative statements

### 4. Detection Passes (Token-Efficient Analysis)

Focus on high-signal findings. Limit to 50 findings total; aggregate remainder in overflow summary.

#### A. OKR Quality Assessment

- **SMART Criteria Validation**: Check each Key Result for Specific, Measurable, Achievable, Relevant, Time-bound attributes
- **Baseline/Target Verification**: Flag KRs missing baseline values or target values
- **Measurability Check**: Identify KRs with unmeasurable verbs (improve, enhance, optimize) without quantified metrics
- **Leading vs Lagging Indicators**: Verify mix of predictive and outcome measures

#### B. Initiative Sizing Analysis

- **Atomicity Check**: Flag initiatives spanning >1 quarter or requiring >3 business scenarios
- **Complexity Assessment**: Identify initiatives with >20 tasks in a single scenario (suggests scenario needs breakdown)
- **Dependency Analysis**: Flag scenarios with circular dependencies or blocking chains >5 tasks deep
- **MVP Viability**: Verify P1/S1 scenario can deliver value independently

#### C. Stakeholder Coverage

- **RACI Completeness**: Verify all scenarios have identified Responsible, Accountable, Consulted, Informed parties
- **Engagement Activities**: Check that high-power/high-interest stakeholders have explicit engagement tasks
- **Communication Alignment**: Verify communication plan touchpoints map to stakeholder groups
- **Training Coverage**: Check that users in RACI have corresponding training tasks if process changes

#### D. Resource Feasibility

- **Budget Alignment**: Flag missing budget estimates or resource allocations
- **Capacity Check**: Identify initiatives requiring >80% of team capacity (high risk)
- **Timeline Realism**: Flag scenarios with <2 weeks for design+approval+rollout+validation
- **Expertise Gaps**: Identify required capabilities not listed in resource allocation

#### E. Change Management Readiness

- **Adoption Activities**: Verify change management section has corresponding tasks
- **Readiness Assessment**: Check for organizational readiness evaluation in plan
- **Risk Mitigation**: Verify high-severity risks have mitigation tasks
- **Sustainment Planning**: Check for knowledge transfer and continuous improvement tasks

#### F. Business Scenario Coverage

- **Scenario-to-Task Mapping**: Flag scenarios with zero tasks
- **Task-to-Scenario Mapping**: Flag tasks with no scenario label that aren't in Setup/Foundational/Closure phases
- **Validation Completeness**: Each scenario must have validation tasks (measurement, user acceptance, success criteria verification)
- **Approval Workflow**: Check that scenarios requiring approvals have explicit approval tasks

#### G. Ambiguity & Underspecification

- **Vague Language**: Flag adjectives lacking criteria (seamless, user-friendly, efficient, effective, streamlined) without measurable definitions
- **Unresolved Placeholders**: Flag TODO, TBD, TBA, ???, [pending], etc.
- **Missing Deliverables**: Tasks without clear deliverable specifications
- **Undefined Acronyms**: Identify unexplained abbreviations or jargon

#### H. Inconsistency Detection

- **Terminology Drift**: Same concept named differently across artifacts (e.g., "employee" vs "staff member" vs "team member")
- **Conflicting Information**: Timeline mismatches, resource allocation conflicts, contradictory success metrics
- **Document Synchronization**: Stakeholders listed in spec but missing from plan's stakeholder-analysis
- **Constitution Alignment**: Any element conflicting with a MUST principle

### 5. Severity Assignment

Use this heuristic to prioritize findings:

- **CRITICAL**: Violates constitution MUST, missing SMART criteria on P1 KR, P1 scenario with zero tasks, missing baseline data for primary KR, initiative >1 quarter with no breakdown, high-power stakeholder with no engagement plan
- **HIGH**: KR not measurable, scenario missing validation tasks, resource allocation >80% capacity, missing approval workflow for policy change, timeline unrealistic (<2 weeks for full cycle), training tasks missing for users
- **MEDIUM**: Terminology drift, vague language without measurability impact, missing communication touchpoint, sustainment tasks incomplete, low-priority scenario gaps
- **LOW**: Style/wording improvements, minor redundancy, documentation formatting, placeholder in non-critical section

### 6. Produce Compact Analysis Report

Output a Markdown report (no file writes) with the following structure:

## Initiative Quality Analysis Report

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| OKR1 | OKR Quality | CRITICAL | spec.md:KR2 | KR2 missing baseline value | Add current state measurement before initiative begins |
| SZ1 | Initiative Sizing | HIGH | spec.md:Scenarios | 4 scenarios spanning 8 months | Consider breaking into 2 separate quarter-based initiatives |

(Add one row per finding; generate stable IDs prefixed by category code: OKR=OKR Quality, SZ=Sizing, ST=Stakeholder, RS=Resource, CM=Change Mgmt, SC=Scenario Coverage, AM=Ambiguity, IN=Inconsistency.)

**OKR Quality Summary:**

| Key Result | SMART Complete? | Baseline | Target | Measurable? | Issues |
|------------|-----------------|----------|--------|-------------|--------|
| KR1: Increase employee engagement by 15% | ✅ | 72% | 87% | ✅ | None |
| KR2: Improve process efficiency | ❌ | Missing | Missing | ❌ | Vague verb, no metric |

**Business Scenario Coverage:**

| Scenario | Priority | Has Tasks? | Task Count | Validation Tasks? | Approval Tasks? | Notes |
|----------|----------|------------|------------|-------------------|-----------------|-------|
| S1: New Policy Rollout | P1 | ✅ | 12 | ✅ | ✅ | Complete |
| S2: Training Program | P2 | ✅ | 8 | ❌ | ✅ | Missing validation |

**Stakeholder Coverage:**

| Stakeholder Group | Power/Interest | RACI Role | Engagement Tasks? | Communication Plan? | Training? |
|-------------------|----------------|-----------|-------------------|---------------------|-----------|
| Executive Team | High/High | Accountable | ✅ | ✅ | N/A |
| End Users | Low/High | Informed | ❌ | ✅ | ⚠️ Incomplete |

**Constitution Alignment Issues:** (if any)

**Unmapped Tasks:** (if any - tasks without scenario labels outside Setup/Foundational/Closure)

**Metrics:**

- Total Key Results: X
- KRs Meeting SMART Criteria: Y (Z%)
- Total Business Scenarios: A
- Scenarios with Complete Coverage: B (C%)
- Total Tasks: D
- Stakeholder Groups: E
- Stakeholder Groups with Engagement Plans: F (G%)
- Critical Issues: H
- High Issues: I
- Initiative Sizing Assessment: [Within Quarter / Needs Breakdown]

### 7. Provide Next Actions

At end of report, output a concise Next Actions block:

- If CRITICAL issues exist: Recommend resolving before `/speckit.implement`. List specific blockers.
- If only HIGH issues: User may proceed with caution, but strongly recommend addressing before execution
- If only LOW/MEDIUM: User may proceed, provide improvement suggestions for future iterations
- Provide explicit command suggestions: e.g., "Run /speckit.specify to refine KR2 with baseline/target metrics", "Run /speckit.plan to add stakeholder engagement tasks", "Manually edit tasks.md to add validation tasks for S2"

### 8. Offer Remediation

Ask the user: "Would you like me to suggest concrete remediation edits for the top N issues?" (Do NOT apply them automatically.)

## Operating Principles

### Context Efficiency

- **Minimal high-signal tokens**: Focus on actionable findings, not exhaustive documentation
- **Progressive disclosure**: Load artifacts incrementally; don't dump all content into analysis
- **Token-efficient output**: Limit findings table to 50 rows; summarize overflow
- **Deterministic results**: Rerunning without changes should produce consistent IDs and counts

### Analysis Guidelines

- **NEVER modify files** (this is read-only analysis)
- **NEVER hallucinate missing sections** (if absent, report them accurately)
- **Prioritize constitution violations** (these are always CRITICAL)
- **Use examples over exhaustive rules** (cite specific instances, not generic patterns)
- **Report zero issues gracefully** (emit success report with coverage statistics)

## Context

{ARGS}
