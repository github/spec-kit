# Improvement Proposal: Guideline Generation & Update Command

**Author**: Senior Developer & Enterprise Architect
**Date**: 2025-11-11
**Status**: ✅ COMPLETED - See `improvement-completed.md` for implementation details
**Priority**: High

---

## Executive Summary

This document proposes a new command/prompt for **generating and updating corporate coding guidelines** by analyzing existing corporate documentation and reference projects. The solution enables organizations to extract principles from their highest-quality codebases and standardize them as reusable, principle-based guidelines.

**Key Value Propositions**:
- **Automate guideline creation** from scattered corporate documents and reference projects
- **Extract implicit standards** from well-built reference codebases
- **Maintain consistency** across tech stacks and teams
- **Evolve guidelines** as best practices emerge

---

## Problem Statement

### Current State

Organizations typically have:
1. **Corporate coding standards documents** (PDFs, Confluence pages, Word docs) - Often outdated, inconsistent, or overly verbose
2. **Reference projects** built with highest standards - Knowledge is implicit, not documented
3. **Scattered tribal knowledge** - Standards exist in code reviews, not written guidelines

### Challenges

1. **Manual guideline creation is time-consuming** - Requires deep analysis of multiple sources
2. **Inconsistent formats** - Different teams write guidelines differently
3. **Code-heavy examples become outdated** - When frameworks upgrade, examples break
4. **No systematic extraction** - Reference project standards remain locked in code
5. **Difficult to maintain** - Updates require re-analyzing all sources

### User Story

> "I have corporate Java coding standards (PDF), a Confluence page on security best practices, and 3 reference Spring Boot projects built with highest standards. I want to **synthesize these into a single `java-guidelines.md` file** that follows the principle-based format (MUST/SHOULD/NEVER), so AI agents can use it for new projects."

---

## Requirements Analysis

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Accept path to temp folder containing corporate docs and reference projects | MUST |
| FR-2 | Detect tech stack from reference projects automatically | MUST |
| FR-3 | Extract principles from corporate documents (PDF, Markdown, Confluence exports) | MUST |
| FR-4 | Analyze reference project code to identify implicit patterns and standards | MUST |
| FR-5 | Synthesize findings into principle-based guidelines (no code examples) | MUST |
| FR-6 | Support update modes: ADD (merge new principles), REPLACE (overwrite section), FULL_REGEN (rebuild entire file) | MUST |
| FR-7 | Generate guidelines in RFC 2119 format (MUST/SHOULD/NEVER keywords) | MUST |
| FR-8 | Maintain version history with changelog in guideline files | SHOULD |
| FR-9 | Support multi-stack scenarios (e.g., React + Java monorepo) | SHOULD |
| FR-10 | Validate generated guidelines against template structure | SHOULD |

### Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-1 | **Deep Analysis**: Use multiple specialized personas for comprehensive analysis | MUST |
| NFR-2 | **Evidence-Based**: All extracted principles must reference source (file:line or doc:page) | MUST |
| NFR-3 | **Consistency**: Follow existing `.guidelines/` folder structure and format | MUST |
| NFR-4 | **Version-Agnostic**: Extract principles independent of framework versions | MUST |
| NFR-5 | **Interactive**: Prompt user for clarifications when ambiguities detected | SHOULD |
| NFR-6 | **Idempotent**: Running twice on same sources should produce consistent output | SHOULD |

---

## Proposed Solution

### Overview

Create a new command: **`/speckit.generate-guidelines`** (or `/speckit.update-guidelines`)

**Command File**: `templates/commands/generate-guidelines.md`

**Supporting Script**:
- `scripts/bash/generate-guidelines.sh`
- `scripts/powershell/generate-guidelines.ps1`

### Workflow Diagram

