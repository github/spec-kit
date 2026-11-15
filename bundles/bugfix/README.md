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

Required inputs must be supplied with `--input`: `report` and `slug`. The slug is used as the working directory under `.specify/bugs/<slug>/` for all artifacts.

Without an interactive terminal, the run pauses at `review-assessment`. Review
the assessment, then approve it using the optional verdict input:

```bash
specify workflow resume <run_id> --input bug_review_assessment_verdict=approve
```

`bug_review_assessment_verdict` defaults to `""`. Omitting it or supplying an
empty value preserves the existing interactive prompt or non-interactive pause.
This input is available in `bugfix` workflow version 1.0.1 and requires Specify
CLI 0.15.1 or later. Update the workflow and start a new run to use the input;
existing runs retain the definition saved when they started.

## Remove

```bash
specify bundle remove bugfix
```

Removing the bundle uninstalls the workflow and the extension it contributed, unless they are still depended on by another installed bundle (FR-022). Components you installed independently are not attributed to this bundle and survive removal.

## See also

- [Bundle overview](https://github.github.io/spec-kit/bundles/overview.html)
- [Bundle CLI reference](https://github.github.io/spec-kit/bundles/cli.html)
