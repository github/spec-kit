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

**Current Status**: v1.0.0-alpha (EXPERIMENTAL) - Redesign Required

**Note**: Phases 1-4 complete (see "Completed Improvements" section). Phase 7 completed but requires redesign based on user feedback. Phase 8 (new) addresses core issues.

**Phases 2-5 Status**: See "Completed Improvements" section for details.

---

### Phase 8 - Interactive AI-Driven Analysis Workflow (HIGH PRIORITY) 🔴

**Current Problem** (User Feedback 2025-11-09):

The existing Python generators (`functional_spec_generator.py`, `tech_stack_proposer.py`, `prompt_generator.py`) produce **template-only artifacts** without real analysis of legacy code. This results in:

- ❌ `functional-spec.md` is just a template (no actual features from legacy code)
- ❌ `proposed-tech-stack.md` is just a template (no real tech stack analysis)
- ❌ Stage prompts are generic templates (no legacy code references)
- ❌ No interactive workflow to gather modernization requirements
- ❌ Cannot ask about target stack preferences, deployment infrastructure, IaC choices
- ❌ Generated artifacts don't provide useful feedback to Toolkit workflow

**Root Cause**: Python cannot perform semantic analysis like AI agents. The current approach has Python generating templates that should be filled by AI analysis + legacy code understanding.

**Solution**: Redesign to use **Interactive AI-Driven Workflow** with AI analysis + prompt templates (similar to meta-prompt approach used in regular Toolkit workflow).

---

#### 8.1 Interactive Workflow Design (CRITICAL)

**Objective**: Make analyze-project **INTERACTIVE-ONLY** with multi-step guided analysis.

**Workflow Steps**:

##### Step 1: Initial Inputs (Required)

```text
PROJECT_PATH: /path/to/legacy/project
ANALYSIS_DEPTH: QUICK | STANDARD | COMPREHENSIVE
FOCUS_AREAS: ALL | SECURITY | PERFORMANCE | ARCHITECTURE | DEPENDENCIES
```

##### Step 2: Quick Tech Stack Sampling

Scan codebase to identify current stack (language, framework, database,
enterprise bus, caching, etc.). Display findings to user:

```text
Detected Stack:
- Frontend: React 16.8 (JavaScript)
- Backend: Java 8 (Spring Boot 2.1)
- Database: Oracle 11g
- Message Bus: TIBCO EMS
- Caching: Memcached 1.4
- Build Tool: Maven 3.6
```

##### Step 3: Modernization Target Questions

Ask user about target stack preferences:

```text
MODERNIZATION PREFERENCES:

1. Backend Language:
   Current: Java 8
   Options:
   - [A] Java 21 LTS (same language, latest LTS)
   - [B] Python 3.12 LTS (different language)
   - [C] Other (specify)
   Your choice: ___

2. Database:
   Current: Oracle 11g
   Options:
   - [A] Oracle 21c (same vendor, latest)
   - [B] PostgreSQL 16 LTS (open source RDBMS)
   - [C] MongoDB 7.0 (NoSQL)
   - [D] Other (specify)
   Your choice: ___

3. Message Bus:
   Current: TIBCO EMS
   Options:
   - [A] TIBCO EMS (latest version)
   - [B] Apache Kafka (open source)
   - [C] Solace (cloud-native)
   - [D] Other (specify)
   Your choice: ___

4. Package Manager (for Java):
   Options:
   - [A] Maven (current)
   - [B] Gradle
   Your choice: ___

5. Target Deployment Infrastructure:
   Options:
   - [A] Dedicated server (physical/VM)
   - [B] Kubernetes cluster
   - [C] OpenShift
   - [D] Azure (App Service, AKS, etc.)
   - [E] AWS (ECS, EKS, Lambda, etc.)
   - [F] Google Cloud (GKE, Cloud Run, etc.)
   Your choice: ___

6. Infrastructure as Code (IaC):
   Options:
   - [A] Helm charts (for Kubernetes)
   - [B] Terraform
   - [C] OpenShift templates
   - [D] CloudFormation (AWS)
   - [E] ARM templates (Azure)
   - [F] None / Manual
   Your choice: ___

7. Containerization:
   Options:
   - [A] Docker containers
   - [B] Kubernetes (orchestration)
   - [C] Docker + Kubernetes
   - [D] No containerization
   Your choice: ___

8. Observability Stack:
   Options:
   - [A] ELK Stack (Elasticsearch, Logstash, Kibana)
   - [B] Prometheus + Grafana
   - [C] Azure Monitor / Application Insights
   - [D] AWS CloudWatch
   - [E] Google Cloud Operations
   - [F] OpenTelemetry (vendor-neutral)
   - [G] Other (specify)
   Your choice: ___

9. Security Requirements:
   Options:
   - [A] OAuth 2.0 / OpenID Connect
   - [B] JWT tokens
   - [C] SAML
   - [D] API Keys
   - [E] Mutual TLS
   - [F] Keep current auth mechanism
   Your choice: ___

10. Testing Strategy:
    Options:
    - [A] Unit tests only
    - [B] Unit + Integration tests
    - [C] Unit + Integration + E2E tests (full coverage)
    - [D] Minimal testing
    Your choice: ___
```

