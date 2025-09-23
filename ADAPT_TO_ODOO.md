# Adapting Spec Kit for Odoo ERP Development

## Overview

This document outlines the plan to adapt the GitHub Spec Kit project to focus specifically on Odoo ERP (version 18 and later) development. The adaptation will modify the existing framework to provide Odoo-specific templates, workflows, and tooling while maintaining the core Spec-Driven Development methodology.

## Current Spec Kit Structure Analysis

The current Spec Kit provides a generic framework for Spec-Driven Development that supports multiple AI agents and programming languages. Key components include:

1. **CLI Tool** (`src/specify_cli/__init__.py`) - Bootstraps projects with agent-specific templates
2. **Templates** (`templates/`) - Specification, plan, and task templates
3. **Scripts** (`scripts/`) - Bash and PowerShell scripts for workflow automation
4. **Command Templates** (`templates/commands/`) - Agent-specific slash commands
5. **Constitution** (`memory/constitution.md`) - Core development principles
6. **Release Packaging** (`.github/workflows/scripts/`) - Template generation for different agents

## Odoo-Specific Adaptation Points

### 1. Core Project Structure Modifications

**Files to Modify:**
- `src/specify_cli/__init__.py` (lines 66-78, 1009-1021) - AI_CHOICES and agent_folder_map
- `pyproject.toml` - Project metadata

**Changes:**
- Add Odoo-specific AI agent support
- Update project description to focus on Odoo development
- Modify versioning to reflect Odoo adaptation

### 2. Template Adaptations

**Files to Modify:**
- `templates/spec-template.md` - Odoo-specific feature specification template
- `templates/plan-template.md` - Odoo implementation planning template
- `templates/tasks-template.md` - Odoo task breakdown template
- `memory/constitution.md` - Odoo development principles

**Changes:**
- Replace generic technology sections with Odoo-specific ones:
  - Language/Version: Python 3.11 with Odoo Framework
  - Primary Dependencies: Odoo 18+, PostgreSQL
  - Storage: PostgreSQL with Odoo ORM
  - Testing: Odoo Testing Framework (unittest2)
  - Target Platform: Odoo 18+ Enterprise/Community
  - Project Type: Odoo Module
- Add Odoo modules, models, views, and workflows
- Include Odoo ORM patterns and best practices
- Add Odoo-specific testing approaches
- Include Odoo security access rules and groups
- Add Odoo data import/export specifications
- Include Odoo internationalization requirements

### 3. Script Modifications

**Files to Modify:**
- `scripts/bash/create-new-feature.sh` - Odoo feature branch naming
- `scripts/bash/update-agent-context.sh` - Odoo context handling
- `scripts/bash/setup-plan.sh` - Odoo plan setup
- `scripts/bash/common.sh` - Odoo path resolution
- PowerShell equivalents

**Changes:**
- Adapt feature numbering for Odoo modules
- Add Odoo-specific directory structures
- Include Odoo development environment checks

### 4. Command Template Adaptations

**Files to Modify:**
- `templates/commands/specify.md` - Odoo feature specification
- `templates/commands/plan.md` - Odoo implementation planning
- `templates/commands/tasks.md` - Odoo task generation
- `templates/commands/implement.md` - Odoo implementation execution
- `templates/commands/constitution.md` - Odoo principles establishment

**Changes:**
- Update script references for Odoo workflows
- Add Odoo-specific command arguments
- Include Odoo development context

### 5. Agent Integration

**Files to Modify:**
- `.github/workflows/scripts/create-release-packages.sh` (lines 140-175) - Odoo agent template generation
- `.github/workflows/scripts/create-github-release.sh` - Release packaging

**Changes:**
- Add Odoo-specific agent configurations
- Create Odoo command directory structures
- Generate Odoo-specific prompt files

## Detailed File Modifications

### Core CLI (`src/specify_cli/__init__.py`)

**Lines to Modify:**
- 66-78: AI_CHOICES - Add Odoo-specific agent options
- 1009-1021: agent_folder_map - Add Odoo folder mappings

**Additions:**
- Odoo development environment checks
- Odoo version compatibility validation

### Templates

#### Specification Template (`templates/spec-template.md`)

