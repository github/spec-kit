# Microservices Constitution

This document establishes the core principles, patterns, and standards for our microservices architecture. All services MUST adhere to these principles.

---

## Core Principles

### 1. Service Boundaries

**Bounded Contexts**
- Each service owns a well-defined bounded context
- Services align with business capabilities, not technical layers
- No shared databases between services
- Data duplication is acceptable to maintain service autonomy

**Single Responsibility**
- Each service does ONE thing well
- If a service description needs "and", it's probably too large
- Services can be understood by a single team

**Independence**
- Services must be deployable independently
- Changes in one service don't require changes in others (except contract evolution)
- Services can be developed, tested, and scaled independently

### 2. Communication Patterns

**Synchronous (REST APIs)**
- Use for: Request/response, immediate consistency needed
- Must have: OpenAPI specification, versioning, error handling
- Implement: Circuit breakers, timeouts, retries with backoff
- Maximum chain depth: 3 services (A → B → C, no deeper)

**Asynchronous (Events)**
- Use for: Fire-and-forget, eventual consistency acceptable
- Must have: Event schema definition, idempotency handling
- Implement: Dead letter queues, retry policies
- Event naming: `domain.entity.action` (e.g., `order.created`, `user.updated`)

**API Gateway Pattern**
- All external traffic goes through API gateway
- Gateway handles: Authentication, rate limiting, routing
- Gateway does NOT: Business logic, data transformation beyond simple mapping

### 3. Data Management

**Database per Service**
- Each service owns its database
- No direct database access between services
- Schema migrations managed by owning service

**Data Ownership**
- Each entity has exactly ONE source of truth
- Other services can cache/replicate (read-only)
- Updates to entities go through owning service's API

**Data Consistency**
- Prefer eventual consistency
- Use Saga pattern for distributed transactions
- Compensating transactions for rollbacks
- Idempotent operations to handle retries

**Data Replication**
- Replicate via events, not database replication
- Document all replicated data and sync method
- TTL-based cache invalidation or event-driven

---

## API Standards

### REST API Guidelines

**Naming Conventions**
```
Resources: Plural nouns (/users, /orders, /products)
Actions: HTTP verbs (GET, POST, PUT, DELETE, PATCH)
Sub-resources: /users/{id}/orders
Actions not CRUD: POST to verb endpoint: /orders/{id}/cancel
```

**Versioning**
```
Strategy: URL path versioning (/api/v1/resource, /api/v2/resource)
Support: Current + previous version minimum
Sunset: 6 months notice before deprecation
```

**Response Format**
```json
{
  "data": { /* actual response */ },
  "meta": {
    "requestId": "uuid",
    "timestamp": "ISO8601"
  },
  "pagination": {  /* if paginated */
    "page": 1,
    "pageSize": 20,
    "totalPages": 10,
    "totalItems": 200
  }
}
```

**Error Format**
```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User with ID 123 not found",
    "details": {},
    "timestamp": "ISO8601",
    "requestId": "uuid"
  }
}
```

**HTTP Status Codes**
```
200 OK: Success
201 Created: Resource created
204 No Content: Success, no response body
400 Bad Request: Invalid input
401 Unauthorized: Authentication required
403 Forbidden: Insufficient permissions
404 Not Found: Resource not found
409 Conflict: Resource conflict (e.g., duplicate)
422 Unprocessable Entity: Validation failed
429 Too Many Requests: Rate limit exceeded
500 Internal Server Error: Unexpected error
503 Service Unavailable: Service temporarily down
```

### Event Standards

**Event Schema**
```json
{
  "eventId": "uuid",
  "eventType": "domain.entity.action",
  "eventVersion": "v1",
  "timestamp": "ISO8601",
  "correlationId": "uuid",
  "causationId": "uuid",
  "data": {
    /* event-specific payload */
  },
  "metadata": {
    "source": "service-name",
    "userId": "user-id-if-applicable"
  }
}
```

**Event Naming**
```
Pattern: domain.entity.action
Examples:
  - user.account.created
  - order.payment.completed
  - inventory.stock.depleted
  - notification.email.sent
```

**Schema Evolution**
- Backward compatible changes only
- Add new optional fields
- Never remove fields (deprecate instead)
- Never change field types
- Use schema registry for validation

---

## Non-Functional Requirements

### Performance

**Response Times (p95)**
```
Synchronous API calls: < 200ms
Database queries: < 50ms
External service calls: < 500ms (with timeout)
Event publishing: < 10ms (async)
```

**Throughput**
```
Minimum: 100 requests/second per instance
Scaling: Horizontal auto-scaling at 70% CPU
Connection pooling: Configured for expected load
```

