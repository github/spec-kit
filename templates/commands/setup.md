---
description: "Initialize or update the InfraKit project configuration: project context, coding style, and tagging standards."
argument-hint: "[optional: describe your project briefly]"
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

You are initializing or updating the InfraKit project configuration. Your task is to create or update three configuration files that every other InfraKit command depends on:

1. `.infrakit/context.md` — Project context (cloud provider, architecture decisions, network topology, naming conventions, compliance)
2. `.infrakit/coding-style.md` — Coding standards (IaC tool versions, tagging, connection secrets, security rules, patch patterns)
3. `.infrakit/tagging-standard.md` — Tagging standards (required tags, tag formats, enforcement rules)

**CRITICAL**: If any of these files already exist, load their current content first and offer the user a chance to update rather than replace.

---

## Phase 1: Check Existing Configuration

### 1.1 Scan for Existing Files

Check whether each configuration file exists:

| File | Path | Status |
|------|------|--------|
| Project Context | `.infrakit/context.md` | Check |
| Coding Style | `.infrakit/coding-style.md` | Check |
| Tagging Constraints | `.infrakit/tagging-standard.md` | Check |
| Resource Registry | `.infrakit/tracks.md` | Check |

### 1.2 Report Current State

Present findings to the user:

> "**InfraKit Setup**
>
> | File | Status |
> |------|--------|
> | `.infrakit/context.md` | ✅ Exists / ❌ Missing |
> | `.infrakit/coding-style.md` | ✅ Exists / ❌ Missing |
> | `.infrakit/tagging-standard.md` | ✅ Exists / ❌ Missing |
> | `.infrakit/tracks.md` | ✅ Exists / ❌ Missing |
>
> What would you like to do?
>
> A) **Full Setup** — Create/update all missing files interactively
> B) **Update Specific File** — Tell me which file to update
> C) **Just Create Missing** — Create only what's missing with sensible defaults"

**WAIT** for user response before continuing.

---

## Phase 2: Gather Project Information

**Trigger**: User chooses A (Full Setup) or a file is missing.

### 2.0 Detect IaC Tool

Read `.infrakit/config.yaml` to determine which IaC tool this project uses (e.g., `iac: crossplane` or `iac: terraform`). Store this as `<iac-tool>` for use in later phases.

Ask these questions **one at a time**. Wait for each response before asking the next.

**Question 1: Project Name**
> "What is the name of this project/platform?
>
> Example: 'Acme Platform Engineering', 'Cloud Infrastructure', 'DataOps Platform'"

**WAIT** for response.

**Question 2: Cloud Provider**
> "Which cloud provider(s) does this project use?
>
> A) AWS
> B) Azure
> C) GCP
> D) Multi-cloud (specify which)"

**WAIT** for response.

**Question 3: API Group** *(Crossplane projects only — skip for Terraform)*

If `<iac-tool>` is **crossplane**, ask:
> "What is the base API group for your Crossplane resources?
>
> Example: `platform.example.com`, `infra.mycompany.io`
>
> This will be used as the prefix for all XRD API groups."

**WAIT** for response.

**Question 4: Naming Conventions**
> "What naming conventions should resources follow?
>
> Examples:
> - kebab-case with env prefix: `prod-payments-rds-primary`, `dev-data-s3-raw`
> - kebab-case simple: `my-database`, `redis-cache`
> - With team prefix: `payments-database`, `data-redis`
>
> Describe your naming convention (or press Enter to use `{env}-{team}-{resource-type}`):"

**WAIT** for response.

**Question 5: Environments**
> "What environments does this project support?
>
> A) dev, staging, prod (standard)
> B) dev, qa, staging, prod (extended)
> C) Just prod
> D) Custom (specify)"

**WAIT** for response.

**Question 6: Security Defaults**
> "What are your default security requirements?
>
> Select all that apply:
> - Encryption at rest required for all storage
> - Private networking required in production
> - IAM/RBAC authentication required (no long-lived credentials)
> - TLS 1.2+ required for all connections
> - Secret rotation required
>
> Or describe your security standards:"

**WAIT** for response.

**Question 7: Architecture Decisions**
> "What IaC and GitOps tooling decisions has this project made?
>
> Examples:
> - 'Crossplane v1.15.2 with function-go-template; ArgoCD for GitOps from main branch; no direct kubectl apply in prod'
> - 'Crossplane v1.14 with function-patch-and-transform; Flux CD; state in EKS etcd with Velero backups to S3'
>
> Describe your IaC tool version, primary pipeline function, GitOps workflow, and state management strategy (or press Enter to leave as TODO):"

**WAIT** for response.

**Question 8: Network Topology**
> "What is your network topology and account structure?
>
> Examples:
> - 'Hub-and-spoke: Transit Gateway in shared-services account, per-env VPCs (dev 10.10.0.0/16, staging 10.11.0.0/16, prod 10.12.0.0/16)'
> - 'Single AWS account with env-based subnets; flat VPC 10.0.0.0/8'
> - 'Multi-region: primary us-east-1, DR in us-west-2; prod private subnets only'
>
> Describe your VPC/subnet strategy, account structure, and connectivity model (or press Enter to leave as TODO):"

**WAIT** for response.

**Question 9: Compliance Requirements**
> "What compliance frameworks apply to this project?
>
> Examples:
> - 'SOC 2 Type II — CloudTrail logging on all data stores, quarterly access reviews'
> - 'PCI-DSS — payments workloads on isolated node group with network policies'
> - 'HIPAA — PHI must be encrypted at rest and in transit; specific AWS regions only'
> - 'None'
>
> List your compliance frameworks and key requirements (or press Enter to skip):"

**WAIT** for response.

**Question 10: DR & HA Requirements**
> "What are your Disaster Recovery and High Availability requirements?
>
> Examples:
> - 'Prod: RTO 4h / RPO 1h; Multi-AZ required for all RDS and ElastiCache; no DR requirement for dev/staging'
> - '99.9% availability SLO in prod; cross-region DR to us-west-2 for prod databases'
> - 'Single-region, best-effort only'
>
> Describe your DR targets, HA requirements, and availability SLOs (or press Enter to leave as TODO):"

**WAIT** for response.

---

## Phase 3: Generate .infrakit/context.md

Based on the gathered information, generate `.infrakit/context.md`:

```markdown
# Project Context

## Project Information

| Property | Value |
|----------|-------|
| **Project Name** | <project_name> |
| **Cloud Provider** | <provider> |
| **Base API Group** | <api_group> |
| **Environments** | <environments> |
| **Last Updated** | <YYYY-MM-DD> |

---

## Naming Conventions

| Resource Type | Convention | Example |
|---------------|------------|---------|
| XRD Kind | PascalCase, prefixed with X | `XSQLInstance`, `XRedisCache` |
| Claim Kind | PascalCase (no X prefix) | `SQLInstance`, `RedisCache` |
| Composition Name | kebab-case | `sql-instance-aws` |
| Cloud Resource | <custom_convention> | <example> |
| Track Name | kebab-case with timestamp | `sql-instance-20260101-120000` |

---

## API Groups

| Group | Purpose | Example |
|-------|---------|---------|
| `<api_group>` | Base group for all compositions | `database.<api_group>/v1alpha1` |

---

## Cloud Provider Defaults

**Provider**: <provider>

| Setting | Default Value |
|---------|---------------|
| Default Region | <region> |
| Provider Package | <package> |
| Provider Config Name | `default` |

---

## Security Standards

<security_requirements listed as bullet points>

---

## Network Architecture

**Topology**: <network_topology_from_Q8>

**Account Structure**:
<account_structure>

**VPC Strategy**: <vpc_strategy>

**Connectivity**: <connectivity_model>

---

## Compliance

<compliance_frameworks_from_Q9 as bullet list — omit section if none>

---

## DR & HA

| Requirement | Production | Staging | Dev |
|-------------|------------|---------|-----|
| RTO | <prod_rto> | <staging_rto> | N/A |
| RPO | <prod_rpo> | <staging_rpo> | N/A |
| HA | <prod_ha> | <staging_ha> | None |

**Availability SLOs**: <slo_targets>

---

## Architecture Decisions

<architecture_decisions_from_Q7 as bullet list>

---

## Organization Standards

- All resources must follow the naming conventions above
- All managed resources must include required tags (see `.infrakit/tagging-standard.md`)
- All production resources must meet security requirements above
- Connection secrets must be published for all resources that have endpoints
```

**Present to user:**
> "I've generated `.infrakit/context.md`. Please review:
>
> What would you like to do?
>
> A) **Accept** — Looks good
> B) **Edit** — Make changes, say 'done' when ready
> C) **Regenerate** — Tell me what to change"

**WAIT** for response. **Loop until user accepts.**

---