##### Step 4: Deep Legacy Analysis

**Scan ALL code files** to understand functionality. Analyze legacy codebase thoroughly:

- Controllers, services, models, repositories
- Configuration files (application.properties, XML configs)
- Database schemas (DDL, migrations)
- API endpoints and contracts
- Business logic and workflows
- Security implementations (auth, authorization, encryption)
- Integration points (external APIs, message queues)
- Deployment scripts and infrastructure code
- Containerization configs (Dockerfile, docker-compose.yml)
- Observability configs (logging, monitoring, tracing)
- Testing suites (unit, integration, E2E tests)

##### Step 5: Clarification Questions (If Needed)

After deep analysis, ask user for any missing details:

```text
CLARIFICATIONS NEEDED:

  1. Your legacy app uses custom encryption for PII fields.
     Should we:
     - [A] Preserve exact encryption algorithm (AES-256-CBC with custom key derivation)
     - [B] Upgrade to modern encryption (AES-256-GCM with industry standard KDF)

  2. Found hardcoded API timeout of 30 seconds in multiple places.
     Should we:
     - [A] Preserve 30 second timeout
     - [B] Make configurable via environment variable

  ... (other clarifications based on analysis findings)
  ```

##### Step 6: Generate Artifacts

Using AI analysis of legacy code + user's modernization preferences, generate:

- ✅ `analysis-report.md` - Comprehensive findings
- ✅ `EXECUTIVE-SUMMARY.md` - High-level overview for stakeholders
- ✅ `functional-spec.md` - BA document (WHAT system does) with REAL features
- ✅ `technical-spec.md` - Architecture document (HOW to build) with target stack
- ✅ Stage prompts for Toolkit workflow (6 stages):
  - `constitution-prompt.md` - Principles for new system
  - `specify-prompt.md` - Requirements for specify stage (uses functional-spec.md)
  - `plan-prompt.md` - Architecture for plan stage (uses technical-spec.md)
  - `clarify-prompt.md` - Clarification guidance + "consult legacy app as source of truth"
  - `tasks-prompt.md` - Task breakdown guidance
  - `implement-prompt.md` - Implementation guidance + "consult legacy app as source of truth"

**Artifacts NOT Generated** (User Feedback):

- ❌ `recommended-constitution.md` - Not needed (replaced by constitution-prompt)
- ❌ `upgrade-plan.md` - Not needed (inline upgrade not goal; full modernization)
- ❌ `proposed-tech-stack.md` - Not needed (embedded in technical-spec.md)

---

#### 8.2 Implementation Tasks

##### Task 1: Create Interactive Analysis Prompt Template

- [x] ~~Create `templates/commands/analyze-project-interactive.md`~~ **Updated `analyze-project.md` directly instead**
- [x] Define multi-step workflow with clear sections
- [x] Add tech stack detection logic (sampling approach)
- [x] Add modernization preference questionnaire (10 questions)
- [x] Add deep analysis guidance (what to look for in legacy code)
- [x] Add artifact generation instructions with real examples

**Completed**: 2025-11-09 - Implemented in `templates/commands/analyze-project.md`

##### Task 2: Create Artifact Generation Templates

**Reference**: Used structure from `tmp/Meta-Prompt - Universal Meta-Prompt to Gen
BA_ARCH_EXEC_AIB_SPEC_JSON docs.md` (reference file later removed to fix markdownlint errors)

- [x] Create `templates/analysis/functional-spec-template.md`
  - **Base structure**: Meta-prompt Section A (Business Analysis)
  - **Adapt for legacy**: Add "Evidence" column with file:line references
  - **Sections**:
    - Executive Summary (WHAT/WHO/WHY extracted from code)
    - Problem & Goals (current state KPIs from legacy)
    - Personas & Journeys (from auth/user roles in code)
    - Functional Requirements (extracted with evidence: file:line)
    - Data Models (from DB schemas/migrations)
    - Configuration Mapping (all config files)
    - Known Quirks & Legacy Behaviors
  - **Placeholders**: `<<EXTRACT_FEATURES_FROM>>`, `<<EXTRACT_DATA_MODELS>>`,
    `<<EXTRACT_CONFIG>>`, etc.
- [x] Create `templates/analysis/technical-spec-template.md`
  - **Base structure**: Meta-prompt Section B (Architecture)
  - **Adapt for modernization**: Add "Legacy vs. Target" comparison
  - **Sections**:
    - Architectural Principles (extracted from legacy + new)
    - Why This Pattern (legacy pattern → target pattern + rationale)
    - Capabilities by Phase (50/30/15/5 with legacy features mapped)
    - High-Level Architecture (phase-colored Mermaid from meta-prompt)
    - Target Tech Stack (from user Q1-Q10 answers)
    - NFR Targets (SLO/SLI based on legacy + improvements)
    - Migration Path (strangler fig/big bang/hybrid)
  - **Placeholders**: `<<USER_CHOICE_LANGUAGE>>`, `<<USER_CHOICE_DATABASE>>`,
    `<<USER_CHOICE_DEPLOYMENT>>`, `<<LEGACY_PAIN_POINTS>>`, etc.
  - **Mermaid**: Use meta-prompt phase colors + adapt pattern for target infra
- [x] Create `templates/analysis/stage-prompt-templates/`
  - 6 template files: constitution, specify, plan, clarify, tasks, implement
  - Structure: Legacy Context + Modernization Guidance + Ready-to-Paste Prompt
  - Clarify & Implement prompts include: "Consult legacy app <<path>> as source of
    truth if specification is underspecified, ambiguous, or requires clarification"

**Completed**: 2025-11-09 - All templates created and markdownlint errors fixed

##### Task 3: Update analyze-project Command

- [x] Modify `templates/commands/analyze-project.md` to be INTERACTIVE-ONLY
- [x] ~~Remove non-interactive mode (arguments mode)~~ **Kept for script passthrough, removed confusing messaging**
- [x] Add "Act as senior developer and architect" guidance (already in Role & Mindset)
- [x] Add instruction to use Python analyzer for metrics only
- [x] Add instruction to use AI for semantic analysis and artifact generation

**Completed**: 2025-11-09 - Interactive workflow with 10 modernization questions implemented

##### Task 4: Remove Template-Only Python Generators

- [x] Remove `functional_spec_generator.py`
- [x] Remove `tech_stack_proposer.py`
- [x] Remove `prompt_generator.py`
- [x] Remove `principle_extractor.py`
- [x] Keep `report_generator.py` for analysis-report.md and metrics
- [x] Update `report_generator.py` imports to remove deleted generators

**Completed**: 2025-11-09 - All template-only generators removed, cleanup complete

##### Task 5: Update Python Analyzer Role

Python analyzer already focuses on **metrics and structure**:

- ✅ Tech stack detection (languages, frameworks, tools)
- ✅ Code metrics (LOC, complexity, test coverage)
- ✅ Dependency analysis (vulnerable packages, outdated versions)
- ✅ File structure analysis (directories, patterns)
- ✅ Generate `analysis-report.md` with technical findings

Python analyzer does NOT generate:

- ❌ Functional specifications (requires semantic understanding)
- ❌ Tech stack proposals (requires business context)
- ❌ Stage prompts (requires understanding of Toolkit workflow)

**Status**: Already correct - No changes needed

##### Task 6: Create Meta-Prompt Style Templates

**Reference**: Studied `tmp/Meta-Prompt - Universal Meta-Prompt to Gen
BA_ARCH_EXEC_AIB_SPEC_JSON docs.md` (file later removed)

