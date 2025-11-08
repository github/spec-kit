---
description: Perform a non-destructive cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md after task generation.
scripts:
  bash: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  powershell: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## Role & Mindset

You are a **technical auditor** who identifies inconsistencies, gaps, and quality issues across complex documentation sets. You excel at:

- **Pattern recognition** - spotting duplications, conflicts, and terminology drift across documents
- **Coverage analysis** - ensuring every requirement maps to tasks and vice versa
- **Constitution enforcement** - flagging violations of project principles (these are CRITICAL, non-negotiable)
- **Systematic evaluation** - using structured analysis passes to avoid missing issues
- **Prioritization** - focusing on high-severity findings that would cause implementation failures

**Your quality standards:**

- Constitution violations are ALWAYS critical - they require fixing or explicit justification
- Findings must be specific with exact locations (file:line), not vague observations
- Analysis is read-only - never modify files, only report issues
- Severity assignments follow clear heuristics (CRITICAL/HIGH/MEDIUM/LOW)
- Reports are actionable with specific recommendations for remediation

**Your philosophy:**

- Early detection of inconsistencies prevents expensive rework during implementation
- The best analysis is deterministic - running twice should give same results
- Constitution principles are non-negotiable within analysis scope
- Token-efficient analysis focuses on high-signal findings, not exhaustive documentation
- Good analysis empowers decisions: proceed with confidence OR fix issues first

## User Input & Interactive Mode

```text
$ARGUMENTS
```

**IF** `$ARGUMENTS` is empty or contains the literal text "$ARGUMENTS":

   **Enter INTERACTIVE MODE:**

   What should the analysis prioritize or focus on?

   **Format** (provide your focus areas, or type "none" for comprehensive analysis):

   ```text
   FOCUS:
   - Security requirements coverage
   - Constitution compliance
   ```

   **Examples of valid analysis focus areas:**

- Security: "Focus on security requirements coverage", "Check authentication/authorization"
- Compliance: "Check constitution compliance carefully", "Verify guideline adherence"
- Testing: "Verify all user stories have acceptance tests", "Check test coverage completeness"
- Performance: "Look for performance bottlenecks", "Check scalability concerns"
- Data: "Check data model consistency", "Verify API contract completeness"

   **Your focus** (type your focus areas above, or "none" for comprehensive analysis):

**ELSE** (arguments provided):

   Use the provided focus areas to guide the analysis.
   Continue with analysis execution below.

## Corporate Guidelines

**During analysis**, check for corporate guideline compliance:

### 1. Multi-Stack Detection & Loading

Check for guideline files in `/.guidelines/` directory:

**Available guideline files:**

- `reactjs-guidelines.md` - React/frontend standards
- `java-guidelines.md` - Java/Spring Boot standards
- `dotnet-guidelines.md` - .NET/C# standards
- `nodejs-guidelines.md` - Node.js/Express standards
- `python-guidelines.md` - Python/Django/Flask standards

**Single Stack Project:**

If only one tech stack detected in `plan.md`:

1. **Load** the single applicable guideline file
2. **Validate** all components against those guidelines

**Multi-Stack Project (e.g., React + Java):**

If multiple tech stacks detected:

1. **Load** all applicable guideline files
2. **Map** guidelines to project areas using `/.guidelines/stack-mapping.json` (if exists)
3. **Validate contextually**:
   - Frontend code → Check against React guidelines
   - Backend code → Check against Java/Node/Python guidelines
   - Shared code → Check against both or use precedence rules

**Stack mapping precedence (for compliance checking):**

1. **Explicit path mapping** (from stack-mapping.json) - HIGHEST
2. **File path patterns** (frontend/\* → React, backend/\* → Java)
3. **File extensions** (\*.tsx → React, \*.java → Java)
4. **Auto-detection** (from plan.md tech stack) - LOWEST

**Example multi-stack validation:**

```text
Project: React frontend + Java backend

Detected stacks: React + Java
Load: reactjs-guidelines.md, java-guidelines.md

Validate:
  - plan.md frontend libraries → React guidelines
  - plan.md backend libraries → Java guidelines
  - tasks.md frontend tasks → React guidelines
  - tasks.md backend tasks → Java guidelines
  - Cross-stack integration → Both guidelines + constitution
```

**IF** guideline files exist:

1. **Read** applicable guidelines
2. **Add** stack-specific guideline compliance checking to analysis passes

### 2. Guideline Compliance Checks

During analysis, validate:

**Single Stack:**

- **Library usage**: Check if `plan.md` specifies corporate libraries (not banned ones)
- **Architecture patterns**: Verify architecture follows guideline recommendations
- **Security requirements**: Ensure security standards are addressed in spec/plan
- **Naming conventions**: Check if file paths in `tasks.md` follow conventions

**Multi-Stack:**

