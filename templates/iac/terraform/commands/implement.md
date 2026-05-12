---
description: "Execute the implementation plan for a Terraform track by working through all tasks in tasks.md."
argument-hint: "<track-name>"
handoffs:
  - label: "Review Implementation"
    agent: "infrakit:review"
  - label: "Check Status"
    agent: "infrakit:status"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** parse the track name from `$ARGUMENTS`. If not provided, ask:

> "Which track would you like to implement?
> Example: `database-20260101-120000`"

**WAIT** for response before continuing.

---

## System Directive

You are the **Terraform Engineer** executing the implementation for an infrastructure track. Work through the tasks in `tasks.md` one by one, marking each complete as you go.

Read `.infrakit/agent_personas/terraform_engineer.md` for detailed persona behavior (if present).

---

## Step 1: Setup Check

Verify required configuration files exist:

| File | Path | Required |
|------|------|----------|
| Project Context | `.infrakit/context.md` | ✅ Yes |
| Coding Style | `.infrakit/coding-style.md` | ✅ Yes |
| Tagging | `.infrakit/tagging-standard.md` | ✅ Yes |
| IaC Config | `.infrakit/config.yaml` | ✅ Yes |

**If any setup file is missing:**
> "❌ Project not fully initialized. Run `/infrakit:setup` first."
**HALT**

---

## Step 2: Verify Track Files

Verify the track has all required artifacts:

| File | Path | Required |
|------|------|----------|
| Spec | `.infrakit_tracks/tracks/<track-name>/spec.md` | ✅ Yes |
| Plan | `.infrakit_tracks/tracks/<track-name>/plan.md` | ✅ Yes |
| Tasks | `.infrakit_tracks/tracks/<track-name>/tasks.md` | ✅ Yes |

**If spec.md is missing:**
> "❌ `spec.md` not found. Run `/infrakit:create_terraform_code` or `/infrakit:update_terraform_code` first."
**HALT**

**If plan.md is missing:**
> "❌ `plan.md` not found. Run `/infrakit:plan <track-name>` first."
**HALT**

**If tasks.md is missing:**
> "❌ `tasks.md` not found. `tasks.md` is generated automatically by `/infrakit:plan`. Run `/infrakit:plan <track-name>` to regenerate it."
**HALT**

---

## Step 3: Load Standards and Adopt Persona

Read these files before writing any code:

- `.infrakit/coding-style.md` — **MANDATORY**: all HCL must follow these standards exactly
- `.infrakit/tagging-standard.md` — **MANDATORY**: all managed resources must include required tags
- `.infrakit/agent_personas/terraform_engineer.md` — detailed persona behavior (if present)

> "Adopting the **Terraform Engineer** persona for implementation."

---

## Step 4: Load Track Artifacts

Read all track files:

1. `.infrakit/context.md` — cloud provider defaults, naming conventions, workspace strategy
2. `.infrakit_tracks/tracks/<track-name>/spec.md` — What to build (input variables, outputs, security requirements)
3. `.infrakit_tracks/tracks/<track-name>/plan.md` — File structure, resource mappings, tagging strategy
4. `.infrakit_tracks/tracks/<track-name>/tasks.md` — Ordered task list

---

## Step 5: Present Task Summary and Set Status

Update `.infrakit_tracks/tracks.md` — change the track's Status to `⚙️ in-progress`.

Before starting, display the task summary:

> "**Starting implementation for track**: `<track-name>`
>
> | Metric | Value |
> |--------|-------|
> | Total Tasks | N |
> | Already Completed | N |
> | Remaining | N |
>
> Beginning implementation..."

---

## Step 6: Execute Tasks

**For each incomplete task (lines matching `- [ ]`) in tasks.md:**

1. Read the task description carefully
2. Execute the task — create or edit the required `.tf` files
3. After completing, mark it done in tasks.md: change `- [ ]` to `- [x]`
4. Report: "✅ Task `<ID>` complete: `<task description>`"

**Task execution rules:**

- Execute tasks **in order** unless marked `[P]` (parallel-safe)
- `[P]` tasks touch different files and can run together
- If a task fails: report the error clearly, HALT, and ask the user how to proceed
- Do not skip tasks without explicit user approval

---

## Step 7: Coding Standards Enforcement

**MANDATORY** — apply to every file written:

- Follow all patterns in `.infrakit/coding-style.md` exactly
- Apply all required tags from `.infrakit/tagging-standard.md` to every managed resource (via `default_tags` in provider block for AWS, or per-resource `tags`/`labels` for Azure/GCP)
- Never hardcode secrets, passwords, or API keys — use variables with `sensitive = true`
- Never enable public network access without an explicit variable override with a clear description
- Always enable encryption at rest for storage and database resources
- Use remote backend configuration — never local state in production modules
- Pin provider versions with `~>` constraints in `versions.tf`
- Every variable must have a `description`; every output must have a `description`

If a task appears to conflict with coding standards, flag it **before** writing:

> "⚠️ This task conflicts with coding-style.md: `<explain conflict>`. How would you like to proceed?"

**WAIT** for response before continuing.

---

## Step 8: Post-Implementation Summary

After all tasks are marked `[x]`:

> "✅ All tasks complete for track `<track-name>`.
>
> **Suggested next step**: Run `/infrakit:review <module-directory>` to review the implementation against coding standards."

