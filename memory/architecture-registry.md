# Architecture Registry

This registry captures **architectural decisions** that MUST be followed across all features. It serves as the source of truth for consistency.

> **CRITICAL**: Before planning ANY new feature, load this registry and verify alignment.
> New features MUST follow established patterns unless explicitly diverging with documented justification.

## How This Registry Works

1. **During Planning** (`/speckit.plan`): Load this registry and verify new design aligns
2. **During Implementation** (`/speckit.implement`): Follow patterns from registry, update after completion
3. **Retrospective** (`/speckit.extract-patterns`): Extract patterns from existing features into this registry

---

## Established Patterns

> Patterns that have been implemented and MUST be reused in similar contexts.

| Pattern | First Used In | Files/Locations | When to Use | Example |
|---------|---------------|-----------------|-------------|---------|
| [PATTERN_NAME] | [feature-id] | [file paths] | [context/trigger] | [code reference] |

<!--
Example entries:
| Repository Pattern | 001-user-auth | src/repositories/*.ts | Data access for any entity | src/repositories/userRepository.ts |
| Service Layer | 001-user-auth | src/services/*.ts | Business logic encapsulation | src/services/authService.ts |
| Zod Validation | 002-forms | src/schemas/*.ts | Input validation with types | src/schemas/userSchema.ts |
| Error Boundary | 003-dashboard | src/components/ErrorBoundary.tsx | Component error handling | See file |
-->

---

## Technology Decisions

> Technology choices that MUST be used consistently across features.

| Category | Decision | Made In | Rationale | Alternatives Rejected |
|----------|----------|---------|-----------|----------------------|
| [category] | [what to use] | [feature-id] | [why] | [what NOT to use] |

<!--
Example entries:
| Validation | Zod | 002-forms | Type inference + runtime validation | Yup (no inference), Joi (Node-only) |
| Data Fetching | TanStack Query | 003-dashboard | Caching, devtools, suspense | SWR (less features), fetch (manual caching) |
| State Management | Zustand | 004-settings | Simple API, no boilerplate | Redux (too verbose), Context (re-render issues) |
| Date Handling | date-fns | 005-reports | Tree-shakeable, immutable | Moment.js (heavy), Day.js (less features) |
-->

---

## Component Conventions

> Standard locations, naming, and structure for different component types.

| Component Type | Standard Location | Naming Convention | Structure/Template |
|----------------|-------------------|-------------------|-------------------|
| [type] | [path pattern] | [naming rule] | [structure notes] |

<!--
Example entries:
| Services | src/services/ | {domain}Service.ts | Class with constructor injection |
| Repositories | src/repositories/ | {entity}Repository.ts | Interface + implementation |
| React Components | src/components/{domain}/ | PascalCase.tsx | Functional + hooks |
| API Routes | src/routes/{domain}/ | {action}.ts | Express router pattern |
| Schemas | src/schemas/ | {entity}Schema.ts | Zod schema + inferred type |
-->

---

## Anti-Patterns

> Approaches that were tried and MUST be avoided. New features violating these will be flagged.

| Anti-Pattern | Discovered In | Why Avoided | What to Do Instead |
|--------------|---------------|-------------|-------------------|
| [what not to do] | [feature-id] | [problems caused] | [correct approach] |

<!--
Example entries:
| Direct DB in routes | 001-user-auth | Tight coupling, untestable | Use repository layer |
| Global state for forms | 002-forms | Re-renders, stale data | Use local state + react-hook-form |
| Inline styles | 003-dashboard | Inconsistent, unmaintainable | Use Tailwind classes |
| Any type | 001-user-auth | Loses type safety | Define proper types/interfaces |
-->

---

## Cross-Feature Dependencies

> Components/services that are shared across features and their ownership.

| Shared Component | Owner Feature | Used By | API/Interface |
|------------------|---------------|---------|---------------|
| [component] | [feature-id] | [list of features] | [key methods/props] |

<!--
Example entries:
| AuthService | 001-user-auth | 003-dashboard, 004-settings, 005-reports | login(), logout(), getCurrentUser() |
| Button | 001-user-auth | ALL | variant, size, disabled, onClick |
| useNotification | 002-forms | 003-dashboard, 005-reports | show(type, message), dismiss() |
-->

---

## File Organization

> Standard project structure that MUST be followed.

```
[PROJECT_STRUCTURE]
```

<!--
Example:
src/
├── components/     # Reusable UI components
│   ├── common/     # Shared across all features
│   └── {domain}/   # Feature-specific components
├── services/       # Business logic layer
├── repositories/   # Data access layer
├── schemas/        # Validation schemas (Zod)
├── hooks/          # Custom React hooks
├── routes/         # API routes (if applicable)
├── types/          # TypeScript type definitions
└── utils/          # Pure utility functions
-->

---

## Naming Conventions

> Consistent naming rules across the codebase.

| Element | Convention | Examples |
|---------|------------|----------|
| [element type] | [rule] | [examples] |

<!--
Example entries:
| Files (components) | PascalCase | Button.tsx, UserCard.tsx |
| Files (utilities) | camelCase | formatDate.ts, parseQuery.ts |
| Functions | camelCase, verb-first | getUser, validateInput, handleSubmit |
| Constants | SCREAMING_SNAKE | MAX_RETRIES, API_BASE_URL |
| Types/Interfaces | PascalCase, I-prefix optional | User, IUserRepository |
| CSS classes | kebab-case | user-card, btn-primary |
-->

---

## Error Handling Patterns

> Standard approach to error handling across the application.

| Layer | Pattern | Example |
|-------|---------|---------|
| [layer] | [how to handle errors] | [code reference] |

<!--
Example entries:
| API Routes | Try-catch + AppError class | src/middleware/errorHandler.ts |
| Services | Throw typed errors | throw new ValidationError("...") |
| React Components | Error Boundary | src/components/ErrorBoundary.tsx |
| Async Operations | Result type (success/error) | src/types/Result.ts |
-->

---

## Testing Conventions

> Standard testing approaches by component type.

| Component Type | Test Location | Framework | Coverage Target |
|----------------|---------------|-----------|-----------------|
| [type] | [path pattern] | [framework] | [percentage] |

<!--
Example entries:
| Services | __tests__/services/*.test.ts | Vitest | 80% |
| Components | __tests__/components/*.test.tsx | Vitest + Testing Library | 70% |
| API Routes | __tests__/integration/*.test.ts | Vitest + Supertest | 90% |
| E2E | e2e/*.spec.ts | Playwright | Critical paths |
-->

---

## Registry Maintenance

### Adding New Entries

When a feature establishes a new pattern:

1. **During `/speckit.implement`**: Agent identifies pattern-worthy decisions
2. **Post-implementation**: Update this registry with:
   - Pattern name and description
   - Feature that introduced it
   - File locations as reference
   - When to apply it
3. **Commit**: Registry changes committed with feature

### Divergence Protocol

If a new feature MUST diverge from an established pattern:

1. **Document in plan.md**: "Diverges from [PATTERN] because [REASON]"
2. **Get approval**: Divergence requires explicit user confirmation
3. **Update registry**: Either update the pattern or add as alternative
4. **Never silently diverge**: Undocumented divergence = architectural drift

### Periodic Review

- Review registry quarterly or after major features
- Archive obsolete patterns (don't delete, mark deprecated)
- Consolidate similar patterns
- Update examples with better references

---

**Version**: 1.0.0 | **Created**: [DATE] | **Last Updated**: [DATE]
