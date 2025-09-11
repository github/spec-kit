#!/usr/bin/env python3
"""
MCP Server for Spec-Kit - Spec-Driven Development Toolkit

This MCP server exposes all the functionality of the spec-kit CLI and scripts
as MCP tools that can be used by AI agents.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    Tool,
    TextContent,
    EmptyResult,
)

# Import our existing functionality
from .cli import (
    run_command,
    check_tool,
    is_git_repo,
    init_git_repo,
    download_and_extract_template,
    AI_CHOICES,
)
from .scripts import (
    run_script,
    get_available_scripts,
    test_script_compatibility,
    get_platform,
    is_windows,
)
from .onboarding import (
    analyze_project_structure,
    parse_existing_documentation,
    extract_requirements_from_code,
    generate_standardized_spec,
    create_migration_plan,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the MCP server
server = Server("spec-kit")


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="init_project",
            description="Initialize a new Spec-Kit project from the latest template",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name for your new project directory (optional if using current directory)"
                    },
                    "ai_assistant": {
                        "type": "string",
                        "enum": ["claude", "gemini", "copilot"],
                        "description": "AI assistant to use: claude, gemini, or copilot"
                    },
                    "use_current_dir": {
                        "type": "boolean",
                        "default": False,
                        "description": "Initialize project in the current directory instead of creating a new one"
                    },
                    "ignore_agent_tools": {
                        "type": "boolean", 
                        "default": False,
                        "description": "Skip checks for AI agent tools like Claude Code"
                    },
                    "no_git": {
                        "type": "boolean",
                        "default": False,
                        "description": "Skip git repository initialization"
                    }
                },
                "required": ["ai_assistant"]
            }
        ),
        Tool(
            name="check_requirements",
            description="Check that all required tools are installed for Spec-Kit",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="list_scripts",
            description="Show available scripts and platform compatibility",
            inputSchema={
                "type": "object", 
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="create_new_feature",
            description="Create a new feature with branch, directory structure, and template",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_description": {
                        "type": "string",
                        "description": "Description of the feature to create"
                    },
                    "repo_root": {
                        "type": "string",
                        "description": "Repository root path (auto-detected if not provided)"
                    }
                },
                "required": ["feature_description"]
            }
        ),
        Tool(
            name="setup_plan", 
            description="Set up implementation plan for the current feature",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_root": {
                        "type": "string",
                        "description": "Repository root path (auto-detected if not provided)"
                    }
                }
            }
        ),
        Tool(
            name="check_task_prerequisites",
            description="Check if task prerequisites are met for the current feature",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_root": {
                        "type": "string", 
                        "description": "Repository root path (auto-detected if not provided)"
                    }
                }
            }
        ),
        Tool(
            name="update_agent_context",
            description="Update agent context files with current feature information",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_root": {
                        "type": "string",
                        "description": "Repository root path (auto-detected if not provided)"
                    }
                }
            }
        ),
        Tool(
            name="get_feature_paths",
            description="Get all paths for the current feature (specs, plans, tasks, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_root": {
                        "type": "string",
                        "description": "Repository root path (auto-detected if not provided)"
                    }
                }
            }
        ),
        Tool(
            name="run_script",
            description="Run a cross-platform script (bash or Python) by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_name": {
                        "type": "string",
                        "description": "Name of the script to run (without extension)"
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Arguments to pass to the script",
                        "default": []
                    },
                    "repo_root": {
                        "type": "string",
                        "description": "Repository root path (auto-detected if not provided)"
                    }
                },
                "required": ["script_name"]
            }
        ),
        Tool(
            name="analyze_existing_project",
            description="Analyze the structure of an existing project to understand its organization and prepare for spec-driven development migration",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the existing project directory to analyze"
                    },
                    "max_depth": {
                        "type": "integer",
                        "default": 3,
                        "description": "Maximum directory depth to scan for analysis"
                    }
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="parse_existing_documentation",
            description="Parse existing documentation files to extract requirements, specifications, and other relevant information",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory containing documentation"
                    },
                    "file_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of file patterns to search for (e.g., ['*.md', 'README*'])",
                        "default": []
                    }
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="extract_requirements_from_code",
            description="Extract requirements and specifications from code comments, docstrings, and TODO/FIXME items",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory containing source code"
                    },
                    "file_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of file patterns to search for (e.g., ['*.py', '*.js'])",
                        "default": []
                    }
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="generate_standardized_spec",
            description="Generate a standardized specification document from existing project analysis data",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_analysis": {
                        "type": "object",
                        "description": "Project structure analysis result (from analyze_existing_project)"
                    },
                    "documentation_analysis": {
                        "type": "object", 
                        "description": "Documentation parsing result (from parse_existing_documentation)"
                    },
                    "code_analysis": {
                        "type": "object",
                        "description": "Code analysis result (from extract_requirements_from_code)"
                    }
                },
                "required": ["project_analysis", "documentation_analysis", "code_analysis"]
            }
        ),
        Tool(
            name="create_migration_plan",
            description="Create a detailed migration plan for adopting spec-driven development workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_analysis": {
                        "type": "object",
                        "description": "Project structure analysis result (from analyze_existing_project)"
                    },
                    "standardized_spec": {
                        "type": "object",
                        "description": "Standardized specification result (from generate_standardized_spec)"
                    }
                },
                "required": ["project_analysis", "standardized_spec"]
            }
        ),
        Tool(
            name="onboard_existing_project",
            description="Complete end-to-end onboarding of an existing project to spec-driven development (combines all analysis steps)",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the existing project directory"
                    },
                    "max_depth": {
                        "type": "integer",
                        "default": 3,
                        "description": "Maximum directory depth to scan"
                    },
                    "include_migration_plan": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether to include a detailed migration plan"
                    }
                },
                "required": ["project_path"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    try:
        if name == "init_project":
            return await handle_init_project(arguments)
        elif name == "check_requirements":
            return await handle_check_requirements(arguments)
        elif name == "list_scripts":
            return await handle_list_scripts(arguments)
        elif name == "create_new_feature":
            return await handle_create_new_feature(arguments)
        elif name == "setup_plan":
            return await handle_setup_plan(arguments)
        elif name == "check_task_prerequisites":
            return await handle_check_task_prerequisites(arguments)
        elif name == "update_agent_context":
            return await handle_update_agent_context(arguments)
        elif name == "get_feature_paths":
            return await handle_get_feature_paths(arguments)
        elif name == "run_script":
            return await handle_run_script(arguments)
        elif name == "analyze_existing_project":
            return await handle_analyze_existing_project(arguments)
        elif name == "parse_existing_documentation":
            return await handle_parse_existing_documentation(arguments)
        elif name == "extract_requirements_from_code":
            return await handle_extract_requirements_from_code(arguments)
        elif name == "generate_standardized_spec":
            return await handle_generate_standardized_spec(arguments)
        elif name == "create_migration_plan":
            return await handle_create_migration_plan(arguments)
        elif name == "onboard_existing_project":
            return await handle_onboard_existing_project(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )
            ]
        )


async def handle_init_project(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle project initialization."""
    project_name = arguments.get("project_name")
    ai_assistant = arguments["ai_assistant"]
    use_current_dir = arguments.get("use_current_dir", False)
    ignore_agent_tools = arguments.get("ignore_agent_tools", False)
    no_git = arguments.get("no_git", False)

    # Validate AI assistant
    if ai_assistant not in AI_CHOICES:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Invalid AI assistant '{ai_assistant}'. Choose from: {', '.join(AI_CHOICES.keys())}"
                )
            ]
        )

    # Determine project directory
    if use_current_dir:
        if project_name:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", 
                        text="Cannot specify both project_name and use_current_dir=True"
                    )
                ]
            )
        project_name = Path.cwd().name
        project_path = Path.cwd()
    else:
        if not project_name:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Must specify either a project name or set use_current_dir=True"
                    )
                ]
            )
        project_path = Path(project_name).resolve()
        if project_path.exists():
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Directory '{project_name}' already exists"
                    )
                ]
            )

    # Check git availability if needed
    git_available = True
    if not no_git:
        git_available = check_tool("git", "https://git-scm.com/downloads")

    # Check agent tools unless ignored
    if not ignore_agent_tools:
        if ai_assistant == "claude":
            if not check_tool("claude", "Install from: https://docs.anthropic.com/en/docs/claude-code/setup"):
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Claude CLI is required for Claude Code projects. Use ignore_agent_tools=True to skip this check."
                        )
                    ]
                )
        elif ai_assistant == "gemini":
            if not check_tool("gemini", "Install from: https://github.com/google-gemini/gemini-cli"):
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Gemini CLI is required for Gemini projects. Use ignore_agent_tools=True to skip this check."
                        )
                    ]
                )

    try:
        # Download and extract template
        download_and_extract_template(
            project_path, 
            ai_assistant, 
            use_current_dir, 
            verbose=False
        )

        # Initialize git repository if needed
        git_status = "skipped"
        if not no_git:
            if is_git_repo(project_path):
                git_status = "existing repo detected"
            elif git_available:
                if init_git_repo(project_path, quiet=True):
                    git_status = "initialized"
                else:
                    git_status = "init failed"
            else:
                git_status = "git not available"
        else:
            git_status = "--no-git flag"

        result_text = f"""Project initialization completed successfully!

Project: {project_name}
Path: {project_path}
AI Assistant: {ai_assistant} ({AI_CHOICES[ai_assistant]})
Git Repository: {git_status}

Next steps:
1. {'You are already in the project directory' if use_current_dir else f'cd {project_name}'}
2. Use AI agent commands with your chosen assistant
3. Update CONSTITUTION.md with your project's principles
"""

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=result_text
                )
            ]
        )

    except Exception as e:
        # Clean up project directory if created and not current directory
        if not use_current_dir and project_path.exists():
            import shutil
            shutil.rmtree(project_path)
        raise e


