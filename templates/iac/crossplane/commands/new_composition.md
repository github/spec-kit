---
description: "Create a new Crossplane resource composition through a multi-persona solutioning and review workflow."
argument-hint: "<resource-name> <resource-directory>"
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

Parse `$ARGUMENTS` for resource name and directory. If either is missing, ask for them (one at a time).

---

## System Directive

You are guiding the user through creating a new Crossplane resource composition. This command orchestrates a multi-persona workflow: Cloud Solutions Engineer → Cloud Architect Review → Cloud Security Engineer Review → spec confirmed.

**CRITICAL**: Ask only one question at a time. Wait for a response before asking the next question.

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

### 1.2 Read Configuration

Read `.infrakit/context.md`, `.infrakit/coding-style.md`, and `.infrakit/tagging-standard.md` before proceeding.

---

## Phase 2: Argument Collection

### 2.1 Resource Name

If not provided in `$ARGUMENTS`, ask:

> "What is the name for this resource?
>
> Examples: `database`, `redis-cache`, `object-storage`"

**WAIT** for response.

### 2.2 Resource Directory

If not provided, ask:

> "Where should the composition files be created?
>
> Example: `./resources/database`"

**WAIT** for response.

### 2.3 Validate Directory

Check if the directory exists and is non-empty:

```bash
test -d <resource_directory> && ls -A <resource_directory>
```

**If the directory is NOT empty:**

> "⚠️ The directory `<resource_directory>` already contains files.
>
> A) **Continue** — files may be overwritten
> B) **Choose a different directory**
> C) **Use update instead** — Run `/infrakit:update_composition` to modify existing resources
> D) **Cancel**"

**WAIT** for response.

**If the directory does not exist**, create it:
```bash
mkdir -p <resource_directory>
```

### 2.4 Create Track

Generate a track name: `<resource-name>-<YYYYMMDD-HHMMSS>`

Example: `database-20260101-120000`

Create the track directory:
```bash
mkdir -p .infrakit_tracks/tracks/<track-name>
```

Register in `.infrakit_tracks/tracks.md` — add a row with Status `🔵 initializing`.

> "✅ Track created: `<track-name>`
> Location: `.infrakit_tracks/tracks/<track-name>/`"

---

## Phase 3: Cloud Solutions Engineer — Spec Generation

**Adopt the Cloud Solutions Engineer persona.**

Read `.infrakit/agent_personas/cloud_solutions_engineer.md` for detailed behavior.

> "I'll now guide you through creating a specification for this resource.
> Acting as the **Cloud Solutions Engineer**, I'll ask clarifying questions."

### 3.1 Initial Questions

**Question 1: Description**

> "Please describe what this resource should do.
>
> Examples:
> - 'A PostgreSQL database with daily backups and encryption at rest'
> - 'An S3 bucket for storing application logs with versioning'
> - 'A Redis cache with private network access and auto-scaling'
>
> Describe your resource:"

**WAIT** for response.

**Question 2: Cloud Provider**

> "Which cloud provider should this resource use?
>
> A) AWS
> B) Azure
> C) GCP
>
> **Note**: This resource will be implemented for a single cloud provider. The project default from context.md is `<provider from context.md>`."

**WAIT** for response.

### 3.2 Service Disambiguation

If the user's description maps to multiple possible services, present each option in a structured table and ask the user to choose before continuing.

### 3.3 Requirements Questions

Ask the following questions, one at a time:

**Question 3: Environment**

> "What environment is this for?
>
> A) Development (minimal cost, single instance)
> B) Staging (production-like, but smaller)
> C) Production (HA, encrypted, secure)
> D) Flexible (user specifies at claim time)"

**WAIT** for response.

**Question 4: Security Requirements**

Generate security options relevant to the resource type and cloud provider. Always include 'Type your own requirements' as the last option.

**WAIT** for response.

**Question 5: Parameters**

Generate parameter options relevant to the resource type. These are the fields the user will configure at claim time.

**WAIT** for response.

**Question 6: Outputs**

Generate output options relevant to the resource type. These are the status fields exposed after the resource is created.

**WAIT** for response.

### 3.4 Generate spec.md

Write to `.infrakit_tracks/tracks/<track-name>/spec.md`:

