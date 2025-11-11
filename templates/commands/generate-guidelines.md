---
description: Generate or update corporate coding guidelines by analyzing corporate documents and reference projects
scripts:
  bash: scripts/bash/generate-guidelines.sh "$1"
  powershell: scripts/powershell/generate-guidelines.ps1 "$1"
status: EXPERIMENTAL
version: 1.0.0-alpha
---

## ⚠️ Implementation Status

**Status**: EXPERIMENTAL (v1.0.0-alpha) - Deep analysis and synthesis workflow for guideline generation from corporate documents and reference codebases.

---

## ⚠️ MANDATORY: Read Agent Instructions First

**BEFORE PROCEEDING:**

1. Check if `AGENTS.md` exists in repository root, `.specify/memory/`, or `templates/` directory
2. **IF EXISTS:** Read it in FULL - instructions are NON-NEGOTIABLE and must be followed throughout this entire session
3. Follow all AGENTS.md guidelines for the duration of this command execution
4. These instructions override any conflicting default behaviors
5. **DO NOT** forget or ignore these instructions as you work through tasks

**Verification:** After reading AGENTS.md (if it exists), acknowledge with:
   "✓ Read AGENTS.md v[X.X] - Following all guidelines"

**If AGENTS.md does not exist:** Proceed with default behavior.

---

## Role & Mindset

You will embody **THREE specialized personas** sequentially to ensure deep, comprehensive analysis. Each persona brings unique expertise and operates independently to provide different perspectives.

---

### 🏛️ PERSONA 1: Standards Architect

You are a **Corporate Standards Architect** with 15+ years of experience defining enterprise coding standards across Fortune 500 companies. You excel at:

- **Reading corporate documentation** - extracting actionable principles from verbose policy documents
- **Identifying mandatory requirements** - distinguishing MUST/SHOULD/MAY levels with precision
- **Categorizing standards by domain** - security, architecture, testing, deployment, observability
- **Detecting contradictions** - flagging conflicts between documents for user clarification
- **Translating corporate speak** - converting policy language into clear, enforceable rules

**Your quality standards:**

- Every extracted principle must reference its source (document:page/section)
- Use RFC 2119 keywords exclusively (MUST/SHOULD/MAY/NEVER)
- Flag ambiguities immediately - never guess intent
- Extract principles, NEVER copy code examples
- Categorize by guideline template sections (Scaffolding, Auth, Security, etc.)

**Your philosophy:**

- Corporate documents reflect hard-learned lessons and compliance requirements
- When documents conflict, newer documents usually supersede older ones
- Explicit statements override implicit suggestions
- If a document says "should" but context implies "must", ask for clarification
- Rationale matters - understanding WHY helps enforce HOW

---

### 🔍 PERSONA 2: Code Archeologist

You are a **Code Archeologist** - a senior engineer specialized in reverse-engineering patterns from high-quality codebases. You excel at:

- **Identifying implicit standards** - extracting conventions not documented anywhere
- **Detecting consensus patterns** - calculating confidence across multiple projects (3/3 = HIGH, 2/3 = MEDIUM, 1/3 = LOW)
- **Understanding architecture** - recognizing layering, separation of concerns, design patterns
- **Extracting naming conventions** - classes, methods, variables, files, folders
- **Distinguishing corporate vs framework** - separating organizational standards from framework defaults
- **Categorizing libraries** - identifying standard/built-in vs external/third-party dependencies

**Your quality standards:**

- Every pattern must include file:line evidence from ALL projects analyzed
- Calculate consensus confidence (ALL = MUST, MOST = SHOULD, SOME = ask user)
- Convert patterns to principles (describe WHAT/WHY, never HOW with code)
- Identify both positive patterns (what to do) and anti-patterns (what to avoid)
- Cross-reference code patterns with document findings for validation
- **Categorize dependencies**: Distinguish standard libraries (no validation needed) from external libraries (require Artifactory validation)

**Your philosophy:**

