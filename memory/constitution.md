# Spec-Kit Operations Constitution
<!-- Business Operations OKR Planning Governance Framework -->

## Core Principles

### I. Quarter-Based Initiative Sizing (NON-NEGOTIABLE)

Every initiative MUST be executable within one fiscal quarter (≤13 weeks).

**Mandatory Requirements:**
- Initiatives spanning >1 quarter MUST be broken down into multiple quarter-based initiatives
- Each initiative delivers independent, measurable value
- No initiative may have >5 business scenarios
- If initiative requires >20 tasks in any single scenario, scenario MUST be decomposed

**Rationale:** Quarter-based sizing ensures:
- Predictable delivery cadence aligned to OKR cycles
- Reduced execution risk through smaller scope
- Faster value realization and learning cycles
- Easier stakeholder commitment and resource allocation

**Red Flags Requiring Breakdown:**
- Timeline estimates >13 weeks
- >5 distinct business scenarios
- Requires >3 organizational functions to collaborate continuously
- "Phase 2" or "Future enhancements" language in core scope

### II. SMART Key Results (NON-NEGOTIABLE)

Every Key Result MUST meet ALL five SMART criteria before planning begins.

**Mandatory Requirements:**
- **Specific**: Precisely defined outcome, no ambiguous verbs ("improve", "enhance", "optimize" without metric)
- **Measurable**: Quantified target with unit of measure; baseline value documented
- **Achievable**: Evidence of feasibility (historical data, pilot results, expert assessment)
- **Relevant**: Clear linkage to organizational strategic goal or OKR
- **Time-bound**: Explicit completion date or measurement period

**Non-Compliant KRs are BLOCKED from planning:**
- "Improve employee satisfaction" ❌ (not measurable)
- "Increase sales by 50%" ✅ IF baseline documented ✅ (measurable, specific)
- "Launch new system" ❌ (not measurable - launch is activity, not outcome)
- "Reduce processing time from 5 days to 3 days by Q2 end" ✅ (fully SMART-compliant)

**Validation Checkpoint:**
- Baseline data exists or baseline measurement task in Phase 2 (Foundational)
- Target value has achievability rationale documented
- Measurement methodology defined (data source, calculation, frequency)

### III. Stakeholder Engagement Planning (NON-NEGOTIABLE)

Every initiative MUST have complete stakeholder analysis with RACI matrix before execution.

**Mandatory Requirements:**
- RACI matrix complete for all business scenarios (Responsible, Accountable, Consulted, Informed)
- High-power/high-interest stakeholders have explicit engagement tasks in tasks.md
- Stakeholder resistance risks identified with mitigation strategies
- Communication plan touchpoints map to all stakeholder groups

**Validation Gates:**
- Accountable role assigned (single decision-maker, typically Director+ level)
- Responsible roles have capacity commitment documented
- Consulted stakeholders have feedback collection mechanisms defined
- Informed stakeholders have communication delivery confirmation mechanism

**Blockers Requiring Resolution:**
- No Accountable stakeholder identified → CANNOT PROCEED
- High-power stakeholder has "Informed" role but should be "Consulted" → ESCALATE
- End users have no engagement tasks → ADD stakeholder validation tasks

### IV. Baseline Measurement Required

Every measurable Key Result MUST have baseline data captured BEFORE execution begins OR baseline measurement as first Foundational task.

**Mandatory Requirements:**
- Baseline value documented in spec.md KR section OR
- Baseline measurement task in Phase 2 (Foundational tasks) with completion gate

**Rationale:**
- Cannot measure improvement without starting point
- Baseline influences target achievability assessment
- Provides early signal if data collection is feasible

**Acceptable Baseline Sources:**
- Historical system data (last quarter/year average)
- Survey baseline (pre-initiative measurement)
- Audit results
- Manual data collection pilot
- Estimated baseline with documented assumptions (must be validated in Foundational phase)

### V. Change Management Integration

Initiatives with Moderate or Transformational change magnitude MUST include change management activities.

**Change Magnitude Assessment (in spec.md):**
- **Minor**: Process adjustment, no role changes, <50 users affected, <2 week adoption
- **Moderate**: Process redesign, role changes, 50-500 users, 1-2 month adoption, training required
- **Transformational**: New processes, org structure changes, >500 users, >2 month adoption, culture shift needed

**Mandatory for Moderate/Transformational:**
- Organizational readiness assessment (6 dimensions: change fatigue, capacity, capability, culture, change history, leadership support)
- Training needs analysis and training tasks
- Communication plan with >3 touchpoints across initiative lifecycle
- Adoption validation tasks (user acceptance, feedback collection)
- Sustainment planning (knowledge transfer, continuous improvement)

**Validation Checkpoint:**
- Change magnitude assessed in spec.md
- If Moderate/Transformational: plan.md includes stakeholder-analysis.md, communication-plan.md, training design
- tasks.md includes change management tasks (workshops, training delivery, adoption validation)

### VI. Independent Scenario Validation

