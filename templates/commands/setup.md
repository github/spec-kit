---
description: "Initialize or update the InfraKit project configuration: project context, coding style, and tagging constraints."
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

1. `.infrakit/context.md` — Project context (cloud provider, API groups, naming conventions, standards)
2. `.infrakit/coding-style.md` — Coding standards (tagging, connection secrets, security rules, patch patterns)
3. `.infrakit/tagging.md` — Tagging constraints (required tags, tag formats, enforcement rules)

**CRITICAL**: If any of these files already exist, load their current content first and offer the user a chance to update rather than replace.

---

## Phase 1: Check Existing Configuration

### 1.1 Scan for Existing Files

Check whether each configuration file exists:

| File | Path | Status |
|------|------|--------|
| Project Context | `.infrakit/context.md` | Check |
| Coding Style | `.infrakit/coding-style.md` | Check |
| Tagging Constraints | `.infrakit/tagging.md` | Check |
| Resource Registry | `.infrakit/tracks.md` | Check |

### 1.2 Report Current State

Present findings to the user:

> "**InfraKit Setup**
>
> | File | Status |
> |------|--------|
> | `.infrakit/context.md` | ✅ Exists / ❌ Missing |
> | `.infrakit/coding-style.md` | ✅ Exists / ❌ Missing |
> | `.infrakit/tagging.md` | ✅ Exists / ❌ Missing |
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

Ask these questions **one at a time**. Wait for each response before asking the next.

**Question 1: Project Name**
> "What is the name of this project/platform?
>
> Example: 'Platform Engineering', 'Cloud Infrastructure', 'DataOps Platform'"

**WAIT** for response.

**Question 2: Cloud Provider**
> "Which cloud provider(s) does this project use?
>
> A) AWS
> B) Azure
> C) GCP
> D) Multi-cloud (specify which)"

**WAIT** for response.

**Question 3: API Group**
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
> - kebab-case: `my-database`, `redis-cache`
> - camelCase: `myDatabase`, `redisCache`
> - With prefix: `platform-database`, `platform-redis`
>
> Describe your naming convention (or press Enter to use kebab-case):"

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
> - IAM/RBAC authentication required
> - TLS 1.2+ required for all connections
> - Secret rotation required
>
> Or describe your security standards:"

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
| Track Name | kebab-case with timestamp | `sql-instance-20260101-120000` |
| <custom_convention> | <format> | <example> |

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

## Organization Standards

- All resources must follow the naming conventions above
- All managed resources must include required tags (see tagging.md)
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

## Phase 4: Generate .infrakit/coding-style.md

Generate `.infrakit/coding-style.md`:

```markdown
# Coding Style Guide

## Overview

This document defines mandatory coding standards for all Crossplane compositions in this project. The Crossplane Engineer MUST follow these standards exactly.

---

## Pipeline Mode (MANDATORY)

All compositions MUST use Pipeline mode:

```yaml
spec:
  mode: Pipeline
  pipeline:
    - step: patch-and-transform
      functionRef:
        name: crossplane-contrib-function-patch-and-transform
```

**NEVER use Resources mode.** Pipeline mode is mandatory for all new compositions.

---

## Required Tagging

Every managed resource MUST include these tags/labels (see tagging.md for full requirements):

```yaml
patches:
  - type: FromCompositeFieldPath
    fromFieldPath: metadata.name
    toFieldPath: spec.forProvider.tags[crossplane.io/claim-name]
  - type: FromCompositeFieldPath
    fromFieldPath: metadata.namespace
    toFieldPath: spec.forProvider.tags[crossplane.io/claim-namespace]
  - type: FromCompositeFieldPath
    fromFieldPath: metadata.name
    toFieldPath: spec.forProvider.tags[managed-by]
    transforms:
      - type: string
        string:
          type: Format
          fmt: "crossplane"
```

---

## Provider Configuration

Every managed resource MUST include `providerConfigRef`:

```yaml
spec:
  providerConfigRef:
    name: default
```

**Never hardcode provider config names other than `default`** unless explicitly required by project context.

---

## Connection Secrets

All resources with network endpoints MUST publish connection details:

```yaml
writeConnectionSecretToRef:
  name: $(claim-name)-connection
  namespace: $(claim-namespace)
