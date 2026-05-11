---
description: "Update an existing Crossplane resource composition through a multi-persona review workflow."
argument-hint: "<resource-directory>"
handoffs:
  - label: "Generate Plan"
    agent: "infrakit:plan"
  - label: "Check Status"
    agent: "infrakit:status"
---

## User Input

```text
$ARGUMENTS
```

Parse `$ARGUMENTS` for the resource directory. If not provided, ask.

---

## System Directive

You are guiding the user through updating an existing Crossplane resource composition. This command scans the existing code to understand the current state, ensures all resource contract files are present and reviewed, then runs a structured solutioning and review workflow.

**CRITICAL**: Ask only one question at a time. Wait for a response before asking the next.

---

## Phase 1: Setup Check

### 1.1 Verify Required Files

| File | Path | Required |
|------|------|----------|
| Project Context | `.infrakit/context.md` | ✅ Yes |
| Coding Style | `.infrakit/coding-style.md` | ✅ Yes |
| Tagging | `.infrakit/tagging-standard.md` | ✅ Yes |
| Track Registry | `.infrakit_tracks/tracks.md` | ✅ Yes |

**If any file is missing:**
> "❌ Project not fully initialized. Run `/infrakit:setup` to initialize."
**HALT**

Read `.infrakit/context.md`, `.infrakit/coding-style.md`, and `.infrakit/tagging-standard.md` before proceeding.

---

## Phase 2: Argument Collection and Validation

### 2.1 Resource Directory

If not provided in `$ARGUMENTS`, ask:

> "Which resource directory do you want to update?
>
> Example: `./resources/database`"

**WAIT** for response.

### 2.2 Validate Directory Exists and Contains Resources

```bash
test -d <resource_directory>
```

**If directory does NOT exist:**
> "❌ Directory `<resource_directory>` does not exist.
>
> To create a new resource, use `/infrakit:new_composition`."
**HALT**

Check for required Crossplane files:

| File Pattern | Required |
|--------------|----------|
| `*definition*.yaml` or `*xrd*.yaml` | ✅ Yes |
| `*composition*.yaml` | ✅ Yes |
| `*claim*.yaml` | ⚠️ Recommended |

**If XRD or Composition is missing:**
> "⚠️ The directory does not appear to contain valid Crossplane resources.
>
> A) **Continue anyway** — I'll work with what I find
> B) **Use new_composition** — Create from scratch
> C) **Cancel**"

**WAIT** for response.

---

## Phase 3: Validate and Generate Resource Contract Files

### 3.1 Check for Required Resource Files

Check for all three resource artifact files in `<resource_directory>`:

| File | Purpose |
|------|---------|
| `.infrakit_context.md` | Original spec, parameters, and design decisions |
| `.infrakit_changelog.md` | History of all changes applied to this resource |
| `infrakit_composition_contract.md` | Stable API surface and guarantees for consumers |

**If ALL three exist**: Read them all and proceed to Phase 4.

**If ANY are missing**: Scan the existing YAML files to generate the missing ones (Phases 3.2–3.4).

### 3.2 Scan Existing Resource Files

Read all `*.yaml` files in `<resource_directory>`. Extract:

**From XRD** (`*definition*.yaml` / `*xrd*.yaml`):
- API group, version, XR Kind, Claim Kind
- All spec parameters (name, type, required, default)
- All status fields
- Connection secret keys (if defined)

**From Composition** (`*composition*.yaml`):
- Pipeline mode or Resources mode
- All managed resources (kind, apiVersion, purpose)
- Patch mappings (input → output)
- Tag patches applied

### 3.3 Generate Missing Files

For each file that does not exist, generate it now:

---

**`.infrakit_context.md`** (if missing):

```markdown
# InfraKit Context: <resource-name>

**Purpose**: <one-line description reconstructed from code>
**Track**: (reconstructed) | **Completed**: <YYYY-MM-DD of last modification>

## XRD

| XR Kind | Claim Kind | API Group | Version |
|---------|-----------|-----------|---------|
| `<XKind>` | `<Kind>` | `<group>` | `<version>` |

## Files

| File | Contents |
|------|----------|
| `definition.yaml` | XRD: <brief description> |
| `composition.yaml` | Pipeline Composition: <managed resources list> |
| `claim.yaml` | Example claim |
| `README.md` | Usage docs |

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| <param> | <type> | <yes/no> | <default> | <desc> |

## Status Outputs

| Field | Source | Description |
|-------|--------|-------------|
| <field> | `<resource>.status.atProvider.<path>` | <desc> |

## Connection Secrets

| Key | Description |
|-----|-------------|
| <key> | <desc> |

<!-- Reconstructed by `/infrakit:update_composition` from code analysis. -->
```

