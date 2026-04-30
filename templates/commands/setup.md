---
description: "Initialize or update the InfraKit project configuration: project context, tagging standards, and resource registry."
argument-hint: "[optional: describe your project briefly]"
handoffs:
  - label: "Configure Coding Style"
    agent: "infrakit:setup-coding-style"
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

You are initializing or updating the InfraKit project configuration. Your task is to create or update two core configuration files that every other InfraKit command depends on:

1. `.infrakit/context.md` — Project context (cloud provider, architecture decisions, network topology, naming conventions, compliance)
2. `.infrakit/tagging-standard.md` — Tagging standards (required tags, tag formats, enforcement rules)

> **Note:** Coding style (`.infrakit/coding-style.md`) is configured separately via `/infrakit:setup-coding-style`. Run that command after this one completes.

**CRITICAL**: If any of these files already exist, load their current content first and offer the user a chance to update rather than replace.

---

## Phase 1: Check Existing Configuration

### 1.1 Scan for Existing Files

Check whether each configuration file exists:

| File | Path | Status |
|------|------|--------|
| Project Context | `.infrakit/context.md` | Check |
| Tagging Standard | `.infrakit/tagging-standard.md` | Check |
| Resource Registry | `.infrakit_tracks/tracks.md` | Check |

### 1.2 Report Current State

Present findings to the user:

> "**InfraKit Setup**
>
> | File | Status |
> |------|--------|
> | `.infrakit/context.md` | ✅ Exists / ❌ Missing |
> | `.infrakit/tagging-standard.md` | ✅ Exists / ❌ Missing |
> | `.infrakit_tracks/tracks.md` | ✅ Exists / ❌ Missing |
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
> - 'Terraform >= 1.6.0; S3 backend with DynamoDB locking; GitHub Actions for plan/apply; no direct terraform apply in prod'
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

## Phase 4: Update .infrakit/tagging-standard.md

`.infrakit/tagging-standard.md` was pre-populated from the IaC-specific template when you ran `infrakit init`. Your task here is to add project-specific required tags.

### 4.1 Read Existing File

Read `.infrakit/tagging-standard.md` and present its current content to the user.

### 4.2 Gather Project-Specific Tags

Ask the user:

> "Your `tagging-standard.md` is pre-configured with baseline required tags.
>
> What **project-specific** tags should every managed resource carry?
>
> Examples:
> - `cost-center` — governance owner, from `var.cost_center` / `spec.parameters.costCenter`
> - `team` — owning team, from `var.team` / `spec.parameters.teamName`
> - `project` — static value (e.g., `acme-platform`)
> - `environment` — target environment, from `var.environment` / `spec.parameters.environment`
>
> List your project-specific tags and their value sources (or press Enter to keep as-is):"

**WAIT** for response.

### 4.3 Update the File

Replace the `[REQUIRED_TAGS]` placeholder with the project-specific tags the user provided. Keep all other content from the pre-populated template intact.

**Present to user:**
> "I've updated `.infrakit/tagging-standard.md`. Please review:
>
> A) **Accept** — Looks good
> B) **Edit** — Make changes, say 'done' when ready
> C) **Regenerate** — Tell me what to change"

**WAIT** for response. **Loop until user accepts.**

---

## Phase 5: Initialize tracks.md

If `.infrakit_tracks/tracks.md` does not exist, create it:

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

## Phase 6: Completion

> "✅ **InfraKit setup complete!**
>
> **Files configured:**
> - `.infrakit/context.md` — Project context ✅
> - `.infrakit/tagging-standard.md` — Tagging standards ✅
> - `.infrakit_tracks/tracks.md` — Resource registry ✅
>
> **Required Next Step — Configure Coding Style:**
>
> Run `/infrakit:setup-coding-style` to define your IaC coding standards.
> This populates `.infrakit/coding-style.md`, which all code generation commands depend on.
>
> **Once coding style is configured, start building:**
> - **Crossplane**: Run `/infrakit:new_composition`
> - **Terraform**: Run `/infrakit:create_terraform_code`
> - Run `/infrakit:status` to see all track statuses"

---

## Error Handling

| Error | Action |
|-------|--------|
| `.infrakit/` directory missing | Create it automatically |
| User wants to skip a file | Skip and note in completion summary |
| User provides partial information | Use sensible defaults, mark TODOs |
