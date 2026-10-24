# /speckit.pr.prepare

Prepare pull request with spec-kit context.

## Trigger

Runs after `/speckit.converge` via extension hook.

## Usage

```bash
/speckit.pr.prepare <feature_name> [--repo=<owner/repo>] [--draft]
```

## Options

- `--repo` — Target repository
- `--draft` — Create as draft PR

## PR Template

```markdown
# {{feature_name}}

## Specification
- Spec: `.specify/specs/{{feature_name}}/spec.md`
- Plan: `.specify/specs/{{feature_name}}/plan.md`
- Tasks: `.specify/specs/{{feature_name}}/tasks.md`

## Convergence
- All FRs implemented: ✅
- All scenarios tested: ✅
- Constitution gates: ✅
- Checklist: ✅

## Changes
- {{file_1}}: {{description}}
- {{file_2}}: {{description}}

## Testing
- Unit: {{coverage}}%
- Integration: {{coverage}}%
- E2E: {{coverage}}%
```

## Hermes Desktop Integration

In Hermes Desktop, available as "Create PR" in TaskBoard convergence column.
