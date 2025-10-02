<!--
Sync Impact Report:
Version Change: v1.0.0 → v1.1.0 (MINOR: New capabilities added)
Modified Principles: None (existing principles unchanged)
Added Sections:
  - Product Characteristics: Added "GitHub Workflow Integration" bullet
  - Core Workflow: Added GitHub integration notes with label tracking
  - GitHub Workflow Tracking: New section documenting automated issue/PR management
Templates Requiring Updates:
  ✅ templates/commands/specify.md - already includes GitHub MCP operations
  ✅ templates/commands/plan.md - already includes GitHub MCP operations
  ✅ templates/commands/tasks.md - already includes GitHub MCP operations
  ✅ templates/commands/implement.md - already includes GitHub MCP operations
  ✅ .github/prompts/*.prompt.md - already synchronized with generic templates
Follow-up TODOs:
  - Set RATIFICATION_DATE once constitution is approved by maintainers
  - Update version to v1.1.0 in this document after merge
-->

# Spec Kit Constitution

## Product Overview

**GitHub Spec Kit** is a comprehensive toolkit for implementing Spec-Driven Development (SDD) - a methodology that fundamentally inverts traditional software development by making specifications executable and code their generated expression. The toolkit provides templates, scripts, command workflows, and AI agent integrations that guide development teams through a structured, specification-first approach to building software.

### Product Characteristics

- **Specification-First Architecture**: Specifications are the source of truth; code serves specifications
- **Multi-Agent Support**: Compatible with multiple AI coding assistants (GitHub Copilot, Claude Code, Gemini CLI, Cursor, Qwen Code, opencode, Windsurf, Codex, Kilocode, Auggie CLI, Roo Code)
- **CLI-Driven Workflow**: Specify CLI (`specify`) bootstraps projects with complete SDD framework structure
- **Template-Based Consistency**: Standardized templates for specifications, plans, tasks, and commands ensure quality
- **Agent-Agnostic Commands**: Command templates work across different AI agents with appropriate format adaptations
- **Cross-Platform Design**: Works on Windows, macOS, and Linux with both bash and PowerShell script support
- **GitHub Workflow Integration**: Automated issue and PR tracking with semantic labels and progressive updates through GitHub MCP (Model Context Protocol)

### Core Workflow

Spec Kit implements a structured development flow executed through AI agent commands with integrated GitHub tracking:

1. **Constitution** (`/constitution`) - Establish project principles and governance
2. **Specification** (`/specify`) - Define WHAT to build and WHY (business requirements) → Creates GitHub issue with `Specification` label
3. **Planning** (`/plan`) - Determine HOW to implement (technical architecture) → Creates draft PR, updates issue label to `Plan`
4. **Task Breakdown** (`/tasks`) - Create executable implementation checklist → Updates PR description with task checkboxes
5. **Implementation** (`/implement`) - Execute tasks following TDD principles → Marks PR ready for review, adds `Implementation` label
6. **Analysis** (`/analyze`) - Validate alignment across all artifacts
7. **Clarification** (`/clarify`) - Surface and resolve ambiguities

**GitHub Integration**: The workflow uses GitHub MCP (Model Context Protocol) when available through AI agents to automatically create issues, manage PRs, and update labels. If GitHub MCP is unavailable, commands provide fallback instructions using the GitHub CLI (`gh`).

### Target Users

- **Development Teams**: Adopt structured, specification-driven workflows
- **Project Maintainers**: Bootstrap new projects with SDD best practices
- **AI-Assisted Developers**: Leverage AI agents with consistent command interfaces
- **Open Source Contributors**: Contribute to Spec Kit or projects using SDD methodology

### Repository Structure

Spec Kit projects follow this standardized structure:

```plaintext
<ProjectRoot>/
├── .specify/                          # SDD framework artifacts
│   ├── memory/
│   │   └── constitution.md            # Project principles and governance
│   ├── specs/                         # Feature specifications
│   │   └── ###-feature-name/
│   │       ├── spec.md                # Feature specification (WHAT/WHY)
│   │       ├── plan.md                # Implementation plan (HOW)
│   │       ├── tasks.md               # Task breakdown (execution)
│   │       ├── research.md            # Technical research (Phase 0)
│   │       ├── data-model.md          # Data entities and relationships
│   │       ├── quickstart.md          # Validation scenarios
│   │       └── contracts/             # API/interface contracts
│   └── templates/                     # Project-specific template overrides
│       ├── spec-template.md
│       ├── plan-template.md
│       ├── tasks-template.md
│       └── commands/                  # Command templates
│           ├── constitution.md
│           ├── specify.md
│           ├── plan.md
│           ├── tasks.md
│           ├── implement.md
│           ├── analyze.md
│           └── clarify.md
├── .<agent>/                          # Agent-specific configurations
│   ├── commands/ or prompts/         # Agent command files
│   └── rules/ or instructions.md     # Agent guidance files
├── scripts/                           # Automation scripts
│   ├── bash/
│   │   ├── create-new-feature.sh
│   │   ├── setup-plan.sh
│   │   ├── update-agent-context.sh
│   │   └── check-prerequisites.sh
│   └── powershell/
│       ├── create-new-feature.ps1
│       ├── setup-plan.ps1
│       ├── update-agent-context.ps1
│       └── check-prerequisites.ps1
├── src/ or backend/ or apps/         # Implementation code
├── tests/ or frontend/                # Test code or additional structure
├── docs/                              # Documentation
├── README.md                          # Project documentation
├── CONTRIBUTING.md                    # Contribution guidelines
└── LICENSE                            # License file
```

**Key Artifacts**:

- **constitution.md**: Project-specific principles that guide all development
- **spec.md**: Business requirements and user scenarios (tech-agnostic)
- **plan.md**: Technical architecture and implementation strategy
- **tasks.md**: Ordered, actionable implementation checklist with TDD gates
- **research.md**: Technical decisions, library choices, and trade-offs
- **data-model.md**: Entity definitions and relationships
- **contracts/**: API specifications, interface definitions

**Agent Integration**:

Each supported AI agent has its own directory convention:

| Agent | Directory |
|-------|-----------|
| GitHub Copilot | `.github/prompts/` |
| Claude Code | `.claude/commands/` |
| Gemini CLI | `.gemini/commands/` |
| Cursor | `.cursor/commands/` |
| Qwen Code | `.qwen/commands/` |
| opencode | `.opencode/command/` |
| Windsurf | `.windsurf/workflows/` |
| Codex | `.codex/commands/` |
| Kilocode | `.kilocode/commands/` |
| Auggie CLI | `.auggie/commands/` |
| Roo Code | `.roo/commands/` |

**GitHub Workflow Tracking**:

Spec Kit integrates with GitHub to provide automated workflow tracking:

- **Issue Creation**: `/specify` creates GitHub issues with spec content and semantic labels (`Specification` + type)
- **Pull Request Management**: `/plan` creates draft PRs linked to issues; `/implement` marks them ready for review
- **Label Conventions**: Semantic labels track workflow phase (`Specification`, `Plan`, `implement`) and change type (`Docs`, `Fix`, `Patch`, `Minor`, `Major`)
- **Progressive Updates**: PR descriptions are updated with plan content, task checkboxes, and completion status
- **MCP Integration**: Uses GitHub MCP (Model Context Protocol) when available through AI agents
- **CLI Fallback**: Provides `gh` CLI commands when GitHub MCP is unavailable

## Core Principles

### I. Specification as Source of Truth (NON-NEGOTIABLE)

Specifications MUST be the primary artifact from which all implementation derives. Code serves specifications, not the other way around. This principle is fundamental to Spec-Driven Development:

- **Specifications drive implementation**: Technical decisions flow FROM business requirements, not vice versa
- **Tech-agnostic specifications**: Spec files MUST NOT contain implementation details (languages, frameworks, APIs)
- **User-centric language**: Specifications written for business stakeholders, not just developers
- **Versioned with code**: Specifications live in version control alongside implementation
- **Living documentation**: Specifications are continuously refined, not write-once artifacts
- **Constitution supremacy**: Project constitution defines non-negotiable principles that override convenience

**Rationale**: Traditional development treats specifications as guidance that quickly becomes stale. SDD inverts this - specifications remain authoritative, with code regenerated when specs evolve. This eliminates spec-implementation drift and enables confident refactoring.

### II. Multi-Agent Compatibility (NON-NEGOTIABLE)

Spec Kit MUST support multiple AI coding assistants without bias toward any single vendor. Teams choose their preferred tools while maintaining consistent SDD workflows:

- **Format adaptation**: Commands adapt to agent-specific formats (Markdown for Copilot/Claude/Cursor, TOML for Gemini/Qwen)
- **Directory conventions**: Each agent has standardized directory structure (`.claude/commands/`, `.github/prompts/`, etc.)
- **Placeholder patterns**: Agent-specific argument patterns (`$ARGUMENTS`, `{{args}}`, etc.)
- **CLI tool detection**: Specify CLI checks for required agent tools during initialization
- **Agent-agnostic templates**: Core templates work across all supported agents
- **No vendor lock-in**: Projects can switch agents without rewriting specifications

**Supported Agents**:
- GitHub Copilot (IDE-based, VS Code integration)
- Claude Code (`claude` CLI)
- Gemini CLI (`gemini` CLI)
- Cursor (`cursor-agent` CLI)
- Qwen Code (`qwen` CLI)
- opencode (`opencode` CLI)
- Windsurf (IDE-based workflows)
- Codex (`codex` CLI)
- Kilocode (`kilocode` CLI)
- Auggie CLI (`auggie` CLI)
- Roo Code (`roo` CLI)

**Rationale**: AI coding assistant landscape is rapidly evolving. Spec Kit must remain neutral and extensible, allowing teams to adopt new agents as they emerge without abandoning SDD methodology.

### III. Template-Driven Consistency (REQUIRED)

All SDD artifacts MUST be generated from standardized templates that enforce quality and completeness:

- **Spec template**: Ensures user scenarios, acceptance criteria, functional requirements
- **Plan template**: Enforces constitution checks, technical context, structured phases
- **Tasks template**: Mandates TDD gates, parallel execution markers, dependency tracking
- **Command templates**: Provide consistent execution flows with error handling
- **Overridable templates**: Projects can customize templates in `.specify/templates/` while maintaining structure
- **Template evolution**: Templates version with Spec Kit, projects inherit improvements

**Template Requirements**:
- **Execution flows**: Each template includes pseudocode workflow for AI agents
- **Validation gates**: Templates enforce quality checks (constitution alignment, requirement completeness)
- **Explicit sections**: Mandatory vs. optional sections clearly marked
- **Failure conditions**: Templates specify ERROR conditions that halt execution
- **Context preservation**: Templates reference other artifacts to maintain consistency

**Rationale**: Without templates, each team reinvents SDD structure. Templates encode best practices, ensure completeness, and provide guardrails that prevent common mistakes.

### IV. Test-Driven Development Integration (NON-NEGOTIABLE)

SDD workflow MUST enforce TDD practices through task ordering and explicit gates:

- **Tests before implementation**: Tasks template mandates Phase 3.2 (Tests First) before Phase 3.3 (Core Implementation)
- **Failing tests required**: Tests MUST fail initially before implementation begins (Red → Green → Refactor)
- **Contract testing**: API/interface contracts generate test tasks automatically
- **Parallel test creation**: Multiple test files marked `[P]` for simultaneous creation
- **Test completeness validation**: Tasks workflow verifies all contracts/entities have corresponding tests
- **TDD gate in plan**: Constitution check section in plan template enforces TDD requirement

**Test Workflow**:
1. Define contracts in `contracts/` (API specs, interface definitions)
2. Generate contract tests from contracts (Phase 3.2)
3. Write integration tests for user scenarios
4. Verify all tests FAIL (Red phase)
5. Implement features to make tests pass (Green phase)
6. Refactor while maintaining passing tests

**Rationale**: TDD ensures code quality, prevents regressions, and creates living documentation. SDD makes TDD mandatory by encoding it into the task generation workflow, not leaving it to developer discipline.

### V. Incremental Complexity with Justification (REQUIRED)

Technical solutions MUST start simple and justify any complexity through constitution checks:

- **Complexity tracking**: Plan template includes dedicated "Complexity Tracking" section
- **Justification required**: Any complex pattern (microservices, event sourcing, advanced architectures) MUST have explicit rationale
- **Constitution alignment**: Complex choices validated against project constitution principles
- **Simplification first**: When constitution check fails, simplify approach before seeking exceptions
- **Trade-off documentation**: Research phase documents pros/cons of complex patterns
- **Two-stage validation**: Constitution check runs before research (Phase 0) and after design (Phase 1)

**Complexity Gates**:
- **Phase 0 (Pre-research)**: Initial constitution check identifies potential violations
- **Phase 1 (Post-design)**: Re-check after technical design validates no new violations introduced
- **Blocking failures**: Unjustifiable violations ERROR and halt workflow

**Rationale**: Premature optimization and over-engineering are common failure modes. SDD embeds complexity justification into the workflow, forcing teams to start simple and consciously choose complexity only when justified.

### VI. Cross-Platform Script Support (REQUIRED)

All automation scripts MUST support both bash (POSIX shell) and PowerShell:

- **Dual implementation**: Every script exists in `scripts/bash/` and `scripts/powershell/`
- **Feature parity**: Both versions provide identical functionality
- **Platform detection**: Specify CLI detects OS and recommends appropriate script type
- **Template compatibility**: Agent command templates reference scripts with `{SCRIPT}` placeholder
- **Shell-specific idioms**: Use bash best practices for `.sh`, PowerShell conventions for `.ps1`

**Script Responsibilities**:
- **create-new-feature**: Creates feature directory structure and initializes spec/plan
- **setup-plan**: Bootstraps plan.md with technical context
- **update-agent-context**: Synchronizes constitution/guidance across agent files
- **check-prerequisites**: Validates required tools installed (Python, uv, Git, agent CLIs)

**Rationale**: Development teams use diverse operating systems. Cross-platform scripts ensure SDD workflow works consistently on Windows, macOS, and Linux without requiring environment-specific workarounds.

### VII. Semantic Versioning and Changelog Discipline (NON-NEGOTIABLE)

Specify CLI MUST follow strict semantic versioning with complete changelog maintenance:

- **Version format**: MAJOR.MINOR.PATCH (SemVer 2.0.0)
- **Version increments**:
  - **MAJOR**: Breaking changes (remove agents, change CLI interface, incompatible template changes)
  - **MINOR**: New features (add agents, new commands, new CLI options)
  - **PATCH**: Bug fixes, documentation updates, clarifications
- **Version locations**: Both `pyproject.toml` (source of truth) and `CHANGELOG.md`
- **Changelog format**: Keep a Changelog 1.0.0 (Added/Changed/Deprecated/Removed/Fixed/Security)
- **Release dates**: ISO 8601 format (YYYY-MM-DD)
- **Entry requirements**: All changes MUST have changelog entry before merge

**Version Bump Rules**:
- Changes to `src/specify_cli/__init__.py` REQUIRE version bump
- New agent support → MINOR bump
- Agent removal → MAJOR bump
- Template additions → MINOR bump
- Template breaking changes → MAJOR bump
- Bug fixes → PATCH bump

**Rationale**: Users depend on Specify CLI for project bootstrapping. Clear versioning and changelogs enable users to understand impact of upgrades and maintain compatible projects.

## Quality Standards

### Code Quality (Specify CLI)

- **Python version**: 3.11+ required (type hints, modern syntax)
- **Dependencies**: Minimal and justified (typer, rich, httpx, platformdirs, readchar, truststore)
- **Type hints**: All functions MUST have type annotations
- **Docstrings**: Public functions MUST have descriptive docstrings with usage examples
- **Error handling**: Clear error messages with actionable guidance
- **Cross-platform paths**: Use `pathlib.Path`, never hardcoded separators

### Template Quality

- **Execution flows**: Every template includes pseudocode workflow for AI agents
- **Section completeness**: Mandatory sections clearly marked, optional sections conditionally included
- **Validation gates**: ERROR conditions specified for quality enforcement
- **Cross-references**: Templates reference related artifacts (spec ← plan ← tasks)
- **Agent placeholders**: `$ARGUMENTS`, `{SCRIPT}`, `__AGENT__` used consistently

### Script Quality

- **Dual implementation**: bash and PowerShell versions functionally identical
- **Error handling**: Exit codes and error messages for all failure modes
- **Path safety**: Handle spaces, special characters, non-ASCII paths
- **Idempotency**: Scripts safe to run multiple times without corruption
- **Help documentation**: Usage instructions in script comments

### Documentation Quality

- **README completeness**: Installation, quickstart, command reference, troubleshooting
- **AGENTS.md maintenance**: Complete guide for adding new agent support
- **CONTRIBUTING.md**: Clear PR guidelines, development workflow, testing requirements
- **Agent-specific docs**: Each agent integration includes setup instructions

## Development Workflow

### Feature Development Process

1. **Create feature branch**: `git checkout -b feature/descriptive-name`
2. **Document in spec**: Use SDD workflow even for Spec Kit itself (inception!)
3. **Update templates**: If changing workflow, update relevant templates
4. **Update CLI**: Implement changes in `src/specify_cli/__init__.py`
5. **Update scripts**: Maintain bash and PowerShell versions together
6. **Test locally**: Run `uv run specify --help` and test affected commands
7. **Update CHANGELOG**: Add entry under `[LATEST_VERSION]` section
8. **Bump version**: Update `pyproject.toml` if CLI changed
9. **Submit PR**: Include rationale, testing evidence, breaking change warnings

### Agent Addition Process

Follow the comprehensive guide in `AGENTS.md`:

1. **Update AI_CHOICES**: Add agent to dictionary in `__init__.py`
2. **Update agent_folder_map**: Add agent folder for security notice
3. **Update CLI help**: Include agent in examples and error messages
4. **Update README**: Add agent to "Supported AI Agents" table
5. **Update release scripts**: Add agent to package generation scripts
6. **Update context scripts**: Add agent to bash and PowerShell context update scripts
7. **Test locally**: Initialize project with new agent, verify file generation
8. **Version bump**: MINOR version increase for new agent support
9. **Changelog entry**: Document new agent support under Added section

### Pull Request Requirements

- **Title format**: `type: description` (feat:, fix:, docs:, chore:)
- **Description**: Explain WHAT changed, WHY, and HOW to test
- **Breaking changes**: Clearly marked with `BREAKING CHANGE:` in description
- **Checklist**: Confirm tests pass, docs updated, changelog updated, version bumped
- **Review process**: At least one maintainer approval required
- **CI validation**: All checks must pass (no bypass)

### Release Process

1. **Merge to main**: PR merge triggers release workflow
2. **Version validation**: Ensure `pyproject.toml` version matches `CHANGELOG.md`
3. **Build packages**: Generate wheel and source distributions
4. **Create GitHub release**: Tag with version (e.g., `v0.0.17`)
5. **Publish artifacts**: Upload distribution packages to release
6. **Update documentation**: Regenerate docs with new version
7. **Announcement**: Communicate release in discussions/README

## Governance

### Constitution Authority

This constitution supersedes all other development practices for Spec Kit and Specify CLI. When conflicts arise between this document and other guidance (including external agent documentation), this constitution takes precedence.

**For Projects Using Spec Kit**: Projects initialized with Specify CLI should create their own project-specific constitution using the `/constitution` command. That constitution governs the project, not this Spec Kit constitution.

### Amendment Process

Changes to this constitution require:

1. **Proposal**: Document proposed change with clear rationale
2. **Impact analysis**: Identify affected templates, scripts, CLI code
3. **Community discussion**: Open issue for maintainer and community feedback
4. **Migration plan**: If breaking changes, provide migration guide
5. **Version bump**:
   - **MAJOR**: Backward-incompatible principle removals or redefinitions
   - **MINOR**: New principles or materially expanded guidance
   - **PATCH**: Clarifications, wording fixes, non-semantic refinements
6. **Maintainer approval**: At least two maintainers must approve
7. **Update propagation**: Update all dependent templates, scripts, docs
8. **Sync impact report**: Document changes in constitution file comment

### Compliance and Validation

- **PR review checklist**: All PRs validated against constitutional principles
- **Template alignment**: Templates must reflect constitutional requirements
- **CLI validation**: `specify check` command verifies prerequisites
- **Agent parity**: New features must work across all supported agents (or document limitations)
- **Breaking changes**: Require explicit justification and migration guide

### Runtime Development Guidance

When developing Spec Kit itself:

- **Use SDD methodology**: Apply Spec-Driven Development to Spec Kit (inception!)
- **Agent-specific guidance**: Reference appropriate agent guidance file:
  - GitHub Copilot: `.github/copilot-instructions.md`
  - Claude Code: `.claude/CLAUDE.md` or `AGENTS.md`
  - Gemini CLI: `GEMINI.md` or `AGENTS.md`
  - Other agents: `AGENTS.md` (general agent integration guide)
- **Constitution first**: Establish or update constitution before major feature work
- **Template consistency**: Changes to workflow require corresponding template updates

**Version**: 1.0.0
**Ratified**: TODO(RATIFICATION_DATE) - Awaiting maintainer approval
**Last Amended**: 2025-10-02
