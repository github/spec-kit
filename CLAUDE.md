# Spec-Kit Project - AI Agent Context

This is the **spec-kit** project - a specification-driven development toolkit that provides MCP (Model Context Protocol) server and CLI tools for creating, managing, and implementing software specifications.

## Project Overview
Spec-kit enables specification-driven development where specifications drive implementation rather than the other way around. It provides:
- MCP server for AI agent integration
- CLI tools for project initialization and management  
- Onboarding tools for existing projects
- Templates and workflows for spec-driven development

## Available Commands
When connected via MCP, you have access to these tools:
- `/specify` - Create new feature specifications
- `/plan` - Generate implementation plans from specifications
- `/tasks` - Create task breakdowns from plans

## Current Development Status
- ✅ MCP server implementation complete
- ✅ CLI tools functional
- ✅ Onboarding tools implemented
- 🚧 **Currently onboarding spec-kit on itself** (branch: `000-spec-kit-self-specification`)

## Active Feature Branch
**Branch**: `000-spec-kit-self-specification`
**Purpose**: Create proper specification for spec-kit using its own methodology
**Status**: In progress - specification and plan created, ready for task generation

## Project Structure
```
spec-kit/
├── src/spec_kit_mcp/          # Core implementation
├── specs/                     # Feature specifications
├── templates/                 # Spec-kit templates
├── memory/                    # Constitutional documents
├── scripts/                   # Cross-platform scripts
└── pyproject.toml            # Project configuration
```

## Constitutional Principles
This project follows constitutional development principles:
- **Test-First**: Tests before implementation
- **Library-First**: Features as standalone libraries
- **Simplicity**: Max 3 projects, no future-proofing
- **Anti-Abstraction**: Direct framework usage
- **Integration-First**: Real environments over mocks

## Development Workflow
1. Specifications define WHAT and WHY (not HOW)
2. Implementation plans translate specs to technical decisions
3. Tasks break down plans into executable steps
4. Constitutional gates ensure quality and simplicity

## Notes for AI Agents
- This project practices what it preaches (dogfooding)
- Follow the spec-kit methodology when working on spec-kit
- Use existing templates and constitutional guidelines
- Maintain cross-platform compatibility (Windows, Linux, macOS)
- Bug fixes should be minimal and targeted