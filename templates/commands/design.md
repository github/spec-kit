---
description: Explore implementation options, risks, and gaps before finalizing the technical plan.
handoffs:
  - label: Finalize Technical Plan
    agent: speckit.plan
    prompt: Finalize the implementation plan using the selected design direction.
  - label: Clarify Spec Requirements
    agent: speckit.clarify
    prompt: Clarify specification requirements before design continues
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). Treat it as
planning guidance, constraints, hypotheses, or questions the user wants to explore.

## Goal

Run an exploratory design conversation for the active feature before the final
`__SPECKIT_COMMAND_PLAN__` workflow commits to an implementation plan.

This command is for rubber-ducking, gap finding, and option comparison. It should help
the user make a better technical decision without prematurely writing final plan
artifacts as if all choices are settled.

## Inputs and Context

1. Resolve the active feature using the same feature context as planning:
   - Prefer `SPECIFY_FEATURE_DIRECTORY` when explicitly provided.
   - Otherwise use `.specify/feature.json` when present.
   - Otherwise use branch/spec fallback resolution.
2. Read the active `spec.md`.
3. Read `.specify/memory/constitution.md`.
4. Read `.specify/memory/project-context.md` if it exists.
5. Read `__CONTEXT_FILE__` if it exists, especially the Project Documentation Map.
6. If an existing `plan.md` or `research.md` exists for the feature, read it and treat
   it as prior planning context, not unquestionable truth.

If no active spec can be found, stop and tell the user to run
`__SPECKIT_COMMAND_SPECIFY__` first or provide `SPECIFY_FEATURE_DIRECTORY`.

## Safety Rules

- Do **not** finalize `plan.md` unless the user explicitly asks you to do so.
- Do **not** create `tasks.md`; task generation belongs to `__SPECKIT_COMMAND_TASKS__`.
- Do **not** change implementation code.
- Do **not** override the constitution or project documentation. If project guidance
  conflicts with the spec, call out the conflict and ask for a decision.
- Preserve existing production behavior unless the spec explicitly requires a migration.
- Keep the discussion grounded in the current repository and documented project rules.

## Exploration Workflow

### 1. Spec Understanding

Summarize the feature in plain language:

- Primary user or system goal
- Highest-priority user stories
- Functional requirements that drive technical design
- Success criteria and constraints
- Assumptions that affect implementation
- Any `[NEEDS CLARIFICATION]` markers or implicit unknowns

### 2. Gap and Risk Scan

Identify gaps before proposing solutions:

- Missing or ambiguous requirements
- Domain model uncertainty
- Integration boundaries and shared-package concerns
- Data migration or backwards-compatibility risks
- Security, authorization, privacy, or compliance concerns
- Testing gaps
- Operational/deployment risks
- Performance or scale uncertainty
- Documentation conflicts or stale guidance

For each gap, state whether it blocks planning or can be handled as an assumption.

### 3. Option Generation

Propose 2-3 viable implementation options when meaningful. For each option include:

- Summary
- When this option is appropriate
- Benefits
- Costs/tradeoffs
- Risks
- Testing implications
- Files/modules likely affected at a high level
- How well it aligns with constitution and project context

If only one sensible option exists, explain why alternatives are not worth pursuing.

### 4. Recommendation

Recommend a direction, but do not pretend uncertainty disappeared.

Use this format:

```markdown
## Recommended Direction

Recommended option: [Option name]

Why:
- ...

Known risks:
- ...

Decisions needed from user:
- ...
```

### 5. Conversation Checkpoint

Stop and ask the user to choose or correct the direction before finalizing the plan.

Ask focused questions, not a sprawling interrogation. Prefer 3-5 high-value questions.

Examples:

- Should we optimize for fastest delivery or long-term extensibility?
- Is changing the public API acceptable for this ticket?
- Should shared package changes happen in this repository or another repository first?
- Is a migration/backfill allowed in scope?
- Which option should become the final implementation plan?

## Optional Output File

If the discussion produces useful durable decisions, create or update:

```text
DESIGN_NOTES = <feature-directory>/design.md
```

Use `design.md` for exploratory notes only. It may include:

- Options considered
- Tradeoffs
- Open questions
- User decisions
- Recommended direction

Do not treat `design.md` as a substitute for `plan.md`. Once the user chooses a
direction, `__SPECKIT_COMMAND_PLAN__` should convert the selected design into the final
implementation plan and normal planning artifacts.

## Final Response

Return:

- Active feature path
- Spec summary
- Gaps and risks
- Options considered
- Recommended direction
- Questions for the user
- Whether `design.md` was created or updated
- Clear next step, usually: choose an option, clarify the spec, or run
  `__SPECKIT_COMMAND_PLAN__` after direction is confirmed
