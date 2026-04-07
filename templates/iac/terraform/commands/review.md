---
description: "Review Terraform module code for correctness, coding standards compliance, and tagging requirements."
argument-hint: "<module-directory>"
handoffs:
  - label: "Check Status"
    agent: "infrakit:status"
  - label: "Architect Review"
    agent: "infrakit:architect-review"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** parse the module directory from `$ARGUMENTS`. If not provided, ask:

> "Which module directory would you like to review?
>
> Example: `./modules/database`"

**WAIT** for response before continuing.

---

## System Directive

You are the **Terraform Engineer** performing a code review of an existing Terraform module. You are verifying that the HCL implementation is correct, follows coding standards, and satisfies tagging requirements.

**This command is READ-ONLY unless the user explicitly asks you to apply fixes.**

Read `.infrakit/agent_personas/terraform_engineer.md` for detailed persona behavior (if present).

---

## Step 1: Setup Check

Verify required configuration files exist:

| File | Path | Required |
|------|------|----------|
| Project Context | `.infrakit/context.md` | ✅ Yes |
| Coding Style | `.infrakit/coding-style.md` | ✅ Yes |
| Tagging | `.infrakit/tagging-standard.md` | ✅ Yes |

**If any file is missing:**
> "❌ Project not fully initialized. Run `/infrakit:setup` first."
**HALT**

---

## Step 2: Validate Directory

Check that the directory exists and contains Terraform files:

| File | Required |
|------|----------|
| `main.tf` | ✅ Yes |
| `variables.tf` | ⚠️ Recommended |
| `outputs.tf` | ⚠️ Recommended |
| `versions.tf` | ⚠️ Recommended |
| `README.md` | ⚠️ Recommended |

**If main.tf is missing:**
> "❌ Required Terraform file not found in `<module_directory>`.
>
> Expected at minimum: `main.tf`.
>
> Run `/infrakit:implement <track-name>` to create these files."
**HALT**

---

## Step 3: Load Standards and Code

Read in this order:

1. `.infrakit/context.md` — naming conventions, cloud provider, workspace strategy
2. `.infrakit/coding-style.md` — All mandatory coding standards
3. `.infrakit/tagging-standard.md` — Required tags for every resource
4. `<module_directory>/versions.tf` — Provider and Terraform version constraints (if present)
5. `<module_directory>/variables.tf` — Variable declarations (if present)
6. `<module_directory>/main.tf` — Resource definitions
7. `<module_directory>/outputs.tf` — Output declarations (if present)
8. `<module_directory>/README.md` — Documentation (if present)
9. `.infrakit_context.md` (in module directory, if present) — Original spec context

---

## Step 4: Run Code Review Checks

### A. File Structure Check

- [ ] `main.tf` present
- [ ] `variables.tf` present (warn if missing — all variables inline in main.tf is discouraged)
- [ ] `outputs.tf` present (warn if missing)
- [ ] `versions.tf` present (warn if missing — pinning is a best practice)
- [ ] `README.md` present (warn if missing)

### B. Versions and Provider Pinning Check

- [ ] `terraform { required_version = "..." }` declared in `versions.tf`
- [ ] Provider version constraints declared (e.g., `~> 5.0` not `>= 5.0` with no upper bound)
- [ ] No unpinned provider versions (bare `source = "hashicorp/aws"` with no `version =`)

### C. Variable Declaration Check

For **every** variable in `variables.tf`:

- [ ] `type` constraint declared
- [ ] `description` present
- [ ] Sensitive variables marked with `sensitive = true`
- [ ] No plaintext default values for secrets (no `default = "mypassword"`)
- [ ] Validation blocks used for constrained values (environments, sizes, etc.)

### D. Tagging Check (per tagging-standard.md)

For **every** resource that supports tags/labels in `main.tf`:

- AWS resources: `tags` map present with required keys from tagging-standard.md
- Azure resources: `tags` map present with required keys
- GCP resources: `labels` map present with required keys

Preferred pattern for AWS — check if `default_tags` is used in provider block:
- [ ] `default_tags` block in `provider "aws"` (preferred) OR per-resource `tags` merge pattern

Required tag keys (per tagging-standard.md):
- [ ] `managed-by = "terraform"` (or equivalent)
- [ ] Project/environment tags as specified in tagging-standard.md

