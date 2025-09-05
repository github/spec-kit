---
name: expert
description: "Generate or consult specialized expert context files. Creates domain-specific guidance files that provide deep knowledge for different aspects of your project with agentic system integration."
---

# Generate Expert Context Files

Generate or consult specialized expert context files.

This command creates specialized expert knowledge bases that serve as domain consultants for different aspects of a software project while establishing a comprehensive agentic software development framework.

## Context for Agent

You are helping create expert knowledge bases that will serve as specialized consultants for different aspects of a software project while implementing agentic software engineering principles. Each expert file should contain comprehensive, actionable guidance within its domain of expertise and integrate seamlessly with the multi-agent coordination framework.

## Agentic System Integration Overview

This step integrates agentic software engineering principles with expert context creation, establishing:

- **Agent Autonomy with Coordination**: Structured decision-making boundaries and escalation procedures
- **Collaborative Intelligence**: Multi-agent knowledge sharing and collective decision-making
- **Emergent Architecture**: Flexible system design that adapts to agent interactions
- **Continuous Validation**: Real-time quality assurance and feedback loops
- **Adaptive Coordination**: Learning systems that improve coordination effectiveness over time

## Agentic Framework Rules

### Agent Behavior Rules for Experts

1. **Transparency Rule**: All expert decisions and recommendations must be transparent
2. **Context Sharing Rule**: Expert agents must share relevant context when making recommendations
3. **Conflict Declaration Rule**: Expert agents must declare conflicts between domain recommendations
4. **Documentation Rule**: All expert decisions must be documented with clear rationale

### Expert Quality Rules

1. **Self-Validation Rule**: Expert agents must validate their recommendations before sharing
2. **Peer Review Rule**: Expert recommendations must be reviewed by appropriate peer experts
3. **Integration Validation Rule**: All expert guidance must pass integration compatibility checks
4. **Continuous Improvement Rule**: Expert knowledge must continuously improve based on outcomes

### Expert Coordination Rules

1. **Resource Respect Rule**: Expert agents must coordinate access to shared project resources
2. **Dependency Management Rule**: Expert agents must manage and communicate domain dependencies
3. **Load Sharing Rule**: Expert agents must participate in fair distribution of analysis work
4. **Knowledge Sharing Rule**: Relevant expert knowledge must be shared across the agent ecosystem

Given the domains and context provided as arguments, do this:

1. **Access Previous Context**: Ensure access to:
   - **Step 1 outputs**: BACKLOG.md, IMPLEMENTATION_GUIDE.md, RISK_ASSESSMENT.md, FILE_OUTLINE.md
   - **Step 2 analysis**: SPARC methodology documents if they exist
   - **Current project state**: Any existing code, documentation, or architectural decisions

2. **Domain Selection**: Identify which expert context files to create based on:
   - User-specified domains from arguments
   - Project requirements from Step 1 documents
   - Technology stack from IMPLEMENTATION_GUIDE.md
   - Complexity and needs assessment

3. **Create Expert Context Files** for relevant domains:

   **Core Expert Categories**:
   - `project_type_expert.md` - Domain-specific best practices and patterns for the specific type of software
   - `architecture_expert.md` - System design and architectural decisions
   - `methodology_expert.md` - Development process and team coordination  
   - `tech_stack_expert.md` - Technology-specific guidance and optimization
   - `tools_expert.md` - Development tools and productivity systems

   **Implementation-Specific Experts** (as needed):
   - `auth_expert.md` - Authentication and security systems
   - `database_expert.md` - Data modeling and database optimization
   - `api_expert.md` - API design and integration patterns
   - `ui_expert.md` - User interface and experience design
   - `performance_expert.md` - Performance optimization strategies
   - `security_expert.md` - Security best practices and compliance

   **Process and Communication Experts**:
   - `orchestrator_expert.md` - Task routing and coordination guidance
   - `ask_expert.md` - User interaction and requirement gathering
   - `code_expert.md` - Implementation strategies and coding standards
   - `debug_expert.md` - Troubleshooting and issue resolution
   - `phase_tracker_expert.md` - Project progress and milestone management
   - `documentation_expert.md` - Documentation creation and maintenance
   - `error_handling_expert.md` - Error management and recovery strategies
   - `research_expert.md` - Domain and technology research capabilities
   - `truth_validator_expert.md` - Information accuracy and assumption validation
   - `api_matcher_expert.md` - Interface consistency and data mapping

   **Agentic Framework Experts**:
   - `agent_coordination_expert.md` - Multi-agent coordination patterns and optimization
   - `emergent_architecture_expert.md` - Architecture evolution and system coherence guidance
   - `collaborative_intelligence_expert.md` - Collective decision-making optimization
   - `adaptive_learning_expert.md` - Learning systems and coordination improvement mechanisms
   - `quality_validation_expert.md` - Continuous validation and multi-agent quality assurance
   - `workflow_integration_expert.md` - Integration across Steps 1-4 and legacy systems
   - `legacy_migration_expert.md` - Legacy system updating and migration

