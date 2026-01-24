---
description: Generate or review checklists for the current feature.
semantic_anchors:
  - Definition of Ready      # Criteria for starting work, Scrum artifact
  - Definition of Done       # Completion criteria, quality gates
  - INVEST Criteria          # Story quality validation
  - Acceptance Criteria      # Testable conditions for requirements
  - Quality Gates            # Stage-gate process checkpoints
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## Command Modes

| Mode | Trigger | Description |
|------|---------|-------------|
| **Generate** | Default, or explicit domain (e.g., `ux`, `security`) | Creates a new checklist file |
| **Review** | `review`, `validate`, `check` | Validates existing checklists against spec/plan |

**Examples:**
- `/speckit.checklist` → Generate mode (asks clarifying questions)
- `/speckit.checklist ux` → Generate UX checklist
- `/speckit.checklist review` → Review all existing checklists
- `/speckit.checklist review constitution` → Review only constitution.md checklist

---

## Checklist Purpose: "Unit Tests for English"

> **Activated Frameworks**: Definition of Ready/Done for quality gates, INVEST Criteria for story validation, Acceptance Criteria for testability.

**CRITICAL CONCEPT**: Checklists are **UNIT TESTS FOR REQUIREMENTS WRITING** - they validate the quality, clarity, and completeness of requirements in a given domain.

**NOT for verification/testing**:

- ❌ NOT "Verify the button clicks correctly"
- ❌ NOT "Test error handling works"
- ❌ NOT "Confirm the API returns 200"
- ❌ NOT checking if code/implementation matches the spec

**FOR requirements quality validation**:

- ✅ "Are visual hierarchy requirements defined for all card types?" (completeness)
- ✅ "Is 'prominent display' quantified with specific sizing/positioning?" (clarity)
- ✅ "Are hover state requirements consistent across all interactive elements?" (consistency)
- ✅ "Are accessibility requirements defined for keyboard navigation?" (coverage)
- ✅ "Does the spec define what happens when logo image fails to load?" (edge cases)

**Metaphor**: If your spec is code written in English, the checklist is its unit test suite. You're testing whether the requirements are well-written, complete, unambiguous, and ready for implementation - NOT whether the implementation works.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Execution Steps

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS list.
   - All file paths must be absolute.
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Clarify intent (dynamic)**: Derive up to THREE initial contextual clarifying questions (no pre-baked catalog). They MUST:
   - Be generated from the user's phrasing + extracted signals from spec/plan/tasks
   - Only ask about information that materially changes checklist content
   - Be skipped individually if already unambiguous in `$ARGUMENTS`
   - Prefer precision over breadth

   Generation algorithm:
   1. Extract signals: feature domain keywords (e.g., auth, latency, UX, API), risk indicators ("critical", "must", "compliance"), stakeholder hints ("QA", "review", "security team"), and explicit deliverables ("a11y", "rollback", "contracts").
   2. Cluster signals into candidate focus areas (max 4) ranked by relevance.
   3. Identify probable audience & timing (author, reviewer, QA, release) if not explicit.
   4. Detect missing dimensions: scope breadth, depth/rigor, risk emphasis, exclusion boundaries, measurable acceptance criteria.
   5. Formulate questions chosen from these archetypes:
      - Scope refinement (e.g., "Should this include integration touchpoints with X and Y or stay limited to local module correctness?")
      - Risk prioritization (e.g., "Which of these potential risk areas should receive mandatory gating checks?")
      - Depth calibration (e.g., "Is this a lightweight pre-commit sanity list or a formal release gate?")
      - Audience framing (e.g., "Will this be used by the author only or peers during PR review?")
      - Boundary exclusion (e.g., "Should we explicitly exclude performance tuning items this round?")
      - Scenario class gap (e.g., "No recovery flows detected—are rollback / partial failure paths in scope?")

   Question formatting rules:
   - If presenting options, generate a compact table with columns: Option | Candidate | Why It Matters
   - Limit to A–E options maximum; omit table if a free-form answer is clearer
   - Never ask the user to restate what they already said
   - Avoid speculative categories (no hallucination). If uncertain, ask explicitly: "Confirm whether X belongs in scope."

   Defaults when interaction impossible:
   - Depth: Standard
   - Audience: Reviewer (PR) if code-related; Author otherwise
   - Focus: Top 2 relevance clusters

   Output the questions (label Q1/Q2/Q3). After answers: if ≥2 scenario classes (Alternate / Exception / Recovery / Non-Functional domain) remain unclear, you MAY ask up to TWO more targeted follow‑ups (Q4/Q5) with a one-line justification each (e.g., "Unresolved recovery path risk"). Do not exceed five total questions. Skip escalation if user explicitly declines more.

