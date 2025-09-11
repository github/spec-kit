# Onboarding Existing Projects to Spec-Driven Development

The Spec-Kit MCP server now provides powerful tools to onboard existing projects to a spec-driven development workflow. This document explains how to use these new capabilities.

## Overview

Previously, Spec-Kit was designed primarily for new projects starting from scratch. The new onboarding tools enable you to:

- Analyze existing project structures and codebases
- Extract requirements and specifications from documentation and code
- Generate standardized specifications following Spec-Kit format
- Create detailed migration plans for adopting spec-driven development
- Perform complete end-to-end onboarding analysis

## New MCP Tools

The following new tools are available in the Spec-Kit MCP server:

### 1. `analyze_existing_project`
Analyzes the structure of an existing project to understand its organization.

**Parameters:**
- `project_path` (required): Path to the existing project directory
- `max_depth` (optional): Maximum directory depth to scan (default: 3)

**Returns:** Detailed project analysis including:
- File counts and project size estimation
- Programming languages detected
- Frameworks and build systems identified
- Test and CI/CD infrastructure detection
- Directory structure analysis

### 2. `parse_existing_documentation`
Parses existing documentation files to extract requirements and specifications.

**Parameters:**
- `project_path` (required): Path to the project directory
- `file_patterns` (optional): List of file patterns to search for

**Returns:** Documentation analysis including:
- Parsed documentation files
- Extracted requirements, features, and user stories
- API endpoints discovered
- Technologies mentioned

### 3. `extract_requirements_from_code`
Extracts requirements from code comments, docstrings, and TODO/FIXME items.

**Parameters:**
- `project_path` (required): Path to the project directory
- `file_patterns` (optional): List of file patterns to search for

**Returns:** Code analysis including:
- Comments and docstrings found
- TODO and FIXME items
- Function and class descriptions
- API documentation in code

### 4. `generate_standardized_spec`
Generates a standardized specification from existing project analysis.

**Parameters:**
- `project_analysis` (required): Result from `analyze_existing_project`
- `documentation_analysis` (required): Result from `parse_existing_documentation`
- `code_analysis` (required): Result from `extract_requirements_from_code`

**Returns:** Standardized specification including:
- Project overview and technical stack
- Functional and non-functional requirements
- User stories and acceptance criteria
- API specification and data model
- Implementation notes and testing strategy
- Gaps identified and recommendations

### 5. `create_migration_plan`
Creates a detailed migration plan for adopting spec-driven development.

**Parameters:**
- `project_analysis` (required): Result from `analyze_existing_project`
- `standardized_spec` (required): Result from `generate_standardized_spec`

**Returns:** Migration plan including:
- 5-phase migration approach
- Timeline estimates based on project size
- Resource requirements
- Risk assessment and mitigations
- Success criteria

### 6. `onboard_existing_project`
Complete end-to-end onboarding (combines all analysis steps).

**Parameters:**
- `project_path` (required): Path to the existing project directory
- `max_depth` (optional): Maximum directory depth to scan (default: 3)
- `include_migration_plan` (optional): Whether to include migration plan (default: true)

**Returns:** Complete onboarding analysis with all components and executive summary.

## Usage Examples

### Basic Project Analysis
```javascript
// Analyze an existing project structure
const analysis = await mcpClient.callTool("analyze_existing_project", {
  project_path: "/path/to/your/project",
  max_depth: 3
});
```

### Parse Documentation
```javascript
// Extract requirements from documentation
const docs = await mcpClient.callTool("parse_existing_documentation", {
  project_path: "/path/to/your/project",
  file_patterns: ["*.md", "README*", "docs/**/*"]
});
```

### Complete Onboarding
```javascript
// Perform complete end-to-end onboarding
const onboarding = await mcpClient.callTool("onboard_existing_project", {
  project_path: "/path/to/your/project",
  max_depth: 2,
  include_migration_plan: true
});

console.log("Project:", onboarding.summary.project_name);
console.log("Size:", onboarding.summary.estimated_size);
console.log("Languages:", onboarding.summary.languages);
console.log("Next steps:", onboarding.summary.next_steps);
```

## Migration Workflow

The typical workflow for onboarding an existing project is:

1. **Initial Analysis**: Use `analyze_existing_project` to understand the project structure
2. **Documentation Review**: Use `parse_existing_documentation` to extract existing requirements
3. **Code Analysis**: Use `extract_requirements_from_code` to find additional requirements
4. **Specification Generation**: Use `generate_standardized_spec` to create a Spec-Kit compatible specification
5. **Migration Planning**: Use `create_migration_plan` to create a detailed migration roadmap

Or simply use `onboard_existing_project` for a complete end-to-end analysis.

## Migration Phases

The migration plan includes these standard phases:

1. **Assessment and Planning** (1-2 weeks): Complete analysis and roadmap creation
2. **Specification Creation** (2-4 weeks): Comprehensive project specification development
3. **Process Integration** (2-3 weeks): Integrate spec-driven processes into workflow
4. **Pilot Implementation** (3-4 weeks): Pilot new approach with selected features
5. **Full Adoption** (Ongoing): Complete transition to spec-driven development

## Best Practices

- **Start with Analysis**: Always begin with a thorough project analysis
- **Review Results**: Manually review and validate extracted requirements
- **Fill Gaps**: Address any gaps identified in the analysis
- **Stakeholder Validation**: Validate specifications with project stakeholders
- **Gradual Migration**: Follow the phased approach rather than attempting immediate full migration
- **Team Training**: Ensure team is trained on spec-driven development methodology

## Supported File Types

The onboarding tools support analysis of:

**Documentation:**
- Markdown files (*.md)
- README files
- Text files (*.txt, *.rst)
- Documentation directories

**Code:**
- Python (*.py)
- JavaScript/TypeScript (*.js, *.ts)
- Java (*.java)
- C# (*.cs)
- C/C++ (*.c, *.cpp, *.h, *.hpp)
- Configuration files (package.json, pyproject.toml, etc.)

**Configuration:**
- YAML/JSON files
- Docker files
- CI/CD configurations (.github, .gitlab)
- Build configurations (Makefile, etc.)

## Troubleshooting

**Large Projects**: For very large projects, consider:
- Reducing `max_depth` parameter
- Using specific `file_patterns` to focus analysis
- Running analysis on project subsections

**Analysis Timeouts**: If analysis takes too long:
- Exclude large directories (node_modules, .git, etc.)
- Use more specific file patterns
- Analyze project sections separately

**Missing Requirements**: If few requirements are found:
- Check documentation file patterns
- Review file naming conventions
- Manually supplement with stakeholder interviews

## Integration with Existing Workflow

The onboarding tools integrate seamlessly with existing Spec-Kit workflows:

- Generated specifications use standard Spec-Kit templates
- Migration plans align with Spec-Kit methodology
- Output formats are compatible with existing tools
- Can be used alongside `init_project` for hybrid approaches

This enables organizations to adopt spec-driven development for both new and existing projects using a consistent approach and toolset.