## Phase 3.5: Transition to Coding Style

Once the user accepts `.infrakit/context.md`, display this message before continuing:

> "Your project context is complete. ✅
>
> Now let's configure your IaC coding style — this defines the standards all engineers
> on this project must follow when generating infrastructure code. I have a few quick
> questions about your project-specific conventions before updating
> `.infrakit/coding-style.md`."

**WAIT** for acknowledgment or proceed after displaying.

---

## Phase 3.6: Gather Coding Style Information

The questions to ask depend on the IaC tool detected in Phase 2.0.

Ask these questions **one at a time**. Wait for each response before asking the next.

### If `<iac-tool>` is **crossplane**:

**Coding Style Q1: Crossplane Version & Functions**
> "Which Crossplane version and pipeline functions does this project use?
>
> Examples:
> - 'Crossplane v1.15.2; function-go-template v0.7.0 (prefer source: Inline)'
> - 'Crossplane v1.14; function-patch-and-transform only'
>
> Specify the Crossplane version and your preferred pipeline function (or press Enter to use defaults):"

**WAIT** for response.

**Coding Style Q2: File Organization**
> "What is your project's directory structure for Crossplane resources?
>
> Default structure:
>
>     apis/<group>/<version>/
>     compositions/
>     examples/<kind>/
>
> Describe any deviations from the default structure (or press Enter to use the default):"

**WAIT** for response.

**Coding Style Q3: Project-Specific Tags**
> "Beyond the required Crossplane tags (`claim-name`, `claim-namespace`, `managed-by`),
> what additional tags should all managed resources carry?
>
> Examples:
> - `cost-center` — from `spec.parameters.costCenter`
> - `team` — from `spec.parameters.teamName`
> - `project` — static value (e.g., `acme-platform`)
> - `environment` — from `spec.parameters.environment`
>
> List your project-specific tags and their sources (or press Enter to skip):"

**WAIT** for response.

**Coding Style Q4: Security Defaults**
> "What are your project-specific security defaults for Crossplane managed resources?
>
> Examples:
> - `storageEncrypted: true` always (even in dev)
> - `publiclyAccessible: false` always, override requires security team approval
> - `deletionProtection: true` in prod, false elsewhere
> - `multiAZ: true` required in prod for databases and caches
>
> Describe your security defaults (or press Enter to use the baseline from context.md):"

**WAIT** for response.

### If `<iac-tool>` is **terraform**:

**Coding Style Q1: Terraform Version & Providers**
> "Which Terraform version and provider(s) does this project use?
>
> Examples:
> - 'Terraform >= 1.6.0; hashicorp/aws ~> 5.0'
> - 'Terraform >= 1.5.0; hashicorp/azurerm ~> 3.0, hashicorp/random ~> 3.6'
>
> Specify the minimum Terraform version and your provider(s) with version constraints (or press Enter to use defaults):"

**WAIT** for response.

**Coding Style Q2: Backend & State Management**
> "What backend does this project use for Terraform state?
>
> Examples:
> - 'S3 backend with DynamoDB locking (bucket name parameterized per workspace)'
> - 'Terraform Cloud / HCP Terraform — remote execution'
> - 'Azure Blob Storage backend'
>
> Describe your backend and state strategy (or press Enter to leave as TODO):"

**WAIT** for response.

**Coding Style Q3: Project-Specific Tags**
> "What tags should all managed resources carry?
>
> Examples:
> - `managed-by = "terraform"` (required)
> - `cost-center` — from `var.cost_center`
> - `team` — from `var.team`
> - `environment` — from `var.environment`
>
> List your required tags and their value sources (or press Enter to use `managed-by` only):"

**WAIT** for response.

**Coding Style Q4: Security Defaults**
> "What are your project-specific security defaults for Terraform resources?
>
> Examples:
> - `encrypted = true` always for all EBS/RDS/S3
> - Public access variables must default to `false`
> - `deletion_protection = true` for databases in prod
> - `multi_az = true` required in prod
>
> Describe your security defaults (or press Enter to use the baseline from context.md):"

**WAIT** for response.

---

## Phase 4: Update .infrakit/coding-style.md

`.infrakit/coding-style.md` was pre-populated from the IaC-specific template when you ran `infrakit init`. Your task here is to fill in the project-specific `[PLACEHOLDER]` values using the information gathered in Phase 2 and Phase 3.6.

### 4.1 Read Existing File