- [x] Analyze meta-prompt structure and adapt for legacy code analysis:
  - **Section A (Business Analysis)** → Used for `functional-spec-template.md`
  - **Section B (Architecture)** → Used for `technical-spec-template.md`
  - **Mermaid patterns** → Adapted for target infrastructure (K8s, AWS, etc.)
  - **Phase coloring (50/30/15/5)** → Implemented in technical-spec template
  - **NFR measurability** → Convert legacy configs to SLO/SLI targets guidance added
  - **R→C→T traceability** → Mentioned in technical-spec template
  - **Determinism guardrails** → Use AI knowledge base for LTS (not hardcoded)
- [x] ~~Create `functional-spec-generator-prompt.md`~~ **Embedded in analyze-project.md Step 6**
- [x] ~~Create `technical-spec-generator-prompt.md`~~ **Embedded in analyze-project.md Step 6**

**Completed**: 2025-11-09 - Templates created with meta-prompt structure, guidance integrated into main prompt

##### Task 7: Integration Testing

- [ ] Test on real legacy project (e.g., Java 8 Spring Boot app)
- [ ] Validate that functional-spec.md contains REAL features (not templates)
- [ ] Validate that technical-spec.md contains target stack based on preferences
- [ ] Validate that stage prompts contain actual legacy code references
- [ ] Ensure artifacts can feed into Toolkit workflow successfully

**Status**: ⏳ User tested on ASP.NET project, identified UX issues (Phase 8.1)

---

#### 8.3 Implementation Plan (Phased Approach)

##### Week 1-2: Foundation & Design ✅ COMPLETED

- [x] Document current issues with detailed examples
- [x] Design new interactive workflow (state machine diagram)
- [x] Create wireframes for questionnaires (modernization preferences)
- [x] Study `tmp/Meta-Prompt - Universal Meta-Prompt...` thoroughly
  - Understand Section A (Business Analysis) structure
  - Understand Section B (Architecture) structure
  - Study Mermaid patterns and phase coloring
  - Study NFR measurability approach (SLO/SLI)
- [x] Design template structure for functional-spec.md (based on Section A)
- [x] Design template structure for technical-spec.md (based on Section B)
- [x] Get user approval on design before implementation

**Completed**: 2025-11-09

##### Week 3-4: Template Creation ✅ COMPLETED

- [x] Create `analyze-project-interactive.md` prompt template (updated `analyze-project.md` instead)
- [x] Create `functional-spec-template.md` with clear structure
- [x] Create `technical-spec-template.md` with clear structure
- [x] Create 6 stage-prompt templates
- [x] Add detailed examples in each template

**Completed**: 2025-11-09

##### Week 5-6: Refactoring ✅ COMPLETED

- [x] Update `analyze-project.md` command to use new workflow
- [x] Refactor or remove Python generators
- [x] Update Python analyzer to focus on metrics only (no changes needed)
- [x] Update `report_generator.py` to generate only technical reports
- [x] Test on sample legacy project (ASP.NET tested by user)

**Completed**: 2025-11-09

##### Week 7-8: Testing & Documentation ⏳ IN PROGRESS

- [ ] Test on 3 diverse legacy projects (Java, Python, Node.js)
- [x] Validate artifact quality (real content vs templates) - User confirmed good output
- [ ] Document new workflow in `docs/reverse-engineering.md`
- [ ] Create video walkthrough (optional)
- [x] Collect user feedback and iterate - **UX issues identified (see Phase 8.1)**

**Status**: User testing complete on ASP.NET project, UX improvements needed

---

#### 8.4 Success Criteria

##### Functional Requirements

- ✅ Analyze-project is INTERACTIVE-ONLY (no non-interactive mode)
- ✅ AI asks for PROJECT_PATH, ANALYSIS_DEPTH, FOCUS_AREAS upfront
- ✅ AI performs quick tech stack sampling and displays findings
- ✅ AI asks user about modernization preferences (target stack, deployment, IaC)
- ✅ AI performs deep analysis of legacy code (all files)
- ✅ AI asks clarification questions if needed
- ✅ AI generates artifacts with REAL content (not templates)

##### Artifact Quality

- ✅ `functional-spec.md` contains actual features from legacy code (with references)
- ✅ `technical-spec.md` contains target stack based on user preferences
- ✅ Stage prompts contain real legacy code references (file paths + line numbers)
- ✅ `analysis-report.md` contains technical metrics and findings
- ✅ `EXECUTIVE-SUMMARY.md` provides high-level overview for stakeholders

##### Integration

