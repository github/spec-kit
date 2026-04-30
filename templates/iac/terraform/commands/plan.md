---
description: "Generate a Terraform implementation plan (plan.md) and task list (tasks.md) for a track from its spec."
argument-hint: "<track-name>"
handoffs:
  - label: "Analyze Consistency"
    agent: "infrakit:analyze"
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
| Tagging | `.infrakit/tagging-standard.md` | ✅ Yes |
| Spec | `.infrakit_tracks/tracks/<track-name>/spec.md` | ✅ Yes |

**If context.md, coding-style.md, or tagging-standard.md is missing:**
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
3. `.infrakit/tagging-standard.md` — Required tags for all resources
4. `.infrakit_tracks/tracks/<track-name>/spec.md` — Requirements, input variables, outputs, security

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

Based on the cloud provider and `.infrakit/tagging-standard.md`, define the tagging approach:

**For AWS** — use `default_tags` in the provider block (preferred) or per-resource `tags` map:

| Tag Key | Value Source | Notes |
|---------|-------------|-------|
| `managed-by` | `"terraform"` | Static — all resources |
| `<project-tag>` | `var.tags` (merged map) | From caller |

**For Azure** — use per-resource or resource group `tags = {}` map.

**For GCP** — use per-resource `labels = {}` map (GCP uses labels, not tags).

---

## Step 7: Write plan.md

Write to `.infrakit_tracks/tracks/<track-name>/plan.md`:

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
> **File**: `.infrakit_tracks/tracks/<track-name>/plan.md`
>
> What would you like to do?
>
> A) **Regenerate** — Tell me what to change and I'll revise
> B) **Manual Changes** — Edit the file, say 'done' when ready
> C) **Proceed** — Generate task list and mark track ready"

**WAIT** for response. Loop until user chooses C.

---

## Step 9: Auto-Generate tasks.md

After the user accepts the plan, expand the Implementation Phases from plan.md into granular checkbox tasks.

Write to `.infrakit_tracks/tracks/<track-name>/tasks.md`:

```markdown
# Implementation Tasks: <Module Name>

**Track**: `<track-name>`
**Generated**: <YYYY-MM-DD>
**Source Plan**: `.infrakit_tracks/tracks/<track-name>/plan.md`

## Phase 1: versions.tf
- [ ] T1.1: Write `terraform {}` block with version constraint from plan.md
- [ ] T1.2: Write `required_providers {}` block with provider source and version constraint from plan.md

## Phase 2: variables.tf
<one task per variable from the Input Variables Design table in plan.md:>
- [ ] T2.1: Declare variable `<var_name>` (type: `<type>`, required: <yes/no>, default: `<default>`)
- [ ] T2.N: ...

## Phase 3: main.tf
- [ ] T3.1: Write provider block with `default_tags` / labels (per plan.md Tagging Strategy)
<one task per resource from the Resources to Provision table in plan.md:>
- [ ] T3.2: Write `<resource_type>` `<name>` resource block
- [ ] T3.N: ...

## Phase 4: outputs.tf
<one task per output from the Output Values Design table in plan.md:>
- [ ] T4.1: Declare output `<output_name>` sourced from `<resource_type>.<name>.<attribute>`
- [ ] T4.N: ...

## Phase 5: README.md
- [ ] T5.1: Document all input variables in a table (name, type, required, default, description)
- [ ] T5.2: Document all output values in a table (name, description)
- [ ] T5.3: Add a usage example showing the module call with all required variables
```

**Expand dynamically**: use the actual variable names, resource types, resource names, and output names from plan.md — do not use placeholders where real values are known.

> "✅ tasks.md generated."

---

## Step 10: Update Track Status

Update `.infrakit_tracks/tracks.md` — change the track's Status to `📋 planned`.

> "✅ **Plan and task list ready for `<track-name>`!**
>
> **Files:**
> - `.infrakit_tracks/tracks/<track-name>/plan.md`
> - `.infrakit_tracks/tracks/<track-name>/tasks.md`
>
> **Next step**: Run `/infrakit:implement <track-name>` to start implementation."

---

## Error Handling

| Error | Action |
|-------|--------|
| Setup files missing | Halt, direct to `/infrakit:setup` |
| spec.md missing | Halt, direct to `/infrakit:create_terraform_code` |
| Resource argument unknown | Use `search_web("site:registry.terraform.io hashicorp/...")` to look it up |
| plan.md already exists | Ask: overwrite or update? |
