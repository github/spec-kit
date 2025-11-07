# Universal Platform Constitution

**Purpose:** Define platform-wide principles, standards, and best practices for all projects regardless of architecture.

**Scope:** Applies to all projects: microservices, monoliths, libraries, frontends, CLIs, mobile apps, etc.

---

## Core Principles

### 1. Consistency
- Maintain consistent patterns across all projects
- Use standard naming conventions
- Follow established architectural patterns
- Document deviations with clear rationale

### 2. Simplicity
- Prefer simple, maintainable solutions
- Avoid over-engineering
- Keep dependencies minimal
- Write self-documenting code

### 3. Documentation
- All features must have specifications
- All public APIs must be documented
- Changes must be tracked in version control
- Architecture decisions must be recorded

### 4. Testing
- All code must have appropriate test coverage (minimum 80%)
- Tests must be fast and reliable
- Integration tests for critical paths
- E2E tests for user-facing features

### 5. Security
- Security is a top priority in all decisions
- Follow OWASP guidelines
- Regular security audits
- Secrets must never be committed
- Input validation is mandatory

---

## Technical Standards

### Code Quality

**General:**
- Follow language-specific style guides (PEP 8, Go fmt, ESLint, etc.)
- Use automated linters and formatters
- Code reviews are mandatory
- No commented-out code in production

**Naming:**
- Use descriptive, meaningful names
- Avoid abbreviations unless well-known
- Be consistent across the codebase

**Comments:**
- Explain "why", not "what"
- Update comments when code changes
- Use docstrings for public APIs

### Architecture

