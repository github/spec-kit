# Templates Reference

Available templates and their structure.

## Specification Templates

### Standard Specification (`spec-template.md`)
Full specification with all sections.

Used for features 800-1000 LOC with complex requirements.

**Sections**:
- Feature Overview
- User Personas
- User Stories & Use Cases
- Functional Requirements
- Non-Functional Requirements
- Technical Constraints
- Acceptance Criteria
- Edge Cases
- Assumptions
- Review & Acceptance Checklist

### Lightweight Specification (`spec-template-lightweight.md`)
Compact specification for simpler features.

Used for features 200-800 LOC.

**Sections**:
- Feature Overview
- Requirements (combined)
- Acceptance Criteria
- Review Checklist

### Quick Specification (`spec-template-quick.md`)
Minimal specification for small changes.

Used for features <200 LOC.

**Sections**:
- What's needed
- Acceptance Criteria
- Checklist

## Implementation Plan Templates

### Standard Plan (`plan-template.md`)
Complete implementation plan with architecture.

**Sections**:
- Overview
- Architecture Decisions
- Technology Choices
- Data Model
- API Design
- Implementation Approach
- Testing Strategy
- Deployment Strategy

### Lightweight Plan (`plan-template-lightweight.md`)
Compact plan for simpler features.

**Sections**:
- Tech Stack
- Key Decisions
- Implementation Steps
- Testing Approach

## Other Templates

### Product Vision (`product-vision-template.md`)
Strategic product definition.

### System Architecture (`system-architecture-template.md`)
Overall system architecture documentation.

### Tasks (`tasks-template.md`)
Task breakdown format.

### Decompose (`decompose-template.md`)
Breaking large features into capabilities.

### Capability Spec (`capability-spec-template.md`)
Specification for individual capabilities.

## Template Customization

Custom templates can be placed in `.specify/templates/`.

The AI agent will use custom templates instead of defaults if they match the naming pattern.

## Template Variables

Templates support variable substitution:
- `[FEATURE_NAME]` - Feature name
- `[FEATURE_ID]` - Feature ID
- `[WORKSPACE_NAME]` - Workspace name (if multi-repo)
- `[REPO_NAME]` - Repository name
- `[DATE]` - Current date

## Related

- [Configuration](./configuration.md) - Where templates are stored
- [Guides](../guides/) - Examples using templates
- [Concepts](../concepts/) - Understanding each template's purpose
