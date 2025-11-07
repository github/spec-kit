# Service Catalog Command

You are generating a comprehensive service catalog for a microservices architecture.

## Purpose

This command creates a navigable catalog of all microservices in the system, showing:
- Service boundaries and responsibilities
- API contracts and event schemas
- Dependencies between services
- Health and operational status
- Quick navigation to detailed specs

## Discovery Process

### 1. Locate All Services

Search for services in these patterns:
- `services/*/specs/` (dedicated services folder)
- `specs/*-service/` (service-named specs)
- Any spec folder containing `service-spec.md` or similar indicators

### 2. Extract Service Metadata

For each service, extract:
- **Service Name:** From directory name or spec title
- **Service Type:** API/Event Processor/BFF/Gateway/Worker
- **Bounded Context:** Core domain responsibility
- **API Endpoints:** List from contracts/api-spec.*
- **Events Published:** From contracts/events/ or service-spec.md
- **Events Consumed:** From service-spec.md dependencies section
- **Upstream Dependencies:** Services this service calls
- **Downstream Dependents:** Services that call this service
- **Data Entities Owned:** Primary data responsibility

## Catalog Output Format

```markdown
# Microservices Catalog

**Last Updated:** [timestamp]
**Total Services:** [N]
**Total API Endpoints:** [N]
**Total Events:** [N]

---

## Quick Navigation

- [Service List](#service-list)
- [Dependency Graph](#dependency-graph)
- [Event Flow](#event-flow)
- [API Endpoints](#api-endpoints-by-domain)
- [Data Ownership](#data-ownership-map)

---

## Service List

### 1. [Service Name] {#service-1}

**Type:** [API Service / Event Processor / BFF / Gateway / Worker]
**Status:** [Active / Deprecated / In Development]
**Bounded Context:** [One-line description of responsibility]

**API Endpoints:**
- `GET /api/v1/resource` - Description
- `POST /api/v1/resource` - Description

**Events Published:**
- `domain.entity.created` - When entity is created
- `domain.entity.updated` - When entity is updated

**Events Consumed:**
- `other-domain.entity.changed` (from other-service) - Purpose

**Dependencies:**
- ↑ [upstream-service-1](#service-x) - For [purpose]
- ↑ [upstream-service-2](#service-y) - For [purpose]

**Dependents:**
- ↓ [downstream-service-1](#service-z) - Uses [endpoint/event]

**Data Ownership:**
- `Entity1` - Source of truth
- `Entity2` - Source of truth

**Quick Refs:**
- [Full Spec](services/service-name/specs/001-feature/spec.md)
- [API Contract](services/service-name/contracts/api-spec.yaml)
- [Quick Ref](services/service-name/specs/001-feature/quick-ref.md)

---

## Dependency Graph

### Visual Representation

```
┌─────────────────┐
│   api-gateway   │ (Entry point)
└────────┬────────┘
         │
    ┌────┴────┬────────────┬──────────┐
    │         │            │          │
┌───▼────┐ ┌─▼────────┐ ┌─▼──────┐ ┌─▼────────┐
│  auth  │ │   user   │ │ order  │ │ product  │
└───┬────┘ └─────┬────┘ └───┬────┘ └────┬─────┘
    │            │           │           │
    │      ┌─────┴───────────┴───────────┘
    │      │
┌───▼──────▼──┐
│  database   │
└─────────────┘

Event Flow:
order-service → [order.created] → notification-service
user-service  → [user.updated] → cache-service
```

### Dependency Matrix

| Service ↓ / Depends On → | api-gateway | auth | user | order | product |
|---------------------------|-------------|------|------|-------|---------|
| api-gateway               | -           | ✓    | ✓    | ✓     | ✓       |
| auth                      | -           | -    | ✓    | -     | -       |
| user                      | -           | ✓    | -    | -     | -       |
| order                     | -           | ✓    | ✓    | -     | ✓       |
| product                   | -           | ✓    | -    | -     | -       |

**Legend:**
- ✓ = Direct dependency (sync API calls)
- ⚡ = Async dependency (event consumption)
- ⚠️ = Circular dependency (needs review)

---

## Event Flow

### Event Publishers

| Event Name | Publisher | Trigger | Consumers |
|------------|-----------|---------|-----------|
| `auth.token.issued` | auth-service | JWT generated | [audit-service] |
| `user.created` | user-service | New user registered | [notification-service, analytics] |
| `user.updated` | user-service | User profile changed | [cache-service] |
| `order.created` | order-service | Order placed | [inventory, notification, analytics] |
| `order.completed` | order-service | Order fulfilled | [billing, notification] |
| `product.updated` | product-service | Catalog changed | [cache-service, search-service] |

### Event Consumers

| Service | Consumes Events | Purpose |
|---------|-----------------|---------|
| notification-service | order.created, user.created | Send emails/SMS |
| analytics-service | *.* (all events) | Business intelligence |
| cache-service | user.updated, product.updated | Invalidate cache |
| inventory-service | order.created | Reserve stock |

---

## API Endpoints by Domain

### Authentication Domain

| Endpoint | Method | Service | Purpose |
|----------|--------|---------|---------|
| `/api/v1/auth/login` | POST | auth-service | User login |
| `/api/v1/auth/refresh` | POST | auth-service | Refresh token |
| `/api/v1/auth/validate` | POST | auth-service | Validate token |

### User Domain

| Endpoint | Method | Service | Purpose |
|----------|--------|---------|---------|
| `/api/v1/users` | GET | user-service | List users |
| `/api/v1/users/{id}` | GET | user-service | Get user details |
| `/api/v1/users/{id}` | PUT | user-service | Update user |
| `/api/v1/users/{id}/avatar` | POST | user-service | Upload avatar |

### Order Domain

| Endpoint | Method | Service | Purpose |
|----------|--------|---------|---------|
| `/api/v1/orders` | GET | order-service | List user's orders |
| `/api/v1/orders` | POST | order-service | Create order |
| `/api/v1/orders/{id}` | GET | order-service | Get order details |
| `/api/v1/orders/{id}/cancel` | POST | order-service | Cancel order |

---

## Data Ownership Map

| Entity | Owner Service | Replicated To | Purpose of Replica |
|--------|---------------|---------------|-------------------|
| User | user-service | order-service | Denormalized for order display |
| User | user-service | cache-service | Performance |
| Order | order-service | - | (No replication) |
| Product | product-service | order-service | Snapshot at order time |
| Product | product-service | search-service | Full-text search |

**Ownership Rules:**
- ✅ Only owner service can write to entity
- ✅ Other services can cache/replicate read-only
- ✅ Replicas updated via events or scheduled sync
- ❌ Never write to replicated data

---

## Service Health Overview

| Service | Status | Uptime SLA | Last Deploy | Version |
|---------|--------|------------|-------------|---------|
| api-gateway | 🟢 Healthy | 99.9% | 2 days ago | v2.3.1 |
| auth-service | 🟢 Healthy | 99.95% | 1 week ago | v1.5.0 |
| user-service | 🟡 Degraded | 99.9% | 3 days ago | v2.1.4 |
| order-service | 🟢 Healthy | 99.9% | 1 day ago | v3.0.2 |
| product-service | 🟢 Healthy | 99.5% | 2 weeks ago | v1.8.1 |

**Legend:**
- 🟢 Healthy: All checks passing
- 🟡 Degraded: Some checks failing, still operational
- 🔴 Down: Service unavailable
- 🔵 Maintenance: Planned downtime

---

## Architecture Patterns

### Communication Patterns Used
- **Synchronous:** REST APIs via HTTP/HTTPS
- **Asynchronous:** Event-driven via [RabbitMQ/Kafka/SNS/SQS]
- **API Gateway:** Centralized routing and auth
- **Service Mesh:** [Istio/Linkerd/Consul] for traffic management

### Data Patterns
- **Database per Service:** Each service owns its database
- **Event Sourcing:** [Which services use it]
- **CQRS:** [Which services use it]
- **Saga Pattern:** For distributed transactions (order-service)

### Resilience Patterns
- **Circuit Breaker:** All external calls
- **Retry with Backoff:** 3 retries, exponential backoff
- **Bulkhead:** Resource isolation per dependency
- **Timeout:** 5s default, 30s for batch operations

---

## Finding Information

### I need to know...

**"What APIs does service X expose?"**
→ Jump to [service in catalog](#service-list), see API Endpoints section

**"Who consumes this event?"**
→ Check [Event Flow](#event-flow) table

**"What services depend on service X?"**
→ See "Dependents" in [service catalog entry](#service-list)

**"Who owns the User entity?"**
→ Check [Data Ownership Map](#data-ownership-map)

**"Are there any circular dependencies?"**
→ Review [Dependency Matrix](#dependency-graph)

**"What's the full spec for a service?"**
→ Click "Full Spec" link in catalog entry

---

## Maintenance

**This catalog is auto-generated from:**
- Service specs in `services/*/specs/`
- Contract files in `contracts/`
- Service-spec.md files

**To update:**
```bash
/speckit.service-catalog --regenerate
```

**Last generated:** [timestamp]
```

## Instructions for AI Agent

When `/speckit.service-catalog` is invoked:

1. **Discovery Phase**
   - Find all service specs (service-spec.md or spec.md with service indicators)
   - Load all contract files (OpenAPI, event schemas)
   - Parse dependency relationships from specs

2. **Analysis Phase**
   - Build dependency graph
   - Detect circular dependencies (warn if found)
   - Map event publishers to consumers
   - Identify data ownership

3. **Generation Phase**
   - Generate the catalog in the format above
   - Create visual dependency graph (ASCII art or Mermaid diagram)
   - Build cross-reference links
   - Add navigation anchors

4. **Output**
   - Write to `docs/SERVICE-CATALOG.md`
   - Create quick index at `docs/services-index.md` (lightweight version)
   - Update `.speckit/cache/catalog-metadata.json` for fast lookups

5. **Validation**
   - Warn about missing contracts
   - Warn about undocumented dependencies
   - Flag potential issues (circular deps, orphaned services)

## Command Variants

```bash
# Generate full catalog
/speckit.service-catalog

# Generate only for specific domain
/speckit.service-catalog --domain=orders

# Show only dependency graph
/speckit.service-catalog --graph-only

# Export as JSON for tooling
/speckit.service-catalog --format=json

# Interactive navigation mode
/speckit.service-catalog --interactive
```

## Integration with Other Commands

- Use `/speckit.find` to locate services by capability
- Use `/speckit.validate-contracts` to ensure catalog is accurate
- Use quick-ref.md files for fast service lookups (lower token cost)
- Link from service catalog entries to full specs

This catalog becomes the "map" of your microservices architecture, making it easy to navigate, understand dependencies, and maintain the system.
