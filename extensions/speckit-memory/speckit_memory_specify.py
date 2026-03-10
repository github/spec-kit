"""
speckit.memory.specify - Enhanced specification with memory integration.

Automatically reads accumulated patterns and lessons before creating specs.
"""

import json
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Try to import memory components
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

    from specify_cli.memory.orchestrator import MemoryOrchestrator
    from specify_cli.memory.headers_reader import HeadersFirstReader
    from specify_cli.memory.smart_search import SmartSearchScope
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False


def get_memory_context_before_spec(project_id: str) -> dict:
    """Get relevant memory context before creating specification.

    Args:
        project_id: Project identifier

    Returns:
        Dict with memory context (lessons, patterns, architecture)
    """
    if not MEMORY_AVAILABLE:
        return {
            "available": False,
            "reason": "Memory components not available"
        }

    try:
        # Headers-first reading
        reader = HeadersFirstReader()
        headers = reader.read_headers(
            project_id=project_id,
            file_types=["lessons", "patterns", "architecture"],
            limit=5
        )

        # Extract relevant items
        context = {
            "available": True,
            "project_id": project_id,
            "recent_lessons": [],
            "active_patterns": [],
            "architecture_notes": []
        }

        for file_type in ["lessons", "patterns", "architecture"]:
            if file_type in headers:
                for item in headers[file_type][:5]:
                    title = item.get("title", "")
                    one_liner = item.get("one_liner", "")
                    context[f"{file_type[:-1]}_notes"].append({
                        "title": title,
                        "summary": one_liner
                    })

        return context

    except Exception as e:
        return {
            "available": False,
            "reason": f"Error reading memory: {e}"
        }


def format_memory_context_for_spec(context: dict) -> str:
    """Format memory context for inclusion in spec.

    Args:
        context: Memory context dict

    Returns:
        Formatted markdown string
    """
    if not context.get("available"):
        return ""

    output = "\n---\n## Memory Context\n\n"

    # Recent lessons
    if context.get("recent_lessons"):
        output += "### Relevant Lessons (from past work)\n\n"
        for lesson in context["recent_lessons"][:3]:
            title = lesson.get("title", "")
            summary = lesson.get("summary", "")
            output += f"- **{title}**: {summary}\n"
        output += "\n"

    # Active patterns
    if context.get("active_patterns"):
        output += "### Useful Patterns (proven solutions)\n\n"
        for pattern in context["active_patterns"][:3]:
            title = pattern.get("title", "")
            summary = pattern.get("summary", "")
            output += f"- **{title}**: {summary}\n"
        output += "\n"

    return output


def save_spec_with_memory(spec_content: str, memory_context: dict, project_id: str) -> bool:
    """Save specification with integrated memory context.

    Args:
        spec_content: Original spec content
        memory_context: Memory context to integrate
        project_id: Project identifier

    Returns:
        True if saved successfully
    """
    try:
        # Add memory context to spec
        enhanced_spec = spec_content

        # Insert memory context before Functional Requirements
        if "## Functional Requirements" in enhanced_spec:
            memory_section = format_memory_context_for_spec(memory_context)
            if memory_section:
                enhanced_spec = enhanced_spec.replace(
                    "## Functional Requirements",
                    memory_section + "## Functional Requirements"
                )

        # Save to spec file (in specs directory)
        specs_dir = Path.cwd() / "specs"
        if not specs_dir.exists():
            specs_dir = Path.cwd().parent / "specs"

        # Find the feature spec file
        feature_specs = list(specs_dir.glob("*-*/spec.md"))
        if feature_specs:
            spec_file = feature_specs[0]
            spec_file.write_text(enhanced_spec, encoding="utf-8")

            if RICH_AVAILABLE:
                console = Console()
                console.print(f"[green]✓[/green] Enhanced spec with memory context: {spec_file.name}")

            return True

    except Exception as e:
        if RICH_AVAILABLE:
            console = Console()
            console.print(f"[red]Error saving enhanced spec:[/red] {e}")
        return False


def record_spec_creation_to_memory(
    project_id: str,
    spec_title: str,
    key_decisions: list
) -> bool:
    """Record spec creation in project memory.

    Args:
        project_id: Project identifier
        spec_title: Specification title
        key_decisions: List of key decisions made

    Returns:
        True if recorded successfully
    """
    if not MEMORY_AVAILABLE:
        return False

    try:
        from specify_cli.memory.agent import MemoryAwareAgent

        agent = MemoryAwareAgent(project_id=project_id)

        # Record as architecture decision (high importance)
        agent.after_task(
            problem=f"Specification created: {spec_title}",
            solution=f"Defined requirements with {len(key_decisions)} key decisions",
            lessons="Specification follows SDD best practices",
            importance=0.8,
            tags=["specification", "requirements", "planning"]
        )

        return True

    except Exception as e:
        if RICH_AVAILABLE:
            console = Console()
            console.print(f"[yellow]Warning:[/yellow] Could not record to memory: {e}")
        return False


# Main command entry point
def speckit_memory_specify(
    project_id: Optional[str] = None,
    spec_file: Optional[Path] = None,
    enhance_only: bool = False
) -> int:
    """Enhanced spec creation with memory integration.

    Usage:
        python -m speckit_memory.specify --project-id my-feature
        python -m speckit_memory.specify --spec-file specs/001-feature/spec.md

    Args:
        project_id: Project identifier
        spec_file: Path to spec file
        enhance_only: Only enhance existing spec without creating new one

    Returns:
        Exit code (0 = success)
    """
    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel.fit(
            "[bold cyan]speckit.memory.specify[/bold cyan]",
            "Enhanced specification with memory integration"
        ))

    # Determine project ID
    if not project_id:
        if spec_file:
            # Extract from spec file path
            parts = spec_file.parent.name.split("-")
            if parts:
                project_id = parts[-1]  # Last part is usually feature name
        else:
            # Use current directory
            project_id = Path.cwd().name

    # Get memory context
    memory_context = get_memory_context_before_spec(project_id)

    if memory_context.get("available"):
        if RICH_AVAILABLE:
            console.print(f"[green]✓[/green] Memory context loaded: {project_id}")
            if memory_context.get("recent_lessons"):
                console.print(f"  - {len(memory_context['recent_lessons'])} relevant lessons")
            if memory_context.get("active_patterns"):
                console.print(f"  - {len(memory_context['active_patterns'])} useful patterns")
    else:
        if RICH_AVAILABLE:
            console.print(f"[yellow]Memory not available:[/yellow] {memory_context.get('reason', 'Unknown')}")

    if not enhance_only and spec_file:
        # Load and enhance spec
        try:
            spec_content = spec_file.read_text(encoding="utf-8")

            if memory_context.get("available"):
                enhanced = save_spec_with_memory(spec_content, memory_context, project_id)
                if enhanced:
                    if RICH_AVAILABLE:
                        console.print("[green]✓[/green] Spec enhanced with memory context")
            else:
                if RICH_AVAILABLE:
                    console.print("[dim]Spec unchanged (memory unavailable)[/dim]")

        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Error processing spec:[/red] {e}")
            return 1

    return 0


if __name__ == "__main__":
    import sys

    # Simple CLI parsing
    project_id = None
    spec_file = None
    enhance_only = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--project-id" and i + 1 < len(sys.argv):
            project_id = sys.argv[i + 1]
            i += 2
        elif arg == "--spec-file":
            spec_file = Path(sys.argv[i + 1])
            i += 2
        elif arg == "--enhance-only":
            enhance_only = True
            i += 1
        else:
            i += 1

    sys.exit(speckit_memory_specify(project_id, spec_file, enhance_only))
