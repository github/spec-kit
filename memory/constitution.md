# [PROJECT_NAME] Constitution

> **Purpose**: This constitution defines the non-negotiable rules that ALL specifications must follow. It serves as the quality gate for requirements, not implementation.

## Specification Principles

> Rules that every spec.md MUST respect. These are validated by `/speckit.checklist`.

### Accessibility

<!--
Define your accessibility requirements. Example:
- All user interfaces MUST specify WCAG 2.1 AA compliance criteria
- Keyboard navigation MUST be specified for all interactive elements
- Screen reader support MUST be documented for dynamic content
-->

[ACCESSIBILITY_REQUIREMENTS]

### Performance

<!--
Define performance requirements with quantified thresholds. Example:
- All response times MUST be quantified (no "fast", "performant")
- Default thresholds: API < 200ms, UI interaction < 100ms, page load < 3s
- Performance degradation scenarios MUST be specified
-->

[PERFORMANCE_REQUIREMENTS]

### Security

<!--
Define security requirements. Example:
- All sensitive data MUST be identified and handling specified
- Authentication/authorization MUST be explicit for each endpoint
- Data validation requirements MUST be specified at system boundaries
-->

[SECURITY_REQUIREMENTS]

### Error Handling

<!--
Define error handling requirements. Example:
- All features MUST specify their failure modes
- Fallback behavior MUST be defined for critical paths
- User-facing error messages MUST be specified
-->

[ERROR_HANDLING_REQUIREMENTS]

### Data & State

<!--
Define data requirements. Example:
- Data retention policies MUST be specified for user data
- State management approach MUST be documented
- Data migration/versioning strategy MUST be defined for schema changes
-->

[DATA_REQUIREMENTS]

---

## Development Principles

> Fundamental development practices that guide implementation.

### [PRINCIPLE_1_NAME]
<!-- Example: Test-First (TDD) -->
[PRINCIPLE_1_DESCRIPTION]
<!-- Example: Tests written before implementation. Red-Green-Refactor cycle enforced. -->

### [PRINCIPLE_2_NAME]
<!-- Example: Library-First -->
[PRINCIPLE_2_DESCRIPTION]
<!-- Example: Every feature starts as a standalone, testable library. -->

### [PRINCIPLE_3_NAME]
<!-- Example: Simplicity -->
[PRINCIPLE_3_DESCRIPTION]
<!-- Example: YAGNI principles. No premature abstraction. -->

---

## Business Constraints

> Domain-specific rules, compliance requirements, legal constraints.

### Compliance
<!-- Example: GDPR, HIPAA, SOC2, PCI-DSS requirements -->
[COMPLIANCE_REQUIREMENTS]

### Domain Rules
<!-- Example: Business logic invariants, regulatory constraints -->
[DOMAIN_RULES]

---

## Quality Standards

> Measurable quality gates for the project.

| Metric | Target | Enforcement |
|--------|--------|-------------|
| Test Coverage | [TARGET]% | CI blocks below threshold |
| Code Review | [REQUIRED/OPTIONAL] | PR merge requires approval |
| Documentation | [REQUIREMENTS] | API docs required for public interfaces |

---

## Governance

- Constitution supersedes all other practices
- Amendments require: documentation, team approval, migration plan
- All specs MUST be validated against this constitution before implementation
- Divergence from principles requires explicit justification and approval

**Version**: [VERSION] | **Ratified**: [DATE] | **Last Amended**: [DATE]
