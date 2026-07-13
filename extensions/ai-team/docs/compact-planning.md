# Compact Plan And Tasks Mode

Status: bundled in `ai-team-sdd` through `planning_mode=compact`.

## Purpose

Small, low-risk changes should not pay the full coordination cost of separate
Plan and Tasks review cycles when the technical path is already clear. Compact
planning allows one user action and one combined human review while preserving
the two different meanings:

- Plan records technical decisions, boundaries, risks, and verification intent.
- Tasks record execution order, dependencies, file scope, and completion checks.

Compact planning is not permission to skip impact analysis, role isolation,
human accountability, implementation permissions, or evidence.

## Intended Flow

```text
work item -> context and impact analysis -> human selects compact mode
-> architect context writes Implementation Plan
-> isolated developer context derives Execution Tasks
-> combined plan/task check and one human gate
-> implementation permission gate -> implement -> converge -> evidence
```

The architect and developer phases must not share hidden chat context. They
exchange the approved specification, impact evidence, `plan.md`, and an
explicit plan-to-tasks handoff.

## Artifact Contract

Compact mode keeps native Spec Kit artifacts so core commands and resume remain
compatible:

```markdown
# plan.md

## Scope And Assumptions
## Expected Architecture Impact
## Technical Decisions
## Compatibility And Risks
## Verification Strategy

# tasks.md

- [ ] T001 ...
- [ ] T002 ...
```

`plan.md` owns technical decisions and `tasks.md` owns execution. Compact mode
combines the user action and human review, not the meanings of these files.
The workflow input and run state record `planning_mode=compact`, the eligibility
gate, and the combined review result. No additional change manifest is required.

## Eligibility

If the user starts with one sentence and no issue, run the Plain-Language
Intake first. Intake may recommend Compact from read-only impact evidence, but
formal Compact SDD starts only after the issue draft and mode are approved and
the issue URL exists. Feature acceptance remains a Technical Committee or
delegated human decision.

AI may recommend compact planning, but an accountable human must select it
after impact analysis. All of the following must be true:

- requirement and expected behavior are clear;
- implementation path has no unresolved technical alternatives;
- change radius is local or within one module;
- source or code graph evidence identifies the affected path and reuse point;
- failure cost is low and rollback is simple;
- no public API, SPI, schema, event, or compatibility promise changes;
- no database migration or state ownership change;
- no authentication, authorization, security, privacy, or sensitive-data rule
  changes;
- no new critical dependency or dependency-direction change;
- no cross-module coordination or parallel multi-agent implementation;
- no special deployment, gray release, migration, or operational rollback plan;
- the combined artifact can remain short, ordered, and independently verifiable.

File count is only a warning signal. A one-file SPI change can be high risk, and
a five-file local test refactor can still be compact.

## Mandatory Fallback

Use the standard `Spec -> Plan -> Plan Review -> Tasks -> Tasks Review` path when
any eligibility condition is false or uncertain. In particular, do not select
compact mode solely because the request says "simple CRUD", "one config item",
"small project", or "only two files".

Zero-to-one projects use the Standard path. Compact mode is for changes to an
existing architecture whose boundary and runnable spine already exist.

If implementation discovers wider impact, stop, set the compact assessment to
invalidated, preserve completed evidence, and resume from the standard Plan
phase. Do not keep patching the compact task list around a changed design.

## Runtime And Chat Entry

Users do not need to know the workflow parameter. An explicit sentence such as
the following invokes `speckit.ai-team.start`, which launches `ai-team-sdd` with
`planning_mode=compact`:

```text
请用 AI Team Compact 模式实现搜索结果导出，需求单是：<issue URL>
```

An issue is optional at the first chat turn:

```text
请帮我在导出结果里增加 CSV 格式，字段和页面列表保持一致；如果影响很小，可以建议走 Compact。
```

The agent launches `ai-team-intake`, not formal SDD, and handles the CLI on the
user's behalf.

The workflow records the user-selected mode, pauses after impact analysis for
the Compact eligibility decision, runs Plan and Tasks in isolated contexts,
and presents one combined Plan/Tasks review. Reject the eligibility gate and
restart in Standard mode when Compact is invalid.
