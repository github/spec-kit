# Idea Assessment Bundle

A first-party GitHub Spec Kit bundle that installs an idea-triage pipeline before committing to Spec-Driven Development.

## What it provides

- **Assess extension** (`extensions/assess`) — the `speckit.assess.intake`, `speckit.assess.research`, `speckit.assess.define`, `speckit.assess.shape`, and `speckit.assess.decide` commands.
- **Assess workflow** (`workflows/assess`) — a guided, resumable pipeline:
  1. `intake` the raw idea.
  2. `research` the evidence.
  3. `define` the problem.
  4. `shape` the concept.
  5. `decide` the verdict.
  6. `review-verdict` gate — approve to complete the assessment; reject to abort. A `go` verdict is then handed off manually to `/speckit.specify`.

## Install

```bash
specify bundle install assess
# or
specify bundle add assess
```

## Run the workflow

```bash
specify workflow run assess
```

You will be prompted for an idea and a slug. The slug is used as the working directory under `.specify/assessments/<slug>/` for all artifacts.

## Remove

```bash
specify bundle remove assess
```

Removing the bundle uninstalls the workflow and the extension it contributed, unless they are still depended on by another installed bundle (FR-022). Components you installed independently are not attributed to this bundle and survive removal.
