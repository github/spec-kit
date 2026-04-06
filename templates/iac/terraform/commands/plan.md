---
description: "Generate a Terraform implementation plan (plan.md) for a track from its spec."
argument-hint: "<track-name>"
handoffs:
  - label: "Analyze Consistency"
    agent: "infrakit:analyze"
  - label: "Generate Tasks"
    agent: "infrakit:tasks"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** parse the track name from `$ARGUMENTS`. If not provided, ask:

> "Which track would you like to generate a plan for?
> Example: `database-20260101-120000`"

**WAIT** for response before continuing.

---

## System Directive

You are the **Terraform Engineer** generating a detailed implementation plan for an infrastructure track. The plan translates the approved spec into a concrete Terraform HCL implementation blueprint.

**You are generating plan.md — you are NOT writing code yet.**

Read `.infrakit/agent_personas/terraform_engineer.md` for detailed persona behavior (if present).

---

## Step 1: Setup Check

Verify required files exist:

| File | Path | Required |
|------|------|----------|
| Project Context | `.infrakit/context.md` | ✅ Yes |
| Coding Style | `.infrakit/coding-style.md` | ✅ Yes |
| Tagging | `.infrakit/tagging.md` | ✅ Yes |
| Spec | `.infrakit/tracks/<track-name>/spec.md` | ✅ Yes |

**If context.md, coding-style.md, or tagging.md is missing:**
> "❌ Project not fully initialized. Run `/infrakit:setup` first."
**HALT**

**If spec.md is missing:**
> "❌ `spec.md` not found. Run `/infrakit:create_terraform_code <track-name>` to create the spec."
**HALT**

---

## Step 2: Load Standards and Spec

Read the following files:

1. `.infrakit/context.md` — cloud provider defaults, naming conventions, workspace strategy
2. `.infrakit/coding-style.md` — Mandatory coding standards (naming, tagging, backend, security defaults)
3. `.infrakit/tagging.md` — Required tags for all resources
4. `.infrakit/tracks/<track-name>/spec.md` — Requirements, input variables, outputs, security

---

## Step 3: Research Provider Resource Arguments

**CRITICAL**: Never guess resource argument names or attribute paths.

For each resource required by the spec:

1. Identify the correct Terraform provider (e.g., `hashicorp/aws`, `hashicorp/azurerm`, `hashicorp/google`)
2. Look up the correct resource type and its arguments using:
   ```
   search_web("site:registry.terraform.io/providers/hashicorp/<provider>/latest/docs/resources/<resource_type>")
   ```
   Example: `search_web("site:registry.terraform.io hashicorp/aws aws_db_instance arguments")`
3. Verify the required and optional arguments for the resource type
4. Record the verified argument details in the plan

---

## Step 4: Design Input Variable Mapping

Map each spec input variable to a Terraform variable definition:

| Spec Variable | Variable Name | Type | Required | Default | Validation |
|---------------|---------------|------|----------|---------|------------|
| `<var>` | `var.<name>` | `<type>` | `<bool>` | `<default>` | `<rule if any>` |

Map each variable to the resource argument it controls:

| Variable | Resource | Argument Path |
|----------|----------|---------------|
| `var.<name>` | `<resource_type>.<name>` | `<argument>` |

---

## Step 5: Design Output Mapping

Map each spec output to the Terraform output value source:

| Spec Output | Output Name | Source Expression |
|-------------|-------------|-------------------|
| `<output>` | `<name>` | `<resource_type>.<name>.<attribute>` |

---

## Step 6: Design Tagging Strategy

Based on the cloud provider and `.infrakit/tagging.md`, define the tagging approach:

**For AWS** — use `default_tags` in the provider block (preferred) or per-resource `tags` map:

| Tag Key | Value Source | Notes |
|---------|-------------|-------|
| `managed-by` | `"terraform"` | Static — all resources |
| `<project-tag>` | `var.tags` (merged map) | From caller |

**For Azure** — use per-resource or resource group `tags = {}` map.

**For GCP** — use per-resource `labels = {}` map (GCP uses labels, not tags).

---

## Step 7: Write plan.md

Write to `.infrakit/tracks/<track-name>/plan.md`:

```markdown
# Implementation Plan: <Module Name>

## Summary
<Brief description of what will be built>

## Infrastructure Context

| Property | Value |
|----------|-------|
| **Track** | `<track-name>` |
| **Cloud Provider** | `<provider>` (from context.md) |
| **Module Directory** | `<module-directory>` |

## Tech Stack

| Component | Version |
|-----------|---------|
| Terraform | `>= <version>` |
| Provider | `hashicorp/<provider> ~> <version>` |

## File Structure

```
<module-directory>/
├── main.tf          # Resource definitions
├── variables.tf     # Input variable declarations
├── outputs.tf       # Output value declarations
├── versions.tf      # Required providers and Terraform version
└── README.md        # Usage documentation
```

## Input Variables Design

| Variable | Type | Required | Default | Description | Validation |
|----------|------|----------|---------|-------------|------------|
| `<var>` | `<type>` | `<bool>` | `<default>` | `<desc>` | `<rule>` |

## Resources to Provision

| # | Resource Type | Name | Arguments | Purpose |
|---|---------------|------|-----------|---------|
| 1 | `<resource_type>` | `<name>` | `<key args>` | `<purpose>` |

## Output Values Design

| Output | Source | Description |
|--------|--------|-------------|
| `<name>` | `<resource_type>.<name>.<attribute>` | `<desc>` |

## Tagging Strategy

<Describe tagging approach — provider-specific, required tags, variable merging>

## Implementation Phases

1. **versions.tf** — Declare required Terraform version and provider constraints
2. **variables.tf** — Declare all input variables with types, defaults, and validation
3. **main.tf** — Define all resources with proper arguments and tagging
4. **outputs.tf** — Declare all output values
5. **README.md** — Document usage, variables, and outputs

## Constraints from coding-style.md

- <Key constraint 1 from project coding style>
- <Key constraint 2>
- **Never** hardcode secrets, passwords, or API keys
- **Never** set public network access enabled without explicit variable override
- **Always** enable encryption at rest for storage resources

## Notes

### Known Challenges
- <any implementation challenges identified>

### Design Decisions
- <key decisions made during planning>
```

---

## Step 8: Feedback Loop

After writing plan.md:

> "I've generated the implementation plan.
>
> **File**: `.infrakit/tracks/<track-name>/plan.md`
>
> What would you like to do?
>
> A) **Regenerate** — Tell me what to change and I'll revise
> B) **Manual Changes** — Edit the file, say 'done' when ready
> C) **Proceed** — Plan looks good"

**WAIT** for response. Loop until user chooses C.

---

## Step 9: Next Actions

> "✅ Plan complete for `<track-name>`.
>
> **Next steps:**
> - Run `/infrakit:analyze <track-name>` to verify spec-plan consistency
> - Run `/infrakit:tasks <track-name>` to generate the implementation task list"

---

## Error Handling

| Error | Action |
|-------|--------|
| Setup files missing | Halt, direct to `/infrakit:setup` |
| spec.md missing | Halt, direct to `/infrakit:create_terraform_code` |
| Resource argument unknown | Use `search_web("site:registry.terraform.io hashicorp/...")` to look it up |
| plan.md already exists | Ask: overwrite or update? |
