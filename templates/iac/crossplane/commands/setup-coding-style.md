---
description: "Configure the Crossplane coding style for this project by filling in the project-specific values in .infrakit/coding-style.md."
argument-hint: "[optional: describe any specific conventions to apply]"
handoffs:
  - label: "Create New Composition"
    agent: "infrakit:new_composition"
  - label: "Check Status"
    agent: "infrakit:status"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

---

## System Directive

You are configuring the Crossplane coding style guide for this project. Your task is to gather project-specific conventions and fill in all `[PLACEHOLDER]` values in `.infrakit/coding-style.md`.

**CRITICAL**: Read `.infrakit/coding-style.md` before asking any questions. If placeholders are already filled in, present the current values and offer to update specific sections rather than regenerating from scratch.

---

## Phase 1: Prerequisites

### 1.1 Load Project Context

Read `.infrakit/context.md` and extract the following values (they will be used to fill placeholders without re-asking the user):

| Value | Source |
|-------|--------|
| `<project_name>` | **Project Name** row in Project Information table |
| `<api_group>` | **Base API Group** row in Project Information table |
| `<environments>` | **Environments** row in Project Information table |
| `<cloud_provider>` | **Cloud Provider** row in Project Information table |
| `<naming_conventions>` | Naming Conventions table |

If `.infrakit/context.md` is missing, stop and tell the user:

> "`.infrakit/context.md` is required before configuring coding style.
> Please run `/infrakit:setup` first."

### 1.2 Check Existing Coding Style File

Read `.infrakit/coding-style.md`.

- **File has `[PLACEHOLDER]` values remaining**: Proceed to Phase 2 to gather information and fill them in.
- **File is fully populated**: Present a summary of current values and ask:
  > "Your `.infrakit/coding-style.md` is already configured. Would you like to update any section?
  >
  > A) **Update specific section** — Tell me which one
  > B) **Review all values** — Walk through each setting
  > C) **No changes needed** — Exit"
  **WAIT** for response before continuing.
- **File missing**: Tell the user:
  > "`.infrakit/coding-style.md` not found. Please run `infrakit init` to initialize the project first."
  **STOP.**

---

## Phase 2: Gather Coding Style Information

Ask these questions **one at a time**. Wait for each response before asking the next.

**Question 1: Crossplane Version & Pipeline Function**
> "Which Crossplane version and pipeline function does this project use?
>
> Examples:
> - 'Crossplane v1.15.2; function-go-template v0.7.0 (source: Inline preferred)'
> - 'Crossplane v1.14; function-patch-and-transform only'
>
> Specify the Crossplane version and preferred pipeline function (or press Enter for defaults):"

**WAIT** for response. *(Fills: `[CROSSPLANE_VERSION]`, `[PRIMARY_FUNCTION]`, `[PREFERRED_FUNCTION]`)*

**Question 2: Provider Packages**
> "Which Crossplane provider packages does this project use?
>
> Examples:
> - `upbound/provider-aws-rds v1.2.0, upbound/provider-aws-s3 v1.2.0`
> - `upbound/provider-azure-sql v1.0.0, upbound/provider-azure-storage v1.0.0`
>
> List your provider packages and versions (or press Enter to leave as TODO):"

**WAIT** for response. *(Fills: `[PROVIDER_PACKAGES]`)*

**Question 3: Directory Structure**
> "What is your project's directory structure for Crossplane resources?
>
> Default structure:
> ```
> apis/<group>/<version>/
> compositions/
> examples/<kind>/
> ```
>
> Describe any deviations (or press Enter to use the default):"

**WAIT** for response. *(Fills: `[PROJECT_FILE_STRUCTURE]`)*

**Question 4: API Versioning Policy**
> "What is your API versioning policy for XRD API versions?
>
> Default progression:
> - `v1alpha1` — Experimental; internal use only, no compatibility guarantees
> - `v1beta1` — Stable API; minor backward-compatible changes allowed; announced to consumers
> - `v1` — Production stable; no breaking changes without a migration plan
>
> Press Enter to use this policy, or describe your own:"

**WAIT** for response. *(Fills: `[V1ALPHA1_POLICY]`, `[V1BETA1_POLICY]`, `[V1_POLICY]`)*

**Question 5: Deletion Policy & Management Policy**
> "What are your default deletion and management policies for managed resources?
>
> **Deletion Policy** (what happens to cloud resources when the XR is deleted):
> - `Delete` *(default)* — managed resource is deleted with the XR
> - `Orphan` — managed resource is kept; use only for stateful prod resources where data loss is unacceptable; requires justification comment in YAML
>
> **Management Policy** (what Crossplane lifecycle operations to perform):
> - Full lifecycle — Crossplane manages create, read, update, delete *(default)*
> - Observe-only — for resources imported from pre-existing infrastructure
>
> Describe your defaults (or press Enter for `Delete` / Full lifecycle):"

**WAIT** for response. *(Fills: `[DELETION_POLICY_DEFAULT]`, `[PROJECT_MANAGEMENT_POLICY]`)*

**Question 6: OpenAPI Validation Approach**
> "What OpenAPI validation approach do you use in XRD schemas?
>
> Examples:
> - 'Use enum constraints on all environment fields; pattern constraints on name fields (`^[a-z][a-z0-9-]*$`); mark all required fields as required'
> - 'Minimal validation — only type constraints; no enums or patterns'
>
> Describe your validation approach (or press Enter to use the standard approach):"

