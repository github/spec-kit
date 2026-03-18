---
description: "Validate project health: templates, agent config, scripts, constitution, and feature artifacts"
---

## User Input

```text
$ARGUMENTS
```

## Outline

Run a comprehensive health check on the spec-kit project, validating that all required components are present and correctly configured.

### Step 1: Find the project root

Locate the `.specify/` directory. If not found, error: "No spec-kit project found. Run `specify init` first."

### Step 2: Check templates

Verify these template files exist in `templates/` and are non-empty:
- `spec-template.md`
- `plan-template.md`
- `tasks-template.md`
- `constitution-template.md`
- `checklist-template.md`

For each template:
- File exists and non-empty: PASS
- File exists but empty: WARN ("template is empty")
- File missing: FAIL ("template not found")

### Step 3: Check agent configuration

Read `.specify/init-options.json` to determine the configured AI agent.

If no `init-options.json` exists: WARN ("no AI agent configured - run `specify init` to set up")

If an agent is configured (e.g., `"ai_assistant": "claude"`):
1. Check that the agent's directory exists (e.g., `.claude/`)
2. Check that command files are registered (e.g., `.claude/commands/speckit.*.md`)
3. Count registered commands

- Agent dir exists with commands: PASS
- Agent dir missing: FAIL ("agent directory not found")
- Agent dir exists but no commands: WARN ("no command files registered")

### Step 4: Check scripts

Scan `scripts/bash/` and `scripts/powershell/` for script files.

- No scripts directory: WARN ("no scripts directory found")
- Scripts exist and are executable: PASS
- Scripts exist but not executable (missing +x on .sh files): WARN ("scripts not executable - run `chmod +x scripts/bash/*.sh`")

### Step 5: Check constitution

Look for `constitution.md` or `memory/constitution.md` in the project root.

- Exists and has content (>10 words): PASS (show word count)
- Exists but empty: WARN ("constitution is empty")
- Not found: WARN ("no constitution found - consider creating one to guide AI decisions")

### Step 6: Check features

Scan `specs/` for numbered feature directories. For each feature:

Check for required artifacts: `spec.md`, `plan.md`, `tasks.md`

- All three present: PASS
- Some missing: WARN (list which are missing, e.g., "spec ✓ plan ✗ tasks ✗")

### Step 7: Report

Output a summary table:

```
Project Health Check
====================

Templates:     5/5 PASS
Agent Config:  PASS (Claude Code, 8 commands registered)
Scripts:       PASS (bash: 4 executable, powershell: 4)
Constitution:  PASS (245 words)

Features:
  001-auth:      spec ✓  plan ✓  tasks ✓  PASS
  002-dashboard: spec ✓  plan ✗  tasks ✗  WARN (needs /speckit.plan)

Overall: 4 PASS, 1 WARN, 0 FAIL
```

If any FAIL results exist, suggest specific remediation steps.
