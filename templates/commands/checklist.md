---
description: Generate a custom checklist for the current feature based on user requirements.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Execution Steps

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS list.
   - All file paths must be absolute.

2. **Clarify intent (dynamic)**: Derive THREE contextual clarifying questions (no pre-baked catalog). They MUST:
   - Be generated from the user's phrasing + extracted signals from spec/plan/tasks
   - Only ask about information that materially changes checklist content
   - Be skipped individually if already unambiguous in `$ARGUMENTS`
   - Prefer precision over breadth

   Generation algorithm:
   1. Extract signals: feature domain keywords (e.g., auth, latency, UX, API), risk indicators ("critical", "must", "compliance"), stakeholder hints ("QA", "review", "security team"), and explicit deliverables ("a11y", "rollback", "contracts").
   2. Cluster signals into candidate focus areas (max 4) ranked by relevance.
   3. Identify probable audience & timing (author, reviewer, QA, release) if not explicit.
   4. Detect missing dimensions: scope breadth, depth/rigor, risk emphasis, exclusion boundaries, measurable acceptance criteria.
   5. Formulate up to three questions chosen from these archetypes:
      - Scope refinement (e.g., "Should this include integration touchpoints with X and Y or stay limited to local module correctness?")
      - Risk prioritization (e.g., "Which of these potential risk areas should receive mandatory gating checks?")
      - Depth calibration (e.g., "Is this a lightweight pre-commit sanity list or a formal release gate?")
      - Audience framing (e.g., "Will this be used by the author only or peers during PR review?")
      - Boundary exclusion (e.g., "Should we explicitly exclude performance tuning items this round?")

   Question formatting rules:
   - If presenting options, generate a compact table with columns: Option | Candidate | Why It Matters
   - Limit to A–E options maximum; omit table if a free-form answer is clearer
   - Never ask the user to restate what they already said
   - Avoid speculative categories (no hallucination). If uncertain, ask explicitly: "Confirm whether X belongs in scope." 

   Defaults when interaction impossible:
   - Depth: Standard
   - Audience: Reviewer (PR) if code-related; Author otherwise
   - Focus: Top 2 relevance clusters

   Output the three questions (or fewer if not needed) and wait for answers before continuing. Clearly label each as Q1/Q2/Q3.

3. **Understand user request**: Combine `$ARGUMENTS` + clarifying answers:
   - Derive checklist theme (e.g., security, review, deploy, ux)
   - Consolidate explicit must-have items mentioned by user
   - Map focus selections to category scaffolding
   - Infer any missing context from spec/plan/tasks (do NOT hallucinate)

4. **Load feature context**: Read from FEATURE_DIR:
   - spec.md: Feature requirements and scope
   - plan.md (if exists): Technical details, dependencies
   - tasks.md (if exists): Implementation tasks
   - Use context to enrich or validate checklist items (omit irrelevant categories)

5. **Generate checklist**:
   - Create `FEATURE_DIR/checklists/` directory if it doesn't exist
   - Generate unique checklist filename:
     * Use short, descriptive name based on checklist type
     * Format: `[type].md` (e.g., `ux.md`, `test.md`, `security.md`, `deploy.md`)
     * If file exists, append counter: `[type]-2.md`, `[type]-3.md`, etc.
     * Examples: `ux.md`, `test.md`, `security.md`, `deploy.md`, `review-2.md`
   - Use format: `[ ] CHK001 Item description here`
   - Number items sequentially starting from CHK001
   - Group items by category/section if applicable
   - Include brief explanations or links where helpful
   - Each `/checklist` run creates a NEW file (never overwrites existing checklists)
   - **CRITICAL**: Focus checklist items on **specification and requirements quality** for the domain:
     * Validate scenario coverage and edge cases
     * Ensure requirements are clear, testable, and measurable
     * Check for completeness of acceptance criteria
     * Verify domain-specific considerations are addressed
     * DO NOT include implementation details like unit tests, code quality, or deployment steps

6. **Checklist structure**:
   ```markdown
   # [Checklist Type] Checklist: [Feature Name]
   
   **Purpose**: [Brief description of what this checklist covers]
   **Created**: [Date]
   
   ## [Category 1]
   - [ ] CHK001 First item
   - [ ] CHK002 Second item
   
   ## [Category 2]
   - [ ] CHK003 Third item
   ```

7. **Report**: Output full path to created checklist, item count, and remind user that each run creates a new file. Summarize:
   - Focus areas selected
   - Depth level
   - Actor/timing
   - Any explicit user-specified must-have items incorporated

**Important**: Each `/checklist` command invocation creates a NEW checklist file using short, descriptive names. This allows:
- Multiple checklists of different types (e.g., `ux.md`, `test.md`, `security.md`)
- Simple, memorable filenames that indicate checklist purpose
- Counter-based uniqueness for duplicate types (e.g., `review-2.md`)
- Easy identification and navigation in the checklists/ folder

To avoid clutter, use descriptive types and clean up obsolete checklists when done.

## Example Checklist Types

**Specification Review:** `spec-review.md`
- Requirement completeness and clarity
- User scenarios and edge cases coverage
- Acceptance criteria definition
- Domain-specific considerations

**Requirements Quality:** `requirements.md`
- Testable and measurable outcomes
- Stakeholder alignment verification
- Assumptions and constraints documentation
- Success metrics definition

**UX/Accessibility Scenarios:** `ux.md` or `a11y.md`
- User journey completeness
- Accessibility requirement coverage
- Responsive design considerations
- Internationalization needs

**Security Requirements:** `security.md`
- Threat model coverage
- Authentication/authorization requirements
- Data protection requirements
- Compliance and regulatory needs

**API/Integration Scenarios:** `api.md`
- Contract completeness
- Error handling scenarios
- Backward compatibility considerations
- Integration touchpoint coverage

Generate checklist items that validate the **quality and completeness of specifications and requirements** for the domain, focusing on scenarios, edge cases, and requirement clarity rather than implementation details.
