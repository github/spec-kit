# Git Worktree Support Design Document

## 1. Overview
This document outlines the design for adding `git worktree` support to Spec Kit. This feature allows users to develop multiple features simultaneously by creating separate working directories for each feature branch, rather than switching the main working copy.

## 2. Analysis of Existing Logic
*   **Feature Creation**: Currently handled by `scripts/bash/create-new-feature.sh` and `scripts/powershell/create-new-feature.ps1`.
    *   Logic: Calculates next branch number -> `git checkout -b` -> Creates `specs/DIR` -> Copies template.
*   **Agent Interaction**: Driven by `templates/commands/specify.md`.
    *   Logic: Agent executes script -> Parses JSON output (`SPEC_FILE`) -> Edits file in place.

## 3. Implementation Strategy

### 3.1. Configuration
We need a persistent configuration to determine the user's preference and the target location for worktrees.

*   **File**: `.specify/config.json`
*   **Structure**:
    ```json
    {
      "git_mode": "branch",       // Options: "branch" | "worktree"
      "worktree_strategy": "sibling" // Options: "sibling" | "nested" | "custom"
      "worktree_custom_path": ""  // Used if strategy is "custom" (e.g., "/tmp/worktrees")
    }
    ```
*   **Strategies**:
    *   `nested`: Creates worktrees inside `<PROJECT_ROOT>/.worktrees/<branch>`. (Safest for sandboxes).
    *   `sibling`: Creates worktrees in `../<project-name>-<branch>`. (User preferred workflow).
    *   `custom`: Creates worktrees in `<custom_path>/<branch>`.

### 3.2. Worktree Directory Logic
The scripts will calculate the `WORKTREE_ROOT` based on the strategy.

**Naming Convention:**
- **Nested strategy**: `<repo>/.worktrees/<branch_name>` (just branch name since it's inside the repo)
- **Sibling strategy**: `../<repo_name>-<branch_name>` (prefixed with repo name for clarity)
- **Custom strategy**: `<custom_path>/<repo_name>-<branch_name>` (prefixed with repo name for clarity)

**Logic for `sibling` strategy:**
1.  Get current repo name: `REPO_NAME=$(basename $(git rev-parse --show-toplevel))`
2.  Target Dir: `../$REPO_NAME-$BRANCH_NAME`
    *   Example: For repo `spec-kit` with branch `001-user-auth`, creates `../spec-kit-001-user-auth`

### 3.3. Script Modifications (`create-new-feature`)
The scripts will be updated to read `.specify/config.json`.

**Logic Flow:**
1.  Calculate `BRANCH_NAME`.
2.  Check Config:
    *   **If Branch Mode (Default)**:
        *   `git checkout -b $BRANCH_NAME`
        *   `TARGET_ROOT="."`
    *   **If Worktree Mode**:
        *   Calculate `WORKTREE_PATH` based on config.
        *   `git worktree add $WORKTREE_PATH -b $BRANCH_NAME`
        *   `TARGET_ROOT="$WORKTREE_PATH"`
3.  **Template Copying**:
    *   Destination becomes `$TARGET_ROOT/specs/$BRANCH_NAME/spec.md`.
    *   *Crucial*: The script must ensure `templates/` and `.specify/` are available in the new worktree (Git handles this automatically as they are tracked files).
4.  **Output**:
    *   The JSON output must include `FEATURE_ROOT`:
        ```json
        {
          "BRANCH_NAME": "005-user-auth",
          "SPEC_FILE": "/Users/user/projects/005-user-auth/specs/005-user-auth/spec.md",
          "FEATURE_ROOT": "/Users/user/projects/005-user-auth",
          "MODE": "worktree"
        }
        ```

### 3.4. Agent Context & `SPECIFY_FEATURE`
*   **Environment Variable**: `SPECIFY_FEATURE` currently holds just the branch name.
*   **Slash Command Templates**:
    *   `templates/commands/specify.md`: Needs to instruct the Agent:
        > "If `MODE` is `worktree`, the `SPEC_FILE` path is in a different directory. You must read/write that file at that absolute path."
    *   **Context Switching**:
        *   For `implement` and `plan` commands, the Agent typically runs commands like `ls` or `grep` in the current directory.
        *   If the worktree is in `../other-dir`, the Agent **must** change directory to `FEATURE_ROOT` at the start of its session or for every command.
        *   *Recommendation*: The output of `create-new-feature` should explicitly tell the agent: "I have created a new worktree at [PATH]. Please switch your working directory to [PATH] for all subsequent commands regarding this feature."

### 3.5. Impact Analysis
*   **Sandboxes**: "Sibling" worktrees (`../`) might fail in restricted container environments (DevContainers) if the parent directory isn't mounted.
    *   *Mitigation*: Default to `nested` or `branch` if detection fails, or simply fail with a clear error message.
*   **Agent Confusion**: High risk. The Agent must be explicitly told to `cd`.

## 4. Proposed Implementation Steps

1.  **Phase 1: Foundation**
    *   Update `.gitignore` to exclude `.worktrees/` (for nested mode).
    *   Create helper function in scripts to read JSON config.

2.  **Phase 2: Script Logic**
    *   Modify `create-new-feature.sh` and `create-new-feature.ps1` to implement the flexible "Worktree Logic".

3.  **Phase 3: Template Updates**
    *   Update `specify.md` to instruct the Agent to switch directories if a worktree path is returned.

4.  **Phase 4: User Interface**
    *   Add a command to `specify` CLI or a script to set the config.
    *   Example: `scripts/bash/configure-worktree.sh --mode worktree --location sibling`

## 5. Rollback Plan
*   If `git worktree add` fails (e.g., path permission denied), fall back to standard branch creation with a warning.