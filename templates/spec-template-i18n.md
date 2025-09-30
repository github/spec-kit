# {{locale:templates.spec.title}}: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`
**Created**: [DATE]
**Status**: Draft
**Input**: User description: "$ARGUMENTS"

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "{{locale:messages.errors.no_description}}"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [{{locale:templates.spec.content.needs_clarification}}: specific question]
4. Fill {{locale:templates.spec.sections.user_scenarios}} section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate {{locale:templates.spec.sections.functional_requirements}}
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify {{locale:templates.spec.sections.key_entities}} (if data involved)
7. Run Review Checklist
   → If any [{{locale:templates.spec.content.needs_clarification}}]: WARN "{{locale:messages.warnings.spec_uncertainties}}"
   → If implementation details found: ERROR "{{locale:messages.warnings.remove_tech_details}}"
8. Return: SUCCESS ({{locale:messages.success.spec_ready}})
```

---

## ⚡ Quick Guidelines
- ✅ {{locale:templates.spec.guidelines.focus_what}}
- ❌ {{locale:templates.spec.guidelines.avoid_how}}
- 👥 {{locale:templates.spec.guidelines.business_stakeholders}}

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [{{locale:templates.spec.content.needs_clarification}}: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## {{locale:templates.spec.sections.user_scenarios}} *(mandatory)*

### {{locale:templates.spec.sections.primary_user_story}}
[{{locale:templates.spec.content.describe_main_journey}}]

### {{locale:templates.spec.sections.acceptance_scenarios}}
1. **{{locale:templates.spec.content.given_when_then}}**
2. **{{locale:templates.spec.content.given_when_then}}**

### {{locale:templates.spec.sections.edge_cases}}
- {{locale:templates.spec.content.what_happens_when}}
- {{locale:templates.spec.content.how_system_handles}}

## {{locale:templates.spec.sections.requirements}} *(mandatory)*

### {{locale:templates.spec.sections.functional_requirements}}
- **FR-001**: System MUST [specific capability, e.g., "allow users to create accounts"]
- **FR-002**: System MUST [specific capability, e.g., "validate email addresses"]
- **FR-003**: Users MUST be able to [key interaction, e.g., "reset their password"]
- **FR-004**: System MUST [data requirement, e.g., "persist user preferences"]
- **FR-005**: System MUST [behavior, e.g., "log all security events"]

*Example of marking unclear requirements:*
- **FR-006**: System MUST authenticate users via [{{locale:templates.spec.content.needs_clarification}}: auth method not specified - email/password, SSO, OAuth?]
- **FR-007**: System MUST retain user data for [{{locale:templates.spec.content.needs_clarification}}: retention period not specified]

### {{locale:templates.spec.sections.key_entities}} *(include if feature involves data)*
- **[Entity 1]**: [What it represents, key attributes without implementation]
- **[Entity 2]**: [What it represents, relationships to other entities]

---

## {{locale:templates.spec.sections.review_checklist}}
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

### Requirement Completeness
- [ ] No [{{locale:templates.spec.content.needs_clarification}}] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

---

## {{locale:templates.spec.sections.execution_status}}
*Updated by main() during processing*

- [ ] User description parsed
- [ ] Key concepts extracted
- [ ] Ambiguities marked
- [ ] User scenarios defined
- [ ] Requirements generated
- [ ] Entities identified
- [ ] Review checklist passed

---