**Odoo-Specific Sections:**
- Odoo Module Requirements
- Model Definitions (with Odoo ORM fields)
- View Specifications (Form, Tree, Kanban, Search views)
- Workflow Definitions (Automated actions, server actions)
- Security Access Rules (Groups, Record rules)
- Data Import/Export Requirements
- Report Specifications
- Wizard Requirements
- API Endpoint Specifications
- Internationalization Requirements

#### Plan Template (`templates/plan-template.md`)

**Odoo-Specific Sections:**
- Module Structure Planning (manifest, init files)
- Model Inheritance Planning (Odoo ORM patterns)
- View Architecture (XML view definitions)
- Workflow Implementation (Automated actions, server actions)
- Security Implementation (Access rights, Record rules)
- Data Migration Planning (XML data files)
- Report Implementation Planning
- Wizard Implementation Planning
- API Endpoint Planning
- Testing Strategy (Unit, Integration, Functional tests)

#### Task Template (`templates/tasks-template.md`)

**Odoo-Specific Tasks:**
- Module Creation (manifest, init files)
- Model Implementation (Python classes with Odoo ORM)
- View Development (XML view definitions)
- Workflow Setup (Automated actions, server actions)
- Security Configuration (Access rights, Record rules)
- Data Migration Implementation (XML data files)
- Report Implementation
- Wizard Implementation
- API Endpoint Implementation
- Testing Implementation (Unit, Integration, Functional tests)
- Documentation Creation
- Internationalization Implementation

### Scripts

#### Feature Creation (`scripts/bash/create-new-feature.sh`)

**Odoo Adaptations:**
- Feature naming: `001_module_name` instead of generic naming
- Odoo module directory structure creation
- Odoo manifest file initialization

#### Agent Context (`scripts/bash/update-agent-context.sh`)

**Odoo Additions:**
- Odoo version tracking
- Module dependency management
- Odoo development environment context

### Command Templates

#### Specify Command (`templates/commands/specify.md`)

**Odoo Context:**
- Odoo module specification focus
- Model and view requirements extraction
- Odoo-specific user story format

#### Plan Command (`templates/commands/plan.md`)

**Odoo Workflow:**
- Odoo module architecture planning
- Model inheritance strategies
- View and workflow implementation planning

## Odoo-Specific Directory Structure

```
odoo_project/
├── addons/
│   └── custom_modules/
│       └── [module_name]/
│           ├── __init__.py
│           ├── __manifest__.py
│           ├── models/
│           │   ├── __init__.py
│           │   └── [model_files].py
│           ├── views/
│           │   └── [view_files].xml
│           ├── security/
│           │   ├── ir.model.access.csv
│           │   └── [security_files].xml
│           ├── data/
│           │   └── [data_files].xml
│           ├── static/
│           │   ├── src/
│           │   │   ├── js/
│           │   │   ├── css/
│           │   │   └── xml/
│           │   └── description/
│           │       └── icon.png
│           ├── controllers/
│           │   ├── __init__.py
│           │   └── [controller_files].py
│           ├── wizards/
│           │   ├── __init__.py
│           │   └── [wizard_files].py
│           ├── reports/
│           │   ├── __init__.py
│           │   └── [report_files].py
│           └── tests/
│               ├── __init__.py
│               └── [test_files].py
├── specs/
│   └── [###-module-name]/
│       ├── spec.md
│       ├── plan.md
│       ├── research.md
│       ├── data-model.md
│       ├── contracts/
│       ├── quickstart.md
│       └── tasks.md
├── .specify/
│   ├── memory/
│   ├── scripts/
│   └── templates/
├── odoo.conf
└── docker-compose.yml
```

## Odoo Development Workflow Integration

### Phase 1: Module Specification
- Define Odoo module requirements and scope
- Specify models with fields and relationships
- Define view specifications (Form, Tree, Kanban, Search)
- Specify workflows and business logic
- Define security access rules and groups
- Specify data import/export requirements
- Define report and wizard requirements

### Phase 2: Implementation Planning
- Plan module directory structure with Odoo conventions
- Design model inheritance and ORM patterns
- Plan view architectures (XML definitions)
- Plan workflow implementations (Automated actions)
- Plan security implementations (Access rights, Record rules)
- Plan data migration strategies (XML data files)
- Plan testing approach (Unit, Integration, Functional)

