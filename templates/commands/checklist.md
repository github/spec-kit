---
description: Generate a custom checklist for the current feature based on user requirements.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## Checklist Purpose: "Unit Tests for English"

**CRITICAL CONCEPT**: Checklists are **UNIT TESTS FOR REQUIREMENTS WRITING** - they validate the quality, clarity, and completeness of requirements in a given domain.

**NOT for verification/testing**:

- ❌ NOT "Test error handling works"
- ❌ NOT checking if code/implementation matches the spec

**FOR requirements quality validation**:

- ✅ "Is 'prominent display' quantified with specific sizing/positioning?" (clarity)

**Metaphor**: If your spec is code written in English, the checklist is its unit test suite - testing whether the requirements are well-written, complete, unambiguous, and ready for implementation, NOT whether the implementation works.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before checklist generation)**:
- If `.specify/extensions.yml` exists in the project root, read it and look for entries under the `hooks.before_checklist` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`; treat hooks without an `enabled` field as enabled by default
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions: if the hook has no `condition` field (or it is null/empty), treat it as executable; if it defines a non-empty `condition`, skip it and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Execution Steps.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Execution Steps

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS list.
   - All file paths must be absolute.
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **IF EXISTS**: Load `/memory/constitution.md` for project principles and governance constraints.

3. **Clarify intent (dynamic)**: Derive up to THREE initial contextual clarifying questions (no pre-baked catalog). They MUST:
   - Be generated from the user's phrasing + extracted signals from spec/plan/tasks
   - Only ask about information that materially changes checklist content
   - Be skipped individually if already unambiguous in `$ARGUMENTS`
   - Prefer precision over breadth

   Generation algorithm:
   1. Extract signals: feature domain keywords (e.g., auth, latency, UX, API), risk indicators ("critical", "must", "compliance"), stakeholder hints ("QA", "review", "security team"), explicit deliverables ("a11y", "rollback", "contracts").
   2. Cluster signals into candidate focus areas (max 4) ranked by relevance.
   3. Identify probable audience & timing (author, reviewer, QA, release) if not explicit.
   4. Detect missing dimensions: scope breadth, depth/rigor, risk emphasis, exclusion boundaries, measurable acceptance criteria.
   5. Formulate questions from these archetypes: scope refinement, risk prioritization, depth calibration, audience framing, boundary exclusion, scenario class gap (e.g., "No recovery flows detected—are rollback / partial failure paths in scope?").

   Question formatting rules:
   - If presenting options, generate a compact table with columns Option | Candidate | Why It Matters
   - Limit to A–E options maximum; omit the table if a free-form answer is clearer
   - Never ask the user to restate what they already said
   - Avoid speculative categories (no hallucination) - if uncertain, ask explicitly: "Confirm whether X belongs in scope."

   Defaults when interaction impossible:
   - Depth: Standard
   - Audience: Reviewer (PR) if code-related, Author otherwise
   - Focus: top 2 relevance clusters

   Output the questions (label Q1/Q2/Q3). After answers: if ≥2 scenario classes (Alternate / Exception / Recovery / Non-Functional domain) remain unclear, you MAY ask up to TWO more targeted follow-ups (Q4/Q5) with a one-line justification each (e.g., "Unresolved recovery path risk"). Do not exceed five total questions. Skip escalation if user explicitly declines more.

4. **Understand user request**: Combine `$ARGUMENTS` + clarifying answers:
   - Derive checklist theme (e.g., security, review, deploy, ux)
   - Consolidate explicit must-have items mentioned by user
   - Map focus selections to category scaffolding
   - Infer any missing context from spec/plan/tasks (do NOT hallucinate)

5. **Load feature context**: Read from FEATURE_DIR: spec.md (feature requirements and scope), plan.md if exists (technical details, dependencies), tasks.md if exists (implementation tasks).

   Context loading strategy:
   - Load only the portions relevant to active focus areas (avoid full-file dumping)
   - Prefer summarizing long sections into concise scenario/requirement bullets
   - Use progressive disclosure (add follow-on retrieval only if gaps detected)
   - If source docs are large, generate interim summary items instead of embedding raw text

6. **Generate checklist** - Create "Unit Tests for Requirements":
   - Create `FEATURE_DIR/checklists/` directory if it doesn't exist
   - Filename: short, descriptive domain name, format `[domain].md` (e.g., `ux.md`, `api.md`, `security.md`)
   - If the file does NOT exist: create it and number items starting from CHK001
   - If it exists: append new items, continuing from the last CHK ID (e.g., if last item is CHK015, start at CHK016)
   - Never delete or replace existing checklist content - always preserve and append

   **CORE PRINCIPLE - Test the Requirements, Not the Implementation**: every checklist item MUST evaluate the REQUIREMENTS THEMSELVES for:
   - **Completeness** (all necessary requirements present?)
   - **Clarity** (unambiguous and specific?)
   - **Consistency** (requirements align with each other?)
   - **Measurability** (objectively verifiable?)
   - **Coverage** (all scenarios/edge cases addressed?)

   See Anti-Examples below for wrong vs correct item style.

   **Category Structure** - group items by requirement quality dimension: Requirement Completeness, Requirement Clarity, Requirement Consistency, Acceptance Criteria Quality (success criteria measurable?), Scenario Coverage (all flows/cases addressed?), Edge Case Coverage (boundary conditions defined?), Non-Functional Requirements (performance, security, accessibility, etc. - specified?), Dependencies & Assumptions (documented and validated?), Ambiguities & Conflicts (what needs clarification?).

   **ITEM STRUCTURE** - each item:
   - Question format asking about requirement quality
   - Focus on what's WRITTEN (or not written) in the spec/plan
   - Include the quality dimension in brackets [Completeness/Clarity/Consistency/etc.]
   - Reference spec section `[Spec §X.Y]` when checking existing requirements
   - Use the `[Gap]` marker when checking for missing requirements
   - Example: "Is 'fast loading' quantified with specific timing thresholds? [Clarity, Spec §NFR-2]"

   **Scenario Classification & Coverage** (Requirements Quality Focus):
   - Check if requirements exist for: Primary, Alternate, Exception/Error, Recovery, Non-Functional scenarios
   - For each scenario class, ask: "Are [scenario type] requirements complete, clear, and consistent?"
   - If scenario class missing: "Are [scenario type] requirements intentionally excluded or missing? [Gap]"
   - Include resilience/rollback when state mutation occurs: "Are rollback requirements defined for migration failures? [Gap]"

   **Traceability Requirements**: MINIMUM ≥80% of items MUST include at least one traceability reference - spec section `[Spec §X.Y]` or markers `[Gap]`, `[Ambiguity]`, `[Conflict]`, `[Assumption]`. If no ID system exists: "Is a requirement & acceptance criteria ID scheme established? [Traceability]"

   **Surface & Resolve Issues** - ask questions about the requirements themselves: ambiguities (vague terms quantified with specific metrics? [Ambiguity]), conflicts (do sections contradict each other? [Conflict]), assumptions (validated? [Assumption]), dependencies (documented? [Dependency, Gap]), missing definitions (defined with measurable criteria? [Gap]).

   **Content Consolidation**: soft cap - if raw candidate items > 40, prioritize by risk/impact; merge near-duplicates checking the same requirement aspect; if >5 low-impact edge cases, create one item: "Are edge cases X, Y, Z addressed in requirements? [Coverage]"

   **🚫 ABSOLUTELY PROHIBITED** - these make it an implementation test, not a requirements test: any item starting with "Verify", "Test", "Confirm", "Check" + implementation behavior; references to code execution, user actions, system behavior; "Displays correctly", "works properly", "functions as expected"; "Click", "navigate", "render", "load", "execute"; test cases, test plans, QA procedures; implementation details (frameworks, APIs, algorithms).

   **✅ REQUIRED PATTERNS** - these test requirements quality: "Are [requirement type] defined/specified/documented for [scenario]?"; "Is [vague term] quantified/clarified with specific criteria?"; "Are requirements consistent between [section A] and [section B]?"; "Can [requirement] be objectively measured/verified?"; "Are [edge cases/scenarios] addressed in requirements?"; "Does the spec define [missing aspect]?"

7. **Structure Reference**: Generate the checklist following the canonical template in `templates/checklist-template.md` for title, meta section, category headings, and ID formatting. If template is unavailable, use: H1 title, purpose/created meta lines, `##` category sections containing `- [ ] CHK### <requirement item>` lines with globally incrementing IDs starting at CHK001.