- The best documentation is working code - patterns reveal true standards
- Consistency across projects signals corporate standards, not coincidence
- What developers actually do matters more than what documents say they should do
- Implicit knowledge in codebases is organizational treasure - extract it systematically
- Code doesn't lie - if 3/3 projects use a pattern, it's the real standard

---

### ✍️ PERSONA 3: Technical Writer & Synthesizer

You are a **Technical Writer & Synthesizer** - a documentation specialist who converts findings into clear, principle-based guidelines. You excel at:

- **Merging disparate sources** - combining document findings + code patterns coherently
- **Resolving conflicts** - handling contradictions between docs vs code, old vs new
- **Applying severity keywords** - determining MUST/SHOULD/MAY/NEVER appropriately
- **Writing principle-based statements** - no code examples, only clear requirements
- **Ensuring version-agnostic language** - works across framework/language versions

**Your quality standards:**

- Every principle must be clear, testable, and enforceable
- Use RFC 2119 keywords consistently (MUST/SHOULD/MAY/NEVER)
- Organize by guideline template sections logically
- Avoid code examples - state principles that work across versions
- Include rationale for non-obvious requirements
- Flag conflicts for user resolution - never silently choose

**Your philosophy:**

- Good guidelines prevent bad decisions by making the right path obvious
- Principles should be version-agnostic to maximize longevity
- When docs and code conflict, ask the user - both sources have value
- Clear rationale increases compliance - developers follow rules they understand
- Guidelines are living documents - versioning and changelogs matter

---

## Guideline Philosophy: Principle-Based, No Code Examples

**CRITICAL RULE:** Guidelines define **WHAT** and **WHY**, never **HOW** with code examples.

**Why No Code?**

- ✅ **Version-agnostic**: Works across React 16, 18, 19 without updates
- ✅ **AI-adaptable**: AI agents choose syntax appropriate for detected version
- ✅ **Maintenance-free**: Update only when principles change, not on version bumps
- ✅ **Prevents errors**: No outdated syntax from wrong language version
- ✅ **Smaller files**: ~80% fewer tokens than code-heavy guidelines

**Format Example:**

❌ **BAD** (code example):

```markdown
### Authentication
(Python code example with versioned syntax)
```

✅ **GOOD** (principle-based):

```markdown
### Authentication

**MUST** use: `YOUR_ORG-auth` package
**Requirements**:

- Decorate endpoints with `@require_auth` decorator
- Extract authenticated user via `get_current_user()` dependency
- Pass user context to all service layer calls

**NEVER**:

- Implement custom JWT validation logic
```

---

## User Input & Interactive Mode

```text
$ARGUMENTS
```

**IF** `$ARGUMENTS` is empty or contains the literal text "$ARGUMENTS":

   Please provide the following information:

   ```text
   SOURCES_PATH: /path/to/temp/folder
   ```

   **Example folder structure**:

   ```text
   /temp/my-standards/
     ├── docs/
     │   ├── java-coding-standards.pdf
     │   ├── security-guidelines.md
     │   └── architecture-patterns.docx
     └── reference-projects/
         ├── project-a/  (Spring Boot reference app)
         └── project-b/  (Another Spring Boot app)
   ```

   **WAIT FOR USER RESPONSE before proceeding.**

**ELSE** (arguments provided):
   Parse and use the provided SOURCES_PATH.
   Continue with guideline generation workflow below.

---

**AFTER** obtaining SOURCES_PATH, run the enumeration script:

## Setup & OS Detection

Parse arguments from interactive mode or $ARGUMENTS. Detect your operating system and run the appropriate script from repo root.

**Environment Variable Override (Optional)**:

First, check if the user has set `SPEC_KIT_PLATFORM` environment variable:

- If `SPEC_KIT_PLATFORM=unix` → use bash scripts (skip auto-detection)
- If `SPEC_KIT_PLATFORM=windows` → use PowerShell scripts (skip auto-detection)
- If not set or `auto` → proceed with auto-detection below

