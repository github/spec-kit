# AI Documentation Repository

This directory contains critical documentation and patterns that are frequently referenced during AI-assisted development. These files provide essential context that helps AI agents understand codebase-specific patterns, library quirks, and implementation guidelines.

## Purpose

When creating specifications and plans, AI agents need access to:
- Library-specific implementation patterns
- Codebase conventions and gotchas
- Custom utility documentation
- Framework-specific best practices

Files in this directory should be referenced in specifications using the `docfile` YAML format:

```yaml
- docfile: ai_docs/framework_patterns.md
  why: Custom authentication patterns for this project
  section: OAuth Implementation
```

## Organization

- **framework_patterns.md**: Patterns specific to the main framework/language
- **library_gotchas.md**: Known issues and workarounds for dependencies
- **custom_utils.md**: Documentation for project-specific utilities
- **integration_patterns.md**: Common integration patterns and examples

## Guidelines

1. **Keep focused**: Each file should address specific implementation needs
2. **Include examples**: Provide concrete code examples, not just descriptions
3. **Update regularly**: Keep documentation current with codebase changes
4. **Reference context**: Explain why patterns exist and when to use them

## Usage in Specifications

Reference these files in your specifications' "All Needed Context" section:

```yaml
Documentation & References:
- docfile: ai_docs/authentication_patterns.md
  why: Custom JWT implementation with refresh token handling
  section: Refresh Token Flow
  gotcha: Tokens expire after 15 minutes, not the standard 1 hour
```

This ensures AI agents have the necessary context for successful implementation without needing to discover patterns throdos ugh trial and error.