3. **Understand user request**: Combine `$ARGUMENTS` + clarifying answers:
   - Derive checklist theme (e.g., security, review, deploy, ux)
   - Consolidate explicit must-have items mentioned by user
   - Map focus selections to category scaffolding
   - Infer any missing context from spec/plan/tasks (do NOT hallucinate)

4. **Load project references**: Read from `/memory/` directory:

   a. **Constitution** (`/memory/constitution.md`):
      - Extract "Specification Principles" section (Accessibility, Performance, Security, Error Handling, Data)
      - These are NON-NEGOTIABLE rules that EVERY spec must follow
      - Generate automatic checklist items for each principle

   b. **Architecture Registry** (`/memory/architecture-registry.md`):
      - Extract "Established Patterns" and "Technology Decisions"
      - Extract "Anti-Patterns" to avoid
      - Generate automatic checklist items for plan alignment (if plan.md exists)

   **If files don't exist or are empty templates**: Skip automatic generation, notify user that project references are not configured.

5. **Load feature context**: Read from FEATURE_DIR:
   - spec.md: Feature requirements and scope
   - plan.md (if exists): Technical details, dependencies
   - tasks.md (if exists): Implementation tasks

   **Context Loading Strategy**:
   - Load only necessary portions relevant to active focus areas (avoid full-file dumping)
   - Prefer summarizing long sections into concise scenario/requirement bullets
   - Use progressive disclosure: add follow-on retrieval only if gaps detected
   - If source docs are large, generate interim summary items instead of embedding raw text

