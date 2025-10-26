# Memory Directory

This directory contains **persistent context** that guides initiative planning across the organization.

---

## Files in This Directory

### 📋 constitution.md
**Purpose**: Defines **NON-NEGOTIABLE governance principles** for initiative planning

**Contains**:
- 7 core principles (Quarter-Based Sizing, SMART KRs, Stakeholder Engagement, Baseline Measurement, Change Management, Independent Validation, Risk Mitigation)
- Quality standards (OKR quality, stakeholder coverage, task completeness)
- Governance process (approval gates, compliance validation)

**When to Update**: Rarely - only when governance rules themselves need to change (requires Director+ approval)

**Used By**: 
- `/speckit.analyze` - validates compliance with all principles
- All commands - enforce governance rules during planning

---

### 🏢 organization-context.md
**Purpose**: Provides **environmental context** about the organization to inform initiative planning

**Contains**:
- Strategic direction (mission, vision, priorities)
- Organizational structure (leaders, reporting, culture)
- Capacity constraints (headcount, budget, systems)
- Governance & compliance (regulatory environment, approval processes)
- Historical context (recent initiatives, lessons learned)
- Stakeholder landscape (power dynamics, common concerns)
- Industry & competitive context

**When to Update**: 
- ✅ Quarterly (at OKR setting time)
- ✅ After major organizational changes (reorg, leadership change, M&A)
- ✅ After completing major initiatives
- ✅ When strategic priorities shift

**Used By**:
- `/speckit.specify` - tailor initiative to organizational realities (strategic priorities, stakeholders, constraints)
- `/speckit.plan` - design stakeholder engagement and change management based on culture and readiness
- `/speckit.clarify` - ask questions appropriate to decision-making culture and approval processes
- `/speckit.analyze` - validate feasibility against capacity constraints and regulatory requirements

---

## Key Distinction

| Aspect | constitution.md | organization-context.md |
|--------|----------------|------------------------|
| **What** | Governance rules | Environmental information |
| **Nature** | Prescriptive ("must do") | Descriptive ("here's reality") |
| **Stability** | Stable (rarely changes) | Dynamic (quarterly updates) |
| **Scope** | Universal principles | Organization-specific context |
| **Examples** | "All KRs must be SMART" | "CFO prefers data-driven proposals, typical approval takes 2 weeks" |
| **Violations** | Block planning/execution | Inform recommendations |

---

## How They Work Together

**Example 1: Stakeholder Engagement**

- **Constitution** (Rule): "Every initiative MUST have complete stakeholder analysis with RACI matrix before execution"
- **Organization Context** (Reality): "Executive Leadership includes CEO Jane Smith (data-driven, fast decision-maker), CFO John Doe (risk-averse, requires 3 budget reviews), COO Sarah Lee (change champion, prefers pilot approaches)"
- **AI Consultant** (Application): "Your RACI matrix must include Jane as Accountable (she'll decide quickly once presented data), John as Consulted (plan for 3 review cycles with financial analysis), and Sarah as Responsible (she can drive execution and will advocate for phased rollout)"

**Example 2: Timeline Planning**

- **Constitution** (Rule): "Every initiative MUST be executable within one fiscal quarter (≤13 weeks)"
- **Organization Context** (Reality): "Blackout periods: Year-end close (Dec 15-Jan 15), Annual sales kickoff (Jan 20-25), Peak season (Nov 1-Dec 31)"
- **AI Consultant** (Application): "Your Q4 initiative must account for the peak season blackout and year-end close. Consider: Q4 = Planning & Approval (Oct-Nov), Q1 = Execution (Feb-Mar to avoid Jan blackouts), or delay until Q1 with faster execution timeline"

**Example 3: Change Management**

- **Constitution** (Rule): "Initiatives with Moderate or Transformational change magnitude MUST include change management activities"
- **Organization Context** (Reality): "Change Readiness: Medium - recent reorg 6 months ago created change fatigue. Communication Preference: Email for formal comms, Slack for updates, town halls for major changes. Change Champions: Sarah Lee (COO), Michael Chen (HR Director)"
- **AI Consultant** (Application): "Your initiative is Moderate change. Given recent change fatigue, recommend: 1) Extra emphasis on 'why now' messaging, 2) Leverage Sarah and Michael as visible champions in town halls, 3) Use Slack for frequent, transparent progress updates to build trust, 4) Consider extending adoption phase by 2 weeks for extra training support"