**Design Principles:**
- SOLID principles
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple, Stupid)
- YAGNI (You Aren't Gonna Need It)

**Patterns:**
- Prefer composition over inheritance
- Keep components loosely coupled
- Design for testability
- Separate concerns (business logic, data access, UI)

**Dependencies:**
- Minimize external dependencies
- Vet dependencies for security and maintenance
- Lock dependency versions
- Regular updates for security patches

### Data Management

**Databases:**
- Use migrations for schema changes
- Never modify production data manually
- Implement proper backups
- Use transactions where appropriate

**APIs:**
- RESTful design for HTTP APIs
- Versioning is mandatory (v1, v2, etc.)
- Consistent error responses
- Pagination for list endpoints
- Rate limiting for public APIs

**Caching:**
- Cache at appropriate layers
- Document cache invalidation strategy
- Monitor cache hit rates
- Avoid premature optimization

### Version Control

**Git:**
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Write meaningful commit messages
- Use feature branches
- Squash commits before merging
- Tag releases

**Commit Messages:**
```
type(scope): subject

body (optional)

footer (optional)
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Examples:**
- `feat(api): add user authentication endpoint`
- `fix(auth): resolve token expiration bug`
- `docs(readme): update installation instructions`

### Error Handling

**General:**
- Fail fast and loud in development
- Graceful degradation in production
- Log errors with context
- Monitor error rates

**Logging:**
- Use structured logging (JSON)
- Include request IDs for tracing
- Log levels: DEBUG, INFO, WARN, ERROR, FATAL
- Never log sensitive data (passwords, tokens, PII)

**Monitoring:**
- Implement health checks
- Track key metrics (latency, throughput, errors)
- Set up alerting for critical issues
- Regular incident reviews

### Performance

**General:**
- Measure before optimizing
- Profile to find bottlenecks
- Document performance requirements
- Load test critical paths

**Targets:**
- API response time: < 200ms (p95)
- Page load time: < 2 seconds
- Database query time: < 50ms (p95)
- Cache hit rate: > 95%

---

## Development Workflow

### Feature Development

1. **Specification** (`/speckit.specify`)
   - Define requirements
   - Document API contracts
   - Identify edge cases
   - Review with team

2. **Planning** (`/speckit.plan`)
   - Break down into tasks
   - Identify dependencies
   - Estimate effort
   - Get approval

3. **Implementation** (`/speckit.implement`)
   - Write tests first (TDD)
   - Implement incrementally
   - Commit frequently
   - Update documentation

4. **Review**
   - Code review by peers
   - Address feedback
   - Run all tests
   - Update changelog

5. **Deployment**
   - Merge to main branch
   - Deploy to staging first
   - Run smoke tests
   - Deploy to production
   - Monitor for issues

### Code Review

**Reviewer Checklist:**
- [ ] Code follows style guide
- [ ] Tests are comprehensive
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance is acceptable
- [ ] Error handling is proper
- [ ] Changes align with spec

**Approval Required:**
- Minimum 1 approval for features
- Minimum 2 approvals for architectural changes
- Security team approval for auth/security changes

### Testing Strategy

**Test Pyramid:**
```
        /\
       /E2E\        (Few, slow, expensive)
      /------\
     /  API  \      (Some, medium speed)
    /--------\
   /   Unit   \     (Many, fast, cheap)
  /------------\
```

**Coverage Requirements:**
- Unit tests: 80% minimum
- Integration tests: Critical paths
- E2E tests: User journeys
- Performance tests: Load scenarios

---

## Operational Standards

### Deployment

**Environment Strategy:**
- Development: Local + CI
- Staging: Production-like
- Production: Multiple regions (if applicable)

**Deployment Process:**
- Automated via CI/CD
- Gradual rollout (canary or blue-green)
- Automatic rollback on errors
- Post-deployment verification

### Monitoring

**Metrics to Track:**
- Application metrics (custom business metrics)
- System metrics (CPU, memory, disk, network)
- Request metrics (throughput, latency, errors)
- User metrics (active users, sessions, conversions)

**Alerting:**
- Alert on symptoms, not causes
- Include runbooks in alerts
- Escalate if not acknowledged
- Post-mortems for incidents

### Incident Response

**Severity Levels:**
- **SEV-1 (Critical):** System down, data loss, security breach
- **SEV-2 (High):** Major feature broken, significant performance degradation
- **SEV-3 (Medium):** Minor feature broken, limited impact
- **SEV-4 (Low):** Cosmetic issues, low-priority bugs

**Response Process:**
1. Acknowledge incident
2. Assess severity
3. Mitigate (rollback if necessary)
4. Communicate status
5. Root cause analysis
6. Post-mortem document
7. Implement preventive measures

---

## Security Standards

### Authentication & Authorization

- Use industry-standard protocols (OAuth 2.0, OpenID Connect)
- Multi-factor authentication for sensitive operations
- Principle of least privilege
- Regular access reviews

### Data Protection

- Encrypt data in transit (TLS 1.3+)
- Encrypt sensitive data at rest
- Proper key management
- Data retention policies
- GDPR/privacy compliance

### Secure Coding

- Input validation and sanitization
- Output encoding
- Parameterized queries (prevent SQL injection)
- CSRF protection
- Content Security Policy (CSP)
- Dependency scanning for vulnerabilities

---

## Compliance & Documentation

### Required Documentation

**Per Feature:**
- `spec.md` - Feature specification
- `plan.md` - Implementation plan
- `tasks.md` - Task breakdown
- `ai-doc.md` - AI-optimized documentation

**Per Project:**
- README.md - Overview and quick start
- ARCHITECTURE.md - System design
- API.md - API documentation (if applicable)
- CHANGELOG.md - Version history

**Platform-Wide:**
- This constitution
- Runbooks for operations
- Incident response procedures
- Disaster recovery plans

### Change Management

**Types of Changes:**
- **Breaking:** Requires major version bump, migration guide
- **Feature:** New functionality, minor version bump
- **Fix:** Bug fixes, patch version bump
- **Docs:** Documentation only, no version change

**Change Process:**
1. Propose change (RFC if architectural)
2. Review and approve
3. Implement with tests
4. Document in CHANGELOG
5. Deploy with communication

---

## Exceptions & Waivers

### When to Deviate

Deviations from this constitution are allowed when:
- Technical constraints require it
- Business urgency demands it
- Alternative approach is demonstrably better

### Documentation Required

For any deviation, document:
1. **What:** Which standard is being violated
2. **Why:** Justification for deviation
3. **How:** Alternative approach being used
4. **When:** Expected duration (temporary or permanent)
5. **Review:** Who approved the deviation

---

## Continuous Improvement

This constitution is a living document:
- Review quarterly
- Update based on lessons learned
- Incorporate new best practices
- Remove obsolete standards

**Amendment Process:**
1. Propose change with rationale
2. Team discussion
3. Approval by tech leads
4. Update document
5. Communicate to team

---

## Enforcement

**Automated:**
- Linters enforce style
- CI/CD enforces tests
- Code review enforces quality

**Manual:**
- Peer reviews
- Architecture reviews
- Periodic audits

**Consequences:**
- First violation: Warning + education
- Repeated violations: Escalation to management
- Serious violations: Immediate intervention

---

## Resources

**Tools:**
- Linters: ESLint, Pylint, golangci-lint, etc.
- Formatters: Prettier, Black, gofmt, etc.
- Testing: Jest, pytest, Go test, etc.
- CI/CD: GitHub Actions, GitLab CI, Jenkins, etc.

**References:**
- OWASP Top 10
- SOLID principles
- 12-Factor App methodology
- Google SRE Book
- Semantic Versioning spec

---

**Status:** Universal Constitution v1.0

**Last Updated:** 2025-11-07

**Next Review:** 2026-02-07 (Quarterly)
