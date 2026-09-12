<!--
Sync Impact Report
- Version change: none → 1.0.0 (initial, deliberately minimal)
- Principles: I. Selective Spec-Driven Development (proposed criteria);
  II. Spec-Forward, Historical Once Shipped (maintainer-stated stance)
- Sections: Status & Scope; Core Principles; Dogfooding On-Ramp; Governance
- Removed vs. earlier draft: standalone "Governance and Agent Context
  Separation" principle — #2476 is an open community question, not a settled
  one; reduced to a one-line working split under Governance rather than
  ratified as a principle.
- Templates requiring updates:
  - ⚠ none required for downstream templates (`templates/plan-template.md`,
    `templates/spec-template.md`, `templates/tasks-template.md`,
    `templates/commands/*.md` are consumed by downstream projects and remain
    unaffected — this constitution governs only spec-kit's own work)
- Follow-up TODOs: none
- Provenance:
  - https://github.com/github/spec-kit/discussions/2504 (spec-forward stance,
    "try it out and see where it leads" — @mnriem)
  - https://github.com/github/spec-kit/discussions/2476 (constitution vs agent
    context — informs the scope boundary, not resolved here)
-->

# Spec Kit Constitution

## Status & Scope

This document governs how Spec-Driven Development is applied **to work in the
spec-kit repository itself**. It does not prescribe behavior for downstream
projects, which generate their own constitutions via the shipped
`/speckit.constitution` workflow.

It is **deliberately minimal and adopted on a trial basis**, per maintainer
guidance to "try it out and see where it leads"
([Discussion #2504](https://github.com/github/spec-kit/discussions/2504)). It
records a small number of decisions to avoid relitigating them, and is expected
to be revised once the project has actually run SDD on one of its own features.

It is **non-binding and loaded on demand**: Spec Kit commands read it during
`plan`, `tasks`, and `implement`, so it only takes effect when SDD is actually
run on this repository — not on every contribution or every LLM call.

## Core Principles

### I. Selective Spec-Driven Development

SDD pays off — and SHOULD be applied — when **at least one** of the following
holds:

- **Non-trivial scope**: the change spans multiple modules, introduces new
  public surface, or touches more than a handful of files cohesively.
- **Ambiguous design space**: more than one viable implementation exists and
  the trade-offs are not obvious from the issue or discussion.
- **Cross-cutting impact**: the change affects shipped templates, command
  files, or any artifact consumed by downstream projects.
- **Security or correctness stakes**: the change touches authentication,
  authorization, input handling, redirect handling, or any path where incorrect
  behavior has a material blast radius beyond the contributor's environment.

Refactors, plumbing changes, dependency bumps, catalog updates, documentation
fixes, and other changes that meet none of these SHOULD ship without spec
artifacts. Manufacturing spec artifacts on changes that do not need them
dilutes the signal value of the ones that do.

These criteria are **guidance for contributor judgment, not a gate**. Reviewers
MAY reference them when asking whether a change warrants SDD artifacts; nothing
here binds anyone to demand or refuse them in any specific case.

### II. Spec-Forward, Historical Once Shipped

Feature spec artifacts in this repository
(`specs/<feature>/{spec,plan,tasks}.md`) are **spec-forward**: they describe
work to be done, not work that has been done.

Once a feature merges, its spec artifacts become a **frozen historical
snapshot**. They MUST NOT be maintained as living documents that track
subsequent code evolution. Drift between merged specs and current code is
expected and acceptable; the spec records what the unit of work was at the
time, not the present state of the codebase. When the same surface is
meaningfully revisited later, the contributor produces new spec artifacts under
a new `specs/<feature>/` directory rather than amending the historical ones.

**Rationale**: the spec-kit codebase evolves rapidly; treating specs as living
documents would create a maintenance burden out of proportion to their value,
whereas snapshots are cheap to merge and serve as evidence of "this was the
unit of work, this is what shipped." This is the maintainer-stated stance for
this repository
([Discussion #2504](https://github.com/github/spec-kit/discussions/2504): "the
spec defines the unit of work and once it is done it is historical").

## Dogfooding On-Ramp

This document is the **governance half** of dogfooding. The operative half is
running the workflow on a real spec-kit feature and committing its artifacts.

- **Trigger**: the next change that clearly meets Principle I's criteria SHOULD
  be developed with committed `specs/<feature>/{spec,plan,tasks}.md`, making
  this constitution the artifact loaded during that feature's `plan`, `tasks`,
  and `implement` phases.
- **Proof-of-concept candidate**: PR #2393 (config-driven opt-in authentication
  registry) is a textbook fit — the security model pivoted mid-PR, the
  `AuthProvider` contract was reshaped twice, and roughly ten follow-up commits
  patched threat-model gaps surfaced in review. A retroactive
  `specs/auth-registry/` would demonstrate the workflow on real product work.
  It is tracked separately and does not block this document.
- **Goal**: give contributors and downstream adopters a real upstream spec to
  point to, not a fixture — the gap originally raised in #2504.

## Governance

**Scope boundary** (a working split for this repository, not a resolution of
the open [#2476](https://github.com/github/spec-kit/discussions/2476) debate):
this document covers when SDD artifacts are warranted and how they are treated.
Agent-operational context, codebase maps, and day-to-day implementation
conventions live in `AGENTS.md`, `.github/copilot-instructions.md`,
`CLAUDE.md`, and similar tool-specific files, and are not duplicated here.

**Amendments**: changes require a pull request explicitly identifying the
amendment, its rationale, and a version bump per the policy below. Amendments
that introduce or remove a principle SHOULD be discussed in a GitHub Discussion
under the `Ideas` category before opening a PR.

**Versioning**:

- **MAJOR**: a principle is removed, redefined in a backwards-incompatible way,
  or a governance rule is replaced.
- **MINOR**: a new principle or new section is added, or guidance is materially
  expanded.
- **PATCH**: clarifications, wording fixes, or non-semantic refinements.

**Compliance review**: pull request reviewers MAY reference this document when
asking a contributor whether a change warrants SDD artifacts. Whether the
criteria in Principle I are met is a judgment call made by the contributor with
reviewer input; this document does not bind reviewers to demand or refuse spec
artifacts in any specific case.

**Version**: 1.0.0 | **Ratified**: 2026-05-26 | **Last Amended**: 2026-05-29
