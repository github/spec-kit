# Tasks: [FEATURE NAME]

**Input**: Odoo design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), odoo-architecture.md, models/, views/, security/
**Strategy**: [Single Addon / Multi-Addon] based on constitutional assessment

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: Odoo version, addon strategy, dependencies
2. Load Odoo-specific design documents:
   → odoo-architecture.md: Extract addon decomposition and model definitions
   → models/: Each model → Python model file task
   → views/: Each view specification → XML view task
   → security/: Extract groups and record rules → security tasks
   → demo/: Each data set → demo data task
   → research.md: Extract Odoo technical decisions → setup tasks
3. Generate Odoo tasks by category based on strategy:
   → Setup: Addon structure, __manifest__.py, __init__.py
   → Model Tests: Unit tests for each model (TDD)
   → Models: Python model files with proper Odoo inheritance
   → Views: XML views (form, list, kanban, search)
   → Security: Access rights and record rules
   → Demo: Sample data files
   → OWL/JS: JavaScript components if needed
   → Integration: Cross-addon tests, workflow tests
   → Migration: Upgrade scripts
   → Package: Install/uninstall validation
4. Apply Odoo task rules:
   → Different models/addons = mark [P] for parallel
   → Same addon components = may be parallel [P] if different files
   → Inter-addon dependencies = sequential ordering
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate Odoo dependency graph (addon dependencies, model inheritance)
7. Create parallel execution examples for Odoo development
8. Validate Odoo task completeness:
   → All models have tests and implementations?
   → All models have required views?
   → All security groups defined?
   → All addons properly structured?
