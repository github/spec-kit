# Future Improvements

This document tracks all planned improvements and known limitations for the Spec Kit project.

**⚠️ IMPORTANT:** Never add TODO comments to prompt files or templates! They can confuse AI agents. Always add improvements here instead.

---

## 🔴 High Priority

### Scripts (create-new-feature.sh / .ps1)

- [ ] Add automated tests for regex patterns and edge cases
- [ ] Add environment variable for enforcing Jira requirement (`REQUIRE_JIRA=true`)
- [ ] Improve error messages with examples and suggestions
- [ ] Add validation examples to help text

### Interactive Prompts

- [ ] Add validation of interactive input format with clear error messages
  - Constitution: Validate PRINCIPLES/PROJECT METADATA structure
  - Specify: Validate JIRA:/FEATURE: line format
- [ ] Add retry logic if user input is malformed
- [ ] Add feature description quality checks (minimum length, keyword detection)
- [ ] Add confirmation step showing what will be created before proceeding

---

## 🟡 Medium Priority

### Testing & Quality

- [ ] Create test suite for branch detection regex patterns
- [ ] Add integration tests for script execution with various inputs
- [ ] Add smoke tests for common scenarios
- [ ] Test edge cases:
  - Very long branch names (near 244 char limit)
  - Special characters in Jira numbers
  - Empty/whitespace inputs
  - Concurrent branch creation

### Documentation

- [ ] Replace `[PLACEHOLDER_CONSTITUTION_EXAMPLES_LINK]` with real URL
- [ ] Add inline constitution examples (remove external dependency)
- [ ] Create troubleshooting guide for common errors
- [ ] Document branch naming convention in README

### User Experience

- [ ] Add progress indicators for long-running operations
- [ ] Improve error messages with actionable suggestions
- [ ] Add `--dry-run` flag to preview branch creation
- [ ] Add `--force` flag to override validations when needed

---

## 🟢 Low Priority / Nice to Have

### AGENTS.md Enforcement

- [ ] Explore technical enforcement alternatives (currently guidance-only)
- [ ] Add verification token system (if feasible)
- [ ] IDE plugin to auto-inject AGENTS.md into context
- [ ] Add reminder if AGENTS.md exists but not acknowledged

### Interactive Mode Enhancements

- [ ] Add autocomplete for common patterns
- [ ] Add interactive help/examples on demand
- [ ] Support multiple input formats (JSON, YAML, key-value)
- [ ] Add template library for common project types

### Branch Management

- [ ] Add command to list all feature branches
- [ ] Add command to cleanup old/merged branches
- [ ] Add branch naming validation before creation

### Corporate Guidelines - Future Enhancements

**Note**: Phase 1-4 completed. See "Completed Improvements" section below.

Additional nice-to-have features:

- [ ] Interactive guideline compliance checker
- [ ] Guideline diff tool (compare project vs template)
- [ ] Auto-fix common guideline violations
- [ ] Guideline analytics (compliance metrics)
- [ ] Enhanced CI/CD integration for guideline checking
- [ ] Guideline version management and migration tools
- [ ] Team-specific guideline overrides

### PowerShell Script

- [ ] Improve regex matching (mirror bash improvements)
- [ ] Add better error handling for Windows-specific issues
- [ ] Test on PowerShell Core (cross-platform)

### Reverse Engineering & Modernization Feature

**Current Status**: v1.0.0-alpha (EXPERIMENTAL) - Working implementation complete (~4,564 LOC Python)

**Note**: Phases 1-4 complete. See "Completed Improvements" section below.

**Phase 2 - Language-Specific Analyzers** ✅ COMPLETE:

- [x] JavaScript/Node.js analyzer (framework detection, build tools) - `languages/javascript.py` (661 lines)
- [x] Python analyzer (virtual env, framework detection) - `languages/python.py` (524 lines)
- [x] Java analyzer (Maven/Gradle, Spring Boot) - `languages/java.py` (423 lines)
- [x] .NET analyzer (NuGet, project type) - `languages/dotnet.py` (~400 lines)
- [ ] Ruby analyzer (Rails, Bundler) - Deferred (low priority)
- [ ] PHP analyzer (Composer, Laravel/Symfony) - Deferred (low priority)

**Phase 3 - Incremental Analysis** ✅ COMPLETE:

- [x] Checkpoint system for large codebases - `checkpoint.py` implemented
- [x] Resume capability from last checkpoint
- [x] Progress indicators and streaming reports
- [x] Support for 500K+ LOC projects

**Phase 4 - Advanced Features** ✅ COMPLETE:

- [x] CI/CD integration templates (GitHub Actions, GitLab CI, Jenkins)
- [ ] Baseline comparison (track improvements over time) - Deferred to Phase 6
- [ ] Plugin architecture for custom analyzers - Deferred to Phase 6
- [ ] Export formats (PDF, JSON, HTML, CSV) - Partial (JSON exists)
- [ ] Architecture diagram generation - Deferred to Phase 6

**Phase 5 - Enterprise Features** (Deferred):

- [ ] Multi-project/monorepo analysis
- [x] Customizable scoring weights - `config.py` with ScoringWeights dataclass
- [ ] Team capacity assessment
- [ ] Historical analytics and trending

---

### Phase 7 - Analysis-to-Spec Workflow Integration (NEW - 2025-11-08)

**Goal**: Bridge reverse engineering analysis with spec-driven development workflow by generating stage-specific prompts and artifacts.