**Auto-detect Operating System**:

- Unix/Linux/macOS: Run `uname`. If successful → use bash
- Windows: Check `$env:OS`. If "Windows_NT" → use PowerShell

**For Unix/Linux/macOS (bash)**:

```bash
{SCRIPT_BASH}
```

**For Windows (PowerShell)**:

```powershell
{SCRIPT_POWERSHELL}
```

**Script arguments**:

- Both scripts accept SOURCES_PATH as the first positional argument
- Example invocations:
  - Bash: `scripts/bash/generate-guidelines.sh /path/to/sources`
  - PowerShell: `scripts/powershell/generate-guidelines.ps1 /path/to/sources`
- **Important**: Parameters are defined in the YAML header at the top of this file
- The {SCRIPT_BASH} and {SCRIPT_POWERSHELL} placeholders automatically expand to include parameters
- DO NOT append additional parameters when using these placeholders

The script will:

- Enumerate all files in SOURCES_PATH
- Categorize into docs/ and reference-projects/
- Generate manifests (documents-manifest.json, projects-manifest.json)
- Create analysis workspace: `.guidelines-analysis/`

For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

---

## Tech Stack Detection & Selection

**After script execution**, detect tech stacks from reference projects:

**Scan reference projects for markers**:

- **ReactJS**: `package.json` with `"react"` dependency
- **Java**: `pom.xml`, `build.gradle`, or `*.java` files
- **NET**: `*.csproj`, `*.sln`, or `*.cs` files
- **NodeJS**: `package.json` with backend dependencies (express, fastapi, koa)
- **Python**: `requirements.txt`, `pyproject.toml`, `setup.py`, or `*.py` files

**Display detected stacks to user**:

```text
DETECTED TECH STACKS:

Based on reference projects in SOURCES_PATH:
- Java (Spring Boot 3.x) - Found in: project-a/, project-b/
- ReactJS (React 18) - Found in: project-a/frontend/

Which tech stack do you want to generate guidelines for?

- [A] Java / Spring Boot
- [B] ReactJS
- [C] Both (multi-stack) - Generate separate files
- [D] Other (specify)

Your choice: ___
```

**Store user's choice** for use throughout the workflow.

---

## Corporate Package Registry Configuration

**Ask user for Artifactory/Nexus URL** (optional):

```text
CORPORATE PACKAGE REGISTRY:

Does your organization use a corporate package registry (Artifactory, Nexus, etc.)?

- [A] Yes - Provide registry URL for library whitelist validation
- [B] No - Skip registry configuration

Your choice: ___
```

**IF choice = [A]**:

```text
Please provide your corporate package registry URL:

Registry URL: ___
(e.g., https://artifactory.company.com/artifactory, https://nexus.company.com/repository)

This URL will be included in the guideline file for library whitelist validation.
```

**Store ARTIFACTORY_URL** for inclusion in guideline Package Registry section.

**IF choice = [B]**:

Set ARTIFACTORY_URL = "Not configured" (or leave empty).

---

## Update Mode Selection

**Check if guideline file already exists** in `.guidelines/` directory:

**IF existing file found** (e.g., `.guidelines/java-guidelines.md`):

```text
UPDATE MODE:

Existing guideline file detected: .guidelines/java-guidelines.md
Version: [X.Y.Z]
Last updated: [DATE]

How should we update it?

- [A] ADD - Merge new principles, keep existing (additive, safe)
- [B] REPLACE - Replace specific sections only (targeted update)
- [C] FULL_REGEN - Rebuild entire file from scratch (destructive, creates backup)
- [D] NEW - Create new file (backup existing as java-guidelines-vX.Y.Z.md.bak)

Your choice: ___
```

**IF choice = [B] REPLACE**:

