---
name: architecture-patterns
description: |
  Apply proven backend architecture patterns including Clean Architecture, Hexagonal Architecture, and Domain-Driven Design for building maintainable, testable, and scalable systems.
  Use when: designing new systems, refactoring monoliths, establishing team standards, planning microservices decomposition.
triggers: ["architecture", "clean architecture", "hexagonal", "DDD", "domain-driven", "layered architecture", "ports and adapters"]
---

# Architecture Patterns

> Build maintainable, testable, and scalable systems with proven architectural patterns.

## Core Principles

- **Dependencies point inward**: Business logic never depends on frameworks
- **Dependency Inversion**: High-level modules don't depend on low-level modules
- **Interface Segregation**: Many specific interfaces over one general interface
- **Separation of Concerns**: Each layer has a single responsibility
- **Testability**: Business logic testable without infrastructure

## Pattern Comparison

| Pattern | Core Idea | Best For |
|---------|-----------|----------|
| Clean Architecture | Concentric layers, deps point inward | Complex business logic |
| Hexagonal (Ports & Adapters) | Core + Ports + Adapters | Multiple integrations |
| Domain-Driven Design | Bounded contexts, rich domain | Complex domains |
| Layered | Horizontal layers | Simple CRUD apps |

## Clean Architecture (Uncle Bob)

```
┌─────────────────────────────────────────────────────────┐
│                 Frameworks & Drivers                     │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Interface Adapters                  │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │            Use Cases                     │    │    │
│  │  │  ┌─────────────────────────────────┐    │    │    │
│  │  │  │          Entities               │    │    │    │
│  │  │  │      (Business Rules)           │    │    │    │
│  │  │  └─────────────────────────────────┘    │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                    ← Dependencies point inward
```

**Layers:**
- **Entities**: Core business objects and rules
- **Use Cases**: Application-specific business rules
- **Interface Adapters**: Controllers, presenters, gateways
- **Frameworks**: Web, DB, external services

## Hexagonal Architecture

```
                    ┌─────────────┐
         ┌─────────│  REST API   │──────────┐
         │         └─────────────┘          │
         ▼                                  ▼
    ┌─────────┐                        ┌─────────┐
    │  Port   │◄───────────────────────│  Port   │
    │   In    │                        │   Out   │
    └────┬────┘                        └────┬────┘
         │         ┌───────────┐            │
         └────────►│   Domain  │◄───────────┘
                   │   Core    │
         ┌────────►│           │◄───────────┐
         │         └───────────┘            │
    ┌────┴────┐                        ┌────┴────┐
    │ Adapter │                        │ Adapter │
    │   CLI   │                        │   DB    │
    └─────────┘                        └─────────┘
```

## Quick Decision Guide

- **Simple CRUD**: Layered architecture
- **Complex business logic**: Clean Architecture
- **Multiple integrations**: Hexagonal
- **Large teams, complex domain**: DDD with bounded contexts
- **Microservices**: Combine DDD + Hexagonal per service

## Critical Don'ts

- Never let domain depend on infrastructure
- Avoid anemic domain models (data without behavior)
- Don't expose ORM entities through APIs
- Never put business logic in controllers
- Avoid framework coupling in core logic

## When to Load References

- For implementation examples: `Read references/implementations.md`
- For DDD patterns: `Read references/ddd-patterns.md`

## External Resources

- [Clean Architecture (Uncle Bob)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
