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
specify extension add bug
specify preset add ai-team-sdd-governance
specify workflow add ai-team-sdd
specify workflow add ai-team-bugfix
```

The `ai-team-sdd-governance` preset composes handoff spec rules and composite AI Team
gates into native SDD commands (checks/evidence in converge
or bug.test). Plan check is `speckit.ai-team.plan-check` (chat report, not preset).
The `bug` extension is required for bugfix composite evidence on `speckit.bug.test`.
Without the preset, core commands do not know about `spec.override.md` or AI Team
policy overlays.

## SDD checks: extension, preset, and workflow

AI Team feature work uses three cooperating layers:

| Layer | What runs | Typical output |
|---|---|---|
| **Extension** | `speckit.ai-team.plan-check` after `speckit.plan` | Plan Check Report in **chat**; `plan_check` summary in work context |
| **Preset** | `ai-team-sdd-governance` on `converge`, `bug.test` | Handoff spec rules; composite checks, Evidence Board |
| **Workflow** | `review-plan`, `review-tasks`, … | **Human** approve / revise / reject |

The bundled `ai-team-sdd` workflow does **not** include core `speckit.checklist`.
Checklist files (`checklists/*.md`) and checkbox gating in `speckit.implement` are
Spec Kit core behavior when you run checklist manually — they are not part of the
default AI Team SDD path.

**Revise loop:** When `review-plan` returns revise, update `plan.md` via
`speckit.plan`, re-run `speckit.ai-team.plan-check`, and approve only when the
Plan Check Report status is `pass`.

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
| `ai-team-sdd compact path` | `work_type=feature`, `planning_mode=compact` |
| `ai-team-bugfix path` | `work_slug=bug-<repo-slug>-<issue-number>` and required `coding_issue_url` |
| `ai-team-sdd new-project path` | `work_type=new-project` |
| `ai-team-sdd resume path` | `work_slug=<work_slug>` and `resume_from=<phase>` |
| `ai-team-memory consolidate path` | `scope=<work-item|bugfix|feature|incident|release>` plus `target_tier=<local|department|enterprise>` |
| `ai-team-release archive path` | `release_id=<version>` plus tag range, release issue, or work slugs |

`ai-team-sdd compact path` is a real branch of the bundled `ai-team-sdd`
workflow. The user can select it in ordinary language; the AI tool launches the
workflow and supplies the input.

Recommended user prompts:

```text
Use the ai-team-sdd feature path for this public coding issue:
https://example.com/org/project/issues/456

Use the ai-team-sdd feature path for this internal handoff requirement:
https://example.com/enhancements/rfcs/REQ-2026-015

请用 AI Team Compact 模式实现搜索结果导出，需求单是：
https://example.com/org/project/issues/456

Use the ai-team-bugfix path with work_slug=bug-project-alpha-123 for this coding issue:
https://example.com/org/project/issues/123

Use the ai-team-sdd new-project path for this internal handoff requirement:
https://example.com/enhancements/rfcs/REQ-2026-020

Use the ai-team-sdd resume path for work_slug=003-search-export from tasks-ready.

Use the ai-team-memory consolidate path for bug_slug=bug-project-alpha-123
target_tier=department. Summarize the bugfix lesson after sanitizing private
details.

Use the ai-team-release archive path for release_id=v1.4.0 since_tag=v1.3.0.
Focus on bugfix lessons and reusable design patterns.
```

## Journey 1: Existing Project Bug Fix

Use this journey when existing behavior is broken, flaky, regressed, or throws
errors.

The preferred path is the dedicated `ai-team-bugfix` workflow. The work item is
a coding repository issue URL; `work_slug` identifies the local bug artifacts.
Coding bug issues use
`type/bug`; enhancement-internal must not be used for bug fixes. The reporter
does not need to understand code internals. The AI agent and maintainer derive
the likely source impact from the codebase.

```bash
specify workflow run ai-team-bugfix \
  --input request="Fix the upload timeout reported by customer support" \
  --input work_slug=bug-project-alpha-123 \
  --input coding_issue_url="https://example.com/org/project/issues/123"
```

When issue 456 is another symptom of the same root cause, add
`--input also_resolves_issue_urls="https://example.com/org/project/issues/456"`.
Use separate PRs when root cause, approved scope, rollback, or release risk
differs.

Flow:

1. `speckit.ai-team.context` creates or loads the Work Context Package from
   workflow inputs (`work_slug`, primary `coding_issue_url`, and optional
   `also_resolves_issue_urls`).
2. `speckit.ai-team.permissions mode=analysis` records the smallest required
   read, command, and network boundary. `review-context` confirms the bug work
   item, linked issues, permission boundary, and resume point.
3. `speckit.ai-team.codegraph` runs inside that analysis boundary when the
   likely fix touches more than a
   trivial local file.
4. `speckit.ai-team.impact` identifies owner module, nearby callers/callees,
   tests, reuse candidates, public contract risks, and stop conditions.
5. `review-impact` decides whether architecture-level, public-contract, or
   cross-module changes are allowed for this bug fix.
6. Run bug assessment, then derive an implementation Permission Envelope from
   the approved remediation. A human reviews write paths, commands, network
   access, and the effective enforcement mode before source edits.
7. Run the bug extension for the actual bug workflow, with human gates between
   assessment, fix, and verification:

   ```text
   speckit.bug.assess -> review-assessment
   -> speckit.bug.fix -> review-fix -> speckit.bug.test
   ```

8. `speckit.bug.test` verifies the fix and runs composite checks plus Evidence Board
   (via preset) before PR preparation. Each linked issue maps to its own
   reproduction and verification evidence.
9. Submit with `speckit.ai-team.pr`, linking every resolved coding issue.
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

1. `speckit.ai-team.context` records the coding issue URL and current phase from
   workflow inputs.
2. `speckit.ai-team.permissions mode=analysis` declares the source and tool
   access needed for planning. `review-context` confirms that boundary before
   code graph and SDD steps.
3. `speckit.ai-team.codegraph` builds or attaches the source graph slice inside
   the approved analysis boundary.
4. `speckit.ai-team.impact` constrains likely modules, public contracts, tests,
   and reuse candidates.
5. `speckit.specify` writes the feature spec from the public issue.
6. `speckit.ai-team.handoff` creates the specify-to-plan handoff so roles do not
   depend on hidden chat.
7. `speckit.plan` creates the architecture plan.
8. `speckit.ai-team.plan-check` outputs a Plan Check Report in chat and updates work
   context before the `review-plan` gate.
9. A human approves or revises at the `review-plan` gate. On **revise**, the
   workflow re-runs steps 7–8 (`plan-cycle` do-while) before continuing.
10. `speckit.tasks` generates implementation tasks.
11. `speckit.analyze` runs the native cross-artifact consistency check before the
    `review-tasks` gate.
12. `speckit.ai-team.permissions mode=implementation` derives intended write
    paths, commands, network access, and approval requirements from the approved
    plan and tasks. A human reviews the envelope before source edits.
13. `speckit.implement` changes code; `speckit.converge` checks remaining work
    and runs composite checks plus Evidence Board (via preset).
14. `speckit.ai-team.pr` and `speckit.ai-team.review` close the evidence loop.

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
via preset: `speckit.converge` (checks + evidence). Native `speckit.analyze` is read-only.
`speckit.ai-team.plan-check` (chat report) is stricter for new projects: it must
establish the project skeleton, architecture spine, dependency strategy, runnable
thin slice, self-test strategy, and evidence strategy before broad feature
construction. The implementation Permission Envelope should initially allow
only that skeleton and thin slice; broad repository writes require a revised
plan and another human permission review.

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
speckit.ai-team.context work_slug=<work_slug> resume=true
```

The task ID can be:

- handoff requirement ID or URL slug;
- coding issue number or URL slug;
- `.specify/bugs/<slug>`;
- explicit `work_slug=<value>` recorded earlier.

On resume, load `work-context.yml`, `context-pack.md`, and
`permission-envelope.yml`, then resolve Spec, Plan, Tasks, or bug reports from
their native locations. Compare the recorded source snapshot, work item,
permission boundary, code graph
artifact, and current repository state. If source or work item changed, rerun
`speckit.ai-team.permissions mode=analysis`, `speckit.ai-team.codegraph`, and
`speckit.ai-team.impact`. Never assume an earlier permission approval still
covers a changed plan or source snapshot.

Stop for human reconciliation when context files disagree, the work item changed
while paused, source changed and impact evidence is stale, or the recorded next
command would skip a required human gate. Also stop when hard confinement is
required but the recorded enforcement mode is only `policy-only`.

## Journey 6: Compact Plan And Tasks

### Starting without an issue

A user may begin with only a natural-language request:

```text
请帮我在导出结果里增加 CSV 格式，字段和页面列表保持一致；如果影响很小，可以建议走 Compact。
```

`speckit.ai-team.start` launches `ai-team-intake`. Intake performs only
read-only context, Code Graph, and impact analysis; writes a local issue draft;
and lets AI recommend Standard or Compact. The human approves the issue draft,
publication target, and planning choice. The system then creates the coding
issue and launches the formal workflow. A feature stops at `state/draft` until
Technical Committee or delegated acceptance is recorded.

Use this mode only for clear, low-risk work whose impact analysis
shows a local or single-module change. The user starts one planning action, but
the workflow still isolates the architect context from the developer context:

```text
impact evidence -> human compact selection
-> Implementation Plan -> isolated handoff -> Execution Tasks
-> combined review -> implementation permission review -> implement
```

The workflow preserves native `plan.md` and `tasks.md`, isolates the architect
and developer contexts with a handoff, and combines their human review into one
gate.

Fall back to the standard journey when the change affects public contracts,
database state, security/privacy, dependencies, multiple modules, deployment or
rollback behavior, or when any technical choice remains unresolved. New
projects use the Standard journey.

## Journey 7: Failure Evolution

Use this journey when a PR fails review, CI fails, a test escapes, or the AI
agent repeats a mistake.

```text
speckit.ai-team.retrospect
```

Classify the failure as context missing, graph missing, skill missing, hook
missing, gate missing, evidence missing, human decision missing, or privacy
leak. Then update the smallest durable artifact: command, gate, knowledge map,
memory entry, test, code graph adapter, or review checklist.

## Journey 7: Memory Consolidation

Use this journey when a contributor or maintainer has a useful lesson from a
completed feature, bugfix, review, incident, or migration.

```text
speckit.ai-team.memory-consolidate scope=bugfix bug_slug=bug-project-alpha-123 target_tier=department privacy=department-internal memory_service=mem0
```

Flow:

1. Identify the source: work slug, bug slug, issue, PR, incident, release, or
   manual note.
2. Load the relevant Work Context Package, specs, bug artifacts, code graph,
   evidence, PR comments, and review findings.
3. Sanitize the lesson:
   - remove raw customer demand;
   - remove secrets and commercial context;
   - separate fact, decision, inference, and opinion;
   - link evidence instead of copying large traces.
4. Choose the target tier:
   - `local` for contributor-only notes that are not uploaded;
   - `department` for uploaded internal team memory that is not formal docs;
   - `enterprise` for reviewed guidance stored under `docs/` and carried with
     formal project/release knowledge.
5. Write a structured memory card and update the relevant index.
6. Sync to a mem0-like service only when namespace, privacy, and access boundary
   are configured.
7. Recommend whether the memory should become a skill, test, hook, gate,
   knowledge-map entry, or code graph rule.

Stop when the tier is unclear, a contributor is publishing someone else's local
memory, a department lesson is being treated as enterprise guidance, or owner
approval is missing for enterprise memory.

Bugfix memory is especially valuable. Prefer a short card with symptom, root
cause, fix pattern, missing detection, future guard, and similar modules to
inspect.

## Journey 8: Release Archive and Knowledge Consolidation

Use this journey when a release candidate or final release is ready and the
team needs to reduce active context, preserve lessons, and make the release
useful for future projects. Maintainers may also run it at any milestone or
checkpoint; it is not a mandatory pre-release gate.

```text
speckit.ai-team.release-archive release_id=v1.4.0 since_tag=v1.3.0 privacy=public-safe
```

Flow:

1. Identify the release range from tags, release branch, release tracking issue,
   or explicit `work_slugs`.
2. Read completed Work Context Packages, specs, bug artifacts, PR evidence,
   release verification, and code graph summaries.
3. Create the ignored private archive under
   `.specify/ai-team/releases/private/<release_id>/`.
4. Promote only approved, sanitized summaries to
   `docs/ai-team/memory/releases/<release_id>/`.
5. Produce the private evidence/index files and reviewed enterprise summaries:
   - release summary;
   - shipped work index;
   - bugfix lessons;
   - feature decisions;
   - migration playbook;
   - evidence rollup;
   - archived work status;
   - privacy review.
6. Promote durable knowledge:
   - bugfix symptoms, root causes, missing detections, and future guards to
     local, department, or enterprise memory, tests, hooks, or skills;
   - accepted architecture and compatibility choices to decision memory;
   - reusable module/API/config/test patterns to the migration playbook and
     knowledge map.
6. Mark task-level work context as archived, retained, private-only,
   superseded, or blocked. Do not delete evidence unless retention policy says
   so.
7. Run `speckit.ai-team.support` when the release archive changes Skill,
   Knowledge, or Memory support files.

Stop when the release range is ambiguous, work items have no stable identity,
raw customer demand would enter a public repository, or archive changes imply a
new public compatibility decision without owner approval.

Bugfix lessons are especially important. A small bugfix may be the only place
that records a missing test, integration drift, code graph misunderstanding,
or compatibility default. Preserve that lesson in a short card even when the
patch itself was small.