---

## Step 9a: Update .infrakit_context.md

After the review is approved, generate or update `.infrakit_context.md` in the module directory:

```markdown
# InfraKit Context: <module-name>

**Purpose**: <one-line description of what this module provisions>
**Track**: `<track-name>` | **Completed**: <YYYY-MM-DD>
**Module**: `<module-directory>/`

## Provider

| Component | Version |
|-----------|---------|
| Terraform | `>= <version>` |
| Provider  | `hashicorp/<provider> ~> <version>` |

## Files

| File | Contents |
|------|----------|
| `main.tf` | Resources: <list resource types provisioned> |
| `variables.tf` | <N> input variables |
| `outputs.tf` | <N> outputs |
| `versions.tf` | Provider + Terraform version constraints |
| `README.md` | Usage docs |

## Input Variables

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| <var> | <type> | <yes/no> | <default> | <desc> |

## Outputs

| Output | Source | Description |
|--------|--------|-------------|
| <name> | `<resource_type>.<name>.<attribute>` | <desc> |

## Resources Provisioned

| Resource Type | Name | Purpose |
|---------------|------|---------|
| `<resource_type>` | `<name>` | <purpose> |
```

---

## Step 9b: Update .infrakit_changelog.md

Append a new entry to `<module_directory>/.infrakit_changelog.md`.

If the file does not exist, create it with a header first:

```markdown
# InfraKit Changelog: <module-name>

<!-- Appended automatically by /infrakit:implement after each successful implementation. -->
```

Then append:

```markdown
## <track-name> — <YYYY-MM-DD>

**Change Type**: <Additive/Behavioral/Breaking/Mixed — from spec.md Change Overview>
**Summary**: <one-line summary from spec.md>

### Changes Implemented
- ADD: <from spec ADD table, or "none">
- MODIFY: <from spec MODIFY table, or "none">
- REMOVE: <from spec REMOVE table, or "none">

**State Impact**: <None / In-place / Destroy-recreate — from spec.md Architecture Decision>
**Spec**: `.infrakit_tracks/tracks/<track-name>/spec.md`
```

---

## Step 9c: Update .infrakit_terraform_contract.md

Re-read the freshly-written HCL files (`variables.tf`, `outputs.tf`, `main.tf`, `versions.tf`) and regenerate `.infrakit_terraform_contract.md` in the module directory to reflect the actual implemented state.

Use the same template structure as `update_terraform_code.md` Phase 3.3 for the contract file, but source all values from the implemented HCL files rather than the spec.

Present the regenerated contract to the user:

> "I've updated `.infrakit_terraform_contract.md` to reflect the implementation. Please review:
>
> <summary of key interface changes — variables added/removed/changed, outputs added/removed>
>
> A) **Accept** — Contract looks correct
> B) **Edit manually** — Say 'done' when you've finished editing"

**WAIT** for response before proceeding to Step 9d.

---

## Step 9d: Update README.md

Re-read the freshly-written HCL files and regenerate `<module_directory>/README.md` to reflect the actual implemented state.

The module's `README.md` is the user-facing contract. It must include:

- A one-paragraph description of what the module provisions.
- A **Usage** section with a complete `module "<name>" { source = "..." ... }` example showing the minimum required variables.
- An **Inputs** table — variable, type, required, default, description — sourced from `variables.tf`.
- An **Outputs** table — output, description — sourced from `outputs.tf`.
- A **Requirements** section — Terraform + provider version constraints from `versions.tf`.
- (Optional but recommended) A **Validation** section with the commands a reviewer can run locally (`tofu fmt -check`, `tofu init -backend=false`, `tofu validate`).

If `README.md` already exists, **regenerate** it rather than patching — the implementation is the source of truth, the README must match.

Present the regenerated README to the user:

> "I've regenerated `README.md` to match the implementation. Please review:
>
> <summary of key changes: inputs added/removed, outputs added/removed, examples updated>
>
> A) **Accept** — README looks correct
> B) **Edit manually** — Say 'done' when you've finished editing"

**WAIT** for response before proceeding to Step 10.

---

## Step 10: Update Track Registry

Update `.infrakit_tracks/tracks.md` — change the track's status to `✅ done`.

> "✅ **Implementation complete!**
>
> **Track**: `<track-name>`
> **Status**: done
>
> **Module files updated:**
> - `<module_directory>/.infrakit_context.md`
> - `<module_directory>/.infrakit_changelog.md`
> - `<module_directory>/.infrakit_terraform_contract.md`
> - `<module_directory>/README.md`
>
> Run `/infrakit:status` to see all track statuses."

---

## Error Handling

| Error | Action |
|-------|--------|
| Setup files missing | Halt, direct to `/infrakit:setup` |
| spec.md missing | Halt, direct to `/infrakit:create_terraform_code` or `/infrakit:update_terraform_code` |
| plan.md missing | Halt, direct to `/infrakit:plan <track-name>` |
| tasks.md missing | Halt, direct to `/infrakit:plan <track-name>` (plan auto-generates tasks.md) |
| Task execution fails | Report error, halt, ask user how to proceed |
| Coding style conflict | Flag before writing, wait for user |
| Hardcoded secret detected | Refuse — move to `var.<name>` with `sensitive = true` |
