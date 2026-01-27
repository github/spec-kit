# Java Style Guide

## Naming Conventions

- **Variables/Methods**: camelCase
- **Classes/Interfaces**: PascalCase
- **Constants**: UPPER_CASE
- **Packages**: lowercase.dot.separated

## Formatting

- **Style**: Google Java Style
- **Indentation**: 2 spaces (Google) or 4 spaces (Standard)
- **Braces**: K&R style (opening brace on same line)
- **Line Length**: 100 characters

## Best Practices

1. **Immutability**: Prefer final fields and immutable objects.
2. **Optional**: Use `Optional<T>` for return types instead of returning `null`.
3. **Streams**: Use Stream API for collections processing.
4. **Exceptions**: Use checked exceptions for recoverable conditions, unchecked for programming errors.
5. **Logging**: Use SLF4J; never `System.out.println`.
6. **Dependency Injection**: Constructor injection preferred over field injection.

## Tooling

- **Linter**: Checkstyle / PMD / SpotBugs
- **Formatter**: Google Java Format
