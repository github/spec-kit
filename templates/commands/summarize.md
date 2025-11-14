---
description: Generate a comprehensive summary of an existing project's technology stack, architecture, and code conventions
scripts:
  sh: scripts/bash/generate-project-summary.sh --json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Analyze an existing codebase to extract its technology stack, project structure, code conventions, and testing setup. This command helps bootstrap spec-kit usage in brownfield/existing projects by automatically discovering project characteristics.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Only analyze existing code and generate a summary document.

**Progressive Analysis**: Start with configuration files, then analyze directory structure, and finally sample code files for conventions.

**Smart Detection**: Adapt analysis depth based on project type and available indicators.

## Execution Steps

### 1. Initialize Project Scan

Run `{SCRIPT}` from repo root and parse JSON output for:

- REPO_ROOT: Project root directory
- TECH_FILES: Discovered configuration files (package.json, pyproject.toml, etc.)
- DIRECTORIES: Key directories found (src/, tests/, etc.)
- PROJECT_TYPE: Detected project type (web, cli, library, monorepo, etc.)

For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

### 2. Analyze Technology Stack

**Scan for language and framework indicators:**

Load and analyze configuration files returned by the script:

**JavaScript/TypeScript:**
- package.json: Extract dependencies, devDependencies, scripts
- tsconfig.json: TypeScript configuration
- Detect frameworks: React, Vue, Angular, Next.js, Express, etc.

**Python:**
- requirements.txt, pyproject.toml, setup.py, Pipfile
- Detect frameworks: Django, Flask, FastAPI, etc.

**Go:**
- go.mod, go.sum
- Detect frameworks: Gin, Echo, Chi, etc.

**Rust:**
- Cargo.toml
- Detect frameworks: Actix, Rocket, Axum, etc.

**Java:**
- pom.xml, build.gradle
- Detect frameworks: Spring Boot, Quarkus, etc.

**Other languages:**
- Ruby: Gemfile
- PHP: composer.json
- C#: *.csproj

**Output consolidated technology stack:**
- Primary language(s) and version(s)
- Main framework(s)
- Key dependencies (top 5-10 most significant)
- Package manager
- Build tool(s)

### 3. Analyze Project Structure

**Map directory structure:**

Scan for common patterns:
- Source code: src/, lib/, app/, pkg/, internal/
- Tests: test/, tests/, __tests__/, spec/
- Documentation: docs/, documentation/
- Configuration: config/, conf/, settings/
- Frontend: frontend/, client/, web/, public/
- Backend: backend/, server/, api/
- Database: migrations/, models/, schemas/

**Identify architecture pattern:**
- Monorepo (presence of packages/, apps/, services/)
- Microservices (multiple service directories)
- Frontend + Backend split
- MVC/MVVM (models/, views/, controllers/)
- Clean Architecture (domain/, application/, infrastructure/)
- Modular monolith (modules/, features/)

**Output:**
- Directory tree (top 2 levels)
- Identified architecture pattern
- Key directories with purpose

### 4. Analyze Code Conventions

**Sample representative files** (read 3-5 files from each category):

**Naming conventions:**
- File naming: camelCase, PascalCase, snake_case, kebab-case
- Variable naming: camelCase, snake_case
- Function naming: camelCase, snake_case, PascalCase
- Class naming: PascalCase, snake_case
- Constant naming: UPPER_CASE, camelCase

**Code style:**
- Indentation: tabs vs spaces, width (2, 4)
- Line length limits
- Brace style (K&R, Allman, etc.)
- Import/require organization

**Documentation style:**
- JSDoc, docstrings, rustdoc, GoDoc
- Comment density and patterns
- README structure

**Look for configuration files:**
- .editorconfig
- .prettierrc, prettier.config.js
- .eslintrc, eslint.config.js
- pyproject.toml [tool.black], [tool.ruff]
- rustfmt.toml
- .clang-format

**Output:**
- Naming convention summary
- Indentation style
- Code style guide (if configured)
- Documentation patterns

### 5. Analyze Testing Setup

**Detect test frameworks:**

**JavaScript/TypeScript:**
- Jest, Vitest, Mocha, Jasmine, AVA
- Testing Library, Enzyme
- Playwright, Cypress, Puppeteer

**Python:**
- pytest, unittest, nose
- Coverage.py

**Go:**
- testing (built-in)
- testify

**Rust:**
- cargo test (built-in)

**Java:**
- JUnit, TestNG
- Mockito

