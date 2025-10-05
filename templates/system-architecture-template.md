# System Architecture

**Established By**: [First feature that created this, e.g., proj-1.messaging]
**Current Version**: [Semantic version, e.g., v1.2.0]
**Last Updated**: [DATE]

## Purpose

This document tracks the evolution of system-wide architecture decisions across all features. It is created by the FIRST `/plan` command (MVP) and updated by subsequent `/plan` commands as features extend or refactor the architecture.

## Core Architecture Decisions

### Application Structure
- **Pattern**: [Monolith | Microservices | Modular Monolith | Serverless]
- **Rationale**: [Why this choice - team size, complexity, scalability needs]
- **Established By**: [Feature that made this decision]

### Technology Stack

#### Language & Runtime
- **Primary Language**: [e.g., Python, Node.js, Go, Rust]
- **Version**: [e.g., Python 3.11+, Node 20+]
- **Rationale**: [Team expertise, ecosystem, performance requirements]

#### Data Layer
- **Primary Database**: [e.g., PostgreSQL, MongoDB, MySQL]
- **Version**: [e.g., PostgreSQL 15+]
- **Caching**: [e.g., Redis, Memcached, None]
- **Search**: [e.g., Elasticsearch, PostgreSQL full-text, None]
- **Rationale**: [Why these choices]

#### API & Communication
- **API Style**: [REST | GraphQL | gRPC | Hybrid]
- **Real-time**: [WebSocket | Server-Sent Events | Polling | None]
- **Message Queue**: [RabbitMQ | Kafka | Redis Pub/Sub | None]
- **Rationale**: [Why these choices]

#### Authentication & Authorization
- **Auth Method**: [JWT | OAuth 2.0 | Session-based | API Keys]
- **Identity Provider**: [Self-hosted | Auth0 | Cognito | Other]
- **Authorization**: [RBAC | ABAC | Custom]
- **Rationale**: [Why these choices]

### Infrastructure & Deployment

#### Container & Orchestration
- **Containerization**: [Docker | None]
- **Orchestration**: [Kubernetes | ECS | Docker Compose | None]
- **Rationale**: [Why these choices]

#### Cloud & Hosting
- **Cloud Provider**: [AWS | GCP | Azure | Self-hosted | Hybrid]
- **Regions**: [e.g., us-east-1, eu-west-1]
- **CDN**: [CloudFront | Cloudflare | None]
- **Object Storage**: [S3 | GCS | Azure Blob | None]
- **Rationale**: [Why these choices]

#### Monitoring & Observability
- **Logging**: [CloudWatch | Datadog | ELK Stack | Custom]
- **Metrics**: [Prometheus | CloudWatch | Datadog]
- **Tracing**: [Jaeger | X-Ray | None]
- **Alerting**: [PagerDuty | Opsgenie | CloudWatch Alarms]
- **Rationale**: [Why these choices]

---

## Architecture Evolution

*Each feature that impacts architecture adds an entry here with semantic versioning.*

### Versioning Rules
- **Patch (v1.0.0 → v1.0.1)**: Bug fixes, clarifications, no architectural impact
- **Minor (v1.0.0 → v1.1.0)**: Additive changes - new components, services, or integrations
- **Major (v1.0.0 → v2.0.0)**: Breaking changes - structural refactors, technology replacements

---

### v1.0.0 ([First Feature ID]) - Initial Architecture

**Type**: Foundation
**Date**: [DATE]
**Feature**: [First feature name and ID]

**Decisions Made**:
- Application structure: [e.g., Monolithic Node.js application]
- Database: [e.g., PostgreSQL for all persistence]
- API: [e.g., REST with JWT authentication]
- Deployment: [e.g., Docker containers on AWS ECS]

**Rationale**:
- [Why these foundational choices were made]
- [Team context, project constraints, business requirements]

**Components Established**:
- [Component 1]: [Purpose]
- [Component 2]: [Purpose]

**Impact**: Foundation for all subsequent features

**Documented In**: `specs/[feature-id]/plan.md`

---

### v1.1.0 ([Second Feature ID]) - [Change Description]