6. **Generate checklist** - Create "Unit Tests for Requirements":
   - Create `FEATURE_DIR/checklists/` directory if it doesn't exist
   - Generate unique checklist filename:
     - Use short, descriptive name based on domain (e.g., `ux.md`, `api.md`, `security.md`)
     - Special case: `constitution.md` for constitution-based validation
     - Format: `[domain].md`
     - If file exists, append to existing file
   - Number items sequentially starting from CHK001
   - Each `/speckit.checklist` run creates a NEW file (never overwrites existing checklists)

   **CONSTITUTION-BASED ITEMS** (Auto-generated from `/memory/constitution.md`):

   For each defined principle in constitution, generate validation items:

   ```markdown
   ## Constitution Compliance

   ### Accessibility [Constitution §Accessibility]
   - [ ] CHK001 - Are accessibility requirements defined per constitution? [Constitution]
   - [ ] CHK002 - Are WCAG compliance levels specified? [Constitution §Accessibility]

   ### Performance [Constitution §Performance]
   - [ ] CHK003 - Are performance thresholds quantified per constitution? [Constitution]
   - [ ] CHK004 - Do response time requirements meet constitution minimums? [Constitution §Performance]

   ### Security [Constitution §Security]
   - [ ] CHK005 - Are security requirements defined per constitution? [Constitution]
   - [ ] CHK006 - Is sensitive data handling specified? [Constitution §Security]

   ### Error Handling [Constitution §Error Handling]
   - [ ] CHK007 - Are failure modes defined per constitution? [Constitution]
   - [ ] CHK008 - Are fallback behaviors specified? [Constitution §Error Handling]
   ```

   **ARCHITECTURE REGISTRY ITEMS** (Auto-generated from `/memory/architecture-registry.md`, only if plan.md exists):

   ```markdown
   ## Architecture Alignment

   - [ ] CHK009 - Does the plan use established patterns from registry? [Registry §Patterns]
   - [ ] CHK010 - Are technology decisions aligned with registry? [Registry §Technology]
   - [ ] CHK011 - Do component conventions match registry? [Registry §Conventions]
   - [ ] CHK012 - Are any anti-patterns from registry present in the plan? [Registry §Anti-Patterns]
   ```

   **Skip sections** where constitution/registry placeholders are not filled (e.g., `[ACCESSIBILITY_REQUIREMENTS]` still present).

   **CORE PRINCIPLE - Test the Requirements, Not the Implementation**:
   Every checklist item MUST evaluate the REQUIREMENTS THEMSELVES for:
   - **Completeness**: Are all necessary requirements present?
   - **Clarity**: Are requirements unambiguous and specific?
   - **Consistency**: Do requirements align with each other?
   - **Measurability**: Can requirements be objectively verified?
   - **Coverage**: Are all scenarios/edge cases addressed?

   **Category Structure** - Group items by requirement quality dimensions:
   - **Requirement Completeness** (Are all necessary requirements documented?)
   - **Requirement Clarity** (Are requirements specific and unambiguous?)
   - **Requirement Consistency** (Do requirements align without conflicts?)
   - **Acceptance Criteria Quality** (Are success criteria measurable?)
   - **Scenario Coverage** (Are all flows/cases addressed?)
   - **Edge Case Coverage** (Are boundary conditions defined?)
   - **Non-Functional Requirements** (Performance, Security, Accessibility, etc. - are they specified?)
   - **Dependencies & Assumptions** (Are they documented and validated?)
   - **Ambiguities & Conflicts** (What needs clarification?)

   **HOW TO WRITE CHECKLIST ITEMS - "Unit Tests for English"**:

   ❌ **WRONG** (Testing implementation):
   - "Verify landing page displays 3 episode cards"
   - "Test hover states work on desktop"
   - "Confirm logo click navigates home"

   ✅ **CORRECT** (Testing requirements quality):
   - "Are the exact number and layout of featured episodes specified?" [Completeness]
   - "Is 'prominent display' quantified with specific sizing/positioning?" [Clarity]
   - "Are hover state requirements consistent across all interactive elements?" [Consistency]
   - "Are keyboard navigation requirements defined for all interactive UI?" [Coverage]
   - "Is the fallback behavior specified when logo image fails to load?" [Edge Cases]
   - "Are loading states defined for asynchronous episode data?" [Completeness]
   - "Does the spec define visual hierarchy for competing UI elements?" [Clarity]

   **ITEM STRUCTURE**:
   Each item should follow this pattern:
   - Question format asking about requirement quality
   - Focus on what's WRITTEN (or not written) in the spec/plan
   - Include quality dimension in brackets [Completeness/Clarity/Consistency/etc.]
   - Reference spec section `[Spec §X.Y]` when checking existing requirements
   - Use `[Gap]` marker when checking for missing requirements

   **EXAMPLES BY QUALITY DIMENSION**:

   Completeness:
   - "Are error handling requirements defined for all API failure modes? [Gap]"
   - "Are accessibility requirements specified for all interactive elements? [Completeness]"
   - "Are mobile breakpoint requirements defined for responsive layouts? [Gap]"

   Clarity:
   - "Is 'fast loading' quantified with specific timing thresholds? [Clarity, Spec §NFR-2]"
   - "Are 'related episodes' selection criteria explicitly defined? [Clarity, Spec §FR-5]"
   - "Is 'prominent' defined with measurable visual properties? [Ambiguity, Spec §FR-4]"

   Consistency:
   - "Do navigation requirements align across all pages? [Consistency, Spec §FR-10]"
   - "Are card component requirements consistent between landing and detail pages? [Consistency]"

   Coverage:
   - "Are requirements defined for zero-state scenarios (no episodes)? [Coverage, Edge Case]"
   - "Are concurrent user interaction scenarios addressed? [Coverage, Gap]"
   - "Are requirements specified for partial data loading failures? [Coverage, Exception Flow]"

   Measurability:
   - "Are visual hierarchy requirements measurable/testable? [Acceptance Criteria, Spec §FR-1]"
   - "Can 'balanced visual weight' be objectively verified? [Measurability, Spec §FR-2]"

   **Scenario Classification & Coverage** (Requirements Quality Focus):
   - Check if requirements exist for: Primary, Alternate, Exception/Error, Recovery, Non-Functional scenarios
   - For each scenario class, ask: "Are [scenario type] requirements complete, clear, and consistent?"
   - If scenario class missing: "Are [scenario type] requirements intentionally excluded or missing? [Gap]"
   - Include resilience/rollback when state mutation occurs: "Are rollback requirements defined for migration failures? [Gap]"

   **Traceability Requirements**:
   - MINIMUM: ≥80% of items MUST include at least one traceability reference
   - Each item should reference: spec section `[Spec §X.Y]`, or use markers: `[Gap]`, `[Ambiguity]`, `[Conflict]`, `[Assumption]`
   - If no ID system exists: "Is a requirement & acceptance criteria ID scheme established? [Traceability]"

   **Surface & Resolve Issues** (Requirements Quality Problems):
   Ask questions about the requirements themselves:
   - Ambiguities: "Is the term 'fast' quantified with specific metrics? [Ambiguity, Spec §NFR-1]"
   - Conflicts: "Do navigation requirements conflict between §FR-10 and §FR-10a? [Conflict]"
   - Assumptions: "Is the assumption of 'always available podcast API' validated? [Assumption]"
   - Dependencies: "Are external podcast API requirements documented? [Dependency, Gap]"
   - Missing definitions: "Is 'visual hierarchy' defined with measurable criteria? [Gap]"

   **Content Consolidation**:
   - Soft cap: If raw candidate items > 40, prioritize by risk/impact
   - Merge near-duplicates checking the same requirement aspect
   - If >5 low-impact edge cases, create one item: "Are edge cases X, Y, Z addressed in requirements? [Coverage]"

   **🚫 ABSOLUTELY PROHIBITED** - These make it an implementation test, not a requirements test:
   - ❌ Any item starting with "Verify", "Test", "Confirm", "Check" + implementation behavior
   - ❌ References to code execution, user actions, system behavior
   - ❌ "Displays correctly", "works properly", "functions as expected"
   - ❌ "Click", "navigate", "render", "load", "execute"
   - ❌ Test cases, test plans, QA procedures
   - ❌ Implementation details (frameworks, APIs, algorithms)

   **✅ REQUIRED PATTERNS** - These test requirements quality:
   - ✅ "Are [requirement type] defined/specified/documented for [scenario]?"
   - ✅ "Is [vague term] quantified/clarified with specific criteria?"
   - ✅ "Are requirements consistent between [section A] and [section B]?"
   - ✅ "Can [requirement] be objectively measured/verified?"
   - ✅ "Are [edge cases/scenarios] addressed in requirements?"
   - ✅ "Does the spec define [missing aspect]?"

