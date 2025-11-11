# Reverse Engineering & Modernization Guide

**Status**: ⚠️ **EXPERIMENTAL** - Working implementation with AI-guided analysis workflow (v1.0.0-alpha)
**Version**: 1.0.0-alpha
**Last Updated**: 2025-11-08
**Implementation**: ~4,564 lines of Python code + orchestration scripts + templates

---

## ⚠️ Important Notice

**Current Maturity Level**: This feature has a **complete working implementation** with extensive Python modules for automated analysis, combined with AI-guided workflows for comprehensive reporting. While the codebase is functional and production-ready from a code perspective, it remains EXPERIMENTAL due to limited real-world validation and alpha status.

**Fully Implemented Components** (~4,564 LOC):

- ✅ **Python Analyzer Modules** (8 core modules):
  - `scanner.py` (661 lines) - Tech stack detection, code metrics, structure analysis
  - `dependency_analyzer.py` (524 lines) - npm audit, pip-audit integration with graceful degradation
  - `scoring_engine.py` (423 lines) - Feasibility scoring algorithms (inline/greenfield)
  - `report_generator.py` (~800 lines) - Comprehensive markdown report generation
  - `security.py` (118 lines) - Path validation and security checks
  - `config.py` (99 lines) - Centralized configuration management
  - `checkpoint.py` - State management for resumable analysis
  - Plus 4 language-specific analyzers (Java, Python, JavaScript, .NET)

- ✅ **Complete `/speckit.analyze-project` command** with bash/PowerShell orchestration scripts
- ✅ **Analysis framework** with phase-by-phase workflows and AI-guided prompts
- ✅ **Comprehensive templates** (analysis reports, upgrade plans, recommended constitutions)
- ✅ **Scoring formulas** implemented in code (0-100 feasibility scoring)
- ✅ **Workflow guidance** for inline upgrade, greenfield rewrite, and hybrid approaches
- ✅ **Corporate guidelines integration** for compliance checking
- ✅ **Multi-language support** (JavaScript, Python, Java, .NET, Ruby, PHP, Go, Rust)

**Enhanced with External Tools** (optional, improves automation):

- ⚠️ Automated dependency scanning (npm audit, pip-audit) - **Graceful degradation if unavailable**
- ⚠️ Code metrics calculation (cloc, tokei, scc) - **Falls back to manual counting**
- ⚠️ Security vulnerability detection (Snyk, OWASP) - **AI agent provides manual analysis**
- ⚠️ Performance profiling tools - **Best-effort analysis if unavailable**

**Why Still EXPERIMENTAL:**

- ⚠️ v1.0.0-alpha status (not production-tested at scale)
- ⚠️ Limited real-world validation and user feedback
- ⚠️ AI-guided workflow components require human review
- ⚠️ Some edge cases and error scenarios may not be fully handled
- ⚠️ Performance characteristics unknown for very large projects (>500K LOC)

**For full automation roadmap**, see [Implementation Roadmap](docs/development/implementation-roadmap.md) below.

---

**Table of Contents:**