---

**`.infrakit_changelog.md`** (if missing):

```markdown
# InfraKit Changelog: <resource-name>

<!-- Change history for this composition. Each update track appends an entry here. -->

## (reconstructed) — <YYYY-MM-DD of last modification>

**Change Type**: (original creation — reconstructed)
**Summary**: Initial composition, reconstructed from code analysis.

### Resources Managed
<list of managed resource types from composition.yaml>

<!-- Reconstructed by `/infrakit:update_composition` from code analysis. -->
```

---

**`infrakit_composition_contract.md`** (if missing):

```markdown
# Composition Contract: <resource-name>

<!-- This contract defines the stable API surface and guarantees for consumers of this composition. -->

## Interface

| Aspect | Value |
|--------|-------|
| XR Kind | `<Kind>` |
| Claim Kind | `<ClaimKind>` |
| API Group | `<api-group>` |
| Current Version | `<version>` |
| Stability | <Stable/Beta/Alpha — inferred from version prefix> |

## Required Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| <required params from XRD spec> | | |

## Optional Inputs (with defaults)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| <optional params from XRD spec> | | | |

## Guaranteed Outputs

| Field | Type | Description |
|-------|------|-------------|
| <status fields from XRD status> | | |

## Connection Secrets

| Key | Description |
|-----|-------------|
| <connection secret keys from XRD> | |

## Stability Guarantees
- Required parameters will not be removed without a XRD version increment
- Optional parameter types will not change without a XRD version increment
- Status fields listed above are guaranteed to be populated when the resource is ready

## Deprecation Policy
- Deprecated parameters are kept for one major version with a deprecation annotation
- Breaking changes require a new XRD version (e.g., `v1alpha1` → `v1beta1`)

<!-- Reconstructed by `/infrakit:update_composition` from code analysis. -->
```

### 3.4 Present Generated Files for Review

Present only the files that were newly generated:

> "I've generated the following resource files from code analysis:
>
> **Generated:**
> - <list only newly generated files>
>
> **Resource Summary:**
>
> | Aspect | Value |
> |--------|-------|
> | XR Kind / Claim | `<Kind>` / `<ClaimKind>` |
> | API Group / Version | `<group>` / `<version>` |
> | Required Params | <N> |
> | Optional Params | <N> |
> | Managed Resources | <comma-separated list> |
>
> Please review the generated files. What would you like to do?
>
> A) **Accept** — Files look correct, proceed with the update
> B) **I've updated them manually** — Edit the files now, say 'done' when ready
> C) **Regenerate** — Tell me what to correct"

**WAIT** for response.

- If **A**: Proceed to Phase 4.
- If **B**: Wait for 'done', re-read all three files, then proceed to Phase 4.
- If **C**: Ask what to correct, regenerate the relevant files, loop back to 3.4.

---

## Phase 4: Create Update Track

Generate a track name: `<resource-name>-update-<YYYYMMDD-HHMMSS>`

Example: `database-update-20260101-120000`

Create the track directory:
```bash
mkdir -p .infrakit_tracks/tracks/<track-name>
```

Register in `.infrakit_tracks/tracks.md` — add a row with Status `🔵 initializing` and Type `update`.

---

## Phase 5: Cloud Solutions Engineer — Requirements Clarification and Spec

This phase is **interactive** — you and the user iterate on what's changing. Run it **inline** in your current context regardless of whether your harness supports subagents: a subagent can't pause to wait for user input.

Adopt the Cloud Solutions Engineer persona by reading `.infrakit/agent_personas/cloud_solutions_engineer.md` and following its behaviour for the duration of Phase 5. Later phases (Architect and Security review) can be delegated to subagents when available — see Phases 6 and 7.

> "I'll now guide you through defining the changes for this resource.
> Acting as the **Cloud Solutions Engineer**, I'll ask clarifying questions until I fully understand your requirements before writing the spec."

### 5.1 Change Description

> "What changes do you want to make to this resource?
>
> Examples:
> - 'Add a backup retention parameter'
> - 'Enable encryption at rest'
> - 'Expose the resource endpoint in status'
>
> Describe your changes:"

