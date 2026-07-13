# Release Archive and Knowledge Consolidation

AI Team SDD creates useful but verbose work artifacts: specs, plans, tasks,
handoffs, code graph slices, evidence boards, review notes, and bug records.
Those artifacts are valuable while the work is active. At release, milestone,
or maintainer-chosen checkpoint time, keeping every intermediate artifact
equally visible makes the next AI task slower and harder to reason about.

The release archive step is the release-scoped batch form of
`speckit.ai-team.memory-consolidate`. It turns completed work into a smaller
knowledge layer that future agents and humans can reuse. It is a standard
maintenance flow, not a mandatory pre-release gate.

## Why Release Archive Exists

Release archive solves three problems:

1. **Reduce redundant context**: active work needs detailed traces; future work
   needs the distilled reason, decision, test, and lesson.
2. **Preserve bugfix experience**: bugfixes often encode the best operational
   knowledge: symptoms, root causes, missing tests, brittle dependencies, and
   integration drift.
3. **Make design portable**: similar projects should inherit proven module
   patterns, compatibility rules, and migration playbooks instead of rediscovering
   them from old PRs.

## Lifecycle Position

Maintainers may run release archive after release candidate verification, after
final release notes, at a milestone, or at another agreed checkpoint:

```text
feature / bugfix work -> PR -> release candidate verification
-> optional release archive -> release notes / final tag
```

For urgent hotfixes, run it after the incident is stable and the hotfix evidence
is available. Do not block production incident response on knowledge cleanup.

## What Changes At Release Time

Before release:

```text
.specify/ai-team/work/<work_slug>/...      detailed process state
specs/<work_slug>/...                      feature SDD artifacts
.specify/bugs/<bug_slug>/...               bug lifecycle artifacts
PRs, evidence, comments, CI output         merge evidence
```

After release archive:

```text
.specify/ai-team/releases/private/<release_id>/ internal archive and privacy evidence
docs/ai-team/memory/releases/<release_id>/ reviewed enterprise release knowledge
.specify/ai-team/support/knowledge-map.md  updated current project knowledge
.specify/ai-team/support/memory-index.md   indexed decisions and attempt lessons
.specify/ai-team/memory/local/...          local-only contributor memory
.specify/ai-team/memory/department/...     uploaded internal team memory
docs/ai-team/memory/...                    reviewed enterprise memory
```

Raw work traces may remain in place, move to internal-only storage, or be marked
as superseded. The default is **summarize, index, and retain evidence**, not
delete.

## Artifact Contract

`speckit.ai-team.release-archive` creates private records first and promotes a
smaller reviewed subset to enterprise docs:

| File | Purpose |
|---|---|
| `release-summary.md` | Enterprise docs after privacy and owner review: what shipped and why |
| `shipped-work-index.md` | Feature, bugfix, PR, issue, work slug, and evidence links |
| `bugfix-lessons.md` | Curated bugfix lessons and future detection rules |
| `feature-decisions.md` | Durable feature decisions, rejected scope, and compatibility commitments |
| `migration-playbook.md` | Reusable design and implementation patterns for similar projects |
| `evidence-rollup.md` | Private archive: release-level test and deferred evidence |
| `archived-work.yml` | Private archive: status for each work or bug slug |
| `privacy-review.md` | Private archive: what may be promoted and what remains internal |

## Bugfix Knowledge Is Special

Bugfixes should be archived even when the code change was small. A small fix can
teach a large lesson:

- a compatibility default was wrong;
- a retry path was missing;
- an integration environment differed from local mocks;
- a dependency version drifted;
- a code graph edge was misunderstood;
- a previous test only covered the happy path.

Every non-trivial bugfix should answer:

```text
Symptom -> root cause -> fix pattern -> missing detection -> future guard
```

Promote the lesson only as far as evidence supports:

| If the lesson is... | Promote to... |
|---|---|
| one-off debugging episode | local or department attempt memory |
| durable human decision | enterprise decision memory after owner review |
| current project fact | knowledge map |
| repeatable behavior | skill, command, hook, gate, or test |
| reusable design pattern | migration playbook |

Attempt memory is advisory. It becomes binding only after it is converted into a
reviewed skill, knowledge entry, gate, or test.

## Design Portability

Many new projects are hard because prior project designs are trapped in old
PRs, meeting notes, or long specs. `migration-playbook.md` captures reusable
project knowledge in a form that can be loaded early by future AI tasks:

- capability or module pattern;
- source release and work slug;
- APIs, abstract classes, configs, and extension points to reuse;
- code graph entry points to inspect first;
- known constraints and rejected alternatives;
- tests and evidence required before reuse;
- privacy-safe examples.

This is not a copy-paste recipe. It is a starting map for a similar project.

## Public And Private Repositories

The coding repository may contain public-safe release knowledge:

- release summary;
- plan-level architecture decisions;
- public-safe bugfix lessons;
- migration playbook entries that do not reveal customers;
- evidence rollups.

Internal-only repositories may contain:

- raw customer demand;
- commercial context;
- private approval discussion;
- incident details that are not public-safe;
- internal-only debugging artifacts.

When in doubt, keep the raw material private and commit only a sanitized lesson.

## Relationship To Existing Commands

| Command | Scope |
|---|---|
| `speckit.ai-team.context` | one active work item |
| `speckit.ai-team.retrospect` | one failed PR/check/incident/repeated AI mistake |
| `speckit.ai-team.support` | support-layer audit across skills, knowledge, memory |
| `speckit.ai-team.memory-consolidate` | one work item, bugfix, incident, release, or manual lesson |
| `speckit.ai-team.release-archive` | one release or release candidate |

`release-archive` follows the same three-tier memory promotion rules as
`memory-consolidate`. It may recommend follow-up `retrospect` commands when a
release reveals a repeated failure pattern.

## Recommended Prompt

```text
Use speckit.ai-team.release-archive for release_id=v1.4.0 since_tag=v1.3.0
privacy=public-safe.

Focus especially on bugfix lessons and reusable design patterns for future
projects. Do not copy raw customer demand into the coding repository.
```
