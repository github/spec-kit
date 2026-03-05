"""
Tasks MCP Tool

Breaks down implementation plans into structured, actionable tasks.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

from fastmcp import FastMCP


def tasks_tool(mcp: FastMCP):
    """MCP tool for generating structured task breakdown."""

    @mcp.tool()
    def tasks(feature_path: str) -> Dict[str, Any]:
        """
        Generate structured tasks from an implementation plan.

        Args:
            feature_path: Path to the feature directory containing plan.md

        Returns:
            Structured task breakdown with dependencies and priorities
        """
        try:
            feature_dir = Path(feature_path)
            if not feature_dir.exists():
                return {
                    "success": False,
                    "error": f"Feature directory does not exist: {feature_path}"
                }

            plan_file = feature_dir / "plan.md"
            if not plan_file.exists():
                return {
                    "success": False,
                    "error": f"Implementation plan not found: {plan_file}"
                }

            # Read the implementation plan
            plan_content = plan_file.read_text()

            # Generate task breakdown
            tasks_content = f"""# Task Breakdown

## Task Overview
Structured breakdown of implementation tasks based on the plan in `plan.md`.

## Task Categories

### ✅ Setup & Infrastructure
- [ ] **SETUP-001**: Initialize project structure
  - Priority: High
  - Estimated effort: 2 hours
  - Dependencies: None
  - Deliverable: Project scaffolding and build configuration

- [ ] **SETUP-002**: Set up development environment
  - Priority: High
  - Estimated effort: 4 hours
  - Dependencies: SETUP-001
  - Deliverable: Local development environment ready

- [ ] **SETUP-003**: Configure CI/CD pipeline
  - Priority: Medium
  - Estimated effort: 6 hours
  - Dependencies: SETUP-001
  - Deliverable: Automated testing and deployment

### 🏗️ Data Model Implementation
- [ ] **DATA-001**: Design database schema
  - Priority: High
  - Estimated effort: 8 hours
  - Dependencies: SETUP-002
  - Deliverable: Database schema and migration scripts

- [ ] **DATA-002**: Implement data entities
  - Priority: High
  - Estimated effort: 12 hours
  - Dependencies: DATA-001
  - Deliverable: Entity models with validation

- [ ] **DATA-003**: Create repository layer
  - Priority: High
  - Estimated effort: 10 hours
  - Dependencies: DATA-002
  - Deliverable: Data access layer with CRUD operations

### ⚙️ Business Logic
- [ ] **LOGIC-001**: Implement core business services
  - Priority: High
  - Estimated effort: 16 hours
  - Dependencies: DATA-003
  - Deliverable: Business logic services

- [ ] **LOGIC-002**: Add business rule validation
  - Priority: High
  - Estimated effort: 8 hours
  - Dependencies: LOGIC-001
  - Deliverable: Business rule enforcement

- [ ] **LOGIC-003**: Implement workflow processes
  - Priority: Medium
  - Estimated effort: 12 hours
  - Dependencies: LOGIC-002
  - Deliverable: Complete business workflows

### 🌐 API Development
- [ ] **API-001**: Design API endpoints
  - Priority: High
  - Estimated effort: 6 hours
  - Dependencies: LOGIC-001
  - Deliverable: API specification and documentation

- [ ] **API-002**: Implement REST endpoints
  - Priority: High
  - Estimated effort: 14 hours
  - Dependencies: API-001
  - Deliverable: Functional API endpoints

- [ ] **API-003**: Add authentication and authorization
  - Priority: High
  - Estimated effort: 10 hours
  - Dependencies: API-002
  - Deliverable: Secure API access

### 🎨 User Interface
- [ ] **UI-001**: Create component library
  - Priority: Medium
  - Estimated effort: 12 hours
  - Dependencies: API-002
  - Deliverable: Reusable UI components

- [ ] **UI-002**: Implement main user flows
  - Priority: High
  - Estimated effort: 18 hours
  - Dependencies: UI-001
  - Deliverable: Complete user interface

- [ ] **UI-003**: Add responsive design
  - Priority: Medium
  - Estimated effort: 8 hours
  - Dependencies: UI-002
  - Deliverable: Mobile-friendly interface

### 🔗 Integration
- [ ] **INT-001**: Implement external API connections
  - Priority: Medium
  - Estimated effort: 10 hours
  - Dependencies: API-003
  - Deliverable: External system integrations

- [ ] **INT-002**: Set up data synchronization
  - Priority: Medium
  - Estimated effort: 8 hours
  - Dependencies: INT-001
  - Deliverable: Automated data sync processes

### 🧪 Testing & Quality
- [ ] **TEST-001**: Write unit tests
  - Priority: High
  - Estimated effort: 16 hours
  - Dependencies: LOGIC-003
  - Deliverable: Comprehensive unit test suite

- [ ] **TEST-002**: Implement integration tests
  - Priority: High
  - Estimated effort: 12 hours
  - Dependencies: API-003
  - Deliverable: Integration test coverage

- [ ] **TEST-003**: Perform security testing
  - Priority: High
  - Estimated effort: 8 hours
  - Dependencies: TEST-002
  - Deliverable: Security validation and fixes

### 🚀 Deployment
- [ ] **DEPLOY-001**: Set up production environment
  - Priority: Medium
  - Estimated effort: 10 hours
  - Dependencies: TEST-003
  - Deliverable: Production-ready deployment

- [ ] **DEPLOY-002**: Configure monitoring and logging
  - Priority: Medium
  - Estimated effort: 6 hours
  - Dependencies: DEPLOY-001
  - Deliverable: Operational monitoring

## Task Summary
- **Total Tasks**: 20
- **Estimated Total Effort**: 200 hours
- **Critical Path**: SETUP → DATA → LOGIC → API → UI → TEST → DEPLOY
- **Parallel Work Possible**: UI and API development, Testing and Integration

## Sprint Planning Suggestions

### Sprint 1 (Setup & Foundation) - 2 weeks
- SETUP-001, SETUP-002, SETUP-003
- DATA-001, DATA-002

### Sprint 2 (Core Implementation) - 3 weeks
- DATA-003, LOGIC-001, LOGIC-002
- API-001, API-002

### Sprint 3 (User Interface) - 3 weeks
- API-003, UI-001, UI-002
- TEST-001 (parallel)

### Sprint 4 (Integration & Testing) - 2 weeks
- UI-003, INT-001, INT-002
- TEST-002, TEST-003

### Sprint 5 (Deployment) - 1 week
- DEPLOY-001, DEPLOY-002
- Final testing and launch

## Progress Tracking
Use `/task_progress` tool to update task status and track completion.
"""

            tasks_file = feature_dir / "tasks.md"
            tasks_file.write_text(tasks_content)

            # Create task summary for easy tracking
            task_summary = {
                "total_tasks": 20,
                "estimated_hours": 200,
                "sprints": 5,
                "critical_path": ["SETUP", "DATA", "LOGIC", "API", "UI", "TEST", "DEPLOY"],
                "categories": {
                    "setup": 3,
                    "data": 3,
                    "logic": 3,
                    "api": 3,
                    "ui": 3,
                    "integration": 2,
                    "testing": 3,
                    "deployment": 2
                }
            }

            return {
                "success": True,
                "tasks_file": str(tasks_file),
                "feature_directory": str(feature_dir),
                "task_summary": task_summary,
                "next_steps": [
                    "Review task breakdown and adjust estimates",
                    "Use /task_progress to track completion",
                    "Begin with Sprint 1 tasks",
                    "Set up project tracking system"
                ]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate task breakdown: {str(e)}"
            }

    return tasks_tool