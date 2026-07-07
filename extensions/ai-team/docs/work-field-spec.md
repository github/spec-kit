# Work Field Specification

AI Team workflows use stable fields so work can resume across terminals, AI
tools, PR reviews, and human approval pauses.

## Required Identity Fields

| Field | Required when | Meaning |
|---|---|---|
| `work_type` | every work unit | `bug`, `feature`, `new-project`, or `template` |
| `work_slug` | every durable work unit | Stable work identity and `.specify/ai-team/work/<work_slug>/` directory name |
| `work_item.type` | every durable work unit | source kind: `coding_bug`, `coding_feature`, `internal_handoff`, `project_charter`, or `template_change` |
| `coding_issue_url` | public bug or public feature | canonical coding repository issue URL |
| `bug_slug` | bug workflows | bug extension slug used by `.specify/bugs/<bug_slug>/`; equals `work_slug` for bugs |
| `handoff_requirement_url` | confidential enterprise feature | sanitized internal enhancement handoff URL |
| `published_requirement_url` | legacy only | deprecated compatibility alias for `handoff_requirement_url` |
| `issue.type_label` | issue-backed work | `type/feature` or `type/bug`; enhancement-internal allows `type/feature` only |
| `issue.state_label` | issue-backed work | one of the AI Team `state/*` labels |

Do not use a mutable issue title, chat summary, local file path, or branch name
as the stable identity.

## Canonical `work_slug`

| Work type | Rule | Example |
|---|---|---|
| feature | basename of Spec Kit feature directory (`FEATURE_DIR`) | `003-user-auth` for `specs/003-user-auth/` |
| bug | same as `bug_slug` | `bug-project-alpha-123` |
| new-project / template | explicit at intake or derived after first SDD step | `customer-notification` |

For feature work after `speckit.specify`, set `work_slug` to the resolved feature
directory basename — the same name used under `specs/`.

## Bug `bug_slug`

The bug extension stores assessment, fix, and verification files under:

```text
.specify/bugs/<bug_slug>/
```

For bug workflows, `work_slug` equals `bug_slug` so AI Team work context and
bug extension artifacts stay aligned.

Recommended pattern:

```text
bug-<repo-slug>-<issue-number>
```

Example:

```yaml
work_slug: bug-project-alpha-123
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
work_slug: 003-search-export
work_type: feature
work_item:
  type: coding_feature
  coding_issue_url: https://example.com/org/project-alpha/issues/456
```

Confidential enterprise feature:

```yaml
work_slug: 004-req-2026-015
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

There is no `task_id` alias for `work_slug`.
