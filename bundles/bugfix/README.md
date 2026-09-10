# Bug Fix Bundle

A first-party GitHub Spec Kit bundle that installs an orchestrated bug-fixing pipeline.

## What it provides

- **Bug extension** (`extensions/bug`) — the `speckit.bug.assess`, `speckit.bug.fix`, and `speckit.bug.test` commands.
- **Bugfix workflow** (`workflows/bugfix`) — a guided, resumable pipeline:
  1. `assess` the bug report.
  2. `review-assessment` gate — approve to proceed, reject to abort.
  3. `fix` the bug.
  4. `test` the fix.

## Install

```bash
specify bundle install bugfix
# or
specify bundle add bugfix
```

## Run the workflow

```bash
specify workflow run bugfix
```

You will be prompted for a bug report and a slug. The slug is used as the working directory under `.specify/bugs/<slug>/` for all artifacts.

## Remove

```bash
specify bundle remove bugfix
```

Removing the bundle uninstalls both the workflow and the extension only if no other installed bundle still depends on them (FR-022).
