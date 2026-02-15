# ADR-001: Package-per-directory registry structure

## Status

Accepted

## Context

Registry repos need a structure for organizing packages (commands, skills, hooks). Two options considered: flat convention-based (files grouped by type) or package-per-directory (each package self-contained).

## Decision

Use package-per-directory structure where each package has its own directory with `package.yaml`, source files, and README.

## Rationale

- Each package is independently auditable — critical for enterprise security review
- Supports per-package versioning and metadata
- Allows different teams within an enterprise to own specific packages
- Scales better as registries grow
- Each package can have its own README for documentation

## Consequences

- Slightly more structure to author than flat layout
- Package authors need to create `package.yaml` for each package
