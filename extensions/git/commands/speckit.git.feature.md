---
description: "Create a feature branch with sequential or timestamp numbering"
scripts:
  sh: ../../scripts/bash/create-new-feature.sh
  ps: ../../scripts/powershell/create-new-feature.ps1
---

# Create Feature Branch

Create a new feature branch for the given specification.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Prerequisites

- Verify Git is available by running `git rev-parse --is-inside-work-tree 2>/dev/null`
- If Git is not available, warn the user and skip branch creation (spec directory will still be created)

## Branch Numbering Mode

Determine the branch numbering strategy by checking configuration in this order:

1. Check `.specify/extensions/git/git-config.yml` for `branch_numbering` value
2. Check `.specify/init-options.json` for `branch_numbering` value (backward compatibility)
3. Default to `sequential` if neither exists

## Execution

Generate a concise short name (2-4 words) for the branch:
- Analyze the feature description and extract the most meaningful keywords
- Use action-noun format when possible (e.g., "add-user-auth", "fix-payment-bug")
- Preserve technical terms and acronyms (OAuth2, API, JWT, etc.)

Run the appropriate script based on your platform:

- **Bash**: `.specify/extensions/git/scripts/bash/create-new-feature.sh --json --short-name "<short-name>" "<feature description>"`
- **Bash (timestamp)**: `.specify/extensions/git/scripts/bash/create-new-feature.sh --json --timestamp --short-name "<short-name>" "<feature description>"`
- **PowerShell**: `.specify/extensions/git/scripts/powershell/create-new-feature.ps1 -Json -ShortName "<short-name>" "<feature description>"`
- **PowerShell (timestamp)**: `.specify/extensions/git/scripts/powershell/create-new-feature.ps1 -Json -Timestamp -ShortName "<short-name>" "<feature description>"`

**IMPORTANT**:
- Do NOT pass `--number` — the script determines the correct next number automatically
- Always include the JSON flag (`--json` for Bash, `-Json` for PowerShell) so the output can be parsed reliably
- You must only ever run this script once per feature
- The JSON output will contain BRANCH_NAME and SPEC_FILE paths

If the extension scripts are not found at the `.specify/extensions/git/` path, fall back to:
- **Bash**: `scripts/bash/create-new-feature.sh`
- **PowerShell**: `scripts/powershell/create-new-feature.ps1`

## Graceful Degradation

If Git is not installed or the current directory is not a Git repository:
- The script will still create the spec directory under `specs/`
- A warning will be printed: `[specify] Warning: Git repository not detected; skipped branch creation`
- The workflow continues normally without branch creation

## Output

The script outputs JSON with:
- `BRANCH_NAME`: The created branch name (e.g., `003-user-auth` or `20260319-143022-user-auth`)
- `SPEC_FILE`: Path to the created spec file
- `FEATURE_NUM`: The numeric or timestamp prefix used
