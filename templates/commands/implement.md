---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

The user input can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute.

2. Load and analyze the Odoo implementation context:
   - **REQUIRED**: Read tasks.md for the complete Odoo task list and execution plan
   - **REQUIRED**: Read plan.md for addon strategy, Odoo version, and addon structure
   - **IF EXISTS**: Read odoo-architecture.md for addon decomposition and model definitions
   - **IF EXISTS**: Read models/ for Odoo model specifications
   - **IF EXISTS**: Read views/ for XML view specifications
   - **IF EXISTS**: Read security/ for access rights and record rules
   - **IF EXISTS**: Read demo/ for sample data requirements
   - **IF EXISTS**: Read research.md for Odoo technical decisions and constraints
   - **IF EXISTS**: Read quickstart.md for Odoo workflow scenarios

3. Parse Odoo tasks.md structure and extract:
   - **Odoo Task phases**: Addon Setup, Model Tests, Models, Views, Security, Demo Data, OWL Components, Integration, Package Validation
   - **Addon dependencies**: Single vs multi-addon execution rules, inter-addon dependencies
   - **Task details**: ID, description, Odoo file paths (models/, views/, security/, etc.), parallel markers [P]
   - **Execution flow**: Odoo-specific order and dependency requirements (models before views, tests before implementation)

4. Execute Odoo implementation following the task plan:
   - **Phase-by-phase execution**: Complete each Odoo phase before moving to the next
   - **Respect addon dependencies**: Single vs multi-addon coordination, inter-addon dependencies
   - **Follow Odoo TDD**: Execute model test tasks before model implementation tasks
   - **Odoo file coordination**: Tasks affecting the same addon files must run sequentially
   - **Constitutional compliance**: Ensure each task respects constitutional principles
   - **Validation checkpoints**: Verify each Odoo phase completion and addon integrity before proceeding

5. Odoo implementation execution rules:
   - **Addon setup first**: Initialize addon directory structure, __manifest__.py, __init__.py, dependencies
   - **Odoo tests before code**: Write model tests (TransactionCase), integration tests, tour tests before implementation
   - **Odoo core development**: Implement Python models with proper inheritance, XML views, security configuration
   - **Odoo integration work**: Cross-addon integration, OWL components, external API connections
   - **Odoo validation and packaging**: Demo data, migration scripts, install/uninstall validation, constitutional compliance checks

   **Specific Odoo Artifact Requirements**:
   - **__manifest__.py**: Complete manifest with proper dependencies, version, description, data files
   - **Python models**: Proper Odoo model inheritance (models.Model, models.TransientModel), field definitions, constraints, methods
   - **XML files**: Well-formed views (form, list, kanban, search), menu structure, data files, security definitions
   - **JavaScript/OWL**: Proper OWL component structure, CSS, static file organization
   - **Tests**: Proper Odoo test structure (TransactionCase, HttpCase, tour tests) with realistic scenarios

6. Odoo progress tracking and error handling:
   - Report progress after each completed Odoo task with artifact confirmation
   - Halt execution if any non-parallel addon task fails (preserve addon integrity)
   - For parallel tasks [P], continue with successful tasks, report failed ones with Odoo-specific context
   - Provide clear Odoo error messages with context (model inheritance issues, view syntax, manifest errors)
   - Suggest Odoo-specific next steps if implementation cannot proceed (addon dependencies, Odoo version compatibility)
   - **IMPORTANT** For completed tasks, mark as [X] in tasks file and verify generated Odoo artifacts exist and are valid
   - **Constitutional Validation**: After each phase, verify constitutional compliance (addon complexity, dependency rules, customer flexibility)

7. Odoo completion validation:
   - Verify all Odoo tasks are completed and marked [X] in tasks.md
   - Check that implemented Odoo features match the original specification
   - Validate that all Odoo tests pass (unit, integration, tour tests) and coverage meets requirements
   - Confirm the implementation follows the Odoo technical plan and constitutional principles
   - **Addon Integrity Validation**:
     * All addons have complete __manifest__.py files
     * All models have required views (minimum form and list)
     * All security groups and access rights are properly defined
     * Demo data is realistic and functional
     * Install/uninstall process works correctly
   - **Constitutional Compliance Check**:
     * Addon complexity within limits (~10 models, ~10 views, ~10 OWL components per addon)
     * Customer deployment flexibility maintained (core vs optional addons)
     * Inter-addon dependencies properly managed
     * No circular dependencies between addons
   - Report final status with summary of completed Odoo artifacts and addon readiness for deployment

Note: This command assumes a complete Odoo task breakdown exists in tasks.md with proper addon strategy and constitutional compliance. If tasks are incomplete or missing, suggest running `/tasks` first to regenerate the Odoo-specific task list.

**Constitutional Reminder**: Throughout implementation, ensure all generated artifacts respect the constitutional principles:
- Addon architecture follows the chosen strategy (single vs multi-addon)
- Feature groups are coherent and within complexity limits
- Customer deployment flexibility is maintained
- Inter-addon dependencies are explicit and well-documented
- Generated code is self-contained, versioned, and testable