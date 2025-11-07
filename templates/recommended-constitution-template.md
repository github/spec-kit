# Project Constitution: [PROJECT_NAME]

**Based on**: Reverse-engineered analysis of existing codebase
**Analysis Date**: [ANALYSIS_DATE]
**Constitution Version**: 1.0.0
**Ratified**: [DATE]
**Last Amended**: [DATE]

---

## Purpose

This constitution establishes the guiding principles, standards, and governance for [PROJECT_NAME]. These principles were extracted from analyzing the existing codebase and identifying patterns that should be codified, anti-patterns to avoid, and gaps to address.

---

## Derived Insights

**Good Patterns Observed** (to preserve):
- [Pattern 1: e.g., "Consistent error handling using custom error classes"]
- [Pattern 2: e.g., "Strong separation between API routes and business logic"]
- [Pattern 3: e.g., "Comprehensive unit tests for utility functions"]

**Anti-Patterns Found** (to eliminate):
- [Anti-pattern 1: e.g., "Direct database access in route handlers"]
- [Anti-pattern 2: e.g., "Inconsistent logging formats"]
- [Anti-pattern 3: e.g., "Missing input validation in public endpoints"]

**Critical Gaps** (to address):
- [Gap 1: e.g., "No formal error handling strategy"]
- [Gap 2: e.g., "Inconsistent authentication patterns"]
- [Gap 3: e.g., "Missing integration tests"]

---

## Core Principles

### Principle 1: [CODE_QUALITY_PRINCIPLE_NAME]

**Statement**: [Clear, actionable principle derived from analysis]

**Example**: "MUST maintain single responsibility - each function/class performs one well-defined task"

**Rationale**:
[Why this principle matters based on findings]

**Example**: "Analysis revealed 37 functions exceeding 100 lines with multiple responsibilities, making maintenance difficult. This principle addresses that technical debt."

**Implementation**:
- [How to apply: e.g., "Functions should not exceed 50 lines"]
- [How to enforce: e.g., "Linter rule: max-lines-per-function: 50"]
- [How to measure: e.g., "Code review checklist includes SRP check"]

**Examples from Codebase**:

**✅ Good example** (preserve this pattern):
```javascript
// File: src/utils/validation.js:45
function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}
```

**❌ Bad example** (refactor to match principle):
```javascript
// File: src/controllers/userController.js:123
function processUser(data) {
  // Validates, transforms, saves to DB, sends email, logs - 150 lines
  // Violates SRP - should be split into separate functions
}
```

---

### Principle 2: [TESTING_PRINCIPLE_NAME]

**Statement**: "MUST write tests before implementation (Test-Driven Development)"

**Rationale**:
Current test coverage is [X]%, with critical paths untested. TDD ensures new code is testable and tested from the start.

**Implementation**:
- Write failing test first
- Implement minimum code to pass
- Refactor with confidence
- Target: 80%+ coverage for new code

**Coverage Requirements**:
- Unit tests: All business logic functions
- Integration tests: All API endpoints
- E2E tests: Critical user journeys

**Tools**:
- Unit: [Jest, pytest, xUnit, etc.]
- Integration: [Supertest, TestContainers, etc.]
- E2E: [Playwright, Cypress, Selenium]

---

### Principle 3: [SECURITY_PRINCIPLE_NAME]

**Statement**: "MUST validate all inputs and sanitize all outputs"

**Rationale**:
Analysis found [X] endpoints accepting user input without validation, creating XSS and injection risks.

**Implementation**:
- Input validation: Use [library/schema] for all public endpoints
- Output encoding: Escape HTML, sanitize SQL, parameterize queries
- Authentication: JWT with expiration, secure session storage
- Authorization: Role-based access control (RBAC)
- Secrets: Never commit secrets, use environment variables

**Required Security Checks**:
- [ ] Input validation on all public endpoints
- [ ] SQL parameterization (no string concatenation)
- [ ] XSS prevention (output encoding)
- [ ] CSRF tokens on state-changing operations
- [ ] Rate limiting on auth endpoints
- [ ] Security headers (CSP, X-Frame-Options, etc.)

**Security Review Trigger**:
Any code touching:
- Authentication/authorization
- Payment processing
- Personal data (PII)
- File uploads
- Admin functionality

---

### Principle 4: [ERROR_HANDLING_PRINCIPLE_NAME]

**Statement**: "MUST use structured error handling with consistent error types and logging"

**Rationale**:
Current error handling is inconsistent (mix of throw/callback/promise rejection), making debugging difficult.

**Implementation**:

**Error Classification**:
```javascript
class ValidationError extends Error { }     // 400
class UnauthorizedError extends Error { }   // 401
class ForbiddenError extends Error { }      // 403
class NotFoundError extends Error { }       // 404
class ConflictError extends Error { }       // 409
class InternalError extends Error { }       // 500
```