- ✅ Generated artifacts feed seamlessly into Toolkit workflow
- ✅ `specify` stage can use functional-spec.md as input
- ✅ `plan` stage can use technical-spec.md as input
- ✅ `constitution` stage can use extracted principles
- ✅ Other stages can use corresponding stage prompts

##### User Experience (Phase 8)

- ✅ Clear guidance at each step of the workflow
- ✅ Reasonable defaults for modernization choices
- ✅ Ability to skip optional questions
- ✅ Progress indicators during analysis
- ✅ Estimated time for each phase
- ✅ Ability to resume if interrupted

---

#### 8.5 Key Design Principles

##### Principle 1: Python for Structure, AI for Semantics

Python analyzer detects tech stack, calculates metrics, finds vulnerabilities.
AI agent understands business logic, extracts requirements, proposes solutions.
Clear separation of responsibilities.

##### Principle 2: Interactive Over Automatic

Always ask user for preferences (don't assume). Provide reasonable defaults but
allow customization. Explain why each question matters.

##### Principle 3: Evidence-Based Analysis

Every finding includes file path + line number reference. Features extracted
from actual code, not guessed. Configurations mapped from actual config files.

##### Principle 4: Template + AI = Real Content

Templates provide structure and guidance. AI fills templates with real analysis
of legacy code. Similar to meta-prompt approach in regular Toolkit workflow.

##### Principle 5: Toolkit Workflow Integration

Generated artifacts must be usable by downstream stages. Stage prompts must be
ready-to-paste. Functional-spec.md must be consumable by specify stage.
Technical-spec.md must be consumable by plan stage.

---

**Note on Phase 7**: Phase 7 (Analysis-to-Spec Workflow Integration) was completed on 2025-11-08 but has been superseded by Phase 8 redesign based on user feedback. The Python generators created in Phase 7 produced template-only artifacts without real legacy code analysis. See "Completed Improvements" section for Phase 7 historical record.

---

### Phase 8.1 - UX Enhancements: Conditional Questions (MEDIUM PRIORITY) 🟡

**Current Problem** (User Feedback 2025-11-09):

After Phase 8 implementation, user testing revealed UX issues with the 10 modernization questions:

#### Issue 1: Confusing "Enter INTERACTIVE MODE" Message

**Problem**: The prompt says "Now I need to enter INTERACTIVE MODE since no specific arguments were provided" which is confusing because there's only one mode.

**Root Cause**: Legacy code from when we had both interactive and non-interactive modes. The `$ARGUMENTS` check is kept for bash/PowerShell script passthrough, but the messaging is outdated.

**Solution**:
- Remove "entering INTERACTIVE MODE" announcement
- Keep `$ARGUMENTS` parsing silently for script compatibility
- Directly say: "Please provide the following information:" (no mode explanation)

**Priority**: LOW - Minor UX polish, doesn't affect functionality

---

#### Issue 2: Irrelevant Questions

**Problem**: Asking questions that don't make sense based on detected stack or previous answers.

**Examples**:
- **Q3 (Message Bus)**: Code analysis shows "None detected" yet we ask 6 options
  - Why bad: Wastes time, feels like AI didn't pay attention
- **Q5 = "Keep traditional (IIS on Windows Server)"** then asking:
  - **Q6 (IaC)**: "Terraform? Kubernetes Helm charts?" (irrelevant for IIS)
  - **Q7 (Containerization)**: "Docker? Kubernetes?" (can't use with IIS)
  - Why absurd: IIS on Windows Server doesn't use these modern cloud tools

**Analysis** (Senior Architect Perspective):

**Approach A: Ask Everything (Current - Simple but Poor UX)**

Pros:
- ✓ Simple, consistent flow
- ✓ Might spark ideas ("I didn't know I could add message queue!")
- ✓ "None / Not needed" handles opt-out

Cons:
- ✗ Wastes time on irrelevant questions
- ✗ Poor UX - feels like AI isn't listening
- ✗ Asking about K8s after "keep traditional" is jarring

**Approach B: Conditional Skip Logic (Smart but Complex)**

Pros:
- ✓ Smart, context-aware
- ✓ Great UX - only relevant questions
- ✓ Faster workflow

Cons:
- ✗ Complex to implement (nested conditionals in prompts)
- ✗ Risk of skipping questions user wanted
- ✗ Harder to maintain

**Approach C: Hybrid - Mark Optional + Conditional ⭐ RECOMMENDED**

Question structure:
1. **Always ask**: Language, Database, Package Manager, Deployment
2. **Mark optional**: Questions for features not detected (Message Bus, Observability if none found)
3. **Conditional skip**: Q6-Q7 (IaC, Containerization) if Q5 = "traditional deployment"
4. **Educational notes**: Explain why we're skipping and when it might become relevant

Example:
```text
3. Message Bus/Queue [OPTIONAL - Not detected in legacy code]
   Current: None (email processing appears polling-based)

   Since your legacy app doesn't use message queues, you can skip this.
   However, modernization could benefit from async messaging for:
   - Email processing (background jobs instead of polling)
   - Future event-driven features

   Options:
   - [A] None / Not needed - Keep simple
   - [B] Redis Pub/Sub - Lightweight, also useful for caching
   - [C] Azure Service Bus - If going Azure
   - [D] Other (specify)
   Your choice (or press Enter to skip): ___

5. Target Deployment Infrastructure
   [Selected: A - Dedicated server (IIS) - Keep traditional]

6. Infrastructure as Code (IaC) [SKIPPED - Not applicable for traditional IIS]
   Note: If you later migrate to cloud, IaC becomes relevant.
   For Windows Server, deployment scripts or DSC are alternatives.

7. Containerization Strategy [SKIPPED - Not applicable for IIS]
   Note: Containerization requires migrating away from IIS.
   This becomes relevant if you choose cloud deployment in future.
```

**Benefits**:
- ✓ Respects user time (skip obviously irrelevant)
- ✓ Still allows discovery (optional = user can opt-in)
- ✓ Provides education (explain why question matters)
- ✓ Flexible (can still add message bus even if not detected)

---

#### Implementation Tasks

##### Task 1: Remove "Interactive Mode" Messaging

- [ ] Update `templates/commands/analyze-project.md` User Input section
- [ ] Remove "Enter INTERACTIVE MODE:" announcement
- [ ] Keep `$ARGUMENTS` parsing for script compatibility
- [ ] Change to direct: "Please provide the following information:"

**Complexity**: LOW (simple text change)

##### Task 2: Implement Conditional Question Logic

- [ ] Add detection flags after tech stack analysis:
  - `HAS_MESSAGE_BUS`: true/false (from code analysis)
  - `HAS_OBSERVABILITY`: true/false (logging, monitoring configs detected)
  - `IS_TRADITIONAL_DEPLOYMENT`: true/false (based on Q5 answer)
- [ ] Update Step 3 (Modernization Questions):
  - **Q1-Q2**: Always ask (Language, Database)
  - **Q3**: Mark `[OPTIONAL - Not detected]` if `!HAS_MESSAGE_BUS`
  - **Q4**: Always ask (Package Manager)
  - **Q5**: Always ask (Deployment)
  - **Q6-Q7**: Skip with `[Not applicable]` note if `IS_TRADITIONAL_DEPLOYMENT`
  - **Q8**: Mark `[OPTIONAL - Not detected]` if `!HAS_OBSERVABILITY`
  - **Q9-Q10**: Always ask (Auth, Testing)
- [ ] Add educational notes explaining:
  - Why question is optional/skipped
  - When it might become relevant
  - Alternatives for current choice

**Complexity**: MEDIUM (conditional logic in prompts)

##### Task 3: Add "Press Enter to Skip" UX

- [ ] For optional questions, add: `Your choice (or press Enter to skip): ___`
- [ ] For skipped questions, show: `[SKIPPED - Reason]` with future guidance
- [ ] Validate that AI handles empty/skipped responses gracefully

**Complexity**: MEDIUM (requires prompt flow testing)

---

#### Implementation Priority

**Phase 8.1a (Quick Win - Days)**:
- Fix "Enter INTERACTIVE MODE" messaging
- Add `[OPTIONAL]` and `[SKIPPED]` markers based on detection

**Phase 8.1b (Full Solution - Weeks)**:
- Implement full conditional logic
- Add educational notes
- Test on multiple scenarios (traditional vs cloud deployments)

**Recommendation**: Start with Phase 8.1a for immediate UX improvement, then iterate to Phase 8.1b based on user feedback.

---

**Status**: 📋 Documented (2025-11-09) - Awaiting user approval on approach

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
