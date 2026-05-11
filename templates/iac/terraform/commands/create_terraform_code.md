---
description: "Create a new Terraform module through a multi-persona solutioning and review workflow."
argument-hint: "<module-name> <module-directory>"
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

Parse `$ARGUMENTS` for module name and directory. If either is missing, ask for them (one at a time).

---

## System Directive

You are guiding the user through creating a new Terraform module. This command orchestrates a multi-persona workflow: Cloud Solutions Engineer → Cloud Architect Review → Cloud Security Engineer Review → spec confirmed.

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

### 2.1 Module Name

If not provided in `$ARGUMENTS`, ask:

> "What is the name for this module?
>
> Examples: `database`, `redis-cache`, `object-storage`, `vpc`"

**WAIT** for response.

### 2.2 Module Directory

If not provided, ask:

> "Where should the module files be created?
>
> Example: `./modules/database`"

**WAIT** for response.

### 2.3 Validate Directory

Check if the directory exists and is non-empty:

```bash
test -d <module_directory> && ls -A <module_directory>
```

**If the directory is NOT empty:**

> "⚠️ The directory `<module_directory>` already contains files.
>
> A) **Continue** — files may be overwritten
> B) **Choose a different directory**
> C) **Use update instead** — Run `/infrakit:update_terraform_code` to modify existing modules
> D) **Cancel**"

**WAIT** for response.

**If the directory does not exist**, create it:
```bash
mkdir -p <module_directory>
```

### 2.4 Create Track

Generate a track name: `<module-name>-<YYYYMMDD-HHMMSS>`

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

This phase is **interactive** — you and the user iterate on requirements via clarifying questions. Run it **inline** in your current context regardless of whether your harness supports subagents: a subagent can't pause to wait for user input, so a `Task`-style delegation would either guess answers or hang.

Adopt the Cloud Solutions Engineer persona by reading `.infrakit/agent_personas/cloud_solutions_engineer.md` and following its behaviour for the duration of Phase 3. When Phase 4 begins, the persona will be swapped (and on Claude Code, the entire review will run in an isolated subagent — see Phase 4 below).

> "I'll now guide you through creating a specification for this module.
> Acting as the **Cloud Solutions Engineer**, I'll ask clarifying questions."

### 3.1 Initial Questions

**Question 1: Description**

> "Please describe what this module should provision.
>
> Examples:
> - 'An RDS PostgreSQL instance with daily backups and encryption at rest'
> - 'An S3 bucket for storing application logs with versioning enabled'
> - 'An ElastiCache Redis cluster with private network access'
>
> Describe your module:"

**WAIT** for response.

**Question 2: Cloud Provider**

> "Which cloud provider should this module target?
>
> A) AWS
> B) Azure
> C) GCP
>
> **Note**: The project default from context.md is `<provider from context.md>`."

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
> D) Flexible (user specifies via input variable)"

**WAIT** for response.

**Question 4: Security Requirements**

Generate security options relevant to the resource type and cloud provider. Always include 'Type your own requirements' as the last option.

**WAIT** for response.

**Question 5: Input Variables**

Generate input variable options relevant to the resource type. These are the fields the caller will configure when using the module.

**WAIT** for response.

**Question 6: Outputs**

Generate output options relevant to the resource type. These are the values the module will expose after provisioning.

**WAIT** for response.

### 3.4 Generate spec.md

Write to `.infrakit_tracks/tracks/<track-name>/spec.md`:

