# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`  
**Created**: [DATE]  
**Status**: Draft  
**Input**: User description: "$ARGUMENTS"

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

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
   - **Odoo-specific**: Module dependencies, access groups, record rules, view requirements, field types and relationships

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

## Odoo Addon Architecture *(mandatory for Odoo projects)*

### Addon Strategy Assessment
**Constitutional analysis of user requirements**
- **Strategy Chosen**: [Single Addon / Multi-Addon]
- **Rationale**: [Why this strategy was chosen based on constitutional indicators]
- **Assessment Factors**: [Customer flexibility needs, localization, technology choices, business domains affected]

### Addon Decomposition Strategy
**Feature breakdown into coherent groups** *(complete this section based on chosen strategy)*

#### If Single Addon Strategy:
- **[Addon Name]**: [Comprehensive description of coherent feature group, e.g., "advanced_inventory_analytics - Complete inventory analytics with reporting, dashboards, and alerts"]

#### If Multi-Addon Strategy:
- **[Core Addon Name]** (Core): [Primary coherent feature group, e.g., "project_analytics_base - Core analytics models, basic reporting, and essential dashboards"]
- **[Extension Addon Name]** (Optional): [Enhanced feature group, e.g., "project_analytics_advanced - AI insights, predictive analytics, and advanced visualizations"]
- **[Integration Addon Name]** (Integration): [Technology-specific group, e.g., "project_analytics_slack - Slack integration, notifications, and collaborative reporting"]
- **[Localization Addon Name]** (Localization): [Region-specific group, e.g., "project_analytics_fr - French localization, compliance reporting, and local integrations"]

### Addon Dependencies & Relationships
**Dependencies based on chosen strategy**

#### If Single Addon Strategy:
```
[Addon Name]
├── Core Dependencies: [required Odoo modules, e.g., base, sale, stock]
├── Optional Dependencies: [optional Odoo modules that enhance functionality]
└── External Dependencies: [third-party modules or APIs if any]
```

#### If Multi-Addon Strategy:
```
[Core Addon]
├── Core Dependencies: [base, project, sale]
├── Inter-addon Dependencies: [none - this is the base]
└── Optional Dependencies: [hr, timesheet]

[Extension Addon]
├── Core Dependencies: [base, project]
├── Inter-addon Dependencies: [core_addon_name]
└── Optional Dependencies: [website, portal]

[Integration Addon]
├── Core Dependencies: [base]
├── Inter-addon Dependencies: [core_addon_name]
└── Optional Dependencies: [third_party_connector]
```

### Per-Addon Architecture Details
**Complete this section based on chosen strategy**

#### If Single Addon Strategy:
##### [Addon Name] - Comprehensive Feature Group
- **Business Purpose**: [Complete business problem this addon solves]
- **Models**: [All models for this coherent feature group]
  - `[model.name]`: [Fields and relationships]
  - `[model.name]`: [Computed fields and methods]
- **Views**: [All forms, lists, kanban, search views needed]
- **Security**: [Complete access groups and record rules]
- **Configuration**: [Settings and parameters]
- **Demo Data**: [Sample records for testing]
- **Localization**: [Translation and regional needs]

#### If Multi-Addon Strategy:
##### [Core Addon Name] - Base Feature Group
- **Business Purpose**: [Core business problem this addon solves]
- **Models**: [Base models for the feature group]
- **Views**: [Essential views and interfaces]
- **Security**: [Core access groups and record rules]
- **API/Interfaces**: [What this addon exposes to other addons]

##### [Extension Addon Name] - Enhanced Feature Group
- **Business Purpose**: [Enhanced functionality built on core addon]
- **Models**: [Additional models or extensions to core models]
- **Views**: [Additional or enhanced views]
- **Security**: [Additional security groups]
- **Dependencies**: [How it integrates with core addon]

##### [Integration Addon Name] - Technology Integration
- **Business Purpose**: [External system integration purpose]
- **Technology**: [Specific technology, API, or service]
- **Models**: [Integration-specific models and logging]
- **Configuration**: [Settings and credentials management]
- **Fallback**: [Behavior when integration is unavailable]

### Customer Deployment Flexibility
**Based on chosen strategy**

#### If Single Addon Strategy:
- **Installation**: [Single addon provides complete functionality]
- **Configuration Options**: [Settings to enable/disable features within the addon]
- **Localization**: [Built-in translation and regional adaptation capabilities]

#### If Multi-Addon Strategy:
- **Minimum Installation**: [Which addons are required for basic functionality]
- **Optional Features**: [Which addons customers can choose to install]
- **Localization Options**: [Region-specific addons available]
- **Integration Choices**: [Technology-specific addons (Stripe vs PayPal, etc.)]

### Cross-Addon Integration Points
**Only applicable for Multi-Addon Strategy**
- **Shared Models**: [Models that other addons extend or reference]
- **Event Hooks**: [Odoo signals/events for inter-addon communication]
- **API Contracts**: [Standardized methods for addon interaction]
- **Data Flow**: [How data moves between addons]
- **Fallback Behavior**: [How system works when optional addons are not installed]

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

### Addon Architecture Completeness
- [ ] Addon strategy assessment completed using constitutional framework
- [ ] Strategy choice (single vs multi-addon) justified based on user requirements
- [ ] Feature decomposed into coherent groups (not micro-addons)
- [ ] Each addon serves a coherent business purpose with appropriate complexity
- [ ] Dependencies clearly mapped (Odoo core, inter-addon if applicable, optional)
- [ ] Customer deployment flexibility defined appropriately for chosen strategy
- [ ] Cross-addon integration points documented (if multi-addon strategy)
- [ ] Base functionality works without optional components
- [ ] Each addon is independently testable and installable
- [ ] Shared functionality properly organized (within addon or across addons)

---

## Execution Status
*Updated by main() during processing*

- [ ] User description parsed
- [ ] Key concepts extracted
- [ ] Ambiguities marked
- [ ] User scenarios defined
- [ ] Requirements generated
- [ ] Entities identified
- [ ] Odoo architecture defined
- [ ] Module dependencies identified
- [ ] Security model specified
- [ ] Review checklist passed

---