- [Important Notice](#️-important-notice)
- [Overview](#overview)
- [When to Use This Feature](#when-to-use-this-feature)
- [Quick Start](#quick-start)
- [Analysis Depths](#analysis-depths)
- [What Gets Analyzed](#what-gets-analyzed)
- [Understanding the Reports](#understanding-the-reports)
- [Feasibility Scoring](#feasibility-scoring)
- [Decision Making](#decision-making)
- [Workflow Examples](#workflow-examples)
- [Best Practices](#best-practices)
- [Known Limitations](#known-limitations)
- [Implementation Roadmap](docs/development/implementation-roadmap.md)
- [Frequently Asked Questions](#frequently-asked-questions)

---

## Overview

The **Reverse Engineering & Modernization** feature helps you analyze existing codebases to:

- 📊 **Assess current state** - Technology stack, architecture, dependencies
- ✅ **Identify strengths** - What's working well and should be preserved
- ❌ **Find weaknesses** - Technical debt, security issues, anti-patterns
- 🔄 **Plan upgrades** - LTS versions, security patches, framework migrations
- 🎯 **Make decisions** - Inline upgrade vs greenfield rewrite vs hybrid approach
- 📈 **Score feasibility** - Data-driven confidence scores for recommendations
- 🎯 **NEW (Phase 9)**: **Cross-Cutting Concern Migration** - Analyze and migrate specific concerns (auth, database, caching, messaging, deployment) without rewriting the entire app

This is particularly useful for:

- **Legacy modernization** projects (full application or targeted concerns)
- **Technical debt** assessment
- **Security audits** and compliance
- **Migration planning** (e.g., upgrade to latest LTS, migrate auth to Okta, VM → Kubernetes)
- **Architecture reviews**
- **NEW**: **Cross-cutting concern migrations** (auth services, database types, caching layers, message buses, deployment infrastructure)

---

## When to Use This Feature

### ✅ Good Use Cases

1. **Inherited Codebase**
   - You've taken over a project and need to understand its state
   - Documentation is missing or outdated
   - You need to assess technical debt

1. **Modernization Planning**
   - Runtime/framework versions approaching EOL
   - Security vulnerabilities need addressing
   - Performance issues need investigation

1. **Migration Decision**
   - Deciding between upgrade-in-place vs rewrite
   - Need cost/risk/timeline estimates
   - Stakeholders need data-driven recommendation

1. **Compliance & Security**
   - Security audit required
   - Need to identify vulnerable dependencies
   - Preparing for compliance certification

1. **Team Onboarding**
   - New team needs architecture overview
   - Need to establish coding standards
   - Want to create project constitution from existing patterns

### ❌ Not Suitable For

- Brand new projects (use `/speckit.orchestrate` instead)
- Projects without code (idea stage)
- Non-software systems

---

## Quick Start

### Step 1: Run Analysis

```bash
# In your AI coding agent (Claude Code, GitHub Copilot, etc.)
/speckit.analyze-project
```text

When prompted, provide:

```text
PROJECT_PATH: /path/to/your/existing/project
ANALYSIS_DEPTH: STANDARD
FOCUS_AREAS: ALL
```text

### Step 2: Interactive Modernization Questions

**NEW (Phase 8):** The agent will ask you **10 interactive questions** about your modernization goals:

1. Target Language/Framework (e.g., upgrade to latest LTS)
2. Target Database (PostgreSQL, MongoDB, keep current)
3. Message Bus/Queue - **[OPTIONAL if not detected in legacy code]**
4. Package Manager (keep current or switch)
5. Deployment Infrastructure (Kubernetes, AWS, Azure, traditional server)
6. Infrastructure as Code - **[SKIPPED for traditional deployments]**
7. Containerization Strategy - **[SKIPPED for traditional deployments]**
8. Observability Stack - **[OPTIONAL if not detected in legacy code]**
9. Security & Authentication (OAuth 2.0, JWT, keep current)
10. Testing Strategy (unit only, integration, E2E, comprehensive)

**Phase 8.1 Enhancement:** Questions adapt based on your legacy stack:

- **[OPTIONAL]** = Feature not detected, but you can opt-in
- **[SKIPPED]** = Not applicable for your deployment choice (e.g., no Kubernetes for traditional servers)
- Educational notes explain why questions are skipped and when they become relevant

### Step 2.5: Choose Analysis Scope (NEW - Phase 9)

**ANALYSIS_SCOPE Selection:**

The agent will ask what type of analysis you need:

- **[A] Full Application Modernization** - Analyze entire codebase for comprehensive modernization (existing workflow)
- **[B] Cross-Cutting Concern Migration** - Analyze ONLY a specific cross-cutting concern (NEW)

**If you choose [B] Cross-Cutting Concern Migration**, you'll be asked:

**CONCERN_TYPE** - Select from 9 concern types:
1. Authentication/Authorization (e.g., Custom JWT → Okta, SAML → OAuth 2.0)
2. Database/ORM Layer (e.g., Oracle → PostgreSQL, Raw SQL → ORM)
3. Caching Layer (e.g., Memcached → Redis, adding distributed cache)
4. Message Bus/Queue (e.g., TIBCO → Kafka, RabbitMQ → Azure Service Bus)
5. Logging/Observability (e.g., Custom logs → ELK Stack, adding Prometheus+Grafana)
6. API Gateway/Routing (e.g., Custom routing → Kong/Nginx)
7. File Storage/CDN (e.g., Local filesystem → S3/Azure Blob)
8. **Deployment/Infrastructure** (e.g., VM → OpenShift, AWS → Azure, On-premise → Cloud)
9. Other (user-specified)

**CURRENT_IMPLEMENTATION** - What you're migrating FROM (auto-detected from code)
**TARGET_IMPLEMENTATION** - What you're migrating TO (e.g., "Okta", "OpenShift", "AWS")

**→ See [Cross-Cutting Concern Analysis](#cross-cutting-concern-analysis-phase-9) section below for detailed workflow**

---

### Step 3: Deep Code Analysis

**For Full Application Modernization ([A]):**

After gathering your preferences, the agent will:

- **Scan ALL code files** to understand functionality
- Analyze dependencies and detect vulnerabilities
- Extract features, business logic, and configuration
- Map architecture patterns and technical debt
- Generate comprehensive reports **with real content** (not templates)

**Time**: 2-4 hours for standard analysis

**For Cross-Cutting Concern Migration ([B]):**

The agent will focus ONLY on the selected concern:

- Identify all concern-related files (using detection heuristics)
- Assess abstraction quality (HIGH/MEDIUM/LOW)
- Calculate blast radius (% of codebase affected)
- Analyze coupling degree (LOOSE/MODERATE/TIGHT)
- Recommend migration strategy (STRANGLER_FIG, ADAPTER_PATTERN, REFACTOR_FIRST, or BIG_BANG_WITH_FEATURE_FLAGS)

**Time**: 30-60 minutes for concern-specific analysis

### Step 4: Review Generated Artifacts

Analysis results saved to `.analysis/[PROJECT_NAME]-[TIMESTAMP]/`:

**For Full Application Modernization ([A]):**

**Core Analysis Documents:**

- `analysis-report.md` - Technical assessment with strengths/weaknesses and data-driven recommendations
- `EXECUTIVE-SUMMARY.md` - High-level overview for stakeholders
- `functional-spec.md` - Business Analyst document (WHAT system does) with real features from code
- `technical-spec.md` - Architecture document (HOW to build) with your chosen target stack

**Toolkit Workflow Integration:**

- `stage-prompts/` - 6 ready-to-use prompts for Toolkit workflow:
  - `constitution-prompt.md` - Principles derived from legacy code
  - `specify-prompt.md` - Requirements guidance (references functional-spec.md)
  - `clarify-prompt.md` - Clarification guidance with legacy code references
  - `plan-prompt.md` - Architecture guidance (references technical-spec.md)
  - `tasks-prompt.md` - Task breakdown guidance
  - `implement-prompt.md` - Implementation guidance with legacy code references

**Supporting Files:**

- `decision-matrix.md` - Comparison table for stakeholders (optional)
- `dependency-audit.json` - Machine-readable dependency data
- `metrics-summary.json` - Codebase metrics

---

**For Cross-Cutting Concern Migration ([B]) - NEW:**

**Core Concern-Specific Documents:**

- `concern-analysis.md` - Detailed analysis of the selected concern:
  - Identified concern files with evidence (file:line)
  - Abstraction level assessment (HIGH/MEDIUM/LOW)
  - Blast radius calculation (files, LOC, percentage)
  - Coupling degree analysis (LOOSE/MODERATE/TIGHT)
  - Entry points and consumer callsites
  - All findings with file:line references

- `abstraction-recommendations.md` - Guidance on improving abstractions:
  - If LOW: Detailed refactoring roadmap before migration
  - If MEDIUM: Recommendations for completing interface coverage
  - If HIGH: Best practices for maintaining abstractions

- `concern-migration-plan.md` - Step-by-step migration strategy:
  - Recommended approach (STRANGLER_FIG/ADAPTER_PATTERN/REFACTOR_FIRST/BIG_BANG_WITH_FEATURE_FLAGS)
  - Phased implementation (50/30/15/5 value delivery)
  - Week-by-week execution plan
  - Risk management and rollback procedures
  - Testing strategy and success criteria

- `EXECUTIVE-SUMMARY.md` - High-level overview for stakeholders:
  - Concern type and current/target implementations
  - Key findings (abstraction quality, blast radius, risk)
  - Recommended approach and timeline
  - Business impact and value delivery

**Supporting Files (Optional):**

- `concern-files-inventory.json` - List of all concern-related files with metadata
- `dependency-graph.md` - Visual dependency map for the concern

### Step 5: Use Artifacts in Toolkit Workflow

**NEW (Phase 8):** Generated artifacts integrate seamlessly with Spec Kit workflow:

#### Option A: Use Stage Prompts Directly

```bash
# Copy stage prompts to .claude/commands/
cp .analysis/[PROJECT]/stage-prompts/* .claude/commands/

# Then run Toolkit workflow as normal
/speckit.constitution    # Uses constitution-prompt.md
/speckit.specify         # Uses specify-prompt.md + functional-spec.md
/speckit.plan           # Uses plan-prompt.md + technical-spec.md
# ... continue with clarify, tasks, implement
```

#### Option B: Manual Review and Adaptation

- Review `functional-spec.md` to understand what the system does
- Review `technical-spec.md` to see proposed architecture
- Use as reference during modernization implementation

### Step 6: Make Decision

Based on the recommendation:

**If INLINE UPGRADE** (modernize existing codebase):

1. Review `analysis-report.md` for upgrade recommendations
1. Review `technical-spec.md` for target architecture
1. Use `stage-prompts/` to guide Toolkit workflow implementation
1. Start with immediate security patches
1. Test thoroughly at each phase

**If GREENFIELD REWRITE**:

1. Review `stage-prompts/constitution-prompt.md` for principles
1. Review `functional-spec.md` for features to preserve
1. Use as starting point for new project:

   ```bash
   /speckit.constitution [use principles from constitution-prompt.md]
   /speckit.specify [describe features based on functional-spec.md]
   /speckit.plan [use target stack from technical-spec.md]
   ```

**If HYBRID APPROACH**:

1. Use Strangler Fig pattern
1. Extract and modernize components incrementally
1. Maintain parallel systems during migration

---

## Analysis Depths

Choose the depth based on your needs and available time:

### QUICK (30 minutes)

**Best For**:

- Initial assessment
- Quick health check
- Time-constrained evaluations

**Includes**:

- Basic dependency scan
- Security vulnerability check
- Tech stack detection
- High-level metrics (LOC, file count)

**Output**:

- Executive summary
- Critical issues only
- Basic upgrade paths

### STANDARD (2-4 hours) - **Recommended**

**Best For**:

- Most use cases
- Comprehensive assessment
- Migration planning

**Includes**:

- Full codebase analysis
- Architecture review
- Code quality assessment
- Complete dependency audit
- Upgrade roadmaps
- Feasibility scoring

**Output**:

- Complete analysis report
- Detailed upgrade plan
- Recommended constitution
- Decision matrix

### COMPREHENSIVE (1-2 days)

**Best For**:

- Mission-critical systems
- Large-scale migrations
- Compliance requirements
- Detailed due diligence

**Includes**:

- Everything in STANDARD, plus:
- Performance profiling
- Deep security audit
- Architecture refactoring proposals
- Team capacity planning
- Detailed risk assessment
- ROI calculations

**Output**:

- All STANDARD outputs, plus:
- Performance optimization roadmap
- Security hardening plan
- Organizational change management plan

---

## What Gets Analyzed

### 1. Technology Stack

**Detected**:

- Languages (JavaScript, Python, Java, C#, Ruby, PHP, etc.)
- Frameworks (React, Vue, Django, Spring Boot, ASP.NET, etc.)
- Databases (PostgreSQL, MySQL, MongoDB, etc.)
- Build tools (Webpack, Vite, Maven, Gradle, etc.)
- Runtime versions (Node.js, Python, .NET, etc.)

**Analysis**:

- Current versions vs latest LTS
- EOL dates
- Breaking changes in upgrades
- Migration paths

### 2. Dependencies

**Checked**:

- Direct and transitive dependencies
- Outdated packages
- Security vulnerabilities (CVEs)
- License compatibility
- Maintenance status (last update date)

**Output**:

- Outdated dependencies table
- Vulnerable dependencies table
- Upgrade priority list

### 3. Code Quality

**Metrics**:

- Lines of code (excluding vendor/node_modules)
- Test coverage percentage
- Cyclomatic complexity
- Function/method length distribution

**Patterns**:

- Code smells (long functions, deep nesting)
- Anti-patterns (god objects, tight coupling)
- TODO/FIXME/HACK comments

### 4. Architecture

**Assessed**:

- Architecture pattern (MVC, microservices, etc.)
- Layer separation (routes, controllers, services, data)
- Component coupling
- API design consistency

**Identified**:

- Modularity issues
- Separation of concerns violations
- Circular dependencies

### 5. Security

**Scanned**:

- Known vulnerabilities (CVEs)
- Missing input validation
- Unsafe authentication patterns
- Exposed secrets (warnings)
- Missing security headers

**Prioritized by severity**:

- 🔴 CRITICAL (immediate action)
- 🟠 HIGH (fix within week)
- 🟡 MEDIUM (fix within month)
- 🟢 LOW (fix when convenient)

### 6. Performance

**Analyzed** (if data available):

- API response times
- Database query efficiency
- Bundle sizes
- Rendering performance

**Identified**:

- Performance bottlenecks
- Optimization opportunities

### 7. Documentation

**Reviewed**:

- README completeness
- Code comments quality
- API documentation
- Architecture documentation

**Gaps identified** for improvement

---

## Understanding the Reports

### analysis-report.md

**Main comprehensive report** with these sections:

1. **Executive Summary**
   - Project type, tech stack, current state
   - Key findings (3-5 bullet points)
   - Primary recommendation

1. **Project Overview**
   - Detailed tech stack breakdown
   - Architecture pattern
   - Codebase metrics

1. **What's Good** ✅
   - Architecture strengths
   - Code quality highlights
   - Testing coverage
   - Documentation quality
   - Examples with file paths

1. **What's Bad** ❌
   - Technical debt table (with effort estimates)
   - Anti-patterns (with impact analysis)
   - Security issues (prioritized by severity)
   - Performance bottlenecks
   - Code smells

1. **Dependency Analysis**
   - Outdated dependencies table
   - Vulnerable dependencies (CVEs)
   - Deprecated packages
   - License issues

1. **Upgrade Path Analysis**
   - LTS upgrade roadmap (step-by-step)
   - Framework upgrade paths
   - Security patches (immediate actions)

1. **Modernization Suggestions**
   - Architecture improvements
   - Technology updates
   - Development process enhancements
   - Performance optimizations
   - Organized by: Quick wins vs Long-term

1. **Feasibility & Confidence Analysis**
   - Inline upgrade feasibility score (0-100)
   - Greenfield rewrite feasibility score (0-100)
   - Confidence scores
   - Scoring breakdown by factor

1. **Decision Matrix**
   - Side-by-side comparison table
   - Time, cost, risk, business impact
   - Hybrid approach evaluation

1. **Recommendations**
    - Primary recommendation with rationale
    - Immediate actions (next 2 weeks)
    - Short-term roadmap (1-3 months)
    - Long-term roadmap (3-12 months)

1. **Risk Assessment**
    - Upgrade risks with mitigation strategies
    - Rewrite risks with mitigation strategies

### upgrade-plan.md

**Step-by-step upgrade instructions** (generated if inline upgrade recommended):

- **9 phases** from preparation to deployment
- Detailed steps for each phase
- Validation checklists
- Rollback procedures
- Risk mitigation strategies
- Timeline and milestones

**Example phases**:

1. Preparation & Baseline
1. Runtime/Platform Upgrade
1. Core Dependencies Upgrade
1. Secondary Dependencies
1. Build Tooling Upgrade
1. Code Modernization
1. Security Hardening
1. Testing & Quality Assurance
1. Documentation Update
1. Deployment & Rollout

### recommended-constitution.md

**Project principles** (generated if greenfield rewrite recommended):

Derived from analyzing:

- ✅ Good patterns to preserve
- ❌ Anti-patterns to avoid
- 🔍 Gaps to address

**10 principles** covering:

1. Code Quality
1. Testing
1. Security
1. Error Handling
1. Architecture
1. Dependency Management
1. Documentation
1. Performance
1. Code Review
1. Deployment

Each principle includes:

- Clear statement (MUST/SHOULD/MAY)
- Rationale (why it matters)
- Implementation guidance
- Examples from codebase (good/bad)
- Enforcement mechanisms

### decision-matrix.md

**Stakeholder-friendly comparison** table:

| Criteria | Inline Upgrade | Greenfield Rewrite | Hybrid |
|----------|----------------|--------------------|--------|
| Time | X weeks | Y months | Z months |
| Cost | $$ | $$$ | $$$ |
| Risk | Medium | High | Medium |
| Business Disruption | Low | Medium | Low |
| Technical Debt Reduction | 40% | 100% | 70% |

Helps communicate with non-technical stakeholders.

---

## Feasibility Scoring

### Inline Upgrade Feasibility (0-100)

**Formula**:

```text
Score = (Code_Quality × 0.20) +
        (Test_Coverage × 0.15) +
        (Dependency_Health × 0.20) +
        (Architecture_Quality × 0.15) +
        (Team_Familiarity × 0.10) +
        (Documentation × 0.10) +
        (Breaking_Changes × 0.10)
```text

**Interpretation**:

- **80-100**: ✅ Highly feasible - proceed with inline upgrade
- **60-79**: ⚠️ Feasible with caution - assess risks carefully
- **40-59**: 🟡 Moderately risky - consider hybrid approach
- **0-39**: 🔴 High risk - consider greenfield rewrite

### Greenfield Rewrite Feasibility (0-100)

**Formula**:

```text
Score = (Requirements_Clarity × 0.20) +
        (Technical_Debt_Level × 0.20) +
        (Business_Continuity × 0.15) +
        (Team_Capacity × 0.15) +
        (Time_Available × 0.15) +
        (Budget × 0.15)
```text

**Interpretation**:

- **80-100**: ✅ Strong candidate for rewrite
- **60-79**: ⚠️ Viable with proper planning
- **40-59**: 🟡 Challenging - need strong business case
- **0-39**: 🔴 Not recommended - too risky

### Confidence Scores

**Analysis Confidence** (0-100):
Based on:

- Code accessibility (can we read all files?)
- Documentation availability
- Test coverage (more tests = more confidence)
- Complexity assessment accuracy

**Recommendation Confidence** (0-100):
Based on:

- Data completeness
- Industry experience with similar migrations
- Risk assessment accuracy

**Example**:

```text
Recommendation: INLINE UPGRADE
Feasibility: 72/100
Confidence: 85/100

Interpretation: Moderately feasible inline upgrade with high confidence in assessment
```

---

## Decision Making

### Decision Tree

```text
START
  ↓
Is code maintainable? (Code Quality Score)
  ├─ YES (≥70) → Inline Upgrade likely
  ├─ NO (<70) → Continue evaluation
  ↓
Are dependencies healthy? (Dependency Score)
  ├─ YES (≥70) → Inline Upgrade likely
  ├─ NO (<70) → Continue evaluation
  ↓
Is architecture sound? (Architecture Score)
  ├─ YES (≥70) → Inline Upgrade likely
  ├─ NO (<70) → Continue evaluation
  ↓
Is technical debt extreme? (>60% of codebase)
  ├─ YES → Greenfield Rewrite likely
  ├─ NO → Hybrid Approach likely
  ↓
Check Business Constraints
  ├─ Time-critical? → Inline (faster)
  ├─ Budget-limited? → Inline (cheaper)
  ├─ Can maintain parallel systems? → Hybrid (safer)
  └─ Can afford downtime? → Greenfield (cleanest)
```text

### Recommendation Logic

**Inline Upgrade** chosen when:

- ✅ Inline score ≥ 70
- ✅ Code quality acceptable
- ✅ Test coverage adequate (≥60%)
- ✅ No critical architecture flaws
- ✅ Team knows codebase well

**Greenfield Rewrite** chosen when:

- ✅ Greenfield score ≥ 60
- ❌ Inline score < 50
- 🔴 Critical technical debt
- 🔴 Architecture fundamentally flawed
- ✅ Requirements well understood
- ✅ Time and budget available

**Hybrid Approach** (Strangler Fig) chosen when:

- 🟡 Both scores in middle range (50-69)
- ⚠️ Inline risky, greenfield too expensive
- ✅ Can maintain parallel systems
- ✅ Can migrate incrementally
- ✅ Business can tolerate gradual transition

---

## Workflow Examples

### Example 1: Legacy Node.js App

**Scenario**: Inherited a Node.js 12 app, need to upgrade

**Analysis**:

```bash
/speckit.analyze-project

PROJECT_PATH: /home/user/legacy-api
ANALYSIS_DEPTH: STANDARD
FOCUS_AREAS: ALL
```text

**Results**:

- Node.js 12 (EOL: 2022-04-30) - Critical
- 47 outdated dependencies, 7 with CVEs
- Test coverage: 38%
- Architecture: Layered (good)
- Code quality: 6/10 (acceptable)

**Recommendation**: INLINE UPGRADE (Feasibility: 68/100)

**Action Taken**:

1. Reviewed `upgrade-plan.md`
1. Fixed critical CVEs immediately (2 hours)
1. Started Phase 1: Node.js 12 → 16 → 18 (1 week)
1. Followed remaining phases (3 weeks total)

**Outcome**: Successfully upgraded in 1 month, 0 downtime

### Example 2: Ancient Java Monolith

**Scenario**: 10-year-old Java 8 monolith, performance issues

**Analysis**:

```bash
/speckit.analyze-project

PROJECT_PATH: /opt/monolith
ANALYSIS_DEPTH: COMPREHENSIVE
FOCUS_AREAS: ALL
```text

**Results**:

- Java 8 (EOL: 2030 but outdated features)
- 200K+ LOC, deeply coupled
- No tests (0% coverage)
- Performance: p95 > 5 seconds
- Security: 23 high/critical issues

**Recommendation**: GREENFIELD REWRITE (Inline: 32/100, Greenfield: 78/100)

**Action Taken**:

1. Used `recommended-constitution.md` to establish principles
1. Reverse-engineered requirements from code
1. Started new project with modern stack (Spring Boot 3, Java 21)
1. Used Strangler Fig to migrate module-by-module
1. Maintained old system during 18-month migration

**Outcome**: New system 10x faster, fully tested, maintainable

### Example 3: React 16 Frontend

**Scenario**: React 16 app, need React 18 features (concurrent rendering)

**Analysis**:

```bash
/speckit.analyze-project

PROJECT_PATH: /var/www/frontend
ANALYSIS_DEPTH: STANDARD
FOCUS_AREAS: ARCHITECTURE, DEPENDENCIES
```text

**Results**:

- React 16.8, TypeScript 3.9
- Well-architected, modular
- 82% test coverage
- No critical security issues
- Few breaking changes to React 18

**Recommendation**: INLINE UPGRADE (Feasibility: 92/100, Confidence: 95%)

**Action Taken**:

1. Followed `upgrade-plan.md`
1. Updated React 16 → 17 → 18 (3 days)
1. Updated createRoot API (1 day)
1. Updated TypeScript 3.9 → 5.3 (2 days)
1. Tested thoroughly (1 week)

**Outcome**: Upgraded in 2 weeks, unlocked concurrent features

---

## Best Practices

### 1. Run Analysis Early

- **Don't wait** until deadlines are tight
- Run quarterly for active projects
- Run immediately when inheriting codebase

### 2. Choose Appropriate Depth

- **QUICK**: For regular health checks
- **STANDARD**: For most assessments
- **COMPREHENSIVE**: For critical decisions

### 3. Involve Stakeholders

- Share `decision-matrix.md` with non-technical stakeholders
- Present `analysis-report.md` to technical leadership
- Get buy-in before starting major work

### 4. Follow the Plan

- Don't skip phases in `upgrade-plan.md`
- Validate at each checkpoint
- Keep rollback option ready

### 5. Test Thoroughly

- Run full test suite after each phase
- Add tests if coverage is low
- Manual QA for critical flows

### 6. Monitor Post-Deployment

- Watch error rates for 48 hours
- Compare performance metrics
- Be ready to rollback if needed

### 7. Document Learnings

- Update constitution with lessons learned
- Document decisions (ADRs)
- Share knowledge with team

---

## Known Limitations

### Current Limitations

### 1. Template-Based Analysis

This feature currently provides comprehensive templates and methodology, but relies on the AI agent and available tools for execution. The analysis process is semi-automated rather than fully automated.

### 2. Tool Dependencies

Analysis quality depends on available tooling:

- **Dependency Scanning**: Requires npm audit (Node.js), pip-audit (Python), or similar
- **Code Metrics**: Requires cloc, tokei, scc, or similar tools
- **Security Scanning**: Best results with Snyk, OWASP Dependency-Check, or similar
- **Without tools**: AI agent will provide best-effort analysis based on manual inspection

### 3. Language Coverage

While the framework supports multiple languages, depth of analysis varies:

- **Best Support**: JavaScript/Node.js, Python
- **Good Support**: Java, .NET, Ruby, PHP
- **Basic Support**: Other languages (general analysis only)

### 4. Large Codebase Performance

- **Tested on**: Projects up to 100K LOC
- **May struggle with**: Monorepos >500K LOC, deeply nested dependencies
- **Workaround**: Focus analysis on specific directories or modules

### 5. Scoring Calibration

Feasibility scores (0-100) are based on industry research and best practices, but:

- Not calibrated against specific organization's risk tolerance
- Weights are generic (customization requires manual adjustment)
- Thresholds (e.g., 80+ = highly feasible) may need adjustment for your context

### 6. No Incremental Analysis

Currently all-or-nothing analysis. Cannot resume from checkpoint if interrupted.

### 7. Manual Report Assembly

AI agent generates sections sequentially. For very large projects, may require multiple sessions with manual compilation.

### 8. Security Considerations

When analyzing untrusted codebases:

- AI agent reads code files but does not execute them
- Be cautious with: symlinks, binary files, very large files
- Recommendation: Analyze only trusted codebases or run in sandboxed environment

### Workarounds

**For Better Results**:

1. **Install analysis tools** before running:

   ```bash
   # Node.js projects
   npm install -g npm-check-updates

   # Python projects
   pip install pip-audit

   # Code metrics (any language)
   npm install -g cloc
   # or: cargo install tokei
   ```

1. **Break down large projects**:

   ```bash
   # Analyze subdirectories separately
   /speckit.analyze-project
   PROJECT_PATH: /project/backend

   /speckit.analyze-project
   PROJECT_PATH: /project/frontend
   ```

1. **Use focus areas** for faster analysis:

   ```bash
   # Security-only audit
   FOCUS_AREAS: SECURITY

   # Dependencies-only check
   FOCUS_AREAS: DEPENDENCIES
   ```

1. **Customize scoring weights** in generated reports based on your priorities

---

---

## Frequently Asked Questions

### Q: How long does analysis take?

**A**: Depends on depth:

- QUICK: 30 minutes
- STANDARD: 2-4 hours
- COMPREHENSIVE: 1-2 days

### Q: Can I analyze non-JavaScript projects?

**A**: Yes! Supports:

- JavaScript/TypeScript (Node.js, React, etc.)
- Python (Django, Flask, etc.)
- Java (Spring Boot, etc.)
- C# (.NET, ASP.NET)
- Ruby (Rails)
- PHP (Laravel, Symfony)
- And more

### Q: What if my project has no tests?

**A**: Analysis will flag this as critical issue and:

- Recommend adding tests before upgrade
- Lower feasibility score
- Suggest greenfield rewrite (if other factors also poor)

### Q: Can I analyze a monorepo with multiple projects?

**A**: Yes, but analyze each project separately:

```bash
/speckit.analyze-project
PROJECT_PATH: /monorepo/packages/frontend

/speckit.analyze-project
PROJECT_PATH: /monorepo/packages/backend
```text

### Q: What if I disagree with the recommendation?

**A**: The AI provides data-driven recommendations, but you make the final decision. Review:

- Feasibility scores and how they're calculated
- Business constraints the AI may not know
- Team capabilities
- Risk tolerance

You can override the recommendation.

### Q: Can I re-run analysis after making changes?

**A**: Yes! Re-run to:

- Track progress
- Validate improvements
- Update recommendations

### Q: What tools does the analysis use?

**A**: Gracefully uses available tools:

- `npm audit`, `pip-audit` for vulnerabilities
- `cloc`, `tokei` for code metrics
- `eslint`, `pylint` for code quality
- Falls back to manual analysis if tools unavailable

### Q: Is my code sent anywhere?

**A**: No. Analysis runs entirely locally using your AI agent. Code never leaves your machine.

### Q: Can I customize the analysis?

**A**: Yes, focus on specific areas:

```bash
FOCUS_AREAS: SECURITY  # Security-focused audit
FOCUS_AREAS: PERFORMANCE  # Performance optimization
FOCUS_AREAS: DEPENDENCIES  # Dependency health only
```text

### Q: What if analysis finds critical security issues?

**A**: Immediate actions section will list:

- CVE numbers and CVSS scores
- Affected packages
- Fix versions
- Estimated effort (usually minutes to hours)

**Prioritize these before any other work.**

### Q: Can I use this for greenfield projects?

**A**: No. For new projects, use:

```bash
/speckit.orchestrate <feature-description>
```text

This is specifically for **existing** codebases.

---

## Next Steps

After running analysis:

1. **Review Reports** - Read `analysis-report.md` thoroughly
1. **Discuss with Team** - Share findings and recommendations
1. **Get Approval** - Present `decision-matrix.md` to stakeholders
1. **Execute Plan**:
   - Inline: Follow `upgrade-plan.md`
   - Greenfield: Use `/speckit.orchestrate` with recommended artifacts
   - Hybrid: Combine both approaches
1. **Monitor Progress** - Re-run analysis quarterly to track improvements

---

## Support

Questions or issues? Open a GitHub issue:
<https://github.com/veerabhadra-ponna/spec-kit-smart/issues>

---

**Happy Modernizing!** 🚀

---

## Developer Resources

For developers interested in implementing or contributing to this feature:

- **Implementation Roadmap**: See [development/implementation-roadmap.md](./development/implementation-roadmap.md)
  - 5-phase plan (16-21 weeks)
  - Priority tasks for contributors
  - Technical requirements and deliverables

- **Engineering Review**: See [development/engineering-review.md](./development/engineering-review.md)
  - Comprehensive technical assessment
  - Issues identified and prioritized
  - Architectural recommendations

- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md) and [AGENTS.md](../AGENTS.md)
  - Contribution guidelines
  - AI agent instructions
  - Development standards

**Quick Links**:

- [GitHub Issues](https://github.com/veerabhadra-ponna/spec-kit-smart/issues) (label: `reverse-engineering`)
- [GitHub Discussions](https://github.com/veerabhadra-ponna/spec-kit-smart/discussions)
