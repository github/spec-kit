# Slash Commands Reference

AI agent commands available in your project.

## Slash Commands Overview

### `/specify`
Create or refine feature specification.

```
/specify Build a feature that...
```

**Purpose**: Gather and clarify requirements before implementation
**Input**: Description of what you want to build
**Output**: `specs/[feature-id]/spec.md` with acceptance criteria
**Time**: 15-30 minutes initial, iterate with follow-ups

### `/decompose`
Break large feature into atomic capabilities.

```
/decompose
```

**Purpose**: Split >1000 LOC features into manageable pieces
**Input**: Complete specification
**Output**: Capability subdirectories with individual plans
**Time**: 5 minutes

### `/plan`
Create implementation plan based on specification.

```
/plan Build with [tech stack description]
/plan --capability cap-001
```

**Purpose**: Make technical decisions to satisfy requirements
**Input**: Specification + tech stack preferences
**Output**: `plan.md` with architecture and design
**Time**: 20-40 minutes

### `/tasks`
Generate actionable task list from plan.

```
/tasks
```

**Purpose**: Break plan into concrete work items
**Input**: Implementation plan
**Output**: `tasks.md` with ordered task list
**Time**: 5 minutes

### `/implement`
Execute implementation plan.

```
implement specs/[feature-id]/plan.md
```

**Purpose**: Convert plan to working code
**Input**: Implementation plan
**Output**: Implemented feature + tests
**Time**: Varies (20 min to hours)

### `/product-vision` (Optional)
Define product-level vision and strategy.

```
/product-vision Description of your product...
```

**Purpose**: Create strategic context for feature development
**Input**: Product description and goals
**Output**: `docs/product-vision.md`
**Time**: 20-30 minutes (once per product)

### `/review`
Code review and quality assessment.

```
/review Check this code against requirements
```

**Purpose**: Validate implementation quality
**Input**: Code changes
**Output**: Review feedback and suggestions

### `/validate`
Validation and quality gates.

```
/validate Is the spec complete?
```

**Purpose**: Ensure each phase meets standards
**Input**: Specification, plan, or implementation
**Output**: Validation report

### `/debug`
Systematic debugging assistance.

```
/debug Help me understand why this fails...
```

**Purpose**: Root cause analysis and problem-solving
**Input**: Problem description and error messages
**Output**: Diagnosis and solution

## Command Workflow

### Simple Features (<200 LOC)
```
/specify → /tasks → /implement
```

### Standard Features (200-800 LOC)
```
/specify → /plan → /tasks → /implement
```

### Complex Features (800-1000 LOC)
```
/specify → Refine → /plan → /tasks → /implement
```

### Large Features (>1000 LOC)
```
/specify → /decompose → for each capability:
  /plan --capability capN → /tasks → /implement
```

## Tips

- Use `/specify` multiple times to refine requirements
- Review plan carefully before `/implement`
- Ask `/tasks` after `/plan` for clear task breakdown
- Use `/review` before committing code
- Use `/validate` to catch issues early

## Related References

- [Concepts: Development Workflow](../concepts/development-workflow.md)
- [Guides](../guides/) - Practical examples
- [Templates](./templates.md) - Template documentation
