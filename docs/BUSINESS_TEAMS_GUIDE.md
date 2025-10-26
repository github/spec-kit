# Spec-Kit for Business Operations Teams - Quick Start Guide

**For**: Legal, HR, Sales Ops, Marketing, Finance, Operations, and other business functions  
**Purpose**: Annual OKR planning, quarterly initiatives, and strategic project execution  
**AI Role**: Senior Business Consultant from top-tier consulting firms (McKinsey, BCG, Bain style)

---

## What is Spec-Kit?

Spec-Kit is your AI-powered business consultant that helps you:
- ✅ **Define rigorous OKRs** with SMART objectives and measurable Key Results
- ✅ **Break down complex initiatives** into achievable, incremental scenarios
- ✅ **Plan execution** with change management, stakeholder engagement, and resource allocation
- ✅ **Validate quality** of your goals using proven frameworks
- ✅ **Track progress** with clear milestones and validation criteria

Think of it as having a McKinsey consultant embedded in your workflow to ensure your initiatives are well-defined, properly sized, and set up for success.

---

## When to Use Spec-Kit

### ✅ Perfect For:
- Annual OKR planning and quarterly goal setting
- Large cross-functional business initiatives
- Process improvement projects
- Policy or compliance updates
- Organizational change programs
- Training and enablement initiatives
- System rollouts or tool implementations (business perspective)
- Department-level transformations

### ❌ Not Designed For:
- Day-to-day operational tasks
- Simple one-off activities
- Pure technical/engineering projects (use original spec-kit)
- Already well-defined, small-scope work

---

## The Spec-Kit Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. SPECIFY                                                      │
│  Describe your initiative → AI generates rigorous spec           │
│  Output: Initiative spec with OKRs, scenarios, stakeholders      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  2. CLARIFY (optional)                                           │
│  AI asks targeted questions → You provide answers                │
│  Output: Refined spec with ambiguities resolved                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  3. ANALYZE (recommended)                                        │
│  AI validates quality → Identifies gaps/risks                    │
│  Output: Quality report with recommendations                     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  4. PLAN                                                         │
│  AI creates execution plan → Stakeholders + change mgmt          │
│  Output: Execution plan with timeline, resources, training       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  5. TASKS                                                        │
│  AI breaks down into actions → Workshops, docs, approvals        │
│  Output: Detailed task list organized by scenario                │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  6. IMPLEMENT                                                    │
│  Execute tasks → Track progress → Validate outcomes              │
│  Output: Completed initiative with measured KRs                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step: Your First Initiative

### Step 1: Define Your Initiative (`/speckit.specify`)

**What you do**: Describe your goal or initiative in plain English

**Example inputs**:
```
"We need to reduce employee onboarding time from 45 days to 30 days and 
improve new hire satisfaction scores"

"Implement a quarterly business review process for the sales team that 
improves forecast accuracy by 20%"

"Ensure GDPR compliance across all customer data touchpoints by Q2"

"Launch a customer feedback program to increase NPS from 45 to 60"
```

**What the AI does**:
1. Analyzes your description for key concepts
2. Creates a short name for the initiative (e.g., "employee-onboarding-q2")
3. Generates a comprehensive specification with:
   - ✅ **SMART Objective**: Clear, measurable, time-bound goal
   - ✅ **Key Results**: 3-5 quantified outcomes with baselines and targets
   - ✅ **Business Scenarios**: Prioritized (P1, P2, P3) incremental deliverables
   - ✅ **Initiative Sizing**: Assessment if it's achievable in one quarter
   - ✅ **Stakeholders**: RACI mapping and engagement plan
   - ✅ **Resources**: Budget, team, timeline breakdown
   - ✅ **Success Validation**: Leading and lagging indicators
   - ✅ **Change Management**: Training plan and adoption strategy

**AI Quality Checks**:
- ❌ Rejects vague goals → ✅ Pushes for specific, measurable outcomes
- ❌ Flags oversized initiatives → ✅ Recommends breakdown into phases
- ❌ Identifies missing baselines → ✅ Requires "from X to Y" format
- ❌ Catches activity-based KRs → ✅ Converts to outcome-based KRs

**Example output snippet**:
```markdown
## Objective
Reduce time-to-productivity for new hires while improving their 
onboarding experience to increase retention and early engagement.

**SMART Validation**:
- Specific: ✅ Targets onboarding process efficiency and satisfaction
- Measurable: ✅ Time in days and satisfaction scores
- Achievable: ✅ 33% reduction is ambitious but realistic
- Relevant: ✅ Addresses retention and hiring ROI
- Time-bound: ✅ Q2 2024 deadline

## Key Results
- KR-001: Reduce average onboarding time from 45 days to 30 days 
  (-33%) by June 30, 2024
- KR-002: Increase new hire satisfaction score from 6.5 to 8.5 
  (out of 10) by Q2 end
- KR-003: Achieve 95% onboarding checklist completion rate 
  (from current 75%) within first 30 days
```