9. Return: SUCCESS (Odoo tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Odoo Path Conventions
- **Single Addon**: `addons/[addon_name]/` structure
- **Multi-Addon**: `addons/[core_addon]/`, `addons/[extension_addon]/`, etc.
- **Standard Odoo Structure**: `models/`, `views/`, `security/`, `demo/`, `tests/`, `static/`
- Paths shown below adjust based on single vs multi-addon strategy from plan.md

## Phase 3.1: Odoo Addon Setup
- [ ] T001 Create addon directory structure per strategy (addons/[addon_name]/)
- [ ] T002 Create __manifest__.py with proper dependencies and metadata
- [ ] T003 [P] Create __init__.py files for Python module imports
- [ ] T004 [P] Configure Odoo development environment and linting

## Phase 3.2: Model Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These model tests MUST be written and MUST FAIL before ANY model implementation**
- [ ] T005 [P] Unit test for ProjectTask model in tests/test_project_task.py
- [ ] T006 [P] Unit test for ProjectAnalytics model in tests/test_project_analytics.py
- [ ] T007 [P] Integration test for analytics workflow in tests/test_analytics_workflow.py
- [ ] T008 [P] Tour test for UI interaction in tests/test_analytics_tour.js

## Phase 3.3: Odoo Models (ONLY after tests are failing)
- [ ] T009 [P] ProjectTask model with fields and methods in models/project_task.py
- [ ] T010 [P] ProjectAnalytics model with computed fields in models/project_analytics.py
- [ ] T011 [P] Model relationships and constraints validation
- [ ] T012 Add model methods and business logic

## Phase 3.4: Odoo Views
- [ ] T013 [P] ProjectTask form view in views/project_task_views.xml
- [ ] T014 [P] ProjectTask list view in views/project_task_views.xml
- [ ] T015 [P] ProjectAnalytics kanban view in views/project_analytics_views.xml
- [ ] T016 [P] Search views with filters and grouping
- [ ] T017 Menu structure and actions in views/menu.xml

## Phase 3.5: Security & Access
- [ ] T018 [P] Access rights in security/ir.model.access.csv
- [ ] T019 [P] Security groups in security/security_groups.xml
- [ ] T020 [P] Record rules for data access control
- [ ] T021 Field-level security permissions

## Phase 3.6: Demo Data & Localization
- [ ] T022 [P] Demo project tasks in demo/project_task_demo.xml
- [ ] T023 [P] Demo analytics data in demo/project_analytics_demo.xml
- [ ] T024 [P] Translation templates in i18n/[addon_name].pot
- [ ] T025 [P] Sample localization files

## Phase 3.7: OWL Components (if needed)
- [ ] T026 [P] Analytics dashboard OWL component in static/src/js/analytics_dashboard.js
- [ ] T027 [P] Custom widget for project metrics in static/src/js/project_widget.js
- [ ] T028 [P] CSS styling for custom components

## Phase 3.8: Integration & Migration
- [ ] T029 Cross-addon integration tests (if multi-addon strategy)
- [ ] T030 Data migration scripts in migrations/[version]/
- [ ] T031 Upgrade compatibility testing
- [ ] T032 Performance testing with realistic data volumes

## Phase 3.9: Package Validation
- [ ] T033 Verify addon install/uninstall process
- [ ] T034 Test addon dependencies and loading order
- [ ] T035 Validate __manifest__.py completeness
- [ ] T036 Run Odoo addon linting and quality checks

## Odoo Dependencies
- Addon setup (T001-T004) before everything
- Model tests (T005-T008) before model implementation (T009-T012)
- Models (T009-T012) before views (T013-T017)
- Models completed before security (T018-T021)
- Models and views before demo data (T022-T025)
- Basic functionality before OWL components (T026-T028)
- Core functionality before integration testing (T029-T032)
- Everything before package validation (T033-T036)

## Odoo Parallel Examples
```
# Launch model tests together:
Task: "Unit test for ProjectTask model in tests/test_project_task.py"
Task: "Unit test for ProjectAnalytics model in tests/test_project_analytics.py"
Task: "Integration test for analytics workflow in tests/test_analytics_workflow.py"

# Launch model implementations together (after tests fail):
Task: "ProjectTask model with fields and methods in models/project_task.py"
Task: "ProjectAnalytics model with computed fields in models/project_analytics.py"

# Launch view creation together (after models exist):
Task: "ProjectTask form view in views/project_task_views.xml"
Task: "ProjectAnalytics kanban view in views/project_analytics_views.xml"
Task: "Search views with filters and grouping"

# Launch security configuration together:
Task: "Access rights in security/ir.model.access.csv"
Task: "Security groups in security/security_groups.xml"
Task: "Record rules for data access control"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Avoid: vague tasks, same file conflicts

## Odoo Task Generation Rules
*Applied during main() execution*

1. **From Odoo Architecture**:
   - Each addon → setup tasks (__manifest__.py, __init__.py, structure)
   - Each model → model test task [P] + model implementation task [P]
   - Each model → required view tasks (form, list minimum)

2. **From Models Definition**:
   - Each model → Python model file task [P]
   - Model relationships → constraint and method tasks
   - Computed fields → specific computation tasks

3. **From Views Specification**:
   - Each view type → XML view file task [P]
   - Menu structure → menu.xml task
   - Actions → action definition tasks

4. **From Security Requirements**:
   - Each user group → security group task [P]
   - Each model → access rights task [P]
   - Data restrictions → record rule tasks [P]

5. **From Demo Data**:
   - Each data set → demo XML file task [P]
   - Sample scenarios → realistic demo data tasks

6. **Odoo Ordering**:
   - Setup → Model Tests → Models → Views → Security → Demo → OWL → Integration → Package
   - Addon dependencies block parallel execution
   - Cross-addon integration requires sequential ordering

## Odoo Validation Checklist
*GATE: Checked by main() before returning*

- [ ] All models have corresponding test tasks
- [ ] All models have required view tasks (minimum form and list)
- [ ] All model tests come before model implementation
- [ ] All security groups and access rights defined
- [ ] All addons have proper __manifest__.py tasks
- [ ] Parallel tasks truly independent (different files/addons)
- [ ] Each task specifies exact Odoo file path
- [ ] No task modifies same addon file as another [P] task
- [ ] Cross-addon dependencies properly ordered
- [ ] Install/uninstall validation included