---

## Setup Instructions

### Initial Setup (One-Time)

1. **Review constitution.md**: Ensure the 7 core principles align with your organization's governance philosophy. Modify only if necessary (requires senior approval).

2. **Populate organization-context.md**: Fill in all sections with your organization's actual information:
   - Strategic priorities from your strategic plan
   - Leadership names and characteristics from org chart
   - Culture observations from employee surveys or leadership assessment
   - Budget thresholds from finance policies
   - Recent initiative history from project archives
   - Stakeholder dynamics from organizational knowledge

3. **Establish ownership**: Assign a person/role to maintain organization-context.md (typically Chief of Staff, Strategy Director, or OKR Program Lead)

4. **Create update cadence**: Add quarterly calendar reminders to review and update organization-context.md

### Ongoing Maintenance

**Every Quarter (at OKR Planning Time)**:
- [ ] Update Strategic Priorities if they've shifted
- [ ] Review and update Capacity & Resource Constraints (headcount, open positions, change capacity)
- [ ] Add completed initiatives to Historical Context
- [ ] Update Busy Seasons / Blackout Periods for upcoming quarters
- [ ] Verify leadership roster (any changes in Organizational Structure section)

**After Major Events**:
- [ ] Leadership change → Update Organizational Structure and Power Dynamics
- [ ] Reorganization → Update Organizational Structure, potentially Cultural Characteristics
- [ ] Major initiative completion → Add to Historical Context with lessons learned
- [ ] Merger/Acquisition → Major rewrite of most sections
- [ ] Strategic pivot → Update Strategic Direction section

**Annual Review**:
- [ ] Comprehensive review of all sections
- [ ] Update Industry & Competitive Context
- [ ] Refresh Benchmarking data
- [ ] Validate all information is still current and accurate

---

## FAQ

**Q: Should I put project-specific information in these files?**
**A**: No. These files are for **organization-wide** context. Project-specific information belongs in the initiative's own `.specify/` directory (spec.md, plan.md, tasks.md, etc.)

**Q: What if my organization doesn't have some of the information requested in organization-context.md?**
**A**: That's OK! Document what you know and mark sections as "[To be determined]" or "[Information not available]". The AI will ask clarifying questions when planning initiatives in areas with missing context.

**Q: Can I add custom sections to organization-context.md?**
**A**: Absolutely! The template is a starting point. Add sections that are relevant to your organization (e.g., "Union Relations", "International Considerations", "Technical Debt Context", etc.)

**Q: Should constitution.md and organization-context.md be version controlled?**
**A**: Yes! Keep them in your repository (this `/memory/` directory) so changes are tracked and can be reviewed. Consider requiring pull request review for changes to constitution.md.

**Q: How does the AI know to reference these files?**
**A**: The command files (specify.md, plan.md, etc.) and agent-file-template.md are configured to load and reference these files. The AI is instructed to consult organization-context.md before making recommendations.

---

## Examples of Good Organization Context

See the full template in `organization-context.md` for detailed examples, but here are some "good" vs "bad" entries:

**Strategic Priorities** ✅ Good:
> **Priority 1: Customer Experience Excellence** - Increase NPS from 42 to 60 by EOY. Executive sponsor: COO Sarah Lee. All initiatives should demonstrate customer impact.

❌ Bad:
> Priority 1: Make customers happy

**Cultural Characteristics** ✅ Good:
> **Change Readiness: Medium** - Successfully implemented new HRIS in Q2 2024 with 85% adoption in 6 weeks. However, recent reorg (Q4 2024) created change fatigue - expect 20% longer adoption timelines for next 2 quarters. Change Champions: Sarah Lee (COO), Michael Chen (HR Director) have strong track records.

❌ Bad:
> Change Readiness: We're good at change usually

**Budget Approval Thresholds** ✅ Good:
> - <$25K: Department head approval, 1-2 weeks
> - $25K-$100K: VP approval + Finance review, 3-4 weeks  
> - >$100K: CFO approval + Executive Committee review, 6-8 weeks, board notification if >$500K

❌ Bad:
> CFO approves big budgets

---

**Last Updated**: [Date]
**Owner**: [Name/Role]
