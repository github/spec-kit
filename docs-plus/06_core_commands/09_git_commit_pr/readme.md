# **Step 8: Ship with `/sp.git.commit_pr`**

**Goal:** Turn a completed feature branch into a clean Git history and ready-to-review pull request by delegating the mechanics to the agentic Git workflow command.

---

## **When to Run This Command**

Use `/sp.git.commit_pr` after you finish the Spec → Plan → Tasks → Implement loop and have already:

- Reviewed the final diff locally (Cursor, VS Code, etc.)
- Re-run your verification suite (tests, type checks, lint)
- Updated documentation and task checklists

Running it earlier can produce partial commits or PRs that do not match the finished work.

---

## **Inputs**

- A working tree with staged or unstaged changes ready to commit
- A clear summary of what was completed (optional argument you can hand the agent)
- Access to GitHub CLI credentials if you expect the agent to create the PR automatically

> The command itself only issues Git (and `gh`) commands. Make sure any required build or test steps are completed beforehand.

---

## **Actions the Agent Performs**

1. **Repository health check** – `git --version`, `git status`, `git diff --stat`, recent history, current branch, and remotes.
2. **Strategy selection** – Inspects the branch state to decide whether to create a feature branch, reuse the current branch, or stop for human input.
3. **Commit authoring** – Generates a conventional commit message from the diff and project conventions.
4. **Branch & push** – Creates or updates a remote tracking branch, pushing changes to GitHub.
5. **Pull request draft** – Uses `gh pr create` (if available) to open a PR with title, body, and checklist grounded in the diff. Falls back to sharing the compare URL if `gh` is unavailable.
6. **Result report** – Summarises the branch name, commit SHA, PR URL (or manual instructions), and any blockers detected.

The agent never runs long-lived processes, executes non-Git commands, or touches files outside the repository root.

---

## **Example Prompt**

```text
/sp.git.commit_pr Wrap up the basic calculator feature. Tests are green and tasks.md is fully checked off.
```

You can omit the argument if you want the agent to infer everything from the diff.

---

## **Deliverables**

- New feature branch (if required) pushed to origin
- Commit applied with conventional summary and body
- Pull request created or ready-to-open compare URL shared
- Final status recap that you can paste into stand-ups or release notes

---

## **Quality Gates ✅**

- ✅ All verification commands (tests/type-check/lint) already executed manually
- ✅ Commit subject accurately reflects the change scope
- ✅ PR description lists what changed, why, and references the relevant spec or tasks
- ✅ Branch targets the correct base (usually `main` or `develop` per your repo rules)

---

## **Common Pitfalls**

- **Dirty dependencies:** Generated files or build artefacts not ignored will be detected; clean them before running the command.
- **Ambiguous intent:** If multiple strategies seem valid (e.g., large refactor + doc-only branch), the agent will pause and ask you to choose.
- **Missing credentials:** Without `gh` authentication, the agent produces a compare URL; you must open the PR manually.
- **Protected branches:** If you are still on `main`, the agent will create a branch for you; confirm the branch name matches your team’s conventions before approving.

---

## **References**

- Command template: `templates/commands/sp.git.commit_pr.md`
- Spec Kit Plus repo: https://github.com/panaversity/spec-kit-plus
- GitHub CLI authentication: https://cli.github.com/manual/
