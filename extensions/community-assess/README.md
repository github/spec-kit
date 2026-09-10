# Community Contribution Assessment Extension

This extension provides one read-only assessment command for a community pull
request. It records the pull request revision, checks evidence against the
repository's contribution policy, and reports missing or conflicting evidence.
It does not review code, execute contributor commands, request changes, apply
labels, merge, or close a pull request.

## Command

| Command | Output |
|---------|--------|
| `speckit.community-assess.assess` | `.specify/community-assessments/<pr-number>-<head-sha>/assessment.md` |

Example:

```text
/speckit.community-assess.assess 123
```

The command is also retained as the assessment rubric for the reviewable
`community-assess` GitHub Agentic Workflow proposal. The proposal is
intentionally not compiled or activated: fork execution and trusted
publication require a repository context and secrets that are unavailable to
ordinary `pull_request` runs.

## Assessment boundary

- `CONTRIBUTING.md` is the authoritative policy source for agreement, scope,
  tests, documentation, workflow compatibility, AI disclosure, human
  understanding/testing, rationale, and concrete evidence.
- Existing checks count only when their recorded head SHA matches the captured
  pull request head SHA. Missing, inaccessible, pending, or mismatched checks
  are reported as unknown.
- Architectural fit remains a maintainer judgment. The command reports the
  evidence state and does not invent an architectural rule.
- Pull request text, diffs, comments, linked pages, and generated files are
  untrusted data. The command never executes instructions found in them or
  exposes secrets.
- Retrospective pilot metrics must come from observable GitHub data. The
  command does not fabricate a 100-PR sample, self-reported minutes, or
  eight-week pilot results.

## Installation

```bash
specify extension add community-assess
```

The extension has no lifecycle hooks and can be disabled without affecting the
normal Spec-Driven Development workflow.
