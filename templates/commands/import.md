---
description: Analyze an existing codebase and generate a product specification to bootstrap the speckit workflow.
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan based on the imported spec
    send: true
  - label: Start Iteration
    agent: speckit.iterate
    prompt: Begin iterating on the imported product
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user input may specify:
- **Product documentation**: Either inline text or a path to a `.md` file containing product vision, objectives, MVP definition, user journeys, personas, etc.
- A specific version name/number for the import
- Focus areas to emphasize in the analysis
- Specific directories or modules to analyze

### Input Document Handling

1. **If a file path is provided** (e.g., `./docs/product-vision.md` or `/path/to/product.md`):
   - Read the file contents using the Read tool
   - Parse and extract product documentation sections

2. **If inline text is provided**:
   - Parse the text directly for product documentation

3. **If no product documentation is provided**:
   - Infer product vision and objectives from README.md and codebase analysis
   - Mark sections with [INFERRED - NEEDS VERIFICATION]

### Expected Product Documentation Sections

The input document should ideally contain (but is not required to have all):
- **Product Vision**: The overarching goal and purpose of the product
- **Objectives & Goals**: Specific, measurable outcomes the product aims to achieve
- **MVP Definition**: Core features required for minimum viable product
- **E2E User Journeys**: Complete workflows from user perspective
- **Personas**: User types and their characteristics, needs, and pain points
- **Success Metrics**: How success will be measured

## Overview

This command analyzes an existing codebase combined with product documentation to generate a comprehensive product specification, bootstrapping the speckit workflow for projects that already have code. It replaces the need for `speckit.constitution` and `speckit.specify` when working with existing products.

**Use this when**:
- You have an existing codebase without speckit artifacts
- You want to start using speckit's planning/iteration workflow on an existing project
- You need to document the current state of a product before adding new features
- You have product documentation (vision, personas, journeys) to integrate with codebase analysis

## Outline

### 1. Initial Setup

1. **Process user input**:
   - Check if input contains a file path (ends with `.md` or starts with `./`, `/`, or `~`)
   - If file path: Read the file and extract product documentation
   - If text: Parse inline text for product documentation sections
   - Extract version name if provided separately

