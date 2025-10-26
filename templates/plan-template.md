# Initiative Execution Plan: [INITIATIVE NAME]

**Branch**: `[###-initiative-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Initiative specification from `/specs/[###-initiative-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Executive Summary

[Extract from initiative spec: primary objective + key results + high-level execution approach]

## Initiative Context

<!--
  ACTION REQUIRED: Replace the content in this section with the execution details
  for the initiative. Use this section to capture critical context for planning.
-->

**Organizational Dependencies**: [e.g., Requires Finance team sign-off or NEEDS CLARIFICATION]  
**Critical Deadlines**: [e.g., Must complete before fiscal year end or NEEDS CLARIFICATION]
**Initiative Type**: [HR/Legal/Sales Ops/Marketing/Finance/Operations - determines execution approach]  
**Key Performance Indicators (KPIs)**: [e.g., Reduce employee onboarding time from 45 days to 30 days or NEEDS CLARIFICATION]  
**Constraints**: [e.g., Budget cap of $50K, must comply with GDPR, or NEEDS CLARIFICATION]  
**Scope**: [e.g., Pilot with 2 departments first, then company-wide rollout or NEEDS CLARIFICATION]
**Strategic Alignment**: [Which company OKRs or strategic initiatives does this support?]

## Constitution Check

*GATE: Must pass before Phase 0 stakeholder analysis. Re-check after Phase 1 execution planning.*

[Gates determined based on constitution file - e.g., initiative sizing limits, mandatory stakeholder reviews, governance requirements, risk thresholds]

**Governance Requirements Validation**:
- [ ] Initiative aligns with organizational constitution/governance
- [ ] Required stakeholder approvals identified
- [ ] Budget authority and approval process clear
- [ ] Compliance and regulatory requirements addressed
- [ ] Risk tolerance within acceptable bounds
- [ ] Resource allocation follows organizational policies

## Initiative Structure

### Documentation (this initiative)

```text
specs/[###-initiative]/
├── plan.md                    # This file (/speckit.plan command output)
├── stakeholder-analysis.md    # Phase 0 output (/speckit.plan command)
├── process-maps.md            # Phase 1 output (/speckit.plan command) - if relevant
├── communication-plan.md      # Phase 1 output (/speckit.plan command)
├── execution-guide.md         # Phase 1 output (/speckit.plan command)
├── training-materials/        # Phase 1 output (/speckit.plan command) - if relevant
└── tasks.md                   # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

## Complexity & Risk Tracking

> **Fill ONLY if Constitution Check has violations that must be justified, or if initiative has significant complexity/risk**

| Concern/Violation | Why Needed | Alternative Considered | Risk Mitigation |
|-------------------|------------|------------------------|-----------------|
| [e.g., Cross-functional dependencies with 5+ teams] | [Scope requires coordination across all functions] | [Limiting to 2 teams would exclude critical stakeholders] | [Weekly coordination meetings, single point of contact per team] |
| [e.g., Budget exceeds normal threshold] | [Vendor costs are fixed market rate] | [In-house solution evaluated but lacks required expertise] | [Phased payment terms, clear deliverable milestones] |
| [e.g., Timeline is aggressive] | [Board deadline immovable] | [Extending timeline would miss regulatory window] | [Additional resources allocated, parallel workstreams] |

---

## Phase 0: Stakeholder Analysis & Alignment

**Purpose**: Build comprehensive understanding of stakeholder landscape, current state, and readiness for change.

### Activities:

1. **Stakeholder Identification & Mapping**:
   - Map all affected stakeholders (individuals, teams, departments)
   - Assess power/interest matrix (High/Low Power × High/Low Interest)
   - Identify champions, skeptics, and blockers
   - Document communication preferences and engagement needs

2. **Current State Analysis**:
   - Document existing processes, policies, or systems being changed
   - Identify pain points and inefficiencies in current state
   - Gather baseline metrics for all Key Results
   - Understand informal workflows and workarounds in use

3. **Organizational Readiness Assessment**:
   - Assess change fatigue and capacity for this initiative
   - Identify competing initiatives and potential conflicts
   - Evaluate organizational culture and change history
   - Determine training needs and capability gaps

4. **Risk & Dependency Analysis**:
   - Identify all dependencies on other teams/initiatives
   - Document regulatory, compliance, or policy constraints
   - Assess resource availability and conflicts
   - Map critical path and potential bottlenecks

5. **Generate stakeholder-analysis.md** with findings:
   - Stakeholder map with engagement strategies
   - Current state documentation with pain points
   - Readiness assessment with gap analysis
   - Risk register with mitigation plans
   - Recommendations for Phase 1 planning

**Output**: `stakeholder-analysis.md` with all unknowns from Initiative Context resolved

**Gate Criteria**: 
- [ ] All key stakeholders identified and engaged
- [ ] Baseline metrics captured for all Key Results
- [ ] Risks documented with mitigation strategies
- [ ] Organizational readiness confirmed or gaps addressed
- [ ] No [NEEDS CLARIFICATION] markers remain from Initiative Context

---

## Phase 1: Execution Planning & Design

**Prerequisites:** `stakeholder-analysis.md` complete, all gates passed

### Activities:

1. **Process Mapping & Design** (if process change initiative):
   - Document target state processes (if relevant)
   - Create process flow diagrams showing current → future state
   - Identify process ownership and hand-offs
   - Define standard operating procedures (SOPs)
   - Output: `process-maps.md`

2. **Communication & Change Management Planning**:
   - Develop communication calendar and key messages
   - Design stakeholder engagement touch points
   - Plan town halls, workshops, and feedback sessions
   - Create FAQ and talking points for leaders
   - Define feedback loops and issue escalation process
   - Output: `communication-plan.md`

3. **Execution Planning**:
   - Break initiative into phases with clear gates
   - Define pilot approach (if applicable)
   - Create detailed timeline with dependencies
   - Assign ownership for each deliverable
   - Define quality gates and approval processes
   - Output: `execution-guide.md`

4. **Training & Enablement Design** (if people/process change):
   - Design training curriculum and materials
   - Identify training delivery methods
   - Create job aids and reference materials
   - Plan train-the-trainer sessions (if applicable)
   - Output: `training-materials/` directory

5. **Measurement & Reporting Framework**:
   - Define how each KPI will be measured
   - Set up data collection mechanisms
   - Create dashboards or reporting templates
   - Define reporting cadence and audience
   - Establish early warning indicators

**Output**: Complete execution plan with all supporting artifacts

**Gate Criteria**:
- [ ] Execution plan is realistic and achievable
- [ ] All stakeholders have reviewed and approved approach
- [ ] Training plan addresses all capability gaps
- [ ] Communication plan covers all stakeholder groups
- [ ] Measurement framework captures all Key Results
- [ ] Resource commitments secured from all teams
- [ ] Budget approved (if required)

**Checkpoint**: Re-evaluate Constitution Check post-planning

---

## Phase 2: Task Breakdown

This phase is handled by the `/speckit.tasks` command (see tasks.md). It will break down the execution plan into specific action items organized by:
- Planning & preparation tasks
- Stakeholder engagement activities
- Document creation and approval workflows
- Training development and delivery
- Communication touchpoints
- Pilot execution (if applicable)
- Full rollout activities
- Validation and measurement checkpoints

---

## Success Criteria for Plan Completion

Before moving to task generation (`/speckit.tasks`), verify:

- [ ] Stakeholder analysis is comprehensive and complete
- [ ] All [NEEDS CLARIFICATION] items from spec.md are resolved
- [ ] Execution approach is validated by key stakeholders
- [ ] Resource commitments are confirmed and documented
- [ ] Timeline is realistic with appropriate buffers
- [ ] Risks have documented mitigation plans
- [ ] Measurement framework is ready to deploy
- [ ] Communication plan addresses all stakeholder groups
- [ ] Training plan (if needed) is designed and approved
- [ ] Budget (if required) is approved and allocated

---

## Next Steps

1. Review this plan with executive sponsor and core team
2. Obtain formal approval to proceed
3. Run `/speckit.tasks` to generate detailed action items
4. Begin Phase 0 stakeholder analysis activities
