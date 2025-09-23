---
description: "Implementation plan template for feature development"
scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
[Extract from feature spec: primary requirement + technical approach from research]

## Odoo Technical Context
**Odoo Version**: [e.g., Odoo 17.0, Odoo 18.0, Odoo 19.0 or NEEDS CLARIFICATION]
**Addon Strategy**: [Single Addon / Multi-Addon based on constitutional assessment or NEEDS CLARIFICATION]
**Strategy Rationale**: [Why this strategy was chosen or NEEDS CLARIFICATION]

### If Single Addon Strategy:
**Addon Name**: [comprehensive addon name and business domain or NEEDS CLARIFICATION]
**Core Dependencies**: [required Odoo modules or NEEDS CLARIFICATION]
**Optional Dependencies**: [optional Odoo modules that enhance functionality or NEEDS CLARIFICATION]
**Feature Scope**: [complete feature group within single addon or NEEDS CLARIFICATION]

### If Multi-Addon Strategy:
**Core Addon**: [base addon name and primary business domain or NEEDS CLARIFICATION]
**Extension Addons**: [list of optional enhancement addons or NEEDS CLARIFICATION]
**Integration Addons**: [technology-specific addons (payments, shipping, etc.) or NEEDS CLARIFICATION]
**Localization Addons**: [region-specific addons or NEEDS CLARIFICATION]
**Inter-Addon Dependencies**: [dependencies between custom addons or NEEDS CLARIFICATION]
**Customer Flexibility**: [which addons are optional vs required or NEEDS CLARIFICATION]

### Common Context:
**Testing Strategy**: [unit, integration, cross-addon tests (if applicable) or NEEDS CLARIFICATION]
**Deployment Target**: [Odoo.sh, on-premise, containerized or NEEDS CLARIFICATION]
**Performance Goals**: [concurrent users, data volume, response times or NEEDS CLARIFICATION]
**Migration Path**: [addon-specific upgrade strategies or NEEDS CLARIFICATION]

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Odoo Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── odoo-architecture.md # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── models/              # Phase 1 output (/plan command)
├── views/               # Phase 1 output (/plan command)
├── security/            # Phase 1 output (/plan command)
├── demo/                # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Odoo Addon Structure
**Structure based on chosen strategy**

#### If Single Addon Strategy:
```
# Single Addon Project Structure
addons/
└── [addon_name]/               # Comprehensive addon with complete feature group
    ├── __init__.py
    ├── __manifest__.py
    ├── models/
    │   ├── __init__.py
    │   └── [all_models].py
    ├── views/
    │   ├── [all_views].xml
    │   └── menu.xml
    ├── security/
    │   ├── ir.model.access.csv
    │   └── security_groups.xml
    ├── data/
    │   └── [configuration].xml
    ├── demo/
    │   └── [demo_data].xml
    ├── static/description/
    ├── tests/
    │   ├── __init__.py
    │   ├── test_[feature_group].py
    │   └── test_tours.js
    └── i18n/
        ├── [addon_name].pot
        └── [lang_code].po
```

#### If Multi-Addon Strategy:
```
# Multi-Addon Project Structure
addons/
├── [core_addon_name]/           # Core business logic addon
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── [core_models].py
│   ├── views/
│   │   ├── [core_views].xml
│   │   └── menu.xml
│   ├── security/
│   ├── data/
│   ├── demo/
│   ├── static/description/
│   ├── tests/
│   └── i18n/
│
├── [extension_addon_name]/      # Optional enhancement addon
│   ├── __manifest__.py          # depends on core_addon_name
│   ├── models/
│   │   └── [extended_models].py
│   ├── views/
│   │   └── [enhanced_views].xml
│   ├── tests/
│   │   └── test_integration.py  # Tests with core addon
│   └── [standard structure]
│
├── [integration_addon_name]/    # Technology-specific addon
│   ├── __manifest__.py          # depends on core_addon_name
│   ├── models/
│   │   └── [integration_models].py
│   ├── controllers/
│   │   └── [api_controllers].py
│   ├── tests/
│   │   └── test_external_api.py
│   └── [standard structure]
│
└── [localization_addon_name]/   # Country/region-specific
    ├── __manifest__.py          # depends on core_addon_name
    ├── data/
    │   └── [country_data].xml
    ├── i18n/
    │   ├── [locale].po
    │   └── [locale].pot
    └── [standard structure]
```

**Structure Decision**: [Single/Multi]-addon architecture following constitutional assessment

## Phase 0: Odoo Module Research
1. **Extract unknowns from Odoo Technical Context** above:
   - For each NEEDS CLARIFICATION → Odoo-specific research task
   - For each core module dependency → best practices and API documentation
   - For each custom requirement → Odoo framework patterns and conventions

