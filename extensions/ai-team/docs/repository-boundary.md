# Repository Boundary

AI Team SDD separates coding work from internal confidential demand records.

```text
org/
|-- enhancement-internal/      # strict-permission internal traceability repo
|   |-- issues/                # private feature demand, approval, wave plan
|   `-- rfcs/
|       `-- REQ-2026-015.md    # sanitized handoff requirement
`-- project-alpha/             # coding repository
    |-- issues/456             # public feature or bug work item
    |-- src/
    `-- .specify/
```

## Rules

1. Coding repositories use issues for both bug fixes and public features.
2. `enhancement-internal` is internal-only and exists for traceability of
   confidential feature demand; enterprise customers do not need visibility.
3. Enhancement-internal issues must use `type/feature`; bug fixes are forbidden
   there and must be filed in the coding repository.
4. Coding repository issues use `type/bug` for bug fixes and `type/feature` for
   feature work.
5. Both repositories use the state label lifecycle in
   [issue-workflow.md](issue-workflow.md).
6. Internal enhancement issues own raw demand, private drafts, approval
   discussion, wave planning, commercial context, and private acceptance notes.
7. Sanitized handoff RFCs under `enhancement-internal/rfcs/` or allowed issue
   URLs are the stable bridge from private demand to coding work.
8. Public coding repositories must not record internal enhancement issue URLs,
   raw customer demand, commercial context, or private acceptance notes. Use a
   public-safe summary instead.
9. Private coding repositories may link an internal handoff URL when the
   organization allows it.
10. Local paths are never the authoritative work-item identity. Use a coding
   issue URL, handoff URL, or explicit task ID.

## Command Mapping

| Work | Repository | Command |
|---|---|---|
| create or refine confidential feature intent | enhancement-internal | `speckit.ai-team.requirement` |
| create sanitized handoff requirement | enhancement-internal | `speckit.ai-team.requirement` |
| route a user request | current workspace | `speckit.ai-team.start` |
| plan/implement feature | coding repository | `speckit.specify`, `speckit.plan`, `speckit.tasks`, `speckit.implement` |
| inspect impact before code edits | coding repository | `speckit.ai-team.impact` |
| verify and submit | coding repository | `speckit.ai-team.checks`, `speckit.ai-team.pr` |

## Feature Reference Shape

Public feature work can use a coding issue URL:

```text
Coding issue: https://example.com/org/project/issues/456
```

Confidential enterprise feature work can use an internal handoff URL only where
visibility allows it:

```text
Handoff requirement: https://example.com/org/enhancement-internal/rfcs/REQ-2026-015.md
```

Do not use a local path as the authoritative feature reference:

```text
rfcs/REQ-2026-015.md
```

The local path may appear only as supporting evidence that the approved handoff
artifact was read.