**WAIT** for response.

### 5.2 Change Classification

Analyze the user's description and classify:

- **Additive** — New optional fields or resources (backward compatible)
- **Behavioral** — Changing defaults or logic (may affect existing claims)
- **Breaking** — Removing fields, changing types, new required fields (migration required)

> "Based on your description, these changes appear to be: **<classification>**
>
> **Recommended XRD version strategy:**
> - Current version: `<from existing XRD>`
> - Recommended: `<new version if breaking, same if not>`
>
> Do you agree? (yes/no/modify)"

**WAIT** for response.

### 5.3 Requirements Clarification Loop

Ask clarifying questions based on the change type, **one at a time**. **WAIT** after each question before asking the next.

Cover these areas (only ask what is not yet answered):

**For new parameters:**
- What type should the parameter be? (string, integer, boolean, object)
- Is it required or optional? If optional, what is the default?
- What validation constraints apply? (min/max, enum values, regex pattern)
- How does it affect the underlying managed resource?

**For behavioral changes:**
- What is the old behavior and what should the new behavior be?
- Which existing claims will be affected when re-applied?
- Is re-apply safe or will it cause disruption?

**For new outputs / status fields:**
- What is the source of the value? (which managed resource and attribute path)
- Should it also be exposed in the connection secret?

**For security requirements:**
- Are there encryption requirements?
- IAM or RBAC constraints?
- Network policy implications?

After each answer, assess: **Are all requirements for this change fully clear?**

When requirements are complete, summarize and confirm:

> "I've gathered all the requirements. Here's my understanding:
>
> <bulleted summary of every change and the reasoning behind it>
>
> Is this correct and complete? (yes / add more)"

**WAIT** for response. If the user adds more, continue the clarification loop. Repeat until the user confirms the summary is complete.

### 5.4 Generate spec.md

Write to `.infrakit_tracks/tracks/<track-name>/spec.md`:

```markdown
# Update Specification: <Resource Name>

## Change Overview

| Property | Value |
|----------|-------|
| **Change Type** | <Additive/Behavioral/Breaking/Mixed> |
| **Current XRD Version** | <from existing XRD> |
| **Proposed XRD Version** | <new version if breaking> |
| **Migration Required** | <Yes/No> |

## Existing Resource (Current State)

**XRD**: `<Kind>` (`<api-group>`)
**Parameters (Current):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| ... | ... | ... | ... |

## Proposed Changes

### ADD: New Elements

| Element | Type | Required | Default | Description |
|---------|------|----------|---------|-------------|
| `<param>` | `<type>` | <yes/no> | <default> | ... |

### MODIFY: Changed Elements

| Element | Current | New | Impact |
|---------|---------|-----|--------|
| `<param>` | `<old>` | `<new>` | <Breaking/Non-breaking> |

### REMOVE: Deprecated Elements

| Element | Reason | Migration Path |
|---------|--------|----------------|
| `<param>` | `<reason>` | `<alternative>` |

## Security Requirements
- <requirement>

## Acceptance Criteria
- [ ] All ADD changes implemented
- [ ] All MODIFY changes implemented
- [ ] All REMOVE changes handled safely
- [ ] Migration guide created (if breaking)
```

### 5.5 Generate migration.md (If Breaking Changes)

If changes are classified as Breaking or Mixed, also write `.infrakit_tracks/tracks/<track-name>/migration.md`:

```markdown
# Migration Guide: <Resource Name>

## Overview

| Property | Value |
|----------|-------|
| **From Version** | `<old version>` |
| **To Version** | `<new version>` |
| **Breaking Changes** | `<count>` |

## Breaking Changes

### 1. <Change Description>

**What changed:**
- Old: `<old behavior/schema>`
- New: `<new behavior/schema>`

**Migration Steps:**
1. <Step 1>
2. <Step 2>

## Pre-Migration Checklist
- [ ] Backup existing claims
- [ ] Test migration in non-production environment

## Rollback Plan
1. <Rollback step 1>
2. <Rollback step 2>
```

### 5.6 Spec Options Loop

> "I've generated the update specification.
>
> **Files:**
> - `.infrakit_tracks/tracks/<track-name>/spec.md`
> <if breaking> - `.infrakit_tracks/tracks/<track-name>/migration.md`
>
> What would you like to do?
>
> A) **Regenerate** — Tell me what to change
> B) **Manual Changes** — Edit the file, say 'done' when ready
> C) **Proceed** — Hand off to Cloud Architect for design options"

