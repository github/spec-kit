---
description: "Configure the Terraform coding style for this project by filling in the project-specific values in .infrakit/coding-style.md."
argument-hint: "[optional: describe any specific conventions to apply]"
handoffs:
  - label: "Create Terraform Code"
    agent: "infrakit:create_terraform_code"
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

You are configuring the Terraform coding style guide for this project. Your task is to gather project-specific conventions and fill in all `[PLACEHOLDER]` values in `.infrakit/coding-style.md`.

**CRITICAL**: Read `.infrakit/coding-style.md` before asking any questions. If placeholders are already filled in, present the current values and offer to update specific sections rather than regenerating from scratch.

---

## Phase 1: Prerequisites

### 1.1 Load Project Context

Read `.infrakit/context.md` and extract the following values (they will be used to fill placeholders without re-asking the user):

| Value | Source |
|-------|--------|
| `<project_name>` | **Project Name** row in Project Information table |
| `<cloud_provider>` | **Cloud Provider** row in Project Information table |
| `<environments>` | **Environments** row in Project Information table |
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

**Question 1: Terraform Version & Provider(s)**
> "Which Terraform version and provider(s) does this project use?
>
> Examples:
> - 'Terraform >= 1.6.0; hashicorp/aws ~> 5.0'
> - 'Terraform >= 1.5.0; hashicorp/azurerm ~> 3.0, hashicorp/random ~> 3.6'
>
> Specify the minimum Terraform version and your provider(s) with version constraints
> (or press Enter to use `>= 1.6, < 2.0` with provider defaults):"

**WAIT** for response. *(Fills: `[TERRAFORM_VERSION]`, `[PRIMARY_PROVIDER]`, `[PROVIDER_VERSIONS]`, `[TF_VERSION_CONSTRAINT]`, `[PROVIDER]`, `[PROVIDER_VERSION_CONSTRAINT]`)*

**Question 2: Backend & State Management**
> "What backend does this project use for Terraform state?
>
> Examples:
> - 'S3 backend with DynamoDB locking; bucket name parameterized per workspace'
> - 'Terraform Cloud / HCP Terraform — remote execution and state'
> - 'Azure Blob Storage backend'
> - 'GCS backend with a shared lock bucket'
>
> Describe your backend type and configuration (or press Enter to leave as TODO):"

**WAIT** for response. *(Fills: `[BACKEND_TYPE]`, `[BACKEND_CONFIGURATION]`)*

**Question 3: Module Directory Structure**
> "What is your module directory structure?
>
> Default structure:
> ```
> modules/
>   <resource>/
>     main.tf
>     variables.tf
>     outputs.tf
>     versions.tf
>     README.md
> environments/
>   dev/
>   staging/
>   prod/
> ```
>
> Describe any deviations (or press Enter to use the default):"

**WAIT** for response. *(Fills: `[PROJECT_FILE_STRUCTURE]`)*

**Question 4: Project Prefix & Naming Pattern**
> "What prefix and naming pattern should cloud resource names use?
>
> Examples:
> - Prefix `acme` with pattern `{prefix}-{resource}-{env}` → `acme-postgres-prod`
> - Prefix `myapp` with pattern `{prefix}-{name}-{env}` → `myapp-vpc-staging`
>
> Specify your project prefix (or press Enter to derive from the project name):"

**WAIT** for response. *(Fills: `[PROJECT_PREFIX]`)*

**Question 5: Terraform Version Policy**
> "What is your Terraform version policy?
>
> Examples:
> - 'Minimum supported >= 1.6; use latest stable patch; upgrade within 3 months of minor release'
> - 'Pinned to >= 1.6, < 2.0; no major version bumps without team review'
>
> Describe your policy (or press Enter to use `>= 1.6, < 2.0` with patch updates allowed):"

**WAIT** for response. *(Fills: `[TF_VERSION_POLICY]`)*