**Look for:**
- Test configuration files
- Test scripts in package.json
- CI/CD configuration (.github/workflows/, .gitlab-ci.yml, etc.)
- Coverage reports configuration

**Output:**
- Test framework(s)
- Test directory structure
- Test coverage setup (if configured)
- CI/CD integration (if present)

### 6. Generate Project Summary

Create a structured summary document at `.specify/memory/project-summary.md`:

```markdown
# Project Summary

**Generated**: [CURRENT_DATE]
**Repository**: [REPO_ROOT]

## Technology Stack

### Languages
- [LANGUAGE]: [VERSION]

### Frameworks
- [FRAMEWORK_NAME]: [VERSION]

### Key Dependencies
- [DEPENDENCY_1]: [VERSION] - [PURPOSE]
- [DEPENDENCY_2]: [VERSION] - [PURPOSE]
...

### Package Manager
- [PACKAGE_MANAGER]

### Build Tools
- [BUILD_TOOL]

## Project Structure

### Architecture Pattern
[DETECTED_PATTERN]

### Directory Structure
```
[DIRECTORY_TREE]
```

### Key Directories
- `[DIRECTORY]`: [PURPOSE]
...

## Code Conventions

### Naming Conventions
- Files: [FILE_NAMING]
- Variables: [VARIABLE_NAMING]
- Functions: [FUNCTION_NAMING]
- Classes: [CLASS_NAMING]
- Constants: [CONSTANT_NAMING]

### Code Style
- Indentation: [TABS_OR_SPACES] ([WIDTH])
- Line length: [MAX_LENGTH] characters
- Style guide: [STYLE_GUIDE_IF_CONFIGURED]

### Documentation
- Format: [DOC_FORMAT]
- Pattern: [DOC_PATTERN]

## Testing

### Test Framework
- [TEST_FRAMEWORK]

### Test Structure
- Test directory: `[TEST_DIR]`
- Test pattern: [TEST_FILE_PATTERN]

### Coverage
- Tool: [COVERAGE_TOOL]
- Configuration: [COVERAGE_CONFIG_IF_PRESENT]

### CI/CD
- Platform: [CI_PLATFORM]
- Configuration: `[CI_CONFIG_FILE]`

## Notes

[ANY_ADDITIONAL_OBSERVATIONS]

---

*This summary was generated by `specify summarize`. Update this file as the project evolves or re-run the command to regenerate.*
```

### 7. Output Results

Display a summary to the user:

1. **Technology Stack Overview**: Brief summary of detected languages and frameworks
2. **Project Type**: Identified architecture pattern
3. **File Location**: Path to generated summary (`.specify/memory/project-summary.md`)
4. **Next Steps**: Suggest using `/speckit.constitution` to define project principles based on discovered conventions

**Example output:**

```
✅ Project analysis complete!

📊 Summary:
  • Language: TypeScript 5.x
  • Framework: Next.js 14.x
  • Architecture: Frontend + Backend (monorepo)
  • Test Framework: Jest + Playwright

📄 Detailed summary saved to:
  .specify/memory/project-summary.md

💡 Next steps:
  1. Review the generated summary
  2. Run /speckit.constitution to define project principles
  3. Start creating feature specs with /speckit.specify
```

## Operating Principles

### Analysis Strategy

- **Configuration first**: Start with package managers and build tools
- **Pattern recognition**: Use heuristics to identify common frameworks and patterns
- **Sampling over exhaustive**: Sample representative files rather than reading entire codebase
- **Graceful degradation**: Provide partial summary if some aspects can't be detected

### Quality Guidelines

- **Accuracy over completeness**: Only report what can be confidently detected
- **Evidence-based**: Cite specific files as evidence for conclusions
- **Version awareness**: Include version numbers where available
- **Avoid assumptions**: Mark uncertain detections as "likely" or "possible"

### Context Efficiency

- **Minimal file reads**: Target specific configuration and sample files
- **Progressive disclosure**: Analyze in stages (config → structure → conventions → tests)
- **Token-efficient**: Summarize findings concisely
- **Reusable data**: Store summary for future commands to reference

## Error Handling

- **No .specify directory**: Initialize it first by suggesting `specify init --here --ai [agent]`
- **Unknown project type**: Still generate summary with available information
- **Multiple languages**: List all detected languages with primary language first
- **Conflicting conventions**: Note variations found in different parts of codebase

## Context

{ARGS}
