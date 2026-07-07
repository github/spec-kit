# Repository Boundary

AI Team SDD separates public coding work from confidential enterprise demand.

```text
org/
|-- enhancement-internal/      # strict-permission internal enhancement repo
|   |-- issues/                # private discussion, approval, wave plan
|   `-- rfcs/
|       `-- REQ-2026-015.md    # sanitized handoff requirement
`-- project-alpha/             # coding repository
    |-- issues/456             # public feature or bug work item
    |-- src/
    `-- .specify/
```

## Rules

1. Public feature requests can start directly as coding repository issues or SDD
   feature requests.
2. Confidential enterprise requirements start in `enhancement-internal`, not in
   the coding repository.
3. Internal enhancement issues own raw demand, private drafts, approval
   discussion, wave planning, commercial context, and private acceptance notes.
4. Sanitized handoff RFCs under `enhancement-internal/rfcs/` are the stable
   bridge from private demand to coding work.
5. Public coding repositories must not record internal enhancement issue URLs,
   raw customer demand, commercial context, or private acceptance notes. Use a
   public-safe summary instead.
6. Private coding repositories may link an internal handoff URL when the
   organization allows it.
7. Local paths are never the authoritative work-item identity. Use a coding
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
