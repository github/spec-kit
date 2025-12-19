"""
MCP server implementation for spec-kit.

This module provides an MCP (Model Context Protocol) server that exposes
spec-kit functionality to AI assistants like Claude Desktop.

Tools exposed:
- speckit_specify: Generate specification from description
- speckit_clarify: Identify clarification questions
- speckit_plan: Generate technical plan
- speckit_tasks: Generate task breakdown
- speckit_analyze: Check artifact consistency
- speckit_list_features: List project features
- speckit_get_artifact: Get a specific artifact
"""

from pathlib import Path
from typing import Any, Optional

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None

from speckit.speckit import SpecKit


def create_server(project_path: Optional[Path] = None) -> Any:
    """
    Create and configure the MCP server.

    Args:
        project_path: Project directory (default: current directory)

    Returns:
        Configured MCP Server instance
    """
    if not MCP_AVAILABLE:
        raise ImportError(
            "MCP is not installed. Install with: pip install speckit-ai[mcp]"
        )

    # Initialize spec-kit
    kit = SpecKit(project_path or Path.cwd())

    # Create server
    server = Server("speckit")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="speckit_specify",
                description="Generate a feature specification from natural language description",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Natural language description of the feature",
                        },
                        "feature_id": {
                            "type": "string",
                            "description": "Optional custom feature ID",
                        },
                    },
                    "required": ["description"],
                },
            ),
            Tool(
                name="speckit_clarify",
                description="Identify clarification questions for a specification",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "feature_id": {
                            "type": "string",
                            "description": "Feature ID to clarify",
                        },
                        "max_questions": {
                            "type": "integer",
                            "description": "Maximum number of questions (default: 5)",
                            "default": 5,
                        },
                    },
                    "required": ["feature_id"],
                },
            ),
            Tool(
                name="speckit_plan",
                description="Generate a technical implementation plan",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "feature_id": {
                            "type": "string",
                            "description": "Feature ID to plan",
                        },
                    },
                    "required": ["feature_id"],
                },
            ),
            Tool(
                name="speckit_tasks",
                description="Generate implementation task breakdown",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "feature_id": {
                            "type": "string",
                            "description": "Feature ID to generate tasks for",
                        },
                    },
                    "required": ["feature_id"],
                },
            ),
            Tool(
                name="speckit_analyze",
                description="Check consistency across all artifacts",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "feature_id": {
                            "type": "string",
                            "description": "Feature ID to analyze",
                        },
                    },
                    "required": ["feature_id"],
                },
            ),
            Tool(
                name="speckit_list_features",
                description="List all features in the project",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="speckit_get_artifact",
                description="Get a specific artifact (spec, plan, or tasks)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "feature_id": {
                            "type": "string",
                            "description": "Feature ID",
                        },
                        "artifact_type": {
                            "type": "string",
                            "enum": ["spec", "plan", "tasks"],
                            "description": "Type of artifact to retrieve",
                        },
                    },
                    "required": ["feature_id", "artifact_type"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls."""
        try:
            if name == "speckit_specify":
                spec = kit.specify(
                    arguments["description"],
                    arguments.get("feature_id"),
                )
                kit.save(spec)
                return [TextContent(type="text", text=spec.to_markdown())]

            elif name == "speckit_clarify":
                spec = kit.load_specification(arguments["feature_id"])
                if not spec:
                    return [
                        TextContent(
                            type="text",
                            text=f"Error: Specification not found: {arguments['feature_id']}",
                        )
                    ]
                _, questions = kit.clarify(spec, arguments.get("max_questions", 5))
                if not questions:
                    return [TextContent(type="text", text="No clarification questions needed.")]
                result = "\n\n".join(q.to_markdown() for q in questions)
                return [TextContent(type="text", text=result)]

            elif name == "speckit_plan":
                spec = kit.load_specification(arguments["feature_id"])
                if not spec:
                    return [
                        TextContent(
                            type="text",
                            text=f"Error: Specification not found: {arguments['feature_id']}",
                        )
                    ]
                plan = kit.plan(spec)
                kit.save(plan)
                return [TextContent(type="text", text=plan.to_markdown())]

            elif name == "speckit_tasks":
                plan = kit.load_plan(arguments["feature_id"])
                if not plan:
                    return [
                        TextContent(
                            type="text",
                            text=f"Error: Plan not found: {arguments['feature_id']}",
                        )
                    ]
                tasks = kit.tasks(plan)
                kit.save(tasks)
                return [TextContent(type="text", text=tasks.to_markdown())]

            elif name == "speckit_analyze":
                feature_id = arguments["feature_id"]
                spec = kit.load_specification(feature_id)
                plan = kit.load_plan(feature_id)
                tasks = kit.load_tasks(feature_id)
                if not all([spec, plan, tasks]):
                    return [
                        TextContent(
                            type="text",
                            text=f"Error: Missing artifacts for: {feature_id}",
                        )
                    ]
                report = kit.analyze(spec, plan, tasks)
                return [TextContent(type="text", text=report.to_markdown())]

            elif name == "speckit_list_features":
                features = kit.list_features()
                if not features:
                    return [TextContent(type="text", text="No features found.")]
                result = "# Features\n\n" + "\n".join(f"- {f}" for f in features)
                return [TextContent(type="text", text=result)]

            elif name == "speckit_get_artifact":
                feature_id = arguments["feature_id"]
                artifact_type = arguments["artifact_type"]

                if artifact_type == "spec":
                    artifact = kit.load_specification(feature_id)
                elif artifact_type == "plan":
                    artifact = kit.load_plan(feature_id)
                elif artifact_type == "tasks":
                    artifact = kit.load_tasks(feature_id)
                else:
                    return [TextContent(type="text", text=f"Unknown artifact type: {artifact_type}")]

                if not artifact:
                    return [
                        TextContent(
                            type="text",
                            text=f"Error: {artifact_type} not found for: {feature_id}",
                        )
                    ]
                return [TextContent(type="text", text=artifact.to_markdown())]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    return server


async def run_server(project_path: Optional[Path] = None):
    """Run the MCP server."""
    server = create_server(project_path)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
