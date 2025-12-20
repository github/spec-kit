---
name: microservices-patterns
description: |
  Design microservices architectures with service boundaries, event-driven communication, and resilience patterns.
  Use when: building distributed systems, decomposing monoliths, implementing microservices, designing service boundaries.
triggers: ["microservices", "distributed system", "service mesh", "event-driven", "saga pattern", "circuit breaker"]
---

# Microservices Patterns

> Design distributed systems with proper service boundaries, communication patterns, and resilience.

## Core Principles

- **Single Responsibility**: Each service owns one business capability
- **Data Autonomy**: Each service owns its data, no shared databases
- **Loose Coupling**: Services communicate through well-defined contracts
- **Failure Isolation**: One service failure shouldn't cascade
- **Independent Deployment**: Services deploy independently

## Quick Reference

| Pattern | Purpose | When to Use |
|---------|---------|-------------|
| API Gateway | Single entry point | Multiple clients, aggregation needed |
| Circuit Breaker | Prevent cascade failures | Remote service calls |
| Saga | Distributed transactions | Multi-service business process |
| Event Sourcing | Audit trail, replay | Complex state transitions |
| CQRS | Read/write optimization | High-read or complex queries |

## Service Decomposition

**By Business Capability:**
```
├── OrderService       # Order lifecycle
├── PaymentService     # Payment processing
├── InventoryService   # Stock management
├── ShippingService    # Delivery tracking
└── NotificationService # Alerts and emails
```

**By Bounded Context (DDD):**
- Identify ubiquitous language per context
- Define context boundaries
- Map relationships between contexts

## Communication Patterns

| Style | When to Use | Examples |
|-------|-------------|----------|
| Synchronous (REST/gRPC) | Real-time response needed | User queries, validation |
| Async Events (Kafka) | Fire-and-forget, broadcast | Order placed, payment received |
| Async Request-Reply | Long operations | Report generation, batch processing |

## Critical Don'ts

- Never share databases between services
- Don't create distributed monoliths (tightly coupled services)
- Avoid synchronous chains (A→B→C→D)
- Don't skip compensating transactions in sagas
- Don't adopt microservices before team is ready

## When to Load References

- For resilience patterns: `Read references/resilience-patterns.md`
- For data patterns: `Read references/data-patterns.md`

## External Resources

- [Microservices.io Patterns](https://microservices.io/patterns/)
- [Microsoft Azure Patterns](https://learn.microsoft.com/en-us/azure/architecture/microservices/design/patterns)