```text
┌─────────────────────────────────────────────────────────────┐
│ Step 1: User Input & Discovery                             │
│ - Collect SOURCES_PATH (temp folder)                       │
│ - Detect tech stack from reference projects                │
│ - Ask for UPDATE_MODE (ADD/REPLACE/FULL_REGEN)             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Document Analysis (Persona: Standards Architect)   │
│ - Extract principles from corporate docs                   │
│ - Identify MUST/SHOULD/NEVER statements                    │
│ - Categorize by section (Auth, Security, Architecture)     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Code Analysis (Persona: Code Archeologist)         │
│ - Scan reference projects for patterns                     │
│ - Identify: Libraries, folder structure, naming, patterns  │
│ - Extract implicit rules (what's NOT in docs)              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Synthesis (Persona: Technical Writer)              │
│ - Merge document principles + code patterns                │
│ - Resolve conflicts (docs vs code, older vs newer)         │
│ - Generate principle-based statements (no code samples)    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Validation & Generation                            │
│ - Validate against guideline template structure            │
│ - Ask user to resolve ambiguities                          │
│ - Generate/update .guidelines/{stack}-guidelines.md        │
│ - Update version and changelog                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Design

### 1. Command Structure

**File**: `templates/commands/generate-guidelines.md`

**YAML Frontmatter**:

```yaml
---
description: Generate or update corporate coding guidelines by analyzing corporate documents and reference projects
scripts:
  bash: scripts/bash/generate-guidelines.sh "$1"
  powershell: scripts/powershell/generate-guidelines.ps1 "$1"
status: EXPERIMENTAL
version: 1.0.0-alpha
---
```

### 2. Personas (Multi-Expert Analysis)

To ensure **deep, comprehensive analysis**, the command will employ **three specialized personas** sequentially:

#### Persona 1: **Standards Architect**


*Role*: Enterprise standards expert who reads corporate documentation to extract organizational principles

**Responsibilities**:
- Parse corporate documents (PDF, Markdown, Confluence exports, Word docs)
- Extract explicit rules and requirements
- Identify mandatory libraries, banned libraries, security policies
- Map requirements to guideline sections (Scaffolding, Auth, Security, etc.)
- Flag contradictions or ambiguities for user clarification

**Output**: Structured list of principles from documents with source references

---

#### Persona 2: **Code Archeologist**
*Role*: Senior engineer who reverse-engineers patterns from high-quality codebases

**Responsibilities**:
- Scan reference project codebases to identify implicit standards
- Detect: Folder structures, naming conventions, architecture patterns
- Identify: Commonly used libraries, middleware patterns, error handling
- Extract: Configuration patterns, security implementations, testing strategies
- Compare patterns across multiple reference projects (consensus analysis)

**Output**: Pattern inventory with evidence (file:line references)

---

#### Persona 3: **Technical Writer & Synthesizer**
*Role*: Documentation specialist who converts findings into clear, principle-based guidelines

**Responsibilities**:
- Merge findings from Standards Architect + Code Archeologist
- Resolve conflicts (e.g., doc says use JWT, code uses OAuth → ask user)
- Convert patterns into principle-based statements (no code examples)
- Apply RFC 2119 keywords (MUST/SHOULD/NEVER) with appropriate severity
- Organize principles by guideline template sections
- Ensure version-agnostic language (no framework-specific syntax)

**Output**: Draft guideline document in proper format

---

### 3. User Input & Interactive Prompts

**Initial Prompt**:

```text
GENERATE/UPDATE GUIDELINES:

Please provide the following information:

SOURCES_PATH: /path/to/temp/folder
(Folder containing corporate documents and reference projects)

Example folder structure:
  /temp/my-standards/
    ├── docs/
    │   ├── java-coding-standards.pdf
    │   ├── security-guidelines.md
    │   └── architecture-patterns.docx
    └── reference-projects/
        ├── project-a/  (Spring Boot reference app)
        └── project-b/  (Another Spring Boot app)

Your input: ___
```

**Tech Stack Detection**:

Script enumerates folder and detects tech stacks from reference projects.

```text
DETECTED TECH STACKS:

Based on reference projects, detected:
- Java (Spring Boot 3.x) - Found in: project-a/, project-b/
- ReactJS (React 18) - Found in: project-a/frontend/

Which tech stack do you want to generate guidelines for?

- [A] Java / Spring Boot
- [B] ReactJS
- [C] Both (multi-stack)
- [D] Other (specify)

Your choice: ___
```

**Update Mode**:

```text
UPDATE MODE:

Existing guideline file detected: .guidelines/java-guidelines.md (v1.2.0)

How should we update it?

- [A] ADD - Merge new principles, keep existing (additive)
- [B] REPLACE - Replace specific sections (e.g., only update "Security")
- [C] FULL_REGEN - Rebuild entire file from scratch (destructive)
- [D] NEW - Create new file (backup existing as java-guidelines-v1.2.0.md)