---

### Step 2: Clarify Ambiguities (`/speckit.clarify`) - OPTIONAL

**When to use**: If the AI marked things as [NEEDS CLARIFICATION] in your spec

**What the AI does**:
1. Asks up to 5 targeted questions about:
   - Scope boundaries (which departments? which processes?)
   - Budget constraints
   - Timeline expectations
   - Success metrics
   - Stakeholder authority
2. Provides **recommended answers** based on best practices
3. You can accept recommendations or provide your own answers
4. Integrates answers back into the spec

**Example interaction**:
```
AI: Question 1: Initiative Scope

**Recommended:** Start with 2-3 pilot departments, then expand company-wide 
in Q3 - This reduces risk and allows for iteration based on learnings.

| Option | Description |
|--------|-------------|
| A | Pilot with 2-3 departments in Q2, expand in Q3 (RECOMMENDED) |
| B | Full company-wide rollout in Q2 (higher risk) |
| C | Single department pilot in Q2, gradual expansion through Q3-Q4 |
| Custom | Provide your own approach (<=5 words) |

You: A

AI: ✅ Updated spec with pilot approach. Moving to next question...
```

---

### Step 3: Validate Quality (`/speckit.analyze`) - RECOMMENDED

**What the AI does**:
1. Checks your spec against quality frameworks:
   - ✅ SMART criteria for objectives
   - ✅ Key Results have baselines, targets, deadlines
   - ✅ Business scenarios are independently validatable
   - ✅ Initiative sizing is realistic
   - ✅ Stakeholders are comprehensively mapped
   - ✅ Resources are identified and realistic
   - ✅ Success metrics are measurable
2. Generates a quality report with:
   - ✅ Items that pass
   - ⚠️ Items that need attention
   - ❌ Critical issues that must be fixed
3. Provides specific recommendations for improvements

**Example output**:
```
## Analysis Report

### ✅ Strengths
- Objective is SMART compliant
- Key Results have clear baselines and targets
- Stakeholder mapping is comprehensive

### ⚠️ Warnings
- KR-002 "satisfaction score" needs defined measurement method
  → RECOMMEND: Add "via monthly new hire survey with 80% response rate"
  
- Scenario 2 timeline (8 weeks) is tight given 4 team dependencies
  → RECOMMEND: Extend to 10 weeks or reduce scope

### ❌ Critical Issues
- No Change Management section completed
  → REQUIRED: Define training approach for hiring managers
  → REQUIRED: Document resistance mitigation strategy
```

---

### Step 4: Create Execution Plan (`/speckit.plan`)

**What the AI does**:
1. **Phase 0 - Stakeholder Analysis**:
   - Maps all affected stakeholders
   - Assesses organizational readiness
   - Identifies dependencies and risks
   - Gathers baseline data
2. **Phase 1 - Execution Planning**:
   - Creates process maps (if relevant)
   - Develops communication plan
   - Designs training materials
   - Establishes measurement framework
   - Builds execution guide

**Example outputs**:
- `stakeholder-analysis.md`: Power/interest matrix, engagement strategies
- `communication-plan.md`: Who, what, when, how for all communications
- `execution-guide.md`: Phased rollout plan with gates and milestones
- `training-materials/`: Training plans and enablement content
- `process-maps.md`: Current state → Future state (if process change)

---

### Step 5: Generate Action Items (`/speckit.tasks`)

**What the AI does**:
Breaks initiative into specific business tasks organized by scenario:

**Task Types**:
- 📋 **Planning & Design**: Requirements workshops, process design, documentation
- 💬 **Communication**: Town halls, stakeholder meetings, feedback sessions
- 📄 **Documentation**: Policy drafting, procedure writing, approval workflows
- 🎓 **Training**: Material creation, training delivery, enablement
- 🚀 **Rollout**: Pilots, go-live activities, adoption monitoring
- ✅ **Validation**: Metrics collection, surveys, retrospectives

**Example task list**:
```markdown
## Phase 2: Foundational Activities
- [ ] T006 Conduct stakeholder workshop to validate current state
- [ ] T007 [P] Complete baseline data collection for all Key Results
- [ ] T008 [P] Secure budget approval from Finance

## Phase 3: Scenario 1 - Streamline Paperwork (P1)
- [ ] T013 [P] [S1] Conduct working session with HR and IT teams
- [ ] T014 [S1] Create simplified onboarding checklist
- [ ] T015 [S1] Draft updated policy document
- [ ] T017 [P] [S1] Create communication materials for managers
- [ ] T018 [S1] Conduct training session for hiring managers
- [ ] T021 [S1] Obtain approval from CHRO
- [ ] T025 [S1] Launch pilot with Engineering and Marketing depts
- [ ] T031 [P] [S1] Collect adoption metrics
```

