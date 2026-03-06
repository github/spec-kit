# quick-review

A slash command for quick, structured code reviews.

## Usage

```
/quick-review src/auth/login.ts
/quick-review                     # Reviews staged or unstaged changes
/quick-review src/api/            # Reviews all files in a directory
```

## What it does

Performs a focused code review evaluating:

- **Correctness** — Logic errors, missing error handling, edge cases
- **Security** — Input validation, injection risks, exposed secrets
- **Design** — Clarity, naming, separation of concerns

Output is structured into "must fix" issues, suggestions, and positive notes.

## Installed files

| File | Agent |
|------|-------|
| `.claude/commands/quick-review.md` | Claude Code |
| `.cursor/commands/quick-review.md` | Cursor |
| `.github/agents/quick-review.agent.md` | GitHub Copilot |

## Customization

Edit the command template to:

- Add project-specific review criteria
- Adjust severity levels
- Add checklist items for your team's conventions
