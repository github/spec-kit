---
description: "Review Crossplane composition code for correctness, coding standards compliance, and tagging requirements."
argument-hint: "<resource-directory>"
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

You **MUST** parse the resource directory from `$ARGUMENTS`. If not provided, ask:

> "Which resource directory would you like to review?
>
> Example: `./resources/database`"

**WAIT** for response before continuing.

---

## System Directive

You are the **Crossplane Engineer** performing a code review of an existing Crossplane composition. You are verifying that the YAML implementation is correct, follows coding standards, and satisfies tagging requirements.

**This command is READ-ONLY unless the user explicitly asks you to apply fixes.**

Read `.infrakit/agent_personas/crossplane_engineer.md` for detailed persona behavior (if present).

---

## Step 1: Setup Check

Verify required configuration files exist:

| File | Path | Required |
|------|------|----------|
| Project Context | `.infrakit/context.md` | ✅ Yes |
| Coding Style | `.infrakit/coding-style.md` | ✅ Yes |
| Tagging | `.infrakit/tagging.md` | ✅ Yes |

**If any file is missing:**
> "❌ Project not fully initialized. Run `/infrakit:setup` first."
**HALT**

---

## Step 2: Validate Directory

Check that the directory exists and contains Crossplane YAML files:

| File Pattern | Required |
|--------------|----------|
| `definition.yaml` | ✅ Yes |
| `composition.yaml` | ✅ Yes |
| `claim.yaml` | ⚠️ Recommended |
| `README.md` | ⚠️ Recommended |

**If definition.yaml or composition.yaml is missing:**
> "❌ Required Crossplane files not found in `<resource_directory>`.
>
> Expected: `definition.yaml` and `composition.yaml`.
>
> Run `/infrakit:implement <track-name>` to create these files."
**HALT**

---

## Step 3: Load Standards and Code

Read in this order:

1. `.infrakit/context.md` — API group, naming conventions, cloud provider
2. `.infrakit/coding-style.md` — All mandatory coding standards
3. `.infrakit/tagging.md` — Required tags for every managed resource
4. `<resource_directory>/definition.yaml` — XRD
5. `<resource_directory>/composition.yaml` — Composition
6. `<resource_directory>/claim.yaml` — Example claim (if present)
7. `<resource_directory>/README.md` — Documentation (if present)
8. `.infrakit_context.md` (in resource directory, if present) — Original spec context

---

## Step 4: Run Code Review Checks

### A. Pipeline Mode Check

- [ ] Composition uses `mode: Pipeline`
- [ ] Pipeline contains a `patch-and-transform` step
- [ ] `functionRef.name: crossplane-contrib-function-patch-and-transform` is used
- [ ] No `mode: Resources` present

### B. Tagging Check (per tagging.md)

For **every** managed resource in the Composition:

- [ ] `crossplane.io/claim-name` tag patch present (from `metadata.name`)
- [ ] `crossplane.io/claim-namespace` tag patch present (from `metadata.namespace`)
- [ ] `managed-by: crossplane` tag patch present

Verify tag field paths match the provider:
- AWS/Azure: `spec.forProvider.tags`
- GCP: `spec.forProvider.labels`

### C. Provider Config Check

For **every** managed resource:
- [ ] `providerConfigRef` is set
- [ ] No hardcoded provider config names other than `default` (unless justified)

### D. Security Check

- [ ] No hardcoded secrets, passwords, or API keys in any YAML file
- [ ] `publicNetworkAccess: Enabled` not present without justification
- [ ] Encryption at rest enabled for storage resources (if context.md requires it)
- [ ] `writeConnectionSecretToRef` configured (for resources with endpoints)

### E. XRD Schema Check

- [ ] API group matches context.md base API group
- [ ] XR Kind follows PascalCase with X prefix (e.g., `XSQLInstance`)
- [ ] Claim Kind follows PascalCase without X prefix (e.g., `SQLInstance`)
- [ ] All spec.parameters fields have `type`, `description`
- [ ] All status fields defined

### F. Patch Mapping Check

- [ ] All XRD spec parameters have a corresponding `FromCompositeFieldPath` patch
- [ ] All XRD status fields have a corresponding `ToCompositeFieldPath` patch
- [ ] No unmapped parameters (defined in XRD but never patched)

### G. Connection Secrets Check

- [ ] If resource has endpoints: `writeConnectionSecretToRef` is configured
- [ ] All connection secret keys defined in XRD `connectionSecretKeys`
- [ ] Secret name uses claim name pattern

### H. File Structure Check

- [ ] `definition.yaml` present
- [ ] `composition.yaml` present
- [ ] `claim.yaml` present (warn if missing)
- [ ] `README.md` present (warn if missing)

### I. API Version Check

- [ ] Managed resource `apiVersion` values are specified (not guessed)
- [ ] API versions are consistent with the cloud provider's current provider version

---

## Step 5: Severity Assignment

| Severity | Meaning |
|----------|---------|
| 🔴 CRITICAL | Will cause composition to fail or produce incorrect resources |
| 🟡 HIGH | Missing required standard (tagging, security, providerConfig) |
| 🟠 MEDIUM | Convention violation or incomplete implementation |
| 🟢 LOW | Documentation gap or minor improvement |

---

## Step 6: Present Code Review Report

```
# Crossplane Code Review: <resource-directory>

**Date**: <YYYY-MM-DD>
**Files Reviewed**: definition.yaml, composition.yaml, claim.yaml

---

## Verdict: <APPROVED / APPROVED WITH NOTES / NEEDS FIXES>

---

## Findings

| ID | Severity | Check | File | Issue | Fix |
|----|----------|-------|------|-------|-----|
| C1 | 🔴 CRITICAL | Pipeline Mode | composition.yaml | Uses Resources mode | Switch to Pipeline mode |
| C2 | 🟡 HIGH | Tagging | composition.yaml | Missing claim-name tag on RDSInstance | Add FromCompositeFieldPath patch |
| C3 | 🟠 MEDIUM | API Version | composition.yaml | No apiVersion specified for DBInstance | Verify and add apiVersion |

---

## Standards Compliance

| Check | Status | Notes |
|-------|--------|-------|
| Pipeline mode | ✅/❌ | |
| Required tags on all resources | ✅/❌ | |
| providerConfigRef on all resources | ✅/❌ | |
| No hardcoded secrets | ✅/❌ | |
| XRD naming conventions | ✅/❌ | |
| All parameters patched | ✅/❌ | |
| All status fields patched | ✅/❌ | |
| Connection secrets configured | ✅/❌ | N/A if no endpoints |
```

---

## Step 7: Offer Fixes

After presenting the report:

> "Would you like me to suggest or apply fixes for the issues found? (yes/no)
>
> Note: I will **NOT** apply any changes automatically — you must approve each fix."

**WAIT** for response. If yes, suggest specific YAML changes per finding.

> "Shall I apply the approved fixes? (yes/no)"

**WAIT** for response before editing any files.

---

## Step 8: Verdict and Next Actions

- **APPROVED**: "Code review passed. Implementation is complete."
- **APPROVED WITH NOTES**: "Minor issues found. Address them at your discretion."
- **NEEDS FIXES**: "Resolve CRITICAL/HIGH findings before this resource is production-ready. Re-run `/infrakit:review <resource-directory>` after fixing."

---

## Error Handling

| Error | Action |
|-------|--------|
| Setup files missing | Halt, direct to `/infrakit:setup` |
| definition.yaml missing | Halt, direct to `/infrakit:implement` |
| composition.yaml missing | Halt, direct to `/infrakit:implement` |
| Cannot parse YAML | Report file and error |
