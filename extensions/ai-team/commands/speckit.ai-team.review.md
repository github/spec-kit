---
description: "Help human reviewers assess PR architecture fit, boundary safety, evidence, and merge readiness."
---

# AI Team Review

Help a human reviewer or committer assess a PR. This command does not replace
human approval.

## User Input

```text
$ARGUMENTS
```

## Review Passes

Check in this order:

1. Repository route: code changes in coding repo; internal enhancement issues,
   handoff RFCs, private drafts, and raw demand in enhancement-internal.
2. Work item: bug fix links a primary coding issue; public feature links a
   coding issue; confidential feature links an allowed handoff requirement or
   public-safe summary. Additional issues must represent different symptoms of
   the same root-cause change and each must map to verification evidence.
3. Native artifacts: `spec.md`, `plan.md`, `tasks.md`, bug reports, workflow
   state, and the Evidence Board agree on the work item and delivered behavior.
4. Work context: `.specify/ai-team/work/<work_slug>/context-pack.md` and
   `work-context.yml` point to the active native artifacts and evidence.
5. Permissions: effective reads, writes, commands, dependencies, and network
   actions stayed inside `permission-envelope.yml`; its enforcement mode and
   gaps are reported honestly.
6. Privacy: coding PRs do not expose raw customer demand or internal drafts.
   Confirm `spec.override.md` is untracked when internal handoff context was
   used.
7. Boundary: touched files stay inside approved modules and do not edit another
   module's internals to avoid an interface request.
8. Architecture: compare the planned Code Graph or source-structure delta with
   the as-built result; dependency direction, state ownership, and public
   contracts are preserved or deviations are approved.
9. Compatibility: default to forward-compatible, behavior-preserving change.
   Pause for owner review when contract diff, config defaults, wire/data shape,
   examples, golden files, or snapshots show an incompatible behavior change.
10. Tests: self-tests match changed behavior.
11. Evidence: work context, code graph, changed nodes, commands, skipped checks,
   uncovered paths, and residual risks are recorded.
12. Minimality: unrelated cleanup and local AI files are absent.

## Findings Format

```text
Review findings:
- [blocker/major/minor] file or area:
  issue:
  why it matters:
  required action:

Open questions:
- ...

Merge recommendation: approve / request changes / split / architecture review

Evidence checked:
- work item:
- coding issue or handoff requirement URL:
- public-safe summary:
- modules:
- work context:
- permission envelope:
- enforcement mode and gaps:
- code graph or fallback:
- changed nodes and impact radius:
- commands:
- tests:
- skipped checks:
- privacy boundary:
```

## Stop Conditions

Recommend request-changes or architecture review when:

- required work item is missing;
- coding feature PR lacks a coding issue, handoff requirement, or approved task ID;
- private requirement content leaks into the coding repository;
- owner approval is missing for public contracts or cross-module semantics;
- code graph or source structure evidence is required but absent;
- tests or evidence are missing for behavior changes;
- indexed artifacts do not match the PR or current work unit;
- operations exceeded the Permission Envelope or hard confinement was required
  but only `policy-only` controls were available.
