# Microservice Specification Template

## Service Overview

### Service Name
[Name of the microservice]

### Service Boundary
**What this service is responsible for:**
- [Bounded context definition]
- [Core domain entities owned]
- [Business capabilities provided]

**What this service is NOT responsible for:**
- [Explicitly exclude related but separate concerns]

### Service Type
- [ ] API Service (synchronous)
- [ ] Event Processor (asynchronous)
- [ ] Backend for Frontend (BFF)
- [ ] Gateway/Proxy
- [ ] Worker/Job Processor

---

## API Contracts

### REST Endpoints

#### Endpoint 1: [Operation Name]
```yaml
Method: GET/POST/PUT/DELETE
Path: /api/v1/resource/{id}
Auth: Required/Optional
Rate Limit: X requests/minute

Request:
  Headers:
    - Authorization: Bearer {token}
  Body:
    {
      "field": "type"
    }

Response (200):
  {
    "data": {},
    "meta": {}
  }

Errors:
  - 400: Bad Request
  - 401: Unauthorized
  - 404: Not Found
  - 500: Internal Server Error
```

### Events Published

#### Event: [EventName]
```yaml
Topic/Exchange: events.domain.entity.action
Schema Version: v1
Trigger: When [condition]

Payload:
  {
    "eventId": "uuid",
    "timestamp": "ISO8601",
    "eventType": "string",
    "data": {
      "entity": {}
    },
    "metadata": {}
  }

Consumers:
  - [service-name-1]: What they do with it
  - [service-name-2]: What they do with it
```

### Events Consumed

#### Event: [EventName]
```yaml
From Service: [producer-service]
Topic/Exchange: events.source.entity.action
Action: What this service does when received
Idempotency: How duplicate events are handled
Error Handling: Dead letter queue strategy
```

---

## Service Dependencies

### Upstream Services (This Service Calls)

| Service | API/Events | Purpose | Failure Mode |
|---------|------------|---------|--------------|
| auth-service | POST /api/v1/validate | Token validation | Return 401, cache last known |
| user-service | GET /api/v1/users/{id} | User details | Return cached data if available |

### Downstream Services (Services That Call This)

| Service | Endpoints Used | SLA Requirements |
|---------|----------------|------------------|
| api-gateway | All public APIs | 99.9%, <200ms p95 |
| notification-service | Events only | N/A (async) |

---

## Data Ownership

### Primary Data Entities
**Entities this service is the source of truth for:**

#### Entity: [EntityName]
```yaml
Table/Collection: entity_name
Owned Fields:
  - id: UUID (Primary Key)
  - field1: type
  - field2: type
  - created_at: timestamp
  - updated_at: timestamp

Access Pattern:
  - Read: By ID, By field1
  - Write: Create, Update (no hard deletes)

Replication:
  - Replicated to: [service-name] via [events/API]
  - Purpose: [read replica/denormalized view]
```

### External Data (Read-Only)
**Data from other services this service caches:**

| Entity | Source Service | Sync Method | TTL/Refresh |
|--------|----------------|-------------|-------------|
| User Profile | user-service | Event subscription | Real-time |
| Product Catalog | product-service | Scheduled sync | 5 minutes |

---

## Non-Functional Requirements

### Performance
- Response Time (p95): < [X]ms for reads, < [Y]ms for writes
- Throughput: [X] requests/second sustained
- Batch Operations: Support up to [N] items

### Scalability
- Horizontal Scaling: Stateless design, auto-scale on CPU > 70%
- Connection Pooling: Database connections capped at [N]
- Cache Strategy: [Redis/Memcached], [TTL strategy]

### Availability
- SLA: [99.9%/99.95%/99.99%]
- Recovery Time Objective (RTO): < [X] minutes
- Recovery Point Objective (RPO): < [Y] minutes of data loss
- Health Check Endpoint: GET /health

### Security
- Authentication: [JWT/OAuth2/API Key]
- Authorization: [RBAC/ABAC]
- Encryption: TLS 1.3 in transit, AES-256 at rest
- Secrets Management: [Vault/AWS Secrets Manager]
- Input Validation: All inputs sanitized, schema validated

### Observability
- Structured Logging: JSON format, correlation IDs
- Metrics: Prometheus-compatible
  - Request rate, error rate, duration (RED metrics)
  - Queue depth, processing time (for async)
