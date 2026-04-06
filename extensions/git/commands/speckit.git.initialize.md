---
description: "Initialize a Git repository with an initial commit"
scripts:
  sh: ../../scripts/bash/initialize-repo.sh
  ps: ../../scripts/powershell/initialize-repo.ps1
---

# Initialize Git Repository

Initialize a Git repository in the current project directory if one does not already exist.

## Execution

Run the appropriate script from the project root:

- **Bash**: `.specify/extensions/git/scripts/bash/initialize-repo.sh`
- **PowerShell**: `.specify/extensions/git/scripts/powershell/initialize-repo.ps1`

If the extension scripts are not found, fall back to:
- **Bash**: `git init && git add . && git commit -m "Initial commit from Specify template"`
- **PowerShell**: `git init; git add .; git commit -m "Initial commit from Specify template"`

The script handles all checks internally:
- Skips if Git is not available
- Skips if already inside a Git repository
- Runs `git init`, `git add .`, and `git commit` with an initial commit message

## Customization

Replace the script to add project-specific Git initialization steps:
- Custom `.gitignore` templates
- Default branch naming (`git config init.defaultBranch`)
- Git LFS setup
- Git hooks installation
- Commit signing configuration
- Git Flow initialization

## Output

On success:
- `✓ Git repository initialized`

## Graceful Degradation

If Git is not installed or `git init` fails:
- Warn the user
- Do NOT block the rest of the workflow
- The project continues to function without Git (specs can still be created under `specs/`)
