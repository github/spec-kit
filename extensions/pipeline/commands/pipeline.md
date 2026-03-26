---
description: "Run the full speckit workflow end-to-end (specify → clarify → plan → tasks → analyze → implement) with automatic progression between steps."
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pipeline Overview

This command orchestrates the full Spec-Driven Development workflow automatically. You MUST execute each step in sequence by invoking the corresponding `/speckit.*` command. After each step completes, proceed immediately to the next one WITHOUT returning control to the user, UNLESS a step explicitly requires user input (e.g., clarification questions).

**Pipeline Steps:**

1. `/speckit.specify` — Create feature specification
2. `/speckit.clarify` — Resolve ambiguities (interactive: user answers questions)
3. `/speckit.plan` — Generate technical plan
4. `/speckit.tasks` — Break plan into actionable tasks
5. `/speckit.analyze` — Cross-artifact consistency analysis
6. `/speckit.implement` — Execute all tasks

## Execution Rules

### Auto-Progression (CRITICAL)

- After each step completes successfully, **immediately invoke the next step**. Do NOT ask the user "shall I proceed?" or "ready for the next step?". Just do it.
- The ONLY reasons to pause are:
  - A step requires user input (e.g., `/speckit.clarify` asking clarification questions, or `/speckit.implement` asking about incomplete checklists)
  - `/speckit.analyze` reports CRITICAL issues (ask user whether to proceed or fix first)
  - A step fails with an error
- When user input is received and the step completes, resume auto-progression to the next step.

### Step Invocation

- Use the agent's native mechanism to invoke each slash command (e.g., Claude Code's Skill tool, Copilot's chat commands).
- Step 1 (`/speckit.specify`): Pass the full `$ARGUMENTS` as the feature description.
- Steps 2-6: Invoke with no arguments (they auto-detect the feature context from the current branch and feature directory).

### Error Handling

- If any step fails, report the error and suggest the corrective action. Do NOT auto-proceed past a failed step.
- If `/speckit.analyze` reports CRITICAL issues, pause and present the user with two options:
  1. Fix the issues before proceeding to implementation
  2. Proceed to implementation despite the issues

### Progress Reporting

- Before each step, output a single line: `## Pipeline Step N/6: [step name]`
- After each step completes, output: `Step N/6 complete. Proceeding to next step...`
- Keep progress reporting minimal — the individual commands already produce their own output.

## Start

Begin by invoking `/speckit.specify` with the feature description from `$ARGUMENTS`. If `$ARGUMENTS` is empty, ask the user for a feature description before starting.