Your choice: ___
```

**If REPLACE mode selected**:

```text
Which sections to replace?

Available sections:
- [1] Scaffolding
- [2] Package Registry
- [3] Mandatory Libraries
- [4] Banned Libraries
- [5] Architecture
- [6] Security
- [7] Coding Standards
- [8] Dependency Management
- [9] Testing
- [10] Build & Deployment
- [11] Observability

Enter section numbers (comma-separated): ___
(e.g., "3,4,6" to replace Mandatory Libraries, Banned Libraries, Security)
```

---

### 4. Analysis Process

#### Step 2.1: Document Analysis (Standards Architect Persona)

**Goal**: Extract explicit principles from corporate documents

**Process**:

1. **Enumerate documents** in `docs/` subfolder
2. **For each document**:
   - Read full content (use Read tool for markdown, WebFetch/OCR for PDFs if needed)
   - Extract principles, rules, requirements
   - Identify MUST/SHOULD/NEVER statements
   - Categorize by section (Auth, Security, Architecture, etc.)
   - Record source reference (filename:page or filename:section)

**Example Extraction**:

```markdown
### Document: security-guidelines.pdf

**Extracted Principles**:

1. **Authentication** (security-guidelines.pdf:12)
   - "All API endpoints MUST use OAuth 2.0 with corporate identity provider"
   - Severity: MUST
   - Category: Security > Authentication

2. **Secrets Management** (security-guidelines.pdf:18)
   - "Secrets MUST NOT be hardcoded in source code"
   - "Use Azure Key Vault for production secrets"
   - Severity: MUST / NEVER
   - Category: Security > Secrets Management

3. **Logging** (java-coding-standards.pdf:45)
   - "Applications SHOULD use SLF4J with Logback"
   - "Log at appropriate levels (ERROR, WARN, INFO, DEBUG)"
   - Severity: SHOULD
   - Category: Observability > Logging
```

**Conflict Detection**:

If multiple documents contradict:
- Flag for user clarification
- Example: "doc-a.pdf says use JWT, doc-b.md says use OAuth 2.0 - which takes precedence?"

---

#### Step 2.2: Code Analysis (Code Archeologist Persona)

**Goal**: Reverse-engineer implicit standards from reference projects

**Process**:

1. **For each reference project**:
   - Scan entire codebase
   - Identify patterns in:
     - **Project structure**: Folder layout, module organization
     - **Dependencies**: pom.xml, package.json, requirements.txt
     - **Architecture**: Controllers, services, repositories, layers
     - **Naming conventions**: Class names, method names, variable patterns
     - **Security**: Auth implementations, input validation, error handling
     - **Configuration**: application.yml, .env patterns
     - **Testing**: Test structure, coverage, frameworks used
     - **Observability**: Logging, metrics, health checks

2. **Pattern Consensus Analysis**:
   - If analyzing 3 reference projects:
     - **All 3 use same pattern** → High confidence (MUST)
     - **2 of 3 use pattern** → Medium confidence (SHOULD)
     - **1 of 3 uses pattern** → Low confidence (mention as option)

**Example Analysis**:

```markdown
### Pattern: Folder Structure (3/3 projects)

**Evidence**:
- project-a/src/main/java/com/acme/app/:
  - controllers/
  - services/
  - repositories/
  - models/
  - config/
- project-b/: (same structure)
- project-c/: (same structure)

**Extracted Principle**:
"MUST follow layered architecture: controllers/ → services/ → repositories/"
Confidence: HIGH (all projects use this)
Category: Architecture > Project Structure

---

### Pattern: Dependency - Spring Security (3/3 projects)

**Evidence**:
- project-a/pom.xml:45: <dependency>spring-boot-starter-security</dependency>
- project-b/pom.xml:52: (same)
- project-c/pom.xml:38: (same)

**Extracted Principle**:
"MUST use Spring Security for authentication and authorization"
Confidence: HIGH
Category: Security > Authentication

---

### Pattern: Custom Auth Library (2/3 projects)

**Evidence**:
- project-a/pom.xml:67: <dependency>acmecorp-auth-spring:2.1.0</dependency>
- project-b/pom.xml:71: <dependency>acmecorp-auth-spring:2.0.5</dependency>
- project-c/: NOT FOUND