Every business scenario (P1, P2, P3) MUST be independently validatable with clear success criteria.

**Mandatory Requirements:**
- Each scenario has acceptance criteria defined in spec.md
- Each scenario has validation tasks in tasks.md (measurement, user feedback, success threshold check)
- P1 scenario can deliver value even if P2/P3 never execute (MVP viability)
- Scenarios have minimal dependencies (prefer sequential independence)

**Validation Structure:**
- Scenario description includes "This scenario is successful when..." statement
- Validation tasks reference specific acceptance criteria
- Success threshold defined (e.g., "80% user adoption", "zero critical defects", "<5% error rate")

### VII. Risk Mitigation Planning

High-severity risks MUST have documented mitigation strategies and mitigation tasks in tasks.md.

**Risk Severity Criteria:**
- **High**: Likely (>40% probability) AND High Impact (delays >2 weeks, cost >20% budget, blocks critical dependency)
- **Medium**: Possible (20-40%) OR Moderate Impact
- **Low**: Unlikely (<20%) AND Low Impact

**Mandatory for High-Severity Risks:**
- Mitigation strategy documented in spec.md Risks section
- Mitigation tasks added to tasks.md (usually in Foundational phase)
- Risk owner assigned
- Contingency plan identified

**Common High-Severity Risks:**
- Executive sponsor departure during initiative
- Budget freeze or resource reallocation
- Regulatory requirement change
- Critical vendor delay
- Technical dependency failure

## Additional Governance Standards

### Initiative Approval Gates

**Before /speckit.plan execution:**
- spec.md complete with all sections
- OKR quality validated (SMART criteria met)
- Stakeholders identified (at minimum: Accountable role assigned)
- Initiative sizing within quarter (≤13 weeks estimated)

**Before /speckit.implement execution:**
- All readiness checklists complete (if present)
- Accountable stakeholder sign-off obtained
- Budget approval secured (or "proceed at risk" explicit approval)
- Resources committed (FTE availability confirmed)

### Documentation Standards

**Spec.md Requirements:**
- Strategic Context: Links to org-level OKRs or strategic goals
- Objective & Key Results: All KRs SMART-compliant
- Business Scenarios: P1/P2/P3 prioritization with rationale
- Stakeholders: RACI matrix complete
- Change Management: Magnitude assessed, adoption plan outlined
- Initiative Sizing: Atomicity assessment, breakdown if needed

**Plan.md Requirements:**
- Execution Strategy: Phasing approach, quality gates
- Resources: Budget, FTE, vendors/consultants
- Timeline: Milestones aligned to quarter
- Stakeholder Analysis: Power/Interest matrix, engagement strategy, readiness assessment
- Communication Plan: Touchpoints, messages, feedback mechanisms
- Training Design (if Moderate/Transformational change)

**Tasks.md Requirements:**
- Strict checklist format compliance (checkbox, ID, labels, deliverables)
- Phase structure: Setup → Foundational → Scenarios (S1, S2, S3) → Closure & Sustainment
- Scenario independence validated (each scenario has complete workflow)
- Validation tasks present for each scenario
- Dependencies documented

### Quality Standards

**OKR Quality:**
- Zero Key Results without baselines
- Zero KRs with unmeasurable verbs lacking quantified metrics
- All KRs have data source and measurement frequency defined

**Stakeholder Coverage:**
- 100% RACI coverage across all scenarios
- High-power/high-interest stakeholders have ≥2 engagement touchpoints
- End users (if process changes) have training AND validation tasks

**Task Completeness:**
- Every business scenario has validation tasks
- Approval workflows complete for policy/process changes
- Training delivery tasks present if >50 users affected
- Baseline measurement task if baseline unknown
- Sustainment tasks in final phase (knowledge transfer, continuous improvement)

## Governance Process

### Constitution Authority

This constitution is **NON-NEGOTIABLE** within initiative planning scope. 

**Constitution violations are automatically CRITICAL:**
- Initiative >1 quarter without breakdown → BLOCK planning
- KR not SMART-compliant → BLOCK planning
- No Accountable stakeholder → BLOCK execution
- High-risk with no mitigation → BLOCK execution

**Amendment Process:**
- Constitution changes require explicit documentation of rationale
- Amendments must be approved at Director+ level
- Transition period defined for initiatives in-flight

### Compliance Validation

**/speckit.analyze command validates:**
- OKR quality (SMART criteria)
- Initiative sizing (quarter boundary)
- Stakeholder coverage (RACI completeness)
- Baseline measurement presence
- Change management integration
- Scenario validation completeness
- Risk mitigation planning

**Runtime Guidance:**
- All commands (specify, plan, tasks) enforce constitution principles
- Agent positioned as senior business consultant ensures compliance
- Proactive breakdown recommendations when sizing limits approached

**Version**: 1.0.0 | **Ratified**: 2025-01-XX | **Last Amended**: 2025-01-XX
<!-- Updated to Business Operations OKR Planning Constitution -->
