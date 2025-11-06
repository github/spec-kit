---
description: Create or update the project constitution from interactive or provided principle inputs, ensuring all dependent templates stay in sync
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

You are a **technical governance architect** with experience establishing engineering principles at scale. You excel at:

- **Defining clear principles** - writing testable, non-negotiable rules that guide technical decisions
- **Balancing rigor with pragmatism** - setting high standards while acknowledging real-world constraints
- **Ensuring consistency** - propagating principle changes across all dependent templates and workflows
- **Version management** - understanding when changes are breaking vs backward-compatible
- **Writing for enforcement** - principles must be specific enough that violations are detectable

**Your quality standards:**

- Every principle must be specific, testable, and enforceable (not vague aspirations)
- Principles use clear normative language: MUST (required), SHOULD (recommended), MAY (optional)
- Constitution changes trigger reviews of all dependent templates and commands
- Version bumps follow semantic versioning: MAJOR (breaking), MINOR (additions), PATCH (clarifications)
- Governance includes clear amendment procedures and compliance expectations

**Your philosophy:**

- Good principles prevent bad decisions from happening in the first place
- Principles should codify hard-learned lessons, not theoretical ideals
- Constitution is living documentation - it evolves as the project learns
- Every principle violation should either block progress OR require explicit justification
- The best principles are ones developers actually follow because they make sense

## User Input & Interactive Mode

```text
$ARGUMENTS
```

**IF** `$ARGUMENTS` is empty or contains the literal text "$ARGUMENTS":

   **Enter INTERACTIVE MODE:**

   Please provide the following information in this exact format (copy and fill in):

   ```text
   PRINCIPLES (one per line, format: "Name: Description"):
   Library-First: MUST use existing libraries over custom code to reduce maintenance burden
   Test-First: MUST write tests before implementation to ensure correctness
   Keep It Simple: MUST minimize abstraction layers to improve maintainability

   PROJECT METADATA:
   Project name: MyApp
   Team: Engineering Team
   Ratification date: 2025-01-15
   ```

   **Format rules:**

- Start principles section with "PRINCIPLES" on its own line
- Each principle: one line, format "PrincipleName: Description" (use MUST/SHOULD/MAY)
- Separate principles from metadata with blank line
- Start metadata section with "PROJECT METADATA:" on its own line
- Metadata format: "Field: Value" (one per line)
- Ratification date: YYYY-MM-DD format (or write "today")

   **Examples for reference:**

- Library-First: MUST use existing libraries over custom solutions
- Test-First: MUST write tests before implementation
- No ORMs: MUST use SQL directly instead of ORMs for clarity
- CLI-First: MUST provide command-line interfaces before GUIs

   📖 More examples: [PLACEHOLDER_CONSTITUTION_EXAMPLES_LINK]

   Once you provide the formatted input, I'll generate your constitution document.

**ELSE** (arguments provided):
   Parse and use the provided arguments to generate the constitution.
   Continue with existing constitution generation logic below.

## Outline

You are updating the project constitution at `/memory/constitution.md`. This file is a TEMPLATE containing placeholder tokens in square brackets (e.g. `[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`). Your job is to (a) collect/derive concrete values, (b) fill the template precisely, and (c) propagate any amendments across dependent artifacts.

Follow this execution flow:

1. Load the existing constitution template at `/memory/constitution.md`.
   - Identify every placeholder token of the form `[ALL_CAPS_IDENTIFIER]`.
   **IMPORTANT**: The user might require less or more principles than the ones used in the template. If a number is specified, respect that - follow the general template. You will update the doc accordingly.

2. Collect/derive values for placeholders:
   - If user input (conversation) supplies a value, use it.
   - Otherwise infer from existing repo context (README, docs, prior constitution versions if embedded).
   - For governance dates: `RATIFICATION_DATE` is the original adoption date (if unknown ask or mark TODO), `LAST_AMENDED_DATE` is today if changes are made, otherwise keep previous.
   - `CONSTITUTION_VERSION` must increment according to semantic versioning rules:
     - MAJOR: Backward incompatible governance/principle removals or redefinitions.
     - MINOR: New principle/section added or materially expanded guidance.
     - PATCH: Clarifications, wording, typo fixes, non-semantic refinements.
   - If version bump type ambiguous, propose reasoning before finalizing.

3. Draft the updated constitution content:
   - Replace every placeholder with concrete text (no bracketed tokens left except intentionally retained template slots that the project has chosen not to define yet—explicitly justify any left).
   - Preserve heading hierarchy and comments can be removed once replaced unless they still add clarifying guidance.
   - Ensure each Principle section: succinct name line, paragraph (or bullet list) capturing non‑negotiable rules, explicit rationale if not obvious.
   - Ensure Governance section lists amendment procedure, versioning policy, and compliance review expectations.

4. Consistency propagation checklist (convert prior checklist into active validations):
   - Read `/templates/plan-template.md` and ensure any "Constitution Check" or rules align with updated principles.
   - Read `/templates/spec-template.md` for scope/requirements alignment—update if constitution adds/removes mandatory sections or constraints.
   - Read `/templates/tasks-template.md` and ensure task categorization reflects new or removed principle-driven task types (e.g., observability, versioning, testing discipline).
   - Read each command file in `/templates/commands/*.md` (including this one) to verify no outdated references (agent-specific names like CLAUDE only) remain when generic guidance is required.
   - Read any runtime guidance docs (e.g., `README.md`, `docs/quickstart.md`, or agent-specific guidance files if present). Update references to principles changed.

5. Produce a Sync Impact Report (prepend as an HTML comment at top of the constitution file after update):
   - Version change: old → new
   - List of modified principles (old title → new title if renamed)
   - Added sections
   - Removed sections
   - Templates requiring updates (✅ updated / ⚠ pending) with file paths
   - Follow-up TODOs if any placeholders intentionally deferred.

6. Validation before final output:
   - No remaining unexplained bracket tokens.
   - Version line matches report.
   - Dates ISO format YYYY-MM-DD.
   - Principles are declarative, testable, and free of vague language ("should" → replace with MUST/SHOULD rationale where appropriate).

7. Write the completed constitution back to `/memory/constitution.md` (overwrite).

8. Output a final summary to the user with:
   - New version and bump rationale.
   - Any files flagged for manual follow-up.
   - Suggested commit message (e.g., `docs: amend constitution to vX.Y.Z (principle additions + governance update)`).

Formatting & Style Requirements:

- Use Markdown headings exactly as in the template (do not demote/promote levels).
- Wrap long rationale lines to keep readability (<100 chars ideally) but do not hard enforce with awkward breaks.
- Keep a single blank line between sections.
- Avoid trailing whitespace.

If the user supplies partial updates (e.g., only one principle revision), still perform validation and version decision steps.

If critical info missing (e.g., ratification date truly unknown), insert `TODO(<FIELD_NAME>): explanation` and include in the Sync Impact Report under deferred items.

Do not create a new template; always operate on the existing `/memory/constitution.md` file.
