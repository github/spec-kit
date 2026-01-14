description: Create or update the project constitution from interactive or provided principle inputs, ensuring it aligns with the higher-level enterprise constitution and all dependent templates stay in sync.
handoffs: 
  - label: Build Specification
    agent: speckit.specify
    prompt: Implement the feature specification based on the updated constitution. I want to build...
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

You are updating the project constitution at `/memory/constitution.md`. This file is a TEMPLATE containing placeholder tokens in square brackets (e.g. `[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`). Your job is to (a) collect/derive concrete values, (b) fill the template precisely, and (c) propagate any amendments across dependent artifacts.

This project-level constitution is **subordinate to the higher-level enterprise constitution**, which is maintained in a **separate, canonical repository** (for example, an organization-wide governance repo). In this project, `/memory/enterprise-constitution.md` is treated as a **cached mirror** of that source of truth.

The project constitution MUST NOT contradict the enterprise constitution. When in doubt, prefer the higher-level rules and explicitly call out any potential tensions or conflicts.

Follow this execution flow:

1. Retrieve the higher-level enterprise constitution from its canonical repository.
   - Use user input first if it specifies where the enterprise constitution lives (e.g., Git repo URL + file path, or a direct HTTP/HTTPS URL to the Markdown file).
   - Otherwise, infer the location from existing documentation (e.g., organization docs, onboarding guides, or configuration files in the repo) and propose a best-guess location; if uncertain, ask the user to confirm.
   - Fetch the latest version of the enterprise constitution from that remote source. You MAY use tools such as raw file URLs, GitHub/GitLab web UIs, or a local checkout of the canonical repo if available in the workspace.
   - After retrieval, you MAY write or update `/memory/enterprise-constitution.md` as a **read-only cached copy** for this project, including a brief HTML comment at the top with the source repository, path, and commit/last-updated reference if known.
   - Understand the enterprise constitution's overarching principles, constraints, and non-negotiable rules.
   - If remote retrieval is not possible in this run, but the user input clearly describes enterprise-wide principles, treat those as effective higher-level rules for this run and propose creating or updating the central enterprise constitution in its own repository as a follow-up TODO. In this case, only create `/memory/enterprise-constitution.md` as a clearly marked temporary mirror, if at all.

2. Load the existing project constitution template at `/memory/constitution.md`.
   - Identify every placeholder token of the form `[ALL_CAPS_IDENTIFIER]`.
   **IMPORTANT**: The user might require less or more principles than the ones used in the template. If a number is specified, respect that - follow the general template. You will update the doc accordingly.

3. Collect/derive values for placeholders:
   - If user input (conversation) supplies a value, use it.
   - Otherwise infer from existing repo context (README, docs, prior constitution versions if embedded).
   - For governance dates: `RATIFICATION_DATE` is the original adoption date (if unknown ask or mark TODO), `LAST_AMENDED_DATE` is today if changes are made, otherwise keep previous.
   - `CONSTITUTION_VERSION` must increment according to semantic versioning rules:
     - MAJOR: Backward incompatible governance/principle removals or redefinitions.
     - MINOR: New principle/section added or materially expanded guidance.
     - PATCH: Clarifications, wording, typo fixes, non-semantic refinements.
   - If version bump type ambiguous, propose reasoning before finalizing.
   - Ensure every project-level principle and governance rule you propose is checked against the enterprise constitution:
     - If fully compatible, proceed.
     - If it narrows or strengthens an enterprise rule, explicitly document that narrowing or strengthening in the project constitution text.
     - If it appears to conflict, either adjust the project rule to comply or insert a `TODO(CONFLICT_<ID>): explanation` marker and list it in the Sync Impact Report.

4. Draft the updated constitution content:
   - Replace every placeholder with concrete text (no bracketed tokens left except intentionally retained template slots that the project has chosen not to define yet—explicitly justify any left).
   - Preserve heading hierarchy and comments can be removed once replaced unless they still add clarifying guidance.
   - Ensure each Principle section: succinct name line, paragraph (or bullet list) capturing non‑negotiable rules, explicit rationale if not obvious.
   - Ensure Governance section lists amendment procedure, versioning policy, and compliance review expectations.

5. Consistency propagation checklist (convert prior checklist into active validations):
   - Read `/templates/plan-template.md` and ensure any "Constitution Check" or rules align with updated principles.
   - Read `/templates/spec-template.md` for scope/requirements alignment—update if constitution adds/removes mandatory sections or constraints.
   - Read `/templates/tasks-template.md` and ensure task categorization reflects new or removed principle-driven task types (e.g., observability, versioning, testing discipline).
   - Read each command file in `/templates/commands/*.md` (including this one) to verify no outdated references (agent-specific names like CLAUDE only) remain when generic guidance is required.
   - Read any runtime guidance docs (e.g., `README.md`, `docs/quickstart.md`, or agent-specific guidance files if present). Update references to principles changed.
    - If `/memory/enterprise-constitution.md` exists and has been updated outside this command, ensure that any project-level references to enterprise principles still point to valid sections or concepts.

6. Produce a Sync Impact Report (prepend as an HTML comment at top of the constitution file after update):
   - Version change: old → new
   - List of modified principles (old title → new title if renamed)
   - Added sections
   - Removed sections
   - Templates requiring updates (✅ updated / ⚠ pending) with file paths
   - Enterprise alignment summary:
       - Whether the enterprise constitution was successfully retrieved from its canonical repository and whether `/memory/enterprise-constitution.md` was present/updated as a cache.
     - Any project-level principles that narrow or extend enterprise rules.
     - Any `TODO(CONFLICT_*)` items, with a short description.
   - Follow-up TODOs if any placeholders intentionally deferred.

7. Validation before final output:
   - No remaining unexplained bracket tokens.
   - Version line matches report.
   - Dates ISO format YYYY-MM-DD.
   - Principles are declarative, testable, and free of vague language ("should" → replace with MUST/SHOULD rationale where appropriate).
   - No project-level rule silently contradicts the enterprise constitution; any suspected conflict is explicitly marked with a TODO and called out in the Sync Impact Report.

8. Write the completed constitution back to `/memory/constitution.md` (overwrite).

9. Output a final summary to the user with:
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