```markdown
# Specification: <Resource Name>

## Description
<What this resource provides — in business/user terms>

## Cloud Provider
**Provider**: <provider>
**Service**: <specific service>

## Project Type
Greenfield (Create new)

## Resource Type
- [ ] Claim (namespace-scoped, backed by cluster-scoped XR)
- [ ] XR only — cluster-scoped

## How It Should Work
<Expected behavior from a user's perspective>

## User Inputs (Parameters)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| <param> | <type> | <yes/no> | <default> | <what it controls> |

## Expected Outputs (Status)

| Field | Type | Description |
|-------|------|-------------|
| <field> | <type> | <what information is provided> |

## Connection Secret Keys

| Key | Description |
|-----|-------------|
| <key> | <description> |

## Security Requirements
- <requirement 1>
- <requirement 2>

## Configuration Constraints
- <constraint 1>
- <constraint 2>

## Acceptance Criteria
- [ ] User can create resource with minimal configuration
- [ ] All required security measures are enforced
- [ ] Status reflects actual resource state
- [ ] Connection secrets published (if applicable)
- [ ] Errors are clearly reported
```

### 3.5 Spec Feedback Loop

> "I've generated the specification.
>
> **File**: `.infrakit_tracks/tracks/<track-name>/spec.md`
>
> What would you like to do?
>
> A) **Regenerate** — Tell me what to change and I'll regenerate
> B) **Manual Changes** — Edit the file yourself, say 'done' when ready
> C) **Proceed** — Looks good, move to architect review"

**WAIT** for response. Loop until user chooses C.

---

## Phase 4: Cloud Architect Review

**Announce the handoff:**

> "Handing off to architecture review..."
> "Reviewing the specification as the **Cloud Architect**."

Read `.infrakit/agent_personas/cloud_architect.md` for detailed behavior.

Run the architecture review inline:

1. Read `.infrakit_tracks/tracks/<track-name>/spec.md`
2. Check: structural security flags, cost, reliability, architecture correctness, completeness
3. Present findings as a structured report (see `/infrakit:architect-review` for report format)

**DO NOT modify spec.md automatically. Present findings first.**

> "**Architecture Review Complete**
>
> What would you like to do?
>
> A) **Apply recommendations** — I'll update spec.md
> B) **Skip** — Proceed without changes
> C) **Discuss** — Explain a specific finding"

**WAIT** for response. Apply changes if requested, then confirm.

---

## Phase 5: Cloud Security Engineer Review

**Announce the handoff:**

> "Handing off to security review..."
> "Reviewing the specification as the **Cloud Security Engineer**."

Read `.infrakit/agent_personas/cloud_security_engineer.md` for detailed behavior.

**Ask which compliance frameworks apply** (see Step 3 of `/infrakit:security-review` for the framework selection question).

**WAIT** for response.

Run the compliance audit inline. Present findings as a structured report.

**DO NOT modify spec.md automatically. Present findings first.**

> "**Security Review Complete**
>
> What would you like to do?
>
> A) **Apply fixes** — I'll update spec.md
> B) **Waive a finding** — Document an exception with justification
> C) **Skip** — Proceed without changes"

**WAIT** for response. Apply changes or document waivers if requested.

---

## Phase 6: Debate and Final Spec Confirmation

Present a combined summary of both reviews:

> "**Review Summary for `<resource-name>`**
>
> | Review | Verdict | Issues |
> |--------|---------|--------|
> | Architecture | <verdict> | <N> findings |
> | Security | <verdict> | <N> findings |
>
> **Recommended changes applied**: <list>
> **Waived**: <list>
>
> Please review the final spec:
> **File**: `.infrakit_tracks/tracks/<track-name>/spec.md`
>
> What would you like to do?
>
> A) **Confirm** — Spec is finalized, proceed
> B) **Make changes** — Edit the spec, say 'done' when ready
> C) **Re-run a review** — Run architect or security review again"

**WAIT** for response. Loop until user confirms.

---

## Phase 7: Register Track as Spec-Generated

Update `.infrakit_tracks/tracks.md` — change the track's Status to `📝 spec-generated`.

> "✅ **Spec finalized for `<resource-name>`!**
>
> **Track**: `<track-name>`
> **Files created:**
> - `.infrakit_tracks/tracks/<track-name>/spec.md` — Specification
>
> **Next step**: Run `/infrakit:plan <track-name>` to generate the implementation plan."

---

## Error Handling

| Error | Action |
|-------|--------|
| Setup files missing | Halt, direct to `/infrakit:setup` |
| Directory not empty | Warn, present options |
| Directory creation fails | Report error, suggest manual creation |
| User rejects spec | Ask for specific changes, revise |
| Breaking change detected in security review | Require explicit waiver with justification |