**WAIT** for response. Loop until user chooses C.

---

## Phase 6: Cloud Architect — Design Options

The **analysis** part of this phase is read-only and benefits from subagent isolation; the **option-selection** part needs user input and must stay inline.

**If your harness supports subagents (Claude Code's `Task` tool):**

Invoke the `Task` tool with:

- `description`: `"Cloud Architect design options for <track-name>"`
- `subagent_type`: `general-purpose`
- `prompt`:

  > You are running an architecture-options analysis against an InfraKit update track. Do not modify any files. Return only the option set.
  >
  > 1. Read `.infrakit/agent_personas/cloud_architect.md` and adopt that persona.
  > 2. Read `.infrakit/context.md`, `.infrakit/coding-style.md`, `.infrakit_tracks/tracks/<track-name>/spec.md`, plus the resource directory's `.infrakit_context.md` and `infrakit_composition_contract.md`.
  > 3. Identify backward-compatibility constraints, XRD version strategy required, migration complexity and state risk, performance and reliability trade-offs.
  > 4. Produce **2–3 distinct, named architecture options** following the format in Phase 6.2 below. Do NOT pick one — return all options for the user to choose from.
  > 5. Return the formatted option set as your final message. Do **not** edit `spec.md`.

Paste the returned options into your reply and proceed to Phase 6.2 (user selection).

**If your harness does not support subagents (Codex, Gemini, Copilot, generic):**

Read `.infrakit/agent_personas/cloud_architect.md` and adopt that persona inline. Mark the boundary in your reply ("entering Cloud Architect phase"). Run the analysis described in Phase 6.1 and produce the option set in Phase 6.2.

> "Handing off to the Cloud Architect..."
> "As the **Cloud Architect**, I'll review the spec and present distinct architecture options for implementing these changes. You choose the direction."

### 6.1 Architecture Analysis

Review the spec alongside `.infrakit_context.md` and `infrakit_composition_contract.md`. Identify:
- Backward compatibility constraints from the current contract
- XRD version strategy required
- Migration complexity and state risk
- Performance and reliability implications of each approach

### 6.2 Present Architecture Options

Present **2–3 distinct, named architecture options**. Each must include a trade-off table so the user can make an informed choice.

> "I've analysed the spec and identified the following design options:
>
> ---
>
> ### Option A: <Short Name> (e.g., Minimal / In-place)
>
> **Approach**: <1–2 sentence description of the design>
>
> | Aspect | Assessment |
> |--------|-----------|
> | Backward Compatibility | <Full / Partial / Breaking> |
> | XRD Version Change | <None / Patch / Minor / Major> |
> | Implementation Complexity | <Low / Medium / High> |
> | Migration Required | <Yes / No> |
>
> **Trade-offs:**
> - ✅ <primary advantage>
> - ⚠️ <key limitation or risk>
>
> ---
>
> ### Option B: <Short Name> (e.g., Recommended)
>
> **Approach**: <1–2 sentence description>
>
> | Aspect | Assessment |
> |--------|-----------|
> | Backward Compatibility | <Full / Partial / Breaking> |
> | XRD Version Change | <None / Patch / Minor / Major> |
> | Implementation Complexity | <Low / Medium / High> |
> | Migration Required | <Yes / No> |
>
> **Trade-offs:**
> - ✅ <primary advantage>
> - ⚠️ <key limitation or risk>
>
> ---
>
> ### Option C: <Short Name> (e.g., Forward-Looking)
>
> **Approach**: <1–2 sentence description>
>
> | Aspect | Assessment |
> |--------|-----------|
> | Backward Compatibility | <Full / Partial / Breaking> |
> | XRD Version Change | <None / Patch / Minor / Major> |
> | Implementation Complexity | <Low / Medium / High> |
> | Migration Required | <Yes / No> |
>
> **Trade-offs:**
> - ✅ <primary advantage>
> - ⚠️ <key limitation or risk>
>
> ---
>
> Which option would you like to proceed with? (A / B / C / Discuss an option)"

**WAIT** for response. If user wants to discuss an option, explain it further and loop. Continue until the user makes a final selection.

### 6.3 Apply Selected Option

Update `.infrakit_tracks/tracks/<track-name>/spec.md` — append an **Architecture Decision** section:

```markdown
## Architecture Decision

**Selected Option**: <Option A/B/C> — <Short Name>
**Rationale**: <why this option was selected>

### Implementation Approach
<detailed description of the chosen design>

### XRD Version Strategy
- Current: `<version>`
- Target: `<version>`
- Rationale: <why this version change>

### Backward Compatibility Notes
<what existing claims will experience during and after the update>
```

> "✅ Architecture option recorded in spec.
>
> Handing off to security review..."

---

## Phase 7: Cloud Security Engineer Review

**Announce:**
> "Reviewing the update specification as the **Cloud Security Engineer**."

Ask which compliance frameworks apply. **WAIT** for response.

**If your harness supports subagents (Claude Code's `Task` tool):**

Invoke the `Task` tool with:

- `description`: `"Cloud Security Engineer audit of update <track-name>"`
- `subagent_type`: `general-purpose`
- `prompt`:

  > You are running a compliance audit against an InfraKit update spec. Do not modify any files. Return only the structured findings.
  >
  > 1. Read `.infrakit/agent_personas/cloud_security_engineer.md` and adopt that persona.
  > 2. Read `.infrakit/context.md` and `.infrakit_tracks/tracks/<track-name>/spec.md` (including the Architecture Decision section).
  > 3. Audit the selected architecture option against the user-chosen frameworks: **{frameworks chosen above}**.
  > 4. Format findings as documented in `.claude/commands/infrakit:security-review.md` Step 6.
  > 5. Return the report as your final message. Do **not** edit `spec.md`.

Paste the report into your reply and proceed to the feedback loop below.

**If your harness does not support subagents (Codex, Gemini, Copilot, generic):**

Read `.infrakit/agent_personas/cloud_security_engineer.md` and adopt that persona inline. Mark the boundary in your reply ("entering Cloud Security Engineer phase"). Audit the selected architecture option against the chosen frameworks and produce the same report format.

**DO NOT modify `spec.md` automatically. Present findings first.**

> "**Security Review Complete**
>
> | Framework | Status | Findings |
> |-----------|--------|----------|
> | <framework> | <COMPLIANT / GAPS FOUND> | <N> findings |
>
> A) **Apply all fixes** — Update spec.md with all remediations
> B) **Apply selected fixes** — Tell me which findings to address
> C) **Waive a finding** — Document with justification
> D) **Discuss** — Explain a finding in detail
> E) **Accept as-is** — Proceed without changes"

