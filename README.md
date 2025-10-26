<div align="cent## Table of Contents

- [🤔 What is Spec-Driven Operations?](#-what-is-spec-driven-operations)
- [⚡ Get Started](#-get-started)
- [🤖 Supported AI Agents](#-supported-ai-agents)
- [🔧 Specify CLI Reference](#-specify-cli-reference)
- [🔑 Key Differences from Original Spec Kit](#-key-differences-from-original-spec-kit)
- [📚 Core Philosophy](#-core-philosophy)
- [🌟 Use Cases](#-use-cases)
- [🎯 Key Features](#-key-features)
- [🔧 Prerequisites](#-prerequisites)
- [📋 Detailed Workflow](#-detailed-workflow)
- [💡 Example Initiatives](#-example-initiatives)
- [🔍 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)
- [👥 Maintainers](#-maintainers)
- [💬 Support](#-support)
- [🙏 Acknowledgments](#-acknowledgments)
- [📄 License](#-license)
src="./media/logo_small.webp" alt="Spec Kit Operations Logo"/>
    <h1>� Spec Kit Operations</h1>
    <h3><em>Plan and execute business initiatives with confidence.</em></h3>
</div>

<p align="center">
    <strong>An adaptation of GitHub's Spec Kit for business operations teams conducting OKR-driven planning and execution.</strong>
</p>

<p align="center">
    <a href="https://github.com/beliaev-maksim/spec-kit-operations/blob/new-templates/LICENSE"><img src="https://img.shields.io/github/license/beliaev-maksim/spec-kit-operations" alt="License"/></a>
</p>

---

## Table of Contents

- [🤔 What is Spec-Driven Operations?](#-what-is-spec-driven-operations)
- [⚡ Get Started](#-get-started)
- [🤖 Supported AI Agents](#-supported-ai-agents)
- [🔧 Specify CLI Reference](#-specify-cli-reference)
- [📚 Core Philosophy](#-core-philosophy)
- [🌟 Use Cases](#-use-cases)
- [🎯 Key Features](#-key-features)
- [🔧 Prerequisites](#-prerequisites)
- [ Detailed Workflow](#-detailed-workflow)
- [� Example Initiatives](#-example-initiatives)
- [👥 Maintainers](#-maintainers)
- [ License](#-license)

## 🤔 What is Spec-Driven Operations?

**Spec-Driven Operations** adapts the principles of Spec-Driven Development for business operations teams. Instead of generating code, it helps teams:

- **Plan strategic initiatives** using OKR (Objectives & Key Results) frameworks
- **Design execution strategies** with stakeholder analysis, communication plans, and change management
- **Break down work** into actionable tasks organized by business scenarios
- **Track progress** against measurable Key Results with clear success criteria
- **Apply governance** through constitutional principles that ensure quality and consistency

This approach is designed for **business functions** like Legal, HR, Sales Operations, Marketing, Finance, and Operations teams who need structured planning without software development complexity.

## ⚡ Get Started

### 1. Install Specify CLI (Local Development)

**Important**: This is a fork of the official Spec Kit. Install it locally to avoid conflicts:

```bash
# Clone this repository
git clone https://github.com/beliaev-maksim/spec-kit-operations.git
cd spec-kit-operations

# Install in development mode with uv
uv pip install -e .

# Verify installation
specify --help
```

**For development work on the CLI itself**:
```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Build package
uv build
```

### 2. Initialize Your Initiative Planning Workspace

```bash
# Create a new initiative planning workspace
specify init my-organization-okrs --ai copilot

# Or initialize in current directory
specify init . --ai claude
# or
specify init --here --ai claude
```

### 3. Set Up Organization Context

### 3. Set Up Organization Context

**Critical First Step**: Populate your organization's context before planning initiatives.

Edit `.specify/memory/organization-context.md` with your organization's information:
- Strategic priorities and executive leadership
- Organizational structure and culture
- Budget processes and approval thresholds  
- Change readiness and stakeholder landscape
- Regulatory environment and governance requirements

See [memory/README.md](memory/README.md) for detailed guidance on populating this file.

### 4. Define Governance Principles

Launch your AI assistant in the project directory and establish your organization's governance principles:

```bash
/speckit.constitution Create business governance principles focused on quarter-based delivery, OKR quality standards, stakeholder engagement requirements, change management gates, and risk mitigation planning
```

This creates `.specify/memory/constitution.md` with the governance rules that guide all initiative planning.

### 5. Plan Your First Initiative

Use the `/speckit.specify` command to describe your business initiative:

```bash
/speckit.specify Design an employee onboarding process improvement initiative. Currently, new hires take 90 days to reach full productivity. We want to reduce this to 60 days by improving the first-week experience, providing better documentation, implementing a buddy system, and creating structured 30/60/90 day check-ins. Target: 100% of new hires complete orientation within first 3 days, 80% report feeling "well-prepared" in week-1 survey.
```

### 6. Create Execution Plan

Use the `/speckit.plan` command to design your execution strategy:

```bash
/speckit.plan Focus on stakeholder engagement with HR, hiring managers, and new hires. Use surveys for baseline measurement. Communication plan should include manager training, new hire orientation materials, and feedback loops. Training needed for hiring managers on buddy system. Pilot with 2 departments before full rollout.
```

### 7. Break Down into Tasks

Use `/speckit.tasks` to create an actionable task list:

```bash
/speckit.tasks
```

### 8. Execute Initiative

Use `/speckit.implement` to track execution of all tasks according to the plan:

```bash
/speckit.implement
```

For detailed step-by-step instructions, see [Detailed Workflow](#-detailed-workflow) below.

## 🤖 Supported AI Agents

All AI agents supported by the original Spec Kit work with Spec Kit Operations:

| Agent                                                     | Support | Notes                                             |
|-----------------------------------------------------------|---------|---------------------------------------------------|
| [GitHub Copilot](https://code.visualstudio.com/)          | ✅ | Recommended for VS Code users                    |
| [Claude Code](https://www.anthropic.com/claude-code)      | ✅ | Excellent for complex business analysis          |
| [Cursor](https://cursor.sh/)                              | ✅ | Good IDE integration                             |
| [Windsurf](https://windsurf.com/)                         | ✅ | Built-in workflow support                        |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | ✅ |                                                   |
| [Qwen Code](https://github.com/QwenLM/qwen-code)          | ✅ |                                                   |
| [opencode](https://opencode.ai/)                          | ✅ |                                                   |
| [Kilo Code](https://github.com/Kilo-Org/kilocode)         | ✅ |                                                   |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview)   | ✅ |                                                   |
| [CodeBuddy CLI](https://www.codebuddy.ai/cli)             | ✅ |                                                   |
| [Roo Code](https://roocode.com/)                          | ✅ |                                                   |
| [Codex CLI](https://github.com/openai/codex)              | ✅ |                                                   |
| [Amp](https://ampcode.com/)                               | ✅ |                                                   |
| [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/) | ⚠️ | Amazon Q Developer CLI [does not support](https://github.com/aws/amazon-q-developer-cli/issues/3064) custom arguments for slash commands. |

## 🔧 Specify CLI Reference

The `specify` command supports the following options:

### Commands

| Command     | Description                                                    |
|-------------|----------------------------------------------------------------|
| `init`      | Initialize a new initiative planning workspace from templates  |
| `check`     | Check for installed tools (git and supported AI agents)        |

### `specify init` Arguments & Options

| Argument/Option        | Type     | Description                                                                  |
|------------------------|----------|------------------------------------------------------------------------------|
| `<project-name>`       | Argument | Name for your initiative workspace directory (optional if using `--here`, or use `.` for current directory) |
| `--ai`                 | Option   | AI assistant to use: `claude`, `gemini`, `copilot`, `cursor-agent`, `qwen`, `opencode`, `codex`, `windsurf`, `kilocode`, `auggie`, `roo`, `codebuddy`, `amp`, or `q` |
| `--script`             | Option   | Script variant to use: `sh` (bash/zsh) or `ps` (PowerShell)                 |
| `--ignore-agent-tools` | Flag     | Skip checks for AI agent tools                                               |
| `--no-git`             | Flag     | Skip git repository initialization                                          |
| `--here`               | Flag     | Initialize in the current directory instead of creating a new one           |
| `--force`              | Flag     | Force merge/overwrite when initializing in current directory (skip confirmation) |
| `--debug`              | Flag     | Enable detailed debug output for troubleshooting                            |

### Examples

```bash
# Initialize new workspace
specify init my-org-planning --ai copilot

# Initialize in current directory
specify init . --ai claude
# or
specify init --here --ai claude

# Force merge into non-empty directory
specify init . --force --ai copilot

# Skip git initialization
specify init my-org --ai gemini --no-git

# Check system requirements
specify check
```

### Available Slash Commands

After running `specify init`, your AI coding agent will have access to these slash commands:

#### Core Workflow Commands

| Command                  | Description                                                           |
|--------------------------|-----------------------------------------------------------------------|
| `/speckit.constitution`  | Create or update business governance principles                       |
| `/speckit.specify`       | Define business initiative with OKRs and business scenarios           |
| `/speckit.plan`          | Create execution strategy with stakeholder analysis and change management |
| `/speckit.tasks`         | Generate actionable task lists organized by business scenarios        |
| `/speckit.implement`     | Track execution of all tasks according to the plan                    |

#### Quality & Validation Commands

| Command              | Description                                                           |
|----------------------|-----------------------------------------------------------------------|
| `/speckit.clarify`   | Clarify underspecified areas (run before `/speckit.plan`)           |
| `/speckit.analyze`   | OKR quality analysis, stakeholder coverage, resource feasibility validation (run after `/speckit.tasks`) |
| `/speckit.checklist` | Generate validation checklists (OKR quality, stakeholder alignment, resource planning, risk assessment, initiative readiness) |

### Key Differences from Original Spec Kit

**Business Focus**:
- Initiatives (not features)
- Business Scenarios (not User Stories)  
- Execution Plans (not Implementation Plans)
- Deliverables: policies, training, approvals (not code)

**AI Consultant Role**:
- Positioned as senior business consultant (McKinsey/BCG/Bain caliber)
- Expertise in OKRs, change management, stakeholder engagement
- Applies SMART criteria, RACI matrices, change management frameworks

**Governance**:
- Quarter-based initiative sizing (≤13 weeks)
- SMART Key Results (non-negotiable)
- Stakeholder engagement planning (RACI required)
- Change management integration for Moderate/Transformational initiatives

## 📚 Core Philosophy

Spec-Driven Operations applies structured planning to business initiatives:

- **OKR-driven planning** where Objectives and Key Results define success before execution
- **Rich specification** using SMART criteria, RACI matrices, and change management frameworks
- **Multi-phase refinement** (specify → plan → tasks → implement) rather than ad-hoc execution
- **AI-assisted guidance** with consultant-level expertise in strategic planning and change management
- **Governance through constitution** ensuring quarter-based sizing, stakeholder engagement, and quality standards

## 🌟 Use Cases

Spec Kit Operations is designed for business operations teams across functions:

| Function | Example Initiatives |
|----------|-------------------|
| **HR** | Employee onboarding redesign, Performance review process improvement, Benefits enrollment optimization, Diversity & inclusion programs |
| **Legal** | Contract management system rollout, Compliance policy updates, Data privacy program implementation, Legal ops automation |
| **Sales Operations** | Sales commission structure redesign, CRM process improvements, Sales territory redesign, Quote-to-cash optimization |
| **Marketing** | Campaign management process, Brand guidelines rollout, Marketing automation implementation, Content workflow optimization |
| **Finance** | Budget planning process improvement, Month-end close optimization, Expense policy updates, Financial reporting automation |
| **Operations** | Process standardization initiatives, Quality improvement programs, Vendor management optimization, Operational excellence projects |

## 🎯 Key Features

### OKR Quality Framework
- **SMART Criteria Validation**: Ensures all Key Results are Specific, Measurable, Achievable, Relevant, Time-bound
- **Baseline Measurement**: Requires baseline data before execution
- **Leading vs Lagging Indicators**: Balances predictive and outcome measures

### Initiative Sizing & Breakdown
- **Quarter-Based Delivery**: Constitutional requirement for ≤13 week initiatives
- **Atomicity Assessment**: Flags initiatives needing breakdown (>5 scenarios, >20 tasks per scenario)
- **MVP Approach**: P1 scenario must deliver independent value

### Stakeholder Management
- **RACI Matrix**: Complete Responsible, Accountable, Consulted, Informed mapping
- **Power/Interest Classification**: High-power stakeholders get explicit engagement tasks
- **Engagement Strategy**: Communication touchpoints mapped to stakeholder groups

### Change Management Integration
- **Change Magnitude Assessment**: Minor / Moderate / Transformational classification
- **Organizational Readiness**: 6-dimension assessment (change fatigue, capacity, capability, culture, change history, leadership support)
- **Adoption Planning**: Training, communication, and validation activities for Moderate/Transformational changes

### Governance & Compliance
- **Constitutional Principles**: 7 non-negotiable rules (Quarter-Based Sizing, SMART KRs, Stakeholder Engagement, Baseline Measurement, Change Management, Independent Validation, Risk Mitigation)
- **Approval Gates**: Budget thresholds, policy approvals, readiness checklists
- **Quality Validation**: OKR quality, stakeholder coverage, resource feasibility checks

## 🔧 Prerequisites

- **Linux/macOS/Windows**
- [Supported AI coding agent](#-supported-ai-agents)
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

---

## 📋 Detailed Workflow

<details>
<summary>Click to expand the complete step-by-step workflow</summary>

### Step 1: Initialize Workspace

```bash
# Clone and install
git clone https://github.com/beliaev-maksim/spec-kit-operations.git
cd spec-kit-operations
uv pip install -e .

# Create workspace
specify init my-org-okrs --ai copilot
cd my-org-okrs
```

### Step 2: Populate Organization Context

**Critical**: Edit `.specify/memory/organization-context.md` with your organization's actual information:

- **Strategic Direction**: Mission, vision, current strategic priorities
- **Organizational Structure**: Executive team, functional leaders, reporting structure
- **Cultural Characteristics**: Change readiness, communication preferences, decision-making style
- **Capacity & Resources**: Headcount, budget processes, approval thresholds
- **Governance**: Regulatory environment, approval processes, risk management
- **Historical Context**: Recent initiatives, lessons learned, success patterns

See [memory/README.md](memory/README.md) for detailed guidance.

### Step 3: Establish Governance (Constitution)

Launch your AI agent in the workspace and create governance principles:

```text
/speckit.constitution Create business governance principles that enforce quarter-based initiative sizing, SMART Key Results, mandatory stakeholder RACI matrices, change management integration for moderate/transformational initiatives, baseline measurement requirements, and risk mitigation planning for high-severity risks.
```

This creates `.specify/memory/constitution.md` with 7 core principles that guide all planning.

### Step 4: Create Initiative Specification

Use `/speckit.specify` to describe your business initiative. Focus on **what** you want to achieve and **why**, using OKR language:

```text
/speckit.specify Design an employee onboarding improvement initiative for HR function. 

**Problem**: New hires currently take 90 days to reach full productivity. Exit interviews show 40% cite poor onboarding as a concern. First-week experience is inconsistent across departments.

**Objective**: Transform the employee onboarding experience to accelerate time-to-productivity and improve retention.

**Key Results**:
1. Reduce average time-to-full-productivity from 90 days to 60 days (measured by manager assessment)
2. Increase new hire "well-prepared" rating from 55% to 85% in week-1 survey
3. Achieve 95% completion of orientation checklist within first 3 days (currently 70%)
4. Reduce 90-day voluntary turnover from 12% to <8%

**Scope**:
- Redesign first-week orientation experience
- Create comprehensive onboarding documentation and resources
- Implement buddy/mentor system
- Establish structured 30/60/90-day check-in process
- Update manager training on onboarding responsibilities

**Out of Scope**: Compensation changes, benefits plan modifications, IT hardware procurement process

**Timeline**: Complete by end of Q2 2025
**Budget**: $50K-$75K (orientation materials, training development, system updates)
**Stakeholders**: HR team (lead), hiring managers (all departments), new hires (300/year), IT (systems support)
```

The AI will generate `spec.md` with:
- Strategic Context (linkage to org OKRs)
- Objective & Key Results (SMART validation)
- Business Scenarios (prioritized P1/P2/P3)
- Stakeholders (RACI matrix)
- Resources (budget, FTE, vendors)
- Risks & Dependencies
- Timeline & Milestones
- Change Management & Adoption strategy
- Success Metrics & Measurement approach

### Step 5: Clarify Specification (Optional but Recommended)

Use `/speckit.clarify` to resolve ambiguities before planning:

```text
/speckit.clarify
```

The AI will ask structured questions about:
- Strategic alignment gaps
- OKR quality issues (missing baselines, unmeasurable KRs)
- Stakeholder identification
- Resource availability
- Timeline constraints
- Risk mitigation needs

Answer questions to refine the spec. The AI records answers in a Clarifications section and integrates them into appropriate spec sections.

### Step 6: Create Execution Plan

Use `/speckit.plan` to design your execution strategy. Focus on stakeholder engagement, change management, and execution approach:

```text
/speckit.plan 

**Execution Strategy**:
- Phased rollout: Pilot with 2 departments (Sales, Engineering) in Q1, full rollout Q2
- Stakeholder engagement: Monthly steering committee (CHRO, Dept VPs), weekly working group (HR BPs, hiring managers)
- Change management: Moderate magnitude - requires training, communication plan, adoption validation

**Stakeholder Analysis**:
- Executive sponsor: CHRO (Accountable)
- Pilot departments: Sales VP and Engineering VP (Consulted, early adopters)
- All hiring managers: Responsible for execution, need training (200 managers)
- HR Business Partners: Responsible for rollout support
- New hires: Informed, provide feedback

**Baseline Measurement**:
- Current time-to-productivity: Survey managers for last 6 months of hires
- Current "well-prepared" rating: Review existing week-1 survey data  
- Current orientation completion: Audit last quarter's HR records
- Current 90-day turnover: Pull from HRIS

**Communication Plan**:
- Kickoff: All-hands announcement from CHRO (week 1)
- Manager training: 2-hour sessions, 4 cohorts over 2 weeks
- New hire communication: Updated welcome email, orientation deck
- Progress updates: Monthly email to all hiring managers
- Pilot feedback: Weekly check-ins with pilot departments

**Training Required**:
- Manager training: Buddy system, 30/60/90 check-ins, new orientation process (2 hours)
- HR BP training: Process changes, system updates (4 hours)
- Buddy training: Self-serve guide + 30-min webinar

**Success Validation**:
- Pilot assessment: 8-week pilot with 20 new hires, measure all 4 KRs
- User feedback: Manager and new hire surveys after pilot
- Go/no-go decision: Steering committee review before full rollout
```

The AI generates:
- `plan.md` - Execution strategy, timeline, resource allocation
- `stakeholder-analysis.md` - Power/Interest matrix, engagement strategies, readiness assessment
- `communication-plan.md` - Touchpoints, messages, feedback mechanisms
- `process-maps.md` - Current state, future state, SOPs (if process redesign)
- `execution-guide.md` - Phased rollout, quality gates, RACI
- `training-materials/` - Training needs analysis, curriculum outline

### Step 7: Generate Task Breakdown

Use `/speckit.tasks` to create actionable tasks organized by business scenarios:

```text
/speckit.tasks
```

The AI generates `tasks.md` with:
- **Phase 1: Initiative Setup** - Governance, kickoff, tracking setup
- **Phase 2: Foundational** - Baseline measurement, stakeholder workshops, approvals
- **Phase 3: Scenario 1 (P1)** - First-week orientation redesign tasks
- **Phase 4: Scenario 2 (P2)** - Buddy system implementation tasks  
- **Phase 5: Scenario 3 (P3)** - 30/60/90 check-in process tasks
- **Phase 6: Closure & Sustainment** - Knowledge transfer, continuous improvement

Each task follows strict format:
```
- [ ] T001 [P] [S1] Conduct manager workshops to identify first-week pain points → workshops/manager-feedback.md
- [ ] T015 [S1] Draft new orientation checklist v1 → deliverables/orientation-checklist-v1.md
- [ ] T023 [S1] Obtain CHRO approval for orientation changes → approvals/chro-orientation-approval.pdf
- [ ] T031 [S1] Deliver manager training on new orientation (Cohort 1) → training-completed/cohort1-attendance.csv
- [ ] T040 [S1] Validate: Pilot new hire survey ≥80% "well-prepared" → metrics/pilot-survey-results.md
```

### Step 8: Validate Quality (Optional but Recommended)

Use `/speckit.analyze` to validate initiative quality before execution:

```text
/speckit.analyze
```

The AI checks:
- **OKR Quality**: All KRs SMART-compliant, baselines present, measurable
- **Initiative Sizing**: Within quarter boundary, <5 scenarios, <20 tasks per scenario
- **Stakeholder Coverage**: RACI complete, high-power stakeholders have engagement tasks
- **Resource Feasibility**: Budget reasonable, capacity <80%, timeline realistic
- **Change Management**: Moderate/Transformational have readiness assessment, training, communication plan
- **Scenario Validation**: Each scenario has validation tasks, approval tasks, deliverables

Produces report with findings (CRITICAL/HIGH/MEDIUM/LOW severity) and remediation recommendations.

### Step 9: Execute Initiative

Use `/speckit.implement` to track execution:

```text
/speckit.implement
```

The AI:
- Verifies readiness checklists complete (if present)
- Loads execution context (spec, plan, stakeholder analysis, communication plan)
- Guides task execution phase-by-phase
- Tracks deliverables (documents, approvals, trained users, validated processes)
- Marks completed tasks as [X] in tasks.md
- Monitors stakeholder engagement, approval deadlines, validation tasks
- Alerts to risks materializing or timeline issues

**Note**: The AI provides execution guidance and tracking, but does not automatically "do" the work (e.g., it won't draft policy documents or schedule workshops). It helps you stay on track, marks progress, and reminds you of upcoming milestones.

### Step 10: Monitor & Measure

Throughout execution:
- Track KPI progress in `.specify/metrics/` directory
- Document decisions and changes in spec.md
- Update risks in spec.md Risks section
- Collect stakeholder feedback
- Adjust communication/training as needed

Post-execution:
- Measure final KR results
- Document lessons learned
- Update organization-context.md with initiative outcomes
- Archive initiative artifacts

</details>

---

## 💡 Example Initiatives

<details>
<summary>Click to see example initiatives across functions</summary>

### HR: Employee Engagement Program

**Objective**: Increase employee engagement and reduce voluntary turnover

**Key Results**:
1. Increase engagement score from 68% to 80% (annual survey)
2. Reduce voluntary turnover from 18% to <12%
3. Achieve 90% manager participation in monthly 1-on-1s (currently 45%)

**Business Scenarios**:
- S1 (P1): Launch manager effectiveness training program
- S2 (P2): Implement recognition and rewards platform
- S3 (P3): Establish career development framework

---

### Legal: Contract Management Process Improvement

**Objective**: Accelerate contract cycle time and reduce legal bottlenecks

**Key Results**:
1. Reduce average contract turnaround from 14 days to 7 days
2. Achieve 95% of standard contracts using approved templates
3. Reduce legal review volume by 40% through self-service portal

**Business Scenarios**:
- S1 (P1): Create and deploy 10 standard contract templates
- S2 (P2): Launch self-service contract initiation portal  
- S3 (P3): Implement contract playbook and negotiation guides

---

### Sales Operations: Commission Structure Redesign

**Objective**: Align sales compensation with strategic priorities and improve transparency

**Key Results**:
1. Increase rep satisfaction with commission plan from 3.2/5 to 4.0/5
2. Achieve <5% commission disputes (currently 18%)
3. Reduce commission calculation time from 5 days to 2 days

**Business Scenarios**:
- S1 (P1): Design new commission structure with rep input
- S2 (P2): Update systems and build commission calculator
- S3 (P3): Train reps and managers on new plan

---

### Marketing: Content Operations Workflow

**Objective**: Streamline content creation and improve quality consistency

**Key Results**:
1. Reduce average content production time from 6 weeks to 3 weeks
2. Achieve 100% content adherence to brand guidelines (currently 70%)
3. Increase content reuse rate from 15% to 40%

**Business Scenarios**:
- S1 (P1): Implement content workflow and approval tool
- S2 (P2): Create content templates and brand guideline library
- S3 (P3): Establish content governance and measurement framework

</details>

---

## 🤝 Contributing

This is a fork of GitHub's Spec Kit adapted for business operations use cases. Contributions that enhance OKR planning, stakeholder management, change management integration, or business operations workflows are welcome.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 👥 Maintainers

- Maksim Beliaev ([@beliaev-maksim](https://github.com/beliaev-maksim))
- Den Delimarsky ([@localden](https://github.com/localden))
- John Lam ([@jflam](https://github.com/jflam))

---

## 💬 Support

For support, please open a [GitHub issue](https://github.com/beliaev-maksim/spec-kit-operations/issues/new). We welcome bug reports, feature requests, and questions about using Spec-Driven Operations for business initiatives.

---

## 🙏 Acknowledgments

This project is built on [GitHub's Spec Kit](https://github.com/github/spec-kit) - an excellent foundation for specification-driven workflows. We've adapted it specifically for business operations teams conducting OKR-driven initiative planning.

Special thanks to:
- John Lam ([@jflam](https://github.com/jflam)) for the original Spec-Driven Development methodology and research
- The GitHub Spec Kit team for creating the toolkit that inspired this adaptation
- The business operations community for feedback and real-world validation

---

## 📄 License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) file for the full terms.