**Extracted Principle**:
"SHOULD use acmecorp-auth-spring for corporate authentication integration"
Confidence: MEDIUM (2/3 projects)
Category: Mandatory Libraries > Authentication
Note: Flag for user - is this corporate standard or just common practice?
```

**Code Pattern Extraction (No Code Copying)**:

**BAD** (code example):
```java
// Don't extract this way
@GetMapping("/users")
public ResponseEntity<List<User>> getUsers(@AuthenticationPrincipal User user) { ... }
```

**GOOD** (principle-based):
```markdown
**MUST**:
- Decorate controller methods with appropriate HTTP method annotations
- Use dependency injection for authenticated user context
- Return ResponseEntity for type-safe HTTP responses
```

---

#### Step 2.3: Synthesis (Technical Writer Persona)

**Goal**: Merge document principles + code patterns into cohesive guidelines

**Process**:

1. **Merge Findings**:
   - Combine principles from documents (Step 2.1)
   - Combine patterns from code (Step 2.2)

2. **Resolve Conflicts**:
   - **Document vs Code**: If doc says one thing, code does another
     - Example: Doc says "use JWT", code uses OAuth 2.0
     - **Action**: Ask user which is correct (doc may be outdated)
   - **Newer vs Older**: If reference projects use different versions
     - Example: project-a uses Spring Boot 3.2, project-b uses 2.7
     - **Action**: Use newer version as standard (unless user specifies otherwise)

3. **Apply RFC 2119 Severity**:
   - **MUST**: Security, compliance, mandatory corporate libraries
   - **SHOULD**: Best practices, recommended patterns
   - **MAY/OPTIONAL**: Nice-to-have, team preference
   - **NEVER**: Banned libraries, anti-patterns, security vulnerabilities

4. **Organize by Template Sections**:
   - Map extracted principles to guideline template structure:
     1. Scaffolding
     2. Package Registry
     3. Mandatory Libraries
     4. Banned Libraries
     5. Architecture
     6. Security
     7. Coding Standards
     8. Dependency Management
     9. Testing
     10. Build & Deployment
     11. Observability

5. **Ensure Version-Agnostic Language**:
   - ❌ BAD: "Use @GetMapping annotation (Spring Boot 2.x syntax)"
   - ✅ GOOD: "Decorate HTTP endpoints with framework-appropriate annotations"

**Example Synthesis**:

```markdown
### Input from Documents:
- "All services must use corporate authentication package" (doc-a.pdf:12)
- "OAuth 2.0 is the standard authentication protocol" (doc-b.md:Security)

### Input from Code:
- 3/3 projects use acmecorp-auth-spring library (HIGH confidence)
- 3/3 projects have @EnableOAuth2Client annotation (HIGH confidence)

### Conflicts Detected:
- None (documents and code align)

### Synthesized Guideline:

## Mandatory Libraries

### Authentication

**MUST** use: `acmecorp-auth-spring` package
**Requirements**:

- Enable OAuth 2.0 client configuration in application
- Decorate protected endpoints with authentication annotations
- Extract authenticated user via framework-provided context injection

**Features**: Corporate SSO integration, token validation, role-based access control

**NEVER**:
- Implement custom JWT validation logic
- Use public OAuth libraries directly (e.g., Spring OAuth without corporate wrapper)

**Rationale**: Corporate authentication ensures compliance with security policies and enables centralized user management.
```

---

### 5. Validation & User Clarification

**Conflict Resolution Prompts**:

```text
CONFLICTS DETECTED:

1. Authentication Library Mismatch
   - Document (security-guidelines.pdf:12): "Use acmecorp-auth v2.x"
   - Reference Project A: Uses acmecorp-auth v3.1.0
   - Reference Project B: Uses acmecorp-auth v3.0.2

   Which should be the standard?
   - [A] v2.x (follow document)
   - [B] v3.x (follow reference projects - newer)
   - [C] Other (specify version)

   Your choice: ___

2. Logging Framework
   - Document (java-coding-standards.pdf:45): "SHOULD use SLF4J + Logback"
   - Reference Projects: 3/3 use SLF4J + Log4j2

   Which takes precedence?
   - [A] Logback (follow document)
   - [B] Log4j2 (follow reference projects)

   Your choice: ___
```

**Ambiguity Clarifications**:

```text
CLARIFICATIONS NEEDED:

1. Found corporate library 'acmecorp-http-client' in 2/3 reference projects.
   Is this a MANDATORY library or just commonly used?
   - [A] MANDATORY (add to "Mandatory Libraries" section)
   - [B] RECOMMENDED (add as "SHOULD use")
   - [C] OPTIONAL (mention in notes)

   Your choice: ___

2. Detected different testing strategies:
   - Project A: JUnit 5 + Mockito + TestContainers
   - Project B: JUnit 5 + Mockito (no TestContainers)
   - Project C: JUnit 5 + Mockito + WireMock

   What is the corporate standard for integration testing?
   - [A] TestContainers (for database/infra testing)
   - [B] WireMock (for API mocking)
   - [C] Both (use based on scenario)
   - [D] Neither (use simple mocks)

   Your choice: ___
```

---

### 6. Output & File Generation

**Generated Files**:

1. **Primary Output**: `.guidelines/{stack}-guidelines.md`
   - Updated or newly created guideline file
   - Follows template structure from existing guidelines
   - Includes version number and changelog

2. **Analysis Report**: `.guidelines-analysis/{stack}-analysis-report.md`
   - Detailed findings from document analysis
   - Code pattern inventory with evidence
   - Synthesis decisions and rationale
   - User clarifications and choices

3. **Backup (if updating)**: `.guidelines/{stack}-guidelines-v{X.Y.Z}.md.bak`
   - Backup of previous version before update

**Version Management**:

```markdown
---
version: 2.0.0  # Incremented from 1.2.0
last_updated: 2025-11-11
changelog:
  - v2.0.0 (2025-11-11): Regenerated from corporate docs + 3 reference projects
  - v1.2.0 (2025-08-15): Added observability section
  - v1.0.0 (2025-06-01): Initial version
---
```

**Update Modes**:

| Mode | Behavior | Use Case |
|------|----------|----------|
| **ADD** | Merge new principles into existing file, keep old ones | Incremental updates |
| **REPLACE** | Replace specific sections only | Fix outdated section (e.g., update Security) |
| **FULL_REGEN** | Rebuild entire file from scratch | Major overhaul, docs + code changed significantly |
| **NEW** | Create new file, backup existing | Create alternate guideline version |

---

### 7. Script Design

**File**: `scripts/bash/generate-guidelines.sh`

**Responsibilities**:
1. Enumerate files in SOURCES_PATH
2. Categorize into documents/ and reference-projects/
3. Generate file manifests for both
4. Create output directory: `.guidelines-analysis/`
5. Pass manifests to AI for analysis

**Pseudocode**:

```bash
#!/bin/bash

SOURCES_PATH=$1
OUTPUT_DIR=".guidelines-analysis"

# Validate input
if [ ! -d "$SOURCES_PATH" ]; then
  echo "ERROR: SOURCES_PATH not found: $SOURCES_PATH"
  exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Enumerate documents
find "$SOURCES_PATH/docs" -type f > "$OUTPUT_DIR/documents-manifest.txt"

# Enumerate reference projects
find "$SOURCES_PATH/reference-projects" -type d -maxdepth 1 > "$OUTPUT_DIR/projects-manifest.txt"

# Generate file trees for each project
for project in $(cat "$OUTPUT_DIR/projects-manifest.txt"); do
  project_name=$(basename "$project")
  find "$project" -type f > "$OUTPUT_DIR/${project_name}-files.txt"
done