### E. Security Check

- [ ] No hardcoded secrets, passwords, or API keys in any `.tf` file
- [ ] Public network access not enabled without explicit variable and default set to `false`
- [ ] Encryption at rest enabled for storage resources (e.g., `encrypted = true`, `storage_encrypted = true`)
- [ ] Encryption in transit enforced where applicable
- [ ] No wildcard IAM policies (`*`) without justification
- [ ] Sensitive outputs declared with `sensitive = true`

### F. Output Declaration Check

- [ ] All outputs declared in `outputs.tf` (not inline in `main.tf`)
- [ ] Each output has a `description`
- [ ] Sensitive outputs (credentials, tokens) marked `sensitive = true`
- [ ] No unnecessary full-object outputs (expose specific attributes, not entire resources)

### G. Resource Naming Check

- [ ] Resource names follow naming convention from `coding-style.md`
- [ ] No hardcoded resource names that would conflict on multiple instantiations
- [ ] `name` arguments use `var.name` or include module-caller-provided prefix

### H. Backend and State Check

- [ ] If backend is configured, it references variables or is parameterized (not hardcoded bucket/container names)
- [ ] No `terraform.tfstate` or `*.tfstate` files committed (check for `.gitignore` patterns)

### I. Provider Configuration Check

- [ ] Provider `region`/`location` is parameterized (not hardcoded) unless the module is explicitly region-specific
- [ ] No hardcoded account IDs, subscription IDs, or project IDs

---

## Step 5: Severity Assignment

| Severity | Meaning |
|----------|---------|
| 🔴 CRITICAL | Will cause apply failure, data exposure, or security breach |
| 🟡 HIGH | Missing required standard (hardcoded secrets, no encryption, missing tags) |
| 🟠 MEDIUM | Convention violation or incomplete implementation |
| 🟢 LOW | Documentation gap or minor improvement |

---

## Step 6: Present Code Review Report

```
# Terraform Code Review: <module-directory>

**Date**: <YYYY-MM-DD>
**Files Reviewed**: main.tf, variables.tf, outputs.tf, versions.tf

---

## Verdict: <APPROVED / APPROVED WITH NOTES / NEEDS FIXES>

---

## Findings

| ID | Severity | Check | File | Issue | Fix |
|----|----------|-------|------|-------|-----|
| T1 | 🔴 CRITICAL | Security | main.tf | Hardcoded password in resource | Use var.password with sensitive=true |
| T2 | 🟡 HIGH | Tagging | main.tf | Missing managed-by tag on aws_instance | Add to tags map or default_tags |
| T3 | 🟠 MEDIUM | Versions | versions.tf | No upper bound on provider version | Change >= 5.0 to ~> 5.0 |

---

## Standards Compliance

| Check | Status | Notes |
|-------|--------|-------|
| File structure complete | ✅/❌ | |
| Provider version pinning | ✅/❌ | |
| Variable descriptions | ✅/❌ | |
| Sensitive variables marked | ✅/❌ | |
| Required tags on all resources | ✅/❌ | |
| No hardcoded secrets | ✅/❌ | |
| Encryption at rest | ✅/❌ | N/A if no storage resources |
| Public access disabled by default | ✅/❌ | |
| Output descriptions | ✅/❌ | |
```

---

## Step 7: Offer Fixes

After presenting the report:

> "Would you like me to suggest or apply fixes for the issues found? (yes/no)
>
> Note: I will **NOT** apply any changes automatically — you must approve each fix."

**WAIT** for response. If yes, suggest specific HCL changes per finding.

> "Shall I apply the approved fixes? (yes/no)"

**WAIT** for response before editing any files.

---

## Step 8: Verdict and Next Actions

- **APPROVED**: "Code review passed. Implementation is complete."
- **APPROVED WITH NOTES**: "Minor issues found. Address them at your discretion."
- **NEEDS FIXES**: "Resolve CRITICAL/HIGH findings before this module is production-ready. Re-run `/infrakit:review <module-directory>` after fixing."

---

## Error Handling

| Error | Action |
|-------|--------|
| Setup files missing | Halt, direct to `/infrakit:setup` |
| main.tf missing | Halt, direct to `/infrakit:implement` |
| Cannot parse HCL | Report file and error |
