---
description: Create or update the project vision document (.specify/memory/vision.md), the North Star that defines where this project is going and why.
handoffs:
  - label: Run Coherence Audit
    agent: speckit.coherence
    prompt: Audit the codebase against the new vision
    send: true
  - label: Create Feature Spec
    agent: speckit.specify
    prompt: Create a spec aligned with the vision
---

# /speckit.vision — Create or Update Vision Document

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Create or update `.specify/memory/vision.md`, the North Star document
that defines where this project is going and why.

## When to run this command

- At project start, before writing any specs
- When the project's purpose or scope changes significantly
- When the team loses clarity on what they're building and why
- When a new major feature would require revisiting core assumptions

## Step 1 — Read existing context

Read the following files:
- `.specify/memory/constitution.md`
- `.specify/memory/vision.md` (if it exists)
- List all files under `.specify/specs/` to understand current scope

## Step 2 — Gather input

Ask the user the following questions ONE AT A TIME.
Wait for a response before asking the next question.
If vision.md already exists, show the current value and ask if they want to update it.

1. "Who is this project for, and what painful problem does it solve for them?"
2. "Describe the ideal outcome in 2–3 sentences: what does the world look like when this project is working perfectly?"
3. "What are the 2–3 most important things a user does with this system?"
4. "What is this project explicitly NOT trying to do?"
5. "What does 'good enough' look like? (speed, reliability, simplicity)"

## Step 3 — Draft vision.md

Using the answers, populate `.specify/memory/vision.md`.

Rules for drafting:
- Section 2 (The World After) must be written in present tense
- Section 3 (User Journeys) must have named actors and concrete success criteria
- Section 4 (What This Is NOT) must be specific — vague exclusions are useless
- Do NOT invent content. If the user's answers are vague, ask for clarification

## Step 4 — Validate against constitution

Read `.specify/memory/constitution.md`.
Confirm that vision.md does not contradict any constitutional principle.
If a conflict exists, flag it explicitly and ask the user how to resolve it.

## Step 5 — Write and confirm

Write the completed vision.md.
Show the user a summary of what was written.
Ask: "Does this accurately represent where this project is going?"
If yes, complete. If no, return to Step 2 for the sections that need revision.

## Handoff

After completing vision.md, suggest running `/speckit.coherence` to audit the
codebase and establish a baseline health snapshot, or `/speckit.specify` to
create a new feature spec in light of the newly defined vision.