**Logging Standard**:
```javascript
logger.error({
  message: error.message,
  stack: error.stack,
  context: { userId, requestId },
  timestamp: new Date().toISOString()
});
```

**Never**:
- ❌ Swallow errors silently
- ❌ Log sensitive data (passwords, tokens, PII)
- ❌ Expose internal errors to users

**Always**:
- ✅ Catch at appropriate layer
- ✅ Log with context
- ✅ Return user-friendly messages

---

### Principle 5: [ARCHITECTURE_PRINCIPLE_NAME]

**Statement**: "MUST follow layered architecture: Routes → Controllers → Services → Data Access"

**Rationale**:
Current codebase mixes concerns (database queries in route handlers), making testing and refactoring hard.

**Layer Responsibilities**:

**Routes** (src/routes/):
- Define endpoints
- Parse request
- Call controller
- Format response
- NO business logic

**Controllers** (src/controllers/):
- Validate input
- Call services
- Handle errors
- Return results
- NO direct database access

**Services** (src/services/):
- Business logic
- Orchestrate data access
- Transaction management
- NO HTTP concerns

**Data Access** (src/repositories/):
- Database queries
- ORM/query builder usage
- Data mapping
- NO business logic

**Enforcement**:
- Linter rule: No SQL in route/controller files
- Code review: Check layer violations
- Architecture tests: Verify dependencies

---

### Principle 6: [DEPENDENCY_MANAGEMENT_PRINCIPLE_NAME]

**Statement**: "MUST keep dependencies current, secure, and minimal"

**Rationale**:
Analysis found [X] vulnerable dependencies and [Y] packages 2+ major versions behind.

**Requirements**:
- Security vulnerabilities: CRITICAL/HIGH must be fixed within 1 week
- LTS versions: Upgrade within 3 months of release
- Deprecated packages: Replace within 6 months of deprecation
- Unused dependencies: Remove immediately

**Process**:
```bash
# Monthly dependency review
npm outdated
npm audit

# Update patch/minor versions
npm update

# Plan major version upgrades
# (follow upgrade-plan-template.md)
```

**Adding New Dependencies**:
- [ ] Justify need (can we use existing dependency?)
- [ ] Check maintenance status (last update < 1 year)
- [ ] Review bundle size impact
- [ ] Verify license compatibility
- [ ] Security scan (npm audit, Snyk)

**Never**:
- Add dependencies for trivial utility functions
- Use packages with critical vulnerabilities
- Use packages with incompatible licenses
- Exceed bundle budget ([X] KB)

---

### Principle 7: [DOCUMENTATION_PRINCIPLE_NAME]

**Statement**: "MUST document intent, not implementation"

**Rationale**:
Current documentation is sparse and often outdated. Good documentation explains WHY, not WHAT.

**Code Comments**:
```javascript
// ❌ Bad - describes WHAT (obvious from code)
// Loop through users and increment count
users.forEach(u => count++);

// ✅ Good - explains WHY (non-obvious intent)
// Exclude soft-deleted users from active count per GDPR requirements
const activeUsers = users.filter(u => !u.deletedAt);
```

**Function Documentation**:
```javascript
/**
 * Calculate shipping cost based on distance and package weight.
 *
 * Uses tiered pricing: <100mi flat rate, >100mi distance-based.
 * Premium members get 20% discount (business requirement BIZ-123).
 *
 * @param {number} distanceMiles - Distance in miles
 * @param {number} weightLbs - Package weight in pounds
 * @param {boolean} isPremium - Is customer premium member
 * @returns {number} Shipping cost in cents
 * @throws {ValidationError} If distance or weight invalid
 */
function calculateShipping(distanceMiles, weightLbs, isPremium) {
  // Implementation
}
```

**Required Documentation**:
- README: Setup, usage, architecture overview
- API docs: All public endpoints (OpenAPI/Swagger)
- Architecture Decision Records (ADR): Major technical decisions
- Runbooks: Deployment, rollback, incident response

---

### Principle 8: [PERFORMANCE_PRINCIPLE_NAME]

**Statement**: "MUST meet defined performance budgets"

**Rationale**:
Performance impacts user experience and operational costs. Current baseline: [metrics].

**Performance Budgets**:
- API response time: p95 < 500ms, p99 < 1000ms
- Page load: First Contentful Paint < 1.5s
- Time to Interactive: < 3.5s
- Bundle size: < [X] KB (gzipped)
- Database queries: < 10 per request

**Monitoring**:
- APM tool: [DataDog, New Relic, etc.]
- Real User Monitoring (RUM)
- Synthetic monitoring

**Optimization Requirements**:
- Database: Indexed queries, connection pooling
- Caching: Redis for frequently accessed data (TTL: [X] minutes)
- Frontend: Code splitting, lazy loading, image optimization
- API: Pagination (max 100 items), rate limiting

**Review Triggers**:
- Any API endpoint slower than budget
- Bundle size increase > 10%
- Database query count spike

---

### Principle 9: [CODE_REVIEW_PRINCIPLE_NAME]