### Phase 3: Task Generation
- Generate implementation tasks for module creation
- Create model implementation tasks
- Generate view development tasks
- Create workflow setup tasks
- Generate security configuration tasks
- Create data migration implementation tasks
- Generate testing implementation tasks

### Phase 4: Implementation Execution
- Execute module development following Odoo conventions
- Implement models with Odoo ORM
- Develop views with XML definitions
- Setup workflows with automated actions
- Configure security with access rights
- Implement data migrations
- Execute testing with Odoo testing framework

## Opininated Elements to Replace

### Generic Technology Choices
Replace generic technology sections with Odoo-specific ones:
- Python → Python 3.11 with Odoo Framework
- Web frameworks → Odoo Web Framework
- Databases → PostgreSQL with Odoo ORM
- Testing → Odoo Testing Framework (unittest2)
- Generic project structure → Odoo module structure

### Generic Project Structure
Replace with Odoo module structure:
- src/ → addons/custom_modules/
- Standard web structure → Odoo module structure with models, views, security, data directories
- Generic testing → Odoo unit and integration testing in tests/ directory

### Generic Development Principles
Update constitution with Odoo principles:
- Odoo Module Development Guidelines
- Odoo ORM Best Practices
- Odoo Security Model Implementation
- Odoo Internationalization Requirements
- Odoo Testing Framework Usage

## Implementation Steps

1. **Update Core CLI** - Add Odoo agent support and project initialization
2. **Create Odoo Templates** - Develop Odoo-specific specification, plan, and task templates
3. **Adapt Scripts** - Modify bash/PowerShell scripts for Odoo workflows
4. **Update Command Templates** - Create Odoo-specific slash commands
5. **Modify Release Packaging** - Add Odoo agent template generation
6. **Update Documentation** - Adapt README and other documentation for Odoo focus
7. **Testing** - Verify Odoo-specific project initialization and workflows

## Files Requiring Modification (With Line Numbers)

### Core Files
1. `src/specify_cli/__init__.py`
   - Lines 66-78: AI_CHOICES dictionary
   - Lines 1009-1021: agent_folder_map dictionary
   - Lines 748-1077: init function - Odoo-specific options

2. `pyproject.toml`
   - Lines 1-13: Project metadata update

### Template Files
3. `templates/spec-template.md`
   - Full file adaptation for Odoo specifications

4. `templates/plan-template.md`
   - Full file adaptation for Odoo planning

5. `templates/tasks-template.md`
   - Full file adaptation for Odoo tasks

6. `memory/constitution.md`
   - Full file adaptation for Odoo principles

### Script Files
7. `scripts/bash/create-new-feature.sh`
   - Lines 70-72: Feature naming for Odoo modules
   - Lines 83-85: Template copying for Odoo

8. `scripts/bash/update-agent-context.sh`
   - Lines 62-71: Agent file paths
   - Lines 177-180: Plan parsing for Odoo context

9. `scripts/bash/setup-plan.sh`
   - Full file adaptation for Odoo planning

10. `scripts/bash/common.sh`
    - Lines 84-109: Path resolution for Odoo structure

### Command Template Files
11. `templates/commands/specify.md`
    - Lines 4-5: Script references
    - Lines 16-22: Odoo-specific instructions

12. `templates/commands/plan.md`
    - Lines 4-5: Script references
    - Lines 16-43: Odoo-specific planning instructions

13. `templates/commands/tasks.md`
    - Lines 4-5: Script references
    - Lines 14-30: Odoo-specific task generation

14. `templates/commands/implement.md`
    - Lines 4-5: Script references
    - Lines 15-36: Odoo-specific implementation

15. `templates/commands/constitution.md`
    - Lines 4-5: Script references
    - Lines 14-26: Odoo-specific constitution creation

### Release Packaging Files
16. `.github/workflows/scripts/create-release-packages.sh`
    - Lines 140-175: Case statement for Odoo agent
    - Lines 181: ALL_AGENTS array

17. `.github/workflows/scripts/create-github-release.sh`
    - Lines where agent packages are referenced

## Conclusion

This adaptation plan focuses the Spec Kit framework on Odoo ERP development while maintaining the core Spec-Driven Development methodology. The changes will provide Odoo-specific templates, workflows, and tooling that align with Odoo development best practices and conventions.