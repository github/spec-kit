---
description: Display current feature workflow status and suggest next steps
scripts:
  sh: scripts/bash/workflow-status.sh --json
  ps: scripts/powershell/workflow-status.ps1 -Json
---

# Workflow Status

## Overview

This command analyzes your current workflow state and provides clear guidance on what to do next.

## Process

1. **Run the status script**: Execute `{SCRIPT}` to gather workflow information
   - The script outputs JSON with comprehensive state information
   - Parse the following fields: `feature_number`, `feature_name`, `branch`, `phase`, `phase_name`, `next_command`, `explanation`, and completion metrics

2. **Analyze the current state**:
   ```json
   {
     "phase": "3",
     "phase_name": "Planning Complete",
     "completion_percentage": 0,
     "next_command": "/speckit.tasks",
     "token_budget_used": 45000,
     "spec_quality": 8
   }
   ```

3. **Generate a formatted status report** using this structure:

```
═══════════════════════════════════════════════════════════
  SPECKIT WORKFLOW STATUS
═══════════════════════════════════════════════════════════

Current Feature: {feature_number}-{feature_name}
Branch: {branch}
Phase: {phase} - {phase_name}
Overall Progress: [{progress_bar}] {completion_percentage}%

✓ COMPLETED STEPS
{list_completed_steps}

⚙ IN PROGRESS
{current_step_details}

⏳ PENDING STEPS
{list_pending_steps}

═══════════════════════════════════════════════════════════

💡 SUGGESTED NEXT STEP

{next_command}

{explanation}

═══════════════════════════════════════════════════════════

📊 QUALITY METRICS

Specification Quality: {spec_quality}/10
Token Budget Used: {token_used}K / {token_total}K ({token_percentage}%)
Checklists Complete: {checklists_complete}/{checklists_total}
Validation Status: {validation_status}

═══════════════════════════════════════════════════════════

🔗 QUICK LINKS

{links_to_files}

═══════════════════════════════════════════════════════════
```

4. **Determine completed steps** based on phase:
   - Phase 0: None
   - Phase 1: Constitution established
   - Phase 2: Constitution, Specification created
   - Phase 3: Constitution, Specification, Plan created
   - Phase 4: Constitution, Specification, Plan, Tasks generated
   - Phase 5: All above + Implementation started
   - Phase 6: All steps complete

5. **Determine pending steps** based on phase:
   - Include all steps not yet completed
   - Show them in logical order

6. **Create progress bar** for tasks (if in implementation phase):
   - Use Unicode block characters: █ for complete, ░ for incomplete
   - 20 character width total
   - Example: `[████████████░░░░░░░░] 60%`

7. **Provide contextual guidance**:
   - If no feature branch: Suggest creating one with `/speckit.specify`
   - If spec has clarifications: Suggest `/speckit.clarify`
   - If token budget > 80%: Warn and suggest `/speckit.prune`
   - If validation not run: Suggest `/speckit.validate`
   - If checklists incomplete: Mention them

## Phase Determination Logic

The script determines phase based on file existence:

| Phase | Name | Condition | Next Step |
|-------|------|-----------|-----------|
| 0 | Setup | No constitution.md | `/speckit.constitution` |
| 1 | Ready for Feature | Constitution exists, no feature branch | `/speckit.specify` |
| 2 | Specification Complete | spec.md exists, no plan.md | `/speckit.plan` |
| 3 | Planning Complete | plan.md exists, no tasks.md | `/speckit.tasks` |
| 4 | Ready for Implementation | tasks.md exists, 0% complete | `/speckit.implement` |
| 5 | Implementation in Progress | tasks.md exists, 1-99% complete | `/speckit.implement` |
| 6 | Implementation Complete | tasks.md exists, 100% complete | `/speckit.document` |

## Example Output

For a feature in Phase 5 (Implementation in Progress):

```
═══════════════════════════════════════════════════════════
  SPECKIT WORKFLOW STATUS
═══════════════════════════════════════════════════════════

Current Feature: 001-task-management
Branch: 001-task-management
Phase: 5 - Implementation in Progress
Overall Progress: [████████████░░░░░░░░] 65%

✓ COMPLETED STEPS
  ✓ Constitution established (memory/constitution.md)
  ✓ Feature specification created (specs/001-task-management/spec.md)
  ✓ Specification validated (3/3 checks passed)
  ✓ Implementation plan created (specs/001-task-management/plan.md)
  ✓ Task breakdown generated (specs/001-task-management/tasks.md)
  ✓ Implementation started (13/20 tasks complete)

⚙ IN PROGRESS
  ⚙ Task T014: Implement TaskService in src/services/task-service.ts
    Status: 65% complete (13/20 tasks done)
    Last updated: 2 hours ago

⏳ PENDING STEPS
  ⏳ Complete remaining 7 implementation tasks
  ⏳ Generate documentation
  ⏳ Final validation and testing

═══════════════════════════════════════════════════════════

💡 SUGGESTED NEXT STEP

/speckit.implement

Continue implementation. Current progress: 65%

The remaining tasks are:
• T015: Add validation and error handling
• T016: Implement API endpoints
• T017-T020: Integration and polish tasks

═══════════════════════════════════════════════════════════

📊 QUALITY METRICS

Specification Quality: 9/10 (Excellent)
Token Budget Used: 45K / 200K (22%)
Checklists Complete: 2/3
Validation Status: All passed

⚠️  Note: 1 checklist incomplete (implementation.md)

═══════════════════════════════════════════════════════════

🔗 QUICK LINKS

Spec: specs/001-task-management/spec.md
Plan: specs/001-task-management/plan.md
Tasks: specs/001-task-management/tasks.md (13/20 complete)

═══════════════════════════════════════════════════════════

💡 Tips:
• Run /speckit.validate to check for issues
• Run /speckit.budget for detailed token breakdown
• Use /speckit.help for command documentation
```

## Error Handling

Handle these scenarios gracefully:

1. **No git repository**:
   ```
   ⚠️  Not a git repository

   Speckit uses git branches to organize features.
   Initialize git: git init
   Or set SPECIFY_FEATURE environment variable for non-git usage.
   ```

2. **No constitution or features**:
   ```
   👋 Welcome to Speckit!

   It looks like you haven't set up your project yet.

   Get started:
   1. /speckit.constitution - Establish project principles
   2. /speckit.specify "your feature" - Create your first feature

   Or use the interactive wizard:
   /speckit.wizard
   ```

3. **Detached HEAD state**:
   ```
   ⚠️  Warning: Detached HEAD state

   You're not on a branch. Workflow state may be unclear.
   Create or checkout a feature branch: git checkout -b NNN-feature-name
   ```

## Notes

- This command is read-only and makes no changes
- Safe to run at any time
- Useful for resuming work after interruption
- Can be called frequently without overhead