### Reliability

**Availability SLA**
```
Critical services (auth, payment): 99.95% (< 22 minutes downtime/month)
Core services (user, order): 99.9% (< 44 minutes downtime/month)
Supporting services: 99.5% (< 3.5 hours downtime/month)
```

**Error Handling**
```
- All errors logged with correlation IDs
- Circuit breaker on external calls: 50% error rate → open
- Retry policy: 3 attempts, exponential backoff (1s, 2s, 4s)
- Timeout: 5s default, 30s max for batch operations
- Graceful degradation: Return cached/default data when possible
```

**Health Checks**
```
Endpoint: GET /health
Response:
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "ISO8601",
  "checks": {
    "database": "healthy",
    "cache": "healthy",
    "dependencies": {
      "auth-service": "healthy",
      "user-service": "degraded"
    }
  }
}

Readiness: /health/ready (is service ready to receive traffic?)
Liveness: /health/live (is service alive? restart if not)
```

### Security

**Authentication**
```
Standard: JWT tokens (HS256 or RS256)
Token lifetime: 15 minutes (access), 7 days (refresh)
Header: Authorization: Bearer {token}
Internal services: mTLS or service mesh auth
```

**Authorization**
```
Model: RBAC (Role-Based Access Control)
Enforcement: At API gateway + service level (defense in depth)
Principle: Least privilege
```

**Data Protection**
```
In Transit: TLS 1.3 minimum
At Rest: AES-256 encryption for sensitive data
Secrets: Vault/AWS Secrets Manager (never in code/env files)
PII: Encrypted, access logged, retention policy enforced
```

**Input Validation**
```
- Validate all inputs at API boundary
- Sanitize data to prevent injection attacks
- Use schema validation (JSON Schema, Pydantic, etc.)
- Rate limiting: Per user/IP, documented in API spec
```

### Observability

**Structured Logging**
```json
{
  "timestamp": "ISO8601",
  "level": "INFO|WARN|ERROR",
  "message": "Human-readable message",
  "correlationId": "uuid",
  "userId": "user-id-if-applicable",
  "service": "service-name",
  "environment": "prod|staging|dev",
  "metadata": {}
}
```

**Log Levels**
```
ERROR: Service degradation, errors
WARN: Potential issues, deprecation usage
INFO: Significant events (API calls, database operations)
DEBUG: Detailed diagnostic info (dev/staging only)
```

**Metrics (RED Method)**
```
- Rate: Requests per second
- Errors: Error rate percentage
- Duration: Latency distribution (p50, p95, p99)

Additional:
- Queue depth (for async processors)
- Database connection pool utilization
- Cache hit/miss ratio
```

**Distributed Tracing**
```
Standard: OpenTelemetry compatible
Trace headers: Propagate correlation ID across services
Sampling: 100% for errors, 10% for success (adjust per load)
Tools: Jaeger, Zipkin, AWS X-Ray, or DataDog
```

**Alerting**
```
Critical alerts (PagerDuty):
  - Error rate > 5%
  - p95 latency > SLA threshold
  - Service down (health check failing)
  - Database connection pool exhausted

Warning alerts (Slack):
  - Error rate > 1%
  - Degraded dependency
  - High memory/CPU usage (> 80%)
```

---

## Development Standards

### Testing

**Test Pyramid**
```
Unit Tests: 70%
  - Fast, isolated
  - Mock external dependencies
  - Coverage > 80%

Integration Tests: 20%
  - Test service boundaries
  - Real database (test instance)
  - Contract tests for APIs/events

End-to-End Tests: 10%
  - Critical user flows
  - Full environment
  - Smoke tests for deployments
```

**Contract Testing**
```
- Use Pact or similar for consumer-driven contracts
- Provider verifies contracts from all consumers
- Contracts version-controlled
- Breaking changes detected before deployment
```

### Code Quality

**Required Checks**
```
- Linting: Language-specific linter (ESLint, Pylint, etc.)
- Formatting: Consistent style (Prettier, Black, gofmt)
- Security scanning: SAST tools, dependency vulnerability checks
- Code coverage: > 80% for critical paths
- Pre-commit hooks: Format, lint, test
```

**Code Review**
```
- All changes require review (no direct commits to main)
- At least 1 approval required
- Automated checks must pass
- Review checklist: Tests, docs, security, performance
```

### Deployment

**CI/CD Pipeline**
```
1. Commit → Trigger build
2. Run tests (unit, integration, contract)
3. Build container image
4. Security scan (vulnerability check)
5. Push to registry
6. Deploy to staging
7. Run smoke tests
8. Manual approval for production
9. Deploy to production (canary/blue-green)
10. Health check validation
11. Rollback on failure
```

