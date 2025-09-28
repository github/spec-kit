---
description: Execute the all-in-one workflow, covering research, planning, execution, and validation in a single pass.
scripts:
  sh: scripts/bash/context-feature-info.sh --json
  ps: scripts/powershell/context-feature-info.ps1 -Json
---

1. Run `{SCRIPT}` to retrieve metadata. Ensure `WORKFLOW` equals `all-in-one`. If not, halt with guidance.
2. Load `PRIMARY_FILE` (the all-in-one record) and treat it as the canonical artifact for discovery, plan, implementation, and validation updates.
3. Merge context gathering, planning, and execution notes directly into the file using the sections provided by `.context-eng/workflows/all-in-one/templates/all-in-one-template.md`.
4. Document:
   - Key insights and decisions reached during research.
   - Planned milestones, dependencies, and risk mitigations.
   - Actions performed, code modules touched, tests written/executed.
   - Validation evidence and follow-up tasks.
5. Close with an explicit status summary (Ready, Blocked, Needs Review) and outline any additional commands or manual steps required.