**Statement**: "MUST conduct thorough code reviews before merging"

**Rationale**:
Code reviews catch bugs early, share knowledge, and enforce standards.

**Code Review Checklist**:

**Functionality**:
- [ ] Code does what it's supposed to
- [ ] Edge cases handled
- [ ] Error scenarios covered

**Quality**:
- [ ] Follows coding standards
- [ ] No code smells
- [ ] Readable and maintainable
- [ ] Appropriate abstractions

**Testing**:
- [ ] Tests included
- [ ] Tests actually test the functionality
- [ ] Coverage meets requirement

**Security**:
- [ ] Input validation present
- [ ] No secrets in code
- [ ] Authorization checks present

**Performance**:
- [ ] No obvious performance issues
- [ ] Database queries optimized
- [ ] Caching used appropriately

**Review Requirements**:
- All PRs require 1+ approval
- Critical changes (auth, payment, data) require 2+ approvals
- Reviewers must run code locally
- Reviewers must check tests pass

**Author Responsibilities**:
- Keep PRs small (< 400 lines)
- Write descriptive PR description
- Link to issue/ticket
- Self-review before requesting review

---

### Principle 10: [DEPLOYMENT_PRINCIPLE_NAME]

**Statement**: "MUST use automated, repeatable deployment process"

**Rationale**:
Manual deployments are error-prone. Automation ensures consistency.

**CI/CD Pipeline**:

**On Pull Request**:
- [ ] Run linter
- [ ] Run tests
- [ ] Run security scan
- [ ] Check test coverage
- [ ] Build successfully
- [ ] Preview deployment (staging)

**On Merge to Main**:
- [ ] Run full test suite
- [ ] Build production artifacts
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Deploy to production (if staging passes)
- [ ] Run post-deployment checks

**Deployment Strategy**:
- Blue-green deployment (zero downtime)
- Gradual rollout (10% → 50% → 100%)
- Automated rollback on error spike

**Deployment Checklist**:
- [ ] Database migrations tested
- [ ] Environment variables configured
- [ ] Secrets rotated (if needed)
- [ ] Monitoring alerts active
- [ ] Rollback plan ready

---

## Governance

### Amendment Process

**Proposing Changes**:
1. Open issue/RFC describing proposed change
2. Discuss with team (minimum 1 week)
3. Vote (requires 2/3 majority)
4. Update constitution
5. Update version number (semantic versioning)

**Version Bumping**:
- MAJOR: Breaking changes (remove/redefine principle)
- MINOR: New principle added
- PATCH: Clarifications, typos, examples

### Compliance Review

**Frequency**: Quarterly

**Review Process**:
1. Audit codebase against principles
2. Identify violations
3. Create tickets to address violations
4. Track remediation progress

**Tooling**:
- Automated: Linters, security scanners
- Manual: Code review checklist, architecture review

### Enforcement

**Violations**:
- **Blocker**: Critical security/data issues (MUST fix before merge)
- **Required**: Principle violations (MUST fix before merge)
- **Recommended**: Best practices (SHOULD fix, can defer with justification)

**Exceptions**:
- Must be explicitly documented in PR
- Require additional approval
- Tracked in technical debt backlog

---

## Implementation Roadmap

**Immediate** (Week 1-2):
- [ ] Set up linters with principle rules
- [ ] Create code review checklist
- [ ] Add security scanning to CI

**Short-term** (Month 1-3):
- [ ] Refactor highest-impact violations
- [ ] Add missing test coverage
- [ ] Document architecture

**Long-term** (Month 3-12):
- [ ] Address remaining technical debt
- [ ] Implement full CI/CD pipeline
- [ ] Achieve 80%+ test coverage

---

## References

### Internal
- Architecture Decision Records: [LINK]
- Coding Standards: [LINK]
- Security Policy: [LINK]

### External
- [Language] Style Guide: [LINK]
- [Framework] Best Practices: [LINK]
- OWASP Top 10: https://owasp.org/www-project-top-ten/

---

## Appendix: Principle Mapping to Codebase Issues

| Principle | Codebase Issues Addressed | Priority |
|-----------|---------------------------|----------|
| Code Quality | [X] god functions, [Y] deep nesting | HIGH |
| Testing | [X]% coverage gap | CRITICAL |
| Security | [X] validation gaps, [Y] vulnerabilities | CRITICAL |
| Error Handling | [X] inconsistent patterns | MEDIUM |
| Architecture | [X] layer violations | HIGH |
| Dependencies | [X] vulnerable packages | CRITICAL |
| Documentation | [X] missing docs | MEDIUM |
| Performance | [X] slow endpoints | MEDIUM |
| Code Review | Currently ad-hoc | HIGH |
| Deployment | Manual deployments | MEDIUM |

---

**Status**: DRAFT | RATIFIED | AMENDED
**Next Review**: [DATE]
**Owner**: [TEAM/PERSON]