7. **Structure Reference**: Generate the checklist following the canonical template in `templates/checklist-template.md` for title, meta section, category headings, and ID formatting. If template is unavailable, use: H1 title, purpose/created meta lines, `##` category sections containing `- [ ] CHK### <requirement item>` lines with globally incrementing IDs starting at CHK001.

8. **Report**: Output full path to created checklist, item count, and remind user that each run creates a new file. Summarize:
   - Focus areas selected
   - Depth level
   - Actor/timing
   - Any explicit user-specified must-have items incorporated

**Important**: Each `/speckit.checklist` command invocation creates a checklist file using short, descriptive names unless file already exists. This allows:

- Multiple checklists of different types (e.g., `ux.md`, `test.md`, `security.md`)
- Simple, memorable filenames that indicate checklist purpose
- Easy identification and navigation in the `checklists/` folder

To avoid clutter, use descriptive types and clean up obsolete checklists when done.

## Example Checklist Types & Sample Items

**Constitution Compliance:** `constitution.md`

Auto-generated items based on project constitution:

- "Are accessibility requirements defined per WCAG 2.1 AA as required by constitution? [Constitution §Accessibility]"
- "Are performance thresholds quantified (API < 200ms, UI < 100ms) per constitution? [Constitution §Performance]"
- "Is sensitive data identified and handling specified per constitution? [Constitution §Security]"
- "Are failure modes and fallback behaviors defined per constitution? [Constitution §Error Handling]"
- "Does the spec comply with GDPR requirements per constitution? [Constitution §Compliance]"

