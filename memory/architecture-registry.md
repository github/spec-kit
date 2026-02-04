# Architecture Registry

> **Purpose**: This registry captures **high-level architectural patterns** and **technology decisions** that apply across all features. It serves as the source of truth for architectural consistency.
>
> **Scope**: Architectural patterns, interface contracts between modules, major technology decisions.
> For module-specific conventions (naming, file organization, code patterns), see `{module}/CLAUDE.md` files.
> For specification rules, see `/memory/constitution.md`.

**CRITICAL**: Before planning ANY new feature, load this registry and verify alignment.
New features MUST follow established patterns unless explicitly diverging with documented justification.

## How This Registry Works

1. **During Planning** (`/speckit.plan`): Load this registry and verify new design aligns
2. **During Implementation** (`/speckit.implement`): Module-specific CLAUDE.md files are auto-loaded by Claude Code
3. **After Merge** (`/speckit.merge` + `/speckit.learn`): Update registry with new patterns, update module CLAUDE.md files
4. **Quality Gate** (`/speckit.checklist`): Validates plan alignment with registry patterns

---

## Architectural Patterns

> High-level patterns that define how the system is structured. For implementation details, see module CLAUDE.md files.

| Pattern | Description | Modules Using | Key Interfaces |
|---------|-------------|---------------|----------------|
| [PATTERN_NAME] | [what problem it solves] | [which modules] | [main interfaces/contracts] |

<!--
Example entries:
| Repository Pattern | Abstracts data access from business logic | backend, api | IRepository<T> interface |
| Service Layer | Encapsulates business logic | backend | *Service classes |
| Event-Driven | Decouples components via events | backend, frontend | EventBus, IEvent |
| Clean Architecture | Dependency rule: outer depends on inner | all | UseCases, Entities |
-->

---

## Technology Stack

> Major technology decisions that affect multiple modules. Version-specific details belong in module CLAUDE.md files.

| Category | Technology | Rationale | Alternatives Rejected |
|----------|------------|-----------|----------------------|
| [category] | [what to use] | [why] | [what NOT to use] |

<!--
Example entries:
| Framework | Next.js | SSR + App Router, React ecosystem | Remix (less mature), Nuxt (Vue) |
| Validation | Zod | Type inference + runtime validation | Yup (no inference), Joi (Node-only) |
| Database | PostgreSQL | Relational integrity, JSON support | MongoDB (no relations), MySQL (less features) |
| ORM | Prisma | Type-safe, migrations | TypeORM (verbose), Drizzle (newer) |
-->

---

## Module Contracts

> Interface contracts between modules. These are the "handshake agreements" that modules must respect.

### [Module A] ↔ [Module B]

**Communication**: [REST API / Events / Shared Types]

**Contract Location**: `[file path]`

**Key Interfaces**:
```typescript
// Example interface definition
interface IContract {
  method(param: Type): ReturnType;
}
```

<!--
Example:
### Frontend ↔ Backend API

**Communication**: REST API over HTTPS

**Contract Location**: `docs/api/` or `specs/{feature}/contracts/`

**Key Interfaces**:
- Authentication: POST /auth/login, POST /auth/logout
- Users: GET /users/:id, PUT /users/:id
- All responses follow: { data: T, error?: { code, message } }
-->

---

## Cross-Module Dependencies

> Shared components that multiple modules depend on.

| Component | Owner Module | Used By | Stability |
|-----------|--------------|---------|-----------|
| [component] | [module] | [list of modules] | Stable / Evolving |

<!--
Example entries:
| AuthService | backend | frontend, api, workers | Stable |
| shared-types | shared | all | Stable |
| EventBus | backend | api, workers | Evolving |
-->

---

## Architectural Anti-Patterns

> Approaches that were tried and MUST be avoided at the architectural level.

| Anti-Pattern | Issue | Correct Approach |
|--------------|-------|------------------|
| [what to avoid] | [why it's problematic] | [what to do instead] |

<!--
Example entries:
| Direct DB access from routes | Tight coupling, untestable | Use repository/service layer |
| Shared mutable state | Race conditions, unpredictable | Use immutable patterns or proper state management |
| Circular dependencies | Build failures, complexity | Dependency injection, event-driven |
-->

---

## Architectural Decisions Log

> Key architectural decisions with context. For detailed ADRs, see `docs/adr/` if available.

### ADR-001: [Decision Title]

- **Date**: [YYYY-MM-DD]
- **Status**: Accepted / Superseded by ADR-XXX
- **Context**: [Why was this decision needed?]
- **Decision**: [What was decided?]
- **Consequences**: [What are the implications?]

---

## Registry Maintenance

### When to Update This Registry

Update this registry when:
- A new **architectural pattern** is established (not just code conventions)
- A **technology decision** affects multiple modules
- A new **module contract** is defined
- An **anti-pattern** is discovered at the architectural level

### What Does NOT Belong Here

These belong in `{module}/CLAUDE.md` instead:
- File naming conventions
- Code formatting rules
- Module-specific patterns (React hooks, service class structure)
- Testing conventions for specific modules
- Error handling details

### Update Process

1. Run `/speckit.learn` after `/speckit.merge`
2. Review proposed changes
3. Keep only high-level patterns in this file
4. Module-specific details go to respective CLAUDE.md files

---

**Version**: 2.0.0 | **Last Updated**: [DATE]
