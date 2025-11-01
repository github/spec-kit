# AI Agent Documentation

Documentation and context for AI agents working with Spec Kit.

## Overview

This directory contains information specifically for AI coding agents (Claude Code, GitHub Copilot, Gemini CLI, etc.) to help them understand and work effectively with the Spec-Driven Development workflow.

## Contents

- **[Library Gotchas](./library_gotchas.md)** - Common pitfalls and issues with various libraries and frameworks

## For AI Agents

When working with Spec Kit projects, AI agents should:

1. **Understand the three-phase workflow**
   - Phase 1: Specification (requirements and constraints)
   - Phase 2: Planning (architecture and technical decisions)
   - Phase 3: Implementation (coding and validation)

2. **Respect the separation of concerns**
   - Specifications define WHAT and WHY
   - Plans define HOW
   - Code implements according to plan

3. **Follow the constitution**
   - Projects may have `memory/constitution.md` with project-specific principles
   - Respect established patterns and decisions
   - Document rationale for architectural choices

4. **Work atomically**
   - For large features (>1000 LOC), decompose into capabilities
   - Each capability should be 400-1000 LOC
   - Create focused PRs for faster reviews

5. **Validate against specifications**
   - Implementation must satisfy acceptance criteria
   - Plans must address all requirements
   - Tests must prove correctness

## Prompt Engineering Tips

When working with Spec Kit:

### For Specifications
```
Create a specification for [feature]. Include:
- What the feature must do (functional requirements)
- Performance and quality targets (non-functional requirements)
- What exists that we must integrate with (technical constraints)
- Testable acceptance criteria
```

### For Planning
```
Create an implementation plan for [feature] using [tech stack].
Include:
- Architecture decisions with rationale
- Technology choices justified by requirements
- Data models and schemas
- API designs
- Testing strategy
```

### For Implementation
```
Implement according to specs/[feature-id]/plan.md.
Ensure:
- All acceptance criteria are met
- Tests validate requirements
- Code follows established patterns
- Clear commit messages reference spec
```

## Context Loading

AI agents can load relevant context from:

1. **Product Vision** (`docs/product-vision.md`) - Strategic direction
2. **System Architecture** (`docs/system-architecture.md`) - Current architecture
3. **Constitution** (`memory/constitution.md`) - Project principles
4. **Specification** (`specs/[feature-id]/spec.md`) - Feature requirements
5. **Implementation Plan** (`specs/[feature-id]/plan.md`) - Technical approach

## Common Patterns

### Feature Addition
1. Read existing product vision and architecture
2. Create specification with `/specify`
3. Create implementation plan with `/plan`
4. Generate tasks with `/tasks`
5. Implement according to plan

### Brownfield Changes
1. Review existing architecture
2. Understand constraints from current system
3. Plan changes that respect existing patterns
4. Implement with minimal disruption

### Large Features
1. Create full specification
2. Use `/decompose` to break into capabilities
3. For each capability:
   - Create focused plan
   - Implement atomically
   - Submit PR and merge
   - Move to next capability

## Related

- [User Documentation](../docs/) - For developers using Spec Kit
- [Contributing](../contributing/) - For Spec Kit contributors