**WAIT** for response. *(Fills: `[PROJECT_VALIDATION_APPROACH]`)*

**Question 7: Project-Specific Tags**
> "Beyond the required Crossplane tags (`claim-name`, `claim-namespace`, `managed-by`),
> what additional tags should all managed resources carry?
>
> Examples:
> - `environment` — from `spec.parameters.environment`
> - `cost-center` — from `spec.parameters.costCenter`
> - `team` — from `spec.parameters.teamName`
> - `project` — static value (e.g., `acme-platform`)
>
> List your tags and their sources as `key — source` pairs (or press Enter to skip):"

**WAIT** for response. *(Fills: `[PROJECT_SPECIFIC_TAGS]`)*

**Question 8: Connection Secret Naming & Keys**
> "What naming pattern and additional keys should connection secrets use?
>
> **Naming pattern** examples:
> - `{claim-name}-{resource-type}-conn` → `my-db-postgres-conn` *(default)*
> - `{claim-name}-conn` → `my-db-conn`
>
> **Additional keys** beyond the standard set (endpoint, port, username, password):
> - e.g., 'All database connections must also include `db-name` and `ssl-mode`'
> - Or press Enter for no additional keys
>
> Describe your naming pattern and any extra keys:"

**WAIT** for response. *(Fills: `[CONNECTION_SECRET_NAME_PATTERN]`, `[PROJECT_CONNECTION_SECRET_KEYS]`)*

**Question 9: Security Defaults**
> "What are your project-specific security defaults for managed resources?
>
> Examples:
> - `storageEncrypted: true` on all RDS instances regardless of environment
> - `publiclyAccessible: false` always; override requires security team approval (tracked as a GitHub issue)
> - `deletionProtection: true` in prod, false in dev/staging
> - `multiAZ: true` required in prod for all databases and caches
>
> Describe your security defaults (or press Enter to inherit from context.md security standards):"

**WAIT** for response. *(Fills: `[PROJECT_SECURITY_DEFAULTS]`)*

---

## Phase 3: Fill Placeholders in .infrakit/coding-style.md

Read `.infrakit/coding-style.md` and replace every `[PLACEHOLDER]` using the values gathered in Phase 2 and loaded from `.infrakit/context.md`:

| Placeholder | Source |
|-------------|--------|
| `[PROJECT_NAME]` | `<project_name>` from context.md |
| `[CROSSPLANE_VERSION]` | Q1 |
| `[PRIMARY_FUNCTION]` | Q1 |
| `[PROVIDER_PACKAGES]` | Q2 |
| `[PROJECT_FILE_STRUCTURE]` | Q3 (or default structure) |
| `[BASE_API_GROUP]` | `<api_group>` from context.md |
| `[XRD_KIND_EXAMPLE]` | Derive from `<naming_conventions>` in context.md (e.g., `XPostgreSQLInstance`) |
| `[CLAIM_KIND_EXAMPLE]` | Derive from `<naming_conventions>` in context.md (e.g., `PostgreSQLInstance`) |
| `[COMPOSITION_NAME_PATTERN]` | Derive from context.md naming conventions (standard: `{resource}-{provider}`) |
| `[COMPOSITION_NAME_EXAMPLE]` | Derive from context.md (e.g., `postgres-aws`) |
| `[V1ALPHA1_POLICY]` | Q4 |
| `[V1BETA1_POLICY]` | Q4 |
| `[V1_POLICY]` | Q4 |
| `[PREFERRED_FUNCTION]` | Q1 |
| `[PROJECT_VALIDATION_APPROACH]` | Q6 |
| `[DELETION_POLICY_DEFAULT]` | Q5 |
| `[PROJECT_MANAGEMENT_POLICY]` | Q5 |
| `[PROJECT_SPECIFIC_TAGS]` | Q7 — formatted as markdown table rows |
| `[CONNECTION_SECRET_NAME_PATTERN]` | Q8 |
| `[PROJECT_CONNECTION_SECRET_KEYS]` | Q8 |
| `[PROJECT_SECURITY_DEFAULTS]` | Q9 |

Keep all non-placeholder content intact — the non-negotiable rules, code examples, and provider-specific reference patterns must not be modified.

**Present to user:**
> "I've updated `.infrakit/coding-style.md`. Please review:
>
> A) **Accept** — Looks good
> B) **Edit** — Make changes, say 'done' when ready
> C) **Regenerate** — Tell me what to change"

**WAIT** for response. **Loop until user accepts.**

---

## Phase 4: Completion

> "✅ **Crossplane coding style configured!**
>
> **File updated:**
> - `.infrakit/coding-style.md` — Crossplane coding standards ✅
>
> **Next Steps:**
> - Run `/infrakit:new_composition` to create your first infrastructure resource
> - Run `/infrakit:status` to see all track statuses"

---

## Error Handling

| Error | Action |
|-------|--------|
| `.infrakit/context.md` missing | Stop — direct user to run `/infrakit:setup` first |
| `.infrakit/coding-style.md` missing | Stop — direct user to run `infrakit init` to initialize the project |
| User skips a question | Leave the corresponding `[PLACEHOLDER]` as-is and note it in the completion summary |
| User provides partial information | Use sensible defaults for derivable values; mark the rest as TODOs |
