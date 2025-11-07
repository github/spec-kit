---
description: Validate API contracts and service interfaces
---

# Validate API Contracts

Validate API contracts between services to ensure compatibility and prevent breaking changes.

## When to Use

- Before deploying service changes
- After API modifications
- During integration testing
- Before major releases

## What This Validates

### API Compatibility
- Request format changes
- Response format changes
- Endpoint modifications
- Breaking vs. non-breaking changes

### Contract Compliance
- Matches OpenAPI/Swagger specs
- Follows versioning strategy
- Maintains backward compatibility
- Honors deprecation timeline

### Integration Points
- Service-to-service contracts
- Database schemas
- Message queue formats
- Event payloads

## Validation Checks

### Request Validation
- Required fields present
- Data types correct
- Formats valid
- Constraints satisfied

### Response Validation
- All documented fields present
- Types match specification
- Error formats consistent
- Status codes correct

### Versioning
- Version headers present
- Deprecated endpoints marked
- Migration path documented
- Sunset dates announced

## Output

Generates:
```
.validation/contract-results.md
```

Shows:
- ✅ Passing contracts
- ❌ Failing contracts
- ⚠️  Warnings (potential issues)
- 📝 Recommendations

## Common Issues Found

- Missing required fields
- Type mismatches
- Undocumented endpoints
- Breaking changes
- Version inconsistencies
- Missing error handling

## Before Deployment

1. Run contract validation
2. Review any failures
3. Fix contract violations
4. Update API documentation
5. Communicate changes to consumers

## Best Practices

- Validate before every deployment
- Maintain API specifications
- Version APIs properly
- Communicate breaking changes
- Provide migration guides
- Test with actual consumers

## Contract Testing

Consider implementing:
- Consumer-driven contracts
- Schema validation tests
- Integration test suites
- Backward compatibility tests
