# AI Team User Journeys

This document explains how users enter AI Team SDD work and how the repository
artifacts connect across bug fixes, existing-project features, new projects,
and interrupted work.

## Common Setup

Install Spec Kit from this independent distribution, initialize the coding
repository, and add the AI Team extension:

```bash
specify init . --integration codex --integration-options="--skills"
specify extension add ai-team
specify workflow add ai-team-sdd
```

Use the integration that matches the active agent: `codex`, `claude`,
`cursor-agent`, or `trae`.

Then configure the repository roles with `speckit.ai-team.workspace`:

```text
speckit.ai-team.workspace
```

The workspace contract should name:

- coding repository;
- requirements-published repository or published requirement URL pattern;
- optional read-only `requirements/` submodule path;
- rules that prevent requirements-internal paths or raw customer demand from
  being committed to the coding repository.

## Journey 1: Existing Project Bug Fix

Use this journey when existing behavior is broken, flaky, regressed, or throws
errors.

### Entry

The work item is a coding repository issue, issue URL, or bug slug. The reporter
does not need to understand code internals. The AI agent and maintainer derive
the likely source impact from the codebase.

```bash
specify workflow run ai-team-sdd \
  --input request="Fix the upload timeout reported by customer support" \
  --input work_type=bug \
  --input coding_issue_url="https://example.com/org/project/issues/123"
```

### Flow

1. `speckit.ai-team.context` creates or loads the Task Context Package.
2. `speckit.ai-team.start` classifies the request as a bug fix and records the
   coding issue or bug slug.
3. `speckit.ai-team.codegraph` runs when the likely fix touches more than a
   trivial local file.
4. `speckit.ai-team.impact` identifies owner module, nearby callers/callees,
   tests, reuse candidates, and stop conditions.
5. Run the bug extension for the actual bug workflow:

   ```text
   speckit.bug.assess -> speckit.bug.fix -> speckit.bug.test
   ```

6. Run `speckit.ai-team.checks` and `speckit.ai-team.evidence`.
7. Submit with `speckit.ai-team.pr`, linking the coding issue.
8. Review with `speckit.ai-team.review`.

### Stop Conditions

Stop for human decision when:

- the expected behavior is actually a new product behavior;
- the fix needs public SPI/API, config, schema, state-owner, or cross-module
  semantic changes;
- source impact cannot be stated from code graph or source evidence;
- there is no coding issue, bug slug, or equivalent bug work item.

## Journey 2: Existing Project New Feature

Use this journey when a user wants a new capability, public behavior,
integration, scenario, or roadmap item in an existing project.

### Entry

The work item is a published requirement URL from the requirements-published
repository. Private drafts and customer discussions stay in
requirements-internal.

If the user only has raw demand, start with:

```text
speckit.ai-team.requirement
speckit.ai-team.feature-review
```

After the technical committee accepts or delegates the feature decision, start
the coding workflow:

```bash
specify workflow run ai-team-sdd \
  --input request="Implement REQ-2026-015 search result export" \
  --input work_type=feature \
  --input published_requirement_url="https://example.com/requirements/rfcs/REQ-2026-015"
```

### Flow

1. `speckit.ai-team.context` records the published requirement URL and current
   phase.
2. `speckit.ai-team.start` routes the work as an existing-project feature.
3. `speckit.ai-team.codegraph` builds or attaches the source graph slice.
4. `speckit.ai-team.impact` constrains likely modules, public contracts, tests,
   and reuse candidates.
5. `speckit.specify` writes the feature spec from the published requirement.
6. `speckit.ai-team.handoff` creates the specify-to-plan handoff so the
   architect does not depend on hidden product-manager chat.
7. `speckit.plan` creates the public technical plan.
8. `speckit.ai-team.plan-gate` checks architecture fit, privacy, code graph
   impact, compatibility, and owner decisions.
9. `speckit.tasks` creates developer tasks.
10. `speckit.ai-team.task-gate` checks task order, self-test mapping, and
    impact radius.
