---
description: Create or update the project constitution for Odoo 18+ implementation projects from interactive or provided principle inputs, ensuring all dependent templates stay in sync with Odoo best practices.
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

You are updating the project constitution at `/memory/constitution.md`. This file is a TEMPLATE containing placeholder tokens in square brackets (e.g. `[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`). Your job is to (a) collect/derive concrete values, (b) fill the template precisely, and (c) propagate any amendments across dependent artifacts.

For Odoo 18+ implementations, anchor the constitution to Odoo best practices: no core modifications, upgrade-safe customizations, OCA-aligned module packaging, robust access control, localization/accounting compliance, and migration readiness.

Follow this execution flow:

1. Load the existing constitution template at `/memory/constitution.md`.
   - Identify every placeholder token of the form `[ALL_CAPS_IDENTIFIER]`.
   **IMPORTANT**: The user might require less or more principles than the ones used in the template. If a number is specified, respect that - follow the general template. You will update the doc accordingly.

2. Collect/derive values for placeholders:
   - If user input (conversation) supplies a value, use it.
   - Otherwise infer from existing repo context (README, docs, prior constitution versions if embedded).
   - For governance dates: `RATIFICATION_DATE` is the original adoption date (if unknown ask or mark TODO), `LAST_AMENDED_DATE` is today if changes are made, otherwise keep previous.
   - `CONSTITUTION_VERSION` must increment according to semantic versioning rules:
     * MAJOR: Backward incompatible governance/principle removals or redefinitions.
     * MINOR: New principle/section added or materially expanded guidance.
     * PATCH: Clarifications, wording, typo fixes, non-semantic refinements.
   - If version bump type ambiguous, propose reasoning before finalizing.
   - For Odoo projects, also collect/define (use placeholders if present, otherwise incorporate directly in the text):
     * ODOO_MAJOR_VERSION (e.g., 18.0) and EDITION (Community/Enterprise).
     * Deployment model (Odoo.sh, on‑prem, cloud) and environments (dev/stage/prod).
     * No‑core‑modification policy (MUST be “no core changes”).
     * OCA dependency policy and module naming/packaging conventions.
     * Upgrade cadence and migration strategy across Odoo releases (e.g., 18.0 → 19.0).
     * Localization and accounting scope (country, fiscal localization packages).
     * Security/access baseline (groups, record rules, ACL CSV expectations).
     * Testing strategy (unit/integration, Odoo test utils) and quality gates/CI.
     * Integration approach (APIs/connectors/webhooks) and data ownership boundaries.

3. Draft the updated constitution content:
   - Replace every placeholder with concrete text (no bracketed tokens left except intentionally retained template slots that the project has chosen not to define yet—explicitly justify any left).
   - Preserve heading hierarchy and comments can be removed once replaced unless they still add clarifying guidance.
   - Ensure each Principle section: succinct name line, paragraph (or bullet list) capturing non‑negotiable rules, explicit rationale if not obvious.
   - Ensure Governance section lists amendment procedure, versioning policy, and compliance review expectations.
   - Recommended Odoo principle set (use by default if not specified):
     * No Core Modifications.
     * Upgrade‑Safe Customizations and Migration Readiness.
     * OCA Alignment and Module Packaging Conventions.
     * Security, Access Rights, and Record Rules.
     * Data Integrity, Accounting, and Localization Compliance.
     * UX Consistency, Translatability, and Accessibility.
     * Performance, Scalability, and Observability.
     * Testing Discipline, CI, and Code Quality.
     * Configuration over Customization when feasible.
     * Change Management and Documentation.

4. Consistency propagation checklist (convert prior checklist into active validations):
   - Read `/templates/plan-template.md` and ensure any "Constitution Check" or rules align with updated principles.
   - Read `/templates/spec-template.md` for scope/requirements alignment—update if constitution adds/removes mandatory sections or constraints.
   - Read `/templates/tasks-template.md` and ensure task categorization reflects new or removed principle-driven task types (e.g., observability, versioning, testing discipline).
   - Read each command file in `/templates/commands/*.md` (including this one) to verify no outdated references to non‑Odoo frameworks or agents remain; prefer Odoo terminology and practices.
   - Odoo-specific validations across templates (update or flag as TODO if missing):
     * Spec includes Odoo module structure expectations: `__manifest__.py`, `models/`, `views/`, `security/ir.model.access.csv`, record rules, `data/`, `demo/`, reports (QWeb), server actions, scheduled actions.
     * Plan details environments (Odoo 18.x target), deployment model (Odoo.sh/on‑prem/cloud), database lifecycle, module install order, and data migration approach.
     * Tasks cover Odoo categories: model/schema changes, views/QWeb, access rights and record rules, accounting/localization, integrations/connectors, automated tests, performance/monitoring, upgrades/migrations.
     * Replace any framework-specific placeholders (e.g., “Django”, “Rails”, “React/Next”) with Odoo equivalents (controllers/JSON‑RPC, OWL/QWeb, ORM/models).
   - Read any runtime guidance docs (e.g., `README.md`, `docs/quickstart.md`, or agent-specific guidance files if present). Update references to principles changed and include Odoo metadata (version, edition, deployment, module list, upgrade cadence).

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
