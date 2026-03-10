"""
speckit.memory.plan - Enhanced planning with memory integration.

Uses accumulated architecture decisions and patterns for better planning.
"""

import json
from pathlib import Path
from typing import Optional, Dict, List

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

    from specify_cli.memory.headers_reader import HeadersFirstReader
    from specify_cli.memory.orchestrator import MemoryOrchestrator
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False


def get_architecture_context(project_id: str) -> Dict[str, List]:
    """Get architecture context for planning.

    Args:
        project_id: Project identifier

    Returns:
        Dict with architecture decisions
    """
    if not MEMORY_AVAILABLE:
        return {"decisions": [], "patterns": []}

    try:
        reader = HeadersFirstReader()

        # Read architecture decisions
        arch_headers = reader.read_headers(
            project_id=project_id,
            file_types=["architecture"],
            limit=10
        )

        decisions = []
        if "architecture" in arch_headers:
            for item in arch_headers["architecture"]:
                decisions.append({
                    "title": item.get("title", ""),
                    "summary": item.get("one_liner", "")
                })

        # Read patterns
        pattern_headers = reader.read_headers(
            project_id=project_id,
            file_types=["patterns"],
            limit=10
        )

        patterns = []
        if "patterns" in pattern_headers:
            for item in pattern_headers["patterns"]:
                patterns.append({
                    "title": item.get("title", ""),
                    "summary": item.get("one_liner", "")
                })

        return {
            "decisions": decisions,
            "patterns": patterns
        }

    except Exception as e:
        if RICH_AVAILABLE:
            console = Console()
            console.print(f"[yellow]Warning:[/yellow] Could not read architecture context: {e}")
        return {"decisions": [], "patterns": []}


def format_plan_memory_section(context: Dict[str, List]) -> str:
    """Format memory context for plan.

    Args:
        context: Architecture context

    Returns:
        Formatted markdown section
    """
    output = "\n## Memory Context\n\n"

    if context["decisions"]:
        output += "### Relevant Architecture Decisions\n\n"
        for decision in context["decisions"][:5]:
            title = decision.get("title", "")
            summary = decision.get("summary", "")
            output += f"- **{title}**: {summary}\n"
        output += "\n"

    if context["patterns"]:
        output += "### Proven Patterns\n\n"
        for pattern in context["patterns"][:5]:
            title = pattern.get("title", "")
            summary = pattern.get("summary", "")
            output += f"- **{title}**: {summary}\n"
        output += "\n"

    return output


def speckit_memory_plan(
    project_id: Optional[str] = None,
    plan_file: Optional[Path] = None
) -> int:
    """Enhanced planning with memory integration.

    Usage:
        python -m speckit_memory_plan --project-id my-feature
        python -m speckit_memory_plan --plan-file plan.md

    Args:
        project_id: Project identifier
        plan_file: Path to plan file

    Returns:
        Exit code (0 = success)
    """
    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel.fit(
            "[bold cyan]speckit.memory.plan[/bold cyan]",
            "Enhanced planning with memory integration"
        ))

    # Get architecture context
    if project_id:
        context = get_architecture_context(project_id)

        if context["decisions"] or context["patterns"]:
            if RICH_AVAILABLE:
                console.print(f"[green]✓[/green] Memory context loaded for: {project_id}")
                console.print(f"  - {len(context['decisions'])} architecture decisions")
                console.print(f"  - {len(context['patterns'])} proven patterns")

            # Format for inclusion in plan
            memory_section = format_plan_memory_section(context)

            if RICH_AVAILABLE:
                console.print("\n[dim]Memory context section ready for plan.md[/dim]")

    return 0


if __name__ == "__main__":
    import sys

    project_id = None
    plan_file = None

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--project-id" and i + 1 < len(sys.argv):
            project_id = sys.argv[i + 1]
            i += 2
        elif arg == "--plan-file":
            plan_file = Path(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    sys.exit(speckit_memory_plan(project_id, plan_file))
