---
name: sparc
description: "Apply SPARC methodology to project or feature development. Guides through Specification, Pseudocode, Architecture, Refinement, and Completion phases with comprehensive documentation."
---

Apply SPARC methodology to project or feature development.

This command implements the SPARC (Specification, Pseudocode, Architecture, Refinement, Completion) methodology for systematic software development.

## Overview for AI Agents

SPARC (Specification, Pseudocode, Architecture, Refinement, Completion) is a structured methodology that transforms software development from ad-hoc coding into a disciplined, systematic approach. Each phase builds upon the previous one, ensuring comprehensive coverage and maintainability.

**Core Flow**: S → P → A → R → C (Specification → Pseudocode → Architecture → Refinement → Completion)

## Key Principles for Agents

1. **Sequential Development**: Each phase must be completed before moving to the next
2. **Comprehensive Documentation**: Every phase requires detailed markdown documentation
3. **Reflective Analysis**: Include justifications for all decisions and consider alternatives
4. **Test-Driven Approach**: Define testing criteria from the specification phase
5. **Iterative Refinement**: Each phase may require revisiting previous phases
6. **Stakeholder Communication**: Write documentation that technical and non-technical stakeholders can understand

Given the context provided as an argument, do this:

1. **Check for Existing Step 1 Documents**: Look for BACKLOG.md, IMPLEMENTATION_GUIDE.md, RISK_ASSESSMENT.md, and FILE_OUTLINE.md in the project directory

2. **Document Foundation Assessment**: If phase 1 documents exist:
   - Review existing documents and determine if they provide sufficient foundation
   - Check if they're current and complete
   - Assess whether to build upon them or start with Phase 2

3. **Phase Determination**: Determine which SPARC phase to execute based on:
   - Current project state and existing documentation
   - User-specified phase preference (if provided)
   - Project complexity and requirements

4. **User Consultation**: Before proceeding with documentation, ask the user:
   - If existing Step 1 documents found: Are they current and should be used as foundation?
   - What specific aspects of the project need attention?
   - Any constraints, preferences, or requirements to consider?
   - Which SPARC phase would be most beneficial to focus on?

5. **Execute Selected SPARC Phase**:

   **For Specification Phase**:
   
   **Your Role**: Requirements Analyst & Domain Expert
   
   **For Existing Projects**: If BACKLOG.md, IMPLEMENTATION_GUIDE.md, RISK_ASSESSMENT.md, and FILE_OUTLINE.md exist, use them as your foundation and enhance the specification by:
   - Converting backlog items into formal functional requirements
   - Expanding implementation guide into detailed technical constraints
   - Incorporating risk assessment into assumptions and mitigation strategies
   - Using file outline to inform technical architecture constraints

   **Create comprehensive specification document with**:
   - **Existing Documents Review** (if applicable): Summary of how existing phase 1 documents inform this specification
   - **Project Overview**: Clear statement of goals, target audience, and scope
   - **Functional Requirements**: Detailed feature descriptions broken into manageable components
   - **Non-Functional Requirements**: Performance, security, usability, reliability standards
   - **User Scenarios**: Detailed user flow descriptions with step-by-step interactions
   - **UI/UX Guidelines**: Design principles, style guidelines, user experience standards
   - **Technical Constraints**: Technology preferences, limitations, integration requirements
   - **Assumptions**: All assumptions made during specification with justifications
   - **Success Criteria**: Measurable criteria for project success
   - **Reflection**: Justify decisions made, consider alternatives, discuss potential challenges

   **For Pseudocode Phase**:
   
   **Your Role**: Algorithm Designer & Logic Architect
   
   Transform specifications into high-level algorithmic design:
   - **High-Level System Flow**: Overall application logic and data flow
   - **Core Algorithms**: Detailed pseudocode for all major functions with complexity analysis
   - **Data Structures**: Define all data models, schemas, and structures
   - **Function Definitions**: High-level function signatures and purposes
   - **Error Handling Strategy**: How errors will be detected, handled, and reported
   - **Performance Considerations**: Algorithm complexity analysis, optimization opportunities
   - **Reflection**: Justify algorithmic choices, consider alternatives, identify potential issues

   **For Architecture Phase**:
   
   **Your Role**: System Architect & Technical Designer
   
   Define system architecture, component interactions, and technical design:
   - **System Architecture Overview**: High-level system design with component descriptions
   - **Architectural Style**: Pattern choice (MVC, Microservices, Layered, etc.) with justification
   - **Technology Stack**: Frontend, backend, database, infrastructure choices with justifications
   - **System Components**: Purpose, responsibilities, interfaces, and dependencies for each component
   - **Data Architecture**: Database schema, relationships, indexes, and data flow
   - **API Design**: Endpoints, request/response formats, authentication
   - **Security Architecture**: Authentication, authorization, data protection strategies
   - **Scalability Considerations**: How the system will handle growth
   - **Reflection**: Architectural decisions justification, alternatives considered, trade-offs

   **For Refinement Phase**:
   
   **Your Role**: Code Quality Engineer & Performance Optimizer
   
   Iteratively improve the design and implementation through testing and optimization:
   - **Testing Strategy**: Unit tests, integration tests, end-to-end tests, performance tests
   - **Test Cases**: Detailed test cases with Given/When/Then format
   - **Performance Optimization**: Identified bottlenecks and optimization strategies
   - **Code Quality Standards**: Coding conventions, documentation requirements
   - **Refactoring Plan**: Areas for improvement and refactoring strategies
   - **Review Checklist**: Comprehensive validation checklist for all requirements
   - **Reflection**: Analysis of design improvements, testing strategy justification

   **For Completion Phase**:
   
   **Your Role**: Deployment Engineer & Project Finalizer
   
   Finalize the project for production deployment:
   - **Deployment Strategy**: Environment configuration and deployment procedures
   - **Production Readiness Checklist**: Infrastructure, application, and documentation validation
   - **User Documentation**: Getting started guide, feature documentation, FAQ
   - **Monitoring and Maintenance**: Application monitoring, infrastructure monitoring, maintenance procedures
   - **Post-Launch Support**: Issue tracking, feature requests, support processes
   - **Project Summary**: Goals achieved, lessons learned, future enhancements
   - **Reflection**: Overall project assessment, process effectiveness, recommendations

6. **Integration with Step 1**: Ensure all SPARC documentation:
   - References and builds upon existing project foundation documents
   - Maintains consistency with established project context
   - Addresses risks and constraints identified in RISK_ASSESSMENT.md
   - Follows structure guidance from FILE_OUTLINE.md

7. **Quality Gates**: Include validation checkpoints for:
   - Completeness of phase documentation
   - Consistency with project objectives
   - Technical feasibility and viability
   - Integration with other project artifacts

8. **Template Application**: Use the appropriate phase template and customize it for the specific project requirements, ensuring all sections are thoroughly completed with thoughtful analysis.

9. **Report Completion**: Provide summary of:
   - Generated SPARC documentation files and their locations
   - Phase completion status and validation results
   - Recommended next phase or development steps
   - Integration points with existing project documentation

**Best Practices**:

- Always check for existing documents first
- Build upon existing work rather than duplicating effort
- Be comprehensive and don't skip sections
- Think critically and question assumptions
- Stay practical with actionable information
- Maintain consistency across phases
- Focus on quality over speed

Use absolute paths for all file operations and ensure SPARC documents follow the established methodology templates exactly.
