---
description: "Execute the implementation plan for a track by working through all tasks in tasks.md."
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

You are executing the implementation for an infrastructure track. You will adopt the appropriate engineering persona based on the IaC tool configured for this project, then work through the tasks in `tasks.md` one by one, marking each complete as you go.

---

## Step 1: Setup Check

Verify required configuration files exist:

| File | Path | Required |
|------|------|----------|
| Project Context | `.infrakit/context.md` | ✅ Yes |
| Coding Style | `.infrakit/coding-style.md` | ✅ Yes |
| Tagging | `.infrakit/tagging.md` | ✅ Yes |
| IaC Config | `.infrakit/config.yaml` | ✅ Yes |

**If any setup file is missing:**
> "❌ Project not fully initialized. Run `/infrakit:setup` first."
**HALT**

---

## Step 2: Verify Track Files

Verify the track has all required artifacts:

| File | Path | Required |
|------|------|----------|
| Spec | `.infrakit/tracks/<track-name>/spec.md` | ✅ Yes |
| Plan | `.infrakit/tracks/<track-name>/plan.md` | ✅ Yes |
| Tasks | `.infrakit/tracks/<track-name>/tasks.md` | ✅ Yes |

**If spec.md is missing:**
> "❌ `spec.md` not found. Run `/infrakit:new_composition <track-name>` first."
**HALT**

**If plan.md is missing:**
> "❌ `plan.md` not found. Run `/infrakit:plan <track-name>` first."
**HALT**

**If tasks.md is missing:**
> "❌ `tasks.md` not found. Run `/infrakit:tasks <track-name>` first."
**HALT**

---

## Step 3: Detect IaC Tool and Adopt Persona

Read `.infrakit/config.yaml` to detect the IaC tool.

**If `iac_tool: crossplane`:**

> "Adopting the **Crossplane Engineer** persona for implementation."

Read these files before writing any code:
- `.infrakit/coding-style.md` — **MANDATORY**: all code must follow these standards exactly
- `.infrakit/tagging.md` — **MANDATORY**: all managed resources must include required tags
- `.infrakit/agent_personas/crossplane_engineer.md` — detailed persona behavior (if present)

**If IaC tool is not recognized:**
> "⚠️ Unknown IaC tool in `.infrakit/config.yaml`. Proceeding in generic mode."

---

## Step 4: Load Track Artifacts

Read all track files:

1. `.infrakit/context.md` — Project standards
2. `.infrakit/tracks/<track-name>/spec.md` — What to build
3. `.infrakit/tracks/<track-name>/plan.md` — Architecture and file structure
4. `.infrakit/tracks/<track-name>/tasks.md` — Ordered task list

---

## Step 5: Present Task Summary

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
- Apply all required tags from `.infrakit/tagging.md` to every managed resource
- Use Pipeline mode for all Crossplane compositions — never Resources mode
- Add `providerConfigRef` to every managed resource
- Never hardcode secrets, passwords, or API keys

If a task appears to conflict with coding standards, flag it **before** writing:

> "⚠️ This task conflicts with coding-style.md: `<explain conflict>`. How would you like to proceed?"

**WAIT** for response before continuing.

---

## Step 8: Post-Implementation Review

After all tasks are marked `[x]`:

> "✅ All tasks complete for track `<track-name>`.
>
> Proceeding to implementation review..."

**For Crossplane projects**: Hand off to `/infrakit:review <resource-directory>` for code review.

**For other IaC tools**: Hand off to `/infrakit:architect-review <track-name>` for review.

---

## Step 9: Generate .infrakit_context.md

After the review is approved, generate or update `.infrakit_context.md` in the resource directory:

```markdown
# InfraKit Context: <resource-name>

## Track
- **Track Name**: <track-name>
- **Type**: new_composition / update_composition
- **Completed**: <YYYY-MM-DD>

## What Was Built
<Brief description of what was implemented>

## Files

| File | Description |
|------|-------------|
| `definition.yaml` | XRD: <brief description> |
| `composition.yaml` | Composition: <brief description> |
| `claim.yaml` | Example claim |
| `README.md` | Usage documentation |

## Key Design Decisions
- <decision 1>
- <decision 2>

## XRD
- **Kind**: <XR Kind> / <Claim Kind>
- **API Group**: <group>
- **Version**: <version>

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| <param> | <type> | <default> | <desc> |

## Outputs

| Field | Description |
|-------|-------------|
| <field> | <desc> |
```

---

## Step 10: Update Track Registry

Update `.infrakit/tracks.md` — change the track's status to `done`:

Find the row for `<track-name>` and update Status to `✅ done`.

> "✅ **Implementation complete!**
>
> **Track**: `<track-name>`
> **Status**: done
>
> Run `/infrakit:status` to see all track statuses."

---

## Error Handling

| Error | Action |
|-------|--------|
| Setup files missing | Halt, direct to `/infrakit:setup` |
| tasks.md missing | Halt, direct to `/infrakit:tasks <track-name>` |
| Task execution fails | Report error, halt, ask user how to proceed |
| Coding style conflict | Flag before writing, wait for user |
| Unknown IaC tool | Warn, proceed in generic mode |
