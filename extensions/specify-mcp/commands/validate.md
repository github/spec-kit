---
description: "Validate MCP compliance and cross-artifact consistency"
tools:
  - 'specify-mcp/analyze'
  - 'specify-mcp/validate_compliance'
---

# Validate & Analyze

Validate cross-artifact consistency and MCP compliance.

## Purpose

Ensure project artifacts are:
- Consistent across specification, plan, and tasks
- Compliant with MCP specifications
- Complete and well-formed
- Aligned with constitution

## Prerequisites

1. Specify MCP server running
2. Project has generated artifacts (spec, plan, tasks)

## User Input

$ARGUMENTS

## Steps

### Step 1: Cross-Artifact Consistency Analysis

Analyze relationships between artifacts:

Use MCP tool: `specify-mcp/analyze`

Parameters:
- `feature_path`: Path to feature directory
- `analysis_type`: "consistency", "coverage", or "full"
- `project_path`: Project root path

```json
{
  "feature_path": "specs/001-oauth-authentication",
  "analysis_type": "consistency",
  "project_path": "."
}
```

### Step 2: Check MCP Compliance

Validate MCP server compliance:

Use MCP tool: `specify-mcp/validate_compliance`

Parameters:
- `project_path`: Project root path
- `strict`: Enable strict validation (default: false)

```json
{
  "project_path": ".",
  "strict": false
}
```

### Step 3: Review Analysis Results

The analysis reports:

**Consistency Check**:
- Spec → Plan alignment
- Plan → Tasks coverage
- Orphaned requirements
- Missing implementations

**Coverage Report**:
- Requirements coverage percentage
- Tasks without specifications
- Unplanned features

**Compliance Report**:
- MCP protocol compliance
- Tool signature validation
- Configuration correctness

### Step 4: Address Issues

Fix identified issues:

```bash
# Review findings
# Update affected artifacts
# Re-run validation
```

## Analysis Types

| Type | Description |
|------|-------------|
| `consistency` | Check artifact alignment |
| `coverage` | Requirement coverage analysis |
| `full` | Complete analysis (both) |

## Validation Output

```
=== Cross-Artifact Analysis ===

Feature: oauth-authentication

Consistency Issues:
  ⚠️ Plan task T003 not linked to spec requirement
  ❌ Spec requirement R-005 has no implementation task

Coverage:
  Requirements: 8/10 (80%)
  Tasks: 12 planned, 0 completed

Compliance:
  ✓ MCP protocol: Valid
  ✓ Tool signatures: Valid
  ⚠️ Configuration: Missing optional fields
```

## Examples

### Quick Consistency Check

```json
{
  "feature_path": "specs/001-dark-mode",
  "analysis_type": "consistency"
}
```

### Full Analysis

```json
{
  "feature_path": "specs/002-notifications",
  "analysis_type": "full",
  "project_path": "."
}
```

### Strict Compliance Check

```json
{
  "project_path": ".",
  "strict": true
}
```

## Notes

- Run validation after generating each artifact
- Fix issues early to prevent technical debt
- Use strict mode before releases
- Coverage below 80% indicates planning gaps

---

*For more information: `specify extension info specify-mcp`*