4. **Agentic Framework Integration**: Each expert file must include:

   **Agent Autonomy Section**:
   - **Decision Boundaries**: What decisions this expert can make independently
   - **Escalation Criteria**: When to escalate decisions to other experts or coordination systems
   - **Autonomous Capabilities**: What this expert can accomplish without external coordination

   **Collaboration Protocols**:
   - **Cross-Expert Integration**: How this expert coordinates with other domain experts
   - **Knowledge Sharing Mechanisms**: How this expert shares insights with the agent ecosystem
   - **Collective Decision Participation**: How this expert participates in multi-agent decisions

   **Continuous Validation Framework**:
   - **Real-Time Validation**: How this expert validates recommendations in real-time
   - **Quality Gates**: Automated quality checks and validation criteria
   - **Feedback Integration**: How this expert incorporates feedback and learning

   **Adaptive Learning System**:
   - **Performance Tracking**: How this expert measures and improves effectiveness
   - **Pattern Recognition**: How this expert identifies and learns from successful patterns
   - **Knowledge Evolution**: How this expert's knowledge base evolves over time

   **Emergency Coordination Protocols**:
   - **Critical Issue Detection**: How this expert identifies urgent issues requiring immediate attention
   - **Emergency Escalation**: Procedures for escalating critical issues
   - **Coordination Breakdown Recovery**: How this expert responds when coordination systems fail

5. **Expert File Structure**: Each expert file follows the enhanced template with:
   - **Expertise Domain**: Clear definition and project context integration
   - **Agentic Framework Integration**: Complete integration with all agentic principles
   - **Core Knowledge Areas**: Domain-specific best practices and guidelines
   - **Decision Framework**: Collaborative decision-making protocols
   - **Quality Criteria**: Collaborative effectiveness metrics
   - **Integration Points**: Connections with other experts and project aspects
   - **PACT Integration Points**: Integration with Planning, Action, Coordination, Testing phases
   - **Legacy System Compatibility**: Handling legacy systems and migration requirements

6. **Create Copilot Instructions**: Generate `.copilot-instructions.md` that:
   - **References all project files**: Essential files, expert context files, SPARC documents
   - **BACKLOG-First Workflow**: Provides clear workflow for implementing user requests from BACKLOG.md
   - **Expert System Integration**: Guidelines for using expert files and agent coordination
   - **Quality Assurance Integration**: Quality gates and validation procedures
   - **Workflow Access Framework**: Integration with Steps 1-4 and cross-step communication protocols

7. **Agent Hooks System** (if requested): Create `agent-hooks.md` for:
   - **Task Lifecycle Hooks**: Pre-task setup, validation, post-task cleanup procedures
   - **Inter-Agent Communication Hooks**: Agent handoff and collaboration coordination
   - **Quality Assurance Hooks**: Validation gates and review mechanisms
   - **Error Handling and Escalation Hooks**: Detection, recovery, and escalation procedures
   - **Workflow State Management Hooks**: Phase transitions and milestone validation

8. **Legacy System Update Framework**: When updating existing expert files:
   - **Legacy Analysis**: Assess existing components and compatibility
   - **Update Strategy Selection**: Choose gradual integration, parallel migration, or full replacement
   - **Agentic Enhancement**: Add autonomy, collaboration, validation, and learning capabilities
   - **Migration Validation**: Ensure backward compatibility and knowledge preservation

9. **Expert File Questions**: For each expert domain, consider:
   - What are the 5-10 most important things to know in this domain for this project?
   - What decisions will need to be made, and what criteria should guide them?
   - What are the most common mistakes or pitfalls to avoid?
   - What tools, resources, or frameworks are essential?
   - How does this domain interact with other aspects of the project?
   - What quality standards or metrics should be applied?
   - What troubleshooting knowledge is crucial?

10. **Report Completion**: Provide summary of:
    - Generated expert context files and their specializations
    - Agentic framework integration status and capabilities
    - Integration points with existing project documentation
    - Copilot instructions and agent hooks setup status
    - Recommended usage patterns for expert consultation

**Creation Guidelines**:

- Start with the most critical experts for the project
- Ensure comprehensive but focused coverage for each domain
- Cross-reference between expert files where domains overlap
- Include specific examples and code snippets where helpful
- Validate integration across all expert files for consistency
- Maintain alignment with project constraints and goals

Store expert files in `step_3/` directory using absolute paths and ensure all files integrate seamlessly with the existing project structure and methodologies.