11. `speckit.implement` changes code.
12. `speckit.ai-team.checks`, `speckit.ai-team.evidence`, `speckit.ai-team.pr`,
    and `speckit.ai-team.review` close the evidence loop.

### Stop Conditions

Stop for human decision when:

- no published requirement URL exists;
- the requirement is still private or contains raw customer demand;
- technical committee acceptance or delegated approval is missing;
- code graph impact crosses module or public interface boundaries without
  owner review;
- plan or tasks exceed the approved wave.

## Journey 3: New Project From Zero

Use this journey when creating a new repository, service, application, or
product from scratch.

### Entry

The work item should be a published project charter or published requirement
URL. If the charter starts in private discussion, publish a sanitized version
first through `speckit.ai-team.requirement`.

```bash
specify workflow run ai-team-sdd \
  --input request="Create the initial customer notification service" \
  --input work_type=new-project \
  --input bootstrap_workspace=true \
  --input published_requirement_url="https://example.com/requirements/rfcs/REQ-2026-020"
```

### Flow

1. Bootstrap the project with Spec Kit `init` through the workflow or by running
   `specify init` directly.
2. `speckit.ai-team.workspace` records repository roles and privacy boundaries.
3. `speckit.ai-team.context` creates the Task Context Package.
4. `speckit.specify` writes the product spec from the published charter.
5. `speckit.ai-team.handoff` isolates the specify-to-plan transition.
6. `speckit.plan` creates the architecture plan.
7. `speckit.ai-team.plan-gate` requires a strict build-from-zero plan:
   project skeleton, architecture spine, dependency strategy, runnable thin
   slice, self-test strategy, evidence strategy, and release/operations owner
   when relevant.
8. `speckit.tasks` creates tasks that produce the runnable spine before breadth.
9. `speckit.ai-team.task-gate` blocks tasks that delay build/run/test setup too
   long.
10. `speckit.implement` builds the first wave.
11. `speckit.ai-team.checks` and `speckit.ai-team.evidence` prove the thin
    slice runs.

### Stop Conditions

Stop for human decision when:

- the project has no charter, published requirement URL, or accountable owner;
- the plan starts with broad feature construction before a runnable thin slice;
- required runtime, deployment, security, data, or operations ownership is
  unclear;
- dependency/license review is missing for load-bearing components.

## Journey 4: Resume From The Middle

Use this journey when work was interrupted by human review, tool switching,
closed terminal, lost chat context, failed CI, review comments, or a paused
workflow gate.

### Entry

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

- published requirement ID or URL slug;
- coding issue number or URL slug;
- `.specify/bugs/<slug>`;
- explicit `task_id=<value>` recorded earlier.

### Flow

1. Load `.specify/ai-team/tasks/<task-id>/state.yml`.
2. Load `.specify/ai-team/tasks/<task-id>/context-pack.md`.
3. Compare the recorded source snapshot, published requirement or bug issue,
   code graph artifact, and current repository state.
4. If source or requirement changed, rerun `speckit.ai-team.codegraph` and
   `speckit.ai-team.impact`.
5. Continue from `next_command` only when stop conditions are clear.
6. Update the context pack after every major phase.

### Stop Conditions

Stop for human reconciliation when:

- `state.yml` and `context-pack.md` disagree;
- the published requirement or coding issue changed while the work was paused;
- source changed and the existing impact evidence is stale;
- the recorded next command would skip a required human gate.

## Journey 5: Failure Evolution

Use this journey when a PR fails review, CI fails, a test escapes, or the AI
agent repeats a mistake.

```text
speckit.ai-team.retrospect
```

Classify the failure as context missing, graph missing, skill missing, hook
missing, gate missing, evidence missing, human decision missing, or privacy
leak. Then update the smallest durable artifact: command, gate, knowledge map,
memory entry, test, code graph adapter, or review checklist.

The goal is not to make the prompt larger. The goal is to make the next run
load the right context, graph, gate, or evidence automatically.
