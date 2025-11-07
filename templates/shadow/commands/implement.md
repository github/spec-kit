---
description: Execute implementation with guidance
---

# Execute Implementation

Implement the feature following the specification, plan, and tasks.

## Process

1. **Review artifacts** - Read spec, plan, and tasks
2. **Start with tests** - Write tests first (TDD)
3. **Implement incrementally** - Complete one task at a time
4. **Validate continuously** - Run tests after each change
5. **Document as you go** - Update docs with code changes

## Implementation Guidelines

### Code Quality
- Follow project coding standards
- Write clean, readable code
- Add comments for complex logic
- Handle errors appropriately

### Testing
- Write unit tests for business logic
- Add integration tests for APIs
- Include edge cases
- Maintain test coverage

### Documentation
- Update API documentation
- Add inline code comments
- Update README if needed
- Document breaking changes

## Validation

After implementation:
```bash
# Run tests
npm test  # or equivalent

# Check code quality
npm run lint
npm run format

# Validate changes
git diff
```

## Best Practices

- Commit frequently with clear messages
- Keep pull requests focused
- Request code review early
- Address feedback promptly