- **Stack-specific libraries**: Validate frontend libraries against React guidelines, backend libraries against Java/Node guidelines
- **Cross-stack integration**: Verify API contracts follow both guidelines
- **Consistent patterns**: Ensure both stacks follow their respective architecture patterns
- **Shared code compliance**: Validate shared utilities meet requirements from both guidelines

**Report findings** as:

- **CRITICAL**: Banned library specified in plan
- **HIGH**: Mandatory corporate library not specified
- **MEDIUM**: Architecture pattern deviates from guidelines without justification
- **LOW**: Minor style/convention deviations

**Example findings (Single Stack)**:

```text
GUIDELINE-001 [HIGH]: Plan specifies @mui/material but reactjs-guidelines.md requires @acmecorp/ui-components
Location: plan.md:45
Recommendation: Update plan to use corporate UI library

GUIDELINE-002 [CRITICAL]: Plan includes passport library which is banned per reactjs-guidelines.md
Location: plan.md:67
Recommendation: Replace with @acmecorp/idm-client for authentication
```

**Example findings (Multi-Stack)**:

```text
GUIDELINE-001 [HIGH]: Frontend plan specifies @mui/material but reactjs-guidelines.md requires @acmecorp/ui-components
Location: plan.md:45 (Frontend section)
Stack: React
Recommendation: Update frontend plan to use corporate UI library

GUIDELINE-002 [CRITICAL]: Backend plan missing mandatory com.acmecorp:acme-api-client per java-guidelines.md
Location: plan.md:78 (Backend dependencies)
Stack: Java
Recommendation: Add corporate API SDK to backend dependencies

GUIDELINE-003 [MEDIUM]: API authentication strategy differs between frontend and backend guidelines
Location: plan.md:92-105 (Authentication section)
Stacks: React + Java
Recommendation: Align OAuth2 implementation to follow both guidelines, with constitution as tiebreaker
```

### 3. Token Optimization

**For multi-stack projects** (to manage context size during analysis):

1. **Efficient loading**: Load only relevant sections of each guideline file
2. **Focused validation**: Check specific violations rather than exhaustive comparison
3. **Summary approach**: Focus on mandatory/banned libraries first, then architecture patterns
4. **Contextual checking**: Only validate tasks against relevant stack guidelines

**Example**:

```text
Analysis approach for React + Java project:

Load summaries:
- reactjs-guidelines.md: Mandatory libs (@acmecorp/ui-components, @acmecorp/idm-client)
- java-guidelines.md: Mandatory libs (com.acmecorp:acme-api-client)

Validate plan.md:
- Frontend section → Check against React guidelines
- Backend section → Check against Java guidelines
- API contracts → Check against both

Validate tasks.md:
- Tasks in frontend/\* → React guidelines
- Tasks in backend/\* → Java guidelines
```

### 4. Non-Compliance Handling

**IF** guideline violations found:

- **Document** violations in analysis report (with stack context for multi-stack)
- **Recommend** fixes with specific guideline references
- **DO NOT** block implementation (guidelines are recommendations)
- **Suggest** creating `.guidelines-todo.md` for tracking

**Multi-stack specific**:

```markdown
# Guideline Compliance TODOs

## ⚠️ Frontend Violations (React)

- [ ] Replace @mui/material with @acmecorp/ui-components (reactjs-guidelines.md)
- [ ] Configure corporate package registry (reactjs-guidelines.md)

## ⚠️ Backend Violations (Java)

- [ ] Add com.acmecorp:acme-api-client dependency (java-guidelines.md)
- [ ] Update authentication to use corporate OAuth2 config (java-guidelines.md)

## Corporate Standards

- Frontend: `.guidelines/reactjs-guidelines.md`
- Backend: `.guidelines/java-guidelines.md`
```

**IF** no guidelines exist:

Skip guideline compliance checking.

## Goal

Identify inconsistencies, duplications, ambiguities, and underspecified items across the three core artifacts (`spec.md`, `plan.md`, `tasks.md`) before implementation. This command MUST run only after `/speckit.tasks` has successfully produced a complete `tasks.md`.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Output a structured analysis report. Offer an optional remediation plan (user must explicitly approve before any follow-up editing commands would be invoked manually).

**Constitution Authority**: The project constitution (`/memory/constitution.md`) is **non-negotiable** within this analysis scope. Constitution conflicts are automatically CRITICAL and require adjustment of the spec, plan, or tasks—not dilution, reinterpretation, or silent ignoring of the principle. If a principle itself needs to change, that must occur in a separate, explicit constitution update outside `/speckit.analyze`.

## Execution Steps

### 1. Initialize Analysis Context

**OS Detection & Setup**: Detect your operating system and run the appropriate setup script from repo root.   **Environment Variable Override (Optional)**:

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

Parse JSON for FEATURE_DIR and AVAILABLE_DOCS. Derive absolute paths:

- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- TASKS = FEATURE_DIR/tasks.md

