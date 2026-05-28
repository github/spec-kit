---
description: "Auto-commit changes after a Spec Kit command completes"
---

# Auto-Commit Changes

Automatically stage and commit all changes after a Spec Kit command completes.

## Instructions

Follow these steps **exactly**. Do NOT skip the config file read or assume default values.

### Step 1 — Determine the event name

Identify the hook event name to use:
- If hook output is present, read it from the `"Hooks available for event '<name>'"` line emitted by Spec Kit — this is the most reliable source.
- If the invocation includes an explicit event name argument (e.g., `/speckit.git.commit after_tasks`), use it.
- If invoked manually with no hook context and no event argument, ask the user which event to use.

### Step 2 — Read the configuration file

**You MUST read** the file `.specify/extensions/git/git-config.yml` before deciding whether to commit. Do NOT assume its contents — the user may have changed the defaults.

If you cannot access local files directly, ask the user to provide the contents of this file. Do NOT guess or fabricate config values.

If the file does not exist, auto-commit is disabled. Exit silently.

### Step 3 — Check whether auto-commit is enabled

Look under the `auto_commit:` section in the config file you just read:

1. Find the key matching the event name (e.g., `after_tasks:`).
2. If the event key exists **and** has `enabled: true` → auto-commit is **enabled**. Use the `message` value from that key if present; if `message` is missing or empty, fall back to the default format `"[Spec Kit] Auto-commit <before|after> <command>"`.
3. If the event key exists **and** has `enabled: false` → auto-commit is **disabled**. Exit silently.
4. If the event key does **not** exist at all, check `auto_commit.default`:
   - `default: true` → auto-commit is **enabled**. Use a default message `"[Spec Kit] Auto-commit <before|after> <command>"` (e.g., `after_tasks` → `"[Spec Kit] Auto-commit after tasks"`).
   - `default: false` or missing → auto-commit is **disabled**. Exit silently.

### Step 4 — Execute the commit (only if enabled)

If auto-commit is enabled:

**Option A — Run the script** (preferred, handles edge cases):
- **Bash (macOS/Linux)**: `.specify/extensions/git/scripts/bash/auto-commit.sh <event_name>`
- **PowerShell (Windows)**: `.specify/extensions/git/scripts/powershell/auto-commit.ps1 <event_name>`

**Option B — Run git directly** (if scripts are unavailable):
1. Check for uncommitted changes: `git status --porcelain`
2. If there are changes, run `git add .` then `git commit -m "<message>"`
3. Report the result

### Graceful Degradation

- Git not available or not a repository → skip with a warning
- No config file → skip silently (disabled by default)
- No changes to commit → skip with a brief message