```markdown
# Specification: <Module Name>

## Description
<What this module provisions — in business/user terms>

## Cloud Provider
**Provider**: <provider>
**Service**: <specific service>

## Project Type
Greenfield (Create new)

## How It Should Work
<Expected behavior from a user's perspective>

## Input Variables

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| <var> | <type> | <yes/no> | <default> | <what it controls> |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| <output> | <type> | <what value is exposed> |

## Security Requirements
- <requirement 1>
- <requirement 2>

## Configuration Constraints
- <constraint 1>
- <constraint 2>

## Acceptance Criteria
- [ ] Caller can use module with minimal variable configuration
- [ ] All required security measures are enforced
- [ ] Outputs expose all values needed by callers
- [ ] No hardcoded secrets or credentials
- [ ] Errors are clearly surfaced via Terraform validation
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

## Phase 4: Cloud Architect Review (delegated when subagents are available)

This phase is **read-only against a finalised spec** — no user input is required mid-flight. That makes it the right shape to delegate to a subagent, which gives the architect's reasoning its own context window. Without delegation, the architect's prompt sees the entire Solutions Engineer Q&A history, which biases the review toward the answers already given.

**If your harness supports subagents (Claude Code's `Task` tool):**

Invoke the `Task` tool with:

- `description`: `"Cloud Architect review of <track-name>"`
- `subagent_type`: `general-purpose`
- `prompt`:

  > You are running an architecture review against an InfraKit track. Do not modify any files. Return only the structured report.
  >
  > 1. Read `.infrakit/agent_personas/cloud_architect.md` and adopt that persona for this entire task.
  > 2. Read `.infrakit/context.md`, `.infrakit/coding-style.md`, `.infrakit/tagging-standard.md`.
  > 3. Read `.infrakit_tracks/tracks/<track-name>/spec.md`.
  > 4. Produce findings against the spec covering: structural security flags, cost, reliability, architecture correctness, completeness, environment-awareness.
  > 5. Format the report exactly as documented in `.claude/commands/infrakit:architect-review.md` Step 6 (header, verdict, findings table, structural security flags, architecture correctness, reliability, cost, completeness).
  > 6. Return the report as your final message. Do **not** edit `spec.md`.

When the subagent returns its report, paste it in your reply to the user and continue with the feedback loop below.

**If your harness does not support subagents (Codex, Gemini, Copilot, generic):**

Switch context inline. Read `.infrakit/agent_personas/cloud_architect.md` and adopt that persona explicitly. Mark the boundary in your reply ("entering Cloud Architect phase") so the user can see the role switch. Then run the same review and produce the same report format as above. Return to the orchestrator persona before continuing.

---

In either case, **DO NOT modify `spec.md` automatically. Present findings first.**

> "**Architecture Review Complete**
>
> What would you like to do?
>
> A) **Apply recommendations** — I'll update spec.md
> B) **Skip** — Proceed without changes
> C) **Discuss** — Explain a specific finding"

**WAIT** for response. Apply changes if requested, then confirm.

---

## Phase 5: Cloud Security Engineer Review (delegated when subagents are available)

Same shape as Phase 4: read-only audit against a finalised spec, so it benefits from subagent isolation when available. The one nuance is the **framework-selection question** — that has to happen *before* the subagent is invoked, because subagents can't wait for user input.

### 5.1 Select compliance frameworks (inline, with user)

> "Which security compliance frameworks apply to this resource? Select all that apply: SOC 2, HIPAA, ISO 27001, CIS, NIST, PCI-DSS, or 'None'."

**WAIT** for response.

### 5.2 Run the audit

**If your harness supports subagents (Claude Code's `Task` tool):**

Invoke the `Task` tool with:

- `description`: `"Cloud Security Engineer audit of <track-name>"`
- `subagent_type`: `general-purpose`
- `prompt`:

  > You are running a compliance audit against an InfraKit track. Do not modify any files. Return only the structured report.
  >
  > 1. Read `.infrakit/agent_personas/cloud_security_engineer.md` and adopt that persona for this entire task.
  > 2. Read `.infrakit/context.md` and `.infrakit_tracks/tracks/<track-name>/spec.md`.
  > 3. Audit the spec against the following compliance frameworks: **{frameworks chosen by the user in step 5.1}**.
  > 4. Format the report exactly as documented in `.claude/commands/infrakit:security-review.md` Step 6 (header, verdict, findings table with severity, control coverage tables per framework, waiver section).
  > 5. Return the report as your final message. Do **not** edit `spec.md`.

When the subagent returns its report, paste it in your reply to the user and continue with the feedback loop below.

**If your harness does not support subagents (Codex, Gemini, Copilot, generic):**

Switch context inline. Read `.infrakit/agent_personas/cloud_security_engineer.md` and adopt that persona explicitly. Mark the boundary in your reply ("entering Cloud Security Engineer phase"). Run the audit against the selected frameworks and produce the same report format as above. Return to the orchestrator persona before continuing.

---

**DO NOT modify `spec.md` automatically. Present findings first.**

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

> "**Review Summary for `<module-name>`**
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

> "✅ **Spec finalized for `<module-name>`!**
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