**Deployment Strategy**
```
Default: Rolling update (zero downtime)
For critical changes: Blue/Green deployment
For gradual rollouts: Canary deployment (10%, 50%, 100%)
Feature flags: For risky features (LaunchDarkly, ConfigCat)
```

**Rollback Criteria**
```
Automatic rollback if:
  - Health check fails
  - Error rate > 10%
  - p95 latency > 2x normal

Manual rollback for:
  - Business logic issues
  - Data integrity concerns
```

---

## Service Lifecycle

### New Service Checklist

Before a new service goes to production:

**Design & Documentation**
- [ ] Bounded context clearly defined
- [ ] Service spec completed (service-spec-template.md)
- [ ] API contracts documented (OpenAPI spec)
- [ ] Event schemas defined
- [ ] Dependencies documented
- [ ] Architecture review completed

**Implementation**
- [ ] Health check endpoints implemented
- [ ] Structured logging configured
- [ ] Metrics exposed (Prometheus format)
- [ ] Distributed tracing integrated
- [ ] Error handling with proper status codes
- [ ] Input validation implemented
- [ ] Authentication/Authorization enforced
- [ ] Rate limiting configured

**Testing**
- [ ] Unit tests (> 80% coverage)
- [ ] Integration tests
- [ ] Contract tests (for APIs and events)
- [ ] Load testing completed (meets SLA)
- [ ] Security testing (OWASP Top 10)

**Infrastructure**
- [ ] Container image built
- [ ] Helm chart/Kubernetes manifests created
- [ ] Environment variables documented
- [ ] Secrets configured in vault
- [ ] Resource limits defined (CPU, memory)
- [ ] Auto-scaling configured
- [ ] Database migrations tested

**Operational Readiness**
- [ ] Runbook created
- [ ] Alerts configured
- [ ] Dashboards created
- [ ] On-call rotation assigned
- [ ] Incident response plan
- [ ] Backup/restore procedure tested

### Service Deprecation

When retiring a service:

1. **Announce:** 6 months notice to all consumers
2. **Document:** Migration guide for consumers
3. **Support:** Parallel running of old + new service
4. **Monitor:** Track usage of deprecated endpoints
5. **Sunset:** Disable service after grace period
6. **Archive:** Preserve specs and contracts for reference

---

## Decision Framework

When making architectural decisions, ask:

1. **Does this maintain service independence?**
   - Can services still deploy independently?
   - Are we creating tight coupling?

2. **Can we handle failure gracefully?**
   - What if this service is down?
   - What if this API call times out?

3. **Is this the simplest solution?**
   - Are we over-engineering?
   - Can we start simpler and evolve?

4. **Does this align with our principles?**
   - Bounded contexts respected?
   - Communication patterns followed?
   - Standards adhered to?

5. **Can we observe and debug this?**
   - Adequate logging/metrics?
   - Tracing across services?
   - Runbook exists?

**When to deviate:** Document exceptions in `specs/ADR/` (Architecture Decision Records)

---

## Common Patterns & Anti-Patterns

### ✅ DO

- **Use asynchronous events** for: Notifications, analytics, cache updates
- **Use circuit breakers** for all external calls
- **Cache aggressively** but invalidate smartly
- **Design for failure:** Assume dependencies will fail
- **Keep services small:** If team can't understand it, it's too big
- **Version APIs early:** Easier to start with v1 than retrofit later
- **Document contracts:** OpenAPI specs are not optional

### ❌ DON'T

- **Share databases** between services
- **Make deep sync call chains** (A → B → C → D)
- **Skip health checks** or monitoring
- **Use distributed transactions** (use Sagas instead)
- **Hardcode URLs/credentials** (use service discovery + vault)
- **Deploy without rollback plan**
- **Skip contract tests** (they prevent breaking consumers)

---

## Governance

**Architecture Review Board**
- Reviews new service proposals
- Approves exceptions to standards
- Ensures consistency across services

**Contract Review**
- All API/event contract changes reviewed
- Breaking changes require major version bump
- Consumer notification required

**Security Review**
- Required for services handling PII/financial data
- Penetration testing for external-facing services
- Annual security audits

---

## Resources

- **Templates:** `/templates/microservices/service-spec-template.md`
- **Commands:** `/speckit.validate-contracts`, `/speckit.service-catalog`
- **Examples:** `/examples/microservices/`
- **Architecture Decision Records:** `/specs/ADR/`

---

**Last Updated:** [Date]
**Approved By:** [Architecture Team]
**Next Review:** [Date + 6 months]