**Question 6: Default Tags Strategy**
> "How should required tags be applied across all resources?
>
> Examples:
> - 'AWS: `default_tags` block in the provider — avoids repeating tags on every resource'
> - 'All providers: `local.common_tags` merged into each resource's `tags` argument'
>
> Choose your strategy (or press Enter to use `default_tags` for AWS and `local.common_tags` for other providers):"

**WAIT** for response. *(Fills: `[DEFAULT_TAGS_STRATEGY]`)*

**Question 7: Project-Specific Tags**
> "What tags should all managed resources carry, beyond the baseline (`managed-by`, `environment`, `project`)?
>
> Examples:
> - `cost-center` — from `var.cost_center`
> - `team` — from `var.team`
> - `terraform-module` — from `path.module`
>
> List your tags and their value sources as `key — source` pairs (or press Enter to use the baseline only):"

**WAIT** for response. *(Fills: `[PROJECT_SPECIFIC_TAGS]`)*

**Question 8: Security Defaults**
> "What are your project-specific security defaults for Terraform resources?
>
> Examples:
> - `storage_encrypted = true` on all RDS/EBS/S3 regardless of environment
> - `publicly_accessible = false` always; override variable requires security team sign-off tracked in spec.md
> - `deletion_protection = true` for prod; false for dev/staging
> - `multi_az = true` required in prod for all RDS; not required in dev/staging
>
> Describe your security defaults (or press Enter to inherit from context.md security standards):"

**WAIT** for response. *(Fills: `[PROJECT_SECURITY_DEFAULTS]`)*

---

## Phase 3: Fill Placeholders in .infrakit/coding-style.md

Read `.infrakit/coding-style.md` and replace every `[PLACEHOLDER]` using the values gathered in Phase 2 and loaded from `.infrakit/context.md`:

| Placeholder | Source |
|-------------|--------|
| `[PROJECT_NAME]` | `<project_name>` from context.md |
| `[TERRAFORM_VERSION]` | Q1 — version constraint (e.g., `>= 1.6.0`) |
| `[PRIMARY_PROVIDER]` | Q1 — primary cloud provider (e.g., `AWS`) |
| `[PROVIDER_VERSIONS]` | Q1 — full provider list with version constraints |
| `[PROJECT_FILE_STRUCTURE]` | Q3 (or default structure) |
| `[PROJECT_PREFIX]` | Q4 |
| `[TF_VERSION_POLICY]` | Q5 |
| `[TF_VERSION_CONSTRAINT]` | Q1 — constraint string (e.g., `>= 1.6, < 2.0`) |
| `[PROVIDER]` | Q1 — primary provider identifier (e.g., `aws`) |
| `[PROVIDER_VERSION_CONSTRAINT]` | Q1 — provider constraint (e.g., `~> 5.0`) |
| `[DEFAULT_TAGS_STRATEGY]` | Q6 |
| `[PROJECT_SPECIFIC_TAGS]` | Q7 — formatted as markdown table rows |
| `[BACKEND_TYPE]` | Q2 — backend type identifier (e.g., `s3`, `gcs`, `azurerm`) |
| `[BACKEND_CONFIGURATION]` | Q2 — backend-specific configuration block |
| `[PROJECT_SECURITY_DEFAULTS]` | Q8 |

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

> "✅ **Terraform coding style configured!**
>
> **File updated:**
> - `.infrakit/coding-style.md` — Terraform coding standards ✅
>
> **Next Steps:**
> - Run `/infrakit:create_terraform_code` to create your first module
> - Run `/infrakit:status` to see all track statuses"

---

## Error Handling

| Error | Action |
|-------|--------|
| `.infrakit/context.md` missing | Stop — direct user to run `/infrakit:setup` first |
| `.infrakit/coding-style.md` missing | Stop — direct user to run `infrakit init` to initialize the project |
| User skips a question | Leave the corresponding `[PLACEHOLDER]` as-is and note it in the completion summary |
| User provides partial information | Use sensible defaults for derivable values; mark the rest as TODOs |
