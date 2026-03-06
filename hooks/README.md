# MiniSpec Hooks

Claude Code hooks that enforce safety guardrails and documentation reminders. These run automatically — no manual setup required.

## Directory Structure

```text
hooks/
├── hooks.yaml              # Hook definitions
├── README.md               # This file
├── scripts/                # Hook scripts (Claude Code protocol)
│   ├── claude-protect-main.sh       # Block commits to protected branches
│   ├── claude-block-force.sh        # Block destructive git operations
│   ├── claude-secrets-scan.sh       # Scan for hardcoded secrets
│   └── claude-doc-update-prompt.sh  # Documentation update reminder
└── adapters/
    └── claude-code.json    # Claude Code settings (→ .claude/settings.json)
```

## Hooks

| Hook                | Type                      | Trigger                             | Action                         |
| ------------------- | ------------------------- | ----------------------------------- | ------------------------------ |
| `protect-main`      | PreToolUse → Bash         | `git commit` on protected branch    | Denies the operation           |
| `block-force`       | PreToolUse → Bash         | `git reset --hard`, `push -f`, etc. | Denies the operation           |
| `secrets-scan`      | PreToolUse → Bash         | `git add` or `git commit`           | Denies if secrets found        |
| `doc-update-prompt` | PostToolUse → Write\|Edit | Source file modified                | Injects documentation reminder |

## How It Works

### PreToolUse (Safety Gates)

Scripts receive JSON on stdin with `tool_input.command`, inspect the command, and either:

- Exit silently (allow)
- Output a JSON `permissionDecision: "deny"` response (block)

### PostToolUse (Documentation)

Scripts receive JSON on stdin with `tool_input.file_path`, and either:

- Exit silently (non-source files, tests, config)
- Output plain text that gets injected into Claude's context as a reminder

## Build Integration

The build script (`create-release-packages.sh`) handles wiring:

1. Copies `hooks/` → `.minispec/hooks/` in every package
2. For Claude packages, copies `adapters/claude-code.json` → `.claude/settings.json`

## Customization

### Protected Branches

Edit `scripts/claude-protect-main.sh`:

```bash
PROTECTED_BRANCHES=("main" "master" "develop" "production")
```

### Secret Patterns

Edit `scripts/claude-secrets-scan.sh` `PATTERNS` array.

### Doc Reminder Skip Patterns

Edit `scripts/claude-doc-update-prompt.sh` case statements to add paths that should not trigger reminders.
