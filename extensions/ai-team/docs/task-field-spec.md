# Task Field Specification

AI Team workflows use stable fields so work can resume across terminals, AI
tools, PR reviews, and human approval pauses.

## Required Identity Fields

| Field | Required when | Meaning |
|---|---|---|
| `work_type` | every task | `bug`, `feature`, `new-project`, or `template` |
| `task_id` | every durable task | AI Team stable task identity and `.specify/ai-team/tasks/<task-id>/` directory name |
| `work_item.type` | every durable task | source kind: `coding_bug`, `coding_feature`, `internal_handoff`, `project_charter`, or `template_change` |
| `coding_issue_url` | public bug or public feature | canonical coding repository issue URL |
| `bug_slug` | bug workflows | bug extension slug used by `.specify/bugs/<bug_slug>/` |
| `handoff_requirement_url` | confidential enterprise feature | sanitized internal enhancement handoff URL |
| `published_requirement_url` | legacy only | deprecated compatibility alias for `handoff_requirement_url` |
| `issue.type_label` | issue-backed tasks | `type/feature` or `type/bug`; enhancement-internal allows `type/feature` only |
| `issue.state_label` | issue-backed tasks | one of the AI Team `state/*` labels |

Do not use a mutable issue title, chat summary, local file path, or branch name
as the stable identity.

## Canonical `task_id`

Use these patterns:

| Work item | Pattern | Example |
|---|---|---|
| coding bug issue | `BUG-<repo-slug>-<issue-number>` | `BUG-project-alpha-123` |
| coding public feature issue | `FEAT-<repo-slug>-<issue-number>` | `FEAT-project-alpha-456` |
| internal enhancement handoff | `REQ-YYYY-NNN` | `REQ-2026-015` |
| new project charter | `PROJ-<repo-slug-or-charter-slug>` | `PROJ-customer-notification` |
| template/distribution change | `TPL-<repo-slug>-<issue-or-pr-number>` | `TPL-spec-kit-1` |

`repo-slug` should be lower-kebab-case from the repository name, without owner
or organization. For example, `EuphoriaYan/project-alpha` becomes
`project-alpha`.

## Bug `bug_slug`

The bug extension stores assessment, fix, and verification files under:

```text
.specify/bugs/<bug_slug>/
```

For workflow runs, provide a deterministic `bug_slug` so
`speckit.bug.assess`, `speckit.bug.fix`, and `speckit.bug.test` all refer to
the same bug directory.

Recommended pattern:

```text
bug-<repo-slug>-<issue-number>
```

Example:

```yaml
task_id: BUG-project-alpha-123
work_type: bug
work_item:
  type: coding_bug
  coding_issue_url: https://example.com/org/project-alpha/issues/123
  bug_slug: bug-project-alpha-123
```

If there is no issue yet, create a coding issue first when possible. If that is
not possible, use a concise lower-kebab bug slug and replace it with the issue
identity once the issue exists.

## Feature Work Items

Public feature:

```yaml
task_id: FEAT-project-alpha-456
work_type: feature
work_item:
  type: coding_feature
  coding_issue_url: https://example.com/org/project-alpha/issues/456
```

Confidential enterprise feature:

```yaml
task_id: REQ-2026-015
work_type: feature
work_item:
  type: internal_handoff
  handoff_requirement_url: https://example.com/enhancements/rfcs/REQ-2026-015
```

Enhancement-internal feature issues must use `type/feature` and exactly one of:

```text
state/draft
state/accepted
state/working
state/finished
state/rejected
state/closed
state/superseded
```

Bug fixes must use coding repository issues, not enhancement-internal issues.

Public coding repositories should not link confidential internal demand records
unless the organization explicitly allows it. Use a public-safe summary in the
PR and keep private traceability in approved internal channels.

## Backward Compatibility

`published_requirement_url` is accepted only as a deprecated alias for older
AI Team runs. New workflows and docs should use `handoff_requirement_url`.