**Architecture Alignment:** `architecture.md`

Auto-generated items based on architecture registry (requires plan.md):

- "Does the plan follow the Repository Pattern from registry? [Registry §Patterns]"
- "Is Zod used for validation as per registry technology decisions? [Registry §Technology]"
- "Are services named {domain}Service.ts per registry conventions? [Registry §Conventions]"
- "Is direct DB access in routes avoided per registry anti-patterns? [Registry §Anti-Patterns]"

**UX Requirements Quality:** `ux.md`

Sample items (testing the requirements, NOT the implementation):

- "Are visual hierarchy requirements defined with measurable criteria? [Clarity, Spec §FR-1]"
- "Is the number and positioning of UI elements explicitly specified? [Completeness, Spec §FR-1]"
- "Are interaction state requirements (hover, focus, active) consistently defined? [Consistency]"
- "Are accessibility requirements specified for all interactive elements? [Coverage, Gap]"
- "Is fallback behavior defined when images fail to load? [Edge Case, Gap]"
- "Can 'prominent display' be objectively measured? [Measurability, Spec §FR-4]"

**API Requirements Quality:** `api.md`

Sample items:

- "Are error response formats specified for all failure scenarios? [Completeness]"
- "Are rate limiting requirements quantified with specific thresholds? [Clarity]"
- "Are authentication requirements consistent across all endpoints? [Consistency]"
- "Are retry/timeout requirements defined for external dependencies? [Coverage, Gap]"
- "Is versioning strategy documented in requirements? [Gap]"

**Performance Requirements Quality:** `performance.md`

Sample items:

- "Are performance requirements quantified with specific metrics? [Clarity]"
- "Are performance targets defined for all critical user journeys? [Coverage]"
- "Are performance requirements under different load conditions specified? [Completeness]"
- "Can performance requirements be objectively measured? [Measurability]"
- "Are degradation requirements defined for high-load scenarios? [Edge Case, Gap]"

**Security Requirements Quality:** `security.md`

Sample items:

- "Are authentication requirements specified for all protected resources? [Coverage]"
- "Are data protection requirements defined for sensitive information? [Completeness]"
- "Is the threat model documented and requirements aligned to it? [Traceability]"
- "Are security requirements consistent with compliance obligations? [Consistency]"
- "Are security failure/breach response requirements defined? [Gap, Exception Flow]"

## Anti-Examples: What NOT To Do

**❌ WRONG - These test implementation, not requirements:**

```markdown
- [ ] CHK001 - Verify landing page displays 3 episode cards [Spec §FR-001]
- [ ] CHK002 - Test hover states work correctly on desktop [Spec §FR-003]
- [ ] CHK003 - Confirm logo click navigates to home page [Spec §FR-010]
- [ ] CHK004 - Check that related episodes section shows 3-5 items [Spec §FR-005]
```

**✅ CORRECT - These test requirements quality:**

```markdown
- [ ] CHK001 - Are the number and layout of featured episodes explicitly specified? [Completeness, Spec §FR-001]
- [ ] CHK002 - Are hover state requirements consistently defined for all interactive elements? [Consistency, Spec §FR-003]
- [ ] CHK003 - Are navigation requirements clear for all clickable brand elements? [Clarity, Spec §FR-010]
- [ ] CHK004 - Is the selection criteria for related episodes documented? [Gap, Spec §FR-005]
- [ ] CHK005 - Are loading state requirements defined for asynchronous episode data? [Gap]
- [ ] CHK006 - Can "visual hierarchy" requirements be objectively measured? [Measurability, Spec §FR-001]
```

**Key Differences:**

