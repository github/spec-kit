# [PROJECT_NAME] Constitution
<!-- Example: Odoo ERP Development Constitution, Custom Odoo Addons Constitution, etc. -->

## Core Principles

> **Odoo Development Focus**: This constitution is specifically designed for Odoo ERP development (v18+). It emphasizes addon-based architecture, ORM patterns, and Odoo community standards while maintaining flexibility for project-specific requirements.

### I. Adaptive Addon Architecture Strategy
**Choose single vs multi-addon based on feature complexity and user requirements**
- **Assessment Criteria**: Analyze user input for feature scope, customer flexibility needs, localization requirements, and technology integrations
- **Single Addon Strategy**: Use when feature is cohesive, no customer choice needed, single business process
- **Multi-Addon Strategy**: Use when feature involves multiple business domains, customer flexibility required, localization needed, or technology choices (payment gateways, shipping, etc.)
- **Coherent Feature Groups**: Group related features/processes into logical addons (not micro-addons)
- **Maximum complexity per addon**: ~10 models, ~10 views, ~10 owl components,manageable for small team

### II. Addon Dependency Management
**Explicit, minimal, and well-documented addon dependencies**
- Core dependencies: Only essential Odoo modules (base, sale, purchase, etc.)
- Inter-addon dependencies: Clearly defined and documented interfaces
- Optional dependencies: Use for optional integrations (payment gateways, localization)
- Dependency cycles: Strictly forbidden - refactor shared logic into base addon
- Version compatibility: Each addon must declare minimum/maximum Odoo version support

### III. Test-First Multi-Addon Development (NON-NEGOTIABLE)
**TDD across addon boundaries with integration focus**
- Unit tests: Each addon tested in isolation with mocked dependencies
- Integration tests: Test addon interactions and data flow between addons
- Addon isolation: Tests must pass with only required dependencies installed
- Cross-addon scenarios: Test complete business flows spanning multiple addons
- Migration tests: Validate addon upgrades and data migrations independently

### IV. Customer Flexibility & Modularity
**Design for optional installation and customer choice**
- Base functionality: Core features work without optional addons
- Feature toggles: Optional addons enhance but don't break base functionality
- Localization addons: Separate addons for country-specific features
- Technology integrations: Payment, shipping, and external services as optional addons
- Customer deployment: Customers install only needed addons for their business

### V. Addon Composition Patterns
**Standard patterns for addon interaction and shared functionality**
- Base addon pattern: Shared models and utilities in dedicated base addon
- Extension pattern: Addons extend base addon functionality via inheritance
- Bridge pattern: Connector addons for integration between business domains
- Configuration addon: Settings and parameters managed in dedicated configuration addon
- API consistency: Standard interfaces between addons for data exchange

## Addon Strategy Assessment Framework

### Decision Matrix for Single vs Multi-Addon
**Analyze user input against these criteria to determine optimal addon architecture**

#### Single Addon Indicators
- Feature describes a cohesive business process (e.g., "advanced inventory reporting")
- No mention of customer choice or optional components
- No localization requirements mentioned
- Single technology/integration mentioned
- Limited scope: affects 1-2 business domains
- User describes unified workflow or process

#### Multi-Addon Indicators
- Feature spans multiple business domains (e.g., "complete e-commerce solution")
- User mentions optional features, customer choice, or "some customers might want..."
- Localization requirements: different countries, languages, regulations
- Multiple technology choices: payment gateways, shipping providers, external integrations
- User describes different customer segments or deployment scenarios
- Feature includes both core functionality and optional enhancements

### Assessment Questions to Ask User (if unclear)
1. **Customer Flexibility**: "Will customers need to choose which parts of this feature to install?"
2. **Localization**: "Will this feature need country or region-specific adaptations?"
3. **Technology Choices**: "Will customers choose between different payment/shipping/integration providers?"
4. **Deployment Scenarios**: "Will different customers use different parts of this feature?"
5. **Business Domains**: "Does this feature affect multiple areas of the business (sales, inventory, accounting, etc.)?"

## Odoo Development Standards

## [SECTION_3_NAME]
<!-- Example: Odoo Development Workflow, Review Process, Quality Gates, etc. -->

[SECTION_3_CONTENT]
<!-- Example: Odoo addon review requirements, pylint-odoo testing gates, Odoo staging/production deployment approval process, migration script validation, etc. -->

## Governance
<!-- Example: Constitution supersedes all other Odoo practices; Amendments require documentation, approval, migration plan -->

> **Odoo-Specific Considerations**: All governance rules should account for Odoo's unique development ecosystem, including OCA community standards, addon dependency management, and Odoo's release cycle compatibility requirements.

[GOVERNANCE_RULES]
<!-- Example: All PRs/reviews must verify Odoo compliance and OCA standards; Deviations from standard Odoo patterns must be justified; Use [GUIDANCE_FILE] for runtime Odoo development guidance; Security changes require Odoo-specific review -->

**Version**: [CONSTITUTION_VERSION] | **Ratified**: [RATIFICATION_DATE] | **Last Amended**: [LAST_AMENDED_DATE]
<!-- Example: Version: 1.0.0 | Ratified: 2025-09-22 | Last Amended: 2025-09-22 -->