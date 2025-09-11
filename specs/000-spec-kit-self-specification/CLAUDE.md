# Spec-Kit Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-09-11

## Active Technologies
- **Language**: Python 3.11+
- **CLI Framework**: Typer with Rich for UI
- **MCP Protocol**: Model Context Protocol for AI agent integration  
- **Package Management**: pip/setuptools with pyproject.toml
- **Cross-platform**: Windows, Linux, macOS support

## Project Structure
```
spec-kit/
├── src/spec_kit_mcp/          # Main MCP server and CLI code
│   ├── server.py              # MCP server implementation
│   ├── cli.py                 # CLI commands and interface
│   ├── onboarding.py          # Project onboarding functionality
│   └── scripts.py             # Cross-platform script management
├── specs/                     # Feature specifications
│   └── 000-spec-kit-self-specification/
│       ├── spec.md            # Main feature specification
│       ├── plan.md            # Implementation plan
│       └── analysis.json      # Onboarding analysis data
├── templates/                 # Spec-kit templates
│   ├── spec-template.md       # Feature specification template
│   ├── plan-template.md       # Implementation plan template
│   └── agent-file-template.md # Agent context template
├── memory/                    # Constitutional documents
│   ├── constitution.md        # Development principles
│   └── constitution_update_checklist.md
├── scripts/py/                # Cross-platform Python scripts
└── pyproject.toml            # Project configuration
```

## Commands

### Spec-Kit CLI Commands
- `specify init <project>` - Initialize new spec-driven project
- `specify check` - Check system requirements
- `specify scripts` - Show available scripts

### MCP Server Commands
Available when running `spec-kit-mcp`:
- `init_project` - Initialize new projects with templates
- `onboard_existing_project` - Analyze and onboard existing projects
- `create_new_feature` - Create feature branches with specifications
- `setup_plan` - Generate implementation plans
- `analyze_project_structure` - Analyze project organization
- `extract_feature_boundaries` - Identify feature boundaries for progressive onboarding

### Development Workflow
1. Create feature specification in `specs/###-feature-name/spec.md`
2. Generate implementation plan in `specs/###-feature-name/plan.md`
3. Follow constitutional principles from `/memory/constitution.md`
4. Use cross-platform scripts from `scripts/py/`

## Code Style
**Python**:
- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Use pathlib.Path for file operations
- Handle both string and Path inputs in functions
- Maintain cross-platform compatibility

**Documentation**:
- Follow spec-kit template formats
- Use markdown for all specifications
- Include execution flow diagrams where helpful
- Mark unclear requirements with [NEEDS CLARIFICATION]

## Recent Changes
1. **000-spec-kit-self-specification**: Added proper specification for spec-kit itself using its own onboarding methodology
2. **Onboarding Tools**: Enhanced path handling to accept both string and Path objects
3. **MCP Integration**: Comprehensive MCP server providing spec-driven development tools

<!-- MANUAL ADDITIONS START -->
## Constitutional Principles
This project follows constitutional development principles defined in `/memory/constitution.md`:
- **Test-First**: All implementation must be preceded by tests
- **Library-First**: Features start as standalone libraries
- **Simplicity**: Maximum 3 projects, avoid future-proofing
- **Anti-Abstraction**: Use frameworks directly, avoid wrapper classes
- **Integration-First**: Test with real environments, not mocks

## Self-Onboarding Notes
This project practices what it preaches by using its own tools to create its own specification. The `000-spec-kit-self-specification` feature demonstrates:
- Using spec-kit onboarding tools on spec-kit itself
- Following spec-kit template formats
- Adhering to constitutional principles
- Creating proper git workflow with feature branches
<!-- MANUAL ADDITIONS END -->