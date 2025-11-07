---
description: Create a new feature specification
---

# Create Feature Specification

You are tasked with creating a comprehensive feature specification for the project.

## Process

1. **Understand the requirement** - Ask clarifying questions if needed
2. **Use the template** - Base your specification on `templates/spec-template.md`
3. **Fill all sections** - Complete every section with detailed information
4. **Validate** - After creating the spec, run validation:

```bash
{SHADOW_PATH}/scripts/bash/validate-spec{SCRIPT_EXT} .specs/<feature-name>.md
```

5. **Iterate** - Fix any validation errors and re-validate

## Specification Structure

Your specification must include:
- Clear problem statement
- Detailed requirements (functional and non-functional)
- Technical approach
- Acceptance criteria
- Dependencies and risks
- Out of scope items

## Output

Save the specification to:
```
.specs/<feature-name>.md
```

where `<feature-name>` is a kebab-case name describing the feature.

## Validation

The specification must pass validation checks:
- All required sections present
- Acceptance criteria properly formatted
- No broken cross-references
- Token budget compliance
