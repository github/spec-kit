# Issue Workflow

AI Team work is tracked with repository issues and labels. Issues are the
human-visible work ledger; Task Context Packages are only the AI reload context.

## Repository Roles

| Repository | Purpose | Allowed type labels |
|---|---|---|
| `enhancement_internal` | internal-only traceability for confidential enterprise feature demand | `type/feature` only |
| coding repository | public or project-controlled feature and bug work | `type/feature`, `type/bug` |

`enhancement_internal` is not a customer-facing repository. Enterprise
customers should not be expected to see it. Its purpose is internal traceability
for private demand, discussion, approval, wave planning, and sanitized handoff
URLs used by coding work.

Bug fixes do not belong in `enhancement_internal`. File bug issues in the
coding repository and use `ai-team-bugfix`.

## State Labels

Every AI Team issue should have exactly one state label:

| State label | Meaning | Typical next state |
|---|---|---|
| `state/draft` | intake exists, scope or acceptance is not ready | `state/accepted`, `state/rejected`, `state/closed`, `state/superseded` |
| `state/accepted` | owner or Technical Committee accepted the work for planning | `state/working`, `state/superseded` |
| `state/working` | implementation or active planning is in progress | `state/finished`, `state/superseded` |
| `state/finished` | implementation and evidence are complete, awaiting closure or release bookkeeping | `state/closed` |
| `state/rejected` | proposal was not accepted before work started | terminal |
| `state/closed` | work is complete or intentionally closed with reason | terminal |
| `state/superseded` | replaced by another issue or requirement | terminal |

Do not use issue title, branch name, or local file path as the stable identity.
Use the issue URL plus the task ID rules in [task-field-spec.md](task-field-spec.md).

## Handoff URLs

When coding work implements a feature from `enhancement_internal`, the coding
workflow receives the internal issue or handoff URL as `handoff_requirement_url`.
The URL is allowed only when the operator and coding repository visibility are
permitted to read it. Public coding repositories should use a public-safe
summary instead of private internal links.
