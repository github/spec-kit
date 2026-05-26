<!--
Sync Impact Report
- Version change: none → 1.0.0 (initial ratification)
- Modified principles: N/A (initial constitution)
- Added sections:
  - Scope
  - Core Principles
    - I. Selective Spec-Driven Development
    - II. Spec-Forward, Historical Once Shipped
    - III. Governance and Agent Context Separation
  - Governance
- Removed sections: none
- Templates requiring updates:
  - ⚠ none required for downstream templates (`templates/plan-template.md`,
    `templates/spec-template.md`, `templates/tasks-template.md`,
    `templates/commands/*.md` are consumed by downstream projects and remain
    unaffected — this constitution governs only spec-kit's own work)
- Follow-up TODOs: none
- Provenance:
  - https://github.com/github/spec-kit/discussions/2504
  - https://github.com/github/spec-kit/discussions/2476
-->

# Spec Kit Constitution

## Scope

This constitution governs work in the spec-kit repository. It does not prescribe behavior for downstream projects, which produce their own constitutions via the shipped `/constitution` workflow.

## Core Principles

### I. Selective Spec-Driven Development

SDD MUST be applied to a change in this repository when **at least one** of the following holds:

- **Non-trivial scope**: the change spans multiple modules, introduces new public surface, or touches more than a handful of files cohesively.
- **Ambiguous design space**: more than one viable implementation exists and the trade-offs are not obvious from the issue or discussion.
- **Cross-cutting impact**: the change affects shipped templates, command files, or any artifact consumed by downstream projects.
- **Security or correctness stakes**: the change touches authentication, authorization, input handling, redirect handling, or any path where incorrect behavior has a material blast radius beyond the contributor's environment.

SDD MUST NOT be applied as theater. Refactors, plumbing changes, dependency bumps, catalog updates, documentation fixes, and other changes that do not meet any of the criteria above SHOULD ship without spec artifacts. Manufacturing spec artifacts on changes that do not need them dilutes the signal value of the ones that do.

### II. Spec-Forward, Historical Once Shipped

Feature spec artifacts in this repository
(`specs/<feature>/{spec,plan,tasks}.md`) are **spec-forward**: they describe
work to be done, not work that has been done.

Once a feature merges, its spec artifacts are a **frozen historical snapshot**. They MUST NOT be maintained as living documents that track subsequent code evolution. Drift between merged specs and current code is expected and acceptable; the spec records what the unit of work was at the time, not the present state of the codebase.

When the same surface is meaningfully revisited later, the contributor MAY produce new spec artifacts under a new `specs/<feature>/` directory rather than amending the historical ones.

**Rationale**: the spec-kit codebase evolves rapidly. Treating specs as living
documents would create a maintenance burden out of proportion to their value.
Treating them as snapshots makes them low-cost to merge and useful as evidence
of "this was the unit of work, this is what shipped." This stance was
established by maintainer guidance in
[GitHub Discussion #2504](https://github.com/github/spec-kit/discussions/2504).

### III. Governance and Agent Context Separation

This constitution MUST define repository-level governance and phase-scoped SDD
rules: when spec artifacts are warranted, how specs/plans/tasks are treated,
and how these rules change. It MUST NOT duplicate agent-specific operating
instructions, local workflow recipes, codebase maps, or day-to-day
implementation conventions that belong in `AGENTS.md`,
`.github/copilot-instructions.md`, `CLAUDE.md`, or other tool-specific context
files.

Agent context files MAY reference this constitution, but SHOULD avoid mirroring
its rules. Conversely, this constitution MAY reference agent context files for
operational details instead of copying them. If a rule must influence every
normal agent interaction, it belongs in agent context; if it governs when or
how spec artifacts and repo process are created, reviewed, or amended, it
belongs here.

**Rationale**: the constitution is loaded by Spec Kit workflows when relevant;
it is not a catch-all context file for every LLM call. Keeping governance
separate from agent context avoids DRY drift across multiple instruction
surfaces. This distinction follows the concerns raised in
[GitHub Discussion #2476](https://github.com/github/spec-kit/discussions/2476).

## Governance

**Amendments**: unlike merged feature spec artifacts, this constitution is the
current governance record and remains amendable through this section. Changes
to this constitution require a pull request explicitly identifying the
amendment, its rationale, and a version bump per the policy below. Amendments
that introduce or remove a principle SHOULD be discussed in a GitHub Discussion
under the `Ideas` category before opening a PR.

**Versioning**:

- **MAJOR**: a principle is removed, redefined in a backwards-incompatible way, or a governance rule is replaced.
- **MINOR**: a new principle or new section is added, or guidance is materially expanded.
- **PATCH**: clarifications, wording fixes, or non-semantic refinements.

**Compliance review**: pull request reviewers MAY reference this constitution when asking a contributor whether a change warrants SDD artifacts. Whether the criteria in Principle I are met is a judgment call made by the contributor with reviewer input; this constitution does not bind reviewers to demand or refuse spec artifacts in any specific case.

**Version**: 1.0.0 | **Ratified**: 2026-05-26 | **Last Amended**: 2026-05-26
