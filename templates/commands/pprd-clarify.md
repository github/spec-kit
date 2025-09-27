---
description: Identify underspecified areas in a PPRD and record clarifications back into the same PPRD file.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --paths-only
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

The user input to you can be provided directly by the agent or as a command argument - you MUST consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

Goal: Clarify a portfolio/product PRD (PPRD). Ask up to 5 targeted questions that materially de-risk subsequent feature decomposition, then write the accepted answers into the PPRD under a Clarifications section and apply updates to relevant sections.

Execution steps:

1) Run `{SCRIPT}` from repo root once and parse JSON for `REPO_ROOT`.
2) Determine the target PPRD file path:
   - If the user provided a path in arguments, use it.
   - Otherwise, resolve specs root via `scripts/bash/spec-root.sh` (or PowerShell) and assume single-file convention: `<SPEC_ROOT>/pprd.md` (or the file name in `files.pprd` from `.specs/.specify/layout.yaml`), if it exists.
   - If single-file not found, search `<SPEC_ROOT>/pprd/*.md` and pick the most recent.
   - If still ambiguous, ask the user to select the PPRD path.
3) Load the PPRD and perform a structured scan for ambiguity using this taxonomy:
   - Context & Vision; Outcomes & Targets (NSM, input metrics, guardrails)
   - Personas & JTBD; Capability Map; Constraints & Non-Goals
   - Risks & Unknowns; Release Strategy; Measurement Plan (events, dashboards, alerts)
4) Generate a prioritized queue (max 5) of high‑impact clarification questions. Constraints:
   - Each question answerable via 2–5 options OR a short answer (<=5 words).
   - Only include questions that change feature decomposition, acceptance criteria, or operational readiness.
5) Ask EXACTLY ONE question at a time. After each accepted answer:
   - Ensure a `## Clarifications` heading exists (and a `### Session YYYY-MM-DD` subheading for today).
   - Append `- Q: <question> → A: <answer>` under the session.
   - Apply the clarification to the most appropriate section(s) in the PPRD: e.g., metrics, personas, guardrails, constraints.
   - Save the PPRD file atomically.
6) Validation after each write and final pass:
   - Max 5 questions. No duplicates. No unresolved placeholders the answer was meant to remove.
   - Remove contradictory earlier statements when clarified.
   - Maintain heading structure and formatting.
7) Report summary: questions asked/answered, path to updated PPRD, sections touched, and a compact coverage map (Resolved/Deferred/Clear/Outstanding).

Behavior rules:
- Stop early if adequate coverage exists; recommend proceeding to feature decomposition (see `/fprds`).
- If the PPRD path is not found, ask the user to provide it; do not create a new PPRD here.
- Keep questions high‑signal and balanced across unresolved categories.

Context for prioritization: {ARGS}
