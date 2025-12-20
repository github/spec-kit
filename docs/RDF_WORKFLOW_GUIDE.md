# RDF-First Specification Workflow Guide

**Version**: 1.0.0
**Last Updated**: 2025-12-19
**Status**: Production

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Complete Workflow](#complete-workflow)
5. [SHACL Validation](#shacl-validation)
6. [Template System](#template-system)
7. [Troubleshooting](#troubleshooting)
8. [Examples](#examples)

---

## Overview

### The Constitutional Equation

```
spec.md = μ(feature.ttl)
```

All specifications in ggen are **deterministic transformations** from RDF/Turtle ontologies to markdown artifacts.

### Key Principles

1. **TTL files are the source of truth** - Edit these, never the markdown
2. **Markdown files are generated artifacts** - Created via `ggen render`, never manually edited
3. **SHACL shapes enforce constraints** - Validation happens before generation
4. **Idempotent transformations** - Running twice produces zero changes
5. **Cryptographic provenance** - Receipts prove spec.md = μ(ontology)

---

## Architecture

### Directory Structure

```
specs/NNN-feature-name/
├── ontology/                    # SOURCE OF TRUTH (edit these)
│   ├── feature-content.ttl      # Feature specification (user stories, requirements)
│   ├── plan.ttl                 # Implementation plan (tech stack, phases, decisions)
│   ├── tasks.ttl                # Task breakdown (actionable work items)
│   └── spec-kit-schema.ttl      # Symlink to SHACL shapes (validation rules)
├── generated/                   # GENERATED ARTIFACTS (never edit)
│   ├── spec.md                  # Generated from feature-content.ttl
│   ├── plan.md                  # Generated from plan.ttl
│   └── tasks.md                 # Generated from tasks.ttl
├── templates/                   # TERA TEMPLATES (symlinks to .specify/templates/)
│   ├── spec.tera                # Template for spec.md generation
│   ├── plan.tera                # Template for plan.md generation
│   └── tasks.tera               # Template for tasks.md generation
├── checklists/                  # QUALITY VALIDATION
│   └── requirements.md          # Specification quality checklist
├── ggen.toml                    # GGEN V6 CONFIGURATION
└── .gitignore                   # Git ignore rules
```

### The Five-Stage Pipeline (ggen v6)

```
μ₁ (Normalization)   → Canonicalize RDF + SHACL validation
  ↓
μ₂ (Extraction)      → SPARQL queries extract data from ontology
  ↓
μ₃ (Emission)        → Tera templates render markdown from SPARQL results
  ↓
μ₄ (Canonicalization)→ Format markdown (line endings, whitespace)
  ↓
μ₅ (Receipt)         → Generate cryptographic hash proving spec.md = μ(ontology)
```

---

## Prerequisites

### Required Tools

- **ggen v6**: `cargo install ggen` (or from workspace)
- **Git**: For branch management
- **Text editor**: With Turtle/RDF syntax support (VS Code + RDF extension recommended)

### Environment Setup

```bash
# Ensure ggen is available
which ggen  # Should show path to ggen binary

# Check ggen version
ggen --version  # Should be v6.x.x or higher

# Ensure you're in the ggen repository root
cd /path/to/ggen
```

---

## Complete Workflow

### Phase 1: Create Feature Specification

#### Step 1.1: Start New Feature Branch

```bash
# Run speckit.specify command (via Claude Code)
/speckit.specify "Add TTL validation command to ggen CLI that validates RDF files against SHACL shapes"
```

**What this does:**
- Calculates next feature number (e.g., 005)
- Creates branch `005-ttl-shacl-validation`
- Sets up directory structure:
  - `specs/005-ttl-shacl-validation/ontology/feature-content.ttl`
  - `specs/005-ttl-shacl-validation/ggen.toml`
  - `specs/005-ttl-shacl-validation/templates/` (symlinks)
  - `specs/005-ttl-shacl-validation/generated/` (empty, for artifacts)

#### Step 1.2: Edit Feature TTL (Source of Truth)

```bash
# Open the TTL source file
vim specs/005-ttl-shacl-validation/ontology/feature-content.ttl
```

**File structure:**

```turtle
@prefix sk: <http://github.com/github/spec-kit#> .
@prefix : <http://github.com/github/spec-kit/examples/005-ttl-shacl-validation#> .

:ttl-shacl-validation a sk:Feature ;
    sk:featureBranch "005-ttl-shacl-validation" ;
    sk:featureName "Add TTL validation command" ;
    sk:created "2025-12-19"^^xsd:date ;
    sk:status "Draft" ;
    sk:userInput "Add TTL validation command..." ;
    sk:hasUserStory :us-001, :us-002 ;
    sk:hasFunctionalRequirement :fr-001, :fr-002 ;
    sk:hasSuccessCriterion :sc-001 ;
    sk:hasEntity :entity-001 ;
    sk:hasEdgeCase :edge-001 ;
    sk:hasAssumption :assume-001 .

# User Story 1 (P1 - MVP)
:us-001 a sk:UserStory ;
    sk:storyIndex 1 ;
    sk:title "Developer validates single TTL file" ;
    sk:priority "P1" ;  # MUST be exactly "P1", "P2", or "P3" (SHACL validated)
    sk:description "As a ggen developer, I want to validate..." ;
    sk:priorityRationale "Core MVP functionality..." ;
    sk:independentTest "Run 'ggen validate <file>.ttl'..." ;
    sk:hasAcceptanceScenario :us-001-as-001 .

# Acceptance Scenario 1.1
:us-001-as-001 a sk:AcceptanceScenario ;
    sk:scenarioIndex 1 ;
    sk:given "A TTL file with known SHACL violations" ;
    sk:when "User runs ggen validate command" ;
    sk:then "Violations are detected and reported with clear error messages" .

# ... more user stories, requirements, criteria, entities, edge cases, assumptions
```

**Critical rules:**
- Priority MUST be exactly "P1", "P2", or "P3" (SHACL validated, will fail if "HIGH", "LOW", etc.)
- Dates must be in YYYY-MM-DD format with `^^xsd:date`
- All predicates must use `sk:` namespace from spec-kit-schema.ttl
- Every user story must have at least 1 acceptance scenario

#### Step 1.3: Validate TTL Against SHACL Shapes

```bash
# Run SHACL validation (automatic in ggen render, or manual)
cd specs/005-ttl-shacl-validation
ggen validate ontology/feature-content.ttl --shapes ontology/spec-kit-schema.ttl
```

**Expected output (if valid):**
```
✓ ontology/feature-content.ttl conforms to SHACL shapes
✓ 0 violations found
```

**Example error (if invalid priority):**
```
✗ Constraint violation in ontology/feature-content.ttl:
  - :us-001 has invalid sk:priority value "HIGH"
  - Expected: "P1", "P2", or "P3"
  - Shape: PriorityShape from spec-kit-schema.ttl
```

**Fix:** Change `sk:priority "HIGH"` to `sk:priority "P1"` in the TTL file.

#### Step 1.4: Generate Spec Markdown

```bash
# Generate spec.md from feature-content.ttl using ggen render
cd specs/005-ttl-shacl-validation
ggen render templates/spec.tera ontology/feature-content.ttl > generated/spec.md
```

**What this does:**
1. **μ₁ (Normalization)**: Validates ontology/feature-content.ttl against SHACL shapes
2. **μ₂ (Extraction)**: Executes SPARQL query from ggen.toml to extract data
3. **μ₃ (Emission)**: Applies spec.tera template to SPARQL results
4. **μ₄ (Canonicalization)**: Formats markdown (line endings, whitespace)
5. **μ₅ (Receipt)**: Generates cryptographic hash (stored in .ggen/receipts/)

**Generated file header:**
```markdown
<!-- Generated from feature-content.ttl - DO NOT EDIT MANUALLY -->
<!-- Regenerate with: ggen render templates/spec.tera ontology/feature-content.ttl > generated/spec.md -->

# Feature Specification: Add TTL validation command to ggen CLI

**Branch**: `005-ttl-shacl-validation`
**Created**: 2025-12-19
**Status**: Draft

...
```

**Footer:**
```markdown
---

**Generated with**: [ggen v6](https://github.com/seanchatmangpt/ggen) ontology-driven specification system
**Constitutional Equation**: `spec.md = μ(feature-content.ttl)`
```

#### Step 1.5: Verify Quality Checklist

```bash
# Review checklist (created during /speckit.specify)
cat specs/005-ttl-shacl-validation/checklists/requirements.md
```

**Checklist items:**
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] All mandatory sections completed
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable and technology-agnostic
- [ ] All user story priorities use SHACL-compliant values ("P1", "P2", "P3")

**All items must be checked before proceeding to planning.**

---

### Phase 2: Create Implementation Plan

#### Step 2.1: Run Speckit Plan Command

```bash
# Run speckit.plan command (via Claude Code)
/speckit.plan
```

**What this does:**
- Detects RDF-first feature (checks for `ontology/` + `ggen.toml`)
- Creates `ontology/plan.ttl` from template
- Symlinks `templates/plan.tera` (if not exists)
- Does NOT generate plan.md yet (manual step)

#### Step 2.2: Edit Plan TTL (Source of Truth)

```bash
# Open the plan TTL file
vim specs/005-ttl-shacl-validation/ontology/plan.ttl
```

**File structure:**

```turtle
@prefix sk: <http://github.com/github/spec-kit#> .
@prefix : <http://github.com/github/spec-kit/examples/005-ttl-shacl-validation#> .

:plan a sk:Plan ;
    sk:featureBranch "005-ttl-shacl-validation" ;
    sk:featureName "Add TTL validation command" ;
    sk:planCreated "2025-12-19"^^xsd:date ;
    sk:planStatus "Draft" ;
    sk:architecturePattern "CLI command with Oxigraph SHACL validator" ;
    sk:hasTechnology :tech-001, :tech-002 ;
    sk:hasProjectStructure :struct-001 ;
    sk:hasPhase :phase-setup, :phase-foundation, :phase-us1 ;
    sk:hasDecision :decision-001 ;
    sk:hasRisk :risk-001 ;
    sk:hasDependency :dep-001 .

# Technology: Rust
:tech-001 a sk:Technology ;
    sk:techName "Rust 1.75+" ;
    sk:techVersion "1.75+" ;
    sk:techPurpose "Existing ggen CLI infrastructure, type safety" .

# Technology: Oxigraph
:tech-002 a sk:Technology ;
    sk:techName "Oxigraph" ;
    sk:techVersion "0.3" ;
    sk:techPurpose "RDF store with SHACL validation support" .

# Project Structure
:struct-001 a sk:ProjectStructure ;
    sk:structurePath "crates/ggen-validation/src/" ;
    sk:structurePurpose "New crate for TTL/SHACL validation logic" .

# Phase: Setup
:phase-setup a sk:Phase ;
    sk:phaseId "phase-setup" ;
    sk:phaseName "Setup" ;
    sk:phaseOrder 1 ;
    sk:phaseDescription "Create crate, configure dependencies" ;
    sk:phaseDeliverables "Cargo.toml with oxigraph dependency" .

# Decision: SHACL Engine Choice
:decision-001 a sk:PlanDecision ;
    sk:decisionId "DEC-001" ;
    sk:decisionTitle "SHACL Validation Engine" ;
    sk:decisionChoice "Oxigraph embedded SHACL validator" ;
    sk:decisionRationale "Zero external deps, Rust native, sufficient for spec validation" ;
    sk:alternativesConsidered "Apache Jena (JVM overhead), pySHACL (Python interop)" ;
    sk:tradeoffs "Gain: simplicity. Lose: advanced SHACL-AF features" ;
    sk:revisitCriteria "If SHACL-AF (advanced features) becomes required" .

# Risk: SHACL Performance
:risk-001 a sk:Risk ;
    sk:riskId "RISK-001" ;
    sk:riskDescription "SHACL validation slow on large ontologies" ;
    sk:riskImpact "medium" ;
    sk:riskLikelihood "low" ;
    sk:mitigationStrategy "Cache validation results, set ontology size limits" .

# Dependency: Spec-Kit Schema
:dep-001 a sk:Dependency ;
    sk:dependencyName "Spec-Kit Schema Ontology" ;
    sk:dependencyType "external" ;
    sk:dependencyStatus "available" ;
    sk:dependencyNotes "Symlinked from .specify/ontology/spec-kit-schema.ttl" .
```

#### Step 2.3: Generate Plan Markdown

```bash
# Generate plan.md from plan.ttl
cd specs/005-ttl-shacl-validation
ggen render templates/plan.tera ontology/plan.ttl > generated/plan.md
```

**Generated output:**
```markdown
<!-- Generated from plan.ttl - DO NOT EDIT MANUALLY -->

# Implementation Plan: Add TTL validation command

**Branch**: `005-ttl-shacl-validation`
**Created**: 2025-12-19
**Status**: Draft

---

## Technical Context

**Architecture Pattern**: CLI command with Oxigraph SHACL validator

**Technology Stack**:
- Rust 1.75+ - Existing ggen CLI infrastructure, type safety
- Oxigraph (0.3) - RDF store with SHACL validation support

**Project Structure**:
- `crates/ggen-validation/src/` - New crate for TTL/SHACL validation logic

---

## Implementation Phases

### Phase 1: Setup

Create crate, configure dependencies

**Deliverables**: Cargo.toml with oxigraph dependency

...
```

---

### Phase 3: Create Task Breakdown

#### Step 3.1: Run Speckit Tasks Command

```bash
# Run speckit.tasks command (via Claude Code)
/speckit.tasks
```

**What this does:**
- SPARQL queries feature.ttl and plan.ttl to extract context
- Generates tasks.ttl with dependency-ordered task breakdown
- Links tasks to phases and user stories

#### Step 3.2: Edit Tasks TTL (Source of Truth)

```bash
# Open the tasks TTL file
vim specs/005-ttl-shacl-validation/ontology/tasks.ttl
```

**File structure:**

```turtle
@prefix sk: <http://github.com/github/spec-kit#> .
@prefix : <http://github.com/github/spec-kit/examples/005-ttl-shacl-validation#> .

:tasks a sk:Tasks ;
    sk:featureBranch "005-ttl-shacl-validation" ;
    sk:featureName "Add TTL validation command" ;
    sk:tasksCreated "2025-12-19"^^xsd:date ;
    sk:totalTasks 12 ;
    sk:estimatedEffort "3-5 days" ;
    sk:hasPhase :phase-setup, :phase-foundation, :phase-us1 .

# Phase: Setup
:phase-setup a sk:Phase ;
    sk:phaseId "phase-setup" ;
    sk:phaseName "Setup" ;
    sk:phaseOrder 1 ;
    sk:phaseDescription "Create crate and configure dependencies" ;
    sk:phaseDeliverables "Project structure, Cargo.toml" ;
    sk:hasTask :task-001, :task-002 .

:task-001 a sk:Task ;
    sk:taskId "T001" ;
    sk:taskOrder 1 ;
    sk:taskDescription "Create crates/ggen-validation directory structure" ;
    sk:filePath "crates/ggen-validation/" ;
    sk:parallelizable "false"^^xsd:boolean ;  # Must run first
    sk:belongsToPhase :phase-setup .

:task-002 a sk:Task ;
    sk:taskId "T002" ;
    sk:taskOrder 2 ;
    sk:taskDescription "Configure Cargo.toml with oxigraph dependency" ;
    sk:filePath "crates/ggen-validation/Cargo.toml" ;
    sk:parallelizable "false"^^xsd:boolean ;
    sk:belongsToPhase :phase-setup ;
    sk:dependencies "T001" .

# ... more tasks, phases
```

#### Step 3.3: Generate Tasks Markdown

```bash
# Generate tasks.md from tasks.ttl
cd specs/005-ttl-shacl-validation
ggen render templates/tasks.tera ontology/tasks.ttl > generated/tasks.md
```

**Generated output:**
```markdown
<!-- Generated from tasks.ttl - DO NOT EDIT MANUALLY -->

# Implementation Tasks: Add TTL validation command

**Branch**: `005-ttl-shacl-validation`
**Created**: 2025-12-19
**Total Tasks**: 12
**Estimated Effort**: 3-5 days

---

## Phase 1: Setup

- [ ] T001 Create crates/ggen-validation directory structure in crates/ggen-validation/
- [ ] T002 Configure Cargo.toml with oxigraph dependency in crates/ggen-validation/Cargo.toml (depends on: T001)

...
```

---

## SHACL Validation

### What is SHACL?

**SHACL (Shapes Constraint Language)** is a W3C standard for validating RDF graphs against a set of constraints (shapes).

**Example shape:**
```turtle
sk:PriorityShape a sh:NodeShape ;
    sh:targetObjectsOf sk:priority ;
    sh:in ( "P1" "P2" "P3" ) ;
    sh:message "Priority must be exactly P1, P2, or P3" .
```

### Validation Workflow

1. **Automatic validation during ggen render:**
   ```bash
   ggen render templates/spec.tera ontology/feature-content.ttl > generated/spec.md
   # ↑ Automatically validates against ontology/spec-kit-schema.ttl before rendering
   ```

2. **Manual validation:**
   ```bash
   ggen validate ontology/feature-content.ttl --shapes ontology/spec-kit-schema.ttl
   ```

### Common SHACL Violations

#### Violation: Invalid Priority Value

**Error:**
```
✗ Constraint violation in ontology/feature-content.ttl:
  - :us-001 has invalid sk:priority value "HIGH"
  - Expected: "P1", "P2", or "P3"
  - Shape: PriorityShape
```

**Fix:**
```turtle
# WRONG
:us-001 sk:priority "HIGH" .

# CORRECT
:us-001 sk:priority "P1" .
```

#### Violation: Missing Acceptance Scenario

**Error:**
```
✗ Constraint violation in ontology/feature-content.ttl:
  - :us-002 is missing required sk:hasAcceptanceScenario
  - Shape: UserStoryShape (min count: 1)
```

**Fix:**
```turtle
# Add at least one acceptance scenario
:us-002 sk:hasAcceptanceScenario :us-002-as-001 .

:us-002-as-001 a sk:AcceptanceScenario ;
    sk:scenarioIndex 1 ;
    sk:given "Initial state" ;
    sk:when "Action occurs" ;
    sk:then "Expected outcome" .
```

#### Violation: Invalid Date Format

**Error:**
```
✗ Constraint violation in ontology/feature-content.ttl:
  - :feature sk:created value "12/19/2025" has wrong datatype
  - Expected: xsd:date in YYYY-MM-DD format
```

**Fix:**
```turtle
# WRONG
:feature sk:created "12/19/2025" .

# CORRECT
:feature sk:created "2025-12-19"^^xsd:date .
```

---

## Template System

### How Tera Templates Work

**Tera** is a template engine similar to Jinja2. It takes SPARQL query results and renders them into markdown.

**Flow:**
```
ontology/feature-content.ttl
  ↓ (SPARQL query from ggen.toml)
SPARQL results (table of bindings)
  ↓ (Tera template from templates/spec.tera)
generated/spec.md
```

### SPARQL Query Example (from ggen.toml)

```sparql
SELECT ?featureBranch ?featureName ?created
       ?storyIndex ?title ?priority ?description
WHERE {
    ?feature a sk:Feature ;
             sk:featureBranch ?featureBranch ;
             sk:featureName ?featureName ;
             sk:created ?created .

    OPTIONAL {
        ?feature sk:hasUserStory ?story .
        ?story sk:storyIndex ?storyIndex ;
               sk:title ?title ;
               sk:priority ?priority ;
               sk:description ?description .
    }
}
ORDER BY ?storyIndex
```

**SPARQL results (table):**
| featureBranch | featureName | created | storyIndex | title | priority | description |
|---------------|-------------|---------|------------|-------|----------|-------------|
| 005-ttl-shacl-validation | Add TTL validation... | 2025-12-19 | 1 | Developer validates... | P1 | As a ggen developer... |
| 005-ttl-shacl-validation | Add TTL validation... | 2025-12-19 | 2 | CI validates... | P2 | As a CI pipeline... |

### Tera Template Example (spec.tera snippet)

```jinja2
{%- set feature_metadata = sparql_results | first -%}

# Feature Specification: {{ feature_metadata.featureName }}

**Branch**: `{{ feature_metadata.featureBranch }}`
**Created**: {{ feature_metadata.created }}

---

## User Stories

{%- set current_story = "" %}
{%- for row in sparql_results %}
{%- if row.storyIndex and row.storyIndex != current_story -%}
{%- set_global current_story = row.storyIndex -%}

### User Story {{ row.storyIndex }} - {{ row.title }} (Priority: {{ row.priority }})

{{ row.description }}

{%- endif %}
{%- endfor %}
```

**Rendered markdown:**
```markdown
# Feature Specification: Add TTL validation command to ggen CLI

**Branch**: `005-ttl-shacl-validation`
**Created**: 2025-12-19

---

## User Stories

### User Story 1 - Developer validates single TTL file (Priority: P1)

As a ggen developer, I want to validate...

### User Story 2 - CI validates all TTL files (Priority: P2)

As a CI pipeline, I want to...
```

---

## Troubleshooting

### Problem: "ERROR: plan.ttl not found"

**Symptom:**
```bash
$ .specify/scripts/bash/check-prerequisites.sh --json
ERROR: plan.ttl not found in /Users/sac/ggen/specs/005-ttl-shacl-validation/ontology
```

**Cause:** RDF-first feature detected (has `ontology/` and `ggen.toml`), but plan.ttl hasn't been created yet.

**Fix:**
```bash
# Run /speckit.plan to create plan.ttl
# OR manually create from template:
cp .specify/templates/rdf-helpers/plan.ttl.template specs/005-ttl-shacl-validation/ontology/plan.ttl
```

---

### Problem: "SHACL violation: invalid priority"

**Symptom:**
```bash
$ ggen render templates/spec.tera ontology/feature-content.ttl > generated/spec.md
✗ SHACL validation failed: :us-001 priority "HIGH" not in ("P1", "P2", "P3")
```

**Cause:** Priority value doesn't match SHACL constraint (must be exactly "P1", "P2", or "P3").

**Fix:**
```turtle
# Edit ontology/feature-content.ttl
# Change:
:us-001 sk:priority "HIGH" .

# To:
:us-001 sk:priority "P1" .
```

---

### Problem: "Multiple spec directories found with prefix 005"

**Symptom:**
```bash
$ .specify/scripts/bash/check-prerequisites.sh --json
ERROR: Multiple spec directories found with prefix '005': 005-feature-a 005-feature-b
```

**Cause:** Two feature directories exist with the same numeric prefix.

**Fix (Option 1 - Use SPECIFY_FEATURE env var):**
```bash
SPECIFY_FEATURE=005-feature-a .specify/scripts/bash/check-prerequisites.sh --json
```

**Fix (Option 2 - Rename one feature to different number):**
```bash
git branch -m 005-feature-b 006-feature-b
mv specs/005-feature-b specs/006-feature-b
```

---

### Problem: "Template variables are empty"

**Symptom:**
Generated markdown has blank fields:
```markdown
**Branch**: ``
**Created**:
```

**Cause:** SPARQL query variable names don't match template expectations.

**Diagnosis:**
```bash
# Check what variables the SPARQL query returns
ggen query ontology/feature-content.ttl "SELECT * WHERE { ?s ?p ?o } LIMIT 10"

# Check what variables the template expects
grep "{{" templates/spec.tera | grep -o "feature_metadata\.[a-zA-Z]*" | sort -u
```

**Fix:** Ensure SPARQL query SELECT clause includes all variables used in template (see [Verify spec.tera](#verify-spectera) section).

---

## Examples

### Example 1: Complete Feature Workflow

**Step 1: Create feature**
```bash
/speckit.specify "Add user authentication to ggen CLI"
```

**Step 2: Edit feature.ttl**
```turtle
@prefix sk: <http://github.com/github/spec-kit#> .
@prefix : <http://github.com/github/spec-kit/examples/006-user-auth#> .

:user-auth a sk:Feature ;
    sk:featureBranch "006-user-auth" ;
    sk:featureName "Add user authentication to ggen CLI" ;
    sk:created "2025-12-19"^^xsd:date ;
    sk:status "Draft" ;
    sk:hasUserStory :us-001 .

:us-001 a sk:UserStory ;
    sk:storyIndex 1 ;
    sk:title "User logs in via CLI" ;
    sk:priority "P1" ;
    sk:description "As a ggen user, I want to log in via the CLI..." ;
    sk:priorityRationale "Core security requirement" ;
    sk:independentTest "Run 'ggen login' and verify authentication" ;
    sk:hasAcceptanceScenario :us-001-as-001 .

:us-001-as-001 a sk:AcceptanceScenario ;
    sk:scenarioIndex 1 ;
    sk:given "User has valid credentials" ;
    sk:when "User runs 'ggen login' command" ;
    sk:then "User is authenticated and session token is stored" .
```

**Step 3: Validate TTL**
```bash
cd specs/006-user-auth
ggen validate ontology/feature-content.ttl --shapes ontology/spec-kit-schema.ttl
# ✓ 0 violations found
```

**Step 4: Generate spec.md**
```bash
ggen render templates/spec.tera ontology/feature-content.ttl > generated/spec.md
```

**Step 5: Verify generated markdown**
```bash
cat generated/spec.md
# Should show user story, acceptance scenario, etc.
```

---

### Example 2: Fixing SHACL Violations

**Original TTL (with errors):**
```turtle
:us-001 a sk:UserStory ;
    sk:storyIndex 1 ;
    sk:title "User logs in" ;
    sk:priority "HIGH" ;  # ❌ WRONG - should be P1, P2, or P3
    sk:description "User logs in..." .
    # ❌ MISSING: hasAcceptanceScenario (required)
```

**Validation error:**
```bash
$ ggen validate ontology/feature-content.ttl --shapes ontology/spec-kit-schema.ttl
✗ 2 violations found:
  1. :us-001 priority "HIGH" not in ("P1", "P2", "P3")
  2. :us-001 missing required sk:hasAcceptanceScenario
```

**Fixed TTL:**
```turtle
:us-001 a sk:UserStory ;
    sk:storyIndex 1 ;
    sk:title "User logs in" ;
    sk:priority "P1" ;  # ✅ FIXED - valid priority
    sk:description "User logs in..." ;
    sk:hasAcceptanceScenario :us-001-as-001 .  # ✅ ADDED - required scenario

:us-001-as-001 a sk:AcceptanceScenario ;
    sk:scenarioIndex 1 ;
    sk:given "User has credentials" ;
    sk:when "User runs login command" ;
    sk:then "User is authenticated" .
```

**Re-validation:**
```bash
$ ggen validate ontology/feature-content.ttl --shapes ontology/spec-kit-schema.ttl
✓ 0 violations found
```

---

## Next Steps

After completing the RDF-first workflow for specifications:

1. **Run /speckit.plan** to create implementation plan (plan.ttl → plan.md)
2. **Run /speckit.tasks** to generate task breakdown (tasks.ttl → tasks.md)
3. **Run /speckit.implement** to execute tasks from RDF sources
4. **Run /speckit.finish** to validate Definition of Done and create PR

---

**Generated with**: [ggen v6](https://github.com/seanchatmangpt/ggen) RDF-first specification system
**Constitutional Equation**: `documentation.md = μ(workflow-knowledge)`