echo "✓ Enumeration complete. Manifests generated in $OUTPUT_DIR"
echo "AI can now analyze documents and reference projects."
```

---

## Implementation Plan

### Phase 1: Core Command (MVP) - 2 weeks

**Deliverables**:
- [ ] `templates/commands/generate-guidelines.md` with full persona prompts
- [ ] `scripts/bash/generate-guidelines.sh` for file enumeration
- [ ] `scripts/powershell/generate-guidelines.ps1` (Windows equivalent)
- [ ] Support for single tech stack (e.g., Java only)
- [ ] UPDATE_MODE: FULL_REGEN only (no ADD/REPLACE yet)
- [ ] Basic document parsing (Markdown, plain text)

**Acceptance Criteria**:
- Command successfully generates java-guidelines.md from 1 PDF + 2 reference projects
- Output follows template structure
- Principles are version-agnostic (no code examples)

---

### Phase 2: Advanced Features - 2 weeks

**Deliverables**:
- [ ] Support for UPDATE_MODE: ADD, REPLACE
- [ ] PDF parsing support (via WebFetch or specialized tool)
- [ ] Multi-stack support (React + Java)
- [ ] Conflict resolution prompts
- [ ] Ambiguity clarification prompts
- [ ] Detailed analysis report generation

**Acceptance Criteria**:
- Can update existing guideline file without overwriting custom sections
- Successfully handles conflicts (doc vs code)
- Analysis report includes all evidence and decisions

---

### Phase 3: Quality & Validation - 1 week

**Deliverables**:
- [ ] Validation against guideline template structure
- [ ] Automated checks for RFC 2119 keyword usage
- [ ] Version history and changelog automation
- [ ] Backup mechanism for existing guidelines
- [ ] Comprehensive testing with multiple tech stacks

**Acceptance Criteria**:
- Generated guidelines pass validation checks
- Version numbers increment correctly
- Backups created before destructive updates

---

## Example Usage Scenario

### Scenario: Acme Corp wants to generate Java guidelines

**Input Structure**:

```
/tmp/acme-java-standards/
├── docs/
│   ├── java-coding-standards-2024.pdf
│   ├── security-best-practices.md
│   └── architecture-patterns.docx
└── reference-projects/
    ├── acme-order-service/     (Spring Boot 3.2, Clean Architecture)
    ├── acme-payment-service/   (Spring Boot 3.1, Hexagonal Architecture)
    └── acme-notification-api/  (Spring Boot 3.2, Layered Architecture)
```

**Command Execution**:

```bash
cd /path/to/spec-kit-smart
./speckit generate-guidelines /tmp/acme-java-standards
```

**Interactive Session**:

```text
DETECTED TECH STACKS:
- Java (Spring Boot 3.x) - Found in 3 reference projects

Generating guidelines for: Java / Spring Boot

UPDATE MODE:
Existing file detected: .guidelines/java-guidelines.md (v1.0.0)
- [C] FULL_REGEN - Rebuild entire file from scratch

Proceeding with full regeneration...

[Standards Architect]: Analyzing corporate documents...
✓ Processed java-coding-standards-2024.pdf (78 pages)
✓ Processed security-best-practices.md (15 sections)
✓ Processed architecture-patterns.docx (45 pages)

Extracted 67 principles across 8 categories.

[Code Archeologist]: Analyzing reference projects...
✓ Scanned acme-order-service (347 files)
✓ Scanned acme-payment-service (289 files)
✓ Scanned acme-notification-api (412 files)

Identified 43 patterns with HIGH confidence (3/3 consensus).
Identified 12 patterns with MEDIUM confidence (2/3 consensus).

[Technical Writer]: Synthesizing findings...

CONFLICTS DETECTED:

1. Logging Library
   - Document: "Use SLF4J + Logback"
   - Code: 3/3 projects use SLF4J + Log4j2

   Which is correct?
   - [A] Logback
   - [B] Log4j2

Your choice: B

✓ Resolved: Will use Log4j2 as standard

[Technical Writer]: Generating guideline document...

✓ Generated: .guidelines/java-guidelines.md (v2.0.0)
✓ Backup created: .guidelines/java-guidelines-v1.0.0.md.bak
✓ Analysis report: .guidelines-analysis/java-analysis-report.md

SUMMARY:

Guideline File: .guidelines/java-guidelines.md
Version: 2.0.0 (updated from 1.0.0)
Sections: 11
Principles: 89 total
- MUST: 34
- SHOULD: 28
- NEVER: 12
- MAY: 15

Sources Analyzed:
- Documents: 3 files, 138 pages
- Reference Projects: 3 projects, 1,048 files