async def handle_check_requirements(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle requirements checking."""
    import httpx
    
    results = []
    
    # Check internet connectivity
    results.append("Checking requirements for Spec-Kit...\n")
    
    try:
        response = httpx.get("https://api.github.com", timeout=5, follow_redirects=True)
        results.append("✓ Internet connection available")
    except httpx.RequestError:
        results.append("✗ No internet connection - required for downloading templates")
    
    results.append("\nOptional tools:")
    git_ok = check_tool("git", "https://git-scm.com/downloads")
    results.append(f"{'✓' if git_ok else '✗'} git")
    
    results.append("\nOptional AI tools:")
    claude_ok = check_tool("claude", "Install from: https://docs.anthropic.com/en/docs/claude-code/setup")
    gemini_ok = check_tool("gemini", "Install from: https://github.com/google-gemini/gemini-cli")
    results.append(f"{'✓' if claude_ok else '✗'} claude")
    results.append(f"{'✓' if gemini_ok else '✗'} gemini")
    
    results.append("\n✓ Spec-Kit MCP server is ready to use!")
    if not git_ok:
        results.append("Consider installing git for repository management")
    if not (claude_ok or gemini_ok):
        results.append("Consider installing an AI assistant for the best experience")
        
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text="\n".join(results)
            )
        ]
    )


async def handle_list_scripts(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle script listing."""
    try:
        platform = get_platform()
        is_win = is_windows()
        available = get_available_scripts()
        compatibility = test_script_compatibility()
        
        results = []
        results.append(f"Platform: {platform.title()}")
        results.append(f"Windows mode: {'Yes' if is_win else 'No'}")
        results.append("\nAvailable Scripts:")
        
        for script_name, paths in available.items():
            results.append(f"\n• {script_name}")
            for path in paths:
                script_type = "Python" if path.suffix == ".py" else "Bash"
                results.append(f"  - {script_type}: {path}")
        
        results.append("\nScript Compatibility Test:")
        for script_name, works in compatibility.items():
            status = "✓" if works else "✗"
            results.append(f"{status} {script_name}")
        
        # Show summary
        working_count = sum(1 for works in compatibility.values() if works)
        total_count = len(compatibility)
        
        if working_count == total_count:
            results.append(f"\n✓ All {total_count} scripts are working on your platform!")
        else:
            results.append(f"\n⚠ {working_count}/{total_count} scripts are working on your platform")
            results.append("Some scripts may require a feature branch to be active")
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="\n".join(results)
                )
            ]
        )
        
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error checking scripts: {str(e)}"
                )
            ]
        )