**Problem Statement**:

Current analysis produces generic reports (`analysis-report.md`, `upgrade-plan.md`) that require manual interpretation to feed into the spec-driven workflow. This causes:

- Context loss between analysis and implementation
- Manual effort to extract principles, functional specs, tech stack
- Risk of ignoring legacy code nuances during modernization
- Ambiguity resolution without reference to "source of truth" (legacy code)

**Solution**: Transform analysis output to produce **workflow-ready artifacts** that automatically feed into each spec-driven stage (Constitution → Specify → Clarify → Plan → Tasks → Analyze → Implement → Checklist).

#### 7.1 Stage-Specific Prompt Generation (HIGH PRIORITY)

**Objective**: Generate custom prompts for ALL 8 workflow stages that inject legacy context at the right time.

**Deliverables**:

- [ ] Create `stage-prompts/` output directory structure
- [ ] Generate 8 prompt files (one per workflow stage):
  - [ ] `1-constitution-prompt.md` - Extracted principles from legacy codebase
  - [ ] `2-specify-prompt.md` - Functional spec derived from legacy features
  - [ ] `3-clarify-prompt.md` - Ambiguity resolution rules with legacy code references
  - [ ] `4-plan-prompt.md` - Proposed tech stack (LTS) + legacy architecture context
  - [ ] `5-tasks-prompt.md` - Task breakdown guidance with legacy complexity hints
  - [ ] `6-analyze-prompt.md` - Consistency checks against legacy behavior
  - [ ] `7-implement-prompt.md` - Implementation guidance with legacy code references
  - [ ] `8-checklist-prompt.md` - Quality validation based on legacy standards
- [ ] Add `README.md` in `stage-prompts/` explaining how to use each prompt
- [ ] Update `report_generator.py` to produce stage prompt files

**Prompt Structure Template**:

Each stage prompt should contain:

```markdown
# [STAGE NAME] Guidance (from Legacy Analysis)

## Quick Reference
**Project**: [Name]
**Legacy Tech Stack**: [List]
**Proposed Tech Stack**: [List with LTS versions]
**Analysis Date**: [ISO 8601]

## Legacy Code References
- **Authentication**: `legacy/auth.py:45-120` (session-based, 30min timeout)
- **Payment Processing**: `legacy/payments.py:156-234` (CRITICAL - preserve exactly)
- **Rate Limiting**: `legacy/middleware/ratelimit.py:23-67` (100 req/min per user)

## Extracted Principles/Requirements
[Stage-specific content extracted from analysis]

## Ambiguity Resolution Rules
When specifications are unclear:
1. Check corresponding legacy code (see references above)
2. Treat legacy implementation as "source of truth"
3. If still unclear after checking code, ASK USER
4. NEVER assume or guess behavior

## Critical Constraints
- [Must-preserve behaviors]
- [Known limitations to maintain]
- [Security/compliance requirements]

## Suggested Prompt
When running /speckit.[stage], use this prompt:

"""
[Ready-to-paste prompt text with all context]
"""
```

**Example - Clarify Stage Prompt**:

```markdown
# Clarify Stage Guidance (from Legacy Analysis)

## Quick Reference
**Project**: E-Commerce Platform v2.3
**Legacy Stack**: Python 2.7, Flask 0.12, MySQL 5.7
**Proposed Stack**: Python 3.12 (LTS), FastAPI 0.104+, PostgreSQL 16 (LTS)

## Legacy Code References
- **User Auth**: `src/auth/login.py:34-89` (session + cookie-based)
- **Order Processing**: `src/orders/checkout.py:112-345` (multi-step workflow)
- **Inventory**: `src/inventory/stock.py:45-123` (race condition exists!)

## Ambiguity Resolution Rules
For ANY clarification questions about:
- **Authentication flow**: Refer to `src/auth/login.py:34-89` - preserves exact session behavior
- **Payment processing**: Refer to `src/orders/payment.py:67-234` - CRITICAL, preserve exactly
- **Edge cases**: Check legacy code first, then ask user if still unclear

## Critical Behaviors (Preserve Exactly)
- Session timeout: 30 minutes (hardcoded in `config.py:12`)
- Payment retry: 3 attempts with exponential backoff (see `payment.py:189-201`)
- Order cancellation: Refunds must be idempotent (see `refund.py:45-67`)

## Suggested Prompt
"""
When clarifying requirements:
- For any ambiguous options, decide based on legacy app code as source of truth
- Specifically refer to: auth (src/auth/login.py), payments (src/orders/payment.py)
- If still not clear after checking legacy code, ASK ME - don't assume
- Preserve these exact behaviors: 30min session timeout, 3-retry payment logic
"""
```

**Implementation Plan**:

Week 1-2:

- [ ] Design prompt template format (Markdown structure)
- [ ] Create `PromptGenerator` class in new `prompt_generator.py` module
- [ ] Implement stage prompt generation for 3 core stages (constitution, clarify, implement)
- [ ] Add unit tests for prompt generation

Week 3-4:

- [ ] Complete remaining 5 stage prompts (specify, plan, tasks, analyze, checklist)
- [ ] Add file path extraction logic (find relevant legacy code sections)
- [ ] Generate "ready-to-paste" prompt text with all context
- [ ] Add stage-prompts/ to output directory structure
- [ ] Update orchestration scripts to produce stage prompts

**Success Criteria**:

- ✅ Analysis produces 8 stage-specific prompt files
- ✅ Each prompt contains actionable legacy code references (file paths + line numbers)
- ✅ Prompts are copy-pasteable (< 2 pages, ready to use)
- ✅ Clarify prompt includes "legacy as source of truth" guidance
- ✅ Plan prompt includes proposed tech stack with LTS versions + rationale

#### 7.2 Extracted Principles (Constitution Feed) (HIGH PRIORITY)

**Objective**: Generate `extracted-principles.md` that feeds directly into `/speckit.constitution` stage.

**Current State**: `recommended-constitution.md` exists but is template-based, not extracted from code.

**Improvement**:

- [ ] Analyze legacy codebase patterns to extract ACTUAL principles:
  - [ ] Security patterns (encryption, auth, audit logging)
  - [ ] Architectural patterns (microservices, monolith, event-driven)
  - [ ] Quality standards (test coverage, code conventions)
  - [ ] Business rules (payment processing, user workflows)
- [ ] Generate `extracted-principles.md` with three sections:
  - **Business Principles** (domain logic, workflows)
  - **Architectural Principles** (patterns, structure)
  - **Quality Principles** (testing, monitoring, performance)
- [ ] Include evidence/references for each principle (file paths)
- [ ] Update `report_generator.py` to produce extracted principles

**Example Output**:

```markdown
# Extracted Principles (from Legacy Codebase Analysis)

## Business Principles

### 1. Customer Data Privacy
**Evidence**: All customer PII encrypted at rest (`models/customer.py:23-45`)
**Source**: Database encryption middleware (`middleware/encryption.py`)
**Requirement**: Continue encrypting PII in new system

### 2. Audit Trail Requirement
**Evidence**: All transactions logged to `audit_log` table (`services/audit.py:12-34`)
**Source**: Regulatory compliance requirement (GDPR, SOX)
**Requirement**: Maintain audit logging with same detail level

## Architectural Principles

### 1. Service-Oriented Design
**Evidence**: Clear separation: Auth service, Order service, Inventory service
**Source**: `services/` directory structure
**Requirement**: Maintain service boundaries in new architecture

### 2. API-First Design
**Evidence**: All features exposed via REST API (`api/v1/`)
**Source**: Mobile app + web app both consume API
**Requirement**: Continue API-first approach, upgrade to OpenAPI 3.1

## Quality Principles

### 1. 80%+ Test Coverage
**Evidence**: `tests/` directory with 1,234 tests, 82% coverage
**Source**: CI/CD pipeline enforces coverage threshold
**Requirement**: Maintain or improve test coverage in new system
```

**Implementation**:

- [ ] Create `PrincipleExtractor` class in `principle_extractor.py`
- [ ] Scan codebase for patterns:
  - Security patterns (encryption, auth, validation)
  - Architectural patterns (service boundaries, data flow)
  - Testing patterns (test coverage, test types)
- [ ] Cross-reference with documentation and comments
- [ ] Generate evidence-backed principles document

**Success Criteria**:

- ✅ Produces `extracted-principles.md` with 10-20 concrete principles
- ✅ Each principle has evidence (file path + line numbers)
- ✅ Categorized into Business/Architecture/Quality sections
- ✅ Ready to feed into `/speckit.constitution` command

#### 7.3 Functional Specification Generation (HIGH PRIORITY)

**Objective**: Generate `functional-spec.md` that documents WHAT the legacy system does (features, workflows, configurations).

**Deliverables**:

- [ ] Create `FunctionalSpecGenerator` class in `functional_spec_generator.py`
- [ ] Generate comprehensive functional spec with:
  - [ ] **Features Inventory** - List all major features with descriptions
  - [ ] **User Workflows** - Document key user journeys
  - [ ] **Configuration Mapping** - All config files and their purposes
  - [ ] **API Endpoints** - Document all REST/GraphQL endpoints
  - [ ] **Data Models** - Key entities and relationships
  - [ ] **Known Quirks** - Undocumented behaviors and edge cases
- [ ] Stratify features by criticality:
  - **CRITICAL** - Must preserve exactly (payment, auth, audit)
  - **STANDARD** - Can modernize implementation (logging, caching)
  - **LEGACY QUIRKS** - Decide whether to preserve or fix
- [ ] Add to analysis output directory

**Example Output**:

```markdown
# Functional Specification (Legacy System)

## Features Inventory

### CRITICAL Features (Preserve Exactly)
1. **Payment Processing** (`src/orders/payment.py`)
   - Credit card payment with 3-retry logic
   - Refund processing (idempotent)
   - Payment gateway integration (Stripe API v2)

2. **User Authentication** (`src/auth/`)
   - Session-based auth (30min timeout)
   - Multi-factor authentication (TOTP)
   - Password reset workflow (email-based)

### STANDARD Features (Can Modernize)
3. **Logging** (`src/logging/`)
   - Current: Text-based logs to `/var/log/app.log`
   - Opportunity: Upgrade to structured logging (JSON)

4. **Caching** (`src/cache/`)
   - Current: Redis with manual cache invalidation
   - Opportunity: Add cache TTL, implement cache-aside pattern

### LEGACY QUIRKS (Decide: Preserve or Fix)
5. **Session Timeout Hardcoded** (`config.py:12`)
   - Currently: 30 minutes (not configurable)
   - Decision Needed: Make configurable via env var?

6. **Order ID Format** (`src/orders/models.py:23`)
   - Currently: `ORD-{timestamp}-{random}`
   - Issue: Not sortable by creation date
   - Decision Needed: Switch to UUID or keep for compatibility?

## Configuration Mapping

| Config File | Purpose | Migration Strategy |
|-------------|---------|-------------------|
| `config.py` | App settings | Migrate to env vars |
| `database.ini` | DB connection | Migrate to connection string |
| `.env.example` | Env template | Keep, update keys |
| `logging.conf` | Log settings | Replace with structured logging |
```

