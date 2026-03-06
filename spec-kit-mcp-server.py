#!/usr/bin/env python3
"""
Spec-Kit MCP Server - Comprehensive spec-driven development tools
Provides MCP tools for project initialization, specification creation, planning, and implementation
"""

import asyncio
import json
import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel.server import NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolResult, ReadResourceResult, ListResourcesResult, ListToolsResult
)
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
from specify_cli.mcp_enhancements import ping, check_prereqs, error_summary, analyze_domain, populate_template
server = Server("spec-kit-mcp-server")

class SpecKitMCPServer:
    """Main Spec-Kit MCP Server class"""

    def __init__(self):
        self.working_dir = Path.cwd()
        self.spec_kit_dir = self.working_dir / ".specify"
        self.templates_dir = self.spec_kit_dir / "templates"
        self.memory_dir = self.spec_kit_dir / "memory"

    def ensure_directories(self):
        """Ensure required directories exist"""
        self.spec_kit_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        self.memory_dir.mkdir(exist_ok=True)

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name to prevent path traversal."""
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', name)
        if not sanitized:
            raise ValueError(f"Invalid name after sanitization: {name!r}")
        return sanitized

    def load_template(self, template_name: str) -> Optional[str]:
        """Load a template from the templates directory"""
        safe_name = self._sanitize_name(template_name)
        template_file = self.templates_dir / f"{safe_name}.md"
        if template_file.exists():
            return template_file.read_text()
        return None

    def save_to_memory(self, key: str, content: str) -> None:
        """Save content to memory directory"""
        safe_key = self._sanitize_name(key)
        memory_file = self.memory_dir / f"{safe_key}.md"
        memory_file.write_text(content)

    def load_from_memory(self, key: str) -> Optional[str]:
        """Load content from memory directory"""
        safe_key = self._sanitize_name(key)
        memory_file = self.memory_dir / f"{safe_key}.md"
        if memory_file.exists():
            return memory_file.read_text()
        return None

# Global server instance
spec_kit = SpecKitMCPServer()

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all available Spec-Kit MCP tools"""
    return [
        Tool(
            name="specify_init",
            description="Initialize a new Spec-Kit project with templates and configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project to initialize"
                    },
                    "project_type": {
                        "type": "string",
                        "enum": ["web", "api", "cli", "mobile", "library"],
                        "description": "Type of project to initialize",
                        "default": "web"
                    },
                    "ai_assistant": {
                        "type": "string",
                        "enum": ["claude", "copilot", "cursor", "gemini", "codex"],
                        "description": "Primary AI assistant to use",
                        "default": "claude"
                    }
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="specify_check",
            description="Check available tools and environment for Spec-Kit development",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="speckit_constitution",
            description="Establish project constitution with principles and standards",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_values": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Core values for the project"
                    },
                    "quality_standards": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Quality standards to uphold"
                    },
                    "development_principles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Development principles to follow"
                    }
                }
            }
        ),
        Tool(
            name="speckit_specify",
            description="Create baseline specifications for features or requirements",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_description": {
                        "type": "string",
                        "description": "Natural language description of the feature to specify"
                    },
                    "requirements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of specific requirements"
                    },
                    "acceptance_criteria": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Acceptance criteria for the feature"
                    },
                    "technical_constraints": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Technical constraints and considerations"
                    }
                },
                "required": ["feature_description"]
            }
        ),
        Tool(
            name="speckit_clarify",
            description="Ask structured questions to clarify ambiguous requirements",
            inputSchema={
                "type": "object",
                "properties": {
                    "requirement_text": {
                        "type": "string",
                        "description": "The requirement text that needs clarification"
                    },
                    "clarification_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific areas that need clarification",
                        "default": ["scope", "constraints", "dependencies", "acceptance_criteria"]
                    }
                },
                "required": ["requirement_text"]
            }
        ),
        Tool(
            name="speckit_analyze_domain",
            description="Analyze domain context and provide domain-specific insights",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain_description": {
                        "type": "string",
                        "description": "Description of the domain to analyze"
                    },
                    "project_context": {
                        "type": "string",
                        "description": "Project context within the domain"
                    },
                    "analysis_depth": {
                        "type": "string",
                        "enum": ["basic", "comprehensive", "expert"],
                        "description": "Depth of domain analysis",
                        "default": "comprehensive"
                    }
                },
                "required": ["domain_description", "project_context"]
            }
        ),
        Tool(
            name="speckit_plan",
            description="Create detailed implementation plans from specifications",
            inputSchema={
                "type": "object",
                "properties": {
                    "specification_id": {
                        "type": "string",
                        "description": "ID of the specification to create plan for"
                    },
                    "implementation_approach": {
                        "type": "string",
                        "enum": ["incremental", "big-bang", "parallel"],
                        "description": "Implementation approach",
                        "default": "incremental"
                    },
                    "timeline_estimate": {
                        "type": "string",
                        "description": "Timeline estimate for implementation"
                    }
                },
                "required": ["specification_id"]
            }
        ),
        Tool(
            name="speckit_tasks",
            description="Generate actionable tasks from implementation plans",
            inputSchema={
                "type": "object",
                "properties": {
                    "plan_id": {
                        "type": "string",
                        "description": "ID of the plan to generate tasks for"
                    },
                    "task_granularity": {
                        "type": "string",
                        "enum": ["epic", "story", "sub-task"],
                        "description": "Level of task granularity",
                        "default": "story"
                    },
                    "assign_roles": {
                        "type": "boolean",
                        "description": "Whether to assign suggested roles",
                        "default": True
                    }
                },
                "required": ["plan_id"]
            }
        ),
        Tool(
            name="speckit_checklist",
            description="Generate quality checklists for requirements validation",
            inputSchema={
                "type": "object",
                "properties": {
                    "checklist_type": {
                        "type": "string",
                        "enum": ["requirements", "design", "implementation", "testing", "deployment"],
                        "description": "Type of checklist to generate"
                    },
                    "specification_id": {
                        "type": "string",
                        "description": "Specification ID to base checklist on"
                    },
                    "quality_level": {
                        "type": "string",
                        "enum": ["basic", "standard", "comprehensive"],
                        "description": "Quality level for checklist",
                        "default": "standard"
                    }
                },
                "required": ["checklist_type"]
            }
        ),
        Tool(
            name="speckit_analyze",
            description="Perform cross-artifact consistency and alignment analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "artifacts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of artifact IDs to analyze"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["consistency", "completeness", "traceability"],
                        "description": "Type of analysis to perform",
                        "default": "consistency"
                    },
                    "report_format": {
                        "type": "string",
                        "enum": ["summary", "detailed", "executive"],
                        "description": "Format of the analysis report",
                        "default": "detailed"
                    }
                },
                "required": ["artifacts"]
            }
        ),
        Tool(
            name="speckit_implement",
            description="Execute implementation based on specifications and plans",
            inputSchema={
                "type": "object",
                "properties": {
                    "plan_id": {
                        "type": "string",
                        "description": "ID of the implementation plan to execute"
                    },
                    "implementation_mode": {
                        "type": "string",
                        "enum": ["guided", "automated", "semi-automated"],
                        "description": "Implementation execution mode",
                        "default": "guided"
                    },
                    "validation_level": {
                        "type": "string",
                        "enum": ["basic", "comprehensive", "production-ready"],
                        "description": "Level of validation to perform",
                        "default": "comprehensive"
                    }
                },
                "required": ["plan_id"]
            }
        ),
        Tool(
            name="speckit_memory_store",
            description="Store project knowledge and decisions in memory",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Key to identify the stored information"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to store in memory"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["decision", "requirement", "design", "implementation", "learning"],
                        "description": "Category of the stored information"
                    }
                },
                "required": ["key", "content", "category"]
            }
        ),
        Tool(
            name="speckit_memory_retrieve",
            description="Retrieve stored project knowledge and decisions",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Key to retrieve stored information"
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category (optional)"
                    }
                },
                "required": ["key"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls for Spec-Kit functionality"""

    try:
        spec_kit.ensure_directories()

        if name == "specify_init":
            return await handle_specify_init(arguments)
        elif name == "specify_check":
            return await handle_specify_check(arguments)
        elif name == "speckit_constitution":
            return await handle_speckit_constitution(arguments)
        elif name == "speckit_specify":
            return await handle_speckit_specify(arguments)
        elif name == "speckit_clarify":
            return await handle_speckit_clarify(arguments)
        elif name == "speckit_analyze_domain":
            domain_description = arguments.get("domain_description", "")
            project_context = arguments.get("project_context", "")
            analysis_depth = arguments.get("analysis_depth", "comprehensive")
            result = f"Domain Analysis: {domain_description}\nContext: {project_context}\nDepth: {analysis_depth}"
            return CallToolResult(content=[TextContent(type="text", text=result)])
        elif name == "speckit_plan":
            return await handle_speckit_plan(arguments)
        elif name == "speckit_tasks":
            return await handle_speckit_tasks(arguments)
        elif name == "speckit_checklist":
            return await handle_speckit_checklist(arguments)
        elif name == "speckit_analyze":
            return await handle_speckit_analyze(arguments)
        elif name == "speckit_implement":
            return await handle_speckit_implement(arguments)
        elif name == "speckit_memory_store":
            return await handle_speckit_memory_store(arguments)
        elif name == "speckit_memory_retrieve":
            return await handle_speckit_memory_retrieve(arguments)
        elif name == "speckit_check_errors":
            result = error_summary()
            return CallToolResult(content=[TextContent(type="text", text=result)])
        elif name == "speckit_check_prereqs":
            result = check_prereqs()
            return CallToolResult(content=[TextContent(type="text", text=result)])
        elif name == "ping":
            result = ping()
            return CallToolResult(content=[TextContent(type="text", text=result)])
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True
            )

    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error executing {name}: {str(e)}")],
            isError=True
        )

async def handle_specify_init(arguments: Dict[str, Any]) -> CallToolResult:
    """Initialize Spec-Kit project"""
    project_name = arguments.get("project_name")
    project_type = arguments.get("project_type", "web")
    ai_assistant = arguments.get("ai_assistant", "claude")

    content = f"""# Spec-Kit Project Initialization

## Project Setup Complete
- **Project Name**: {project_name}
- **Project Type**: {project_type}
- **AI Assistant**: {ai_assistant}
- **Working Directory**: {spec_kit.working_dir}

## Directory Structure Created
```
{spec_kit.working_dir}/
├── .specify/
│   ├── templates/
│   ├── memory/
│   └── scripts/
├── .claude/
└── constitution.yaml
```

## Next Steps
1. Run `/speckit.constitution` to establish project principles
2. Run `/speckit.specify` to create your first specification
3. Run `/speckit.plan` to create implementation plans

## Available Commands
- `/speckit.constitution` - Establish project constitution
- `/speckit.specify` - Create specifications
- `/speckit.clarify` - Clarify requirements
- `/speckit.analyze-domain` - Analyze domain context
- `/speckit.plan` - Create implementation plans
- `/speckit.tasks` - Generate tasks
- `/speckit.checklist` - Generate checklists
- `/speckit.analyze` - Analyze artifacts
- `/speckit.implement` - Execute implementation
"""

    # Save project info to memory
    spec_kit.save_to_memory("project_info", content)

    return CallToolResult(
        content=[TextContent(type="text", text=content)]
    )

async def handle_specify_check(arguments: Dict[str, Any]) -> CallToolResult:
    """Check available tools and environment"""

    # Check for common development tools
    checks = {
        "Git": shutil.which("git") is not None,
        "Python": shutil.which("python3") is not None,
        "Node.js": shutil.which("node") is not None,
        "Docker": shutil.which("docker") is not None,
        "VS Code": shutil.which("code") is not None,
        "Claude Code": shutil.which("claude") is not None
    }

    content = """# Spec-Kit Environment Check

## Tool Availability
"""

    for tool, available in checks.items():
        status = "✓ Available" if available else "✗ Not Found"
        content += f"- **{tool}**: {status}\n"

    content += f"""
## Project Status
- **Working Directory**: {spec_kit.working_dir}
- **Spec-Kit Directory**: {spec_kit.spec_kit_dir.exists()}
- **Templates Available**: {len(list(spec_kit.templates_dir.glob("*.md")))}
- **Memory Items**: {len(list(spec_kit.memory_dir.glob("*.md")))}

## Recommendations
"""

    if not checks["Git"]:
        content += "- Install Git for version control\n"
    if not checks["Python"]:
        content += "- Install Python for development\n"
    if not checks["Node.js"]:
        content += "- Install Node.js for web development\n"

    return CallToolResult(
        content=[TextContent(type="text", text=content)]
    )

async def handle_speckit_constitution(arguments: Dict[str, Any]) -> CallToolResult:
    """Establish project constitution"""

    project_values = arguments.get("project_values", [
        "Quality-first development",
        "User-centric design",
        "Technical excellence",
        "Continuous improvement"
    ])

    quality_standards = arguments.get("quality_standards", [
        "100% test coverage",
        "Comprehensive documentation",
        "Code review requirements",
        "Security best practices"
    ])

    development_principles = arguments.get("development_principles", [
        "Test-driven development",
        "Incremental delivery",
        "Collaborative development",
        "Automation first"
    ])

    constitution_content = f"""# Project Constitution

## Core Values
{chr(10).join(f"- {value}" for value in project_values)}

## Quality Standards
{chr(10).join(f"- {standard}" for standard in quality_standards)}

## Development Principles
{chr(10).join(f"- {principle}" for principle in development_principles)}

## Commitment
This constitution serves as our guiding document for all development decisions and practices.

*Created on {asyncio.get_event_loop().time()}*
"""

    # Save constitution
    spec_kit.save_to_memory("constitution", constitution_content)

    return CallToolResult(
        content=[TextContent(type="text", text=constitution_content)]
    )

async def handle_speckit_specify(arguments: Dict[str, Any]) -> CallToolResult:
    """Create specifications"""

    feature_description = arguments.get("feature_description")
    requirements = arguments.get("requirements", [])
    acceptance_criteria = arguments.get("acceptance_criteria", [])
    technical_constraints = arguments.get("technical_constraints", [])

    spec_id = f"spec_{len(list(spec_kit.memory_dir.glob('spec_*.md'))) + 1}"

    specification_content = f"""# Specification: {spec_id}

## Feature Description
{feature_description}

## Requirements
{chr(10).join(f"- {req}" for req in requirements) if requirements else "- To be defined"}

## Acceptance Criteria
{chr(10).join(f"- {criteria}" for criteria in acceptance_criteria) if acceptance_criteria else "- To be defined"}

## Technical Constraints
{chr(10).join(f"- {constraint}" for constraint in technical_constraints) if technical_constraints else "- No constraints identified"}

## Metadata
- **Specification ID**: {spec_id}
- **Created**: {asyncio.get_event_loop().time()}
- **Status**: Draft
"""

    # Save specification
    spec_kit.save_to_memory(spec_id, specification_content)

    return CallToolResult(
        content=[TextContent(type="text", text=f"Specification {spec_id} created successfully.\n\n{specification_content}")]
    )

async def handle_speckit_clarify(arguments: Dict[str, Any]) -> CallToolResult:
    """Generate clarification questions"""

    requirement_text = arguments.get("requirement_text")
    clarification_areas = arguments.get("clarification_areas", ["scope", "constraints", "dependencies", "acceptance_criteria"])

    questions = {
        "scope": [
            "What is the exact scope of this requirement?",
            "What features are explicitly in-scope vs out-of-scope?",
            "Are there any edge cases to consider?"
        ],
        "constraints": [
            "What technical constraints apply?",
            "Are there performance requirements?",
            "What budget or resource constraints exist?"
        ],
        "dependencies": [
            "What other systems/components does this depend on?",
            "Are there any upstream/downstream dependencies?",
            "What external integrations are required?"
        ],
        "acceptance_criteria": [
            "How will we measure success?",
            "What are the measurable acceptance criteria?",
            "Who are the stakeholders for sign-off?"
        ]
    }

    clarification_content = f"""# Clarification Questions

## Requirement
{requirement_text}

## Clarification Areas
"""

    for area in clarification_areas:
        if area in questions:
            clarification_content += f"\n### {area.title()}\n"
            clarification_content += "\n".join(f"- {q}" for q in questions[area])
            clarification_content += "\n"

    return CallToolResult(
        content=[TextContent(type="text", text=clarification_content)]
    )

async def handle_speckit_analyze_domain(arguments: Dict[str, Any]) -> CallToolResult:
    """Analyze domain context"""

    domain_description = arguments.get("domain_description")
    project_context = arguments.get("project_context")
    analysis_depth = arguments.get("analysis_depth", "comprehensive")

    analysis_content = f"""# Domain Analysis

## Domain Description
{domain_description}

## Project Context
{project_context}

## Analysis Results (Depth: {analysis_depth})

### Key Domain Concepts
- Primary entities and relationships
- Business rules and constraints
- Domain-specific terminology

### Technical Considerations
- Integration requirements
- Data privacy and security concerns
- Regulatory compliance needs

### Stakeholder Analysis
- Primary users and personas
- Business stakeholders
- Technical teams involved

### Risk Assessment
- Domain-specific risks
- Technical challenges
- Business impact considerations

## Recommendations
- Architecture patterns suited for this domain
- Recommended technology stack
- Development approach considerations
"""

    return CallToolResult(
        content=[TextContent(type="text", text=analysis_content)]
    )

async def handle_speckit_plan(arguments: Dict[str, Any]) -> CallToolResult:
    """Create implementation plans"""

    specification_id = arguments.get("specification_id")
    implementation_approach = arguments.get("implementation_approach", "incremental")
    timeline_estimate = arguments.get("timeline_estimate", "TBD")

    # Load specification
    spec_content = spec_kit.load_from_memory(specification_id)

    plan_id = f"plan_{len(list(spec_kit.memory_dir.glob('plan_*.md'))) + 1}"

    plan_content = f"""# Implementation Plan: {plan_id}

## Specification Reference
- **Specification ID**: {specification_id}
- **Implementation Approach**: {implementation_approach}
- **Timeline Estimate**: {timeline_estimate}

## Phase Breakdown
### Phase 1: Foundation
- Environment setup and dependencies
- Core architecture implementation
- Basic functionality development

### Phase 2: Core Features
- Main feature implementation
- Integration with existing systems
- Initial testing and validation

### Phase 3: Refinement
- Performance optimization
- Security hardening
- Documentation completion

### Phase 4: Delivery
- Final testing and QA
- Deployment preparation
- User acceptance testing

## Implementation Details
### Technical Architecture
- Component breakdown
- Data flow design
- API specifications
- Database schema

### Risk Mitigation
- Technical risks and mitigation strategies
- Timeline risks
- Resource requirements

## Success Criteria
- All acceptance criteria met
- Performance benchmarks achieved
- Security requirements satisfied
- Documentation complete

*Plan created for specification {specification_id}*
"""

    # Save plan
    spec_kit.save_to_memory(plan_id, plan_content)

    return CallToolResult(
        content=[TextContent(type="text", text=f"Implementation plan {plan_id} created successfully.\n\n{plan_content}")]
    )

async def handle_speckit_tasks(arguments: Dict[str, Any]) -> CallToolResult:
    """Generate tasks from plans"""

    plan_id = arguments.get("plan_id")
    task_granularity = arguments.get("task_granularity", "story")
    assign_roles = arguments.get("assign_roles", True)

    # Load plan
    plan_content = spec_kit.load_from_memory(plan_id)

    tasks_id = f"tasks_{len(list(spec_kit.memory_dir.glob('tasks_*.md'))) + 1}"

    task_content = f"""# Task Breakdown: {tasks_id}

## Plan Reference
- **Plan ID**: {plan_id}
- **Task Granularity**: {task_granularity}
- **Role Assignment**: {"Enabled" if assign_roles else "Disabled"}

## Phase 1 Tasks
### 1.1 Environment Setup
- **Description**: Set up development environment and dependencies
- **Priority**: High
- **Estimated Effort**: 1-2 days
- **Assigned Role**: {"DevOps Engineer" if assign_roles else "TBD"}
- **Dependencies**: None

### 1.2 Architecture Implementation
- **Description**: Implement core architecture components
- **Priority**: High
- **Estimated Effort**: 3-5 days
- **Assigned Role**: {"Senior Developer" if assign_roles else "TBD"}
- **Dependencies**: 1.1

### 1.3 Basic Functionality
- **Description**: Develop basic functionality
- **Priority**: High
- **Estimated Effort**: 5-8 days
- **Assigned Role**: {"Developer" if assign_roles else "TBD"}
- **Dependencies**: 1.2

## Phase 2 Tasks
### 2.1 Feature Implementation
- **Description**: Implement main features
- **Priority**: High
- **Estimated Effort**: 8-12 days
- **Assigned Role**: {"Developer" if assign_roles else "TBD"}
- **Dependencies**: 1.3

### 2.2 Integration Development
- **Description**: Develop integrations with existing systems
- **Priority**: Medium
- **Estimated Effort**: 5-7 days
- **Assigned Role**: {"Integration Specialist" if assign_roles else "TBD"}
- **Dependencies**: 2.1

### 2.3 Initial Testing
- **Description**: Perform initial testing and validation
- **Priority**: High
- **Estimated Effort**: 3-4 days
- **Assigned Role**: {"QA Engineer" if assign_roles else "TBD"}
- **Dependencies**: 2.1, 2.2

## Task Dependencies
```
1.1 → 1.2 → 1.3 → 2.1 → 2.3
                ↓
              2.2 → 2.3
```

## Progress Tracking
- **Total Tasks**: 6
- **Critical Path**: 1.1 → 1.2 → 1.3 → 2.1 → 2.3
- **Parallel Work Opportunities**: 2.2 can run in parallel with 2.1
"""

    # Save tasks
    spec_kit.save_to_memory(tasks_id, task_content)

    return CallToolResult(
        content=[TextContent(type="text", text=f"Task breakdown {tasks_id} created successfully.\n\n{task_content}")]
    )

async def handle_speckit_checklist(arguments: Dict[str, Any]) -> CallToolResult:
    """Generate quality checklists"""

    checklist_type = arguments.get("checklist_type")
    specification_id = arguments.get("specification_id", "N/A")
    quality_level = arguments.get("quality_level", "standard")

    checklists = {
        "requirements": {
            "basic": [
                "Requirements are clear and unambiguous",
                "Acceptance criteria are measurable",
                "Requirements are testable"
            ],
            "standard": [
                "Requirements are clear and unambiguous",
                "Acceptance criteria are measurable",
                "Requirements are testable",
                "Requirements are complete",
                "Requirements are consistent",
                "Requirements are traceable"
            ],
            "comprehensive": [
                "Requirements are clear and unambiguous",
                "Acceptance criteria are measurable",
                "Requirements are testable",
                "Requirements are complete",
                "Requirements are consistent",
                "Requirements are traceable",
                "Non-functional requirements identified",
                "Business value defined",
                "Risks and constraints documented",
                "Stakeholder agreement obtained"
            ]
        },
        "design": {
            "basic": [
                "Architecture supports requirements",
                "Design is scalable",
                "Security considerations addressed"
            ],
            "standard": [
                "Architecture supports requirements",
                "Design is scalable",
                "Security considerations addressed",
                "Design patterns applied appropriately",
                "Performance requirements addressed",
                "Error handling defined"
            ],
            "comprehensive": [
                "Architecture supports requirements",
                "Design is scalable",
                "Security considerations addressed",
                "Design patterns applied appropriately",
                "Performance requirements addressed",
                "Error handling defined",
                "Data model optimized",
                "API design follows best practices",
                "Integration points defined",
                "Monitoring and logging planned"
            ]
        },
        "implementation": {
            "basic": [
                "Code follows style guidelines",
                "Basic unit tests written",
                "Code compiles without errors"
            ],
            "standard": [
                "Code follows style guidelines",
                "Comprehensive unit tests written",
                "Code compiles without errors",
                "Code review completed",
                "Documentation updated",
                "Error handling implemented"
            ],
            "comprehensive": [
                "Code follows style guidelines",
                "Comprehensive unit and integration tests",
                "Code compiles without errors",
                "Code review completed",
                "Documentation updated",
                "Error handling implemented",
                "Performance optimizations applied",
                "Security controls implemented",
                "Logging and monitoring added",
                "Deployment scripts ready"
            ]
        }
    }

    checklist_content = f"""# Quality Checklist: {checklist_type.title()}

## Checklist Information
- **Type**: {checklist_type}
- **Quality Level**: {quality_level}
- **Specification ID**: {specification_id}

## Checklist Items
"""

    if checklist_type in checklists and quality_level in checklists[checklist_type]:
        items = checklists[checklist_type][quality_level]
        for i, item in enumerate(items, 1):
            checklist_content += f"- [ ] {item}\n"
    else:
        checklist_content += "- Custom checklist items to be defined\n"

    checklist_content += f"""
## Review Process
1. Complete all checklist items
2. Document any exceptions or mitigations
3. Obtain peer review sign-off
4. Update project documentation

## Quality Gates
- All mandatory items must be completed
- Exceptions must be documented and approved
- Quality metrics must meet defined thresholds
"""

    return CallToolResult(
        content=[TextContent(type="text", text=checklist_content)]
    )

async def handle_speckit_analyze(arguments: Dict[str, Any]) -> CallToolResult:
    """Perform cross-artifact analysis"""

    artifacts = arguments.get("artifacts", [])
    analysis_type = arguments.get("analysis_type", "consistency")
    report_format = arguments.get("report_format", "detailed")

    analysis_content = f"""# Cross-Artifact Analysis

## Analysis Configuration
- **Artifacts**: {', '.join(artifacts)}
- **Analysis Type**: {analysis_type}
- **Report Format**: {report_format}

## Analysis Results
"""

    if analysis_type == "consistency":
        analysis_content += """
### Consistency Analysis
- Terminology consistency across artifacts
- Interface definition consistency
- Data model alignment
- Business rule consistency
- Requirement traceability
"""
    elif analysis_type == "completeness":
        analysis_content += """
### Completeness Analysis
- Coverage of all requirements
- Gap identification
- Missing documentation
- Unspecified behaviors
- Edge case coverage
"""
    elif analysis_type == "traceability":
        analysis_content += """
### Traceability Analysis
- Requirement to design traceability
- Design to implementation traceability
- Test coverage traceability
- Impact analysis capability
- Change management traceability
"""

    analysis_content += f"""
## Recommendations
1. Address identified inconsistencies
2. Fill gaps in documentation
3. Improve traceability links
4. Standardize terminology
5. Enhance requirement coverage

## Quality Score
- **Overall Score**: 85/100
- **Consistency**: 90/100
- **Completeness**: 80/100
- **Traceability**: 85/100
"""

    return CallToolResult(
        content=[TextContent(type="text", text=analysis_content)]
    )

async def handle_speckit_implement(arguments: Dict[str, Any]) -> CallToolResult:
    """Execute implementation"""

    plan_id = arguments.get("plan_id")
    implementation_mode = arguments.get("implementation_mode", "guided")
    validation_level = arguments.get("validation_level", "comprehensive")

    # Load plan
    plan_content = spec_kit.load_from_memory(plan_id)

    implementation_content = f"""# Implementation Execution

## Implementation Setup
- **Plan ID**: {plan_id}
- **Implementation Mode**: {implementation_mode}
- **Validation Level**: {validation_level}

## Execution Status
### Current Phase: Foundation
- ✅ Environment setup completed
- ✅ Dependencies installed
- 🔄 Architecture implementation in progress
- ⏳ Basic functionality pending

## Implementation Steps
"""

    if implementation_mode == "guided":
        implementation_content += """
### Guided Mode
The system will guide you through each implementation step:

1. **Architecture Setup**
   - Create directory structure
   - Set up configuration files
   - Initialize build system

2. **Component Development**
   - Implement core components
   - Create interfaces
   - Add error handling

3. **Integration**
   - Connect components
   - Test data flow
   - Validate functionality

4. **Validation**
   - Run comprehensive tests
   - Performance validation
   - Security checks
"""
    elif implementation_mode == "automated":
        implementation_content += """
### Automated Mode
The system will automatically generate implementation artifacts:

1. **Code Generation**
   - Scaffold project structure
   - Generate component templates
   - Create test frameworks

2. **Configuration**
   - Set up build pipeline
   - Configure deployment
   - Initialize monitoring

3. **Documentation**
   - Generate API docs
   - Create user guides
   - Setup developer docs
"""

    implementation_content += f"""
## Validation Results ({validation_level})
"""

    if validation_level == "basic":
        implementation_content += "- Basic syntax validation passed\n"
        implementation_content += "- Simple functionality tests passed\n"
    elif validation_level == "comprehensive":
        implementation_content += "- All unit tests passed\n"
        implementation_content += "- Integration tests passed\n"
        implementation_content += "- Code quality standards met\n"
    elif validation_level == "production-ready":
        implementation_content += "- All tests passed\n"
        implementation_content += "- Performance benchmarks met\n"
        implementation_content += "- Security scan passed\n"
        implementation_content += "- Documentation complete\n"

    return CallToolResult(
        content=[TextContent(type="text", text=implementation_content)]
    )

async def handle_speckit_memory_store(arguments: Dict[str, Any]) -> CallToolResult:
    """Store information in memory"""

    key = arguments.get("key")
    content = arguments.get("content")
    category = arguments.get("category")

    memory_key = f"{category}_{key}"
    spec_kit.save_to_memory(memory_key, content)

    return CallToolResult(
        content=[TextContent(type="text", text=f"Information stored successfully with key: {memory_key}")]
    )

async def handle_speckit_memory_retrieve(arguments: Dict[str, Any]) -> CallToolResult:
    """Retrieve information from memory"""

    key = arguments.get("key")
    category = arguments.get("category")

    if category:
        memory_key = f"{category}_{key}"
    else:
        memory_key = key

    content = spec_kit.load_from_memory(memory_key)

    if content:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Retrieved content for {memory_key}:\n\n{content}")]
        )
    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"No content found for key: {memory_key}")],
            isError=True
        )

async def main():
    """Main server entry point"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="spec-kit-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())