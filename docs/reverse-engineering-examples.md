# Reverse Engineering Examples & Prompt Suggestions

This document provides example prompts and workflows for using the reverse engineering feature effectively.

---

## Table of Contents

- [Quick Start Prompts](#quick-start-prompts)
- [Analysis Scope Examples](#analysis-scope-examples)
- [Using Generated Artifacts](#using-generated-artifacts)
- [Inline Upgrade Workflow](#inline-upgrade-workflow)
- [Greenfield Rewrite Workflow](#greenfield-rewrite-workflow)
- [Hybrid Approach Workflow](#hybrid-approach-workflow)

---

## Quick Start Prompts

### Comprehensive Analysis

**Prompt**:
```
I have an existing Node.js project at /home/user/my-legacy-app that I want to modernize. Please analyze it comprehensively and provide recommendations on whether to upgrade in place or start fresh.

/speckit.analyze-project

When prompted, use:
- PROJECT_PATH: /home/user/my-legacy-app
- ANALYSIS_DEPTH: STANDARD
- FOCUS_AREAS: ALL
```

**What happens**:
- Agent scans entire codebase
- Analyzes dependencies, code quality, architecture
- Generates comprehensive report with recommendation
- Provides feasibility scores

---

### Security-Focused Analysis

**Prompt**:
```
I need to assess security vulnerabilities in my Python Django application before our compliance audit.

/speckit.analyze-project

Settings:
- PROJECT_PATH: /var/www/django-app
- ANALYSIS_DEPTH: COMPREHENSIVE
- FOCUS_AREAS: SECURITY
```

**What happens**:
- Deep security scan
- CVE analysis of all dependencies
- Code pattern analysis for security anti-patterns
- Prioritized remediation list

---

### Quick Health Check

**Prompt**:
```
I want a quick sanity check on our React frontend to see if there are any critical issues.

/speckit.analyze-project

Use QUICK depth, focus on DEPENDENCIES and SECURITY.
PROJECT_PATH: ./frontend
```

**What happens**:
- 30-minute rapid scan
- Critical vulnerabilities identified
- Outdated dependencies flagged
- Executive summary only

---

## Analysis Scope Examples

### Focus Area: Architecture

**Prompt**:
```
Our team is planning a major refactoring. I want to understand the current architecture quality and get suggestions for improvements.

/speckit.analyze-project
PROJECT_PATH: /workspace/api-server
ANALYSIS_DEPTH: COMPREHENSIVE
FOCUS_AREAS: ARCHITECTURE
```

**Output includes**:
- Architecture pattern identification (MVC, layered, microservices)
- Component coupling analysis
- Separation of concerns assessment
- Refactoring recommendations
- Architecture modernization roadmap

---

### Focus Area: Performance

**Prompt**:
```
Our application has performance issues. Users are complaining about slow page loads. Please analyze and identify bottlenecks.

/speckit.analyze-project
PROJECT_PATH: /app
ANALYSIS_DEPTH: COMPREHENSIVE
FOCUS_AREAS: PERFORMANCE
```

**Output includes**:
- Performance metrics (if available from logs)
- Identified bottlenecks
- Database query analysis
- Bundle size analysis (frontend)
- Optimization recommendations (quick wins + long-term)

---

### Focus Area: Dependencies Only

**Prompt**:
```
I just want to understand our dependency health - what's outdated, what's vulnerable, what needs urgent attention.

/speckit.analyze-project
PROJECT_PATH: .
ANALYSIS_DEPTH: QUICK
FOCUS_AREAS: DEPENDENCIES
```

**Output includes**:
- Outdated dependencies table
- Vulnerable dependencies (CVEs)
- Deprecated packages
- Upgrade priority list

---

## Using Generated Artifacts

### Using recommended-constitution.md

**Scenario**: Analysis recommended greenfield rewrite

**Workflow**:

1. **Review the generated constitution**:
   ```bash
   cat .analysis/MyApp-2025-11-06/recommended-constitution.md
   ```

2. **Use it to start new project**:
   ```
   I want to create a new modern version of MyApp based on the analysis.

   /speckit.constitution

   Please use the principles from .analysis/MyApp-2025-11-06/recommended-constitution.md as the foundation. These were derived from analyzing the existing codebase to preserve good patterns and eliminate anti-patterns.

   Specifically, keep these principles:
   - [List key principles from the document]
   - [Add any additional project-specific principles]
   ```

3. **Create spec based on reverse-engineered requirements**:
   ```
   /speckit.specify

   Based on the analysis report at .analysis/MyApp-2025-11-06/analysis-report.md, the existing application provides these capabilities:

   [Copy relevant functional requirements from analysis report]

   Create a specification for a modern version that:
   1. Preserves all existing functionality
   2. Addresses the technical debt identified
   3. Follows the constitution principles we just established
   ```

---

### Using upgrade-plan.md

**Scenario**: Analysis recommended inline upgrade

**Workflow**:

1. **Review the upgrade plan**:
   ```bash
   cat .analysis/MyApp-2025-11-06/upgrade-plan.md
   ```

2. **Start Phase 0 (Preparation)**:
   ```
   I'm ready to start the upgrade process. Let's begin with Phase 0: Preparation & Baseline from the upgrade plan.

   Please help me:
   1. Create the feature branch: upgrade/node-18-react-18
   2. Capture current test coverage metrics
   3. Document current behavior by running the test suite
   4. Set up performance baseline measurements
   ```

3. **Execute Phase 1**:
   ```
   Phase 0 is complete. Let's move to Phase 1: Runtime/Platform Upgrade.

   According to the upgrade plan, we need to:
   1. Upgrade Node.js from 14.x to 18.x
   2. Update .nvmrc file
   3. Update CI/CD configuration
   4. Address the breaking changes listed in the plan

   Let's start with step 1. Please update the Node.js version.
   ```

4. **Continue through phases**:
   ```
   Phase [N] validation complete. Let's proceed to Phase [N+1]: [Phase Name].

   Please execute the steps from the upgrade plan and validate at each checkpoint.
   ```

---

## Inline Upgrade Workflow

### Complete Example: Upgrading Node.js + React App

**Step 1: Initial Analysis**

```
I have a Node.js 14 + React 16 application that needs upgrading. Node 14 is EOL and we want React 18's concurrent features.

/speckit.analyze-project
PROJECT_PATH: /home/user/my-app
ANALYSIS_DEPTH: STANDARD
FOCUS_AREAS: ALL
```

**Step 2: Review Recommendation**

```
Please summarize the key findings from the analysis:
1. What's the overall health score?
2. What's the recommendation (inline/greenfield/hybrid)?
3. What are the critical immediate actions?
4. What's the estimated effort for the upgrade?
```

**Step 3: Fix Critical Issues First**

```
Before starting the main upgrade, let's fix the critical security vulnerabilities identified:

1. CVE-2021-XXXXX in lodash
2. CVE-2022-YYYYY in axios

Please upgrade these packages to the safe versions listed in the analysis report.
```

**Step 4: Execute Upgrade Plan - Phase by Phase**

```
Let's follow the upgrade plan. Starting with Phase 0:

1. Create branch: upgrade/node18-react18
2. Capture baseline metrics (run npm test -- --coverage)
3. Document current performance (run npm run build and note bundle size)
```

Then continue:

```
Phase 0 complete. Moving to Phase 1: Node.js Upgrade

According to the plan:
- Update Node.js 14 → 16 → 18
- Update package.json engines field
- Update .nvmrc
- Update GitHub Actions workflow
- Address breaking changes (list from plan)

Let's execute these steps one by one.
```

**Step 5: Validation**

```
After each phase, please:
1. Run the full test suite
2. Run the linter
3. Build the application
4. Check for any warnings or errors

If all pass, mark Phase [N] complete and we'll proceed to Phase [N+1].
```

**Step 6: Deployment**

```
All phases complete. Now let's deploy:

1. Deploy to staging environment
2. Run smoke tests
3. If staging looks good, deploy to production using blue-green strategy
4. Monitor for 24 hours

Please help me execute the deployment checklist from the upgrade plan.
```

---

## Greenfield Rewrite Workflow

### Complete Example: Rewriting Legacy Java Monolith

**Step 1: Analysis**

```
We have a 10-year-old Java monolith that's becoming unmaintainable. I want to assess whether we should upgrade it or rewrite it.

/speckit.analyze-project
PROJECT_PATH: /opt/legacy-monolith
ANALYSIS_DEPTH: COMPREHENSIVE
FOCUS_AREAS: ALL
```

**Step 2: Review Recommendation**

```
Based on the analysis:
- Inline feasibility: 32/100 (not recommended)
- Greenfield feasibility: 78/100 (recommended)

The report recommends a greenfield rewrite. Let's plan this carefully.
```

**Step 3: Extract Requirements**

```
Let's use the analysis to understand what the current system does.

Please review the analysis report and extract:
1. All functional capabilities (what features exist)
2. All user personas (who uses the system)
3. All integrations (what external systems it connects to)
4. All business rules (critical logic that must be preserved)

Create a comprehensive list.
```

**Step 4: Create Constitution**

```
/speckit.constitution

Based on the recommended constitution at .analysis/LegacyMonolith-2025-11-06/recommended-constitution.md:

Let's establish these principles for the new system:

1. Code Quality: Single Responsibility Principle
   - Current system has god classes (found in analysis)
   - New system must avoid this

2. Testing: Test-Driven Development
   - Current system has 0% coverage (critical gap)
   - New system must have 80%+ coverage

3. Architecture: Clean Architecture with DDD
   - Current system has tight coupling (found in analysis)
   - New system must have clear boundaries

[Continue with remaining principles from recommended-constitution.md]
```

**Step 5: Create Specification**

```
/speckit.specify

Based on the reverse-engineered requirements from the analysis:

The system is an order management platform that:

USER STORIES:
[Extracted from analysis of existing functionality]

US1: As a sales rep, I can create customer orders
US2: As a warehouse manager, I can view pending orders
US3: As a customer, I can track my order status

FUNCTIONAL REQUIREMENTS:
[Derived from analyzing the codebase]

FR1: System must support multiple payment methods (Credit Card, PayPal, Invoice)
FR2: System must integrate with SAP for inventory
FR3: System must generate PDF invoices

[Continue with all requirements from analysis]
```

**Step 6: Create Plan with Modern Stack**

```
/speckit.plan

Technology Stack for the new system:

Backend:
- Java 21 (current LTS)
- Spring Boot 3.2
- PostgreSQL 15
- Redis for caching
- Kafka for events

Frontend:
- React 18
- TypeScript 5
- Vite
- TanStack Query

Infrastructure:
- Docker + Kubernetes
- GitHub Actions for CI/CD
- Terraform for IaC

Architecture:
- Microservices (bounded contexts from DDD)
- Event-driven where appropriate
- API-first design (OpenAPI spec)
```

**Step 7: Implement Using Strangler Fig**

```
Let's use the Strangler Fig pattern to migrate incrementally:

Phase 1: Authentication Service (2 weeks)
- Extract auth from monolith
- Build new auth service
- Point old system to new auth

Phase 2: Order Service (4 weeks)
- Extract order management
- Build new order service
- Migrate data

[Continue for all services]

Please help me execute Phase 1.
```

---

## Hybrid Approach Workflow

### Complete Example: Gradual Modernization

**Scenario**: Inline too risky, greenfield too expensive

**Workflow**:

```
The analysis shows:
- Inline feasibility: 55/100 (borderline risky)
- Greenfield feasibility: 58/100 (possible but expensive)

Recommendation: Hybrid approach (Strangler Fig pattern)

Let's create a migration strategy:

1. Identify the modules in priority order (riskiest/most valuable first)
2. For each module:
   a. Extract to new service
   b. Modernize the extracted service
   c. Update old system to call new service
   d. Migrate data incrementally
3. Eventually decommission old system when all modules extracted

Please help me:
1. Analyze the codebase to identify logical modules
2. Score each module by: risk level, business value, extraction difficulty
3. Create a priority-ordered extraction plan
```

Then execute:

```
Let's start with the highest-priority module: [Module Name]

Step 1: Create new service project
/speckit.orchestrate Create a modern [Module] service that replaces the [old component]

Step 2: Implement with best practices
[Follow generated plan]

Step 3: Create adapter layer
Build an API gateway that routes requests:
- New functionality → New service
- Old functionality → Old monolith

Step 4: Migrate data
Create data sync scripts to keep old and new DBs in sync during transition

Step 5: Gradual cutover
Route 10% traffic → new service
Monitor, then 50%, then 100%

Step 6: Repeat for next module
```

---

## Suggested Prompt Patterns

### For Greenfield Projects Using Analysis

**Constitution Prompt**:
```
/speckit.constitution

Create a project constitution based on lessons learned from our legacy system.

Use the recommended constitution from the analysis (.analysis/[PROJECT]/recommended-constitution.md) as the foundation, which includes:

PRESERVE (good patterns found):
- [Pattern 1]
- [Pattern 2]

ELIMINATE (anti-patterns found):
- [Anti-pattern 1]
- [Anti-pattern 2]

ADDRESS (gaps identified):
- [Gap 1]
- [Gap 2]

Also add these additional principles specific to our team:
- [Custom principle 1]
- [Custom principle 2]
```

**Spec Prompt**:
```
/speckit.specify

Create a specification for a modern replacement of [Old System Name].

Based on the reverse-engineered analysis at .analysis/[PROJECT]/analysis-report.md, the system provides these capabilities:

EXISTING FEATURES TO PRESERVE:
[List from analysis]

FEATURES TO ADD (missing in old system):
[List from gaps/modernization suggestions]

FEATURES TO REMOVE (deprecated/unused):
[List from analysis]

The new system should follow the constitution we established and address all the technical debt identified in the analysis.
```

**Plan Prompt**:
```
/speckit.plan

Technology choices for the modernized system:

KEEP (from old system - still good):
- [Technology 1] - analysis showed this is working well

REPLACE (from old system - outdated):
- [Old Tech] → [New Tech] - analysis showed this is problematic

ADD (missing in old system):
- [New Tech] - addresses gap identified in analysis

Architecture:
- [Pattern] - addresses architectural issues from analysis

Please create a plan that:
1. Preserves good patterns identified in analysis
2. Eliminates anti-patterns from analysis
3. Addresses technical debt from analysis
4. Uses modern, LTS versions of all technologies
```

---

## Tips for Effective Prompting

### 1. Reference Specific Analysis Sections

❌ **Vague**:
```
Use the analysis findings.
```

✅ **Specific**:
```
According to Section 3.3 (Security Issues) of the analysis report, we have 7 critical vulnerabilities. Let's address the top 3:
1. CVE-2021-XXXXX in lodash
2. CVE-2022-YYYYY in axios
3. Missing input validation in /api/login endpoint
```

### 2. Break Down Large Tasks

❌ **Too big**:
```
Execute the entire upgrade plan.
```

✅ **Manageable**:
```
Let's execute Phase 1 of the upgrade plan: Runtime/Platform Upgrade.

Phase 1 has 5 steps. Let's do step 1 first: Update .nvmrc file from Node 14 to Node 18.

After step 1 is complete and validated, we'll move to step 2.
```

### 3. Use Validation Checkpoints

✅ **Good practice**:
```
After completing [task], please validate:
1. All tests pass (npm test)
2. Build succeeds (npm run build)
3. No new linter errors (npm run lint)
4. Application starts (npm start)

If all 4 pass, we proceed. If any fail, we debug before continuing.
```

### 4. Provide Context from Analysis

✅ **Helpful context**:
```
The analysis found that we're using React class components with legacy lifecycle methods.

According to Section 7 (Modernization Suggestions), we should refactor to hooks.

Let's start with the most complex component: UserDashboard.jsx

Current approach (from analysis):
- Uses componentDidMount, componentDidUpdate
- 250 lines long
- Mixes concerns

Target approach (from modernization plan):
- Use useEffect
- Split into smaller components
- Separate data fetching from rendering

Please help refactor this component.
```

---

## Common Workflows Quick Reference

| Scenario | Analysis Depth | Follow-up Command | Estimated Time |
|----------|----------------|-------------------|----------------|
| Quick health check | QUICK | None (just review) | 30 min |
| Security audit | STANDARD (SECURITY focus) | Fix critical CVEs | 1 day |
| LTS upgrade | STANDARD (ALL) | Follow upgrade-plan.md | 1-4 weeks |
| Performance optimization | COMPREHENSIVE (PERFORMANCE) | Implement optimizations | 2-4 weeks |
| Architecture refactoring | COMPREHENSIVE (ARCHITECTURE) | Create refactoring plan | 1-3 months |
| Greenfield rewrite | COMPREHENSIVE (ALL) | /speckit.orchestrate | 3-12 months |
| Dependency cleanup | QUICK (DEPENDENCIES) | Update packages | 1-2 days |

---

**Need Help?**

See full documentation: `docs/reverse-engineering.md`

Open issues: https://github.com/veerabhadra-ponna/spec-kit-smart/issues
