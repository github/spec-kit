# JavaScript/TypeScript Style Guide

## Naming Conventions

- **Variables/Functions**: camelCase
- **Classes/Components**: PascalCase
- **Constants**: UPPER_CASE
- **Private Properties**: _camelCase (or #private in classes)
- **Files**: kebab-case.ts or PascalCase.tsx for React components

## Formatting

- **Indentation**: 2 spaces
- **Quotes**: Single quotes preferred
- **Semicolons**: Always used
- **Line Length**: 100 characters max
- **Trailing Commas**: ES5 compatible (objects, arrays, etc.)

## Best Practices

1. **Strict Types**: Always use `strict: true` in `tsconfig.json`.
2. **Explicit Returns**: Explicitly define return types for exported functions.
3. **No Any**: Avoid `any` type; use `unknown` if necessary.
4. **Async/Await**: Prefer `async/await` over `.then()` chains.
5. **Functional**: Prefer functional programming patterns (map, filter, reduce) over loops where appropriate.
6. **Immutability**: Treat data as immutable; use `const` by default.

## Tooling

- **Linter**: ESLint with recommended config
- **Formatter**: Prettier
