# Brownfield Development

Adding features to established systems while respecting existing patterns and constraints.

## What is Brownfield?

Building new features into systems that:
- Already have established architecture
- Have existing code patterns
- Have defined technology choices
- Have historical constraints and decisions

## Key Differences from Greenfield

**Greenfield** (`/product-vision` → first feature)
- Define everything from scratch
- Establish architectural foundation
- Set product direction

**Brownfield** (adding to existing system)
- Inherit product vision and architecture
- Work within or extend existing patterns
- Respect established decisions

## The Brownfield Process

1. **Specify new feature**
   - Inherits product vision context if exists
   - Specifies new requirements
   - Notes constraints from existing architecture

2. **Plan feature**
   - Chooses: Work within? Extend? Refactor?
   - Makes decisions respecting existing patterns
   - Documents how feature integrates

3. **Implement**
   - Follows established code patterns
   - Integrates with existing systems
   - Maintains architectural consistency

## Working Within Architecture

Most new features work within existing architecture:
- Use existing databases, frameworks, APIs
- Follow established patterns
- No architectural changes needed

## Extending Architecture

Some features require new components:
- Add new database tables or columns
- Add new services or microservices
- Extend existing APIs
- Minor version bump of architecture

## Major Refactors

Large features sometimes require rearchitecting:
- Migrate from monolith to microservices
- Replace core infrastructure
- Fundamental design changes
- Major version bump, breaking changes

## Documentation

Maintain `docs/system-architecture.md` documenting:
- Current version
- Major components
- Technology choices
- Scaling characteristics
- Known limitations and debt

## Tips for Success

- Read existing architecture documentation
- Understand why current decisions were made
- Respect established patterns (even if you'd choose differently)
- Propose changes formally rather than circumventing them
- Document new patterns you establish
- Pay down technical debt strategically

## Next Steps

- [Architecture Evolution](./architecture-evolution.md) - How systems evolve
- [Guides: Complex Features](../guides/complex-features.md) - Examples
- [Reference](../reference/) - Documentation templates
