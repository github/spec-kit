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
specify workflow run bugfix \
  --input report="https://github.com/example/repo/issues/1234" \
  --input slug="callback-token"
```

Inputs omitted from the command line are prompted interactively. The slug is used as the working directory under `.specify/bugs/<slug>/` for all artifacts.

## Remove

```bash
specify bundle remove bugfix
```

Removing the bundle uninstalls the workflow and the extension it contributed, unless they are still depended on by another installed bundle (FR-022). Components you installed independently are not attributed to this bundle and survive removal.
