---
description: Discover and catalog project structure and components
---

# Project Discovery

Discover and catalog the project's structure, components, and patterns.

## Usage

```bash
{SHADOW_PATH}/scripts/bash/project-catalog{SCRIPT_EXT}
```

## What This Discovers

### Project Structure
- Directory organization
- File naming conventions
- Module boundaries
- Configuration locations

### Code Components
- Main entry points
- Core modules
- Utility functions
- Third-party integrations

### Patterns & Conventions
- Coding patterns used
- Architectural patterns
- Testing patterns
- Documentation patterns

### Dependencies
- External libraries
- Internal dependencies
- Build dependencies
- Runtime dependencies

## Output

Generates:
```
.catalog/project-structure.md
.catalog/components.md
.catalog/patterns.md
.catalog/dependencies.md
```

## Use Cases

### New Team Members
Understand project layout quickly

### Before Major Changes
Know what exists and where

### Documentation
Generate up-to-date project maps

### Refactoring
Identify tightly coupled components

## Best Practices

- Run discovery initially and after major changes
- Keep catalog updated
- Review when onboarding new members
- Use as input for architecture discussions
