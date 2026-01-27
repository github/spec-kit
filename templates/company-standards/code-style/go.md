# Go Style Guide

## Naming Conventions

- **Variables/Functions**: camelCase (exported start with Uppercase)
- **Interfaces**: MethodName + er (e.g., Reader, Writer)
- **Constants**: PascalCase (exported) or camelCase (internal)
- **Packages**: singleword (lowercase)

## Formatting

- **Style**: Standard `gofmt` style
- **Indentation**: Tabs (standard Go)
- **Line Length**: No strict limit, but keep reasonable

## Best Practices

1. **Error Handling**: Handle errors explicitly; do not ignore returned errors.
2. **Concurrency**: Share memory by communicating, don't communicate by sharing memory.
3. **Context**: Pass `context.Context` as the first argument to functions involving I/O.
4. **Interfaces**: Define interfaces where they are used, not where they are implemented.
5. **Constructors**: Use `NewType` or `New` functions.
6. **Testing**: Use table-driven tests.

## Tooling

- **Formatter**: gofmt / goimports
- **Linter**: golangci-lint
