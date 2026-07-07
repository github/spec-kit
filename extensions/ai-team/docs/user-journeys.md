# AI Team User Journeys

This document explains how users enter AI Team SDD work and how artifacts
connect across bug fixes, public feature requests, confidential enterprise
features, new projects, and interrupted work.

## Common Setup

Install Spec Kit from this independent distribution, initialize the coding
repository, and add the AI Team extension, handoff-spec preset, and workflows:

```bash
specify init . --integration codex --integration-options="--skills"
specify extension add ai-team
specify preset add ai-team-handoff-spec
specify workflow add ai-team-sdd
specify workflow add ai-team-bugfix
```

The `ai-team-handoff-spec` preset appends handoff spec rules and composite AI Team
gates to native SDD commands (plan gate in checklist, task gate in analyze,
checks/evidence in converge or bug.test). Install the `bug` extension for bugfix
composite evidence. Without it, core commands do not know about
`spec.override.md` or AI Team policy overlays.

Use the integration that matches the active agent: `codex`, `claude`,
`cursor-agent`, or `trae`.

Then configure repository roles with `speckit.ai-team.workspace`:

```text
speckit.ai-team.workspace
```

The workspace contract should name:

- coding repository;
- optional internal-only enhancement repository for confidential enterprise
  demand traceability;
- optional handoff URL pattern for sanitized internal RFCs;
- rules that prevent private enhancement drafts or raw customer demand from
  being committed to public coding repositories.
- issue type/state label policy from [issue-workflow.md](issue-workflow.md).

## Chat Alias Convention

Use stable workflow aliases in chat-first tools so users do not need to
remember command details:

| Chat alias | Workflow input |
|---|---|
| `ai-team-sdd feature path` | `work_type=feature` |
| `ai-team-bugfix path` | `task_id=BUG-<repo-slug>-<issue-number>`, `bug_slug=bug-<repo-slug>-<issue-number>`, and optional `coding_issue_url` |
| `ai-team-sdd new-project path` | `work_type=new-project` |
| `ai-team-sdd resume path` | `task_id=<task-id>` and `resume_from=<phase>` |

Recommended user prompts:

```text
Use the ai-team-sdd feature path for this public coding issue:
https://example.com/org/project/issues/456

Use the ai-team-sdd feature path for this internal handoff requirement:
https://example.com/enhancements/rfcs/REQ-2026-015

Use the ai-team-bugfix path with task_id=BUG-project-alpha-123 and bug_slug=bug-project-alpha-123 for this coding issue:
https://example.com/org/project/issues/123

Use the ai-team-sdd new-project path for this internal handoff requirement:
https://example.com/enhancements/rfcs/REQ-2026-020

Use the ai-team-sdd resume path for task_id=REQ-2026-015 from tasks-ready.
```

## Journey 1: Existing Project Bug Fix

Use this journey when existing behavior is broken, flaky, regressed, or throws
errors.

The preferred path is the dedicated `ai-team-bugfix` workflow. The work item is
a coding repository issue, issue URL, or bug slug. Coding bug issues use
`type/bug`; enhancement-internal must not be used for bug fixes. The reporter
does not need to understand code internals. The AI agent and maintainer derive
the likely source impact from the codebase.

```bash
specify workflow run ai-team-bugfix \
  --input request="Fix the upload timeout reported by customer support" \
  --input task_id=BUG-project-alpha-123 \
  --input bug_slug=bug-project-alpha-123 \
  --input coding_issue_url="https://example.com/org/project/issues/123"
```

Flow:

1. `speckit.ai-team.context` creates or loads the Task Context Package.
2. `speckit.ai-team.start` classifies the request as a bug fix and records the
   coding issue and bug slug.
3. `review-route` confirms this is a bug, not a hidden feature request.
4. `speckit.ai-team.codegraph` runs when the likely fix touches more than a
   trivial local file.
5. `speckit.ai-team.impact` identifies owner module, nearby callers/callees,
   tests, reuse candidates, public contract risks, and stop conditions.
6. `review-impact` decides whether architecture-level, public-contract, or
   cross-module changes are allowed for this bug fix.
7. Run the bug extension for the actual bug workflow, with human gates between
   assessment, fix, and verification:

   ```text
   speckit.bug.assess -> review-assessment
   -> speckit.bug.fix -> review-fix -> speckit.bug.test
   ```

8. `speckit.bug.test` verifies the fix and runs composite checks plus Evidence Board
   (via preset) before PR preparation.
9. Submit with `speckit.ai-team.pr`, linking the coding issue.
10. Review with `speckit.ai-team.review`.

Stop for human decision when expected behavior is actually a new product
behavior, source impact cannot be stated, or the fix needs public SPI/API,
config, schema, state-owner, or cross-module semantic changes.

## Journey 2: Existing Project Public Feature

Use this journey when the requested feature can be discussed in the coding
repository.

The work item is a public coding repository issue or SDD feature request.
Public feature issues use `type/feature` and exactly one `state/*` label:

