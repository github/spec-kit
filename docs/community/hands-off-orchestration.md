# Hands-Off Orchestration Example

This example shows how to ask an AI coding agent to run a hands-off, artifact-first Spec Kit flow without moving into issue creation or implementation by default.

Use this pattern when you want a repeatable planning pass that produces reviewed artifacts first:

```text
/speckit.specify -> /speckit.clarify -> /speckit.checklist -> /speckit.plan -> /speckit.tasks -> /speckit.analyze
```

This ordering matches the [Quick Start Guide](../quickstart.md) workflow, where `/speckit.checklist` is a requirements-quality gate before `/speckit.plan` (if you are following a workflow that runs `/speckit.plan` before `/speckit.checklist`, swap those two steps).

The key rule is that the agent stops after analysis unless the user explicitly asks it to continue.

> [!NOTE]
> This conservative example uses only `README.md` and `DESIGN.md` as in-repo guidance sources unless the user explicitly provides more context.

## Guardrails

- Generate and review artifacts before creating issues or writing code.
- Ask the user when a product decision is required.
- Loop back to an earlier stage when a later stage finds stale, incomplete, or inconsistent artifacts.
- Use only `README.md` and `DESIGN.md` as in-repo guidance sources unless the user explicitly provides more context.
- Do not run `/speckit.taskstoissues` unless the user explicitly requests issue creation.
- Do not run `/speckit.implement` unless the user explicitly requests implementation.

## Example Agent Prompt

Copy this prompt into your agent after initializing a Spec Kit project:

```text
Run an artifact-first Spec Kit orchestration flow for the following feature:

<describe the feature here>

Follow this sequence:

1. Run /speckit.specify for the requested feature.
2. Run /speckit.clarify to identify ambiguity. If a real product decision is required, stop and ask me before continuing.
3. Run /speckit.checklist and fix requirement-quality gaps by looping back to /speckit.clarify or /speckit.specify as needed.
4. Run /speckit.plan after the specification passes the requirements checklist.
5. Run /speckit.tasks after the plan and checklist are consistent.
6. Run /speckit.analyze to check cross-artifact consistency.
7. Stop after analysis and report the generated artifacts, open questions, and recommended next step.

Use only README.md and DESIGN.md as in-repo guidance sources unless I explicitly provide more context.
Do not create GitHub issues unless I explicitly ask for issue creation.
Do not implement tasks unless I explicitly ask for implementation.
```

## Optional Follow-Up Prompts

After reviewing the generated artifacts, continue with one of these explicit prompts:

```text
Run /speckit.taskstoissues to create GitHub issues from the generated tasks, but do not implement them.
```

```text
Run /speckit.implement to implement the generated tasks now.
```

Keeping issue creation and implementation as separate follow-up prompts makes the default flow safe for planning, design review, and handoff scenarios.

## When To Use This Pattern

Use this pattern when:

- A team lead wants implementation-ready artifacts before assigning work.
- A project wants consistent specs, plans, and tasks for every feature request.
- The feature has enough ambiguity that clarification and checklist passes are useful.
- You want automation to prepare work, but not silently create issues or write code.

For smaller experiments, the shorter workflow in the [Quick Start Guide](../quickstart.md) may be enough.