async def handle_create_new_feature(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle new feature creation."""
    feature_description = arguments["feature_description"]
    repo_root = arguments.get("repo_root")
    
    try:
        if repo_root:
            repo_root_path = Path(repo_root)
        else:
            repo_root_path = None
            
        result = run_script(
            "create_new_feature",
            [feature_description, "--json"],
            repo_root_path,
            capture_output=True
        )
        
        if isinstance(result, dict):
            # JSON output
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )
                ]
            )
        else:
            # Text output
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=result.stdout if hasattr(result, 'stdout') else str(result)
                    )
                ]
            )
            
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error creating feature: {str(e)}"
                )
            ]
        )


async def handle_setup_plan(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle plan setup."""
    repo_root = arguments.get("repo_root")
    
    try:
        if repo_root:
            repo_root_path = Path(repo_root)
        else:
            repo_root_path = None
            
        result = run_script("setup_plan", [], repo_root_path, capture_output=True)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=result.stdout if hasattr(result, 'stdout') else str(result)
                )
            ]
        )
        
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error setting up plan: {str(e)}"
                )
            ]
        )


async def handle_check_task_prerequisites(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle task prerequisites checking."""
    repo_root = arguments.get("repo_root")
    
    try:
        if repo_root:
            repo_root_path = Path(repo_root)
        else:
            repo_root_path = None
            
        result = run_script("check_task_prerequisites", [], repo_root_path, capture_output=True)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=result.stdout if hasattr(result, 'stdout') else str(result)
                )
            ]
        )
        
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error checking task prerequisites: {str(e)}"
                )
            ]
        )


async def handle_update_agent_context(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle agent context updates."""
    repo_root = arguments.get("repo_root")
    
    try:
        if repo_root:
            repo_root_path = Path(repo_root)
        else:
            repo_root_path = None
            
        result = run_script("update_agent_context", [], repo_root_path, capture_output=True)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=result.stdout if hasattr(result, 'stdout') else str(result)
                )
            ]
        )
        
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error updating agent context: {str(e)}"
                )
            ]
        )