```bash
specify workflow run ai-team-sdd \
  --input request="Implement public search result export" \
  --input work_type=feature \
  --input coding_issue_url="https://example.com/org/project/issues/456"
```

Flow:

1. `speckit.ai-team.context` records the coding issue URL and current phase.
2. `speckit.ai-team.start` routes the work as an existing-project feature.
3. `speckit.ai-team.codegraph` builds or attaches the source graph slice.
4. `speckit.ai-team.impact` constrains likely modules, public contracts, tests,
   and reuse candidates.
5. `speckit.specify` writes the feature spec from the public issue.
6. `speckit.ai-team.handoff` creates the specify-to-plan handoff so roles do not
   depend on hidden chat.
7. `speckit.plan` creates the architecture plan.
8. `speckit.checklist` runs the native requirements-quality checklist and the
   composite AI Team plan gate (via preset) before the `review-plan` gate.
9. `speckit.tasks` generates implementation tasks.
10. `speckit.analyze` runs the native cross-artifact consistency check and the
    composite AI Team task gate (via preset) before the `review-tasks` gate.
11. `speckit.implement` changes code; `speckit.converge` checks remaining work
    and runs composite checks plus Evidence Board (via preset).
12. `speckit.ai-team.pr` and `speckit.ai-team.review` close the evidence loop.

Stop when the feature lacks an accountable public work item, crosses approved
scope, or needs private customer context that should move to an internal
enhancement issue.

## Journey 3: Existing Project Confidential Enterprise Feature

Use this journey when the demand comes from an enterprise customer, private
roadmap, commercial context, or other source that cannot be public.
`enhancement_internal` is internal-only and used for traceability; enterprise
customers do not need visibility into it. Enhancement-internal issues use
`type/feature` only.

Start in the internal enhancement repository:

```text
speckit.ai-team.requirement
speckit.ai-team.feature-review
```

After the Technical Committee accepts the feature and the maintainer prepares a
sanitized handoff, start the coding workflow:

```bash
specify workflow run ai-team-sdd \
  --input request="Implement REQ-2026-015 search result export" \
  --input work_type=feature \
  --input handoff_requirement_url="https://example.com/enhancements/rfcs/REQ-2026-015"
```

The coding repository should not record raw customer demand or private
enhancement draft paths. Public coding repositories should use a public-safe
summary instead of confidential internal links. Private coding repositories may
pass `handoff_requirement_url` to `speckit.plan`; the `before_plan` hook
(`speckit.ai-team.handoff-spec-sync`) fetches the URL and merges it with
`spec.md` into ignored `spec.override.md` when the preset is installed.

Stop for human decision when no accepted handoff exists, the handoff contains
raw customer demand, Technical Committee acceptance is missing, owner review is
missing, or plan/tasks exceed the approved wave.

## Journey 4: New Project From Zero

Use this journey when creating a new repository, service, application, or
product from scratch.

The work item may be a public project issue/charter or an internal handoff
requirement.

```bash
specify workflow run ai-team-sdd \
  --input request="Create the initial customer notification service" \
  --input work_type=new-project \
  --input bootstrap_workspace=true \
  --input handoff_requirement_url="https://example.com/enhancements/rfcs/REQ-2026-020"
```

New projects still follow the same native SDD command spine with composite gates
via preset: `speckit.checklist` (plan gate), `speckit.analyze` (task gate), and
`speckit.converge` (checks + evidence). The plan gate is stricter for new projects:
it must establish the project skeleton, architecture spine, dependency strategy,
runnable thin slice, self-test strategy, and evidence strategy before broad feature
construction.

Stop for human decision when the project has no charter, work item, or
accountable owner; the plan starts with broad feature construction before a
runnable thin slice; or required runtime, deployment, security, data, or
operations ownership is unclear.

## Journey 5: Resume From The Middle

Use this journey when work was interrupted by human review, tool switching,
closed terminal, lost chat context, failed CI, review comments, or a paused
workflow gate.

Resume by workflow run ID when the same run paused:

```bash
specify workflow status <run-id>
specify workflow resume <run-id>
```

Resume by task ID when the chat, terminal, or AI tool changed:

```text
speckit.ai-team.context task_id=<task-id> resume=true
```

The task ID can be:

- handoff requirement ID or URL slug;
- coding issue number or URL slug;
- `.specify/bugs/<slug>`;
- explicit `task_id=<value>` recorded earlier.

On resume, compare the recorded source snapshot, work item, code graph artifact,
and current repository state. If source or work item changed, rerun
`speckit.ai-team.codegraph` and `speckit.ai-team.impact`.

Stop for human reconciliation when context files disagree, the work item changed
while paused, source changed and impact evidence is stale, or the recorded next
command would skip a required human gate.

## Journey 6: Failure Evolution

Use this journey when a PR fails review, CI fails, a test escapes, or the AI
agent repeats a mistake.

```text
speckit.ai-team.retrospect
```

Classify the failure as context missing, graph missing, skill missing, hook
missing, gate missing, evidence missing, human decision missing, or privacy
leak. Then update the smallest durable artifact: command, gate, knowledge map,
memory entry, test, code graph adapter, or review checklist.
