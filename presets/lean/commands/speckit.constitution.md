---
description: Create or update the project constitution. Detects whether this is a new or existing solution and adapts the workflow accordingly.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Step 0 — Determine Solution State

Before generating or revising the constitution, determine whether this is a **new** or **existing** solution.

1. If `.specify/memory/constitution.md` exists **and** contains concrete content (not just unfilled square-bracket placeholder identifiers such as `[PROJECT_NAME]`), treat as **existing** → follow Path A below.
2. If `.specify/memory/constitution.md` does not exist, or contains only unfilled square-bracket placeholder identifiers, treat as **new** → follow Path B below.

Do not ask the user — the check is automatic.

## Path A — Existing Solution

1. Create or update the project constitution and store it in `.specify/memory/constitution.md`.
   - Project name, guiding principles, non-negotiable rules
   - Derive from user input and existing repo context (README, docs)

## Path B — New Solution Bootstrap

Do **NOT** draft the constitution yet. First collect these minimum durable inputs (present options and examples to reduce ambiguity):

1. **solution_name** — "What is the name of the solution?" (e.g. `InventoryTracker`, `PayrollEngine`)
2. **solution_purpose** — "In 2–5 sentences, what is this solution for?"
3. **solution_type** — "What type of solution is this?" Options: `Windows desktop app` · `Web app` · `REST API` · `Background service` · `Class library` · `CLI tool` · `Mobile app`
4. **primary_stack** — "What is the expected primary stack or platform?" Options: `C# / .NET` · `Python` · `TypeScript / Node.js` · `Java / Spring` · `Go` · `Rust`. Include framework + database if known.
5. **core_dependencies** — "What important external systems or dependencies does it rely on?" (e.g. Active Directory, Azure, Stripe). Reply `none` if self-contained.
6. **security_constraints** — "What security or auth constraints must always be followed?" Options: `Windows Auth` · `OAuth 2.0` · `API keys` · `RBAC` · `No auth`. Reply `unknown` for safe defaults.
7. **data_rules** — "What data/storage rules must always be followed?" Options: `SQL Server only` · `PostgreSQL` · `SQLite` · `NoSQL` · `No persistent storage`. Also: parameterized queries, no sensitive data in logs. Reply `unknown` for safe defaults.
8. **quality_rules** — "What quality expectations must always apply?" Options: `Unit tests` · `Integration tests` · `Code review` · `CI must pass` · `Structured logging` · `Retry handling`. Reply `unknown` for safe defaults.
9. **boundary_rules** — "Does this solution need strict boundaries from other solutions or repos?" (e.g. no shared DB, API-only communication). Reply `none` if no boundaries.
10. **out_of_scope** — "What should NOT go into the constitution?" Options: `Feature-specific requirements` · `Screen UI behavior` · `One-off queries` · `Sprint priorities`. Reply `standard exclusions` for defaults.

Then generate a lean constitution with these sections: Scope, Purpose, Solution Boundary, Architecture, Security, Data Access, Error Handling, Quality, Change Governance, and Explicit Exclusions. Write to `.specify/memory/constitution.md`.

The constitution must contain only durable, solution-wide principles — no feature specs, UI flows, or one-off implementation details.