Next Steps:
1. Review generated guideline: .guidelines/java-guidelines.md
2. Review analysis report for detailed evidence
3. Commit updated guidelines to version control
4. Share with development teams
```

---

## Alternative Approaches Considered

### Approach 1: Manual Template Filling
**Rejected**: Too time-consuming, prone to inconsistency, doesn't extract implicit knowledge from code

### Approach 2: Simple Document Concatenation
**Rejected**: Doesn't analyze code patterns, no synthesis, results in code-heavy examples

### Approach 3: Single Persona Analysis
**Rejected**: Lacks depth, misses implicit patterns, no specialized expertise (documents vs code require different analysis approaches)

### Approach 4: Code Example Extraction
**Rejected**: Violates principle-based philosophy, creates version-specific guidelines that break on upgrades

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| AI extracts code examples instead of principles | HIGH | MEDIUM | Strict persona prompts emphasizing "no code, principles only" |
| Documents and code contradict each other | MEDIUM | HIGH | Conflict resolution prompts, user clarification required |
| PDF parsing fails or is inaccurate | MEDIUM | MEDIUM | Fallback to manual document conversion, recommend Markdown/text formats |
| Reference projects have poor quality code | HIGH | LOW | Pre-validation step: ask user to confirm projects represent "gold standard" |
| Multi-stack projects cause confusion | MEDIUM | MEDIUM | Clear tech stack detection, separate analysis per stack |
| Guideline sections don't match template | LOW | LOW | Validation step, map extracted principles to template sections |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Time to generate guidelines** | < 30 minutes (vs 8+ hours manual) | Stopwatch from command start to file generation |
| **Principle extraction accuracy** | > 90% (validated by human review) | Human review of 20 random principles |
| **Version-agnostic compliance** | 100% (no framework-specific code) | Automated check for code blocks in output |
| **User satisfaction** | > 4.5/5 | Survey after using command |
| **Guideline reusability** | Works across 3+ framework versions | Test with Spring Boot 2.7, 3.0, 3.2 projects |

---

## Open Questions

1. **PDF Parsing**: Should we require pre-converted Markdown, or invest in robust PDF parsing?
   - **Recommendation**: Start with "Markdown preferred, PDF supported best-effort" approach

2. **Guideline Versioning**: Semantic versioning (MAJOR.MINOR.PATCH) or date-based?
   - **Recommendation**: Semantic versioning (breaking changes = MAJOR, new sections = MINOR, fixes = PATCH)

3. **Multi-Language Support**: Can one command handle Java + Python in same run?
   - **Recommendation**: Phase 1 = single stack, Phase 2 = multi-stack with separate output files

4. **Approval Workflow**: Should generated guidelines require human approval before use?
   - **Recommendation**: Yes, generate in `.guidelines-analysis/` first, manual review, then move to `.guidelines/`

5. **Corporate Library Auto-Detection**: Should we automatically detect `@acmecorp/*` packages and add to Mandatory Libraries?
   - **Recommendation**: Yes, with confidence scoring (3/3 projects = MUST, 2/3 = SHOULD, 1/3 = ask user)

---

## Appendix A: Guideline Template Structure

(Reference: Existing `.guidelines/python-guidelines.md`)

```markdown
# {Language} Corporate Guidelines

**Tech Stack**: [Language, Frameworks, Use Cases]
**Auto-detected from**: [File patterns]
**Version**: X.Y.Z

---

## Scaffolding
[Corporate project creation commands]

## Package Registry
[Corporate artifact repository configuration]

## Mandatory Libraries
### [Category 1]
### [Category 2]

## Banned Libraries
[Prohibited packages with rationale]

## Architecture
[Patterns, structure, design principles]

## Security
[Auth, secrets, input validation, etc.]

## Coding Standards
[Naming, style, conventions]

## Dependency Management
[Package managers, versioning]

## Testing
[Test frameworks, coverage, strategies]

## Build & Deployment
[Build tools, Docker, CI/CD]

## Observability
[Logging, metrics, health checks]

## Non-Compliance
[What to do when guidelines can't be followed]
```

---

## Appendix B: Sample Persona Prompts

### Standards Architect Prompt

```markdown
## Role & Mindset

You are a **Corporate Standards Architect** with 15+ years of experience defining enterprise coding standards. You excel at:

- Reading corporate documentation and extracting actionable principles
- Identifying mandatory requirements vs recommendations
- Categorizing standards by domain (security, architecture, testing, etc.)
- Detecting ambiguities and contradictions in documentation
- Translating verbose corporate speak into clear, concise rules

**Your Task**:

Analyze the provided corporate documents and extract coding principles in the following format:

**Output Format**:

```markdown
### [Category Name]

**Principle**: [Clear statement in RFC 2119 format]
**Severity**: [MUST | SHOULD | MAY | NEVER]
**Source**: [document-name.ext:page/section]
**Rationale**: [Why this rule exists]
```

**Critical Rules**:
- Extract PRINCIPLES, not code examples
- Use RFC 2119 keywords (MUST/SHOULD/NEVER)
- Include source references for traceability
- Flag contradictions between documents
- Ask user when ambiguous

**Example Output**:

```markdown
### Authentication

**Principle**: All API endpoints must authenticate users via corporate identity provider
**Severity**: MUST
**Source**: security-guidelines.pdf:12
**Rationale**: Ensures compliance with corporate security policy and centralized user management

**Principle**: Avoid storing user passwords in application database
**Severity**: NEVER
**Source**: security-guidelines.pdf:15
**Rationale**: Corporate IdP handles authentication; apps should only validate tokens
```
```

### Code Archeologist Prompt

```markdown
## Role & Mindset

You are a **Code Archeologist** - a senior engineer specialized in reverse-engineering patterns from well-built codebases. You excel at:

- Identifying implicit standards not documented anywhere
- Detecting consensus patterns across multiple projects
- Extracting architecture, naming, and design conventions
- Understanding the "why" behind code patterns
- Distinguishing corporate standards from framework defaults

**Your Task**:

Analyze the provided reference projects and identify coding patterns that represent corporate standards.

**Analysis Checklist**:

1. **Project Structure**: Folder layout, module organization
2. **Dependencies**: Required libraries, version patterns
3. **Architecture**: Layering, separation of concerns
4. **Naming Conventions**: Classes, methods, variables, files
5. **Security Patterns**: Auth implementation, input validation
6. **Configuration**: File formats, environment handling
7. **Testing**: Test structure, frameworks, coverage approach
8. **Error Handling**: Exception patterns, logging, monitoring

**Output Format**:

```markdown
### Pattern: [Pattern Name]

**Evidence**:
- project-a/path/to/file.ext:line: [What you found]
- project-b/path/to/file.ext:line: [What you found]
- project-c/path/to/file.ext:line: [What you found]

**Consensus**: [ALL projects | X/Y projects use this]
**Confidence**: [HIGH | MEDIUM | LOW]

**Extracted Principle** (NO CODE):
[Principle-based statement]

**Recommended Severity**: [MUST | SHOULD | MAY]
**Category**: [Architecture | Security | Testing | etc.]
```

**Critical Rules**:
- NO code examples in "Extracted Principle" section
- Use file:line references for evidence
- Calculate consensus (3/3 = HIGH, 2/3 = MEDIUM, 1/3 = LOW)
- Convert patterns to principles (describe WHAT/WHY, not HOW)
- Flag for user review if confidence is LOW

**Example Output**:

```markdown
### Pattern: Layered Architecture

**Evidence**:
- project-a/src/main/java/com/acme/controllers/: Controller classes found
- project-a/src/main/java/com/acme/services/: Service classes found
- project-a/src/main/java/com/acme/repositories/: Repository interfaces found
- project-b/: (same structure)
- project-c/: (same structure)

**Consensus**: ALL 3 projects use this structure
**Confidence**: HIGH

**Extracted Principle**:
Follow strict layered architecture with clear separation: presentation layer (controllers) → business logic layer (services) → data access layer (repositories). Controllers should delegate business logic to services and never access repositories directly.

**Recommended Severity**: MUST
**Category**: Architecture > Project Structure
```
```

---

## Conclusion

This proposal provides a comprehensive solution for **automated generation and maintenance of corporate coding guidelines**. By leveraging AI with specialized personas (Standards Architect, Code Archeologist, Technical Writer), we can systematically extract principles from documents and reference codebases, synthesize them into consistent, version-agnostic guidelines, and maintain them over time.

**Key Benefits**:
- ⏱️ **10x faster** than manual guideline creation
- 🎯 **Consistent format** across all tech stacks
- 🔍 **Evidence-based** with full traceability
- 🔄 **Easy to update** as standards evolve
- 📚 **Extracts implicit knowledge** from reference projects

**Next Steps**:
1. Review and approve this design
2. Implement Phase 1 (MVP) - 2 weeks
3. Test with real corporate documents + reference projects
4. Gather feedback and iterate
5. Roll out to additional tech stacks

---

**Document Version**: 3.0.0
**Last Updated**: 2025-11-11
**Status**: ✅ COMPLETED
**Implementation Details**: See `improvement-completed.md`

---

> **Note**: This document contains the original design proposal. For implementation details, testing results, and completion status, see **`improvement-completed.md`**.

---
