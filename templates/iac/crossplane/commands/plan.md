---
description: "Generate a Crossplane implementation plan (plan.md) for a track from its spec."
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
> Example: `sql-instance-20260101-120000`"

**WAIT** for response before continuing.

---

## System Directive

You are the **Crossplane Engineer** generating a detailed implementation plan for an infrastructure track. The plan translates the approved spec into a concrete Crossplane YAML implementation blueprint.

**You are generating plan.md — you are NOT writing code yet.**

Read `.infrakit/agent_personas/crossplane_engineer.md` for detailed persona behavior (if present).

---

## Step 1: Setup Check

Verify required files exist:

| File | Path | Required |
|------|------|----------|
| Project Context | `.infrakit/context.md` | ✅ Yes |
| Coding Style | `.infrakit/coding-style.md` | ✅ Yes |
| Tagging | `.infrakit/tagging-standard.md` | ✅ Yes |
| Spec | `.infrakit/tracks/<track-name>/spec.md` | ✅ Yes |

**If context.md, coding-style.md, or tagging-standard.md is missing:**
> "❌ Project not fully initialized. Run `/infrakit:setup` first."
**HALT**

**If spec.md is missing:**
> "❌ `spec.md` not found. Run `/infrakit:new_composition <track-name>` to create the spec."
**HALT**

---

## Step 2: Load Standards and Spec

Read the following files:

1. `.infrakit/context.md` — API group, naming conventions, cloud provider defaults
2. `.infrakit/coding-style.md` — Mandatory coding standards (Pipeline mode, tagging, secrets)
3. `.infrakit/tagging-standard.md` — Required tags for all managed resources
4. `.infrakit/tracks/<track-name>/spec.md` — Requirements, parameters, outputs, security

---

## Step 3: Research Managed Resource APIs

**CRITICAL**: Never guess `apiVersion` or resource `kind` values.

For each managed resource required by the spec:

1. Identify the correct Crossplane provider family (e.g., `provider-aws`, `provider-azure`, `provider-gcp`)
2. Look up the correct `apiVersion` and `kind` using:
   ```
   search_web("site:doc.crds.dev <provider> <resource-type>")
   ```
   Example: `search_web("site:doc.crds.dev upbound provider-aws RDSInstance")`
3. Verify the `spec.forProvider` fields available for the resource type
4. Record the verified API details in the plan

---

## Step 4: Design XRD Schema

Map each spec parameter to an XRD schema field:

| Spec Parameter | XRD Path | Type | Required | Default |
|----------------|----------|------|----------|---------|
| `<param>` | `spec.parameters.<param>` | `<type>` | `<bool>` | `<default>` |

Map each spec output to an XRD status field:

| Spec Output | XRD Status Path | Source |
|-------------|-----------------|--------|
| `<output>` | `status.<output>` | `status.atProvider.<field>` |

---

## Step 5: Design Patch Mappings

For each parameter → managed resource field:

| XR Field | Patch Type | Target Resource | Target Field |
|----------|------------|-----------------|--------------|
| `spec.parameters.<param>` | `FromCompositeFieldPath` | `<resource>` | `spec.forProvider.<field>` |

For each status output ← managed resource:

| Source Field | Patch Type | XR Status Field |
|--------------|------------|-----------------|
| `<resource>.status.atProvider.<field>` | `ToCompositeFieldPath` | `status.<output>` |

For required tags (per tagging-standard.md):

| Tag Key | Patch Type | Source | Target |
|---------|------------|--------|--------|
| `crossplane.io/claim-name` | `FromCompositeFieldPath` | `metadata.name` | `spec.forProvider.tags[crossplane.io/claim-name]` |
| `crossplane.io/claim-namespace` | `FromCompositeFieldPath` | `metadata.namespace` | `spec.forProvider.tags[crossplane.io/claim-namespace]` |
| `managed-by` | `FromCompositeFieldPath` (with format transform: `"crossplane"`) | `metadata.name` | `spec.forProvider.tags[managed-by]` |

---

## Step 6: Write plan.md

Write to `.infrakit/tracks/<track-name>/plan.md`:

```markdown
# Implementation Plan: <Resource Name>

## Summary
<Brief description of what will be built>

## Infrastructure Context

| Property | Value |
|----------|-------|
| **Track** | `<track-name>` |
| **Cloud Provider** | `<provider>` (from context.md) |
| **API Group** | `<api-group>` (from context.md) |
| **Crossplane Composition Mode** | Pipeline (mandatory) |

## Tech Stack

| Component | Version/Package |
|-----------|----------------|
| Crossplane | >= 1.14 |
| Provider | `<provider-package>` |
| Function | `crossplane-contrib-function-patch-and-transform` |

## XRD Design

### API Definition
- **XR Kind**: `<XKind>` (e.g., `XSQLInstance`)
- **Claim Kind**: `<Kind>` (e.g., `SQLInstance`)
- **API Group**: `<api-group>`
- **Version**: `v1alpha1`

### Spec Parameters

| Parameter | XRD Path | Type | Required | Default | Description |
|-----------|----------|------|----------|---------|-------------|
| `<param>` | `spec.parameters.<param>` | `<type>` | `<bool>` | `<default>` | `<desc>` |

### Status Fields

| Output | XRD Path | Source |
|--------|----------|--------|
| `<output>` | `status.<output>` | `<managed-resource>.status.atProvider.<field>` |

### Connection Secret Keys

| Key | Description |
|-----|-------------|
| `<key>` | `<description>` |

## Composition Design

### Managed Resources

| # | Resource Name | Kind | API Version | Purpose |
|---|---------------|------|-------------|---------|
| 1 | `<name>` | `<Kind>` | `<apiVersion>` | `<purpose>` |

### Patch Mappings

#### Input Patches (XR → Managed Resource)

| XR Field | Patch Type | Resource | Target Field |
|----------|------------|----------|--------------|
| `spec.parameters.<param>` | `FromCompositeFieldPath` | `<resource>` | `spec.forProvider.<field>` |

#### Output Patches (Managed Resource → XR Status)

| Source Field | Patch Type | XR Status Field |
|--------------|------------|-----------------|
| `<resource>.status.atProvider.<field>` | `ToCompositeFieldPath` | `status.<output>` |

#### Required Tag Patches (per tagging-standard.md)

Applied to **every** managed resource:

| Tag | Patch Type | Source | Target Field |
|-----|------------|--------|--------------|
| `crossplane.io/claim-name` | `FromCompositeFieldPath` | `metadata.name` | `spec.forProvider.tags[crossplane.io/claim-name]` |
| `crossplane.io/claim-namespace` | `FromCompositeFieldPath` | `metadata.namespace` | `spec.forProvider.tags[crossplane.io/claim-namespace]` |
| `managed-by` | `FromCompositeFieldPath` (format: `"crossplane"`) | `metadata.name` | `spec.forProvider.tags[managed-by]` |

## File Structure

```
<resource-directory>/
├── definition.yaml    # CompositeResourceDefinition (XRD)
├── composition.yaml   # Composition (Pipeline mode)
├── claim.yaml         # Example claim with all parameters
└── README.md          # Usage documentation
```

## Implementation Phases

1. **definition.yaml** — Create XRD with full OpenAPI v3 schema
2. **composition.yaml** — Create Pipeline mode Composition with all patches and tags
3. **claim.yaml** — Create example claim with all parameters populated
4. **README.md** — Document usage, parameters, and connection secrets
5. **Validate** — Run `crossplane render` to verify correctness

## Constraints from coding-style.md

- Pipeline mode is **mandatory** — never use Resources mode
- Every managed resource **must** have `providerConfigRef`
- Every managed resource **must** have all three required tag patches
- **Never** hardcode secrets or passwords
- **Never** set `publicNetworkAccess: Enabled` in production without explicit override

## Notes

### Known Challenges
- <any implementation challenges identified>

### Design Decisions
- <key decisions made during planning>
```

---

## Step 7: Feedback Loop

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

## Step 8: Next Actions

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
| spec.md missing | Halt, direct to `/infrakit:new_composition` |
| API version unknown | Use `search_web("site:doc.crds.dev ...")` to look it up |
| plan.md already exists | Ask: overwrite or update? |
