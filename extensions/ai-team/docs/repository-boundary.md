# Repository Boundary

AI Team SDD separates private demand, published requirements, and code.

```text
org/
|-- requirements-published/    # public/read-only requirement repository
|   `-- rfcs/
|       `-- REQ-2024-015.md
|-- requirements-internal/     # strict-permission private repository
|   `-- drafts/
`-- project-alpha/             # coding repository
    |-- src/
    `-- requirements/          # Git submodule -> requirements-published
        `-- rfcs/
            `-- REQ-2024-015.md
```

## Rules

1. The coding repository pulls only `requirements-published`, normally through
   a read-only Git submodule such as `requirements/`.
2. The coding repository does not know `requirements-internal` exists. Do not
   commit private repository URLs, paths, branch names, issue links, or raw
   customer demand into coding artifacts.
3. New feature implementation references the stable published requirement URL,
   not a local submodule path.
4. Local submodule files are a cache for reading published content. They are not
   the authoritative work-item identity.
5. Private drafts, approval discussion, commercial context, and unpublished
   acceptance details stay in `requirements-internal`.
6. Public SDD artifacts may include plan, tasks, code graph impact, Evidence
   Board, and sanitized acceptance intent only after publication.

## Command Mapping

| Work | Repository | Command |
|---|---|---|
| create or refine private feature intent | requirements-internal | `speckit.ai-team.requirement` |
| publish sanitized requirement/RFC | requirements-published | `speckit.ai-team.requirement` |
| route a user request | current workspace | `speckit.ai-team.start` |
| plan/implement feature | coding repository | `speckit.specify`, `speckit.plan`, `speckit.tasks`, `speckit.implement` |
| inspect impact before code edits | coding repository | `speckit.ai-team.impact` |
| verify and submit | coding repository | `speckit.ai-team.checks`, `speckit.ai-team.pr` |

## Feature Reference Shape

Use a URL:

```text
Published requirement: https://example.com/org/requirements-published/rfcs/REQ-2024-015.md
```

Do not use a local path as the authoritative feature reference:

```text
requirements/rfcs/REQ-2024-015.md
```

The local path may appear only as supporting evidence that the published
requirements submodule was read.