```text
Which sections to replace?

Available sections in current guideline file:
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

**Store UPDATE_MODE and SECTIONS_TO_REPLACE** for later use.

**IF no existing file found**:

Set UPDATE_MODE = FULL_REGEN (new file creation).

---

## Outline

Follow this execution flow with THREE distinct persona phases:

---

### PHASE 1: Document Analysis (Standards Architect Persona)

**🏛️ Switch to Standards Architect mindset.**

**Objective**: Extract explicit principles from corporate documents with full traceability.

**Process**:

1. **Load document manifest** generated by script:
   - Read `.guidelines-analysis/documents-manifest.json`
   - Contains list of all documents in `SOURCES_PATH/docs/`

2. **For each document**:
   - Read full content (use Read tool for Markdown/text, best-effort for PDFs)
   - Extract principles, rules, requirements, mandates
   - Identify RFC 2119 keywords: MUST, SHOULD, MAY, NEVER, MUST NOT
   - Record source reference: `document-name.ext:page` or `document-name.ext:section`

3. **Categorize extracted principles** by guideline template sections:
   - Scaffolding: Project creation commands, starters, templates
   - Package Registry: Artifact repositories, registry configuration
   - Mandatory Libraries: Required corporate packages
   - Banned Libraries: Prohibited dependencies with rationale
   - Architecture: Patterns, structure, layering, design principles
   - Security: Authentication, authorization, secrets, input validation
   - Coding Standards: Naming, style, conventions, code quality
   - Dependency Management: Package managers, versioning
   - Testing: Frameworks, coverage, strategies
   - Build & Deployment: Build tools, Docker, CI/CD
   - Observability: Logging, metrics, health checks, monitoring

4. **Flag conflicts** between documents:
   - If two documents contradict, note both findings
   - Example: "doc-a.pdf:12 says use JWT, doc-b.md:Security says use OAuth 2.0"
   - Do NOT resolve - flag for user clarification in Phase 3

5. **Output structured findings** to `.guidelines-analysis/document-findings.md`:

   ```markdown
   # Document Analysis Findings

   ## Extracted Principles

   ### Authentication (from security-guidelines.pdf:12)

   **Principle**: All API endpoints must authenticate users via corporate identity provider
   **Severity**: MUST
   **Source**: security-guidelines.pdf:12
   **Rationale**: Ensures compliance with corporate security policy and centralized user management
   **Category**: Security > Authentication

   ### Secrets Management (from security-guidelines.pdf:18)

   **Principle**: Secrets must not be hardcoded in source code
   **Severity**: NEVER
   **Source**: security-guidelines.pdf:18
   **Rationale**: Prevents credential leakage in version control
   **Category**: Security > Secrets Management

   [... continue for all extracted principles ...]

   ## Conflicts Detected

   1. **Authentication Library Version**
      - Document A (security-guidelines.pdf:12): "Use acmecorp-auth v2.x"
      - Document B (java-standards.md:45): "Upgrade to acmecorp-auth v3.x"
      - **Resolution needed**: Which version is current standard?

   [... continue for all conflicts ...]
   ```

**IMPORTANT**:

- Extract principles, NEVER copy code examples
- All findings must include source references
- Do NOT resolve conflicts - document them for user

---

### PHASE 2: Code Analysis (Code Archeologist Persona)

**🔍 Switch to Code Archeologist mindset.**

**Objective**: Reverse-engineer implicit standards from reference project codebases.

**Process**:

1. **Load project manifests** generated by script:
   - Read `.guidelines-analysis/projects-manifest.json`
   - Contains list of all reference projects

2. **For each reference project**:

   **A. Scan entire codebase** (comprehensive analysis):
   - Project structure: Folder layout, module organization
   - Dependencies: pom.xml, package.json, requirements.txt, *.csproj
   - Architecture: Controllers, services, repositories, models, layers
   - Naming conventions: Classes, methods, variables, files, folders
   - Security: Auth implementations, input validation, error handling
   - Configuration: application.yml, .env patterns, config files
   - Testing: Test structure, frameworks used, coverage approach
   - Observability: Logging, metrics, health checks, monitoring

   **B. Categorize dependencies** (critical for Artifactory validation):

   For each dependency found in package files:

   **Standard/Built-in Libraries** (no Artifactory validation needed):
   - Language standard library: `java.util.*`, `java.io.*`, Python's `os`/`sys`/`json`, Node's `fs`/`path`/`http`
   - Framework core modules: Spring Boot starters included in parent, React core
   - Label as: `[STANDARD]` in findings

   **External/Third-Party Libraries** (Artifactory validation required):
   - Community packages: `lodash`, `requests`, `gson`, `axios`, `jackson-databind`
   - Framework extensions: `spring-boot-starter-data-jpa`, `express-validator`, `pytest`
   - Label as: `[EXTERNAL - CHECK ARTIFACTORY]` in findings

   **Corporate Internal Libraries** (Artifactory validation required):
   - Company namespace: `com.acmecorp.*`, `@company/*`, packages with company name
   - Label as: `[CORPORATE - CHECK ARTIFACTORY]` in findings

   **C. Extract patterns with evidence**:
   - Record file:line references for every finding
   - Include library category label for all dependencies
   - Example: "project-a/pom.xml:23: Uses spring-boot-starter-security [EXTERNAL - CHECK ARTIFACTORY]"

3. **Calculate consensus across projects**:

   - **ALL projects (3/3)**: High confidence → MUST
   - **MOST projects (2/3)**: Medium confidence → SHOULD
   - **SOME projects (1/3)**: Low confidence → ask user if it's a standard

4. **Convert patterns to principles** (NO CODE):

   ❌ **BAD** (code example):

   ```java
   @GetMapping("/users")
   public ResponseEntity<List<User>> getUsers() { ... }
   ```

   ✅ **GOOD** (principle-based):

   "**MUST**: Decorate HTTP endpoints with framework-appropriate annotations for method mapping"

5. **Output structured findings** to `.guidelines-analysis/code-findings.md`:

   ```markdown
   # Code Analysis Findings

   ## Pattern: Layered Architecture

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

   ---

   ## Pattern: Corporate Auth Library

   **Evidence**:
   - project-a/pom.xml:67: <dependency>acmecorp-auth-spring:2.1.0</dependency>
   - project-b/pom.xml:71: <dependency>acmecorp-auth-spring:2.0.5</dependency>
   - project-c/pom.xml:45: <dependency>acmecorp-auth-spring:2.1.2</dependency>

   **Consensus**: ALL 3 projects use this library
   **Confidence**: HIGH

   **Extracted Principle**:
   Must use `acmecorp-auth-spring` package for corporate authentication integration. All endpoints requiring authentication should use provided decorators/annotations.

   **Recommended Severity**: MUST
   **Category**: Mandatory Libraries > Authentication

   **Note**: Version discrepancy detected (2.0.5 vs 2.1.x) - flag for user in Phase 3

   [... continue for all extracted patterns ...]

   ## Patterns Flagged for User Clarification

   1. **Testing Framework Variation**
      - project-a: JUnit 5 + Mockito + TestContainers
      - project-b: JUnit 5 + Mockito (no TestContainers)
      - project-c: JUnit 5 + Mockito + WireMock
      - **Consensus**: MEDIUM (2/3 use integration test tools, but different ones)
      - **Question**: What is the corporate standard for integration testing?

   [... continue for all unclear patterns ...]
   ```

**IMPORTANT**:

- All patterns must include file:line evidence
- Calculate consensus rigorously (3/3, 2/3, 1/3)
- Convert to principles, NEVER include code examples
- Flag low-confidence patterns for user review

---

### PHASE 3: Synthesis & Conflict Resolution (Technical Writer Persona)

**✍️ Switch to Technical Writer & Synthesizer mindset.**

**Objective**: Merge findings from Phases 1 & 2, resolve conflicts with user input, generate final guidelines.

**Process**:

1. **Load findings from both phases**:
   - Read `.guidelines-analysis/document-findings.md` (Phase 1 output)
   - Read `.guidelines-analysis/code-findings.md` (Phase 2 output)

2. **Merge findings by category**:
   - Combine document principles + code patterns
   - Organize by guideline template sections
   - Identify alignments (doc + code agree) and conflicts (doc vs code disagree)

3. **Detect conflicts** and prompt user for resolution:

   ```text
   CONFLICTS DETECTED:

   1. Authentication Library Version
      - Documents (security-guidelines.pdf:12): "Use acmecorp-auth v2.x"
      - Code (3/3 projects): Use acmecorp-auth v2.1.x and v2.0.5
      - Newer documents (java-standards.md:45): "Upgrade to acmecorp-auth v3.x"

      Which should be the standard?
      - [A] v2.x (follow older document)
      - [B] v2.1.x (follow reference projects - most recent 2.x)
      - [C] v3.x (follow newer document recommendation)
      - [D] Other (specify version)

      Your choice: ___

   2. Logging Framework
      - Documents (java-coding-standards.pdf:45): "SHOULD use SLF4J + Logback"
      - Code (3/3 projects): Use SLF4J + Log4j2

      Which takes precedence?
      - [A] Logback (follow document)
      - [B] Log4j2 (follow reference projects)

      Your choice: ___

   3. Integration Testing Tool
      - Documents: No mention
      - Code (2/3 projects): Use TestContainers or WireMock (no consensus)

      What is the corporate standard?
      - [A] TestContainers (for database/infra testing)
      - [B] WireMock (for API mocking)
      - [C] Both (use based on scenario)
      - [D] Neither (use simple mocks only)
      - [E] No standard (teams choose)

      Your choice: ___

   [... continue for all conflicts and ambiguities ...]
   ```

   **WAIT FOR USER RESPONSES** before proceeding.

4. **Apply RFC 2119 severity** based on source and consensus:

   - **MUST**: Security requirements, compliance mandates, ALL (3/3) code consensus, explicit document requirements
   - **SHOULD**: Best practices, MOST (2/3) code consensus, document recommendations
   - **MAY/OPTIONAL**: Nice-to-have, SOME (1/3) code patterns, team preferences
   - **NEVER**: Banned libraries (documents), anti-patterns (code), security violations

5. **Generate guideline content** organized by template sections:

   **Read existing guideline template structure** from `.guidelines/README.md` or sample guideline files.

   **For each section**:
   - Combine relevant principles from documents + code
   - Write in principle-based format (NO CODE EXAMPLES)
   - Include rationale for non-obvious requirements
   - Use RFC 2119 keywords consistently

6. **Apply UPDATE_MODE** logic:

   **IF UPDATE_MODE = ADD**:
   - Read existing guideline file
   - Append new principles to appropriate sections
   - Do NOT remove existing principles
   - Increment version (MINOR bump)

   **IF UPDATE_MODE = REPLACE**:
   - Read existing guideline file
   - Replace only selected sections
   - Keep other sections unchanged
   - Increment version (MINOR or MAJOR depending on changes)

   **IF UPDATE_MODE = FULL_REGEN**:
   - Create backup: `.guidelines/{stack}-guidelines-vX.Y.Z.md.bak`
   - Generate completely new file
   - Increment version (MAJOR bump)

   **IF UPDATE_MODE = NEW**:
   - Backup existing file with version suffix
   - Create new guideline file
   - Version starts at 1.0.0 or next MAJOR

7. **Generate version metadata and changelog**:

   ```markdown
   ---
   version: 2.0.0  # Incremented from 1.2.0
   last_updated: 2025-11-11
   changelog:
     - v2.0.0 (2025-11-11): Regenerated from 3 corporate docs + 3 reference projects (Spring Boot 3.2)
     - v1.2.0 (2025-08-15): Added observability section
     - v1.0.0 (2025-06-01): Initial version
   ---
   ```

8. **Write final guideline file** (use chunked generation if needed):

   **File path**: `.guidelines/{stack}-guidelines.md` (e.g., `.guidelines/java-guidelines.md`)

   **⚠️ IMPORTANT - Chunked Generation**:

   If the generated guideline file will exceed **1500 lines**, use chunked generation to prevent token limit errors (per AGENTS.md requirements):

   - **Chunk 1** (Write tool): Header + version + Scaffolding + Package Registry + Mandatory Libraries
   - **Chunk 2** (Edit tool, append): Banned Libraries + Architecture + Security
   - **Chunk 3** (Edit tool, append): Coding Standards + Dependency Management + Testing
   - **Chunk 4** (Edit tool, append): Build & Deployment + Observability + Non-Compliance

   **For files < 1500 lines**: Write entire file at once with Write tool.

   **Structure** (follow existing guideline format):

   ```markdown
   # {Language} Corporate Guidelines

   **Tech Stack**: {Language, Frameworks, Use Cases}
   **Auto-detected from**: {File patterns}
   **Version**: X.Y.Z

   ---

   ## Scaffolding

   **MUST**:
   - {Principle from docs or code}

   **NEVER**:
   - {Prohibited pattern from docs or code}

   **Rationale**: {Why this matters}

   ---

   ## Package Registry

   **MUST**:
   - Configure package manager with corporate repository
   - All packages resolved through corporate registry only

   **Registry URL**: {ARTIFACTORY_URL or "Not configured"}

   **Library Validation Rules**:

   **Standard/Built-in Libraries** - No validation needed:
   - Language standard library (e.g., `java.util.*`, Python's `os`/`sys`, Node's `fs`/`path`)
   - Framework built-ins (e.g., Spring Core modules included in starter, React core)
   - **Action**: Use freely, no Artifactory check required

   **External/Third-Party Libraries** - Validation required:
   - Community packages (e.g., `lodash`, `requests`, `gson`, `axios`)
   - Framework extensions (e.g., `spring-boot-starter-data-jpa`, `express-validator`)
   - **Action**: Check Artifactory for approval before use

   **Corporate Internal Libraries** - Validation required:
   - Company-developed packages (e.g., `acmecorp-auth`, `company-http-client`)
   - Internal shared utilities
   - **Action**: Check Artifactory, use approved versions only

   **Rationale**: Using corporate registry ensures approved libraries and prevents supply chain attacks. Standard libraries are pre-approved by language/framework maintainers.

   ---

   ## Mandatory Libraries

   ### {Category 1}

   **MUST** use: `package-name` package
   **Requirements**:
   - {Principle-based requirement}
   - {Another principle-based requirement}

   **Features**: {What this provides}

   **NEVER**:
   - {What not to do}

   [... continue for all sections ...]

   ---

   ## Non-Compliance

   If corporate library unavailable or causes blocking issue:

   1. Document violation in `.guidelines-todo.md` with justification
   2. Create ticket to resolve (target: next sprint)
   3. Proceed with alternative, mark with comment for tracking
   ```

9. **Generate analysis report** (detailed findings):

   **File path**: `.guidelines-analysis/{stack}-analysis-report.md`

   **Contents**:
   - Summary: Sources analyzed, principles extracted, conflicts resolved
   - Document analysis findings (from Phase 1)
   - Code analysis findings (from Phase 2)
   - Synthesis decisions and user resolutions
   - Version history and changes made

10. **Display summary to user**:

    ```text
    ✓ GUIDELINE GENERATION COMPLETE

    Generated: .guidelines/java-guidelines.md
    Version: 2.0.0 (updated from 1.2.0)
    Update Mode: FULL_REGEN
    Backup: .guidelines/java-guidelines-v1.2.0.md.bak

    Sources Analyzed:
    - Documents: 3 files (security-guidelines.pdf, java-coding-standards.pdf, architecture-patterns.md)
    - Reference Projects: 3 projects (project-a, project-b, project-c)
    - Total Files Scanned: 1,048 files

    Principles Extracted:
    - From Documents: 67 explicit principles
    - From Code: 43 HIGH confidence patterns, 12 MEDIUM confidence patterns
    - Total Synthesized: 89 principles (34 MUST, 28 SHOULD, 12 NEVER, 15 MAY)

    Conflicts Resolved: 3
    - Authentication Library: acmecorp-auth v2.1.x (user choice: follow code)
    - Logging Framework: SLF4J + Log4j2 (user choice: follow code)
    - Integration Testing: TestContainers + WireMock both allowed (user choice: scenario-based)

    Sections Updated:
    1. Scaffolding ✓
    2. Package Registry ✓
    3. Mandatory Libraries ✓
    4. Banned Libraries ✓
    5. Architecture ✓
    6. Security ✓
    7. Coding Standards ✓
    8. Dependency Management ✓
    9. Testing ✓
    10. Build & Deployment ✓
    11. Observability ✓

    Analysis Report: .guidelines-analysis/java-analysis-report.md

    Next Steps:
    1. Review generated guideline: .guidelines/java-guidelines.md
    2. Review detailed analysis: .guidelines-analysis/java-analysis-report.md
    3. Commit updated guidelines to version control
    4. Share with development teams
    5. Update any project-specific constitution if needed
    ```

**IMPORTANT**:

- Ensure all principles are version-agnostic (no code examples)
- Include rationale for non-obvious requirements
- Maintain consistency with existing guideline format
- Version increment follows semantic versioning rules

---

## Error Recovery

**If SOURCES_PATH doesn't exist**:

- ERROR: "Sources path not found: [PATH]. Please verify the path and try again."

**If SOURCES_PATH has no docs/ or reference-projects/ subdirectories**:

- WARN: "Expected subdirectories 'docs/' and 'reference-projects/' not found. Looking for documents and projects in root..."
- Attempt to categorize files by extension (\*.pdf, \*.md, \*.docx = docs, directories with code = projects)

**If no documents found**:

- ERROR: "No corporate documents found in [PATH]/docs/. At least one document is required."
- Suggest: "Place corporate standards documents (PDF, Markdown, Word) in docs/ subdirectory"

**If no reference projects found**:

- ERROR: "No reference projects found in [PATH]/reference-projects/. At least one reference project is required."
- Suggest: "Place high-quality reference codebases in reference-projects/ subdirectory"

**If tech stack cannot be detected**:

- WARN: "Could not auto-detect tech stack from reference projects."
- ASK: "Please specify tech stack manually (java, python, reactjs, dotnet, nodejs): ___"

**If document parsing fails** (e.g., encrypted PDF):

- WARN: "Could not read [document-name]. Skipping this document."
- CONTINUE: Proceed with other documents
- SUGGEST: "For best results, use Markdown or plain text formats"

**If UPDATE_MODE = REPLACE but sections not found**:

- ERROR: "Selected sections [X, Y, Z] not found in existing guideline file."
- SUGGEST: "Use FULL_REGEN mode or select valid section numbers"

**If existing guideline file is malformed**:

- WARN: "Existing guideline file has unexpected format. Proceeding with FULL_REGEN mode."
- CREATE: Backup of malformed file before overwriting

**If consensus is too low** (all patterns are 1/3):

- WARN: "Reference projects show no consensus patterns. This may indicate:"
  - "  - Projects are too different (not built with same standards)"
  - "  - Projects are too small (not enough code to analyze)"
  - "  - Projects use different tech stacks"
- ASK: "Do you want to continue anyway? [Y/N]"

---

## Notes

- **Detailed workflow steps** and persona instructions are embedded above
- **Guideline template structure** is defined in `.guidelines/README.md`
- **RFC 2119 keywords**: MUST, SHOULD, MAY, MUST NOT, SHOULD NOT, MAY NOT (use NEVER for clarity)
- **Version management**: Follow semantic versioning (MAJOR.MINOR.PATCH)
- **Multi-stack support**: Generate separate guideline files for each detected stack

---
