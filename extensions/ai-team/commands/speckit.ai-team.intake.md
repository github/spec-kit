---
description: "Classify an unanchored request and produce read-only impact evidence plus an Issue draft."
---

# AI Team Intake

Handle a request that does not yet have a coding issue, project charter, or
confidential requirement handoff. Intake owns normalization, classification,
read-only impact evidence, and the Issue draft. It does not approve features,
publish issues, create formal Work Context, or launch formal SDD.

## User Input

```text
$ARGUMENTS
```

## Local Artifacts

Use `.specify/ai-team/intake/<intake_slug>/`:

```text
intake.yml              # resolved classification, privacy, recommendation, approval evidence
request.md              # concise user wording; never copy confidential text publicly
impact-summary.md       # links to Code Graph or source-structure evidence
issue-draft.md          # proposed issue body and labels
result.yml              # written later by deterministic workflow scripts
```

These are provisional local workflow artifacts. Do not commit them merely to
start work. Durable formal context begins under
`.specify/ai-team/work/<work_slug>/` after a work item exists.

## Mode: Analyze

1. Preserve the user's original intent in `request.md` and assign a safe,
   lower-kebab `intake_slug`.
2. Classify provisionally as `bug`, `feature`, `new-project`, or `unclear`. Ask one focused
   question only when bug versus feature changes the repository or approval
   route.
3. Classify publication as `public-safe`, `confidential`, or `unknown`. Never
   publish `unknown` or confidential text to a public coding repository.
4. Create only an analysis Permission Envelope. Read source, tests, module
   ownership, history, and Code Graph; do not edit product source or create a
   formal Spec Kit feature directory.
5. Record likely modules, reuse candidates, contracts at risk, expected change
   radius, and evidence gaps.
6. Write `intake.yml` with this machine-readable contract before asking for the
   boundary review:

```yaml
work_type: bug | feature | new-project
privacy_class: public-safe | confidential
planning_mode: standard | compact
feature_decision_evidence: not-applicable | unreviewed | accepted
feature_approver:
feature_approver_role:
```

`work_type=auto` is allowed only as input to this analysis. It must be resolved
to `bug`, `feature`, or `new-project` in `intake.yml`; otherwise the review must
be revised or rejected and no formal workflow may start. `new-project` always
uses Standard planning and publishes a `type/feature` work item.

## Mode: Draft

Create `issue-draft.md` from the request and impact evidence. It must contain:

```yaml
---
title: <public-safe issue title>
type_label: type/bug | type/feature
target_repository: owner/repository
---
```

- observable problem or desired behavior;
- affected users and acceptance examples;
- work type and target repository;
- likely modules and current architecture impact;
- public API/SPI/config/schema/dependency flags;
- validation expected and known unknowns;
- proposed labels: exactly one `type/*` and `state/draft`;
- recommended planning mode with reasons and mandatory fallback conditions.

Recommend Compact only for an existing project when evidence shows a local or
single-module change, a clear reuse path, no public-contract or migration
change, no security/privacy or critical-dependency decision, and simple
rollback. Words such as "small" or "quick" are not evidence. AI recommends;
the human gate selects.

Feature acceptance is owned by `speckit.ai-team.feature-review` and the
Technical Committee or delegated authority. Intake may copy verifiable approval
evidence into `intake.yml`; it must not create that decision. Without such
evidence, the Issue remains `state/draft` after publication.

## Handoff To Workflow

Intake ends after returning its artifacts and recommendation:

```text
AI Team Intake Result:
- intake slug:
- classification:
- privacy class:
- issue draft path:
- impact evidence path:
- planning recommendation:
- feature acceptance evidence, if supplied:
- unresolved questions:
- stop conditions:
```

The `ai-team-intake` workflow owns review loops, publication, waiting states,
and formal workflow routing. Intake must not invoke or reproduce those steps.

## Stop Conditions

Stop without completing the Intake draft when:

- classification, repository visibility, or target repository is unresolved;
- issue body and analyzed request disagree;
- required read-only impact evidence is missing;
- Intake claims a Feature is accepted without external Technical Committee or
  delegated approval evidence;
- Compact was selected without qualifying impact evidence;
- confidential demand would be copied into a public-safe draft.
