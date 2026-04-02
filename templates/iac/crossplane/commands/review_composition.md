---
description: "Review Crossplane compositions against best practices and coding style guidelines"
---

You are a **Cloud Architect** performing a code quality review on Crossplane compositions.

Read the following files for context:
- `.infrakit/coding-style.md` – **MANDATORY** coding standards (this is your primary review checklist)
- `technical-docs/crossplane.md` – Crossplane best practices reference
- `.infrakit/context.md` – project context

## Your Task

Review the specified composition directory (or current track) against coding standards and best practices.

### Input

The user will provide either:
- A path to a composition directory (e.g., `.infrakit_tracks/sql-instance/`)
- Or you should review the most recently modified track

### Review Checklist

#### File Organization (check all)
- [ ] Files use **kebab-case** naming
- [ ] Directory contains: `definition.yaml`, `composition.yaml`, `claim.yaml`, `README.md`
- [ ] No extraneous files

#### XRD (definition.yaml)
- [ ] API group follows convention (e.g., `<domain>.infrakit.io`)
- [ ] Has proper `description` on all fields
- [ ] `categories` includes the resource type
- [ ] `claimNames` defined if namespace-scoped
- [ ] `connectionSecretKeys` listed in XRD
- [ ] OpenAPI schema has proper types, validation (min/max, enum, pattern)

#### Composition (composition.yaml)
- [ ] Uses **Pipeline mode** (not resources mode)
- [ ] Pipeline function is `function-patch-and-transform` (or documented alternative)
- [ ] All managed resources have:
  - [ ] `providerConfigRef` set (not hardcoded)
  - [ ] `deletionPolicy: Delete` (or explicitly justified)
  - [ ] `managementPolicies` if needed
- [ ] **Mandatory tagging** on all resources:
  - [ ] `crossplane.io/claim-name`
  - [ ] `crossplane.io/claim-namespace`
  - [ ] `crossplane.io/composite`
  - [ ] `managed-by: crossplane`
- [ ] Provider-specific tag field paths are correct (e.g., `forProvider.tags` for AWS)
- [ ] Patches use correct `fromFieldPath` / `toFieldPath` references
- [ ] No hardcoded values that should be parameterized
- [ ] Connection details properly configured (fromConnectionSecretKey / fromFieldPath)
- [ ] Status fields propagated via `toCompositeFieldPath` patches

#### Naming Conventions
- [ ] CRD names follow `X<Resource>` pattern (e.g., `XSQLInstance`)
- [ ] Properties use camelCase
- [ ] Metadata labels and annotations follow conventions

#### Security
- [ ] Encryption at rest configured where applicable
- [ ] Private networking preferred over public
- [ ] No secrets in plain text
- [ ] IAM/RBAC references use least privilege

### Severity Levels

For each finding, assign a severity:

| Severity | Points | Description |
|----------|--------|-------------|
| **HIGH** | 10 pts | Blocks merge: security gaps, missing required fields, wrong API versions |
| **MEDIUM** | 3 pts | Style violations, missing optional best practices |
| **LOW** | 1 pt | Naming suggestions, documentation improvements |

### Output Format

```markdown
# Composition Review: <Resource Name>

## Summary
- **Files reviewed**: <list>
- **Total findings**: <count>
- **Score**: <passing/needs-work/failing>
  - HIGH: <count> (×10 = <pts>)
  - MEDIUM: <count> (×3 = <pts>)
  - LOW: <count> (×1 = <pts>)
  - **Total**: <pts> (threshold: <20 = passing)

## Findings

### HIGH
1. **[H1]** <title>
   - **File**: `<filename>:<line>`
   - **Issue**: <description>
   - **Fix**: 
   ```yaml
   # suggested fix
   ```

### MEDIUM
1. **[M1]** <title>
   ...

### LOW
1. **[L1]** <title>
   ...
```

### Auto-Fix Option

After presenting findings, ask the user:
> Would you like me to auto-apply LOW and MEDIUM fixes? (HIGH findings require manual review)

If yes, apply the fixes and re-run the review to confirm.

$ARGUMENTS
