# Contract Validation Command

You are validating microservice contracts for consistency and completeness.

## Context Files to Load

Load these files to understand the contracts:
1. All `contracts/**/*.json` (OpenAPI specs)
2. All `contracts/**/*.yaml` (OpenAPI specs)
3. All `contracts/events/**/*.json` (Event schemas)
4. All `contracts/events/**/*.avsc` (Avro schemas)
5. `specs/*/service-spec.md` or `specs/*/spec.md` (Service specifications)

## Validation Rules

### API Contract Validation

For each OpenAPI specification:

1. **Completeness Checks**
   - [ ] All endpoints have descriptions
   - [ ] All request bodies have schemas
   - [ ] All responses (200, 4xx, 5xx) are documented
   - [ ] Authentication/security schemes defined
   - [ ] Example requests/responses provided

2. **Consistency Checks**
   - [ ] Consistent naming conventions (kebab-case, camelCase, snake_case)
   - [ ] Consistent error response format across services
   - [ ] Consistent pagination strategy
   - [ ] Consistent versioning approach
   - [ ] Consistent authentication headers

3. **Breaking Change Detection**
   - [ ] No removed endpoints (unless documented as deprecated)
   - [ ] No removed required fields
   - [ ] No changed field types
   - [ ] No changed error codes for same scenarios
   - [ ] Version number incremented if breaking changes

4. **Best Practices**
   - [ ] Idempotency keys for non-idempotent operations
   - [ ] Rate limiting documented
   - [ ] Timeout recommendations provided
   - [ ] Retry policies documented
   - [ ] Health check endpoint exists

### Event Contract Validation

For each event schema:

1. **Schema Completeness**
   - [ ] Event type/name defined
   - [ ] Schema version specified
   - [ ] All fields have types and descriptions
   - [ ] Required vs optional fields marked
   - [ ] Example payloads provided

2. **Event Metadata**
   - [ ] eventId (correlation/tracing)
   - [ ] timestamp (when event occurred)
   - [ ] eventType (for routing/filtering)
   - [ ] version (schema version)
   - [ ] Optional: causationId, correlationId

3. **Schema Evolution**
   - [ ] Backward compatible changes only (new optional fields)
   - [ ] No removed fields
   - [ ] No type changes
   - [ ] Schema registry compatible (Avro/Protobuf/JSON Schema)

4. **Event Documentation**
   - [ ] When event is published (trigger condition)
   - [ ] Who consumes this event
   - [ ] Expected consumer actions
   - [ ] Idempotency considerations
   - [ ] Ordering guarantees

### Cross-Service Consistency

1. **Service Dependencies**
   - [ ] All upstream services exist
   - [ ] All referenced endpoints exist in upstream specs
   - [ ] All consumed events have published schemas
   - [ ] No circular dependencies (unless documented)

2. **Data Ownership**
   - [ ] Each entity has exactly one source of truth
   - [ ] No conflicting entity definitions
   - [ ] Data replication explicitly documented

3. **Naming Consistency**
   - [ ] Service names match across all specs
   - [ ] Entity names consistent across services
   - [ ] Event naming follows convention: `domain.entity.action`

## Validation Output Format

```markdown
## Contract Validation Report

**Generated:** [timestamp]
**Scope:** [All services / Specific service]

### Summary
- ✅ Passed: [N] checks
- ⚠️  Warnings: [N] issues
- ❌ Failed: [N] critical issues

### Critical Issues (Must Fix)

#### [Service Name] - [Contract File]
**Issue:** [Description]
**Location:** [File path and line number]
**Impact:** [Breaking change / Missing required field / etc.]
**Recommendation:** [How to fix]

### Warnings (Should Fix)

#### [Service Name] - [Contract File]
**Issue:** [Description]
**Location:** [File path]
**Impact:** [Inconsistency / Missing documentation / etc.]
**Recommendation:** [How to fix]

### Breaking Changes Detected

#### [Service Name] - [API/Event]
**Change Type:** [Removed field / Changed type / etc.]
**Before:** [Old definition]
**After:** [New definition]
**Affected Consumers:** [List of services]
**Action Required:** [Version bump / Migration guide / etc.]

### Cross-Service Dependencies

#### Service: [service-name]
**Upstream Dependencies:**
- [service-name-1]: [status: ✅ valid / ❌ broken]
- [service-name-2]: [status: ✅ valid / ❌ broken]

**Downstream Dependents:**
- [service-name-3]: [status: ✅ valid / ⚠️  outdated]

### Contract Coverage

| Service | API Spec | Event Schemas | Test Coverage |
|---------|----------|---------------|---------------|
| auth-service | ✅ Complete | ✅ 5/5 events | ⚠️  60% |
| user-service | ❌ Missing | ✅ 3/3 events | ✅ 85% |
| order-service | ✅ Complete | ⚠️  1/3 missing | ✅ 90% |

## Next Steps

1. Fix all critical issues before deployment
2. Address warnings to improve maintainability
3. Update consuming services if breaking changes detected
4. Add missing contract tests
5. Update documentation for any new endpoints/events
```

## Special Validation Scenarios

### Scenario: New Service Being Added
- Validate all referenced services exist
- Check for service name conflicts
- Verify bounded context doesn't overlap with existing services

### Scenario: API Version Upgrade (v1 → v2)
- Validate both versions coexist
- Check sunset timeline for old version documented
- Ensure backward compatibility layer exists

### Scenario: Event Schema Migration
- Validate consumers can handle both old and new schema
- Check schema registry compatibility
- Verify rollback plan exists

## Integration with CI/CD

This validation should run:
1. **Pre-commit:** Validate local changes
2. **PR Checks:** Validate against main branch contracts
3. **Pre-deployment:** Final validation before release

Exit codes:
- 0: All validations passed
- 1: Warnings found (allow deployment with approval)
- 2: Critical issues found (block deployment)

## Example Usage in Workflow

```bash
# Validate all contracts
/speckit.validate-contracts

# Validate specific service
/speckit.validate-contracts --service=auth-service

# Check for breaking changes only
/speckit.validate-contracts --breaking-changes-only

# Validate against specific branch (for PRs)
/speckit.validate-contracts --compare-with=main
```

## Instructions for AI Agent

When this command is invoked:

1. **Discover all contract files** in the repository
2. **Load and parse** each contract (handle JSON, YAML, Avro)
3. **Run all validation checks** as documented above
4. **Generate a detailed report** in the format specified
5. **Provide actionable recommendations** for each issue
6. **Exit with appropriate code** based on severity

If asked to validate specific aspects:
- `--api-only`: Only validate REST API contracts
- `--events-only`: Only validate event schemas
- `--service=<name>`: Only validate contracts for one service
- `--breaking-changes-only`: Focus on breaking changes

Always explain WHY something is an issue and HOW to fix it, not just WHAT is wrong.