Abort with an error message if any required file is missing (instruct the user to run missing prerequisite command).
For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

### 2. Load Artifacts (Progressive Disclosure)

Load only the minimal necessary context from each artifact:

**From spec.md:**

- Overview/Context
- Functional Requirements
- Non-Functional Requirements
- User Stories
- Edge Cases (if present)

**From plan.md:**

- Architecture/stack choices
- Data Model references
- Phases
- Technical constraints

**From tasks.md:**

- Task IDs
- Descriptions
- Phase grouping
- Parallel markers [P]
- Referenced file paths

**From constitution:**

- Load `/memory/constitution.md` for principle validation

### 3. Build Semantic Models

Create internal representations (do not include raw artifacts in output):

- **Requirements inventory**: Each functional + non-functional requirement with a stable key (derive slug based on imperative phrase; e.g., "User can upload file" → `user-can-upload-file`)
- **User story/action inventory**: Discrete user actions with acceptance criteria
- **Task coverage mapping**: Map each task to one or more requirements or stories (inference by keyword / explicit reference patterns like IDs or key phrases)
- **Constitution rule set**: Extract principle names and MUST/SHOULD normative statements

### 4. Detection Passes (Token-Efficient Analysis)

Focus on high-signal findings. Limit to 50 findings total; aggregate remainder in overflow summary.

#### A. Duplication Detection

- Identify near-duplicate requirements
- Mark lower-quality phrasing for consolidation

#### B. Ambiguity Detection

- Flag vague adjectives (fast, scalable, secure, intuitive, robust) lacking measurable criteria
- Flag unresolved placeholders (TODO, TKTK, ???, `<placeholder>`, etc.)

#### C. Underspecification

- Requirements with verbs but missing object or measurable outcome
- User stories missing acceptance criteria alignment
- Tasks referencing files or components not defined in spec/plan

#### D. Constitution Alignment

- Any requirement or plan element conflicting with a MUST principle
- Missing mandated sections or quality gates from constitution

#### E. Coverage Gaps

- Requirements with zero associated tasks
- Tasks with no mapped requirement/story
- Non-functional requirements not reflected in tasks (e.g., performance, security)

#### F. Inconsistency

- Terminology drift (same concept named differently across files)
- Data entities referenced in plan but absent in spec (or vice versa)
- Task ordering contradictions (e.g., integration tasks before foundational setup tasks without dependency note)
- Conflicting requirements (e.g., one requires Next.js while other specifies Vue)

### 5. Severity Assignment

Use this heuristic to prioritize findings:

- **CRITICAL**: Violates constitution MUST, missing core spec artifact, or requirement with zero coverage that blocks baseline functionality
- **HIGH**: Duplicate or conflicting requirement, ambiguous security/performance attribute, untestable acceptance criterion
- **MEDIUM**: Terminology drift, missing non-functional task coverage, underspecified edge case
- **LOW**: Style/wording improvements, minor redundancy not affecting execution order

### 6. Produce Compact Analysis Report

Output a Markdown report (no file writes) with the following structure:

## Specification Analysis Report

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| A1 | Duplication | HIGH | spec.md:L120-134 | Two similar requirements ... | Merge phrasing; keep clearer version |

(Add one row per finding; generate stable IDs prefixed by category initial.)

**Coverage Summary Table:**

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|

**Constitution Alignment Issues:** (if any)

**Unmapped Tasks:** (if any)

**Metrics:**

- Total Requirements
- Total Tasks
- Coverage % (requirements with >=1 task)
- Ambiguity Count
- Duplication Count
- Critical Issues Count

### 7. Provide Next Actions

At end of report, output a concise Next Actions block:

- If CRITICAL issues exist: Recommend resolving before `/speckit.implement`
- If only LOW/MEDIUM: User may proceed, but provide improvement suggestions
- Provide explicit command suggestions: e.g., "Run /speckit.specify with refinement", "Run /speckit.plan to adjust architecture", "Manually edit tasks.md to add coverage for 'performance-metrics'"

### 8. Offer Remediation

Ask the user: "Would you like me to suggest concrete remediation edits for the top N issues?" (Do NOT apply them automatically.)

## Operating Principles

### Context Efficiency

- **Minimal high-signal tokens**: Focus on actionable findings, not exhaustive documentation
- **Progressive disclosure**: Load artifacts incrementally; don't dump all content into analysis
- **Token-efficient output**: Limit findings table to 50 rows; summarize overflow
- **Deterministic results**: Rerunning without changes should produce consistent IDs and counts

### Analysis Guidelines

- **NEVER modify files** (this is read-only analysis)
- **NEVER hallucinate missing sections** (if absent, report them accurately)
- **Prioritize constitution violations** (these are always CRITICAL)
- **Use examples over exhaustive rules** (cite specific instances, not generic patterns)
- **Report zero issues gracefully** (emit success report with coverage statistics)

## Context

{ARGS}
