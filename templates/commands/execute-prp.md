---
description: Translate the approved Product Requirement Prompt into implementation tasks and deliverables.
scripts:
  sh: scripts/bash/context-feature-info.sh --json
  ps: scripts/powershell/context-feature-info.ps1 -Json
---

Use only for the `prp` workflow after `/generate-prp` is complete.

1. Run `{SCRIPT}` once to obtain `WORKFLOW`, `PRP_FILE`, `PLAN_FILE`, and `FEATURE_DIR`.
2. Load the PRP artifact and extract:
   - Final requirements list
   - Guardrails and constraints
   - Validation plan
3. Update or create `PLAN_FILE` so it reflects execution sequencing, owners, and checklist items mapped directly to PRP requirements.
4. Produce implementation-ready outputs:
   - Task breakdown (commit or issue plan) saved to `FEATURE_DIR/tasks.md` (create if needed).
   - Risk/status notes appended to `PLAN_FILE`.
   - Testing/validation steps derived from the PRP validation plan.
5. Report readiness to proceed with `/implement` along with any blockers discovered.