**[P] = Parallelizable**: Tasks can run simultaneously  
**[S1] = Scenario**: Maps to Business Scenario 1 from spec

---

### Step 6: Execute (`/speckit.implement`)

**What the AI does**:
1. Guides you through executing each task
2. Tracks progress and completion
3. Validates outcomes against success criteria
4. Helps you pivot if needed based on feedback

**Execution flow**:
```
Setup → Foundational → Scenario 1 → Validate → Scenario 2 → 
Validate → Scenario 3 → Validate → Closure & Sustainment
```

**Each scenario is validated independently before moving to the next**

---

## Key Concepts Explained

### 🎯 OKRs (Objectives & Key Results)

**Objective**: Inspirational "what" - where you want to go
- Should be ambitious but achievable
- Qualitative and directional
- Time-bound (typically quarterly or annually)

**Key Results**: Measurable "how" - how you'll know you got there
- Must be quantifiable (numbers, percentages, scores)
- Need baseline (from X...) and target (...to Y)
- Need deadline (by [date])
- Should be outcome-focused (impact, not activity)

**Example**:
```
Objective: Transform our customer support into a world-class experience

Key Results:
- KR1: Increase CSAT from 72% to 88% (+16 pts) by Dec 31
- KR2: Reduce average response time from 4 hours to 1 hour by Dec 31
- KR3: Achieve 95% first-contact resolution rate (from 68%) by Dec 31
```

---

### 📊 Business Scenarios (Incremental Value Delivery)

