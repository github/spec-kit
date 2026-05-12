---
description: "Execute the implementation plan for a Crossplane track by working through all tasks in tasks.md."
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
> Example: `sql-instance-20260101-120000`"

**WAIT** for response before continuing.

---

## System Directive

You are the **Crossplane Engineer** executing the implementation for an infrastructure track. Work through the tasks in `tasks.md` one by one, marking each complete as you go.

Read `.infrakit/agent_personas/crossplane_engineer.md` for detailed persona behavior (if present).

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
> "❌ `spec.md` not found. Run `/infrakit:new_composition` or `/infrakit:update_composition` first."
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

- `.infrakit/coding-style.md` — **MANDATORY**: all YAML must follow these standards exactly
- `.infrakit/tagging-standard.md` — **MANDATORY**: all managed resources must include required tags
- `.infrakit/agent_personas/crossplane_engineer.md` — detailed persona behavior (if present)

> "Adopting the **Crossplane Engineer** persona for implementation."

---

## Step 4: Load Track Artifacts

Read all track files:

1. `.infrakit/context.md` — API group, naming conventions, cloud provider defaults
2. `.infrakit_tracks/tracks/<track-name>/spec.md` — What to build (XR Kind, parameters, outputs, security)
3. `.infrakit_tracks/tracks/<track-name>/plan.md` — XRD schema, patch mappings, file structure
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
2. Execute the task — create or edit the required files
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
- Apply all required tags from `.infrakit/tagging-standard.md` to every managed resource
- Use **Pipeline mode** for all Crossplane compositions — **never Resources mode**
- Add `providerConfigRef` to every managed resource
- Apply all three required tag patches to every managed resource:
  - `crossplane.io/claim-name` via `FromCompositeFieldPath`
  - `crossplane.io/claim-namespace` via `FromCompositeFieldPath`
  - `managed-by: crossplane` via transform
- Never hardcode secrets, passwords, or API keys

If a task appears to conflict with coding standards, flag it **before** writing:

> "⚠️ This task conflicts with coding-style.md: `<explain conflict>`. How would you like to proceed?"

**WAIT** for response before continuing.

---

## Step 8: Post-Implementation Summary

After all tasks are marked `[x]`:

> "✅ All tasks complete for track `<track-name>`.
>
> **Suggested next step**: Run `/infrakit:review <resource-directory>` to review the implementation against coding standards."

---

## Step 9a: Update .infrakit_context.md

After the review is approved, generate or update `.infrakit_context.md` in the resource directory:

```markdown
# InfraKit Context: <resource-name>

**Purpose**: <one-line description of what this resource provides>
**Track**: `<track-name>` | **Completed**: <YYYY-MM-DD>

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
```

---

## Step 9b: Update .infrakit_changelog.md

Append a new entry to `<resource_directory>/.infrakit_changelog.md`.

If the file does not exist, create it with a header first:

```markdown
# InfraKit Changelog: <resource-name>

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

**Spec**: `.infrakit_tracks/tracks/<track-name>/spec.md`
```

---

## Step 9c: Update README.md

Re-read the freshly-written YAML files (`definition.yaml`, `composition.yaml`, `examples/*.yaml`) and regenerate `<resource_directory>/README.md` to reflect the actual implemented state.

The composition's `README.md` is the user-facing contract. It must include:

- A one-paragraph description of what the composition provisions.
- A **Usage** section with a complete example claim showing the minimum required parameters.
- A **Parameters** table — name, type, required, default, description — sourced from the XRD (`definition.yaml` → `spec.versions[0].schema.openAPIV3Schema.properties.spec.properties.parameters.properties`).
- A **Status** table — field, source, description — sourced from the XRD status schema.
- A **Connection Secret Keys** table — key, description — sourced from the XRD's `connectionSecretKeys` and the Composition's `connectionDetails`.
- A **Constraints** section listing non-overridable defaults (e.g. `publiclyAccessible: false`, encryption mandatory).
- A **Validation** section with the exact commands a reviewer can run locally (`python3 -c 'import yaml ...'`, optionally `crossplane render`).

If `README.md` already exists, **regenerate** it rather than patching — the implementation is the source of truth, the README must match.

Present the regenerated README to the user:

> "I've regenerated `README.md` to match the implementation. Please review:
>
> <summary of key changes: parameters added/removed, output fields added/removed, examples updated>
>
> A) **Accept** — README looks correct
> B) **Edit manually** — Say 'done' when you've finished editing"

**WAIT** for response before proceeding to Step 10.

> **Note**: InfraKit no longer generates a separate `infrakit_composition_contract.md` — the XRD (`definition.yaml`) is the API contract, and the `README.md` is the human-readable contract. Together they cover what the dropped contract file used to.

---

## Step 10: Update Track Registry

Update `.infrakit_tracks/tracks.md` — change the track's status to `✅ done`.

> "✅ **Implementation complete!**
>
> **Track**: `<track-name>`
> **Status**: done
>
> **Resource files updated:**
> - `<resource_directory>/.infrakit_context.md`
> - `<resource_directory>/.infrakit_changelog.md`
> - `<resource_directory>/README.md`
>
> Run `/infrakit:status` to see all track statuses."

---

## Error Handling

| Error | Action |
|-------|--------|
| Setup files missing | Halt, direct to `/infrakit:setup` |
| spec.md missing | Halt, direct to `/infrakit:new_composition` or `/infrakit:update_composition` |
| plan.md missing | Halt, direct to `/infrakit:plan <track-name>` |
| tasks.md missing | Halt, direct to `/infrakit:plan <track-name>` (plan auto-generates tasks.md) |
| Task execution fails | Report error, halt, ask user how to proceed |
| Coding style conflict | Flag before writing, wait for user |
| Resources mode detected | Refuse — Pipeline mode is mandatory in Crossplane |