**Type**: Additive Extension
**Date**: [DATE]
**Feature**: [Feature name and ID]

**Changes**:
- + [New component/service added, e.g., "S3 for file storage"]
- + [New integration, e.g., "CloudFront CDN"]

**Rationale**:
- [Why this extension was needed]
- [Why existing architecture couldn't satisfy requirement]

**Components Added**:
- [Component name]: [Purpose and how it integrates]

**Impact**: Low - Additive only
- Existing features unaffected
- New capability available to future features

**Documented In**: `specs/[feature-id]/plan.md`

---

### v1.2.0 ([Third Feature ID]) - [Change Description]

**Type**: Additive Extension
**Date**: [DATE]
**Feature**: [Feature name and ID]

**Changes**:
- + [New component, e.g., "Redis for caching and ephemeral state"]
- + [New pattern, e.g., "Pub/sub for real-time events"]

**Rationale**:
- [Why this extension was needed]
- [Performance/scale/capability requirement]

**Components Added**:
- [Component name]: [Purpose]

**Refinements**:
- [Optional: Existing features enhanced to use new capability]

**Impact**: Low to Medium
- Additive, but recommended for existing features
- Performance improvement opportunity

**Documented In**: `specs/[feature-id]/plan.md`

---

### v2.0.0 ([Feature ID]) - [BREAKING: Change Description]

**Type**: BREAKING CHANGE - Architecture Refactor
**Date**: [DATE]
**Feature**: [Feature name and ID that triggered refactor]

**Breaking Changes**:
- [Structural change, e.g., "Split monolith into microservices"]
- [Technology replacement, e.g., "Migrate from PostgreSQL to distributed database"]
- [Deployment change, e.g., "Move from ECS to Kubernetes"]

**New Architecture**:
- [Describe new structure]
- [List new components/services]

**Rationale**:
- [Why refactor was necessary]
- [What requirement couldn't be met with existing architecture]
- [Business/technical drivers]

**Migration Required**:
- **Affected Features**: [List all features that need refactoring, e.g., "proj-1 through proj-9"]
- **Migration Plan**: [Link to migration documentation or describe approach]
- **Timeline**: [Expected migration duration]
- **Risk Assessment**: [Risks of migration, mitigation strategies]

**Impact**: HIGH
- All existing features require updates
- Coordinated migration effort needed
- Potential downtime or phased rollout

**Documented In**: `specs/[feature-id]/plan.md` + `docs/migrations/v2-migration.md`

---

## Architecture Constraints

*These constraints apply to ALL features unless explicitly justified and approved.*

### Database Constraints
- **PRIMARY RULE**: Use PostgreSQL for persistent data
- **Exception Process**: New database types require architecture review
- **Rationale**: Maintain operational simplicity, team expertise

### Authentication Constraints
- **PRIMARY RULE**: Use existing JWT authentication system
- **Exception Process**: New auth schemes require security review
- **Rationale**: Consistent security model, reduce attack surface

### API Constraints
- **PRIMARY RULE**: REST endpoints following existing conventions
- **Exception Process**: GraphQL/gRPC require specific use case justification
- **Rationale**: API consistency, client compatibility

### Deployment Constraints
- **PRIMARY RULE**: Deploy within existing Docker/container infrastructure
- **Exception Process**: New deployment models require operations review
- **Rationale**: Operational efficiency, monitoring consistency

### Language Constraints
- **PRIMARY RULE**: [Primary language] for backend services
- **Exception Process**: New languages require architecture review
- **Rationale**: Team expertise, operational consistency

---

## Extension Guidelines

### When to ADD Components (Minor Version Bump)

**Appropriate for**:
- New storage type for specific feature need (object storage, cache, queue)
- New external service integration (payment gateway, email service)
- New infrastructure component (CDN, load balancer)
- New monitoring/observability tool

**Process**:
1. Document need in feature's `plan.md`
2. Justify why existing components insufficient
3. Update this file with new version entry
4. Ensure operations team can support new component

**Example**: "Adding Redis for real-time presence tracking (v1.1.0 → v1.2.0)"

### When to REFINE Architecture (Minor Version Bump)

**Appropriate for**:
- Performance optimizations that don't change structure
- Adding caching/optimization layers
- Enhancing existing components
- Backward-compatible improvements

**Process**:
1. Document refinement in feature's `plan.md`
2. Note which existing features benefit from refinement
3. Update this file with refinement details
4. Optional: Update affected features to use refinement

**Example**: "Adding Redis caching layer, existing features can optionally adopt"

### When to REFACTOR Architecture (Major Version Bump)

**Appropriate for**:
- Changing application structure (monolith ↔ microservices)
- Replacing core technology (database migration, language change)
- Changing deployment model (cloud provider, serverless)
- Introducing distributed systems patterns

**Process**:
1. **Architecture Review Required**: Propose refactor with detailed rationale
2. **Impact Assessment**: Document all affected features and migration effort
3. **Migration Plan**: Create detailed migration document
4. **Stakeholder Approval**: Business and technical leadership sign-off
5. **Phased Rollout**: Plan for incremental migration or feature flag approach
6. **Update this file**: Major version bump with full documentation

**Example**: "Splitting monolith into microservices to support independent scaling (v1.x → v2.0.0)"

---

## Architecture Fitness Functions

*Automated checks to ensure architectural integrity*

### Structural Fitness
- [ ] Feature uses existing database (no new persistence without justification)
- [ ] Feature integrates with existing auth (no custom auth implementations)
- [ ] Feature follows API conventions from v1.0.0
- [ ] Feature deploys via existing container infrastructure

### Performance Fitness
- [ ] API response times within NFRs from product vision
- [ ] Database queries optimized (no N+1 queries, proper indexing)
- [ ] Caching used appropriately (leverages Redis if available)

### Security Fitness
- [ ] Authentication follows established pattern
- [ ] Authorization checks present for all protected resources
- [ ] PII encryption at rest and in transit
- [ ] Security headers configured

### Operational Fitness
- [ ] Logging follows established patterns
- [ ] Metrics exposed for monitoring
- [ ] Health checks implemented
- [ ] Error handling consistent with system patterns

### Quality Fitness
- [ ] Tests exist (unit, integration, contract)
- [ ] Documentation updated
- [ ] No direct database access from UI (proper API layer)
- [ ] Dependencies declared and version-pinned

---

## Architecture Decision Records (ADRs)

*For significant architectural decisions, maintain lightweight ADRs*

### ADR Template
```markdown
### ADR-[Number]: [Decision Title]

**Status**: [Proposed | Accepted | Deprecated | Superseded]
**Date**: [DATE]
**Context**: [What is the issue we're seeing that is motivating this decision?]
**Decision**: [What is the change that we're proposing/making?]
**Consequences**: [What becomes easier or more difficult as a result?]
```

### Example ADRs

#### ADR-001: Use PostgreSQL as Primary Database

**Status**: Accepted
**Date**: 2025-01-15
**Context**: Need to choose database for initial product launch
**Decision**: Use PostgreSQL for all persistent data storage
**Consequences**:
- Positive: Relational model fits our data, strong ACID guarantees, team expertise
- Negative: May need additional tools for specific use cases (caching, full-text search)

---

## Review & Maintenance

### Review Triggers
This document should be reviewed when:
- [ ] Any feature proposes architecture changes (during `/plan`)
- [ ] Quarterly architecture health review
- [ ] Performance issues traced to architectural limitations
- [ ] Major technology/framework upgrades planned

### Ownership
- **Architecture Owner**: [Role/person responsible for architectural consistency]
- **Review Committee**: [Who approves major architecture changes]

### Version History
*Track major milestones*
- v1.0.0: Initial architecture established
- v1.1.0: Added [component]
- v2.0.0: Refactored to [new pattern]

---

## References

### Internal Documentation
- Product Vision: `docs/product-vision.md`
- Feature Plans: `specs/*/plan.md`
- Migration Plans: `docs/migrations/`

### External Documentation
- [Technology documentation links]
- [Architecture pattern references]
- [Cloud provider best practices]