- Distributed Tracing: OpenTelemetry compatible
- Alerting: PagerDuty/Opsgenie on critical failures

---

## Deployment & Infrastructure

### Container Specification
```yaml
Base Image: [language:version]
Resource Limits:
  CPU: [X] cores (request), [Y] cores (limit)
  Memory: [X]Mi (request), [Y]Mi (limit)
Environment Variables:
  - DATABASE_URL (secret)
  - REDIS_URL (config)
  - LOG_LEVEL (config)
Ports:
  - 8080: HTTP API
  - 9090: Metrics endpoint
```

### Configuration
- Config Source: [Environment vars/ConfigMap/Secrets]
- Feature Flags: [LaunchDarkly/ConfigCat/Custom]
- Dynamic Config Reload: Yes/No

### Database
- Type: [PostgreSQL/MySQL/MongoDB/etc.]
- Schema Migration: [Flyway/Liquibase/Alembic]
- Backup Schedule: [Daily/Hourly]
- Read Replicas: [Yes/No], [N] replicas

---

## Testing Strategy

### Unit Tests
- Coverage Target: > [X]%
- Mock External Services: Yes
- Test Framework: [pytest/jest/junit]

### Integration Tests
- Service Boundary Tests: API contract validation
- Database Integration: Test migrations, queries
- Message Queue Integration: Test event publishing/consuming

### Contract Tests
- Consumer-Driven Contracts: [Pact/Spring Cloud Contract]
- Provider Tests: Validate API spec compliance
- Event Schema Tests: Validate published events match schema

### End-to-End Tests
- Critical Paths: [List critical user journeys]
- Test Environment: Staging with real dependencies
- Data Setup: [Test data strategy]

---

## Migration & Rollout

### Deployment Strategy
- [ ] Blue/Green
- [ ] Canary (X% traffic gradually)
- [ ] Rolling Update
- [ ] Feature Flag Gated

### Backward Compatibility
- API Versioning: [URL path/Header-based]
- Breaking Changes: Require new version, old version sunset in [X] months
- Event Schema Evolution: Backward compatible only, use schema registry

### Rollback Plan
- Trigger: Error rate > [X]%, p95 latency > [Y]ms
- Steps: [Automated rollback procedure]
- Data Migration Rollback: [Strategy for schema changes]

---

## Operational Runbook

### Common Issues

#### Issue: Service Not Responding
**Symptoms:** Health check fails, 503 errors
**Diagnosis:** Check logs, CPU/memory usage
**Resolution:** Restart pods, scale horizontally

#### Issue: High Latency
**Symptoms:** p95 > threshold
**Diagnosis:** Check database slow queries, external service latency
**Resolution:** Optimize queries, increase cache TTL, add circuit breaker

### Maintenance Windows
- Database backups: [Schedule]
- Schema migrations: [Process]
- Dependency updates: [Monthly/Quarterly]

---

## Open Questions

### Technical Decisions Pending
- [ ] Question 1: [Technical decision needed]
  - Options: A, B, C
  - Impact: [Performance/Cost/Complexity trade-offs]
  - Decision by: [Date]

### Clarifications Needed
- [ ] Clarification 1: [Ambiguity in requirements]
  - Asked: [Date]
  - Answered: [Date]
  - Answer: [Summary]

---

## Acceptance Criteria

### Service is Production-Ready When:
- [ ] All REST endpoints documented with OpenAPI spec
- [ ] All events have schema definitions
- [ ] Health check endpoint implemented
- [ ] Metrics and logging configured
- [ ] Database migrations tested
- [ ] Circuit breakers configured for external calls
- [ ] Rate limiting implemented
- [ ] Authentication/Authorization enforced
- [ ] Container image built and pushed
- [ ] Helm chart/Kubernetes manifests created
- [ ] Load testing completed (meets SLA)
- [ ] Security scan passed (no critical vulnerabilities)
- [ ] Contract tests passing
- [ ] Runbook documented

---

## References

- OpenAPI Spec: `contracts/api-spec.yaml`
- Event Schemas: `contracts/events/*.avsc` or `*.json`
- Architecture Diagram: [Link or embedded diagram]
- Related Services: [Links to other service specs]
