---
description: Create or update the project constitution from interactive or provided principle inputs. Detects whether this is a new or existing solution — new solutions go through a guided bootstrap to collect durable inputs first; existing solutions follow the standard update flow. Ensures all dependent templates stay in sync.
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

## Pre-Execution Checks

**Check for extension hooks (before constitution update)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_constitution` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
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

   Wait for the result of the hook command before proceeding to Step 0.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Step 0 — Determine Solution State

Before generating or revising the constitution, determine whether this is a **new** or **existing** solution automatically — do not ask the user.

**Detection rule** (check in order):

1. If `.specify/memory/constitution.md` exists **and** contains concrete content (not just unfilled square-bracket placeholder identifiers such as `[PROJECT_NAME]`), treat as **existing** → proceed to **Path A**.
2. If `.specify/memory/constitution.md` does not exist **but** `.specify/templates/constitution-template.md` exists, treat the solution as an **initialized existing repo with a missing working copy** → copy the template to `.specify/memory/constitution.md`, then proceed to **Path A**.
3. If `.specify/memory/constitution.md` exists but contains only unfilled square-bracket placeholder identifiers, treat as **new** → proceed to **Path B**.
4. If neither `.specify/memory/constitution.md` nor `.specify/templates/constitution-template.md` exists, treat as **new** → proceed to **Path B**.

---

## Path A — Existing Solution

If you determined this is an existing solution in Step 0, follow the standard constitution update flow.

You are updating the project constitution at `.specify/memory/constitution.md`. This file is a TEMPLATE containing placeholder tokens in square brackets (e.g. `[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`). Your job is to (a) collect/derive concrete values, (b) fill the template precisely, and (c) propagate any amendments across dependent artifacts.

**Note**: The missing-file recovery in Path A applies only when `.specify/templates/constitution-template.md` exists, which indicates the repo was already initialized and only the working copy is missing. In that case, copy the template first.

Follow this execution flow:

1. Load the existing constitution at `.specify/memory/constitution.md`.
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
   - Read `.specify/templates/plan-template.md` and ensure any "Constitution Check" or rules align with updated principles.
   - Read `.specify/templates/spec-template.md` for scope/requirements alignment—update if constitution adds/removes mandatory sections or constraints.
   - Read `.specify/templates/tasks-template.md` and ensure task categorization reflects new or removed principle-driven task types (e.g., observability, versioning, testing discipline).
   - Read each command file in `.specify/templates/commands/*.md` (including this one) to verify no outdated references (agent-specific names like CLAUDE only) remain when generic guidance is required.
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

7. Write the completed constitution back to `.specify/memory/constitution.md` (overwrite).

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

Do not create a new template; always operate on the existing `.specify/memory/constitution.md` file.

---

## Path B — New Solution Bootstrap

If `solution_state = new`, do **NOT** draft the constitution yet.

### B.1 — Collect minimum durable inputs

Ask exactly these questions to gather the information needed for a strong constitution. Do not ask for feature-by-feature requirements, screen flows, or pseudo-code. Present options and examples as shown below to reduce ambiguity.

1. **solution_name** — "What is the name of the solution?"
   - Example: `InventoryTracker`, `PayrollEngine`, `Contoso.Api`

2. **solution_purpose** — "In 2–5 sentences, what is this solution for?"
   - Example: *"A desktop tool for warehouse staff to track incoming shipments, manage stock levels, and generate reorder reports. It replaces the current spreadsheet-based workflow."*

3. **solution_type** — "What type of solution is this?"
   - Options: `Windows desktop app` · `Web app` · `REST API` · `Background service / worker` · `Class library / SDK` · `CLI tool` · `Mobile app` · `Monorepo (multiple projects)`
   - Pick one, or describe if none fit.

4. **primary_stack** — "What is the expected primary stack or platform?"
   - Options: `C# / .NET` · `Python` · `TypeScript / Node.js` · `Java / Spring` · `Go` · `Rust` · `Ruby / Rails`
   - Include framework and database if known. Example: `C# / .NET 8, WPF, SQL Server` or `TypeScript, Next.js, PostgreSQL`

5. **core_dependencies** — "What important external systems or dependencies does it rely on?"
   - Examples: Active Directory, Azure Blob Storage, Stripe API, SAP, RabbitMQ, a shared internal auth service
   - Reply `none` if the solution is self-contained.

6. **security_constraints** — "What security or authentication constraints must always be followed?"
   - Options: `Windows Auth / AD` · `OAuth 2.0 / OIDC` · `API keys` · `Certificate-based` · `Role-based access (RBAC)` · `No auth required`
   - Also mention: secrets management, encryption-at-rest, PII handling, compliance standards (HIPAA, SOC 2, GDPR) if applicable.
   - Reply `unknown` if not yet decided — safe defaults will be used.

7. **data_rules** — "What data/storage rules must always be followed?"
   - Options: `SQL Server only` · `PostgreSQL only` · `SQLite (local)` · `NoSQL (MongoDB, Cosmos)` · `File-based storage` · `No persistent storage`
   - Also consider: parameterized queries only, no raw SQL in app code, no sensitive data in logs, soft-delete policy, audit trail required.
   - Reply `unknown` if not yet decided — safe defaults will be used.

8. **quality_rules** — "What quality expectations must always apply?"
   - Options: `Unit tests required` · `Integration tests required` · `Code review required` · `CI pipeline must pass` · `Structured logging` · `Responsive UI (< 200ms)` · `Retry / resilience handling` · `Accessibility (WCAG)`
   - Pick all that apply, or describe your own.
   - Reply `unknown` if not yet decided — safe defaults will be used.

9. **boundary_rules** — "Does this solution need strict boundaries from other solutions or repos?"
   - Examples: *"Must not share a database with the billing system"*, *"Must communicate with the auth service only via its public API"*, *"Must be deployable independently from the monorepo"*
   - Reply `none` if there are no cross-solution boundaries.

10. **out_of_scope** — "What kinds of details should NOT go into the constitution?"
    - Options: `Feature-specific requirements` · `Screen-by-screen UI behavior` · `One-off SQL queries` · `Sprint-level priorities` · `Individual user stories`
    - Reply `standard exclusions` to use the defaults above.

### B.2 — Normalize answers into constitution categories

Map collected answers into durable constitution sections:

| Constitution category | Source inputs |
|---|---|
| **Scope** | solution_name, solution_purpose, boundary_rules |
| **Technical context** | solution_type, primary_stack, core_dependencies |
| **Security and data handling** | security_constraints, data_rules |
| **Quality and engineering standards** | quality_rules |
| **Exclusions** | out_of_scope |

Where the user answered `unknown`:
- Use safe, minimal defaults.
- Keep them generic and durable.
- Mark assumptions clearly with `<!-- ASSUMPTION: ... -->` in the generated constitution.

### B.3 — Generate the constitution

Generate a lean constitution written to `.specify/memory/constitution.md` with only durable, solution-wide principles. The constitution MUST include these sections:

1. **Scope** — Solution name, boundary, and what is in/out of scope.
2. **Purpose** — What the solution exists to do (2–5 sentences).
3. **Solution Boundary** — Strict separation from other solutions/repos if applicable.
4. **Architecture / Separation of Concerns** — High-level layering and dependency rules.
5. **Security and Credential Handling** — Authentication, authorization, secrets management rules.
6. **Data Access and Storage Rules** — Database access patterns, sensitive-data handling.
7. **Error Handling and Observability** — Logging, monitoring, error propagation rules.
8. **Quality and Testing Expectations** — Testing strategy, coverage expectations, CI gates.
9. **Simplicity and Change Governance** — YAGNI, amendment process, versioning policy.
10. **Explicit Exclusions** — What does NOT belong in the constitution (feature specs, UI flows, one-off queries).

The constitution MUST also include a **Documentation Boundaries** rule:

> - The **constitution** defines durable engineering principles and global constraints.
> - **Specifications** define functional requirements and expected behavior.
> - **Implementation plans** define technical design and architecture choices for a specific effort.
> - **Tasks** define actionable work derived from the plan.

The constitution MUST:
- Apply to the whole solution, not individual features.
- Avoid detailed functional requirements or feature-specific behavior.
- Avoid one-off implementation details unless they are global rules.
- Avoid pseudo-code unless it expresses a global engineering rule.

The constitution MUST end with:

```
**Version**: 1.0.0 | **Ratified**: <TODAY> | **Last Amended**: <TODAY>
```

### B.4 — Output behavior for new solutions

1. Summarize the captured inputs briefly.
2. Generate the constitution using those inputs.
3. Write it to `.specify/memory/constitution.md`.
4. Output a final summary with the version, a suggested commit message, and any assumptions marked for follow-up.

### B.5 — Safety rails

Never do the following in a new-solution constitution:
- Copy raw functional requirements into it.
- Include UI screen-by-screen behavior.
- Include feature-specific acceptance criteria.
- Include exact one-off queries, workflows, or pseudo-code unless they represent global rules.
- Over-specify technical details that are better suited for a plan.

When in doubt: keep the constitution smaller, move feature behavior to the spec, move implementation specifics to the plan.

## Post-Execution Checks

**Check for extension hooks (after constitution update)**:
Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.after_constitution` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
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
