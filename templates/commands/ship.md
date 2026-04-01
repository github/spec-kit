---
description: Automate the release pipeline including pre-flight checks, branch sync, changelog generation, CI verification, and pull request creation.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before ship)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_ship` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Goal

Automate the complete release engineering workflow: verify readiness, synchronize branches, generate a changelog, verify CI status, create a well-structured pull request, and archive release artifacts. This command transforms the implemented feature into a shippable, reviewable PR with full traceability back to the original specification.

## Operating Constraints

**SAFE BY DEFAULT**: Every destructive or potentially destructive operation (e.g., rebase/merge during branch sync, push/force push, branch delete, PR creation) requires explicit user confirmation.
- For the branch sync flow, add a required confirmation prompt **immediately before** performing any rebase/merge, with the default answer set to **no**.
- Add a separate required confirmation prompt **immediately before** performing any push (including force push) to the remote, with the default answer set to **no**.
- Default to dry-run mode for destructive git operations wherever possible.

**TRACEABILITY**: The PR description and changelog must link back to spec, plan, tasks, review, and QA artifacts for full audit trail.

## Outline

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Pre-Flight Readiness Checks**:
   Run a comprehensive readiness assessment before proceeding:

   **Task Completion**:
   - Read `tasks.md` and count total tasks vs. completed tasks (marked `[X]` or `[x]`)
   - If any tasks are incomplete: **STOP** and warn. Ask user to confirm proceeding or run `/speckit.implement` first.

   **Review Status** (if FEATURE_DIR/reviews/ exists):
   - Read the most recent review report
   - If verdict is ❌ CHANGES REQUIRED: **STOP** and warn. Recommend running `/speckit.review` after fixes (if available).
   - If verdict is ⚠️ APPROVED WITH CONDITIONS: Warn but allow proceeding with confirmation.

   **QA Status** (if FEATURE_DIR/qa/ exists):
   - Read the most recent QA report
   - If verdict is ❌ FAILURES FOUND: **STOP** and warn. Recommend running `/speckit.qa` after fixes (if available).
   - If verdict is ⚠️ PARTIAL PASS: Warn but allow proceeding with confirmation.

   **Working Tree**:
   - Run `git status` to check for uncommitted changes
   - If uncommitted changes exist: prompt user to commit or stash before proceeding

   Display a readiness summary:
   ```
   Ship Readiness Check:
   ✅ Tasks: 12/12 complete
   ✅ Review: APPROVED
   ⚠️ QA: PARTIAL PASS (2 non-critical items)
   ✅ Working tree: Clean
   
   Overall: READY TO SHIP (with notes)
   Proceed? (yes/no)
   ```

3. **Determine Shipping Configuration**:
   - Detect the current feature branch: `git branch --show-current`
   - Determine the target branch (default: `main`; allow override via user input/prompt)
   - Detect remote name (default: `origin`; check `git remote -v`)
   - Check if GitHub CLI (`gh`) is available for PR creation
   - If `gh` is not available, generate the PR description as a markdown file for manual creation

4. **Branch Synchronization**:
   - Fetch latest from remote: `git fetch {remote_name}`
   - Check if feature branch is behind target branch:
     ```bash
     git rev-list --count HEAD..{remote_name}/{target_branch}
     ```
   - If behind, offer to rebase or merge:
     - Prompt the user for explicit confirmation **before** performing the rebase/merge (default **no**)
     - **Rebase** (recommended for clean history): `git rebase {remote_name}/{target_branch}`
     - **Merge**: `git merge {remote_name}/{target_branch}`
   - If conflicts arise: **STOP** and provide conflict resolution guidance
   - After sync, prompt the user for explicit confirmation **before** pushing (default **no**):
     `git push {remote_name} {feature_branch}`

5. **Changelog Generation**:
   - Collect changelog inputs:
     - Feature summary from `spec.md` (overview section)
     - Implementation highlights from completed tasks in `tasks.md`
     - Git commit messages: `git log {remote_name}/{target_branch}..HEAD --oneline`
   - Generate a structured changelog entry:
     ```markdown
     ## [Feature Name] - {date}
     
     ### Added
     - [List of new features/capabilities from spec]
     
     ### Changed
     - [List of modifications to existing behavior]
     
     ### Fixed
     - [List of bug fixes discovered during implementation]
     
     ### Technical Notes
     - [Key architecture decisions from plan.md]
     ```
   - If a CHANGELOG.md exists at repo root: prepend the new entry (ask for confirmation)
   - If no CHANGELOG.md exists: create one with the entry

6. **CI Verification**:
   - If GitHub CLI (`gh`) is available:
     - Check CI status: `gh run list --branch {feature_branch} --limit 5`
     - If CI is running: wait and report status
     - If CI failed: **STOP** and display failure details. Recommend fixing before shipping.
     - If CI passed: record the passing run ID for the PR
   - If `gh` is not available:
     - Remind the user to verify CI status manually before merging
     - Check for local test commands and run them: `npm test`, `pytest`, `go test ./...`, etc.

7. **Generate PR Description**:
   Compose a comprehensive PR description from `.specify/` artifacts:

   ```markdown
   ## Summary
   [One-paragraph summary from spec.md overview]

   ## Specification
   [Link to or summary of key requirements from spec.md]

   ## Implementation
   [Key implementation decisions from plan.md]
   [Summary of completed tasks from tasks.md]

   ## Testing
   [QA results summary if qa/ reports exist]
   [Test coverage information]

   ## Review Notes
   [Summary of review findings if reviews/ reports exist]
   [Any conditions or known limitations]

   ## Checklist
   - [ ] All tasks completed
   - [ ] Code review passed
   - [ ] QA testing passed
   - [ ] CI pipeline green
   - [ ] Changelog updated
   - [ ] Documentation updated (if applicable)

   ---
   *Generated by `/speckit.ship` from spec-driven development artifacts.*
   ```

8. **Create Pull Request**:
   - Write the PR description to `FEATURE_DIR/releases/pr-description-{timestamp}.md`
   - If GitHub CLI (`gh`) is available:
     - Prompt the user for explicit confirmation **right before** creating the PR (default **no**):
     ```bash
     gh pr create --base {target_branch} --head {feature_branch} --title "{PR title}" --body-file FEATURE_DIR/releases/pr-description-{timestamp}.md
     ```
   - If `gh` is not available:
     - Provide instructions for manual PR creation
     - Output the PR title and description for copy-paste

   **PR Title Format**: `feat: {feature_name} — {one-line summary from spec}`

9. **Archive Release Artifacts**:
   - Create `FEATURE_DIR/releases/release-{timestamp}.md` with:
     - PR URL (if created via `gh`)
     - Changelog entry
     - Readiness check results
     - Links to review and QA reports
     - Git commit range: `{base_sha}..{head_sha}`

10. **Post-Ship Summary**:
    Display a completion summary:
    ```
    🚀 Ship Complete!
    
    PR: #{pr_number} - {pr_title} ({pr_url})
    Branch: {feature_branch} → {target_branch}
    Commits: {commit_count}
    Files changed: {files_changed}
    Changelog: Updated
    
    Next steps:
    - Review the PR at {pr_url}
    - After merge, consider running `/speckit.retro` for a retrospective (if available)
    ```

**Check for extension hooks (after ship)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.after_ship` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently
