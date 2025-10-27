# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[username/jira-123.feature-name]` OR `[username/feature-name]`
**Created**: [DATE]
**Status**: Draft
**Input**: User description: "$ARGUMENTS"

**Product Context**: docs/product-vision.md (if exists)
**System Architecture**: docs/system-architecture.md (if exists)

## Execution Flow (main)
```
1. Check for product context:
   → If docs/product-vision.md exists: Load personas, product-wide NFRs, success metrics
   → If missing: Proceed with feature-only context (no product context)
2. Check for system architecture:
   → If docs/system-architecture.md exists: Load architectural constraints, existing tech stack
   → If missing: No architectural constraints (likely first feature/MVP)
3. Parse user description from Input
   → If empty: ERROR "No feature description provided"
4. Extract key concepts from description
   → Identify: actors, actions, data, constraints
5. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
6. Research Phase: Fill Context Engineering section
   → Search codebase for similar features
   → Document external research findings
   → If product vision exists: Skip market research, extract from product-vision.md
   → Identify required documentation and gotchas
   → Run Context Completeness Check
7. Fill User Scenarios & Testing section
   → If product vision exists: Use personas from product-vision.md
   → If no clear user flow: ERROR "Cannot determine user scenarios"
8. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
9. Generate Non-Functional Requirements (NEW - Industry Tier 2)
   → If product vision exists: Inherit product-wide NFRs
   → Add feature-specific NFRs (performance, security, scale)
   → Each NFR must be measurable
10. Document Technical Constraints (NEW - Industry Tier 2)
   → If system architecture exists: Note integration requirements
   → Constraints are WHAT EXISTS, not HOW TO BUILD
   → Must integrate with X, Must use existing Y
11. Identify Key Entities (if data involved)
12. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
   → If architecture decisions found: ERROR "Architecture belongs in /plan"
   → If Context Completeness Check fails: WARN "Insufficient context for implementation"
13. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ✅ Include HOW WELL (performance targets, security requirements)
- ✅ Include WHAT EXISTS (must integrate with X, must use existing Y)
- ❌ Avoid HOW TO BUILD (no architecture decisions, no technology choices)
- 👥 Written for product/engineering collaboration (Industry Tier 2: Requirements + Constraints)
### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
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

## Context Engineering *(for AI agents)*

When an AI agent later implements this specification, it will need comprehensive context to succeed. Fill this section during the specification phase to ensure implementation success.

### Context Completeness Check

_Before finalizing this spec, validate: "If someone knew nothing about this codebase, would they have everything needed to implement this feature successfully?"_

### Research & Documentation *(fill during /specify)*

```yaml
# MUST READ - Include these in implementation context
- url: [Complete URL with section anchor if applicable]
  why: [Specific methods/concepts needed for implementation]
  critical: [Key insights that prevent common implementation errors]

- file: [exact/path/to/pattern/file.ext]
  why: [Specific pattern to follow - class structure, error handling, etc.]
  pattern: [Brief description of what pattern to extract]
  gotcha: [Known constraints or limitations to avoid]

- docfile: [ai_docs/domain_specific.md]
  why: [Custom documentation for complex library/integration patterns]
  section: [Specific section if document is large]
  gotcha: [Critical gotchas specific to this feature]
```

### Similar Features *(reference during /specify)*

List existing features in the codebase that share patterns with this one:
- **[Feature Name]** at `path/to/implementation` - [What pattern to reuse]
- **[Feature Name]** at `path/to/implementation` - [What to avoid/learn from]

### External Research Notes *(fill during /specify)*

Key findings from researching this feature type:
- **Best Practices**: [Links to authoritative sources]
- **Common Pitfalls**: [What typically goes wrong]
- **Performance Considerations**: [Known bottlenecks or optimization opportunities]

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
[Describe the main user journey in plain language]

### Acceptance Scenarios
1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]

### Edge Cases
- What happens when [boundary condition]?
- How does system handle [error scenario]?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST [specific capability, e.g., "allow users to create accounts"]
- **FR-002**: System MUST [specific capability, e.g., "validate email addresses"]  
- **FR-003**: Users MUST be able to [key interaction, e.g., "reset their password"]
- **FR-004**: System MUST [data requirement, e.g., "persist user preferences"]
- **FR-005**: System MUST [behavior, e.g., "log all security events"]

*Example of marking unclear requirements:*
- **FR-006**: System MUST authenticate users via [NEEDS CLARIFICATION: auth method not specified - email/password, SSO, OAuth?]
- **FR-007**: System MUST retain user data for [NEEDS CLARIFICATION: retention period not specified]

### Key Entities *(include if feature involves data)*
- **[Entity 1]**: [What it represents, key attributes without implementation]
- **[Entity 2]**: [What it represents, relationships to other entities]

### Non-Functional Requirements *(NEW - Industry Tier 2)*

*These specify HOW WELL the feature must perform, not HOW to build it.*

#### Performance Requirements
- **NFR-P001**: [Specific performance target, e.g., "API responds in < 200ms (p95)"]
- **NFR-P002**: [Throughput requirement, e.g., "Support 100 concurrent requests"]
- **NFR-P003**: [Load time requirement, e.g., "Page loads in < 2 seconds"]

#### Security Requirements
- **NFR-S001**: [Security constraint, e.g., "Encrypt PII data at rest and in transit"]
- **NFR-S002**: [Auth requirement, e.g., "Require MFA for administrative actions"]
- **NFR-S003**: [Access control, e.g., "Role-based access control for feature access"]

#### Scalability Requirements
- **NFR-SC001**: [Scale target, e.g., "Support 1000 concurrent users for this feature"]
- **NFR-SC002**: [Data scale, e.g., "Handle up to 100k records per user"]

#### Availability Requirements
- **NFR-A001**: [Uptime requirement, e.g., "99.9% availability for this feature"]
- **NFR-A002**: [Degradation, e.g., "Graceful degradation when dependent service unavailable"]

#### Compliance Requirements *(if applicable)*
- **NFR-C001**: [Regulatory requirement, e.g., "GDPR-compliant data handling"]
- **NFR-C002**: [Audit requirement, e.g., "Audit log all user actions in this feature"]

**Source Tracking**:
- Inherited from product vision (docs/product-vision.md): [List NFRs that came from product vision]
- Feature-specific (new for this feature): [List NFRs unique to this feature]

*Note: If product vision exists, many NFRs will be inherited. Feature adds specifics.*

### Technical Constraints *(NEW - Industry Tier 2)*

*These specify WHAT EXISTS and must be used or integrated with. They are constraints, not decisions.*

**Key Distinction**:
- ✅ Constraint: "Must integrate with existing PostgreSQL database" (what exists)
- ✅ Constraint: "Must use existing JWT authentication" (what exists)
- ❌ Decision: "Use PostgreSQL for storage" (how to build - belongs in /plan)
- ❌ Decision: "Implement JWT authentication" (how to build - belongs in /plan)

#### Integration Constraints
- Must integrate with: [Existing feature/system, e.g., "proj-1 messaging system"]
- Must use existing: [Component, e.g., "WebSocket connection from proj-1"]
- Must maintain compatibility with: [API/interface, e.g., "v1 REST API"]

#### Technology Constraints *(from system architecture)*
- Must use: [Existing tech, e.g., "PostgreSQL 15+ (system constraint)"]
- Must deploy via: [Infrastructure, e.g., "Existing Docker/ECS infrastructure"]
- Must authenticate with: [Auth system, e.g., "Existing JWT token system"]

#### Compatibility Constraints
- Must support: [Platforms/browsers, e.g., "Latest 2 versions of Chrome, Firefox, Safari"]
- Must work with: [Existing data, e.g., "Existing user account schema"]

#### Operational Constraints
- Must adhere to: [Operational requirement, e.g., "Existing logging/monitoring patterns"]
- Must respect: [Resource limits, e.g., "Database connection pool limits"]

**Source Tracking**:
- From system architecture (docs/system-architecture.md): [List constraints from existing architecture]
- From existing features: [List integration requirements with other features]
- From operational requirements: [List infrastructure/deployment constraints]

*Note: First feature (MVP) will have minimal constraints. Later features accumulate constraints from earlier features.*

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] No architecture decisions (those belong in /plan)
- [ ] Focused on user value, requirements, and constraints
- [ ] Written for product/engineering collaboration (Industry Tier 2)
- [ ] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Functional requirements are testable and unambiguous
- [ ] Non-functional requirements are measurable and specific
- [ ] Technical constraints clearly stated (what exists, not how to build)
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

### Tier 2 Alignment (NEW)
- [ ] NFRs include performance, security, scale, availability targets
- [ ] Constraints distinguish between "what exists" and "how to build"
- [ ] Product context integrated if product-vision.md exists
- [ ] Architecture constraints noted if system-architecture.md exists

---

## Execution Status
*Updated by main() during processing*

- [ ] Product context loaded (if exists)
- [ ] System architecture context loaded (if exists)
- [ ] User description parsed
- [ ] Key concepts extracted
- [ ] Ambiguities marked
- [ ] Research phase completed (Context Engineering filled)
- [ ] Context completeness check passed
- [ ] User scenarios defined
- [ ] Functional requirements generated
- [ ] Non-functional requirements generated
- [ ] Technical constraints documented
- [ ] Entities identified
- [ ] Review checklist passed

---

## Change History

_Track specification evolution over time. Add entries when requirements change after initial creation._

_Format: Use delta format (ADDED/MODIFIED/REMOVED) to clearly document what changed and why._

### Example Entry Format

**[YYYY-MM-DD] ADDED: [Requirement Name]**

[New requirement text using SHALL/MUST]

**Rationale**: [Why this was added - business justification, user feedback, discovered need]

---

**[YYYY-MM-DD] MODIFIED: [Requirement Name]**

**Previous**: [Old requirement text]

**Updated**: [New requirement text]

**Rationale**: [Why this changed - new information, clarification, scope adjustment]

---

**[YYYY-MM-DD] REMOVED: [Requirement Name]**

**Removed Text**: [What was removed]

**Reason**: [Why this was removed - out of scope, moved to different feature, no longer needed]

---

<!-- Add actual change entries below as specification evolves -->

---