async def handle_get_feature_paths(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle feature path retrieval."""
    repo_root = arguments.get("repo_root")
    
    try:
        if repo_root:
            repo_root_path = Path(repo_root)
        else:
            repo_root_path = None
            
        result = run_script("get_feature_paths", ["--json"], repo_root_path, capture_output=True)
        
        if isinstance(result, dict):
            # JSON output
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )
                ]
            )
        else:
            # Text output
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=result.stdout if hasattr(result, 'stdout') else str(result)
                    )
                ]
            )
            
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error getting feature paths: {str(e)}"
                )
            ]
        )


async def handle_run_script(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle generic script execution."""
    script_name = arguments["script_name"]
    args = arguments.get("args", [])
    repo_root = arguments.get("repo_root")
    
    try:
        if repo_root:
            repo_root_path = Path(repo_root)
        else:
            repo_root_path = None
            
        result = run_script(script_name, args, repo_root_path, capture_output=True)
        
        if isinstance(result, dict):
            # JSON output
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )
                ]
            )
        else:
            # Text output
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=result.stdout if hasattr(result, 'stdout') else str(result)
                    )
                ]
            )
            
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error running script '{script_name}': {str(e)}"
                )
            ]
        )


async def handle_analyze_existing_project(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle existing project analysis."""
    project_path = arguments["project_path"]
    max_depth = arguments.get("max_depth", 3)
    
    try:
        project_path_obj = Path(project_path).resolve()
        
        if not project_path_obj.exists():
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Project path does not exist: {project_path}"
                    )
                ]
            )
        
        if not project_path_obj.is_dir():
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Project path is not a directory: {project_path}"
                    )
                ]
            )
        
        analysis = analyze_project_structure(project_path_obj, max_depth)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(analysis, indent=2)
                )
            ]
        )
        
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error analyzing project: {str(e)}"
                )
            ]
        )


async def handle_parse_existing_documentation(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle existing documentation parsing."""
    project_path = arguments["project_path"]
    file_patterns = arguments.get("file_patterns")
    
    try:
        project_path_obj = Path(project_path).resolve()
        
        if not project_path_obj.exists():
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Project path does not exist: {project_path}"
                    )
                ]
            )
        
        parsed_docs = parse_existing_documentation(
            project_path_obj, 
            file_patterns if file_patterns else None
        )
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(parsed_docs, indent=2)
                )
            ]
        )
        
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error parsing documentation: {str(e)}"
                )
            ]
        )


