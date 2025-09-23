---
description: Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute.
2. Load and analyze available Odoo design documents:
   - Always read plan.md for addon strategy and Odoo version
   - IF EXISTS: Read odoo-architecture.md for addon decomposition and models
   - IF EXISTS: Read models/ for Odoo model definitions
   - IF EXISTS: Read views/ for XML view specifications
   - IF EXISTS: Read security/ for access rights and record rulesnahita
   
   - IF EXISTS: Read demo/ for sample data requirements
   - IF EXISTS: Read research.md for technical decisions
   - IF EXISTS: Read quickstart.md for test scenarios

   Note: Documents vary based on single vs multi-addon strategy:
   - Single addon: Comprehensive documentation in single set
   - Multi-addon: Separate documentation per addon
   - Generate tasks based on chosen strategy and available artifacts

3. Generate Odoo-specific tasks following the template:
   - Use `/templates/tasks-template.md` as the base
   - Replace example tasks with Odoo development tasks based on chosen strategy:

   **For Single Addon Strategy**:
     * **Setup tasks**: Addon structure, __manifest__.py, dependencies
     * **Model tasks [P]**: Define models in Python with proper inheritance
     * **View tasks [P]**: Create XML views (form, list, kanban, search)
     * **Security tasks [P]**: Configure access rights and record rules
     * **Demo tasks [P]**: Create sample data files
     * **Test tasks**: Unit tests for models, integration tests for workflows
     * **OWL/JS tasks**: Build JavaScript components if needed
     * **Migration tasks**: Version upgrade scripts
     * **Package tasks**: Ensure install/uninstall works properly

   **For Multi-Addon Strategy**:
     * **Per-Addon Setup**: Addon structure and manifest for each addon
     * **Dependency Order**: Core addon → Extension → Integration → Localization
     * **Cross-Addon Integration**: Shared models, event hooks, API contracts
     * **Addon-Specific**: Models, views, security, demo data per addon
     * **Integration Testing**: Cross-addon functionality and data flow
     * **Package Suite**: Ensure all addons work together

4. Odoo task generation rules:
   - Each Odoo model → Python model file task marked [P]
   - Each model → unit test task marked [P]
   - Each view type per model → XML view file task marked [P]
   - Each security group → access rights task marked [P]
   - Each record rule → record rule configuration task marked [P]
   - Each demo data set → XML data file task marked [P]
   - Each OWL component → JavaScript component task marked [P]
   - Each user workflow → integration test task marked [P]
   - Each addon → manifest.py and __init__.py task
   - Each migration → upgrade script task
   - Different addons = can be parallel [P] (if independent)
   - Same addon components = may be parallel [P] if different files
   - Inter-addon dependencies = sequential ordering

5. Order Odoo tasks by dependencies:

   **For Single Addon Strategy**:
   - Addon setup (__manifest__.py, __init__.py, directory structure)
   - Model tests (TDD approach)
   - Model implementation (Python files)
   - View XML files (depends on models)
   - Security configuration (depends on models and views)
   - Demo data (depends on models)
   - OWL/JS components (depends on views)
   - Integration tests (depends on complete functionality)
   - Migration scripts
   - Package validation (install/uninstall)

   **For Multi-Addon Strategy**:
   - Base/shared addon setup (if applicable)
   - Core addon: Models → Views → Security → Demo
   - Extension addons: Models → Views → Security → Demo
   - Integration addons: API connections → Controllers → Tests
   - Localization addons: Data → Translations
   - Cross-addon integration tests
   - Package suite validation

6. Include Odoo parallel execution examples:
   - Group [P] tasks that can run together based on Odoo development patterns
   - Show actual Task agent commands for Odoo-specific workflows

   **Parallel Task Examples**:
   - Multiple independent model files can be created simultaneously
   - Different view types for the same model (form, list, kanban) can be parallel
   - Security access rights for different models can be parallel
   - Demo data for different models can be parallel
   - Unit tests for different models can be parallel
   - Independent addon development (in multi-addon strategy)

7. Create FEATURE_DIR/tasks.md with Odoo-specific requirements:
   - Correct feature name and addon strategy from implementation plan
   - Numbered tasks (T001, T002, etc.) following Odoo development workflow
   - Clear file paths for each Odoo component (models/, views/, security/, demo/, etc.)
   - Odoo-specific dependency notes (model inheritance, view dependencies, etc.)
   - Addon-aware parallel execution guidance
   - Odoo version compatibility notes
   - Migration and upgrade considerations

**Task Specificity Requirements**:
- Each task must specify exact Odoo model classes, field definitions, and inheritance
- XML view tasks must include view types (form, list, kanban, search) and target models
- Security tasks must specify exact groups, access rights, and record rule conditions
- Demo data tasks must reference specific models and realistic business scenarios
- Test tasks must cover Odoo-specific testing patterns (TransactionCase, HttpCase, tours)
- Package tasks must validate Odoo addon structure and dependencies

Context for task generation: {ARGS}

The tasks.md should be immediately executable by an LLM familiar with Odoo development patterns.
