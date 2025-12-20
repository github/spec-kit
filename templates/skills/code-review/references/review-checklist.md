# Comprehensive Code Review Checklist

## 1. Architecture & Design

### Structure
- [ ] Code follows established patterns in the codebase
- [ ] New abstractions are justified and well-designed
- [ ] Dependencies flow in the correct direction
- [ ] No circular dependencies introduced

### SOLID Principles
- [ ] **S**ingle Responsibility: Each class/function has one job
- [ ] **O**pen/Closed: Extensible without modification
- [ ] **L**iskov Substitution: Subtypes are substitutable
- [ ] **I**nterface Segregation: No forced unused dependencies
- [ ] **D**ependency Inversion: Depend on abstractions

### Separation of Concerns
- [ ] Business logic separate from infrastructure
- [ ] UI logic separate from data access
- [ ] Configuration externalized appropriately

## 2. Code Quality

### Readability
- [ ] Code is self-documenting
- [ ] Variable/function names are descriptive
- [ ] Complex logic has explanatory comments
- [ ] No "clever" code that's hard to understand

### Complexity
- [ ] Cyclomatic complexity is reasonable (< 10)
- [ ] No deeply nested conditionals (< 3 levels)
- [ ] Functions are short (< 30 lines ideal)
- [ ] Classes are focused (< 300 lines ideal)

### DRY (Don't Repeat Yourself)
- [ ] No copy-pasted code blocks
- [ ] Common patterns extracted to utilities
- [ ] Magic numbers replaced with named constants

### Error Handling
- [ ] Errors are caught at appropriate levels
- [ ] Error messages are informative
- [ ] Failures are logged with context
- [ ] Recovery strategies are in place

## 3. Security Review

### Input Validation
- [ ] All user input is validated
- [ ] Input length limits enforced
- [ ] Type checking on dynamic data
- [ ] Whitelist over blacklist approach

### Authentication & Authorization
- [ ] Auth checks on all protected endpoints
- [ ] Principle of least privilege applied
- [ ] Session handling is secure
- [ ] Tokens have appropriate expiry

### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] Secure transmission (HTTPS)
- [ ] PII handled according to policy
- [ ] No secrets in logs or error messages

### Common Vulnerabilities
- [ ] No SQL injection vectors
- [ ] No XSS vulnerabilities
- [ ] No CSRF vulnerabilities
- [ ] No path traversal issues
- [ ] No command injection

## 4. Performance

### Database
- [ ] Queries are optimized
- [ ] Indexes exist for query patterns
- [ ] No N+1 query patterns
- [ ] Batch operations where appropriate

### Memory
- [ ] No memory leaks
- [ ] Large objects handled efficiently
- [ ] Streams used for large data
- [ ] Caches have eviction policies

### Concurrency
- [ ] Thread-safe where needed
- [ ] No race conditions
- [ ] Deadlocks prevented
- [ ] Async/await used correctly

## 5. Testing

### Coverage
- [ ] New code has tests
- [ ] Critical paths are tested
- [ ] Edge cases are covered
- [ ] Error paths are tested

### Quality
- [ ] Tests are readable
- [ ] Tests are independent
- [ ] Tests are deterministic
- [ ] Tests follow AAA pattern

### Types
- [ ] Unit tests for logic
- [ ] Integration tests for workflows
- [ ] Contract tests for APIs
- [ ] E2E tests for critical journeys

## 6. Documentation

### Code Comments
- [ ] Complex algorithms explained
- [ ] "Why" documented, not "what"
- [ ] TODO/FIXME items are tracked
- [ ] Outdated comments removed

### API Documentation
- [ ] Public APIs documented
- [ ] Parameters described
- [ ] Return values specified
- [ ] Examples provided

### README Updates
- [ ] Setup instructions current
- [ ] New features documented
- [ ] Breaking changes noted

## 7. Operational Readiness

### Observability
- [ ] Appropriate logging added
- [ ] Metrics for key operations
- [ ] Tracing for distributed calls
- [ ] Alerts configured

### Deployment
- [ ] Feature flags if needed
- [ ] Rollback plan exists
- [ ] Database migrations reversible
- [ ] No breaking changes without versioning

### Configuration
- [ ] Environment-specific config externalized
- [ ] Secrets managed properly
- [ ] Defaults are sensible
- [ ] Validation on startup