**WAIT** for response. Loop until user is satisfied and makes a final choice.

---

## Phase 8: Final Spec Confirmation

Present a combined summary of both reviews:

> "**Update Review Summary**
>
> | Review | Verdict | Outcome |
> |--------|---------|---------|
> | Architecture | <Selected Option Name> | Applied to spec |
> | Security | <COMPLIANT / COMPLIANT_WITH_WAIVERS / ACCEPTED> | <N> findings resolved |
>
> **Final Spec**: `.infrakit_tracks/tracks/<track-name>/spec.md`
>
> A) **Confirm** — Spec is finalized, register the track
> B) **Make changes** — Edit spec now, say 'done' when ready
> C) **Re-run a review** — Return to architect or security review"

**WAIT** for response. Loop until user confirms.

---

## Phase 9: Register Track

Update `.infrakit_tracks/tracks.md` — change the track's Status to `📝 spec-generated`.

> "✅ **Update spec finalized for `<resource-name>`!**
>
> **Track**: `<track-name>`
> **Change Type**: `<Additive/Behavioral/Breaking>`
> **Architecture**: `<Selected Option Name>`
>
> **Files created:**
> - `.infrakit_tracks/tracks/<track-name>/spec.md`
> <if breaking> - `.infrakit_tracks/tracks/<track-name>/migration.md`
>
> **Next step**: Run `/infrakit:plan <track-name>` to generate the implementation plan."

---

## Error Handling

| Error | Action |
|-------|--------|
| Setup files missing | Halt, direct to `/infrakit:setup` |
| Directory not found | Halt, suggest `/infrakit:new_composition` |
| Missing XRD/Composition | Warn, offer options |
| YAML parse errors | Report file and error, halt |
| Breaking change without migration | Generate migration.md automatically |
| Contract files unreadable | Report error, regenerate from YAML |
