---
description: "Archive finished AI Team work for a release and distill reusable feature, bugfix, migration, and operations knowledge."
---

# AI Team Release Archive

Close the release learning loop. This command is the release-scoped form of
`speckit.ai-team.memory-consolidate`: it summarizes completed feature and bugfix
work, reduces process-document sprawl, and promotes reusable knowledge into the
right memory tier.

This command does not edit production code by default.

## User Input

```text
$ARGUMENTS
```

Useful arguments:

- `release_id=<version-or-release-candidate>`
- `since_tag=<previous-release-tag>`
- `target_tag=<release-tag-or-rc-tag>`
- `work_slugs=<comma-separated-work-slugs>` when tag discovery is unavailable
- `coding_issue_url=<release-tracking-issue>` when the release has one
- `privacy=public-safe|internal-only`
- `target_tier=department|enterprise` depending on whether the release archive
  is internal team knowledge or formal project guidance

## Goal

At a release, release candidate, milestone, or maintainer-chosen checkpoint,
convert many task-level artifacts into a small release knowledge package:

- what shipped and why;
- which feature decisions are reusable;
- which bugfix lessons should prevent future repeated mistakes;
- which designs, module patterns, or migration playbooks can be reused in new
  projects;
- which raw traces can be archived, superseded, or kept private.

## Inputs To Read

Read the coding repository first:

- release tag, release candidate tag, release branch, or release tracking issue;
- `.specify/ai-team/work/<work_slug>/work-context.yml`;
- `.specify/ai-team/work/<work_slug>/context-pack.md`;
- `.specify/ai-team/work/<work_slug>/handoffs/`;
- `.specify/ai-team/work/<work_slug>/codegraph/`;
- `.specify/ai-team/work/<work_slug>/evidence/`;
- `specs/<work_slug>/spec.md`, `plan.md`, `tasks.md`, and `quickstart.md`;
- `.specify/bugs/<bug_slug>/` for bugfix work;
- merged PR descriptions, release notes, self-test output, CI results, and
  reviewer findings.

Read internal enhancement artifacts only when visibility allows it. Public
coding repositories must not copy raw customer demand, private commercial
context, or internal approval discussion into release archives.

## Archive Shape

Create or update two explicitly different destinations:

```text
 .specify/ai-team/releases/private/<release_id>/
|-- evidence-rollup.md
|-- archived-work.yml
`-- privacy-review.md

docs/ai-team/memory/releases/<release_id>/
|-- release-summary.md
|-- shipped-work-index.md
|-- bugfix-lessons.md
|-- feature-decisions.md
`-- migration-playbook.md
```

The private archive is Git-ignored and may contain internal indexes and privacy
review details. The enterprise directory is created only by an explicit,
owner-approved promotion of sanitized summaries and is the only release archive
location intended for commit. Do not copy raw evidence into `docs/` or delete
it unless the team has an explicit retention rule.

## Bugfix Lesson Card

Bugfix learning is first-class. For every non-trivial bugfix, add or update a
lesson card in `bugfix-lessons.md`:

```markdown
## <bug_slug or issue id>: <short symptom>

- **Symptom**:
- **User impact**:
- **Root cause**:
- **Fault pattern**: regression / concurrency / config compatibility /
  integration drift / data shape / dependency / unclear requirement / other
- **Fix pattern**:
- **Code graph nodes changed**:
- **Tests or checks added**:
- **What failed to catch it earlier**:
- **Future detection rule**:
- **Reusable lesson**:
- **Similar modules or projects to inspect**:
- **Privacy classification**:
```

Promote a bugfix lesson into support artifacts when it is likely to repeat:

- update `.specify/ai-team/support/knowledge-map.md` when it changes current
  project facts, module boundaries, capability indexes, test maps, or known
  integration constraints;
- add `.specify/ai-team/memory/department/attempts/<date>-<slug>.md` when it
  is a reviewed internal episode lesson that is not formal guidance;
- add `docs/ai-team/memory/decisions/<date>-<slug>.md` only when a human owner
  made a durable enterprise decision;
- update a skill, command, gate, hook, test, or code graph adapter when the
  lesson should become repeatable behavior.

## Feature Decision Card

For every shipped feature or new-project milestone, add the reusable decisions
that future projects should inherit:

```markdown
## <work_slug>: <feature or milestone>

- **Problem solved**:
- **Accepted scope**:
- **Rejected scope**:
- **Architecture decision**:
- **Reusable design pattern**:
- **Public contracts or compatibility commitments**:
- **Config/default compatibility**:
- **Dependency/license/security decision**:
- **Operations or rollback lesson**:
- **Migration note for similar projects**:
- **Superseded process artifacts**:
```

## Migration Playbook

Use `migration-playbook.md` to capture reusable project design so similar
projects do not start from scratch:

- capability name;
- source work slug or release;
- reusable module/API/config/test pattern;
- required environment or dependency assumptions;
- known anti-patterns from this release;
- adaptation steps for a new project;
- code graph slice or source entry points to inspect first;
- evidence required before reuse is trusted.

This playbook should be public-safe when committed to a coding repository. Put
private customer examples in internal-only memory instead.

## Workflow

1. Identify the release range:
   - prefer `since_tag` -> `target_tag`;
   - otherwise use `work_slugs`;
   - otherwise use a release tracking issue.
2. Collect shipped work:
   - feature work;
   - bugfix work;
   - new-project milestones;
   - template/process changes that affected the release.
3. For each work item, classify:
   - keep as active;
   - archive as done;
   - superseded by release summary;
   - private/internal-only;
   - must remain because audit or incident policy requires it.
4. Write private archive files first. Run the memory adapter ignore setup before
   writing `.specify/ai-team/releases/private/`.
5. Promote durable knowledge:
   - bugfix lessons to department or enterprise attempt memory, knowledge map,
     tests, hooks, or skills;
   - feature architecture decisions to enterprise decision memory or migration
     playbook;
   - repeated AI mistakes to `speckit.ai-team.retrospect`.
6. Update `archived-work.yml` with the status of each `work_slug`:
   - `archived`;
   - `kept-active`;
   - `private-only`;
   - `superseded`;
   - `blocked`.
7. Invoke or follow `speckit.ai-team.memory-consolidate` for each lesson that
   should enter local, department, or enterprise memory.
8. Produce a final release archive report in chat.

## Output Shape

```text
Release archive:
- release id:
- release range:
- work items scanned:
- features archived:
- bugfixes archived:
- new-project milestones archived:
- private artifacts excluded:
- public-safe archive path:
- internal-only archive path, if any:
- bugfix lessons promoted:
- decision memories promoted:
- attempt memories promoted:
- migration playbooks updated:
- support files updated:
- artifacts intentionally retained:
- artifacts superseded:
- required human approver:
- follow-up retrospect commands:
```

## Stop Conditions

Stop and ask when:

- the release range is ambiguous;
- a work item has no stable issue, PR, tag, or `work_slug`;
- raw customer demand would be copied into a public coding repository;
- enterprise files would be written without explicit owner approval and a
  completed privacy review;
- a bugfix lesson implies a new product behavior rather than a defect fix;
- a feature decision changes public compatibility without owner approval;
- deleting or moving raw evidence would violate audit, incident, or retention
  policy;
- memory conflicts with current source, release notes, or owner decisions.
