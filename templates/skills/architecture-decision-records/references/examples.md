# ADR Examples

> Real-world examples of well-written ADRs.

## Example 1: Database Selection

```markdown
# ADR-0002: Use PostgreSQL for Primary Data Store

## Status

Accepted

Date: 2024-01-20
Deciders: Engineering Team, CTO

## Context and Problem Statement

We need to select a primary database for our new e-commerce platform. The system needs to handle:
- 100k daily active users
- Complex product queries with filtering
- Transaction processing for orders
- Full-text search for products

## Decision Drivers

* ACID compliance required for financial transactions
* Complex query support (joins, aggregations)
* Team has 3 years of PostgreSQL experience
* Need JSON support for flexible product attributes
* Cost-effective for startup budget

## Considered Options

1. PostgreSQL
2. MongoDB
3. MySQL
4. Amazon DynamoDB

## Decision Outcome

Chosen option: "PostgreSQL", because it provides the best balance of ACID compliance, query flexibility, and team expertise.

### Positive Consequences

* ACID transactions ensure order integrity
* JSONB columns handle flexible product attributes
* Full-text search with tsvector (no separate search service initially)
* Extensive tooling and community support
* Team can be productive immediately

### Negative Consequences

* Vertical scaling limits (mitigated by read replicas)
* Need to manage our own database (mitigated by using managed service)
* Less flexible schema evolution than MongoDB

## Pros and Cons of the Options

### PostgreSQL

* Good, because ACID compliant
* Good, because excellent JSON support
* Good, because team expertise
* Good, because mature ecosystem
* Bad, because requires more schema planning
* Bad, because complex sharding

### MongoDB

* Good, because flexible schema
* Good, because horizontal scaling
* Bad, because eventual consistency for transactions
* Bad, because team has no experience

### MySQL

* Good, because familiar to team
* Bad, because weaker JSON support
* Bad, because fewer advanced features

### DynamoDB

* Good, because fully managed
* Good, because infinite scale
* Bad, because vendor lock-in
* Bad, because limited query patterns
* Bad, because significantly higher cost at our scale

## Links

* [PostgreSQL vs MongoDB Comparison](internal-doc-link)
* [Database Capacity Planning](internal-doc-link)
```

## Example 2: API Design

```markdown
# ADR-0005: Use GraphQL for Mobile API

## Status

Accepted

Date: 2024-02-15

## Context

Our mobile app requires flexible data fetching across multiple resources. Current REST API issues:
- Over-fetching: endpoints return more data than needed
- Under-fetching: multiple requests needed for one screen
- Versioning challenges with different mobile versions

## Decision

We will use GraphQL for the mobile API gateway, keeping REST for internal microservice communication.

## Rationale

* **Reduced bandwidth**: Mobile clients fetch exactly what they need
* **Single endpoint**: Simpler caching and monitoring
* **Strong typing**: Schema serves as contract and documentation
* **Tooling**: Apollo Client handles caching, optimistic updates
* **Backwards compatible**: Add fields without versioning

## Consequences

### Positive
* Mobile team can iterate faster without backend changes
* Bandwidth usage reduced by estimated 40%
* Self-documenting API via schema introspection

### Negative
* Learning curve for backend team
* Need to implement proper query complexity limits
* Additional caching layer needed (Apollo Server caching)
* Two API paradigms to maintain

## Implementation Notes

* Use Apollo Server as GraphQL gateway
* Implement DataLoader for N+1 prevention
* Set query depth limit to 5
* Set complexity limit to 1000 points
```

## Example 3: Architecture Pattern

```markdown
# ADR-0008: Adopt Event Sourcing for Order Domain

## Status

Proposed

Date: 2024-03-01
Deciders: Architecture Review Board

## Context and Problem Statement

Order processing requires:
- Complete audit trail for compliance
- Ability to replay events for debugging
- Support for complex order state machines
- Integration with multiple downstream systems

Current CRUD-based approach lacks audit trail and makes debugging difficult.

## Decision Drivers

* Regulatory requirement for complete order history
* Support team needs to understand order state transitions
* Multiple systems need to react to order events
* Need to handle compensation for failed multi-step processes

## Considered Options

1. Event Sourcing with CQRS
2. Traditional CRUD with audit log table
3. CDC (Change Data Capture) from database

## Decision Outcome

Chosen option: "Event Sourcing with CQRS" for the Order bounded context only.

### Scope

Apply event sourcing ONLY to:
- Order aggregate
- Payment aggregate

Keep CRUD for:
- Product catalog
- User management
- Inventory (with eventual migration)

### Positive Consequences

* Complete, immutable audit trail
* Temporal queries ("what was order state at time X")
* Natural integration via events
* Better debugging and support experience
* Easy replay for testing

### Negative Consequences

* Steeper learning curve
* Additional infrastructure (event store, projections)
* Eventually consistent read models
* More complex local development setup

## Implementation Plan

### Phase 1: Infrastructure (2 weeks)
- Set up EventStoreDB
- Create projection framework
- Establish event schema conventions

### Phase 2: Order Aggregate (4 weeks)
- Migrate Order to event sourcing
- Create read model projections
- Update API layer

### Phase 3: Payment Aggregate (3 weeks)
- Migrate Payment to event sourcing
- Integrate with Order events

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Team unfamiliar with ES | High | Medium | Training, pair programming |
| Performance issues | Medium | High | Load testing, proper indexing |
| Operational complexity | Medium | Medium | Runbooks, monitoring |
```

## Example 4: Technology Deprecation

```markdown
# ADR-0012: Deprecate Legacy Authentication System

## Status

Accepted

Date: 2024-04-01
Deprecates: Custom auth implementation
Superseded by: ADR-0013 (Adopt Auth0)

## Context

Our custom authentication system:
- Has known security vulnerabilities
- Lacks MFA support
- Requires significant maintenance
- Doesn't support modern OAuth flows

## Decision

Deprecate the custom authentication system and migrate to Auth0.

## Migration Path

1. **Parallel Running** (Month 1-2)
   - Deploy Auth0 alongside existing system
   - New users created in Auth0
   - Existing users can use either

2. **Migration Wave 1** (Month 3)
   - Migrate power users (staff, VIP customers)
   - Monitor and fix issues

3. **Migration Wave 2** (Month 4-5)
   - Migrate all remaining users
   - Email campaigns with reset links

4. **Deprecation** (Month 6)
   - Disable old login
   - Keep read-only for 3 months
   - Delete after retention period

## Timeline

| Milestone | Date |
|-----------|------|
| Auth0 in production | 2024-04-15 |
| New user migration | 2024-05-01 |
| Wave 1 complete | 2024-06-01 |
| Wave 2 complete | 2024-08-01 |
| Old system disabled | 2024-09-01 |
| Data deletion | 2024-12-01 |

## Rollback Plan

If critical issues arise:
1. Re-enable old login endpoint
2. Pause migration
3. Users can continue with old credentials
4. Fix issues before resuming
```

## Writing Tips

1. **Be specific**: "Improves performance" → "Reduces p99 latency from 500ms to 100ms"
2. **Acknowledge trade-offs**: Every decision has downsides, document them
3. **Link related decisions**: ADRs form a connected history
4. **Include dates**: Context changes over time
5. **Name deciders**: Accountability and future questions
6. **Keep it short**: One decision per ADR, one page maximum