- Wrong: Tests if the system works correctly
- Correct: Tests if the requirements are written correctly
- Wrong: Verification of behavior
- Correct: Validation of requirement quality
- Wrong: "Does it do X?"
- Correct: "Is X clearly specified?"

---

## Review Mode Execution

When `$ARGUMENTS` contains "review", "validate", or "check", execute this flow instead of generation:

### 1. Setup

Run `{SCRIPT}` from repo root and parse JSON for FEATURE_DIR.

### 2. Load Checklists

Scan `FEATURE_DIR/checklists/` for all `.md` files:
- If specific checklist specified (e.g., `review constitution`), load only that file
- Otherwise, load all checklist files

**If no checklists exist**: Abort with message "No checklists found. Run `/speckit.checklist` first to generate."

### 3. Load Feature Context

Read from FEATURE_DIR:
- `spec.md` (required)
- `plan.md` (if exists)

Also load project references if checklist contains `[Constitution]` or `[Registry]` markers:
- `/memory/constitution.md`
- `/memory/architecture-registry.md`

### 4. Validate Each Item

For each unchecked item (`- [ ]`), analyze against loaded documents:

**Validation Logic:**
1. Parse the item question (e.g., "Are accessibility requirements defined?")
2. Search spec/plan for evidence that answers the question
3. Determine status:
   - **✅ PASS**: Clear evidence found in spec/plan that satisfies the requirement
   - **❌ FAIL**: No evidence found, or evidence contradicts the requirement
   - **⚠️ PARTIAL**: Some evidence exists but incomplete or ambiguous

**For each item, record:**
- Status (PASS/FAIL/PARTIAL)
- Evidence location (e.g., "spec.md:L45-52")
- Brief justification (1 sentence)

### 5. Generate Validation Report

Output a Markdown report (do NOT write to file):

```markdown
## Checklist Validation Report

**Feature**: [FEATURE_NAME]
**Date**: [DATE]
**Checklists Reviewed**: [LIST]

### Summary

| Checklist | Total | ✅ Pass | ❌ Fail | ⚠️ Partial | Already Checked |
|-----------|-------|---------|--------|------------|-----------------|
| constitution.md | 8 | 5 | 2 | 1 | 0 |
| ux.md | 12 | 8 | 3 | 1 | 0 |

**Overall**: 13/20 items pass (65%)

### Detailed Results

#### constitution.md

| ID | Item | Status | Evidence |
|----|------|--------|----------|
| CHK001 | Are accessibility requirements defined? | ✅ PASS | spec.md:L45 defines WCAG 2.1 AA |
| CHK002 | Are performance thresholds quantified? | ❌ FAIL | No performance metrics found |
| CHK003 | Is sensitive data handling specified? | ⚠️ PARTIAL | Auth mentioned but no data classification |

### Failed Items (Action Required)

1. **CHK002** - Are performance thresholds quantified?
   - **Gap**: spec.md has no performance section
   - **Suggestion**: Add NFR section with response time targets

2. **CHK005** - Are error handling patterns defined?
   - **Gap**: Only happy path documented
   - **Suggestion**: Add error scenarios to each user story

### Partial Items (Review Recommended)

1. **CHK003** - Is sensitive data handling specified?
   - **Found**: Authentication flow mentions password hashing
   - **Missing**: No data classification or retention policy
```

### 6. Offer Auto-Check

After presenting the report, ask:

> "Would you like me to mark the {N} passing items as checked in the checklist files? (yes/no)"

**If user confirms:**
- Update each checklist file, changing `- [ ]` to `- [x]` for PASS items only
- Add validation timestamp as comment: `<!-- Validated: {DATE} -->`
- Report files updated

**If user declines:**
- No changes made
- Remind user they can manually check items

### 7. Suggest Next Steps

Based on results:

- **All PASS**: "All checklist items validated. Ready for `/speckit.implement`."
- **Some FAIL**: "Address {N} failed items before implementation. Consider running `/speckit.clarify` to resolve gaps."
- **Many FAIL**: "Significant gaps detected. Consider revisiting `/speckit.specify` to improve spec completeness."