**Implementation**:

- [ ] Scan code for feature markers (routes, controllers, services)
- [ ] Document API endpoints from code (Flask routes, FastAPI endpoints)
- [ ] Extract configuration from files (`.env`, `config.py`, YAML)
- [ ] Identify critical vs standard features based on:
  - Payment/auth/audit keywords → CRITICAL
  - Logging/caching/formatting → STANDARD
  - Hardcoded values → LEGACY QUIRKS

**Success Criteria**:

- ✅ Produces `functional-spec.md` with complete feature inventory
- ✅ Features categorized by criticality (CRITICAL/STANDARD/QUIRKS)
- ✅ Configuration files mapped with migration strategy
- ✅ Serves as reference for all downstream stages

#### 7.4 Proposed Tech Stack with LTS + Rationale (HIGH PRIORITY)

**Objective**: Generate `proposed-tech-stack.md` with latest LTS versions and rationale for each choice.

**Current State**: `upgrade-plan.md` suggests versions but lacks detailed rationale.

**Improvement**:

- [ ] Create `TechStackProposer` class in `tech_stack_proposer.py`
- [ ] For each component, recommend:
  - **Latest LTS version** (not just "upgrade to X")
  - **Rationale** (why this version, why this framework)
  - **Migration Complexity** (Low/Medium/High)
  - **Compatibility Notes** (breaking changes, migration guides)
- [ ] Include version EOL dates for urgency context
- [ ] Add "Alternative Options" section for each choice

**Example Output**:

```markdown
# Proposed Tech Stack (with LTS + Rationale)

## Language & Runtime

### Python 3.12 (LTS until 2028-10)
**Current**: Python 2.7 (EOL 2020-01-01)
**Rationale**:
- Latest LTS version with 5-year support
- Performance improvements (up to 10% faster than 3.11)
- Type hinting improvements for better IDE support
- Team already familiar with Python
**Migration Complexity**: HIGH (breaking changes from 2.7)
**Migration Guide**: [Official 2-to-3 Guide](https://docs.python.org/3/howto/pyporting.html)

**Alternative Options**:
- Python 3.11 (stable, but shorter support window)
- Go 1.21 (better performance, but team has no expertise)

## Web Framework

### FastAPI 0.104+ (Latest Stable)
**Current**: Flask 0.12 (EOL 2018)
**Rationale**:
- Modern async support (10x throughput improvement)
- Automatic OpenAPI schema generation
- Type validation with Pydantic
- Similar to Flask (easier team adoption)
**Migration Complexity**: MEDIUM (async patterns new to team)
**Migration Path**: Incremental (run Flask + FastAPI side-by-side)

**Alternative Options**:
- Flask 3.0 (easier migration, but no async support)
- Django 5.0 (more batteries included, but overkill for our API-first design)

## Database

### PostgreSQL 16 (LTS until 2028-11)
**Current**: MySQL 5.7 (EOL 2023-10)
**Rationale**:
- Compatible with existing schema (minimal changes)
- JSONB support for new flexible fields
- Better concurrent write performance
- Strong ACID compliance (critical for payments)
**Migration Complexity**: LOW (schema mostly compatible)
**Migration Path**: Use `pgloader` tool for automated migration

**Alternative Options**:
- MySQL 8.4 LTS (familiar, but less feature-rich)
- MongoDB 7.0 (flexible schema, but lose ACID guarantees)

## Summary Table

| Component | Current | Proposed (LTS) | Complexity | Priority |
|-----------|---------|----------------|------------|----------|
| Python    | 2.7 (EOL) | 3.12 (2028) | HIGH | CRITICAL |
| Flask     | 0.12 (EOL) | FastAPI 0.104+ | MEDIUM | HIGH |
| MySQL     | 5.7 (EOL) | PostgreSQL 16 | LOW | HIGH |
| Redis     | 3.2 (EOL) | 7.2 LTS (2027) | LOW | MEDIUM |
```

**LTS Version Resolution Logic**:

