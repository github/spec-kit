---
description: Build the implementation plan tailored to the active workflow.
scripts:
  sh: scripts/bash/context-plan-setup.sh --json
  ps: scripts/powershell/context-plan-setup.ps1 -Json
---

Objective: convert research findings into a sequenced plan.

Procedure:
1. Execute `{SCRIPT}` once. Capture:
   - `WORKFLOW`
   - `PLAN_FILE`
   - `PRIMARY_FILE`
   - `RESEARCH_FILE`
   - `CHECKLIST` (path to the full implementation checklist template when provided)
2. Review `PRIMARY_FILE` and `RESEARCH_FILE` to align on context and outstanding questions.
3. Populate `PLAN_FILE` with:
   - Overview summarizing intent and constraints.
   - Workstreams broken down by layers (frontend, backend, data, infra, test, docs).
   - Risk register and mitigation notes.
   - Integration points or stakeholder touchpoints.
4. Ensure every entry in the Full Implementation Checklist is addressed; if the script provides a template, embed it verbatim and mark progress.
5. Finish with execution sequencing and expected next command for the workflow (e.g., `/implement`, `/generate-prp`, or `/context-engineer`).
