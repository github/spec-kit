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

#### Approach A: Ask Everything (Current - Simple but Poor UX)

Pros:

- ✓ Simple, consistent flow
- ✓ Might spark ideas ("I didn't know I could add message queue!")
- ✓ "None / Not needed" handles opt-out

Cons:

- ✗ Wastes time on irrelevant questions
- ✗ Poor UX - feels like AI isn't listening
- ✗ Asking about K8s after "keep traditional" is jarring

#### Approach B: Conditional Skip Logic (Smart but Complex)

Pros:

- ✓ Smart, context-aware
- ✓ Great UX - only relevant questions
- ✓ Faster workflow

Cons:

- ✗ Complex to implement (nested conditionals in prompts)
- ✗ Risk of skipping questions user wanted
- ✗ Harder to maintain

#### Approach C: Hybrid - Mark Optional + Conditional ⭐ RECOMMENDED

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

##### Task 1: Remove "Interactive Mode" Messaging ✅ COMPLETED (2025-11-09)

- [x] Update `templates/commands/analyze-project.md` User Input section
- [x] Remove "Enter INTERACTIVE MODE:" announcement
- [x] Keep `$ARGUMENTS` parsing for script compatibility
- [x] Change to direct: "Please provide the following information:"

**Complexity**: LOW (simple text change)

##### Task 2: Implement Conditional Question Logic ✅ COMPLETED (2025-11-09)

- [x] Add detection flags after tech stack analysis:
  - `HAS_MESSAGE_BUS`: true/false (from code analysis)
  - `HAS_OBSERVABILITY`: true/false (logging, monitoring configs detected)
  - `IS_TRADITIONAL_DEPLOYMENT`: true/false (based on Q5 answer)
- [x] Update Step 3 (Modernization Questions):
  - **Q1-Q2**: Always ask (Language, Database)
  - **Q3**: Mark `[OPTIONAL - Not detected]` if `!HAS_MESSAGE_BUS`
  - **Q4**: Always ask (Package Manager)
  - **Q5**: Always ask (Deployment)
  - **Q6-Q7**: Skip with `[Not applicable]` note if `IS_TRADITIONAL_DEPLOYMENT`
  - **Q8**: Mark `[OPTIONAL - Not detected]` if `!HAS_OBSERVABILITY`
  - **Q9-Q10**: Always ask (Auth, Testing)
- [x] Add educational notes explaining:
  - Why question is optional/skipped
  - When it might become relevant
  - Alternatives for current choice

**Complexity**: MEDIUM (conditional logic in prompts)

##### Task 3: Add "Press Enter to Skip" UX ✅ COMPLETED (2025-11-09)

- [x] For optional questions, add: `Your choice (or press Enter to skip): ___`
- [x] For skipped questions, show: `[SKIPPED - Reason]` with future guidance
- [x] Validate that AI handles empty/skipped responses gracefully

**Complexity**: MEDIUM (requires prompt flow testing)

---

#### Implementation Priority

**Phase 8.1a (Quick Win - Days)**: ✅ COMPLETED (2025-11-09)

- [x] Fix "Enter INTERACTIVE MODE" messaging
- [x] Add `[OPTIONAL]` and `[SKIPPED]` markers based on detection

**Phase 8.1b (Full Solution - Weeks)**: ✅ COMPLETED (2025-11-09)

- [x] Implement full conditional logic
- [x] Add educational notes
- [ ] Test on multiple scenarios (traditional vs cloud deployments) - **Requires user testing**

**Recommendation**: Phase 8.1a and 8.1b implementation complete. User testing recommended on real projects.

---

**Status**: ✅ IMPLEMENTED (2025-11-09) - Ready for user testing

---

### Phase 9 - Cross-Cutting Concern Analysis (HIGH PRIORITY) 🔴

**Status**: ✅ IMPLEMENTED - Core functionality complete, needs user testing

**User Requirement** (2025-11-11):

Extend analyze-project to support **targeted cross-cutting concern migration** in addition to full application modernization.

**Business Context**:

Modern applications need to migrate specific cross-cutting concerns without rewriting the entire app:

- **Auth migration**: Custom JWT → Okta/Auth0/Azure AD
- **Database migration**: RDBMS → NoSQL (PostgreSQL → MongoDB)
- **Caching**: Add/replace caching layer (Memcached → Redis)
- **Messaging**: Migrate message bus (TIBCO → Kafka, RabbitMQ → Azure Service Bus)
- **Observability**: Custom logging → ELK/Prometheus/DataDog

**Current Gap**:

The analyze-project feature analyzes **entire applications** for full modernization. It cannot:

- ❌ Analyze only authentication code while ignoring other features
- ❌ Assess abstraction quality of a specific concern
- ❌ Recommend migration strategies for isolated concerns
- ❌ Provide concern-specific impact analysis
- ❌ Check if proper abstractions exist for easy swapping

---

#### 9.1 Architecture Assessment & Design

**Senior Developer/Architect Analysis**:

##### Design Constraint: AI-Driven Analysis (No Python Dependencies)

