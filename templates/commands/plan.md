---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## Strict Contract

- **Required Inputs**
  - Feature directory and spec details provided by `{SCRIPT}`.
  - Optional `$ARGUMENTS` for supplemental instructions.
- **Allowed Tools**
  - Run `{SCRIPT}` exactly once to stage plan artifacts.
  - Read from `spec.md`, `/memory/constitution.md`, and template files.
  - Write to `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/`.
  - Invoke `{AGENT_SCRIPT}` for each configured agent only after Phase 1 succeeds.
- **Outputs**
  - Persist updated Markdown/contract artifacts in the feature directory.
  - Emit a single JSON code block:

    ```json
    {
      "status": "success" | "error",
      "branch": "<branch-name>",
      "plan_path": "<absolute-path>",
      "phase_status": {
        "phase0": "pass" | "fail",
        "phase1": "pass" | "fail",
        "phase2": "pass" | "fail"
      },
      "gates": [
        {"name": "<gate>", "status": "PASS|FAIL|WAIVED", "evidence": "<section reference>"}
      ],
      "next_actions": ["<follow-up>", "..."]
    }
    ```

- **Idempotency**
  - Re-running must update artifacts in place without duplicating sections or regenerating context unnecessarily.
- **Stop Conditions**
  - Abort (set `status` to `error`) if any constitution gate remains `FAIL`.
  - Finish after agent context update and JSON response. No additional prompts or loops.

## User Input

```text
$ARGUMENTS
```

Consider user input for tailoring the plan when provided.

## Execution Flow

1. **Initialize**
   - Execute `{SCRIPT}` once from repo root; parse JSON for `FEATURE_DIR`, `PLAN_FILE`, `SPEC_FILE`, `AGENTS`, and template paths.
   - Shell guidance:
     - **Bash**: Surround arguments with double quotes; escape embedded quotes as `\"`.
     - **PowerShell**: Use double quotes and escape embedded quotes by doubling them.

2. **Load Context**
   - Read `spec.md`, `/memory/constitution.md`, and `templates/plan-template.md`.
   - Capture unresolved `[NEEDS CLARIFICATION]` markers; planning **fails** if any remain.

3. **Phase 0 – Research**
   - Derive research tasks from assumptions, risks, and open questions.
   - Populate/refresh `research.md` summarizing findings and links to supporting evidence.
   - Mark Phase 0 `fail` if outstanding questions remain unchecked.

4. **Phase 1 – Architecture & Contracts**
   - Draft `plan.md` using the template: fill Technical Context, gates, decision log, risk register, and exit criteria.
   - Generate `data-model.md`, `contracts/` artifacts, and `quickstart.md` outlines aligned with spec requirements.
   - Re-evaluate constitution gates and capture evidence references.
   - If any gate fails, update `phase_status.phase1` to `fail` and stop further phases.

5. **Phase 1 Aftermath**
   - For each configured agent, run `{AGENT_SCRIPT}` with appropriate agent name to refresh context (no output expected on success).

6. **Phase 2 – Implementation Readiness**
   - Confirm prerequisites for `/speckit.tasks`: enumerate completed artifacts, remaining risks, and blockers.
   - Update plan exit criteria and next steps for task generation. Record status in `phase_status.phase2`.

7. **Respond**
   - Compile gate results, outstanding actions, and phase status into the JSON response.

## Planning Standards

- Cite plan sections when referencing constitution evidence.
- Keep decision log entries concise but actionable; mark status explicitly (Proposed/In Review/Accepted).
- Risk register must include owner, mitigation, and trigger fields.
- Ensure generated Markdown retains YAML front matter headers.
