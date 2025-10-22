# Implementation Plan: Bicep Generator Command

**Branch**: `002-bicep-generator-command` | **Date**: 2025-10-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-bicep-generator-command/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a new GitHub Copilot command that automates the generation of Azure Bicep templates from project analysis. The system will analyze project files, ask intelligent questions about deployment requirements, and generate production-ready Bicep templates organized by resource type with environment-specific parameter files. Templates will be validated using Azure Resource Manager and prepared for Ev2 deployment integration.

## Technical Context

**Language/Version**: PowerShell 5.1+ and Python 3.11+ (for MCP Server integration)  
**Primary Dependencies**: Azure MCP Server, Azure CLI, Bicep CLI, PowerShell modules (Az.Resources, Az.Profile)  
**Storage**: File system for template generation, Azure Resource Manager for validation  
**Testing**: Pester for PowerShell scripts, pytest for Python components, ARM template validation  
**Target Platform**: Windows, macOS, Linux (cross-platform PowerShell support)
**Project Type**: CLI tool integration with GitHub Copilot  
**Performance Goals**: Template generation under 10 minutes, validation under 2 minutes  
**Constraints**: Must integrate with existing Azure MCP Server, preserve manual customizations, offline-capable analysis  
**Scale/Scope**: Support projects up to 1000 files, generate 20+ resource templates, handle 3 environments

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principles Compliance

- **✅ Code Simplicity and Clarity**: PowerShell scripts for local operations, clear separation between analysis and generation phases
- **✅ Root Cause Solutions**: Addresses fundamental need for automated infrastructure template generation rather than manual template creation
- **✅ Explicit Failure Over Silent Defaults**: ARM validation will fail explicitly on template errors, no silent fallbacks during analysis
- **✅ Early and Fatal Error Handling**: Clear error messages when Azure MCP Server unavailable, project analysis fails, or validation errors occur
- **✅ Iterative Development Approach**: MVP focuses on basic template generation (P1), then incremental updates (P2), then optimization (P3)
- **✅ Minimal and Focused Changes**: Single command focused on Bicep template generation, clear scope boundaries
- **✅ Engineering Excellence Through Simplicity**: Leverages existing Azure MCP Server, avoids complex object hierarchies, functional approach to template generation

### Constitutional Compliance Re-evaluation (Post-Design)

**✅ All principles maintained after detailed design**:

- **Code Simplicity**: Clear separation between PowerShell orchestration, Python MCP integration, and file operations
- **Root Cause Solutions**: Addresses fundamental infrastructure-as-code automation rather than manual template creation
- **Explicit Failures**: ARM validation provides clear error messages, no silent fallbacks in template generation
- **Early Error Handling**: Validation occurs at multiple stages (syntax, schema, deployment) with clear feedback
- **Iterative Development**: Phased approach (P1: generation, P2: updates, P3: optimization) enables incremental delivery
- **Minimal Changes**: Focused scope on Bicep template generation, clear boundaries with Ev2 deployment
- **Engineering Excellence**: Leverages proven Azure patterns, follows infrastructure-as-code best practices

**No constitutional violations introduced during design phase.**

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── specify_cli/
│   ├── commands/
│   │   └── bicep_generator.py      # New command implementation
│   ├── bicep/
│   │   ├── analyzer.py             # Project analysis logic
│   │   ├── generator.py            # Template generation orchestrator
│   │   ├── validator.py            # ARM validation integration
│   │   └── mcp_client.py           # Azure MCP Server client
│   └── utils/
│       ├── file_scanner.py         # Project file analysis
│       └── template_manager.py     # Template organization and backup

scripts/
├── powershell/
│   ├── bicep-generate.ps1          # Main PowerShell entry point
│   ├── bicep-validate.ps1          # Template validation script
│   └── bicep-update.ps1            # Incremental update script
└── bash/
    └── [equivalent bash scripts for cross-platform support]

templates/
├── bicep/
│   ├── base-templates/             # Base Bicep template patterns
│   └── parameter-files/            # Environment parameter file templates
└── commands/
    └── bicep-generate.md           # GitHub Copilot command definition

tests/
├── unit/
│   ├── test_analyzer.py            # Project analysis tests
│   ├── test_generator.py           # Template generation tests
│   └── test_validator.py           # Validation logic tests
├── integration/
│   ├── test_mcp_integration.py     # Azure MCP Server integration tests
│   └── test_end_to_end.py          # Full workflow tests
└── fixtures/
    └── sample_projects/            # Test project samples
```

**Structure Decision**: Extended the existing Specify CLI structure to include the new Bicep generation functionality. This leverages the existing Python CLI framework while adding specialized modules for Azure Bicep template generation, PowerShell script integration, and MCP Server communication.

## Complexity Tracking

No constitutional violations detected - complexity tracking not required.