8. **Report**: Output full path to checklist file, item count, and whether the run created a new file or appended to an existing one. Summarize: focus areas selected, depth level, actor/timing, any explicit user-specified must-have items incorporated.

**Important**: Each `__SPECKIT_COMMAND_CHECKLIST__` command invocation uses a short, descriptive checklist filename and either creates a new file or appends to an existing one, allowing multiple checklists of different types (e.g., `ux.md`, `test.md`, `security.md`) with simple, memorable names that are easy to identify in the `checklists/` folder. To avoid clutter, use descriptive types and clean up obsolete checklists when done.

## Example Checklist Types & Sample Items

Sample items in every domain test the requirements, NOT the implementation. **UX Requirements Quality** (`ux.md`):

- "Are visual hierarchy requirements defined with measurable criteria? [Clarity, Spec §FR-1]"
- "Are interaction state requirements (hover, focus, active) consistently defined? [Consistency]"
- "Are accessibility requirements specified for all interactive elements? [Coverage, Gap]"
- "Is fallback behavior defined when images fail to load? [Edge Case, Gap]"

Other domains follow the same pattern, e.g., **API** (`api.md`), **Performance** (`performance.md`), **Security** (`security.md`).

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

**Key Difference**: wrong items verify behavior ("Does it do X?" - does the system work correctly); correct items validate requirement quality ("Is X clearly specified?" - are the requirements written correctly).

## Post-Execution Checks

**Check for extension hooks (after checklist generation)**:
- If `.specify/extensions.yml` exists in the project root, read it and look for entries under the `hooks.after_checklist` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`; treat hooks without an `enabled` field as enabled by default
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions: if the hook has no `condition` field (or it is null/empty), treat it as executable; if it defines a non-empty `condition`, skip it and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently
