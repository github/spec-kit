---
description: Generate comprehensive project catalog
---

# Project Catalog

Generate a comprehensive catalog of project components, services, and APIs.

## Usage

```bash
{SHADOW_PATH}/scripts/bash/project-catalog{SCRIPT_EXT}
```

## What Gets Cataloged

### Components
- Libraries and modules
- Services and microservices
- Shared utilities
- Third-party integrations

### APIs
- REST endpoints
- GraphQL schemas
- WebSocket connections
- Internal APIs

### Data Models
- Database schemas
- Entity relationships
- Data flows
- Cache layers

### Infrastructure
- Deployment environments
- CI/CD pipelines
- Monitoring and logging
- External services

## Catalog Structure

```
.catalog/
├── components.md     # Component inventory
├── apis.md           # API catalog
├── data-models.md    # Data model documentation
├── infrastructure.md # Infrastructure overview
└── dependencies.md   # Dependency graph
```

## Use Cases

### Architecture Reviews
Understand system composition

### Impact Analysis
Assess change impact

### Documentation
Maintain system documentation

### Onboarding
Help new team members understand system

## Catalog Contents

For each component:
- Purpose and responsibility
- Dependencies (upstream and downstream)
- APIs exposed
- Configuration
- Owners and contacts

## Best Practices

- Update catalog after changes
- Review in architecture meetings
- Use for impact analysis
- Keep dependencies current
- Document service contracts

## Benefits

- Single source of truth
- Clear ownership
- Dependency visibility
- Change impact analysis
- Architecture documentation
