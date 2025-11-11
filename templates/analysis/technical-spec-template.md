# Technical Specification - Modernization Architecture

**Project**: <<PROJECT_NAME>>
**Legacy Version**: <<LEGACY_VERSION>> → **Target Version**: <<TARGET_VERSION>>
**Architecture Date**: <<ANALYSIS_DATE>>
**Architect**: AI Agent
**Status**: Draft (Modernization Plan)

---

## Instructions for AI

This template is based on **Section B (Architecture)** from the Universal Meta-Prompt.
It is adapted for **legacy code modernization** to define HOW to build the new system.

**Key Adaptations for Modernization**:

- Show **Legacy vs. Target** comparison for each section
- Use **user's modernization preferences** from Q1-Q10
- Include **migration path** (not just greenfield)
- Leverage **AI knowledge base** for LTS versions (don't hardcode)
- Use **phase-colored Mermaid** adapted to target infrastructure
- Convert **legacy NFRs to measurable SLO/SLI targets**

**Placeholders to Fill** (from user answers + AI knowledge):

- `<<USER_CHOICE_LANGUAGE>>` - From Q1 (e.g., "Java 21 LTS")
- `<<USER_CHOICE_DATABASE>>` - From Q2 (e.g., "PostgreSQL 16 LTS")
- `<<USER_CHOICE_MESSAGE_BUS>>` - From Q3 (e.g., "Apache Kafka")
- `<<USER_CHOICE_PACKAGE_MANAGER>>` - From Q4 (e.g., "Gradle")
- `<<USER_CHOICE_DEPLOYMENT>>` - From Q5 (e.g., "Kubernetes cluster")
- `<<USER_CHOICE_IAC>>` - From Q6 (e.g., "Helm charts")
- `<<USER_CHOICE_CONTAINERIZATION>>` - From Q7 (e.g., "Docker + Kubernetes")
- `<<USER_CHOICE_OBSERVABILITY>>` - From Q8 (e.g., "Prometheus + Grafana")
- `<<USER_CHOICE_SECURITY>>` - From Q9 (e.g., "OAuth 2.0 / OpenID Connect")
- `<<USER_CHOICE_TESTING>>` - From Q10 (e.g., "Unit + Integration + E2E tests")
- `<<LEGACY_PAIN_POINTS>>` - Extract from functional-spec.md
- `<<LTS_VERSIONS>>` - Query AI knowledge base for latest LTS

---

## 1. Architectural Principles

### Legacy System Principles (Extracted)

From analysis of the legacy codebase:

1. **<<Principle 1>>** - <<Evidence from code>>
2. **<<Principle 2>>** - <<Evidence from code>>
3. **<<Principle 3>>** - <<Evidence from code>>

### Target System Principles (New + Preserved)

**Preserve from Legacy**:

- ✅ <<Good pattern to keep>> (Evidence: <<file:line>>)

**Add for Modernization**:

- ✨ **Simplicity**: Reduce complexity (current: <<N>> layers → target: <<M>> layers)
- ✨ **Evolvability**: Use latest LTS for long-term support
- ✨ **Operability**: Cloud-native observability and automation
- ✨ **Security**: Modern auth (OAuth 2.0), encryption at rest/transit
- ✨ **Cost Awareness**: Right-size resources, use managed services

---

## 2. Why This Pattern (Legacy → Target)

### Legacy Architecture Pattern

**Current Pattern**: <<e.g., Monolithic 3-tier>>

**Evidence**:

- <<Directory structure shows monolith>>
- <<All code in single deployment unit>>
- <<Direct DB access from web layer>>

**Pain Points** (from analysis):

1. <<Pain 1>>: <<e.g., Cannot scale components independently>>
2. <<Pain 2>>: <<e.g., Long deployment cycles>>
3. <<Pain 3>>: <<e.g., Technology lock-in>>

### Target Architecture Pattern

**Chosen Pattern**: <<Based on user's deployment choice + best practices>>

**Mapping BA Needs → Pattern**:

- **Need**: <<from functional-spec.md>> → **Pattern**: <<How target pattern addresses it>>
- **Need**: <<Scalability>> → **Pattern**: <<Microservices with K8s autoscaling>>
- **Need**: <<Faster releases>> → **Pattern**: <<Independent service deployments>>

**Rationale**:

1. <<Reason 1>>: <<Why this pattern fits>>
2. <<Reason 2>>: <<Based on user's infrastructure choice>>
3. <<Reason 3>>: <<Leverages LTS stack>>

---

## 3. Capabilities by Phase (50/30/15/5)

Map legacy features (from functional-spec.md) to modernization phases:

| Phase | Scope | Value % | Features (from Legacy) | Risks | Exit Criteria |
|-------|-------|--------:|----------------------|-------|---------------|
| **P1** | Core MVP | 50 | <<CRITICAL features from FR-CRIT-*>> | <<Risk>> | <<Criteria>> |
| **P2** | Extended | 30 | <<STANDARD features from FR-STD-*>> | <<Risk>> | <<Criteria>> |
| **P3** | Enhanced | 15 | <<Nice-to-have features>> | <<Risk>> | <<Criteria>> |
| **P4** | Polish | 5 | <<Optional/future features>> | <<Risk>> | <<Criteria>> |

**P1 Minimum Viable Migration (50% value)**:

- ✅ <<Feature 1 from functional-spec>> (CRITICAL)
- ✅ <<Feature 2 from functional-spec>> (CRITICAL)
- ✅ <<Feature 3 from functional-spec>> (CRITICAL)
- ✅ Data migration for <<core entities>>
- ✅ Auth/security parity with legacy
- **Exit Criteria**: Can replace legacy for <<core workflow>>

**P2 Feature Parity (30% value)**:

- ✅ <<Feature 4-6 from functional-spec>> (STANDARD)
- ✅ Complete data migration
- ✅ <<Integration X>>
- **Exit Criteria**: Full functional parity with legacy

**P3 Modernization Benefits (15% value)**:

- ✨ <<New capability enabled by modern stack>>
- ✨ <<Performance improvements>>
- ✨ <<Observability enhancements>>
- **Exit Criteria**: Demonstrates ROI of modernization

**P4 Future Enhancements (5% value)**:

- 🚀 <<Future feature>>
- 🚀 <<Experimental feature>>
- **Exit Criteria**: Foundation for future growth

---

## 4. High-Level Architecture (Phase-Colored Mermaid)

### Target Architecture Diagram

**Pattern**: <<Adapted based on USER_CHOICE_DEPLOYMENT>>

```mermaid
%%{init: { "themeVariables": { "fontFamily":"Inter","lineColor":"#6b7280","primaryTextColor":"#111827"}}}%%
graph TB
  classDef P1 fill:#90EE90,stroke:#1f2937,color:#111;
  classDef P2 fill:#FFD700,stroke:#1f2937,color:#111;
  classDef P3 fill:#FFA500,stroke:#1f2937,color:#111;
  classDef P4 fill:#D3D3D3,stroke:#1f2937,color:#111;

  %% Example for Kubernetes deployment (adapt based on user choice):
  INGRESS[Ingress/ALB]:::P1 --> API[API Gateway]:::P1
  API --> AUTH[Auth Service]:::P1
  API --> CORE[Core Service]:::P1
  CORE --> DB[(Database)]:::P1
  CORE --> CACHE[(Cache)]:::P2
  API --> INTEG[Integration Service]:::P2
  INTEG --> EXT[External APIs]:::P2
  CORE --> EVENTS[Event Bus]:::P3
  EVENTS --> ANALYTICS[Analytics]:::P3
  MON[Monitoring]:::P1

  %% Legend
  LEGEND[Legend: P1=Green MVP | P2=Yellow Extended | P3=Orange Enhanced | P4=Gray Future]
```

**Notes**:

- Diagram shows **<<USER_CHOICE_DEPLOYMENT>>** deployment pattern
- Uses **<<USER_CHOICE_CONTAINERIZATION>>** for runtime
- Managed by **<<USER_CHOICE_IAC>>** infrastructure as code

### Legacy vs. Target Comparison

| Aspect | Legacy | Target | Improvement |
|--------|--------|--------|-------------|
| Deployment | <<VM/bare metal>> | <<Kubernetes cluster>> | Auto-scaling, self-healing |
| Database | <<Oracle 11g>> | <<PostgreSQL 16 LTS>> | Open source, modern features |
| Caching | <<Memcached 1.4>> | <<Redis 7.x>> | Persistence, pub/sub |
| Observability | <<Log files>> | <<Prometheus + Grafana>> | Metrics, dashboards, alerts |
| Auth | <<Session-based>> | <<OAuth 2.0 / JWT>> | Stateless, scalable |

---

## 5. Component / Service Responsibilities

Map legacy code to modernized components:

### Component: <<Component Name>> (e.g., Auth Service)

**Responsibilities**:

- <<Responsibility 1>>
- <<Responsibility 2>>

**Migrates From** (Legacy):

- <<legacy/src/auth/>> → <<new/services/auth-service/>>
- <<legacy/src/session/>> → (Replaced by JWT tokens)

**Technology Stack**:

- Language: <<USER_CHOICE_LANGUAGE>> (from Q1)
- Framework: <<e.g., Spring Boot 3.x for Java, FastAPI for Python>>
- Database: <<USER_CHOICE_DATABASE>> (from Q2)

**P1 Scope**: <<Core functionality>>
**P2 Scope**: <<Extended functionality>>

### Component: <<Next Component>>

<<Repeat>>

---

## 6. Interfaces & Contracts

### API Design

**Legacy**:

- Protocol: <<REST/SOAP/RPC>>
- Auth: <<Session cookies>>
- Versioning: <<None/implicit>>

**Target**:

- Protocol: **REST** (with OpenAPI 3.1 spec)
- Auth: **<<USER_CHOICE_SECURITY>>** (from Q9)
- Versioning: **URI versioning** (`/api/v1/`, `/api/v2/`)
- Rate Limiting: **<<100 req/min per user>>** (from legacy config)
- Idempotency: **Idempotency-Key header** for mutations
- Error Model: **RFC7807** (Problem Details)

### Example Endpoint (Modernized)

| Method | Path | Auth | Request Schema | Response Schema | Errors |
|--------|------|------|----------------|-----------------|--------|
| GET | `/api/v1/users` | Bearer token | - | UserListResponse | 401, 429, 500 |
| POST | `/api/v1/users` | Bearer token | UserInput | User | 400, 401, 409, 429, 500 |

**Schemas**: See functional-spec.md §10 for legacy contracts
**Target Schemas**: <<Update with modern conventions (camelCase, ISO8601, etc.)>>

### Authentication Flow (Target)

**<<USER_CHOICE_SECURITY>>** implementation:

- **Legacy**: Session-based (30min timeout)
- **Target**: OAuth 2.0 Authorization Code Flow with PKCE
- **Token Lifetime**: Access token 15min, Refresh token 7 days
- **Migration**: Dual-mode support during transition

---

## 7. Data & Schema (Legacy → Target)

### Database Migration

**Legacy Database**: <<Oracle 11g>>
**Target Database**: <<USER_CHOICE_DATABASE>> (from Q2)

### Schema Mapping

#### Entity: <<User>> (Example)

**Legacy Schema** (from functional-spec.md §8):

```sql
-- Oracle 11g
CREATE TABLE users (
  id NUMBER PRIMARY KEY,
  email VARCHAR2(255) UNIQUE NOT NULL,
  password_hash VARCHAR2(255) NOT NULL,
  role VARCHAR2(50) DEFAULT 'user',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Target Schema** (PostgreSQL 16):

```sql
-- PostgreSQL 16 LTS
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role user_role DEFAULT 'user', -- ENUM type
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE user_role AS ENUM ('admin', 'user', 'guest');
```

**Migration Notes**:

- ID: NUMBER → UUID (generate mapping table)
- Timestamps: Add timezone awareness
- Role: VARCHAR → ENUM for type safety
- Add `updated_at` for audit trail

**Migration Tool**: <<pgloader / custom script>>

### Data Migration Strategy

| Phase | Approach | Rollback Plan |
|-------|----------|---------------|
| P1 | Dual-write (legacy + new) | Stop writing to new, keep legacy |
| P2 | Read from new, fallback to legacy | Switch read back to legacy |
| P3 | Decommission legacy | Restore from backups |

---

## 8. Target Tech Stack (From User Preferences + LTS)

### Summary Table

| Component | Legacy | User Choice | LTS Version | EOL Date | Rationale |
|-----------|--------|-------------|-------------|----------|-----------|
| Language | <<Java 8>> | <<USER_CHOICE_LANGUAGE>> | <<Java 21 LTS>> | 2028-09 | Latest LTS, performance, features |
| Database | <<Oracle 11g>> | <<USER_CHOICE_DATABASE>> | <<PostgreSQL 16>> | 2028-11 | Open source, JSONB, better perf |
| Message Bus | <<TIBCO EMS>> | <<USER_CHOICE_MESSAGE_BUS>> | <<Kafka 3.x>> | Active | Industry standard, scalable |
| Package Mgr | <<Maven 3.6>> | <<USER_CHOICE_PACKAGE_MANAGER>> | <<Gradle 8.x>> | Active | Faster builds, better caching |
| Deployment | <<VM>> | <<USER_CHOICE_DEPLOYMENT>> | <<Kubernetes 1.28+>> | Active | Cloud-native, auto-scaling |
| IaC | <<Manual>> | <<USER_CHOICE_IAC>> | <<Helm 3.x>> | Active | K8s package manager |
| Container | <<None>> | <<USER_CHOICE_CONTAINERIZATION>> | <<Docker 24.x>> | Active | Consistent environments |
| Observability | <<Logs>> | <<USER_CHOICE_OBSERVABILITY>> | <<Prom 2.x + Grafana>> | Active | Metrics, dashboards, alerts |
| Security (Auth) | <<Sessions>> | <<USER_CHOICE_SECURITY>> | <<OAuth 2.0 / OIDC>> | Standard | Stateless, scalable, secure |
| Testing | <<Unit only>> | <<USER_CHOICE_TESTING>> | <<JUnit 5 + Testcontainers>> | Active | Unit + Integration + E2E |

**LTS Guidance** (AI Knowledge Base):

- All versions above queried from official sources or AI knowledge as of <<ANALYSIS_DATE>>
- Chosen based on: Latest LTS, community support, team familiarity, migration complexity

### Detailed Stack Specifications

#### Language: <<USER_CHOICE_LANGUAGE>>

**Version**: <<Java 21 LTS>> (example)
**Why**: Latest LTS with support until 2028, performance improvements (Virtual Threads, Pattern Matching)
**Migration Complexity**: HIGH (Java 8 → 21 requires code changes)
**Migration Guide**: [Oracle Java 8 to 21 Migration](https://docs.oracle.com/...)

**Alternative Considered**: Java 17 LTS (more conservative, but shorter support)

#### Framework: <<Spring Boot 3.2>>

**Why**: Matches Java 21, native compilation, observability built-in
**Migration**: Spring Boot 2.x → 3.x has breaking changes (Jakarta EE namespace)

#### Database: <<USER_CHOICE_DATABASE>>

**Version**: <<PostgreSQL 16 LTS>>
**Why**: Latest LTS, JSONB for flexible schema, better concurrent writes
**Migration Tool**: `pgloader` for automated Oracle → PostgreSQL
**Schema Compatibility**: 90% compatible, need to handle NUMBER → UUID, sequences

<<Repeat for other stack components>>

#### Library Availability Validation

**Artifactory URL**: <<ARTIFACTORY_URL or "Not configured">>

**Validation Results** (if Artifactory configured):

| Library | Category | Status | Version | Notes |
|---------|----------|--------|---------|-------|
| <<spring-boot-starter-web>> | External | ✅ Approved | 3.2.0 | Found in Artifactory |
| <<jackson-databind>> | External | ✅ Approved | 2.15.3 | Found in Artifactory |
| <<@acmecorp/auth-client>> | Corporate | ✅ Approved | 2.1.0 | Internal package |
| <<some-library>> | External | ❌ Not Whitelisted | N/A | Not found - risk documented |
| <<java.util.*>> | Standard | ⊘ Skipped | N/A | Built-in, no validation needed |

**Summary**:
- ✅ Approved: <<N>> libraries
- ❌ Not Whitelisted: <<N>> libraries (documented as risk)
- ⊘ Skipped: <<N>> standard/built-in libraries

**Risk Assessment** (if any libraries not whitelisted):
- **Impact**: <<Libraries not approved may cause build failures in corporate environment>>
- **Mitigation**: <<1) Request security approval, 2) Use approved alternatives, 3) Document exception>>
- **Decision**: <<User chose [A/B/C] - see analysis-report.md for details>>

**Note**: If Artifactory URL not configured, this section shows "Validation skipped - no corporate package registry configured"

---

## 9. NFR Targets (Measurable SLO/SLI)

Convert legacy NFRs (from functional-spec.md §7) to measurable targets:

### Performance

| Metric | Legacy | Target | Measurement | SLI |
|--------|--------|--------|-------------|-----|
| API Response (p95) | <<1.5s>> | **< 500ms** | Prometheus histogram | 95% of requests < 500ms |
| API Response (p99) | <<3s>> | **< 1s** | Prometheus histogram | 99% of requests < 1s |
| Throughput | <<100 req/min>> | **1000 req/min** | Prometheus counter | Sustained load test |
| DB Query (p95) | <<800ms>> | **< 100ms** | APM tracing | Query optimization + indexing |

**SLO**: 95% of API requests complete in < 500ms (measured weekly)

### Availability

| Metric | Legacy | Target | Measurement |
|--------|--------|--------|-------------|
| Uptime SLA | <<99%>> | **99.9%** | Uptime monitor (Datadog/Pingdom) |
| Error Rate | <<2%>> | **< 0.1%** | Prometheus error counter |
| MTTR | <<2 hours>> | **< 15 minutes** | Incident tracking |

**SLO**: 99.9% uptime per month (allows 43min downtime)

### Scalability

| Metric | Legacy | Target | Approach |
|--------|--------|--------|----------|
| Horizontal Scaling | Manual | **Auto (HPA)** | Kubernetes HPA based on CPU/memory |
| Max Load | <<1000 users>> | **10,000 users** | Load testing + auto-scaling |
| Resource Efficiency | <<50% CPU idle>> | **70-80% utilization** | Right-sizing + auto-scaling |

### Security

| Metric | Legacy | Target | Implementation |
|--------|--------|--------|----------------|
| Auth Token Lifetime | 30min session | **15min access token** | OAuth 2.0 / JWT |
| Encryption at Rest | <<None>> | **AES-256** | Database encryption |
| Encryption in Transit | <<TLS 1.0>> | **TLS 1.3** | Ingress/ALB config |
| Vulnerability Scan | Manual | **Automated (weekly)** | Snyk / Trivy integration |

### Observability

| Aspect | Legacy | Target | Tool |
|--------|--------|--------|------|
| Logs | Text files | **Structured (JSON)** | <<USER_CHOICE_OBSERVABILITY>> |
| Metrics | <<None>> | **RED (Rate/Errors/Duration)** | Prometheus |
| Tracing | <<None>> | **Distributed tracing** | OpenTelemetry + Jaeger |
| Dashboards | <<None>> | **Grafana dashboards** | Pre-built + custom |
| Alerting | <<Email on crash>> | **PagerDuty integration** | Alert rules + runbooks |

---

## 10. Operations & SRE

### SLO Table

| Service | SLI | Target SLO | Error Budget (monthly) | Alert Threshold |
|---------|-----|------------|----------------------|-----------------|
| API | Response time p95 < 500ms | 99.5% | 21 minutes downtime | 98% threshold |
| API | Error rate | < 0.1% | 43 requests | 0.5% spike |
| DB | Query time p95 < 100ms | 99% | 7 hours slow | 95% threshold |

### Runbooks

<<Link to runbook repo or inline key runbooks>>

- **Runbook 001**: High API latency
- **Runbook 002**: Database connection pool exhaustion
- **Runbook 003**: Cache miss storm

### Rollout / Rollback Strategy

**Deployment Strategy**: <<Canary / Blue-Green / Rolling>>

- **P1**: Blue-Green (safe, instant rollback)
- **P2+**: Canary (5% → 25% → 50% → 100%)

**Rollback Triggers**:

- Error rate > 1%
- p95 latency > 2x baseline
- Any P0/P1 incident

**Rollback Time**: <<< 5 minutes>> (automated)

---

## 11. Security & Compliance

### Threat Model

| Threat | Legacy Mitigation | Target Mitigation | Priority |
|--------|------------------|------------------|----------|
| SQL Injection | <<ORM only>> | **Parameterized queries + ORM** | HIGH |
| XSS | <<Template escaping>> | **CSP + Content escaping** | HIGH |
| CSRF | <<None>> | **SameSite cookies + CSRF tokens** | HIGH |
| Secrets in Code | <<Hardcoded>> | **Secrets Manager (AWS/Azure/Vault)** | CRITICAL |

### Compliance Requirements

From legacy analysis (functional-spec.md §6):

- **GDPR**: PII encryption, right to erasure
- **SOX**: Audit logging, immutability
- **<<Other>>**: <<Requirements>>

**Target Implementation**:

- PII: Encrypt at rest (DB-level encryption)
- Audit: Immutable audit log table + event stream
- Access Controls: RBAC + audit trail

### Data Residency

**Legacy**: <<Single region>>
**Target**: <<USER_CHOICE_DEPLOYMENT region>> (configurable)

---

## 12. Migration / Expansion Paths

### P1: Minimum Viable Migration (Months 1-3)

**Approach**: Strangler Fig Pattern

1. **Week 1-2**: Setup infrastructure (<<USER_CHOICE_DEPLOYMENT>>)
2. **Week 3-4**: Deploy auth service (P1)
3. **Week 5-8**: Deploy core service + DB (P1)
4. **Week 9-10**: Dual-write data (legacy + new)
5. **Week 11-12**: Route <<10%>> traffic to new system (canary)

**Exit Criteria**:

- ✅ Core workflow functional
- ✅ Performance meets SLO
- ✅ Zero data loss in dual-write
- ✅ Rollback tested

### P2: Feature Parity (Months 4-6)

**Approach**: Incremental migration

1. **Month 4**: Migrate <<Feature Set 2>>
2. **Month 5**: Migrate integrations
3. **Month 6**: Route <<50%>> traffic to new

**Exit Criteria**:

- ✅ All features migrated
- ✅ Performance better than legacy
- ✅ User acceptance testing passed

### P3: Modernization Benefits (Months 7-9)

**Approach**: Leverage new capabilities

1. **Month 7**: Add <<new observability>>
2. **Month 8**: Optimize performance
3. **Month 9**: Route <<100%>> traffic

**Exit Criteria**:

- ✅ Legacy system decommissioned
- ✅ Observability dashboards live
- ✅ Cost savings achieved

### Data Migration Detailed Plan

| Phase | Data | Approach | Validation | Rollback |
|-------|------|----------|-----------|----------|
| P1 | <<Core entities>> | Dual-write | Reconciliation job | Stop new writes |
| P2 | <<All entities>> | Backfill historical | Data integrity checks | Restore from backup |
| P3 | <<Cleanup>> | Delete from legacy | Archive verification | Restore from archive |

---

## 13. Risks & Decisions (RAD)

### Top Risks (Prioritized)

| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| Data migration corruption | Medium | CRITICAL | Reconciliation + rollback plan | Data Team |
| Performance regression | Medium | HIGH | Load testing + canary rollout | Platform Team |
| Feature gap discovery | High | MEDIUM | Comprehensive functional spec review | Product |
| Team unfamiliarity with new stack | High | MEDIUM | Training + pair programming | Engineering |

### Decisions Required

**D-001**: Preserve legacy quirk <<X>>?

- **Options**: A) Preserve, B) Fix and migrate
- **Recommendation**: <<Based on analysis>>
- **Owner**: Product
- **Deadline**: Before P1 implementation

**D-002**: Migration strategy?

- **Options**: A) Big bang, B) Strangler fig, C) Hybrid
- **Recommendation**: Strangler fig (lower risk)
- **Owner**: Architecture
- **Deadline**: Before P1 start

---

## 14. R→C→T Traceability

Map Requirements (from functional-spec.md) → Components → Tests:

| Requirement ID | Requirement | Component | Test ID | Test Type |
|----------------|-------------|-----------|---------|-----------|
| FR-CRIT-001 | <<Feature name>> | <<Auth Service>> | T-001 | Unit + E2E |
| FR-CRIT-002 | <<Feature name>> | <<Core Service>> | T-002 | Integration |
| FR-STD-001 | <<Feature name>> | <<Integration Service>> | T-003 | E2E |

**Testing Strategy** (from Q10):

- **<<USER_CHOICE_TESTING>>**: <<e.g., Unit + Integration + E2E tests>>
- **Test Coverage Target**: <<85%>> (from legacy: <<current coverage>>%)
- **Test Frameworks**:
  - Unit: <<JUnit 5 / pytest / Jest>>
  - Integration: <<Testcontainers / pytest-docker>>
  - E2E: <<Playwright / Cypress / Selenium>>

---

## 15. Open Questions & Next Steps

### Open Questions

1. **Q-001**: <<Question needing user input>>
2. **Q-002**: <<Question needing user input>>

### Next Steps

1. **User Review**: Validate target architecture and tech stack
2. **Prototype**: Build P1 MVP spike to validate assumptions
3. **Cost Estimation**: Calculate infra costs for <<USER_CHOICE_DEPLOYMENT>>
4. **Team Training**: Plan upskilling for new stack
5. **Implementation**: Proceed with P1 based on this spec

---

## Appendix: LTS Version Sources

**Sources for LTS versions** (queried <<ANALYSIS_DATE>>):

- Java: [OpenJDK Roadmap](https://openjdk.org/projects/jdk/)
- PostgreSQL: [Versioning Policy](https://www.postgresql.org/support/versioning/)
- Kubernetes: [Release Schedule](https://kubernetes.io/releases/)
- <<Other>>: <<Source URLs>>

---

## END OF TECHNICAL SPECIFICATION

This document defines HOW to build the modernized system.
For WHAT the system does, see `functional-spec.md`.
For stage-specific guidance, see `stage-prompts/plan-prompt.md`.
