---
description: Produce a Product Requirement Prompt artifact for the active PRP workflow feature.
scripts:
  sh: scripts/bash/context-feature-info.sh --json
  ps: scripts/powershell/context-feature-info.ps1 -Json
---

Only run when `.context-eng/workflow.json` declares the `prp` workflow.

1. Execute `{SCRIPT}` to fetch metadata. Confirm `WORKFLOW` is `prp`. If not, stop and inform the user.
2. Identify or create the target PRP file:
   - Use `PRP_FILE` from the JSON when available.
   - Otherwise create `PRPs/{CONTEXT_FEATURE}.md` using the template at `.context-eng/workflows/prp/templates/prp-template.md`.
3. Incorporate material from `PRIMARY_FILE` (INITIAL brief) and any research artifacts to fill the PRP template: context snapshot, requirements matrix, guardrails, validation plan, follow-up tasks.
4. Validate that every requirement traces back to the INITIAL brief and note confidence levels.
5. Save the PRP file and summarize key requirements plus recommended follow-up (`/execute-prp`).