- [ ] Query official sources for LTS versions:
  - Python: [python.org/downloads](https://www.python.org/downloads/)
  - Node.js: [nodejs.org/releases](https://nodejs.org/en/about/releases/)
  - Java: [oracle.com/java/support-roadmap](https://www.oracle.com/java/technologies/java-se-support-roadmap.html)
  - .NET: [dotnet.microsoft.com/platform/support/policy](https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core)
- [ ] Fallback: Use package manager to query (e.g., `npm view node versions`)
- [ ] Default: "Latest Stable" if LTS not clearly defined

**Implementation**:

- [ ] Create mapping of tech stacks to LTS sources
- [ ] Implement LTS version lookup (with caching)
- [ ] Generate rationale based on:
  - Team expertise (from legacy tech stack)
  - Migration complexity (breaking changes)
  - Feature gaps (what new stack enables)
  - Community support (ecosystem size)
- [ ] Add EOL dates for urgency

**Success Criteria**:

- ✅ All proposed versions are latest LTS (or latest stable)
- ✅ Each choice includes detailed rationale (3-5 bullet points)
- ✅ Migration complexity assessed (LOW/MEDIUM/HIGH)
- ✅ Alternative options provided for major choices
- ✅ Ready to feed into `/speckit.plan` stage

#### 7.5 Integration with Orchestrator Workflow (MEDIUM PRIORITY)

**Objective**: Enable seamless flow from analysis → spec-driven workflow using `/speckit.orchestrate --from-analysis`.

**Deliverables**:

- [ ] Add `--from-analysis` flag to `/speckit.orchestrate` command
- [ ] Detect presence of analysis artifacts (`stage-prompts/`, `extracted-principles.md`, etc.)
- [ ] Auto-inject stage prompts when running each workflow phase
- [ ] Update orchestration state to track analysis-driven workflow
- [ ] Add validation: warn if analysis is > 30 days old (may be stale)

**Workflow Integration**:

```bash
# Step 1: Analyze legacy project
/speckit.analyze-project
# Produces: analysis-report.md, stage-prompts/, extracted-principles.md, etc.

# Step 2: Start modernization workflow with analysis context
/speckit.orchestrate --from-analysis "Modernize e-commerce platform"
# Automatically:
# - Loads extracted-principles.md for constitution
# - Uses constitution-prompt.md guidance
# - Injects legacy context into each stage
# - References functional-spec.md throughout

# Step 3: Resume after interruption (preserves analysis context)
/speckit.resume
# Continues with full analysis context restored
```

**Implementation**:

- [ ] Update `orchestrate` script to accept `--from-analysis` flag
- [ ] Scan for analysis artifacts in project root or `analysis/` directory
- [ ] Modify stage execution to:
  - Load corresponding stage prompt file
  - Append prompt content to user's stage input
  - Inject legacy code references into agent context
- [ ] Update `.speckit-state.json` to include:
  - `analysis_based: true`
  - `analysis_date: "2025-11-08"`
  - `analysis_artifacts: ["stage-prompts/", "extracted-principles.md"]`

**Success Criteria**:

- ✅ `/speckit.orchestrate --from-analysis` successfully loads all analysis artifacts
- ✅ Each stage automatically receives relevant legacy context
- ✅ No manual copy-paste of prompts required
- ✅ Resume workflow preserves analysis context

#### 7.6 Documentation & Examples (MEDIUM PRIORITY)

**Objective**: Document the analysis-to-spec workflow with clear examples.

**Deliverables**:

- [ ] Create `docs/analysis-to-spec-workflow.md` guide
- [ ] Add "Complete Example" section with before/after
- [ ] Update `docs/reverse-engineering.md` with stage-prompts section
- [ ] Add FAQ: "How do I use stage prompts?"
- [ ] Create video walkthrough (optional, 5-10 minutes)

**Documentation Structure**:

```markdown
# Analysis-to-Spec Workflow Guide

## Overview
How to use analysis artifacts to drive modernization workflow.

## Quick Start
1. Run analysis: `/speckit.analyze-project`
2. Review artifacts: `analysis/stage-prompts/`
3. Start modernization: `/speckit.orchestrate --from-analysis "Description"`

## Using Stage Prompts Manually
[Step-by-step for each stage]

## Complete Example
[Before/after comparison with real project]

## FAQ
- How do I know if stage prompts are being used?
- Can I edit stage prompts before using them?
- What if analysis is outdated?
```

**Success Criteria**:

- ✅ Complete documentation with examples
- ✅ FAQ addresses common questions
- ✅ Examples show real output from analysis

#### 7.7 Success Metrics & Validation (LOW PRIORITY)

**Objective**: Validate that analysis-to-spec workflow improves modernization outcomes.

**Metrics to Track**:

- [ ] **Context Preservation**: % of legacy requirements captured in spec
- [ ] **Rework Reduction**: % of implementation rework due to missed requirements
- [ ] **Time Savings**: Time to complete modernization (with vs without analysis)
- [ ] **Accuracy**: % of critical behaviors preserved correctly

**Validation Plan**:

- [ ] Test on 3 real legacy projects
- [ ] Compare analysis-driven workflow vs manual workflow
- [ ] Survey users on usefulness of stage prompts
- [ ] Measure reduction in "forgot to preserve X" issues

**Success Criteria**:

- ✅ 90%+ of legacy requirements captured in spec
- ✅ 50%+ reduction in implementation rework
- ✅ 30%+ time savings vs manual approach
- ✅ 95%+ critical behaviors preserved correctly

---

### Phase 6 - Production Readiness (v1.0.0-alpha → v1.0.0)

**Goal**: Move from EXPERIMENTAL to PRODUCTION-READY status

**Current Blockers**:

- ❌ No unit tests (0% coverage)
- ❌ Not tested on real-world projects (0 validations)
- ❌ AI-guided workflow requires manual intervention
- ❌ No beta testing or user feedback
- ❌ No security audit completed

**Timeline**: 4-6 months (16-23 weeks) with 1-2 FTE developers

#### 6.1 Testing & Validation (4-6 weeks) - HIGH PRIORITY

**Unit Tests**:

- [ ] Create `tests/` directory structure
- [ ] Write unit tests for all Python modules:
  - [ ] `test_scanner.py` - Tech stack detection, metrics
  - [ ] `test_dependency_analyzer.py` - npm/pip parsing
  - [ ] `test_scoring_engine.py` - Feasibility algorithms
  - [ ] `test_report_generator.py` - Report generation
  - [ ] `test_security.py` - Path validation edge cases
  - [ ] `test_config.py` - Configuration validation
- [ ] Add pytest configuration (`pytest.ini`, `pyproject.toml`)
- [ ] Add coverage reporting (`pytest-cov`)
- [ ] Achieve 85%+ code coverage
- [ ] Add CI/CD workflow for automated testing

**Integration Tests**:

- [ ] Test against 10+ real-world projects:
  - [ ] 3x Node.js projects (React, Vue, Express)
  - [ ] 2x Python projects (Django, Flask)
  - [ ] 2x Java projects (Spring Boot)
  - [ ] 2x .NET projects (ASP.NET Core)
  - [ ] 1x Go project
  - [ ] 1x Rust project
- [ ] Validate analysis accuracy vs manual audits (target: 95%+)
- [ ] Document edge cases and failure modes
- [ ] Add regression tests for discovered issues

**Performance Testing**:

- [ ] Test varying project sizes:
  - [ ] Small (< 10K LOC)
  - [ ] Medium (10K-100K LOC)
  - [ ] Large (100K-500K LOC)
  - [ ] Very Large (500K+ LOC)
- [ ] Measure and document:
  - [ ] Analysis time vs project size
  - [ ] Memory usage
  - [ ] CPU utilization
- [ ] Fix performance bottlenecks
- [ ] Add timeout handling for very large projects
- [ ] Target: < 30 minutes for 500K LOC, < 2GB RAM

**Error Handling**:

- [ ] Test error scenarios:
  - [ ] Missing/corrupted package.json
  - [ ] Inaccessible files/directories
  - [ ] Mixed language projects
  - [ ] Monorepos
  - [ ] Binary files in codebase
- [ ] Improve error messages with actionable guidance
- [ ] Add graceful degradation for all failure modes
- [ ] Log errors with context for debugging

#### 6.2 Automation Improvements (3-4 weeks) - HIGH PRIORITY

**Reduce AI Manual Intervention**:

- [ ] Implement full automated report generation
- [ ] Auto-populate all template sections from analysis data
- [ ] Add CLI mode for non-interactive execution:

  ```bash
  python -m analyzer.main --project /path --depth STANDARD --output json
  ```

- [ ] Implement automated decision-making:
  - [ ] Auto-recommend inline vs greenfield based on scores
  - [ ] Auto-prioritize issues by severity
  - [ ] Auto-generate upgrade roadmap
- [ ] Target: Complete analysis without AI agent intervention

**External Tool Integration**:

- [ ] Add automatic tool detection and installation suggestions
- [ ] Improve fallback analysis quality (< 10% difference)
- [ ] Add support for more package managers:
  - [ ] Cargo (Rust) - full support
  - [ ] Go modules - full support
  - [ ] Composer (PHP) - full support
  - [ ] Bundler (Ruby) - full support
  - [ ] NuGet (.NET) - upgrade from "unsupported"
  - [ ] Maven/Gradle (Java) - upgrade from "unsupported"
- [ ] Add CVE database integration (offline mode)

**Structured Output Formats**:

- [x] JSON output format - Already exists
- [ ] YAML output format
- [ ] HTML report generation
- [ ] PDF export (optional)
- [ ] CSV for metrics

#### 6.3 User Validation (6-8 weeks) - MEDIUM PRIORITY

**Beta Testing Program**:

- [ ] Recruit 20+ beta testers:
  - [ ] Enterprise developers
  - [ ] Open source maintainers
  - [ ] Consultants/agencies
  - [ ] Individual developers
- [ ] Provide testing guidelines and feedback forms
- [ ] Collect structured feedback:
  - [ ] Analysis accuracy
  - [ ] Report usefulness
  - [ ] Time savings
  - [ ] Missing features
  - [ ] Bugs/issues
- [ ] Iterate based on feedback (minimum 2 cycles)
- [ ] Target: 80%+ satisfaction, < 5 critical bugs

**Case Studies**:

- [ ] Create 5+ detailed case studies:
  - [ ] Legacy Node.js app modernization
  - [ ] Java monolith assessment
  - [ ] Python Django upgrade
  - [ ] .NET framework → .NET 8 migration
  - [ ] React 16 → React 18 upgrade
- [ ] Document before/after metrics
- [ ] Create video walkthroughs (optional)
- [ ] Publish case studies with real data

#### 6.4 Production Hardening (2-3 weeks) - MEDIUM PRIORITY

**Security Audit**:

- [ ] Security review of path validation logic
- [ ] Test against malicious inputs:
  - [ ] Path traversal attacks
  - [ ] Symlink attacks
  - [ ] Command injection via subprocess
  - [ ] Resource exhaustion (DoS)
- [ ] Add rate limiting for subprocess calls
- [ ] Implement sandboxing for untrusted projects
- [ ] Add security scanning to CI/CD (Bandit, Safety)
- [ ] Target: Pass audit with 0 high/critical findings

**Dependency Management**:

- [ ] Create `requirements.txt` with pinned versions
- [ ] Create `requirements-dev.txt` for dev tools
- [ ] Test with minimum supported Python versions
- [ ] Document Python version compatibility (3.10+)
- [ ] Add dependency vulnerability scanning (Dependabot, Snyk)
- [ ] Add `setup.py` or `pyproject.toml` for distribution

**Cross-Platform Testing**:

- [ ] Test on Linux (Ubuntu, Debian, Fedora, Arch)
- [ ] Test on macOS (Intel + Apple Silicon)
- [ ] Test on Windows (10, 11)
- [ ] Test on Python versions (3.10, 3.11, 3.12)
- [ ] Fix platform-specific issues
- [ ] Document compatibility matrix

#### 6.5 Documentation & Support (2 weeks) - MEDIUM PRIORITY

**Documentation**:

- [ ] API documentation for Python modules (Sphinx)
- [ ] Developer guide for contributors
- [ ] Detailed troubleshooting guide
- [ ] FAQ based on beta testing feedback
- [ ] Architecture diagrams (system design, data flow)
- [ ] Performance tuning guide
- [ ] Migration guide (alpha → v1.0)

**Support Infrastructure**:

- [ ] Create GitHub issue templates:
  - [ ] Bug report
  - [ ] Feature request
  - [ ] Analysis accuracy issue
- [ ] Set up GitHub Discussions for Q&A
- [ ] Update contributing guidelines
- [ ] Add code of conduct
- [ ] Set up automated issue triage

#### 6.6 Release Engineering (1 week) - LOW PRIORITY

**Version Management**:

- [ ] Update version: v1.0.0-alpha → v1.0.0-beta1 (after 6.1)
- [ ] Update version: v1.0.0-beta1 → v1.0.0-rc1 (after 6.2-6.3)
- [ ] Update version: v1.0.0-rc1 → v1.0.0 (after 6.4-6.5)
- [ ] Update all documentation references
- [ ] Create release notes for each version
- [ ] Tag releases in Git
- [ ] Publish to PyPI (optional)
- [ ] Update README badges

**Success Criteria for v1.0.0**:

- ✅ 85%+ unit test coverage
- ✅ 95%+ accuracy on 10+ real projects
- ✅ Full automation (no AI intervention)
- ✅ 80%+ beta tester satisfaction
- ✅ 5+ published case studies
- ✅ Pass security audit
- ✅ Cross-platform compatibility verified
- ✅ Complete documentation

---

### Quick Wins (Can Start Immediately)

**Week 1-2**:

- [ ] Create `tests/` directory + basic test structure
- [ ] Add pytest + pytest-cov to project
- [ ] Create `requirements.txt` with pinned dependencies
- [ ] Set up GitHub Actions for CI/CD
- [ ] Test on 3 diverse real projects

**Week 3-4**:

- [ ] Write unit tests for scanner.py, scoring_engine.py
- [ ] Improve error messages with examples
- [ ] Add CLI mode for non-interactive execution
- [ ] Create troubleshooting guide
- [ ] Add security scanning (Bandit)

**Impact**: These 10 items enable **v1.0.0-beta1** release

---

## 🐛 Known Limitations

### By Design

- **Jira number is optional:** Can be made required via env var (future)
- **AGENTS.md enforcement is guidance-only:** Technical enforcement not feasible with current architecture
- **Interactive mode detection fragile:** Relies on literal `$ARGUMENTS` string matching
- **Branch numbering race condition:** Possible if multiple users create branches simultaneously

### Technical Constraints

- **No real-time validation:** Can't validate input until agent processes it
- **IDE-dependent behavior:** Some IDEs may not support interactive prompts well
- **Git fetch required:** Branch detection needs network access to check remote branches

---

## 📝 Maintenance

### Review Schedule

- **Monthly:** Review this document and prioritize items
- **Per sprint:** Pick 1-2 high priority items to implement
- **As needed:** Add new items as they're discovered

### Adding New Items

When adding improvements:

1. Choose priority level (🔴 High / 🟡 Medium / 🟢 Low)
2. Add checkbox with clear description
3. Include why it's needed and impact if not done
4. Link to related issues/PRs if applicable

### Completing Items

When completing improvements:

1. Mark checkbox as complete: `- [x]`
2. Add completion date and PR link
3. Move to "Completed" section at bottom (optional)
4. Update related documentation

---

## ✅ Completed Improvements

Track completed items here for reference.

### 2025-01-15

- [x] Add Jira number validation (regex format check) - PR #X
- [x] Fix branch detection regex to be more precise - PR #X
- [x] Clarify interactive input formats with templates - PR #X
- [x] Fix all markdownlint errors (multiple PRs) - PR #X
- [x] Create centralized improvements document - PR #X
- [x] Fix interactive mode detection in prompts (plan, implement, tasks, analyze) - PR #X
- [x] Implement Corporate Guidelines Phase 1 (Foundation) - PR #X
  - Created 7 guideline template files
  - Integrated guidelines into plan/implement/analyze/tasks prompts
  - Added tech stack auto-detection
  - Implemented multi-stack support
  - Added non-compliance handling
  - Updated AGENTS.md with guidelines documentation
- [x] Implement Corporate Guidelines Phase 2 (Configurable Branch Naming) - PR #18 (commit 98195d8)
  - Created `branch-config.json` schema
  - Refactored `create-new-feature.sh` to read from config file
  - Refactored `create-new-feature.ps1` to read from config file
  - Made Jira format configurable with regex patterns
  - Made Jira optional for teams without ticket systems
  - Maintained backward compatibility with defaults
  - Added documentation for branch configuration
- [x] Implement Corporate Guidelines Phase 3 (Multi-Stack Coordination) - PR #19 (commit 8f51529)
  - Implemented guideline precedence rules for multi-stack projects
  - Created `stack-mapping.json` for file-to-stack mapping
  - Added contextual guideline application logic
  - Optimized token usage with selective loading
  - Updated templates for multi-stack detection
  - Added examples for common combinations (React+Java, etc.)
- [x] Implement Corporate Guidelines Phase 4 (Advanced Features) - PR #21 (commit 13fd910)
  - Enhanced analysis capabilities
  - Added comprehensive testing suite for critical paths
  - Implemented advanced guideline features
  - Completed full corporate customization system
- [x] Implement Reverse Engineering Phase 1 (Core Implementation) - (commits f0eff30, 9f5629a)
  - Created scoring_engine.py for feasibility scoring (inline/greenfield) - 423 lines
  - Created dependency_analyzer.py for npm/pip security analysis - 524 lines
  - Created scanner.py for tech stack detection and metrics - 661 lines
  - Created report_generator.py for markdown report generation - ~800 lines
  - Created security.py for path validation - 118 lines
  - Created config.py for configuration management - 99 lines
  - Created analyze-project.sh bash orchestration script
  - Created analyze-project-setup.sh for cross-platform setup
  - Created analyze-project-setup.ps1 for PowerShell support
  - Full end-to-end analysis workflow operational
  - Total implementation: ~4,564 lines of Python + orchestration scripts
- [x] Implement Reverse Engineering Phase 2 (Language Analyzers) - (commit c414e65)
  - Created languages/javascript.py for Node.js/JavaScript analysis - ~661 lines
  - Created languages/python.py for Python-specific analysis - ~524 lines
  - Created languages/java.py for Java/Maven/Gradle analysis - ~423 lines
  - Created languages/dotnet.py for .NET/NuGet analysis - ~400 lines
  - 4 core language analyzers complete (Ruby/PHP deferred to Phase 6)
  - Framework detection, build tool detection, version detection
  - Graceful degradation when package managers unavailable
- [x] Implement Reverse Engineering Phase 3 (Checkpointing) - (commit verified 2025-11-08)
  - Created checkpoint.py for incremental analysis
  - Resume capability for interrupted analysis
  - Progress tracking and ETA estimation
  - Streaming report generation
  - Support for 500K+ LOC projects
- [x] Implement Reverse Engineering Phase 4 (CI/CD & Advanced Features) - (commit verified 2025-11-08)
  - Created GitHub Actions workflow template
  - Created GitLab CI configuration template
  - Created Jenkins pipeline template
  - Implemented customizable scoring weights (config.py)
  - JSON output format support
  - Complete documentation in templates
- [x] Deep analysis and documentation accuracy update - (commit c18c770, 2025-11-08)
  - Analyzed complete implementation (~4,564 LOC Python)
  - Updated reverse-engineering.md with accurate status
  - Clarified EXPERIMENTAL status with transparent reasons
  - Added comprehensive parameter documentation to README
  - Fixed Mermaid diagram rendering errors

---

## 📚 Historical Records

### Corporate Guidelines Implementation (2025-01-06 to 2025-11-06)

**Original Planning Document**: `GUIDELINES-IMPLEMENTATION-PLAN.md` (archived - content preserved below)

**Purpose**: Enable corporate customization of Spec Kit through configurable guidelines for tech stack standards, branch naming conventions, and multi-stack project support.

**Implementation Approach**: 4-phase rollout with clear deliverables and success criteria at each phase.

**Final Status**: ✅ **FULLY IMPLEMENTED** - All 4 phases completed successfully.

**Key Deliverables**:

1. `.guidelines/` directory with comprehensive templates (ReactJS, Java, .NET, Node.js, Python)
2. `branch-config.json` for configurable branch naming patterns
3. `stack-mapping.json` for multi-stack project coordination
4. Integration into all command templates (plan, implement, analyze, tasks)
5. Tech stack auto-detection and contextual guideline application
6. Priority system: Constitution > Corporate Guidelines > Spec Kit Defaults

**Results**:

- Teams can now customize Spec Kit to match corporate standards
- Supports corporate package registries (Artifactory, Nexus)
- Configurable branch naming without code changes
- Multi-stack projects (React+Java, etc.) properly supported
- Backward compatible - works with existing projects

**Lessons Learned**:

- Phased approach worked well for managing complexity
- Template-based guidelines provided good flexibility
- JSON configuration files easier than hardcoded scripts
- Token usage optimization critical for multi-stack support
- Clear priority hierarchy (Constitution > Guidelines > Defaults) prevented conflicts

**Reference PRs**:

- Phase 1: Foundation - TBD
- Phase 2: Branch Configuration - PR #18 (commit 98195d8)
- Phase 3: Multi-Stack Coordination - PR #19 (commit 8f51529)
- Phase 4: Advanced Features - PR #21 (commit 13fd910)

**Implementation Plan Archive**: For detailed phase breakdown, technical architecture, and original planning rationale, see Git history: `GUIDELINES-IMPLEMENTATION-PLAN.md` (removed 2025-11-07 after completion).

---

## 🤝 Contributing

To propose a new improvement:

1. Add it to the appropriate priority section above
2. Create a GitHub issue for discussion (for major changes)
3. Submit PR with implementation
4. Update this document when merged

**Remember:** Never add TODOs directly in prompt files!
