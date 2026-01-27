# Python Style Guide

## Naming Conventions

- **Variables/Functions**: snake_case
- **Classes**: PascalCase
- **Constants**: UPPER_CASE
- **Modules/Packages**: snake_case (short, all lowercase)
- **Protected/Private**: _leading_underscore

## Formatting

- **Style**: Follow PEP 8
- **Indentation**: 4 spaces
- **Line Length**: 88 characters (Black compatible) or 79 (Strict PEP 8)
- **Quotes**: Double quotes preferred (Black default)

## Best Practices

1. **Type Hints**: Use type hints for all function arguments and return values.
2. **Docstrings**: Use Google style docstrings for all public modules, functions, classes, and methods.
3. **Imports**: Sort imports (Standard Library > Third Party > Local Application).
4. **Exceptions**: Catch specific exceptions, never bare `except:`.
5. **Context Managers**: Use `with` statements for resource management.
6. **List Comprehensions**: Use for simple transformations; avoid for complex logic.

## Tooling

- **Linter**: Ruff or Flake8
- **Formatter**: Black or Ruff
- **Type Checker**: Mypy