2. **Determine version identifier**:
   - If user provided a version name in arguments, use it as a suffix
   - Otherwise, use "baseline" as the default suffix
   - The script auto-generates the next available feature number (###-import-{suffix})
   - This ensures compatibility with all other speckit commands

3. **Create specs directory structure**:
   ```
   specs/
   └── {###}-import-{suffix}/
       ├── spec.md           # Product specification
       ├── analysis/         # Detailed analysis artifacts
       │   ├── architecture.md
       │   ├── entities.md
       │   ├── features.md
       │   └── domains.md    # Domain separation for multi-team development
       └── checklists/       # Validation checklists
   ```

4. **Run setup script**:
   ```bash
   .specify/scripts/bash/import-existing-product.sh --json --version "{suffix}"
   ```
   - If user provides a name like "v1.0" or "initial", pass it: `--version "initial"`
   - If no name provided, omit the --version flag for default "baseline"
   - Parse JSON output for BRANCH_NAME, SPEC_DIR, SPEC_FILE, ANALYSIS_DIR, IMPORT_DATE
   - The script creates a git branch matching the spec directory name

### 2. Codebase Analysis

Perform comprehensive analysis of the existing codebase:

#### 2.1 Project Structure Analysis

1. **Identify project type and stack**:
   - Check for package.json, requirements.txt, go.mod, Cargo.toml, etc.
   - Identify frontend frameworks (React, Vue, Angular, etc.)
   - Identify backend frameworks (Express, FastAPI, Gin, etc.)
   - Identify database technologies (PostgreSQL, MongoDB, etc.)

2. **Map directory structure**:
   - Identify source directories (src/, lib/, app/, etc.)
   - Identify test directories
   - Identify configuration files
   - Identify documentation

3. **Extract dependencies**:
   - List key dependencies and their purposes
   - Identify integration points (APIs, services)

#### 2.2 Feature Discovery

1. **Analyze routes/endpoints**:
   - Extract API routes from router files
   - Identify page routes from frontend routing
   - Map HTTP methods and paths

2. **Identify user-facing features**:
   - Analyze component directories for UI features
   - Extract page/view names and purposes
   - Identify forms and user interactions

3. **Discover entities/models**:
   - Parse database schemas (Prisma, TypeORM, SQLAlchemy, etc.)
   - Extract model definitions
   - Map relationships between entities

4. **Identify business logic**:
   - Analyze service layers
   - Extract core workflows
   - Identify integrations with external services

#### 2.3 Architecture Analysis

1. **Identify architectural patterns**:
   - Monolith vs microservices
   - API patterns (REST, GraphQL, gRPC)
   - State management approach
   - Authentication/authorization patterns

2. **Map data flow**:
   - Client → Server → Database paths
   - Event-driven components
   - Real-time features (WebSockets, SSE)

#### 2.4 Domain Discovery & Separation

**CRITICAL**: This section is essential for multi-team development. Clearly separate application domains to enable parallel team work.

1. **Identify bounded contexts**:
   - Analyze directory structure for natural domain boundaries
   - Look for module/package organization patterns
   - Identify services that could be owned by different teams
   - Map domain-specific terminology and ubiquitous language

2. **Domain classification criteria**:
   - **Functional domains**: Authentication, Payments, Notifications, Analytics, etc.
   - **Data ownership**: Which entities belong to which domain
   - **Team alignment**: Natural team boundaries based on expertise
   - **Dependency direction**: Which domains depend on which

3. **Cross-domain interactions**:
   - Identify integration points between domains
   - Map API contracts between domains
   - Document shared entities and who owns them
   - Identify potential coupling issues

4. **Domain ownership indicators**:
   - Separate database schemas or tables per domain
   - Distinct API route prefixes
   - Isolated frontend modules/features
   - Independent deployment capabilities

### 3. Generate Specification

Create `spec.md` following the spec template structure but adapted for existing products.

**IMPORTANT**: Integrate both the provided product documentation AND codebase analysis. The spec should bridge strategic vision with technical reality.

```markdown
# Product Specification: [PROJECT_NAME]

**Feature Branch**: `{BRANCH_NAME}`
**Analyzed**: [IMPORT_DATE]
**Status**: Imported from existing codebase

---

## 1. Product Vision & Strategy

### Vision Statement

[From input document or inferred from codebase]
[The overarching goal and purpose of the product]

### Objectives & Goals

[From input document - measurable outcomes the product aims to achieve]

1. **[Objective 1]**: [Description and success criteria]
2. **[Objective 2]**: [Description and success criteria]
3. **[Objective 3]**: [Description and success criteria]

### Success Metrics

[From input document or inferred]

| Metric | Target | Current State |
|--------|--------|---------------|
| [Metric 1] | [Target] | [Assessed from codebase] |
| [Metric 2] | [Target] | [Assessed from codebase] |

---

## 2. User Personas

[From input document or inferred from codebase user types]

### Persona 1: [Name/Role]

- **Description**: [Who they are]
- **Goals**: [What they want to achieve]
- **Pain Points**: [Current frustrations]
- **Technical Proficiency**: [Low/Medium/High]
- **Key Features Used**: [Features relevant to this persona]

### Persona 2: [Name/Role]

[Repeat structure]

---

## 3. MVP Definition

[From input document - core features required for minimum viable product]

### MVP Scope

| Feature | Priority | Status | Domain |
|---------|----------|--------|--------|
| [Feature 1] | Must Have | [Implemented/Partial/Missing] | [Domain] |
| [Feature 2] | Must Have | [Implemented/Partial/Missing] | [Domain] |
| [Feature 3] | Should Have | [Implemented/Partial/Missing] | [Domain] |

### MVP vs Current State Gap

[Analysis of what's implemented vs what's needed for MVP]

---

## 4. E2E User Journeys

[From input document - complete workflows from user perspective]

### Journey 1: [Journey Name]

**Persona**: [Which persona]
**Goal**: [What user wants to accomplish]

| Step | User Action | System Response | Status |
|------|-------------|-----------------|--------|
| 1 | [Action] | [Response] | [Implemented/Missing] |
| 2 | [Action] | [Response] | [Implemented/Missing] |
| 3 | [Action] | [Response] | [Implemented/Missing] |

**Entry Points**: [Routes/Components]
**Exit Points**: [Success/Error states]

### Journey 2: [Journey Name]

[Repeat structure]

---

## 5. Application Domains

**CRITICAL FOR MULTI-TEAM DEVELOPMENT**: The following domains represent distinct bounded contexts that can be developed independently by separate teams.

### Domain Map Overview

| Domain | Owner Team | Dependencies | Key Entities |
|--------|------------|--------------|--------------|
| [Domain 1] | [Team/TBD] | [Dependencies] | [Entities] |
| [Domain 2] | [Team/TBD] | [Dependencies] | [Entities] |
| [Domain 3] | [Team/TBD] | [Dependencies] | [Entities] |

### Domain 1: [Domain Name] (e.g., Authentication & Identity)

**Purpose**: [What this domain handles]
**Team Ownership**: [Suggested team or TBD]

**Bounded Context**:
- [Core responsibilities]
- [What it does NOT handle]

**Entities Owned**:
- [Entity 1]: [Description]
- [Entity 2]: [Description]

**API Surface**:
- [Endpoints/interfaces exposed to other domains]

**Dependencies**:
- Depends on: [Other domains this relies on]
- Depended by: [Domains that rely on this]

**Source Locations**:
- Backend: `[paths]`
- Frontend: `[paths]`
- Database: `[schema/tables]`

### Domain 2: [Domain Name]

[Repeat structure]

### Cross-Domain Integration Points

| From Domain | To Domain | Integration Type | Contract |
|-------------|-----------|------------------|----------|
| [Domain A] | [Domain B] | [API/Event/Shared DB] | [Description] |

---

## 6. Current Capabilities

### Core Features by Domain

#### [Domain 1] Features

##### Feature: [Feature Name]

**What it does**: [Description]
**Domain**: [Which domain owns this]

**User Flow**:
1. [Step 1]
2. [Step 2]
3. [Expected outcome]

**Key Components**:
- [Component/file references]

[Repeat for each feature, grouped by domain]

---

## 7. Technical Foundation

### Architecture

- **Pattern**: [Monolith/Microservices/Serverless]
- **Frontend**: [Framework and key libraries]
- **Backend**: [Framework and key libraries]
- **Database**: [Database type and ORM]
- **Infrastructure**: [Deployment/hosting if detectable]

### Key Entities by Domain

[List entities discovered from database schema, organized by domain]

#### [Domain 1] Entities
- **[Entity 1]**: [Description, key fields]
- **[Entity 2]**: [Description, relationships]

#### [Domain 2] Entities
- **[Entity 3]**: [Description, key fields]

### Integration Points

[External services and APIs]

- **[Integration 1]**: [Purpose] → Used by [Domain]
- **[Integration 2]**: [Purpose] → Used by [Domain]

---

## 8. Current State Assessment

### Strengths

- [What's working well]
- [Well-structured areas]

### Areas for Enhancement

- [Potential improvements noted]
- [Technical debt observed]

### Dependencies & Constraints

- [Key dependencies]
- [Known limitations]

---

## 9. Baseline Metrics

[If detectable from code or configs]

| Metric | Value |
|--------|-------|
| Lines of code | ~[X] |
| Number of entities | [X] |
| Number of API endpoints | [X] |
| Number of UI pages/views | [X] |
| Number of domains | [X] |

---

## 10. Ready for Planning

This specification captures the current state of [PROJECT_NAME] and is ready for:
- `/speckit.plan` - Create implementation plans for new features
- `/speckit.iterate` - Begin iterating with Linear integration
- `/speckit.clarify` - Refine specific areas of the specification

### Recommended Next Steps by Domain

| Domain | Priority | Next Action |
|--------|----------|-------------|
| [Domain 1] | [High/Medium/Low] | [Suggested action] |
| [Domain 2] | [High/Medium/Low] | [Suggested action] |
```

### 4. Generate Supporting Artifacts

#### 4.1 Architecture Document (`analysis/architecture.md`)

```markdown
# Architecture Analysis: [PROJECT_NAME]

## System Overview

[Diagram description or component list]

## Component Breakdown

### Frontend
[Detailed frontend analysis]

### Backend
[Detailed backend analysis]

### Data Layer
[Database and data flow analysis]

## Patterns Identified

[Design patterns found in the codebase]

## Security Considerations

[Authentication, authorization, data protection patterns found]
```

#### 4.2 Entities Document (`analysis/entities.md`)

```markdown
# Entity Model: [PROJECT_NAME]

## Entity Relationship Overview

[List all entities and their relationships]

## Detailed Entity Definitions

### [Entity Name]

**Source**: [file path]

| Field | Type | Description |
|-------|------|-------------|
| id | string | Primary identifier |
| ... | ... | ... |

**Relationships**:
- Has many [Entity]
- Belongs to [Entity]
```

#### 4.3 Features Document (`analysis/features.md`)

```markdown
# Feature Inventory: [PROJECT_NAME]

## Feature Map

| Feature | Type | Status | Domain | Location |
|---------|------|--------|--------|----------|
| [Name] | [UI/API/Background] | Active | [Domain] | [paths] |

## Detailed Feature Analysis

### [Feature Name]

**Purpose**: [What it does]
**Domain**: [Which domain owns this feature]

**Entry Points**:
- [Route/Component]

**Dependencies**:
- [Services/APIs used]

**Data Flow**:
1. [Step 1]
2. [Step 2]
```

#### 4.4 Domains Document (`analysis/domains.md`)

**CRITICAL**: This document is essential for multi-team development and should be reviewed carefully.

```markdown
# Domain Separation Analysis: [PROJECT_NAME]

## Executive Summary

This document maps the application into distinct bounded contexts (domains) that can be developed and maintained by separate teams. Each domain represents a cohesive area of functionality with clear boundaries and ownership.

## Domain Inventory

| Domain | Description | Team Size Recommendation | Complexity |
|--------|-------------|--------------------------|------------|
| [Domain 1] | [Brief description] | [1-2 / 2-3 / 3-5] | [Low/Medium/High] |
| [Domain 2] | [Brief description] | [1-2 / 2-3 / 3-5] | [Low/Medium/High] |

## Detailed Domain Definitions

### Domain: [Domain Name]

#### Overview

**Purpose**: [What business capability this domain provides]
**Ubiquitous Language**: [Key terms and their meanings within this domain]

#### Bounded Context

**IN Scope**:
- [Responsibility 1]
- [Responsibility 2]
- [Responsibility 3]

**OUT of Scope** (handled by other domains):
- [What this domain does NOT handle]

#### Ownership

**Suggested Team**: [Team name or characteristics]
**Required Expertise**: [Skills needed]
**Estimated Team Size**: [X-Y developers]

#### Data Ownership

| Entity | Ownership Type | Notes |
|--------|----------------|-------|
| [Entity 1] | Full Owner | [Notes] |
| [Entity 2] | Full Owner | [Notes] |
| [Entity 3] | Consumer Only | Owned by [Other Domain] |

#### API Contracts

**Exposes to Other Domains**:

| Endpoint/Interface | Consumer Domains | Contract Type |
|--------------------|------------------|---------------|
| [API endpoint] | [Domain A, Domain B] | [REST/Event/Direct] |

**Consumes from Other Domains**:

| Endpoint/Interface | Provider Domain | Contract Type |
|--------------------|-----------------|---------------|
| [API endpoint] | [Domain X] | [REST/Event/Direct] |

#### Source Code Locations

```
Backend:
  - [path/to/module]
  - [path/to/services]

Frontend:
  - [path/to/components]
  - [path/to/pages]

Database:
  - [schema.table]
  - [schema.table]

Tests:
  - [path/to/tests]
```

#### Key Components

| Component | Purpose | Dependencies |
|-----------|---------|--------------|
| [Component 1] | [Purpose] | [Internal/External deps] |
| [Component 2] | [Purpose] | [Internal/External deps] |

---

[Repeat for each domain]

---

## Cross-Domain Dependencies

### Dependency Graph

```
[Visual or text representation of domain dependencies]

Example:
┌─────────────┐     ┌─────────────┐
│    Auth     │────▶│    Core     │
└─────────────┘     └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│  Payments   │     │ Notifications│
└─────────────┘     └─────────────┘
```

### Integration Points

| From | To | Type | Description | Coupling Risk |
|------|-----|------|-------------|---------------|
| [Domain A] | [Domain B] | [Sync API/Async Event/Shared DB] | [What data flows] | [Low/Medium/High] |

### Shared Entities

| Entity | Owner Domain | Consumer Domains | Sharing Strategy |
|--------|--------------|------------------|------------------|
| [Entity] | [Domain] | [Domain A, B] | [Read-only API / Event / Shared table] |

## Team Coordination Requirements

### Communication Channels

| Domain Pair | Coordination Frequency | Key Topics |
|-------------|------------------------|------------|
| [A] ↔ [B] | [Daily/Weekly/As needed] | [Topics] |

### Potential Conflicts

| Area | Involved Domains | Risk | Mitigation |
|------|------------------|------|------------|
| [Shared functionality] | [Domains] | [Risk level] | [Suggested approach] |

## Migration Considerations

### Current State
[How tightly coupled the domains currently are]

### Target State
[How domains should be separated]

### Recommended Decoupling Steps

1. **Phase 1**: [First decoupling action]
2. **Phase 2**: [Second decoupling action]
3. **Phase 3**: [Third decoupling action]

## Domain Health Indicators

| Domain | Cohesion | Coupling | Autonomy | Notes |
|--------|----------|----------|----------|-------|
| [Domain] | [High/Medium/Low] | [High/Medium/Low] | [High/Medium/Low] | [Notes] |

---

## Appendix: Domain Discovery Methodology

### How Domains Were Identified

1. **Directory structure analysis**: [Findings]
2. **Entity relationship analysis**: [Findings]
3. **API route patterns**: [Findings]
4. **Business capability mapping**: [Findings]

### Confidence Levels

| Domain | Confidence | Needs Verification |
|--------|------------|-------------------|
| [Domain] | [High/Medium/Low] | [Areas to verify] |
```

### 5. Validation & Report

1. **Validate spec completeness**:
   - Ensure all major features are documented
   - Verify entity list matches schema
   - Confirm architecture description is accurate
   - **Validate domain separation is clear and actionable**
   - Verify product documentation sections are populated (vision, personas, journeys)

2. **Validate domain boundaries**:
   - Each domain should have clear ownership
   - Cross-domain dependencies should be explicitly mapped
   - No orphan entities (entities not assigned to any domain)
   - Integration points should have defined contracts

3. **Generate import summary**:

   ```markdown
   ## Import Summary

   **Branch**: {BRANCH_NAME}
   **Spec Location**: specs/{BRANCH_NAME}/spec.md

   ### Product Documentation Integration

   | Section | Source | Status |
   |---------|--------|--------|
   | Vision Statement | [Input doc/Inferred] | [Complete/Needs Review] |
   | Objectives & Goals | [Input doc/Inferred] | [Complete/Needs Review] |
   | Personas | [Input doc/Inferred] | [Complete/Needs Review] |
   | User Journeys | [Input doc/Inferred] | [Complete/Needs Review] |
   | MVP Definition | [Input doc/Inferred] | [Complete/Needs Review] |

   ### Codebase Analysis Results

   - **Features Discovered**: X
   - **Entities Mapped**: X
   - **API Endpoints**: X
   - **UI Components**: X
   - **Domains Identified**: X

   ### Domain Summary

   | Domain | Features | Entities | Team Readiness |
   |--------|----------|----------|----------------|
   | [Domain 1] | X | X | [Ready/Needs clarification] |
   | [Domain 2] | X | X | [Ready/Needs clarification] |

   ### Generated Artifacts

   - [x] spec.md - Product specification with domains
   - [x] analysis/architecture.md - Architecture details
   - [x] analysis/entities.md - Data model documentation
   - [x] analysis/features.md - Feature inventory by domain
   - [x] analysis/domains.md - **Domain separation for multi-team development**

   ### Next Steps

   1. Review the generated spec.md for accuracy
   2. **Review analysis/domains.md with team leads** to validate domain boundaries
   3. Assign team ownership to each domain
   4. Run `/speckit.plan` to create plans for new features
   5. Run `/speckit.iterate` to begin development with Linear tracking

   ### Manual Review Recommended

   - [ ] Verify feature descriptions match actual behavior
   - [ ] Confirm entity relationships are correct
   - [ ] Add any business context not detectable from code
   - [ ] **Review domain boundaries with engineering leads**
   - [ ] **Validate cross-domain contracts are accurate**
   - [ ] Confirm personas match actual user segments
   - [ ] Verify user journeys reflect real workflows
   ```

4. **Report completion** with paths and suggested next actions.

## Analysis Techniques

### For TypeScript/JavaScript Projects

- Parse `package.json` for dependencies
- Analyze `tsconfig.json` for project structure
- Check for Prisma schema at `prisma/schema.prisma`
- Look for route definitions in common patterns:
  - Express: `app.get()`, `router.post()`
  - Next.js: `pages/` or `app/` directory
  - React Router: `<Route>` components

### For Python Projects

- Parse `requirements.txt` or `pyproject.toml`
- Look for Django models, FastAPI routes, Flask blueprints
- Check for SQLAlchemy or Django ORM models

### General Patterns

- README.md for project description
- Environment files for configuration hints
- Docker/docker-compose for service architecture
- CI/CD configs for build/test processes

## Error Handling

### Codebase Errors
- **Empty codebase**: ERROR "No source code found to analyze"
- **No identifiable structure**: WARN and create minimal spec with manual completion markers
- **Missing dependencies file**: WARN but continue with structure analysis
- **Large codebase**: Focus on entry points and core modules, note areas needing manual review

### Product Documentation Errors
- **File path not found**: ERROR "Product documentation file not found at [path]"
- **Unreadable file**: ERROR "Unable to read product documentation file"
- **Empty documentation**: WARN "No content found in product documentation" and proceed with inference
- **Malformed markdown**: WARN and attempt to parse available sections

### Domain Analysis Errors
- **Cannot identify domains**: WARN "Unable to automatically identify domain boundaries" - suggest monolith structure and recommend manual domain definition
- **Circular dependencies**: WARN "Circular domain dependencies detected" and flag for architectural review
- **Orphan entities**: WARN "Entities not assigned to any domain" and list them for review

## Guidelines

### General
- Focus on WHAT the product does, not implementation details
- Use business language in feature descriptions
- Preserve technical accuracy in architecture sections
- Mark uncertain areas with [NEEDS VERIFICATION] for manual review
- Keep the spec consumable by non-technical stakeholders
- Analysis artifacts can be more technical for developer reference

### Product Documentation Integration
- If user provides product documentation, prioritize that content over inferences
- Always indicate the source (Input doc vs Inferred) for each section
- When documentation and code contradict, note the discrepancy for review
- Missing documentation sections should be marked as [NOT PROVIDED - INFERRED FROM CODE]

### Domain Separation (Critical for Multi-Team Development)
- **Domains must be clearly bounded** - each should have distinct responsibilities
- **Avoid shared ownership** - every entity should have exactly one owning domain
- **Document all contracts** - cross-domain integrations need explicit API contracts
- **Consider team dynamics** - domains should align with realistic team structures
- **Minimize coupling** - flag high-coupling areas that need architectural attention
- **Include migration path** - if domains are currently coupled, suggest decoupling steps

### Domain Identification Heuristics
- Directory structure often reflects domain boundaries (e.g., `modules/`, `features/`, `domains/`)
- Separate database schemas or table prefixes indicate domains
- Distinct API route prefixes (e.g., `/auth/*`, `/payments/*`) suggest domains
- Frontend feature folders often map to business domains
- Look for existing team ownership patterns in git history or code comments