Think of scenarios as "chapters" in your initiative story. Each chapter:
- ✅ Delivers standalone value
- ✅ Can be validated independently
- ✅ Takes 4-8 weeks to complete
- ✅ Builds upon (but doesn't depend on) previous scenarios

**Priority Levels**:
- **P1 (Critical)**: Must-have for success, highest impact, enables others
- **P2 (Important)**: Significant value, but initiative can proceed without it initially
- **P3 (Nice-to-have)**: Enhancement, lowest priority, often deferred

**Example**:
```
Initiative: Improve customer onboarding

Scenario 1 (P1): Simplify registration process
→ Value: Reduces friction, increases completion rate
→ Validation: Registration completion rate increases from 65% to 85%

Scenario 2 (P2): Add interactive product tour
→ Value: Reduces time-to-value for new customers
→ Validation: Time to first valuable action reduces from 14 days to 7 days

Scenario 3 (P3): Build customer community forum
→ Value: Enables peer-to-peer support and engagement
→ Validation: 30% of new customers engage in forum within 30 days
```

If you only complete P1, you still deliver measurable value!

---

### 📏 Initiative Sizing & Atomicity

**Well-Sized Initiative** (achievable in one quarter):
- ✅ 3-5 Key Results
- ✅ 5 or fewer cross-functional teams involved
- ✅ Clear ownership and decision authority
- ✅ Timeline: 8-12 weeks
- ✅ Realistic resource requirements

**Red Flags** (initiative too large, needs breakdown):
- ❌ More than 5 Key Results
- ❌ 6+ team dependencies
- ❌ Vague timeline ("this year")
- ❌ Words like "transform," "overhaul," "revolutionize"
- ❌ Requires organizational restructuring

**The AI will proactively recommend breaking down large initiatives into phases**

---

### 🔄 Change Management Essentials

Every initiative that changes how people work needs:
1. **Impact Assessment**: What's changing? Who's affected? How much?
2. **Communication Plan**: Who needs to know what, when, and how?
3. **Training & Enablement**: What skills/knowledge gaps exist? How to close them?
4. **Adoption Strategy**: How to drive usage and sustained behavior change?
5. **Resistance Management**: What pushback to expect? How to address?

**The AI builds this into your spec and plan automatically**

---

## Tips for Success

### ✅ Do's

1. **Be specific in your initial description**
   - ✅ "Reduce customer churn from 15% to 10% by Q4"
   - ❌ "Improve customer retention"

2. **Trust the AI's recommendations**
   - The AI applies best practices from top consulting firms
   - If it suggests breaking down an initiative, there's a good reason

3. **Validate early and often**
   - Use `/speckit.analyze` before planning
   - Review with stakeholders after spec generation

4. **Think incrementally**
   - Embrace the P1/P2/P3 scenario model
   - Deliver value early, learn, adjust

5. **Don't skip change management**
   - Even "small" changes need communication and training
   - Adoption is where most initiatives fail

### ❌ Don'ts

1. **Don't be vague**
   - ❌ "Make things better"
   - ❌ "Improve efficiency"
   - ✅ Always include: what, by how much, by when

2. **Don't skip baselines**
   - ❌ "Achieve 90% satisfaction"
   - ✅ "Increase satisfaction from 72% to 90%"

3. **Don't ignore sizing warnings**
   - If AI says "this is too large," listen
   - Oversized initiatives rarely succeed in one quarter

4. **Don't use jargon**
   - Write for cross-functional teams
   - Everyone should understand your spec

5. **Don't skip stakeholder mapping**
   - Forgotten stakeholders become blockers later
   - RACI early prevents confusion later

---

## Function-Specific Examples

### 💼 HR: Employee Engagement Initiative
```bash
/speckit.specify "Launch employee engagement program to increase 
engagement scores from 6.2 to 7.5 and reduce voluntary turnover from 
18% to 12% by end of year"
```

### ⚖️ Legal: Compliance Initiative
```bash
/speckit.specify "Achieve SOC 2 Type II compliance certification by Q3, 
including gap remediation and audit readiness across all systems"
```

### 📈 Sales Ops: CRM Optimization
```bash
/speckit.specify "Improve CRM data quality and sales team adoption from 
60% to 90%, enabling more accurate forecasting with 85% accuracy"
```

### 🎨 Marketing: Campaign Effectiveness
```bash
/speckit.specify "Increase marketing qualified lead (MQL) to sales 
qualified lead (SQL) conversion rate from 25% to 40% through improved 
lead scoring and nurturing"
```

### 💰 Finance: Budget Process Improvement
```bash
/speckit.specify "Streamline annual budget planning process, reducing 
cycle time from 8 weeks to 5 weeks while increasing stakeholder 
satisfaction from 65% to 85%"
```

---

## Getting Help

### Built-in Guidance
- Every template has inline comments with examples
- The AI will explain its recommendations
- Use `/speckit.analyze` to get quality feedback

### Common Questions

**Q: How specific should my initial description be?**  
A: Include: what you want to achieve, current baseline (if known), desired outcome, and timeline. The AI will fill in gaps and ask clarifying questions.

**Q: What if the AI creates too large of an initiative?**  
A: The AI should proactively detect this and recommend breakdown. If not, use the "Initiative Sizing" section to identify red flags.

**Q: Can I modify the generated spec?**  
A: Yes! The AI generates a starting point. Edit freely, then re-run `/speckit.analyze` to validate your changes.

**Q: How do I know if my KRs are good?**  
A: Use `/speckit.analyze`. It checks: quantifiable, baseline, target, deadline, outcome-focused, measurable.

**Q: What if I don't have baselines?**  
A: The AI will recommend gathering baselines in the "Foundational Activities" phase of your tasks.

---

## Success Stories (Example Scenarios)

### Scenario 1: HR Onboarding Transformation
**Before Spec-Kit**: Vague goal "improve onboarding"  
**After Spec-Kit**: 
- Specific KRs: Time from 45d→30d, satisfaction 6.5→8.5, completion 75%→95%
- 3 scenarios: P1 (paperwork), P2 (buddy program), P3 (automation)
- Change management plan for hiring managers
- Result: P1 delivered in 6 weeks, 35% time reduction achieved

### Scenario 2: Sales Ops CRM Adoption
**Before Spec-Kit**: "Get the team to use CRM more"  
**After Spec-Kit**:
- Specific KRs: Adoption 60%→90%, data quality 70%→95%, forecast accuracy +15%
- 3 scenarios: P1 (mandatory fields), P2 (training), P3 (automation)
- Training curriculum for 120 sales reps
- Result: 87% adoption in 10 weeks, forecast accuracy improved

---

## Glossary

- **OKR**: Objectives and Key Results - Goal-setting framework
- **SMART**: Specific, Measurable, Achievable, Relevant, Time-bound
- **KPI**: Key Performance Indicator - Metric that matters
- **RACI**: Responsible, Accountable, Consulted, Informed - Stakeholder framework
- **P1/P2/P3**: Priority levels for scenarios (Critical/Important/Nice-to-have)
- **MVP**: Minimum Viable Product - Smallest thing that delivers value
- **Change Management**: Structured approach to transitioning individuals and teams
- **Baseline**: Current state measurement (the "from" in "from X to Y")
- **Target**: Desired future state (the "to" in "from X to Y")
- **Leading Indicator**: Metric that predicts future success (measured during initiative)
- **Lagging Indicator**: Metric that confirms success (measured after initiative)

---

**Next Steps**: Run your first `/speckit.specify` command with your initiative description!

**Questions?** The AI consultant is here to help - just ask!