2. **Generate and dispatch Odoo research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for Odoo {version} development"
   For each core module dependency:
     Task: "Find Odoo {module} best practices and available models/fields"
   For each custom model/view:
     Task: "Research Odoo framework patterns for {component_type}"
   ```

3. **Consolidate Odoo findings** in `research.md` using format:
   - **Odoo Version Decision**: [version chosen and compatibility requirements]
   - **Module Dependencies**: [core modules confirmed and their APIs]
   - **Data Model Approach**: [inheritance vs new models, field types]
   - **View Strategy**: [standard views vs custom, OWL component needs]
   - **Security Model**: [access groups, record rules, field security]
   - **Testing Approach**: [unit tests, integration tests, tour tests]
   - **Deployment Strategy**: [packaging, dependencies, upgrade path]
   - **Performance Considerations**: [indexing, lazy loading, batch operations]

**Output**: research.md with all Odoo NEEDS CLARIFICATION resolved

## Phase 1: Odoo Architecture Design
*Prerequisites: research.md complete*

1. **Confirm addon strategy from spec** → `odoo-architecture.md`:
   - Validate single vs multi-addon decision from constitutional assessment
   - Document rationale for chosen strategy
   - Identify coherent feature groups and addon boundaries

2. **Design addon architecture** → `/models/`, `/views/`, `/security/`, `/demo/`:
   **If Single Addon Strategy**:
   - Complete addon with all models, views, and functionality
   - Internal feature organization and configuration options
   - Comprehensive security model and demo data

   **If Multi-Addon Strategy**:
   - **Core Addon**: Base models, primary business logic, essential views
   - **Extension Addons**: Enhanced features, additional views, optional functionality
   - **Integration Addons**: External API connections, payment gateways, third-party services
   - **Localization Addons**: Country-specific data, translations, regulatory compliance

3. **Define integration strategy**:
   **For Single Addon**: Internal module organization and configuration
   **For Multi-Addon**: Cross-addon integration points:
   - Shared abstract models and mixins
   - Event hooks and signals for addon communication
   - API contracts between addons
   - Data flow and synchronization patterns

4. **Plan testing strategy**:
   **For Single Addon**:
   - **Unit Tests**: All models, methods, and business logic
   - **Integration Tests**: Complete workflows and feature interactions
   - **Configuration Tests**: Different settings and options

   **For Multi-Addon**:
   - **Isolation Tests**: Each addon tested independently
   - **Integration Tests**: Cross-addon functionality and data flow
   - **Configuration Tests**: Various addon combination scenarios
   - **Migration Tests**: Addon upgrade and dependency changes

5. **Design deployment approach**:
   **For Single Addon**: Configuration-based feature enablement
   **For Multi-Addon**: Multiple installation scenarios and customer choice

6. **Update agent file incrementally** (O(1) operation):
   - Run `{SCRIPT}`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW Odoo tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: odoo-architecture.md, addon-specific /models/*, /views/*, /security/*, /demo/*, test plans, deployment approach, quickstart.md, agent-specific file

## Phase 2: Odoo Development Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Adaptive Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks based on chosen addon strategy from Phase 1

**For Single Addon Strategy**:
- **Single Comprehensive Addon**: Manifest → Models → Views → Security → Demo Data → Tests
- **Feature Group Organization**: Organize tasks by functional areas within the addon
- **Configuration Tasks**: Settings and feature toggles within the addon
- **Complete Testing**: Unit and integration tests for all functionality

**For Multi-Addon Strategy**:
- **Per Addon**: Manifest → Models → Views → Security → Demo Data → Tests [P]
- **Cross-Addon**: Integration tests, deployment configurations
- **Dependency Order**: Core addon → Extension addons → Integration addons → Localization addons
- **Optional Addons**: Marked clearly for customer choice

**Ordering Strategy**:
- **TDD Approach**: Tests before implementation (within addon or across addons)
- **Dependency Order**: Based on Odoo modules and inter-addon dependencies
- **Parallel Execution**: Independent components marked [P]
- **Deployment Scenarios**: Tasks for different customer configurations

**Estimated Output**:
- Single Addon: 10-15 numbered, comprehensive tasks
- Multi-Addon: 35-50 numbered, distributed across addons

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Odoo Implementation & Deployment
*These phases are beyond the scope of the /plan command*

**Phase 3**: Odoo Task execution (/tasks command creates tasks.md)
- Execute Odoo-specific development tasks
- Follow Odoo coding standards and conventions
- Implement TDD with Odoo testing framework

**Phase 4**: Odoo Module Implementation (execute tasks.md following constitutional principles)
- Create __manifest__.py with proper dependencies
- Implement models with Odoo field types and constraints
- Design XML views following Odoo UI patterns
- Configure security groups and record rules
- Create demo data and migration scripts
- Implement OWL components if needed

**Phase 5**: Odoo Testing & Validation Strategy
- **Unit Testing**: Test model methods, constraints, and computed fields using Odoo's TestCase
- **Integration Testing**: Test complete business workflows and module interactions
- **Tour Testing**: Test UI interactions using Odoo's tour framework
- **Performance Testing**: Test with realistic data volumes and concurrent users
- **Migration Testing**: Verify upgrade path and data migration scripts
- **Security Testing**: Validate access controls and record rules

**Phase 6**: Odoo Deployment & Upgrade Path
- **Packaging**: Prepare addon for distribution (manifest, dependencies, description)
- **Environment Testing**: Validate on development, staging, and production-like environments
- **Deployment Strategy**:
  - Odoo.sh: Configure deployment pipeline
  - On-premise: Document installation and configuration steps
  - Containerized: Provide Docker configuration
- **Upgrade Path**: Document migration steps between versions
- **Rollback Plan**: Prepare rollback procedures for production
- **Performance Monitoring**: Set up monitoring for key metrics
- **Documentation**: Create user guides and technical documentation

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [ ] Phase 0: Odoo Module Research complete (/plan command)
- [ ] Phase 1: Odoo Architecture Design complete (/plan command)
- [ ] Phase 2: Odoo Task Planning complete (/plan command - describe approach only)
- [ ] Phase 3: Odoo Tasks generated (/tasks command)
- [ ] Phase 4: Odoo Module Implementation complete
- [ ] Phase 5: Odoo Testing & Validation passed
- [ ] Phase 6: Odoo Deployment & Documentation complete

**Gate Status**:
- [ ] Initial Constitution Check: PASS
- [ ] Post-Design Constitution Check: PASS
- [ ] All Odoo NEEDS CLARIFICATION resolved
- [ ] Odoo module dependencies validated
- [ ] Odoo security model approved
- [ ] Performance requirements defined
- [ ] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
