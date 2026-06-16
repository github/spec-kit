# Handling Complex Features

Large or complex features often run smoothly through `/speckit.specify`,
`/speckit.plan`, and `/speckit.tasks`, then degrade during implementation. In
the middle of a long `/speckit.implement` run, agents can start to lose track of
the plan, ignore tasks, or hallucinate — usually right before or after context
compaction is triggered.

The underlying cause is context window exhaustion. When a single
implementation run tries to hold the entire feature in context, the model
degrades as the window fills. The fix is to scope each run so it stays well
within context limits.

The `/speckit.implement` command accepts free-form user input that the agent
must consider before proceeding. This means you can scope each run without any
tooling changes.

## Option 1: Limit How Many Tasks Run Per Invocation

Instead of letting `/speckit.implement` run through every task at once, tell it
to stop early:

```text
/speckit.implement only execute tasks T001-T010, then stop and report progress
```

or scope by phase:

```text
/speckit.implement only execute the Setup phase, then stop
```

Because completed tasks are marked `[X]` in `tasks.md`, the next
`/speckit.implement` invocation picks up where you left off. This keeps each run
well within context limits.

## Option 2: Instruct the Agent to Use Sub-Agents

If your coding agent supports sub-agents (for example, GitHub Copilot CLI or the
GitHub Copilot extension for VS Code), you can instruct `/speckit.implement` to
delegate individual tasks:

```text
/speckit.implement delegate each parallel [P] task to a sub-agent
```

Each sub-agent gets a focused context — one task plus the relevant plan
excerpts — rather than the full feature context, so compaction never triggers
in the main session.

## Option 3: Combine Both

For very large features, combine scoping and delegation:

```text
/speckit.implement execute only the Core phase, delegate [P] tasks to sub-agents
```

## Option 4: Decompose the Feature Into Smaller Specs

When even a single phase overwhelms the context, break the feature into
independently specified sub-features. Each sub-feature gets its own
`spec.md`, `plan.md`, and `tasks.md`, and runs through its own
specify/plan/tasks/implement cycle.

This is the "spec of specs" approach: the first iteration breaks a massive
feature into smaller, self-contained specs that can each be implemented without
overwhelming the model. It adds the most overhead, so reserve it for features
that are too large to handle any other way.

## Which Approach to Choose

| Approach | Best for |
| --- | --- |
| Limit to N tasks or a phase | Any agent; simplest; no sub-agent support needed |
| Sub-agent delegation | Agents that support sub-agents; maximizes parallelism |
| Combine scoping + delegation | Large features on sub-agent-capable agents; balances both |
| Decompose into smaller specs | When even a single phase overwhelms the context |

For most cases, limiting task scope per run is the simplest fix. Reach for
sub-agent delegation when your agent supports it and you want parallelism, and
decompose into smaller specs only when a single phase is still too large to
handle in one run.
