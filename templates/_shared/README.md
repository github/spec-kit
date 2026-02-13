# Shared Context

This directory holds project-wide standards and conventions that apply across
all feature specs. Every `.md` file placed here is automatically loaded as
read-only context by the following Spec Kit commands:

- **specify** -- informs spec structure and alignment with project standards
- **clarify** -- validates spec alignment and informs ambiguity detection
- **plan** -- guides technical decisions in implementation plans
- **tasks** -- informs task structure and sequencing
- **implement** -- guides implementation decisions and coding patterns
- **checklist** -- incorporates project-wide requirements into validation
- **analyze** -- uses standards as additional validation criteria

## What to put here

Create `.md` files for any project-wide standards you want consistently applied:

- **Architecture decisions** -- system boundaries, data flow, service topology
- **API conventions** -- endpoint naming, versioning, request/response patterns
- **Coding standards** -- naming, formatting, error handling, logging patterns
- **Security requirements** -- authentication, authorization, input validation
- **Accessibility standards** -- WCAG compliance, ARIA patterns
- **Testing conventions** -- coverage expectations, mocking strategies, test naming

## Example

```
specs/_shared/
  api-conventions.md
  coding-standards.md
  security-requirements.md
```

## Notes

- Files are **read-only** -- Spec Kit commands never modify shared context.
- Only `.md` files are loaded; other file types are ignored.
- This directory is optional. If absent, commands proceed without shared context.
