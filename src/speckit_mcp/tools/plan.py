"""
Plan MCP Tool

Generates detailed implementation plans from feature specifications.
"""

import json
from pathlib import Path
from typing import Dict, Any

from fastmcp import FastMCP


def plan_tool(mcp: FastMCP):
    """MCP tool for generating implementation plans."""

    @mcp.tool()
    def plan(feature_path: str) -> Dict[str, Any]:
        """
        Generate an implementation plan from a feature specification.

        Args:
            feature_path: Path to the feature directory containing spec.md

        Returns:
            Information about the generated implementation plan
        """
        try:
            feature_dir = Path(feature_path)
            if not feature_dir.exists():
                return {
                    "success": False,
                    "error": f"Feature directory does not exist: {feature_path}"
                }

            spec_file = feature_dir / "spec.md"
            if not spec_file.exists():
                return {
                    "success": False,
                    "error": f"Specification file not found: {spec_file}"
                }

            # Read the specification
            spec_content = spec_file.read_text()

            # Generate implementation plan template
            plan_content = f"""# Implementation Plan

## Overview
Implementation plan for the feature specification in `spec.md`.

## Architecture

### System Components
- **Frontend**: User interface components
- **Backend**: Business logic and API endpoints
- **Database**: Data models and storage
- **Integration**: External system connections

### Technology Stack
- **Framework**: [To be determined based on project]
- **Database**: [To be determined based on requirements]
- **Authentication**: [If required]
- **Testing**: Unit tests, integration tests

## Implementation Phases

### Phase 1: Data Model Implementation
1. **Database Schema**
   - Create entity tables based on domain analysis
   - Define relationships and constraints
   - Set up indexes for performance

2. **Data Access Layer**
   - Implement repository patterns
   - Create data validation rules
   - Set up migration scripts

### Phase 2: Business Logic
1. **Core Services**
   - Implement business rules from specification
   - Create service interfaces
   - Add validation and error handling

2. **API Layer**
   - Design REST/GraphQL endpoints
   - Implement request/response models
   - Add authentication and authorization

### Phase 3: User Interface
1. **Frontend Components**
   - Create UI components based on entities
   - Implement forms and validation
   - Add responsive design

2. **User Experience**
   - Implement workflows
   - Add feedback and notifications
   - Create help and documentation

### Phase 4: Integration & Testing
1. **External Integrations**
   - Implement API connections
   - Set up data synchronization
   - Add error handling and retries

2. **Testing & Quality**
   - Write comprehensive tests
   - Perform security testing
   - Conduct performance testing

## File Structure
```
src/
├── models/          # Data models and entities
├── services/        # Business logic services
├── api/            # API endpoints and controllers
├── ui/             # User interface components
├── integrations/   # External system integrations
└── tests/          # Test suites
```

## Dependencies
- Core framework dependencies
- Database drivers and ORM
- Authentication libraries
- Testing frameworks
- Integration libraries

## Deployment Strategy
1. **Development Environment**
   - Local development setup
   - Database migrations
   - Environment configuration

2. **Testing Environment**
   - Automated testing pipeline
   - Integration testing
   - Performance benchmarks

3. **Production Deployment**
   - Container orchestration
   - Database backup and recovery
   - Monitoring and logging

## Risk Assessment
- **Technical Risks**: Complexity, performance, scalability
- **Integration Risks**: External system dependencies
- **Timeline Risks**: Resource availability, scope creep

## Success Criteria
- All acceptance criteria met
- Performance requirements satisfied
- Security standards complied with
- Code quality standards achieved

## Next Steps
1. Review and approve implementation plan
2. Use `/tasks` to break down into specific tasks
3. Set up development environment
4. Begin Phase 1 implementation
"""

            plan_file = feature_dir / "plan.md"
            plan_file.write_text(plan_content)

            return {
                "success": True,
                "plan_file": str(plan_file),
                "feature_directory": str(feature_dir),
                "next_steps": [
                    "Review the generated implementation plan",
                    "Use /tasks to break down into specific actionable tasks",
                    "Set up development environment",
                    "Begin implementation following the planned phases"
                ]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate implementation plan: {str(e)}"
            }

    return plan_tool