**User Requirement**:
- ❌ NO new Python modules (Python analyzer didn't perform well)
- ❌ NO additional dependencies (end users may not have them installed)
- ✅ AI agent performs ALL semantic analysis (like full app analysis)
- ✅ Bash/PowerShell ONLY for orchestration/setup

**Rationale**:
- Current full app analysis proves AI can understand code semantics
- AI already does: pattern recognition, abstraction assessment, impact analysis
- Python was only used for basic metrics (not needed for concern analysis)
- Simpler architecture, no dependency management issues

##### Current Architecture Strengths

1. **AI-Driven Workflow** (Phase 8)
   - AI agent reads code, understands patterns, generates real analysis
   - Interactive 10-question workflow
   - Prompt engineering guides AI behavior
   - No Python needed for semantic understanding

2. **Lightweight Orchestration**
   - Bash/PowerShell scripts for setup, file enumeration
   - AI agent does heavy lifting (semantic analysis)
   - No external tool dependencies

3. **Corporate Guidelines Integration**
   - Checks compliance with organizational standards
   - Multi-stack support (React+Java, Node+Python)

4. **Extensible Template System**
   - functional-spec-template.md (WHAT system does)
   - technical-spec-template.md (HOW to build)
   - stage-prompts/ for Toolkit workflow integration

##### Extension Points for Cross-Cutting Concerns

**Extension Point 1: Scope Selection (analyze-project.md:60-85)**

Current:

```text
## User Input & Interactive Mode

$ARGUMENTS

**IF** `$ARGUMENTS` is empty or contains the literal text "$ARGUMENTS":
   Please provide the following information:
   PROJECT_PATH: /path/to/existing/project
```

Proposed Enhancement:

```text
## User Input & Interactive Mode

$ARGUMENTS

**IF** `$ARGUMENTS` is empty:
   Please provide the following information:

   PROJECT_PATH: /path/to/existing/project

   ANALYSIS_SCOPE:
   - [A] Full Application Modernization (entire codebase)
   - [B] Cross-Cutting Concern Migration (specific area)
   Your choice: ___

   **IF CHOICE = [B]**, ask follow-up:

   CONCERN_TYPE:
   - [1] Authentication/Authorization
   - [2] Database/ORM Layer
   - [3] Caching Layer
   - [4] Message Bus/Queue
   - [5] Logging/Observability
   - [6] API Gateway/Routing
   - [7] File Storage/CDN
   - [8] Deployment/Infrastructure
   - [9] Other (specify)
   Your choice: ___

   CURRENT_IMPLEMENTATION: ___  (detected from code, user confirms)
   TARGET_IMPLEMENTATION: ___   (e.g., "Migrate to Okta", "VM → OpenShift", "AWS → Azure")
```

**Extension Point 2: AI Analysis Guidance (analyze-project.md Step 4)**

Current: AI analyzes entire codebase

Proposed Enhancement: Add concern-specific analysis instructions

```markdown
## Step 4: Deep Code Analysis

**IF ANALYSIS_SCOPE = [A] Full Application:**
   [Current behavior - analyze entire codebase]

**IF ANALYSIS_SCOPE = [B] Cross-Cutting Concern:**

### Concern-Specific Analysis Instructions

You are analyzing ONLY the <<CONCERN_TYPE>> concern. Focus your analysis on:

#### 1. Identify Concern-Specific Files

Use these detection heuristics:

**For Authentication/Authorization:**
- File patterns: auth*, login*, session*, jwt*, passport*, oauth*, security*
- Import patterns: jsonwebtoken, passport, bcrypt, oauth, jose
- Decorator patterns: @authenticated, @require_auth, @authorize
- Config files: auth.config.*, security.yml, passport.config.*

**For Database/ORM Layer:**
- File patterns: *repository*, *model*, *entity*, *dao*, db*, database*
- Import patterns: sequelize, mongoose, typeorm, prisma, knex
- Migrations: migrations/*, db/migrate/*
- Config files: database.yml, ormconfig.*, knexfile.*

**For Caching Layer:**
- File patterns: *cache*, *redis*, *memcache*
- Import patterns: redis, node-cache, memcached, ioredis
- Decorator patterns: @Cacheable, @CacheEvict
- Config files: redis.conf, cache.config.*

[Similar patterns for other 5 concern types...]

#### 2. Analyze Abstraction Level (HIGH/MEDIUM/LOW)

**HIGH Abstraction Indicators:**
- Single interface/contract (e.g., IAuthProvider, IRepository)
- Dependency injection used throughout
- No direct implementation imports in consumers
- Example: All auth consumers import IAuthProvider, not JWTAuthProvider

**MEDIUM Abstraction Indicators:**
- Multiple entry points but consistent pattern
- Some direct dependencies mixed with abstraction
- Partial use of interfaces

**LOW Abstraction Indicators:**
- Implementation scattered across codebase
- Direct imports of concrete classes everywhere
- No interfaces or contracts defined
- Example: passport.authenticate() called directly in 47 places

Provide evidence with file:line references for your assessment.

#### 3. Calculate Blast Radius

Count and report:
- **Files affected**: How many files import/use this concern
- **LOC affected**: Approximate lines of code
- **Percentage**: X% of total codebase
- **Test impact**: How many test files need updating

#### 4. Assess Coupling Degree (LOOSE/MODERATE/TIGHT)

**LOOSE Coupling:**
- Concern accessed only via interface
- No circular dependencies
- Easy to mock for testing

**MODERATE Coupling:**
- Some direct dependencies
- Few circular references
- Moderate test complexity

**TIGHT Coupling:**
- Direct implementation dependencies throughout
- Circular dependencies present
- Concern code mixed with business logic

#### 5. Recommend Migration Strategy

Based on abstraction level + blast radius + coupling:

**IF** high_abstraction AND loose_coupling:
   → STRANGLER_FIG (low risk, 2-4 weeks)

**ELSE IF** medium_abstraction:
   → ADAPTER_PATTERN (medium risk, 4-8 weeks)

**ELSE IF** low_abstraction AND blast_radius < 20%:
   → REFACTOR_FIRST (medium risk, 6-12 weeks)

**ELSE**:
   → BIG_BANG_WITH_FEATURE_FLAGS (high risk, 3-6 months)

Explain your reasoning with evidence.
```

**Extension Point 3: New Templates (AI-Generated Content)**

Proposed templates for concern-specific analysis:

1. **concern-analysis-template.md**

```markdown
# Cross-Cutting Concern Analysis: <<CONCERN_TYPE>>

## Executive Summary

**Concern**: <<e.g., Authentication/Authorization>>
**Current**: <<e.g., Custom JWT implementation>>
**Target**: <<e.g., Migrate to Okta>>
**Recommendation**: <<STRANGLER_FIG | ADAPTER_PATTERN | etc.>>
**Risk**: <<LOW/MEDIUM/HIGH>>
**Effort**: <<2-4 weeks>>

## Current Implementation Analysis

### Entry Points (file:line references)

| Entry Point | Type | Usage Count | Evidence |
|-------------|------|-------------|----------|
| AuthService.authenticate() | Interface | 47 callsites | src/auth/AuthService.ts:23 |
| verifyToken() | Direct function | 12 callsites | src/middleware/auth.js:45 |

### Abstraction Assessment

**Level**: <<HIGH/MEDIUM/LOW>>

**Rationale**:
- <<Evidence 1>> (file:line)
- <<Evidence 2>> (file:line)

### Coupling Analysis

**Degree**: <<LOOSE/MODERATE/TIGHT>>

**Dependencies**:
- Database: User table (tight coupling - schema changes needed)
- API: 23 endpoints depend on auth middleware
- Frontend: 15 components check auth state

### Blast Radius

- Files affected: <<N>> files (<<X>>% of codebase)
- LOC affected: <<M>> lines
- Tests to update: <<T>> test files

## Missing Abstractions

**What's Missing**:
1. <<Abstraction 1>>: <<Why needed>> (file:line showing problem)
2. <<Abstraction 2>>: <<Why needed>> (file:line showing problem)

**Recommended Abstractions**:
- Create IAuthProvider interface
- Extract TokenService for token management
- Add AuthContext for dependency injection

## Migration Strategy

**Approach**: <<STRANGLER_FIG>>

**Phasing** (50/30/15/5):

### Phase 1 (50% value): Core Migration
- Week 1-2: Implement OktaAuthProvider with IAuthProvider interface
- Week 3: Dual-auth mode (support both JWT and Okta)
- Week 4: Route 10% traffic to Okta (canary)

### Phase 2 (30% value): Rollout
- Week 5: Route 50% traffic to Okta
- Week 6: Full cutover with feature flag

### Phase 3 (15% value): Cleanup
- Week 7: Remove legacy JWT code
- Week 8: Update tests and documentation

### Phase 4 (5% value): Future-Proofing
- Add abstraction layer for easy provider swapping
- Document migration lessons learned

## Rollback Strategy

- Feature flag: `USE_OKTA_AUTH` (instant rollback)
- Database: No schema changes (rollback safe)
- API: Backward compatible tokens during transition

## Impact on Other Concerns

| Concern | Impact | Mitigation |
|---------|--------|------------|
| Database | None | Auth tokens in separate table |
| Caching | Session cache keys change | Update cache prefix |
| Logging | Auth events format changes | Update log parsers |

## Testing Strategy

- Unit tests: Update 47 auth-related tests
- Integration tests: Add Okta mock server
- E2E tests: Test both auth flows during transition

## Success Criteria

- ✅ Zero downtime during migration
- ✅ 100% feature parity with legacy auth
- ✅ < 5% performance degradation
- ✅ Instant rollback capability

---

## Appendix: Detailed Evidence

### File-by-File Analysis
...
```

2. **abstraction-recommendations-template.md**

```markdown
# Abstraction Recommendations: <<CONCERN_TYPE>>

## Current Architecture Gaps

### Gap 1: <<Gap Name>>
**Problem**: <<Description with file:line>>
**Impact**: <<Why this makes migration harder>>
**Recommendation**: <<How to fix>>

## Recommended Abstraction Patterns

### Pattern 1: Repository Pattern (for Database concern)
**Why**: Isolates data access logic
**Implementation**:
- Create IRepository<T> interface
- Implement PostgresRepository and MongoRepository
- Swap at runtime via dependency injection

### Pattern 2: Strategy Pattern (for Auth concern)
**Why**: Allows swapping auth providers
**Implementation**:
- Create IAuthProvider interface
- Implement JWTProvider, OktaProvider, Auth0Provider
- Select via configuration

## Refactoring Roadmap

### Phase 1: Extract Interfaces (1-2 weeks)
- [ ] Define IAuthProvider interface
- [ ] Define ITokenService interface
- [ ] Add dependency injection container

### Phase 2: Migrate to Interfaces (2-3 weeks)
- [ ] Update all callsites to use interfaces
- [ ] Remove direct implementation dependencies
- [ ] Add integration tests

### Phase 3: Implement New Provider (1-2 weeks)
- [ ] Create OktaAuthProvider implementing IAuthProvider
- [ ] Add configuration management
- [ ] Test side-by-side with legacy

## Future-Proofing

**Design for Change**:
- Use interfaces, not concrete classes
- Inject dependencies, don't hardcode
- Config-driven provider selection
- Feature flags for gradual rollout

**Next Migration Will Be Easy**:
- Okta → Auth0: Just implement Auth0Provider
- PostgreSQL → MongoDB: Just implement MongoRepository
- Redis → Memcached: Just implement MemcachedCache
```

---

#### 9.2 Implementation Tasks (AI-Driven, No Python)

##### Task 1: Enhance analyze-project.md Prompt ✨ DESIGN COMPLETE

**Changes**:

1. Add "ANALYSIS_SCOPE" question (Full App vs Cross-Cutting Concern)
2. Add "CONCERN_TYPE" follow-up question (8 common concerns)
3. Add "CURRENT_IMPLEMENTATION" and "TARGET_IMPLEMENTATION" inputs
4. Add Step 4 concern-specific analysis instructions:
   - Detection heuristics for 8 concern types
   - Abstraction level assessment criteria (HIGH/MEDIUM/LOW)
   - Blast radius calculation guidance
   - Coupling degree assessment criteria
   - Migration strategy decision tree
5. Add Step 6 conditional artifact generation logic

**Complexity**: MEDIUM (prompt template update with comprehensive guidance)

**Estimated Effort**: 4-6 hours

**No Python Code**: ✅ Pure prompt engineering

##### Task 2: Create Concern-Specific Templates ✨ DESIGN COMPLETE

**Templates to Create** (AI fills with real analysis):

1. `templates/analysis/concern-analysis-template.md`
   - Executive summary (concern, current, target, recommendation, risk, effort)
   - Entry points table (with file:line evidence)
   - Abstraction assessment (with rationale)
   - Coupling analysis (with dependencies)
   - Blast radius (files/LOC/percentage)
   - Missing abstractions (gaps with evidence)
   - Migration strategy (phased 50/30/15/5)
   - Rollback strategy
   - Impact on other concerns
   - Testing strategy

2. `templates/analysis/abstraction-recommendations-template.md`
   - Current architecture gaps (with file:line)
   - Recommended patterns (Repository, Strategy, Adapter, etc.)
   - Refactoring roadmap (phased approach)
   - Future-proofing guidance

3. `templates/analysis/concern-migration-plan-template.md`
   - Detailed phased rollout plan
   - Risk assessment with mitigation
   - Rollback procedures
   - Monitoring and success criteria

**Complexity**: MEDIUM (template creation with clear structure)

**Estimated Effort**: 1-2 days

**No Python Code**: ✅ Pure markdown templates

##### Task 3: Update Bash/PowerShell Scripts (Optional) ⏳ FUTURE

**Optional Enhancement** (not required for MVP):

- Add concern-type-specific file enumeration (optimization only)
- Example: If concern=auth, enumerate auth* files first
- Still lightweight, no heavy processing

**Complexity**: LOW (simple file globbing)

**Estimated Effort**: 2-3 hours

**No Python Code**: ✅ Pure bash/PowerShell

##### Task 4: Integration Testing ⏳ FUTURE

- Test on real projects with different concern types
- Validate AI's abstraction detection accuracy
- Validate AI's migration strategy recommendations
- Ensure generated artifacts are actionable
- Compare AI analysis quality vs Python analyzer

**Complexity**: MEDIUM (manual testing, qualitative assessment)

**Estimated Effort**: 1-2 weeks

**No Python Code**: ✅ AI-driven analysis only

---

#### 9.3 Decision Logic (AI-Guided, Embedded in Prompts)

**NO Python algorithms** - All decision logic is embedded in AI prompt instructions.

##### Abstraction Level Assessment (Prompt Guidance)

AI follows these criteria (from analyze-project.md Step 4):

**HIGH Abstraction:**
- Single interface/contract found
- Dependency injection used throughout
- No direct implementation imports in consumers
- **AI evaluates** code patterns and assigns HIGH

**MEDIUM Abstraction:**
- Multiple entry points but consistent pattern
- Some direct dependencies mixed with abstraction
- Partial use of interfaces
- **AI evaluates** code patterns and assigns MEDIUM

**LOW Abstraction:**
- Implementation scattered across codebase
- Direct imports of concrete classes everywhere
- No interfaces or contracts defined
- **AI evaluates** code patterns and assigns LOW

**Evidence Required:** AI must provide file:line references for assessment

##### Migration Strategy Selection (Prompt Guidance)

AI follows this decision tree (from analyze-project.md Step 4):

```
IF abstraction=HIGH AND coupling=LOOSE:
   → Recommend: STRANGLER_FIG
   → Risk: LOW
   → Effort: 2-4 weeks
   → Rationale: Clean interfaces allow gradual replacement

ELSE IF abstraction=MEDIUM:
   → Recommend: ADAPTER_PATTERN
   → Risk: MEDIUM
   → Effort: 4-8 weeks
   → Rationale: Add abstraction layer first, then migrate

ELSE IF abstraction=LOW AND blast_radius<20%:
   → Recommend: REFACTOR_FIRST
   → Risk: MEDIUM
   → Effort: 6-12 weeks
   → Rationale: Small enough to refactor, then migrate

ELSE (abstraction=LOW AND blast_radius>=20%):
   → Recommend: BIG_BANG_WITH_FEATURE_FLAGS
   → Risk: HIGH
   → Effort: 3-6 months
   → Rationale: Extensive changes required, use feature flags for safety
```

**AI Applies Logic:** No hardcoded algorithms, AI interprets guidance and applies to specific codebase

---

#### 9.4 Example User Scenarios

##### Scenario 1: Auth Migration (High Abstraction) ✅ IDEAL CASE

**User Input**:

```text
ANALYSIS_SCOPE: [B] Cross-Cutting Concern Migration
CONCERN_TYPE: [1] Authentication/Authorization
CURRENT_IMPLEMENTATION: Custom JWT with PassportJS
TARGET_IMPLEMENTATION: Migrate to Okta
```

**AI Analysis Result**:

```text
Detected Auth Implementation:
- Entry Point: src/auth/AuthService.ts (single interface)
- Pattern: Clean interface, dependency injection used
- Abstraction Level: HIGH
- Files Affected: 15 files import IAuthProvider interface
- Blast Radius: 8% of codebase
- Coupling: LOOSE (no direct dependencies on JWT implementation)

Recommendation:
- Strategy: STRANGLER_FIG
- Risk: LOW
- Effort: 2-3 weeks

Phasing:
- P1 (50%): Implement OktaAuthProvider with IAuthProvider interface (Week 1-2)
- P2 (30%): Canary rollout (10% → 50% → 100%) with feature flag (Week 3)
- P3 (15%): Remove legacy JWT code (Week 4)
- P4 (5%): Documentation and future-proofing

Rollback: Feature flag `USE_OKTA_AUTH` allows instant rollback
```

##### Scenario 2: Database Migration (Low Abstraction) ⚠️ COMPLEX CASE

**User Input**:

```text
ANALYSIS_SCOPE: [B] Cross-Cutting Concern Migration
CONCERN_TYPE: [2] Database/ORM Layer
CURRENT_IMPLEMENTATION: PostgreSQL with raw SQL queries
TARGET_IMPLEMENTATION: Migrate to MongoDB
```

**AI Analysis Result**:

```text
Detected Database Implementation:
- Entry Points: 47 files with direct SQL queries (no ORM, no repository pattern)
- Pattern: Raw SQL scattered throughout services and controllers
- Abstraction Level: LOW
- Files Affected: 47 files (68% of codebase)
- Blast Radius: 80% of codebase (includes tests)
- Coupling: TIGHT (direct SQL in business logic)

Recommendation:
- Strategy: REFACTOR_FIRST + STRANGLER_FIG
- Risk: HIGH
- Effort: 3-6 months

Missing Abstractions:
1. No IRepository interface
2. No data access layer
3. No domain models (anemic data classes)

Phasing:
- P1 (40%): Extract data access layer with IRepository interface (Month 1-2)
  - Create Repository pattern for each entity
  - Migrate services to use repositories
  - Add integration tests
- P2 (40%): Implement dual-write (Postgres + Mongo) (Month 3-4)
  - Implement MongoRepository for each entity
  - Add schema mapping layer
  - Sync data bidirectionally
- P3 (15%): Gradual read cutover (Month 5)
  - Route reads to Mongo with Postgres fallback
  - Monitor data consistency
  - Fix schema mismatches
- P4 (5%): Decommission Postgres (Month 6)
  - Remove Postgres repositories
  - Clean up migration code

Rollback: Dual-write allows rollback until P4 complete
Critical: Schema mapping required (Postgres relational → Mongo document)
```

##### Scenario 3: Adding Caching (Greenfield) ✨ NEW FEATURE

**User Input**:

```text
ANALYSIS_SCOPE: [B] Cross-Cutting Concern Migration
CONCERN_TYPE: [3] Caching Layer
CURRENT_IMPLEMENTATION: None (no caching detected)
TARGET_IMPLEMENTATION: Add Redis caching layer
```

**AI Analysis Result**:

```text
Detected Caching Implementation:
- Entry Points: None (no caching currently)
- Hot Paths Identified: 12 endpoints with direct DB queries on every request
  - getUserProfile() - 1.2s average (file:line)
  - getProductList() - 800ms average (file:line)
  - searchOrders() - 2.1s average (file:line)

Recommendation:
- Strategy: DECORATOR_PATTERN + GRADUAL_ROLLOUT
- Risk: LOW (additive change, no breaking changes)
- Effort: 2-4 weeks

Phasing:
- P1 (20%): Create caching abstraction (Week 1)
  - Define ICacheService interface
  - Implement RedisCacheService
  - Add cache configuration
- P2 (60%): Add @Cacheable decorator to hot paths (Week 2-3)
  - Start with getUserProfile (highest impact)
  - Add cache invalidation on updates
  - Monitor cache hit rates
- P3 (15%): Tune and expand (Week 4)
  - Adjust TTLs based on hit rate data
  - Add caching to more endpoints
  - Implement cache warming for critical data
- P4 (5%): Documentation and monitoring
  - Add cache metrics dashboard
  - Document caching strategy

Rollback: Feature flag `ENABLE_REDIS_CACHE` allows instant disable
No data migration needed (cache is ephemeral)
```

---

#### 9.5 Design Principles

**Principle 1: Concern Identification via Multiple Signals**

Use layered detection:

1. **Naming Patterns**: Files/classes with concern keywords (auth*, cache*, db*, queue*)
2. **Import Analysis**: Libraries used (jsonwebtoken, mongoose, redis, kafka-node)
3. **Decorator/Annotation Patterns**: @Authenticated, @Transactional, @Cacheable
4. **Configuration Files**: auth.config.js, database.yml, redis.conf
5. **Call Graph Analysis**: Which functions call the concern's functions?

**Principle 2: Abstraction Quality Assessment**

Three-level taxonomy:

- **HIGH Abstraction**:
  - Single interface/contract
  - Dependency injection used
  - No direct implementation imports
  - Easy to swap implementations

- **MEDIUM Abstraction**:
  - Multiple entry points but consistent
  - Some direct dependencies
  - Mixed abstraction levels
  - Requires adapter layer

- **LOW Abstraction**:
  - Scattered across codebase
  - Direct implementation dependencies
  - No interfaces or contracts
  - Requires refactoring before migration

**Principle 3: Risk-Based Strategy Selection**

Migration strategy based on abstraction + coupling + blast radius:

```
IF high_abstraction AND loose_coupling THEN
    strategy = STRANGLER_FIG (low risk, incremental)
ELSE IF medium_abstraction THEN
    strategy = ADAPTER_PATTERN (moderate risk, add abstraction layer first)
ELSE IF low_abstraction AND small_blast_radius (<20%) THEN
    strategy = REFACTOR_FIRST (moderate risk, worth refactoring)
ELSE
    strategy = BIG_BANG_WITH_FEATURE_FLAGS (high risk, extensive changes)
END IF
```

**Principle 4: Phased Rollout with Rollback Points**

Every migration strategy includes:

- **Dual-running phase**: Old and new implementations coexist
- **Feature flags**: Instant rollback capability
- **Canary rollout**: Gradual traffic shifting (10% → 50% → 100%)
- **Monitoring**: Metrics to detect regressions
- **Rollback triggers**: Automated rollback on error rate spike

**Principle 5: Future-Proofing via Abstraction**

Every concern migration should:

- Add missing abstractions (interfaces, contracts)
- Use dependency injection
- Make provider selection config-driven
- Document migration lessons learned
- Ensure next migration is easier

---

#### 9.6 Success Criteria

##### Functional Requirements

- ✅ User can select "Cross-Cutting Concern" scope
- ✅ User can specify concern type (8 common concerns)
- ✅ AI detects concern-specific code accurately (>90% precision)
- ✅ AI assesses abstraction level (HIGH/MEDIUM/LOW)
- ✅ AI calculates blast radius (files/LOC affected)
- ✅ AI recommends migration strategy with rationale
- ✅ AI identifies missing abstractions with evidence
- ✅ AI generates actionable phased rollout plan

##### Artifact Quality

- ✅ `concern-analysis.md` contains real analysis (not template)
  - File:line references for all findings
  - Evidence-based abstraction assessment
  - Accurate blast radius calculation

- ✅ `abstraction-recommendations.md` provides actionable refactoring guidance
  - Clear gap identification with evidence
  - Recommended patterns with rationale
  - Phased refactoring roadmap

- ✅ `concern-migration-plan.md` includes detailed strategy
  - Risk assessment with mitigation
  - Phased rollout (50/30/15/5 value delivery)
  - Rollback procedures
  - Testing strategy

##### Integration

- ✅ Seamless integration with existing analyze-project workflow
- ✅ Backward compatible (full app analysis still works)
- ✅ Generated artifacts feed into Toolkit workflow
- ✅ Corporate guidelines checking for concern-specific code

---

#### 9.7 Implementation Plan (AI-Driven, No Python)

**Total Timeline**: 1-2 weeks (vs 11 weeks with Python)

##### Day 1-2: Prompt Enhancement ✅ COMPLETE

- [x] Update `templates/commands/analyze-project.md`:
  - [x] Add "ANALYSIS_SCOPE" question (Full App vs Cross-Cutting Concern)
  - [x] Add "CONCERN_TYPE" follow-up (9 concern types including Deployment/Infrastructure)
  - [x] Add "CURRENT_IMPLEMENTATION" / "TARGET_IMPLEMENTATION" inputs
  - [x] Add Step 4 concern-specific analysis instructions:
    - [x] Detection heuristics for all 9 concern types
    - [x] Abstraction level assessment criteria
    - [x] Blast radius calculation guidance
    - [x] Coupling degree assessment criteria
    - [x] Migration strategy decision tree
  - [x] Add Step 6 conditional artifact generation logic

**Deliverable**: ✅ Updated analyze-project.md with concern-specific workflow

**No Python**: ✅ Pure prompt engineering

**Actual Effort**: ~4 hours (as estimated)

**Commit**: `307b095` - feat: Implement Phase 9 - Cross-Cutting Concern Analysis

##### Day 3-4: Template Creation ✅ COMPLETE

- [x] Create `templates/analysis/concern-analysis-template.md` (comprehensive 10-section template)
- [x] Create `templates/analysis/abstraction-recommendations-template.md` (conditional HIGH/MEDIUM/LOW guidance)
- [x] Create `templates/analysis/concern-migration-plan-template.md` (detailed phased migration with 4 strategies)
- [x] Add examples and clear structure to all templates

**Deliverable**: ✅ 3 new templates with comprehensive structure

**No Python**: ✅ Pure markdown templates

**Actual Effort**: ~3 hours (better than 1-2 days estimate)

**Commit**: `307b095` - feat: Implement Phase 9 - Cross-Cutting Concern Analysis

##### Day 5-7: Testing & Iteration ⏳ FUTURE

- [ ] Test on 3 real projects with different concerns:
  - [ ] Auth migration (expect HIGH abstraction)
  - [ ] Database migration (expect LOW abstraction)
  - [ ] Adding caching (greenfield case)
- [ ] Validate AI analysis quality
- [ ] Iterate on prompt instructions based on findings
- [ ] Collect user feedback

**Deliverable**: Validated concern analysis feature

**No Python**: ✅ AI-driven analysis validation

**Estimated Effort**: 2-3 days

##### Day 8-9: Documentation ✅ COMPLETE

- [x] Update `docs/reverse-engineering.md` with concern analysis section
- [x] Added Step 2.5: Choose Analysis Scope (Full App vs Concern Migration)
- [x] Listed all 9 concern types with examples
- [x] Documented concern-specific analysis workflow
- [x] Added Step 4 artifacts for concern migration
- [ ] Add example walkthroughs for each concern type (FUTURE - after user testing)
- [ ] Update README.md with new capability (FUTURE - after user testing)
- [x] Update IMPROVEMENTS.md status

**Deliverable**: ✅ Core documentation complete (docs/reverse-engineering.md updated)

**No Python**: ✅ Documentation only

**Actual Effort**: ~2 hours

**Commit**: `80bb393` - docs: Document Phase 9 - Cross-Cutting Concern Analysis

---

#### 9.8 Quick Wins ✅ COMPLETE

**Immediate Tasks** (2-4 hours):

- [x] Add "ANALYSIS_SCOPE" question to analyze-project.md
- [x] Add "CONCERN_TYPE" follow-up question (9 types including Deployment/Infrastructure)
- [x] Add detection heuristics for ALL concern types (not just Auth)
- [x] Add complete analysis workflow (abstraction, blast radius, coupling, strategy)
- [x] Create all 3 templates (concern-analysis, abstraction-recommendations, migration-plan)

**Impact**: ✅ Users can now run full concern-specific analysis

**Implementation Status**:
- Feature is functional and ready to test
- All core components implemented in ~7 hours
- Zero Python dependencies, pure AI-driven analysis

---

#### 9.9 Dependencies & Risks

**Dependencies**:

- Phase 8 completion (✅ DONE - Interactive AI workflow)
- Phase 8.1 completion (✅ DONE - Conditional questions)
- Bash/PowerShell scripts (✅ EXISTING - analyze-project.sh/.ps1)
- AI agent (✅ EXISTING - Claude Code or compatible)
- ❌ NO Python dependencies
- ❌ NO external tools required

**Risks**:

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| AI concern detection accuracy <90% | Medium | High | Improve prompt heuristics, iterate based on feedback |
| AI abstraction assessment subjective | Low | Medium | Require file:line evidence, test on diverse codebases |
| AI migration recommendations inconsistent | Low | High | Embed decision tree in prompt, require rationale |
| Users prefer full app analysis | Low | Low | Backward compatible, both modes available |
| Prompt complexity overwhelms AI | Low | Medium | Break into clear sections, test with multiple AI models |

---

#### 9.10 Future Enhancements (Post-v1.0)

**Advanced Features** (AI-driven, no code):

- [ ] Interactive refactoring guidance (AI generates step-by-step refactoring tasks)
- [ ] Cost estimation prompts (AI estimates cloud costs for new providers)
- [ ] Performance impact analysis (AI analyzes before/after performance characteristics)
- [ ] Security comparison analysis (AI compares security posture of old vs new)
- [ ] Compliance impact assessment (GDPR, SOX, HIPAA considerations)
- [ ] Team skill gap analysis (AI identifies training needs for new tech)

**Additional Concern Types**:

- [ ] Error handling/exception management
- [ ] Configuration management (hardcoded → env vars → config service)
- [ ] Secret management (code → vault/key management)
- [ ] API versioning strategy
- [ ] Rate limiting/throttling
- [ ] Circuit breaker pattern
- [ ] Service mesh integration
- [ ] Feature flags/toggles

**Prompt Enhancements**:

- [ ] Multi-concern analysis (e.g., Auth + Database together)
- [ ] Dependency analysis (identify concerns that depend on each other)
- [ ] Migration sequencing (optimal order for migrating multiple concerns)

---

#### 9.11 Summary: AI-Driven Architecture (No Python)

**Key Design Decisions**:

1. **AI Does All Semantic Analysis**
   - Pattern recognition (interfaces, DI, coupling)
   - Abstraction quality assessment
   - Blast radius calculation
   - Strategy recommendation
   - No Python code needed

2. **Prompt Engineering is the Core**
   - Detection heuristics embedded in prompts
   - Decision trees embedded in prompts
   - Assessment criteria embedded in prompts
   - AI interprets and applies to specific codebase

3. **Lightweight Orchestration**
   - Bash/PowerShell for setup only
   - No dependency installation
   - No external tools required
   - Works out of the box

4. **Template-Driven Output**
   - AI fills templates with real analysis
   - Consistent structure across concerns
   - Evidence-based (file:line references)
   - Actionable recommendations

**Benefits vs Python Approach**:

| Aspect | Python Approach | AI-Driven Approach |
|--------|----------------|-------------------|
| **Implementation** | 2-3 weeks Python coding | 1-2 days prompt engineering |
| **Dependencies** | Python 3.10+, packages | None |
| **Maintenance** | Update Python code for new patterns | Update prompts (easier) |
| **Flexibility** | Hardcoded algorithms | AI adapts to context |
| **Accuracy** | Rule-based (brittle) | Semantic understanding (robust) |
| **User Setup** | Install Python, packages | Zero setup |
| **Error Handling** | Try/catch, fallbacks | AI graceful degradation |

**Timeline Comparison**:

- **Python Approach**: 11 weeks (3 weeks core module + 2 weeks scanner + 1 week templates + 2 weeks testing + 3 weeks integration)
- **AI-Driven Approach**: 1-2 weeks (2 days prompts + 2 days templates + 3 days testing + 2 days docs)

**Cost Comparison**:

- **Python Approach**: ~640 hours implementation + ongoing maintenance
- **AI-Driven Approach**: ~60 hours implementation + minimal maintenance

---

#### 9.12 Implementation Summary (2025-11-11)

**Status**: ✅ IMPLEMENTED - Core functionality complete, ready for user testing

**What Was Built**:

1. ✅ **Enhanced analyze-project.md** (Commit: `307b095`)
   - Added ANALYSIS_SCOPE question (Full App vs Cross-Cutting Concern)
   - Added 9 CONCERN_TYPE options including Deployment/Infrastructure
   - Added comprehensive Step 4 concern-specific analysis instructions
   - Added conditional Step 6 artifact generation logic
   - Detection heuristics for all 9 concern types
   - Abstraction/coupling/blast radius assessment criteria
   - Migration strategy decision tree (4 strategies)

2. ✅ **Created 3 Templates** (Commit: `307b095`)
   - `concern-analysis-template.md` - 10-section comprehensive analysis
   - `abstraction-recommendations-template.md` - Conditional HIGH/MEDIUM/LOW guidance
   - `concern-migration-plan-template.md` - Detailed phased migration with rollback plans

3. ✅ **Updated Documentation** (Commit: `80bb393`)
   - Enhanced `docs/reverse-engineering.md` with Phase 9 section
   - Added Step 2.5: Choose Analysis Scope
   - Documented all 9 concern types with examples
   - Listed artifacts generated for concern migration
   - Updated IMPROVEMENTS.md status

**Total Implementation Time**: ~7 hours (vs 11 weeks for Python approach)

**Zero Dependencies**: Pure AI-driven analysis, no Python code

**Backward Compatible**: Existing full app analysis unchanged

**Next Steps**:

1. ✅ Design validated (user approved AI-driven approach)
2. ✅ Prompt enhancement complete (Day 1-2 tasks)
3. ✅ Templates created (Day 3-4 tasks)
4. ✅ Core documentation updated (Day 8-9 tasks)
5. ⏳ Test on real projects (Day 5-7) - **NEEDS USER TESTING**
6. ⏳ Add example walkthroughs after testing
7. ⏳ Update README.md after testing validation

**How to Use**:

Run `/analyze-project` and choose:
- [A] Full Application Modernization (existing workflow)
- [B] Cross-Cutting Concern Migration (new Phase 9 workflow)

Select concern type (1-9), specify current/target implementation, and AI will generate:
- concern-analysis.md
- abstraction-recommendations.md
- concern-migration-plan.md
- EXECUTIVE-SUMMARY.md

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