Read `.infrakit/coding-style.md` and identify all `[PLACEHOLDER]` sections (e.g., `[PROJECT_NAME]`, `[CROSSPLANE_VERSION]`, `[TERRAFORM_VERSION]`, `[REQUIRED_TAGS]`, `[SECURITY_DEFAULTS]`, etc.).

### 4.2 Fill Placeholders

Replace each `[PLACEHOLDER]` with the appropriate value from Phase 2 and Phase 3.6 answers:

- `[PROJECT_NAME]` → project name from Q1
- For **Crossplane**: `[CROSSPLANE_VERSION]` → from CS Q1; `[PRIMARY_FUNCTION]` → from CS Q1; `[FILE_STRUCTURE]` → from CS Q2; `[REQUIRED_TAGS]` → from CS Q3; `[SECURITY_DEFAULTS]` → from CS Q4
- For **Terraform**: `[TERRAFORM_VERSION]` → from CS Q1; `[PROVIDER_VERSIONS]` → from CS Q1; `[BACKEND_CONFIG]` → from CS Q2; `[REQUIRED_TAGS]` → from CS Q3; `[SECURITY_DEFAULTS]` → from CS Q4

Keep all non-placeholder content intact.

**Present to user:**
> "I've updated `.infrakit/coding-style.md`. Please review:
>
> A) **Accept** — Looks good
> B) **Edit** — Make changes, say 'done' when ready
> C) **Regenerate** — Tell me what to change"

**WAIT** for response. **Loop until user accepts.**

---

## Phase 5: Update .infrakit/tagging-standard.md

`.infrakit/tagging-standard.md` was pre-populated from the IaC-specific template when you ran `infrakit init`. Your task here is to add project-specific required tags.

### 5.1 Read Existing File

Read `.infrakit/tagging-standard.md` and present its current content to the user.

### 5.2 Gather Project-Specific Tags

Ask the user:

> "Your `tagging-standard.md` is pre-configured with baseline required tags.
>
> What **project-specific** tags should every managed resource carry?
>
> Examples:
> - `cost-center` — from `var.cost_center` / `spec.parameters.costCenter`
> - `team` — from `var.team` / `spec.parameters.teamName`
> - `project` — static value (e.g., `acme-platform`)
> - `environment` — from `var.environment` / `spec.parameters.environment`
>
> List your project-specific tags and their value sources (or press Enter to keep as-is):"

**WAIT** for response.

### 5.3 Update the File

Replace the `[REQUIRED_TAGS]` placeholder with the project-specific tags the user provided. Keep all other content from the pre-populated template intact.

**Present to user:**
> "I've updated `.infrakit/tagging-standard.md`. Please review:
>
> A) **Accept** — Looks good
> B) **Edit** — Make changes, say 'done' when ready
> C) **Regenerate** — Tell me what to change"

**WAIT** for response. **Loop until user accepts.**

---

## Phase 6: Initialize tracks.md

If `.infrakit/tracks.md` does not exist, create it:

```markdown
# Infrastructure Resource Registry

Track all infrastructure compositions and their current status.

## Status Reference

| Symbol | Meaning |
|--------|---------|
| 🔵 `initializing` | Track created, spec in progress |
| 📝 `spec-generated` | Spec confirmed, ready for plan |
| 📋 `planned` | Plan generated, ready for implementation |
| ⚙️ `in-progress` | Implementation underway |
| ✅ `done` | Implementation complete and reviewed |
| ❌ `blocked` | Blocked, needs attention |

---

## Tracks

| Track | Type | Directory | Status | Created |
|-------|------|-----------|--------|---------|
| (none yet) | — | — | — | — |
```

---

## Phase 7: Completion

> "✅ **InfraKit setup complete!**
>
> **Files configured:**
> - `.infrakit/context.md` — Project context ✅
> - `.infrakit/coding-style.md` — Coding standards ✅
> - `.infrakit/tagging-standard.md` — Tagging standards ✅
> - `.infrakit/tracks.md` — Resource registry ✅
>
> **Next Steps:**
> - **Crossplane**: Run `/infrakit:new_composition` to create your first infrastructure resource
> - **Terraform**: Run `/infrakit:create_terraform_code` to create your first module
> - Run `/infrakit:status` to see all track statuses"

---

## Error Handling

| Error | Action |
|-------|--------|
| `.infrakit/` directory missing | Create it automatically |
| User wants to skip a file | Skip and note in completion summary |
| User provides partial information | Use sensible defaults, mark TODOs |
