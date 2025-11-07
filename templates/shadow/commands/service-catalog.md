---
description: Generate service catalog for microservices architecture
---

# Service Catalog

Generate a comprehensive catalog of services in a microservices architecture.

## Usage

```bash
{SHADOW_PATH}/scripts/bash/project-catalog{SCRIPT_EXT} --services
```

## What Gets Cataloged

### Service Inventory
- Service name and purpose
- Service ownership
- Technology stack
- Deployment locations

### Service APIs
- Endpoints exposed
- API versioning
- Authentication method
- Rate limits

### Service Dependencies
- Upstream services
- Downstream consumers
- Database dependencies
- External APIs

### Service Characteristics
- Scalability profile
- Availability requirements
- Data sensitivity
- Monitoring and alerts

## Catalog Structure

```
.catalog/services/
├── overview.md           # Service map
├── <service-name>.md     # Per-service details
├── dependencies.md       # Dependency graph
└── contracts.md          # API contracts
```

## Per-Service Documentation

Each service includes:
- **Purpose** - What it does
- **APIs** - Endpoints exposed
- **Dependencies** - What it needs
- **Consumers** - Who uses it
- **SLAs** - Performance targets
- **Contacts** - Ownership info

## Dependency Graph

Visual representation of:
- Service-to-service calls
- Database connections
- External integrations
- Message queues

## Use Cases

### Service Discovery
Find services by capability

### Impact Analysis
Assess change impact across services

### Onboarding
Help developers understand system

### Architecture Reviews
Visualize system structure

## Best Practices

- Update after service changes
- Document API contracts
- Include deployment info
- Track service health
- Maintain ownership

## Service Contract

For each API:
- Request/response formats
- Error codes
- Authentication
- Rate limits
- Versioning strategy
