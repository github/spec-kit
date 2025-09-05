# Spec-Kit Commands and Features Guide

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Core SDD Commands](#core-sdd-commands)
- [Foundation Commands](#foundation-commands)
- [Methodology Commands](#methodology-commands)
- [Expert System Commands](#expert-system-commands)
- [Collaboration Commands](#collaboration-commands)
- [Orchestration Commands](#orchestration-commands)
- [Command Integration Patterns](#command-integration-patterns)
- [Usage Workflows](#usage-workflows)
- [Command Dependencies](#command-dependencies)
- [Best Practices](#best-practices)

## Overview

The Spec-Kit provides a comprehensive set of 10 commands that work together in a layered architecture to transform software development from ad-hoc coding into a systematic, specification-driven process. These commands maintain full backward compatibility with the original Spec-Driven Development (SDD) workflow while adding powerful new capabilities for project discovery, structured methodology, expert guidance, and multi-agent coordination.

### Core Philosophy

- **Intent-driven development** where specifications define the "_what_" before the "_how_"
- **Executable specifications** that generate working implementations
- **Continuous refinement** through AI-assisted validation and consistency checking
- **Multi-layered integration** supporting gradual adoption and enhancement
- **Collaborative intelligence** through expert systems and agent coordination

## Architecture

The Spec-Kit implements a 4-layer architecture where each layer builds upon the previous ones:

```text
Layer 4: PACT Coordination (Multi-agent collaboration)
├── /pact command for coordination setup
├── coordination/ directory structure
└── Enhanced collaboration patterns

Layer 3: Expert Systems (Domain guidance)  
├── /expert command for domain expertise
├── experts/ directory for knowledge files
└── Agentic integration patterns

Layer 2: SPARC Methodology (Structured development)
├── /sparc command for systematic approach
├── Phase-by-phase documentation
└── Quality gates and validation

Layer 1: Project Foundation (Discovery & planning)
├── /discover command for comprehensive analysis
├── Foundation documents (BACKLOG.md, IMPLEMENTATION_GUIDE.md, etc.)
└── Market reality validation
```

**Orchestration Layer**: Integrated workflows that coordinate all layers

- `/workflow` for complex development scenarios
- `/sync` for maintaining consistency across systems

## Core SDD Commands

These are the original Spec-Driven Development commands, enhanced with integration capabilities:

### `/specify`

**Purpose**: Start a new feature by creating a specification and feature branch.

**What it does**:

1. Automatically determines next feature number and creates semantic branch name
2. Creates feature specification using structured template
3. Generates comprehensive user stories and acceptance criteria
4. Integrates with existing project foundation documents

**Generated Output**:

- `specs/###-feature-name/spec.md` - Complete feature specification
- Feature branch with semantic naming
- User scenarios and testing requirements
- Functional and non-functional requirements

**Enhanced Integration**:

- Uses `BACKLOG.md` for project context and priority
- Leverages expert systems for domain-specific guidance
- Coordinates with PACT framework for multi-agent development

**Example Usage**:

```bash
/specify "Real-time chat system with message history and user presence"
```

### `/plan`

**Purpose**: Create a technical implementation plan for the specified feature.

**What it does**:

1. Analyzes feature specification and constitutional requirements
2. Generates comprehensive implementation approach
3. Creates technical architecture and design decisions
4. Produces multiple supporting documents for implementation

**Generated Output**:

- `plan.md` - Master implementation plan
- `research.md` - Technology research and decisions
- `data-model.md` - Entity definitions and relationships
- `contracts/` - API contracts and schemas
- `quickstart.md` - Validation scenarios

**Enhanced Integration**:

- Consults expert systems for technology recommendations
- Applies SPARC methodology for systematic design
- Coordinates with PACT framework for collaborative planning

**Example Usage**:

```bash
/plan "WebSocket for real-time messaging, PostgreSQL for history, Redis for presence"
```

### `/tasks`

**Purpose**: Break down the implementation plan into executable, numbered tasks.

**What it does**:

1. Analyzes all design documents from planning phase
2. Generates specific, actionable tasks with dependencies
3. Creates parallel execution opportunities where possible
4. Follows Test-Driven Development (TDD) principles

**Generated Output**:

- `tasks.md` - Numbered task list with dependencies
- Parallel execution examples
- Clear file paths and implementation requirements
- Validation and completion criteria

**Enhanced Integration**:

- Uses expert system guidance for task optimization
- Coordinates with PACT framework for multi-agent task distribution
- Integrates with methodology patterns for systematic execution

**Example Usage**:

```bash
/tasks "Context: WebSocket implementation with TDD approach"
```

## Foundation Commands

These commands establish comprehensive project foundation and discovery:

### `/discover`

**Purpose**: Execute comprehensive project discovery and foundation setup with brutal market reality validation.

**What it does**:

1. Analyzes project requirements and market viability
2. Creates comprehensive planning documents
3. Provides brutally honest sales and marketing advisory
4. Establishes foundation for all subsequent development

**Generated Output**:

- `BACKLOG.md` - Prioritized features and requirements
- `IMPLEMENTATION_GUIDE.md` - Technical strategy and approach
- `RISK_ASSESSMENT.md` - Risk analysis and mitigation strategies
- `FILE_OUTLINE.md` - Project structure and organization

**Key Features**:

- Market viability validation with uncomfortable questions
- Sales model validation and revenue potential analysis
- Technical feasibility assessment with resource requirements
- Integration with existing systems and constraints

**Example Usage**:

```bash
/discover "Photo organization app with drag-and-drop albums and metadata management"
```

### `/enhance`

**Purpose**: Upgrade existing projects with enhanced analysis and codebase extraction.

**What it does**:

1. Analyzes existing codebase and documentation
2. Extracts architectural patterns and technical decisions
3. Identifies gaps and improvement opportunities
4. Generates enhanced foundation documents based on current state

**Generated Output**:

- Enhanced versions of foundation documents
- Gap analysis and improvement recommendations
- Technical debt assessment
- Migration strategies for modernization

**Key Features**:

- Codebase analysis and metadata extraction
- Existing documentation enhancement
- Technical debt identification and prioritization
- Gradual adoption strategies for team integration

**Example Usage**:

```bash
/enhance "Analyze existing e-commerce platform and create enhancement roadmap"
```

## Methodology Commands

These commands apply structured development methodologies:

### `/sparc`

**Purpose**: Apply SPARC methodology (Specification, Pseudocode, Architecture, Refinement, Completion) for systematic development.

**What it does**:

1. Guides through structured development phases
2. Ensures comprehensive coverage of all aspects
3. Enforces quality gates between phases
4. Integrates with existing foundation documents

**SPARC Phases**:

- **Specification**: Comprehensive requirements and user scenarios
- **Pseudocode**: Algorithm design and logic architecture
- **Architecture**: System design and technical architecture
- **Refinement**: Code quality and performance optimization
- **Completion**: Final validation and deployment preparation

**Generated Output**:

- Phase-specific documentation for each SPARC stage
- Decision justifications and alternative considerations
- Integration guidelines with other methodologies
- Quality checkpoints and validation criteria

**Example Usage**:

```bash
/sparc --phase=architecture "Design system architecture for chat application"
```

## Expert System Commands

These commands create and manage domain-specific expert knowledge systems:

### `/expert`

**Purpose**: Generate or consult specialized expert context files with agentic system integration.

**What it does**:

1. Creates domain-specific expert knowledge bases
2. Establishes agentic software development framework
3. Provides specialized guidance for different project aspects
4. Enables multi-agent coordination and collaboration

**Expert Categories**:

**Core Experts**:

- `project_type_expert.md` - Domain-specific best practices
- `architecture_expert.md` - System design decisions
- `methodology_expert.md` - Development process coordination
- `tech_stack_expert.md` - Technology-specific guidance
- `tools_expert.md` - Development tools and productivity

**Implementation Experts**:

- `auth_expert.md` - Authentication and security systems
- `database_expert.md` - Data modeling and optimization
- `api_expert.md` - API design and integration patterns
- `ui_expert.md` - User interface and experience design
- `performance_expert.md` - Performance optimization strategies

**Process Experts**:

- `orchestrator_expert.md` - Task routing and coordination
- `debug_expert.md` - Problem diagnosis and resolution
- `documentation_expert.md` - Documentation standards and practices

**Example Usage**:

```bash
/expert --domains="security,performance,database" "Create expert systems for banking application"
```

## Collaboration Commands

These commands establish multi-agent coordination frameworks:

### `/pact`

**Purpose**: Implement PACT framework (Planning, Action, Coordination, Testing) for multi-agent coordination.

**What it does**:

1. Establishes agent roles and responsibilities
2. Creates coordination protocols and workflows
3. Implements collaborative quality assurance
4. Enables adaptive multi-agent collaboration

**PACT Framework Components**:

- **Planning (P)**: Agent role definition and task distribution
- **Action (A)**: Real-time coordination during execution
- **Coordination (C)**: Collaboration optimization and coherence
- **Testing (T)**: Collaborative behavior validation

**Generated Output**:

- `AGENT_ECOSYSTEM_DESIGN.md` - Agent roles and interactions
- `COORDINATION_STRATEGY.md` - Task decomposition and coordination
- `COLLABORATIVE_WORKFLOWS.md` - Multi-agent development processes
- `AGENTIC_TESTING_FRAMEWORK.md` - Collaboration validation strategies

**Example Usage**:

```bash
/pact --agents=3 --complexity=high "Setup coordination for complex microservices project"
```

## Orchestration Commands

These commands coordinate and integrate all layers of the system:

### `/workflow`

**Purpose**: Execute integrated workflow combining multiple methodologies across all integration layers.

**What it does**:

1. Orchestrates complete Spec-Kit integration
2. Coordinates Step 1-4 methodologies
3. Manages complex development scenarios
4. Enables end-to-end workflow automation

**Workflow Types**:

- **Feature Development**: Complete feature lifecycle from discovery to implementation
- **New Project Setup**: End-to-end project initialization with all layers
- **Existing Project Enhancement**: Brownfield integration and modernization
- **Continuous Enhancement**: Ongoing improvement and adaptation

**Integration Flow Example (Feature Development)**:

```text
1. Discovery Integration: Check BACKLOG.md for feature context
2. SPARC Application: Apply appropriate phases for complexity
3. Expert Consultation: Consult relevant expert systems
4. PACT Coordination: Coordinate with agent ecosystem
5. Enhanced SDD Execution: Run /specify, /plan, /tasks with full context
```

**Example Usage**:

```bash
/workflow --type=feature-development "Payment processing with fraud detection"
```

### `/sync`

**Purpose**: Update and synchronize expert and memory systems to maintain consistency.

**What it does**:

1. Synchronizes all expert context files with current project state
2. Updates constitutional and foundational memory
3. Validates cross-reference consistency
4. Maintains system coherence as project evolves

**Synchronization Scope**:

- Memory system updates (constitution, decision tracking)
- Expert system synchronization (all expert files)
- Cross-reference validation (consistency checks)
- Integration health monitoring (system status)

**Example Usage**:

```bash
/sync --scope=all "Update all systems after major architecture change"
```

## Command Integration Patterns

### Progressive Adoption Patterns

#### Level 1: Basic SDD (Always Available)

```bash
/specify "Feature description" → /plan "Implementation" → /tasks "Break down work"
```

#### Level 2: Foundation-Enhanced SDD (Recommended)

```bash
/discover "Project overview" → /specify → /plan → /tasks
```

#### Level 3: Methodology-Enhanced Development

```bash
/discover → /sparc --phase=specification → /specify → /plan → /tasks
```

#### Level 4: Expert-Guided Development

```bash
/discover → /expert → /specify → /plan → /tasks
```

#### Level 5: Full Integration (Complex Projects)

```bash
/discover → /sparc → /expert → /pact → /specify → /plan → /tasks
```

#### Level 6: Orchestrated Workflow (Production)

```bash
/workflow --type=feature-development "Feature description"
```

### Specialized Integration Patterns

**New Project Development**:

```bash
/discover "Project overview" → /sparc → /expert → /pact → /workflow --type=setup
```

**Existing Project Enhancement**:

```bash
/enhance "Project analysis" → /expert --focus=migration → /pact --gradual → /sync
```

**Complex Feature Development**:

```bash
/sparc --phase=specification → /expert --consult → /specify → /plan → /tasks
```

**Team Collaboration Setup**:

```bash
/pact --setup → /expert --domains=coordination → /sync --validate
```

## Usage Workflows

### New User Journey

1. **Start Simple**: Begin with basic SDD commands

   ```bash
   /specify "Feature description"
   /plan "Technical approach"
   /tasks "Implementation breakdown"
   ```

2. **Add Foundation**: Enhance with project discovery

   ```bash
   /discover "Project overview"
   # Then continue with enhanced context
   ```

3. **Apply Methodology**: Use structured development

   ```bash
   /sparc --phase=specification
   # Apply systematic approach to complex features
   ```

4. **Expert Guidance**: Add domain expertise

   ```bash
   /expert --domains="security,performance"
   # Get specialized guidance
   ```

5. **Full Integration**: Use complete system

   ```bash
   /workflow --type=feature-development
   # Orchestrated development process
   ```

### Team Adoption Strategy

#### Phase 1: Individual Adoption (Low Risk)

- Start with `/discover` for project foundation
- Use enhanced `/specify`, `/plan`, `/tasks` workflow
- Build familiarity with structured approach

#### Phase 2: Methodology Integration (Medium Risk)

- Apply `/sparc` for complex features
- Introduce expert systems with `/expert`
- Establish consistent development patterns

#### Phase 3: Team Coordination (Higher Risk)

- Implement `/pact` for multi-agent coordination
- Use `/workflow` for orchestrated development
- Establish collaborative quality assurance

#### Phase 4: Full Integration (Production Ready)

- Complete system integration across all layers
- Continuous improvement with `/sync`
- Adaptive workflow optimization

## Command Dependencies

### Required Dependencies

**`/specify`**:

- Project initialization (can be done manually or via CLI)
- Optional: Foundation documents from `/discover`

**`/plan`**:

- Feature specification from `/specify`
- Constitution file (`memory/constitution.md`)

**`/tasks`**:

- Implementation plan from `/plan`
- Design documents (contracts, data models, etc.)

**`/discover`**:

- Project concept or existing codebase
- No other dependencies

**`/enhance`**:

- Existing project with codebase
- No other dependencies

**`/sparc`**:

- Optional: Foundation documents for context
- Project requirements or existing specifications

**`/expert`**:

- Optional: Foundation and methodology documents
- Domain requirements and project context

**`/pact`**:

- Project complexity assessment
- Agent coordination requirements

**`/workflow`**:

- Depends on workflow type
- May require any combination of other commands

**`/sync`**:

- Existing expert systems and documentation
- Project state to synchronize against

### Optional Enhancements

Commands work better when foundation documents exist:

- **BACKLOG.md**: Enhances all commands with project context
- **IMPLEMENTATION_GUIDE.md**: Provides technical constraints and direction
- **Expert systems**: Provide domain-specific guidance
- **PACT framework**: Enables collaborative development

## Best Practices

### Command Selection Guidelines

**For Simple Features**: Use basic SDD workflow

```bash
/specify → /plan → /tasks
```

**For Complex Features**: Add methodology and expertise

```bash
/sparc → /expert → /specify → /plan → /tasks
```

**For New Projects**: Start with comprehensive discovery

```bash
/discover → /sparc → /expert → /pact → /workflow
```

**For Existing Projects**: Begin with enhancement analysis

```bash
/enhance → /expert → /sparc → /sync
```

### Quality Assurance Integration

1. **Foundation Validation**: Ensure market viability with `/discover`
2. **Methodology Validation**: Apply quality gates with `/sparc`
3. **Expert Validation**: Consult domain expertise with `/expert`
4. **Collaborative Validation**: Use multi-agent review with `/pact`
5. **System Validation**: Maintain consistency with `/sync`

### Performance Optimization

- **Start Minimal**: Begin with core commands and add layers gradually
- **Validate Early**: Use foundation documents to catch issues early
- **Expert Guidance**: Leverage domain expertise to avoid common pitfalls
- **Continuous Sync**: Keep systems aligned with regular `/sync` execution
- **Measure Effectiveness**: Track workflow success and adapt patterns

### Error Handling and Recovery

**Graceful Degradation**:

- Commands work with minimal available information
- Missing context files don't break core functionality
- Partial expert systems still provide value

**Error Recovery**:

- Clear error messages with remediation steps
- Automatic detection of common integration issues
- Safe reset mechanisms to return to known good states

**Validation and Consistency**:

- Pre-execution validation of command prerequisites
- Post-execution validation of generated artifacts
- Cross-command consistency checks via `/sync`

### Maintenance and Evolution

**Regular Synchronization**:

```bash
/sync --scope=all --validate
```

**Health Monitoring**:

```bash
/workflow --analyze-effectiveness --period=30-days
```

**Continuous Improvement**:

```bash
/expert --update-patterns --based-on-outcomes
```

**System Evolution**:

```bash
/sync --evolve-patterns --adapt-to-usage
```

---

## Conclusion

The Spec-Kit command system transforms software development from an ad-hoc process into a systematic, specification-driven methodology. The 10 commands work together seamlessly, providing:

- **Backward Compatibility**: Original SDD workflow continues to work unchanged
- **Gradual Enhancement**: Add capabilities incrementally as needed
- **Expert Intelligence**: Domain-specific guidance throughout development
- **Collaborative Development**: Multi-agent coordination and quality assurance
- **Systematic Quality**: Structured methodology with built-in validation

Whether you're starting with a simple feature or building a complex system, the Spec-Kit provides the tools and structure to build high-quality software faster through specification-driven development.

---

## Conclusion

The Spec-Kit command system transforms software development from an ad-hoc process into a systematic, specification-driven methodology. The 10 commands work together seamlessly, providing:

- **Backward Compatibility**: Original SDD workflow continues to work unchanged
- **Gradual Enhancement**: Add capabilities incrementally as needed
- **Expert Intelligence**: Domain-specific guidance throughout development
- **Collaborative Development**: Multi-agent coordination and quality assurance
- **Systematic Quality**: Structured methodology with built-in validation

Whether you're starting with a simple feature or building a complex system, the Spec-Kit provides the tools and structure to build high-quality software faster through specification-driven development.
