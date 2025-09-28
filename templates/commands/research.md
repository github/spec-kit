---
description: Drive the research phase for the active context engineering workflow.
scripts:
  sh: scripts/bash/context-feature-info.sh --json
  ps: scripts/powershell/context-feature-info.ps1 -Json
---

Purpose: collect signals that deepen understanding for the current feature.

Steps:
1. Run `{SCRIPT}` once to obtain workflow metadata. Capture:
   - `WORKFLOW`
   - `FEATURE_DIR`
   - `RESEARCH_FILE` (if provided)
   - `PRIMARY_FILE`
2. Review `PRIMARY_FILE` for open questions and knowledge gaps.
3. Assemble research notes:
   - Summarize repository insights (existing modules, APIs, configs).
   - Identify external references (docs, issues, RFCs) and log links.
   - Highlight risks, blockers, or validation needs per workflow:
     * Free-Style → architecture impacts & data touchpoints.
     * PRP → requirement coverage and stakeholder expectations.
     * All-in-One → end-to-end feasibility and sequencing concerns.
4. Persist findings:
   - Use `RESEARCH_FILE` when provided; otherwise create `research.md` in `FEATURE_DIR`.
   - Structure sections as Context Signals, Insights, Assumptions, Risks.
5. Close with a summary that lists research outcomes, unanswered questions, and recommended next command.