```

**Required connection secret keys** (for applicable resource types):

| Resource Type | Keys |
|---------------|------|
| Databases | `endpoint`, `port`, `username`, `password`, `database` |
| Caches | `endpoint`, `port` |
| Object Storage | `endpoint`, `bucket` |
| Message Queues | `endpoint`, `queue-url` |

---

## Security Rules

- **NEVER** hardcode secrets, passwords, or API keys in YAML
- **NEVER** set `publicNetworkAccess: Enabled` in production without explicit override
- **ALWAYS** enable encryption at rest for storage resources in staging/prod
- **ALWAYS** use `deletionPolicy: Delete` unless explicitly overridden

---

## Patch Patterns

### Input patch (Composite → Managed Resource)
```yaml
- type: FromCompositeFieldPath
  fromFieldPath: spec.parameters.<field>
  toFieldPath: spec.forProvider.<field>
```

### Output patch (Managed Resource → Composite Status)
```yaml
- type: ToCompositeFieldPath
  fromFieldPath: status.atProvider.<field>
  toFieldPath: status.<field>
```

### String format transform
```yaml
- type: FromCompositeFieldPath
  fromFieldPath: metadata.name
  toFieldPath: spec.forProvider.name
  transforms:
    - type: string
      string:
        type: Format
        fmt: "%s-<suffix>"
```

---

## File Structure

Every composition directory MUST contain:

| File | Description |
|------|-------------|
| `definition.yaml` | CompositeResourceDefinition (XRD) |
| `composition.yaml` | Composition with Pipeline mode |
| `claim.yaml` | Example claim with all parameters |
| `README.md` | Usage documentation |
```

**Present to user:**
> "I've generated `.infrakit/coding-style.md`. Please review:
>
> A) **Accept** — Looks good
> B) **Edit** — Make changes, say 'done' when ready
> C) **Regenerate** — Tell me what to change"

**WAIT** for response. **Loop until user accepts.**

---

## Phase 5: Generate .infrakit/tagging.md

Generate `.infrakit/tagging.md`:

```markdown
# Tagging Constraints

## Overview

This document defines mandatory tagging requirements for all cloud resources managed by Crossplane compositions in this project.

---

## Required Tags (ALL resources)

Every managed resource MUST include these tags:

| Tag Key | Value Source | Description |
|---------|-------------|-------------|
| `crossplane.io/claim-name` | `metadata.name` (from composite) | Name of the Claim |
| `crossplane.io/claim-namespace` | `metadata.namespace` (from composite) | Namespace of the Claim |
| `managed-by` | Static: `crossplane` | Identifies Crossplane-managed resources |

---

## Environment Tag

Resources supporting multiple environments MUST include:

| Tag Key | Allowed Values | Description |
|---------|---------------|-------------|
| `environment` | `dev`, `staging`, `prod` | Target environment |

---

## Provider-Specific Tag Field Paths

| Provider | Tag Field Path | Notes |
|----------|---------------|-------|
| **AWS** | `spec.forProvider.tags` | Map of key/value pairs |
| **Azure** | `spec.forProvider.tags` | Map of key/value pairs |
| **GCP** | `spec.forProvider.labels` | GCP uses labels not tags |

---

## Crossplane System Labels

In addition to cloud resource tags, all Crossplane objects MUST carry these labels in `metadata.labels`:

| Label | Value | Purpose |
|-------|-------|---------|
| `crossplane.io/composite` | Composite name | Links managed resource to XR |

This is set automatically by Crossplane. Do not manually override.

---

## Tagging Enforcement

The Crossplane Engineer MUST:
1. Add the required tag patches to **every** managed resource in every composition
2. Verify tags are present in the compliance check (Phase 2.5) before submitting for review
3. Never submit a composition without the required tags — this is a `HIGH` severity violation

---

## Validation

Run this check to confirm tags are applied:
```bash
crossplane render claim.yaml composition.yaml definition.yaml | grep -A5 "tags:"
```
```

**Present to user:**
> "I've generated `.infrakit/tagging.md`. Please review:
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
> - `.infrakit/tagging.md` — Tagging constraints ✅
> - `.infrakit/tracks.md` — Resource registry ✅
>
> **Next Steps:**
> - Run `/infrakit:new_composition` to create your first infrastructure resource
> - Run `/infrakit:status` to see all track statuses"

---

## Error Handling

| Error | Action |
|-------|--------|
| `.infrakit/` directory missing | Create it automatically |
| User wants to skip a file | Skip and note in completion summary |
| User provides partial information | Use sensible defaults, mark TODOs |