async def handle_extract_requirements_from_code(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle requirements extraction from code."""
    project_path = arguments["project_path"]
    file_patterns = arguments.get("file_patterns")
    
    try:
        project_path_obj = Path(project_path).resolve()
        
        if not project_path_obj.exists():
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Project path does not exist: {project_path}"
                    )
                ]
            )
        
        code_analysis = extract_requirements_from_code(
            project_path_obj,
            file_patterns if file_patterns else None
        )
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(code_analysis, indent=2)
                )
            ]
        )
        
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error extracting from code: {str(e)}"
                )
            ]
        )


async def handle_generate_standardized_spec(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle standardized specification generation."""
    project_analysis = arguments["project_analysis"]
    documentation_analysis = arguments["documentation_analysis"]
    code_analysis = arguments["code_analysis"]
    
    try:
        standardized_spec = generate_standardized_spec(
            project_analysis,
            documentation_analysis,
            code_analysis
        )
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(standardized_spec, indent=2)
                )
            ]
        )
        
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error generating standardized spec: {str(e)}"
                )
            ]
        )


async def handle_create_migration_plan(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle migration plan creation."""
    project_analysis = arguments["project_analysis"]
    standardized_spec = arguments["standardized_spec"]
    
    try:
        migration_plan = create_migration_plan(project_analysis, standardized_spec)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(migration_plan, indent=2)
                )
            ]
        )
        
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error creating migration plan: {str(e)}"
                )
            ]
        )


async def handle_onboard_existing_project(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle complete end-to-end project onboarding."""
    project_path = arguments["project_path"]
    max_depth = arguments.get("max_depth", 3)
    include_migration_plan = arguments.get("include_migration_plan", True)
    
    try:
        project_path_obj = Path(project_path).resolve()
        
        if not project_path_obj.exists():
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Project path does not exist: {project_path}"
                    )
                ]
            )
        
        if not project_path_obj.is_dir():
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Project path is not a directory: {project_path}"
                    )
                ]
            )
        
        # Step 1: Analyze project structure
        project_analysis = analyze_project_structure(project_path_obj, max_depth)
        
        # Step 2: Parse documentation
        documentation_analysis = parse_existing_documentation(project_path_obj)
        
        # Step 3: Extract from code
        code_analysis = extract_requirements_from_code(project_path_obj)
        
        # Step 4: Generate standardized spec
        standardized_spec = generate_standardized_spec(
            project_analysis,
            documentation_analysis,
            code_analysis
        )
        
        # Step 5: Create migration plan (if requested)
        migration_plan = None
        if include_migration_plan:
            migration_plan = create_migration_plan(project_analysis, standardized_spec)
        
        # Combine all results
        onboarding_result = {
            "onboarding_date": standardized_spec["analysis_date"],
            "project_analysis": project_analysis,
            "documentation_analysis": documentation_analysis,
            "code_analysis": code_analysis,
            "standardized_specification": standardized_spec,
            "migration_plan": migration_plan,
            "summary": {
                "project_name": project_analysis.get("project_name"),
                "estimated_size": project_analysis.get("estimated_size"),
                "languages": project_analysis.get("languages_detected", []),
                "documentation_files_found": len(documentation_analysis.get("files_parsed", [])),
                "requirements_found": len(documentation_analysis.get("requirements_found", [])),
                "features_found": len(documentation_analysis.get("features_found", [])),
                "code_files_analyzed": len(code_analysis.get("files_analyzed", [])),
                "gaps_identified": len(standardized_spec.get("gaps_identified", [])),
                "next_steps": [
                    "Review the generated specification and fill in gaps",
                    "Validate requirements with stakeholders",
                    "Follow the migration plan phases",
                    "Set up spec-kit environment for the project",
                    "Train team on spec-driven development workflow"
                ]
            }
        }
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(onboarding_result, indent=2)
                )
            ]
        )
        
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error during project onboarding: {str(e)}"
                )
            ]
        )


def main():
    """Main entry point for the MCP server."""
    import asyncio
    
    logger.info("Starting Spec-Kit MCP Server")
    
    async def run_server():
        async with stdio_server() as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )
    
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()