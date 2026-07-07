---
description: "Create role-isolated SDD handoff records between specify, plan, tasks, and implementation roles."
---

# AI Team Role Handoff

Create a document handoff between SDD roles. This command is commonly run after
`speckit.specify`, and may also be used between plan, tasks, and implementation
when a phase needs explicit human approval.

## User Input

```text
$ARGUMENTS
```

## Goal

Prevent hidden context sharing between AI roles. The product/customer manager,
architect, and developer agents must communicate through written artifacts.

## Steps

1. Locate the active feature directory from `.specify/feature.json`.
2. Read:
   - `.specify/ai-team/tasks/<task-id>/task-context.yml` and `context-pack.md` when
     present;
   - `spec.md`;
   - `plan.md` if present;
   - `tasks.md` if present;
   - the coding issue or handoff requirement URL referenced by the feature;
   - `.specify/extensions/ai-team/ai-team-config.yml` when present.
3. Decide the handoff direction:
   - specify to plan;
   - plan to tasks;
   - tasks to implement;
   - implementation to evidence;
   - unclear.
4. Create or update `.specify/ai-team/handoffs/<feature-slug>/<phase>.md`.
5. Include only information the next role should know. Do not copy raw customer
   or private commercial context into a public coding repository handoff unless
   the workspace contract allows it.
6. For feature work, include the coding issue or allowed handoff requirement as
   the authoritative work item. A local file path may be listed only as a
   supporting source that was read.
7. Update the Task Context Package with the handoff artifact path, current
   phase, and next command.

## Handoff Shape

```markdown
# AI Team Handoff: <phase>

- **Feature**:
- **Task ID**:
- **Context Path**:
- **From role**:
- **To role**:
- **Source artifacts**:
- **Coding issue or handoff requirement URL**:
- **Allowed context**:
- **Private context excluded**:
- **Decision status**:

## What the next role may rely on

## What remains uncertain

## Scope and non-goals

## Approval required before next phase

## Evidence expected in the next phase

## Stop conditions
```

## Stop Conditions

Stop and ask when:

- the active feature directory cannot be located;
- the next role cannot be identified;
- private demand would leak into a public plan or coding artifact;
- approval is required before the next phase but no approver is named.
