# Idea Assessment Quickstart

Use this process to decide whether an idea deserves investment before committing
to a solution. It works for software ideas and non-software decisions alike.
No existing source code is required.

The bundled, opt-in **assess** extension provides five stages:
**intake → research → define → shape → decide**. The result is an evidence-backed
`go`, `needs-clarification`, or `kill` decision, not an implementation.

## Set up

[Install Spec Kit and initialize a project](../installation.md). An empty project
is enough, or you can use an
[existing repository](existing-projects.md) when the idea relates to its code.
In a terminal at the initialized project root, install the extension:

```bash
specify extension add assess
```

Then launch your coding agent in that directory. The examples below use
GitHub Copilot's default skills mode (`--integration copilot`). Other agents
use their own
[command invocation syntax](../reference/integrations.md#command-invocation).
Run each command separately in the agent, not in your terminal, reviewing the
artifact before moving on.

## 1. Capture the idea

```text
/speckit-assess-intake "Let users work offline and sync when they reconnect." slug=offline-mode
```

You can also supply a URL, ticket, or codebase pointer. The agent captures the
input in `.specify/assessments/offline-mode/intake.md`.
The slug is the shared handle for all five stages.

## 2. Research the evidence

```text
/speckit-assess-research slug=offline-mode
```

The agent gathers supporting and opposing evidence in `research.md`. Review
sources and confidence levels: uncited assumptions are not established facts.
This stage should challenge the idea, not just build a case for it.

## 3. Define the problem

```text
/speckit-assess-define slug=offline-mode
```

The agent writes `problem.md`, describing the affected users, problem, goals,
non-goals, success metrics, and cost of doing nothing.

## 4. Shape possible solutions

```text
/speckit-assess-shape slug=offline-mode
```

The agent compares concept-level options, constraints, appetite, and trade-offs
in `concept.md`. Detailed architecture, implementation tasks, and source changes
are deliberately outside this process.

## 5. Make the decision

```text
/speckit-assess-decide slug=offline-mode
```

The agent records the scorecard, rationale, and verdict in `decision.md`.

| Verdict | What it means | What to do |
| --- | --- | --- |
| `go` | The problem and evidence are adequate and a concept is recommended | Decide whether to act; optionally hand a software idea to SDD |
| `needs-clarification` | Specific unknowns still block a defensible decision | Refine the affected artifacts with the missing information |
| `kill` | The idea is not worth pursuing now | Keep the recorded rationale; stopping is a successful outcome |

All five artifacts live under `.specify/assessments/offline-mode/`. None of the
assessment commands modify source code.

## Resolve unknowns by refining the artifacts

The usual flow runs each command once. When an artifact contains
`[NEEDS CLARIFICATION: ...]`, edit that Markdown file directly or ask the agent
in free-form chat to incorporate the missing information:

```text
Update .specify/assessments/offline-mode/problem.md with these confirmed success metrics: <your metrics>. Update any dependent wording and revise decision.md if this resolves the blocker. Preserve source and confidence tags.
```

Do not automatically regenerate the entire stage. Ask the agent to review
whether the new facts clear the blocker and revise the downstream scorecard,
verdict, or handoff accordingly. Rerunning a command is an exception, such as
replacing a discarded draft, and existing artifacts must not be overwritten
without confirmation.

## Optional handoff to SDD

Assessment is standalone: it does not automatically invoke SDD or insert itself
into the specification process. If you choose to build a software idea with a
`go` verdict, establish your project constitution if needed, then pass the
decision's handoff summary to the specification command:

```text
/speckit-specify Use the handoff summary in .specify/assessments/offline-mode/decision.md to specify the approved offline-mode concept.
```

Continue with the [SDD quickstart](../quickstart.md). For stage prerequisites,
slug rules, and evidence requirements, see the
[idea assessment command reference](../reference/agentic-assessment.md).
