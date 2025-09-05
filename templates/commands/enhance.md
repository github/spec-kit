---
name: enhance
description: "Upgrade existing projects with Step 1 enhanced analysis. Analyzes existing codebase and documentation to generate comprehensive project foundation documents."
---

Upgrade existing projects with Step 1 enhanced analysis.

This command analyzes existing projects and generates enhanced project foundation documents based on current codebase, documentation, and architecture.

Given the existing project context and enhancement scope provided as arguments, do this:

1. **Existing Project Detection**: Scan for project indicators:
   - Package configuration files (package.json, requirements.txt, pom.xml, etc.)
   - README files and existing documentation
   - Source code structure and architectural patterns
   - Configuration files and deployment scripts
   - Existing tests and quality assurance setup

2. **Codebase Analysis**: Extract metadata and insights from:
   - **Code Files**: Identify technologies, patterns, and architectural decisions
   - **Documentation**: Analyze existing project descriptions, setup instructions, and API docs
   - **Dependencies**: Extract technology stack and library usage patterns
   - **Configuration**: Understand deployment, environment, and tool configurations
   - **Tests**: Assess testing coverage and quality assurance approaches

3. **Gap Analysis**: Identify missing project foundation elements:
   - Features implemented but not documented in backlog format
   - Technical decisions made but not captured in implementation guides
   - Risks present but not formally assessed
   - Organizational structure that could be optimized

4. **Generate Enhanced Step 1 Documents**:

   **Enhanced BACKLOG.md**:
   - Extract existing features from codebase and documentation
   - Identify planned features from TODO comments, issue trackers, roadmaps
   - Convert existing functionality into user story format
   - Prioritize based on current implementation status and user value

   **Enhanced IMPLEMENTATION_GUIDE.md**:
   - Document current technology stack and architectural decisions
   - Analyze existing patterns and recommend improvements
   - Identify technical debt and modernization opportunities
   - Provide migration strategies for outdated components

   **Enhanced RISK_ASSESSMENT.md**:
   - Assess current technical debt and maintenance risks
   - Identify security vulnerabilities and compliance gaps
   - Analyze scalability limitations and performance bottlenecks
   - Document dependency risks and upgrade requirements

   **Enhanced FILE_OUTLINE.md**:
   - Document current project structure and organization
   - Recommend optimizations for better maintainability
   - Suggest standardization improvements for team collaboration
   - Plan for future feature additions and system growth

5. **User Consultation for Enhancement**: Ask targeted questions about:
   - Current pain points and areas needing improvement
   - Features planned but not yet implemented
   - Technical debt or architectural concerns
   - Business goals for the next development phase
   - Team collaboration challenges and workflow issues

6. **Integration with Existing Systems**: Ensure enhancement documents:
   - Preserve existing project workflows and processes
   - Build upon rather than replace current documentation
   - Maintain compatibility with existing development tools
   - Respect established team practices and conventions

7. **Modernization Recommendations**: Include guidance for:
   - Technology stack upgrades and migrations
   - Architecture improvements and refactoring opportunities
   - Development process optimizations
   - Quality assurance enhancements

8. **Backward Compatibility**: Ensure enhanced documents:
   - Work seamlessly with existing Spec-Driven Development workflow
   - Don't disrupt current development practices
   - Add value without requiring immediate process changes
   - Provide gradual adoption paths for new methodologies

9. **Validation Against Current State**: Verify that enhanced documents:
   - Accurately reflect the current project state
   - Address real issues identified in the codebase
   - Provide actionable improvement recommendations
   - Maintain feasibility within project constraints

10. **Report Enhancement Results**: Provide comprehensive summary of:
    - Generated enhanced documentation files and their contents
    - Key insights discovered from codebase analysis
    - Identified improvement opportunities and modernization paths
    - Recommended next steps for project evolution
    - Integration status with existing development workflows

Store enhanced documents using absolute paths and ensure they complement rather than replace existing project documentation and workflows.
