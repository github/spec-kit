"""
speckit.memory.clarify - Enhanced clarification with cross-project context.

Uses accumulated knowledge across projects for better clarifications.
"""

from pathlib import Path
from typing import Optional, Dict, List

try:
    from rich.console import Console
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def get_cross_project_context(query: str) -> Dict:
    """Get relevant context from all projects.

    Args:
        query: Search query

    Returns:
        Dict with cross-project context
    """
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        from specify_cli.memory.orchestrator import MemoryOrchestrator

        orchestrator = MemoryOrchestrator(project_id="_global")

        # Search across all projects
        results = orchestrator.search(
            query=query,
            scope="global"
        )

        return {
            "available": True,
            "results": results[:5],
            "count": len(results)
        }

    except Exception as e:
        return {
            "available": False,
            "results": [],
            "count": 0,
            "error": str(e)
        }


def speckit_memory_clarify(
    query: str,
    project_id: Optional[str] = None
) -> int:
    """Enhanced clarification with cross-project context.

    Usage:
        python -m speckit_memory_clarify --query "authentication pattern"

    Args:
        query: Clarification query
        project_id: Project identifier

    Returns:
        Exit code (0 = success)
    """
    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel.fit(
            "[bold cyan]speckit.memory.clarify[/bold cyan]",
            "Enhanced clarification with cross-project context"
        ))

    # Get cross-project context
    context = get_cross_project_context(query)

    if context["available"] and context["results"]:
        if RICH_AVAILABLE:
            console.print(f"[green]✓[/green] Found {context['count']} relevant items from global memory")

            for i, result in enumerate(context["results"][:3], 1):
                title = result.get("title", "")
                source = result.get("source", "unknown")
                if RICH_AVAILABLE:
                    console.print(f"  {i}. [{source}] {title}")
    else:
        if RICH_AVAILABLE:
            if context.get("error"):
                console.print(f"[yellow]Cross-project search unavailable:[/yellow] {context['error']}")
            else:
                console.print("[dim]No cross-project context found[/dim]")

    return 0


if __name__ == "__main__":
    import sys

    query = None
    project_id = None

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--query" and i + 1 < len(sys.argv):
            query = sys.argv[i + 1]
            i += 2
        elif arg == "--project-id" and i + 1 < len(sys.argv):
            project_id = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    if not query:
        # Use first positional arg as query
        if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
            query = sys.argv[1]

    if query:
        sys.exit(speckit_memory_clarify(query, project_id))
    else:
        if RICH_AVAILABLE:
            console = Console()
            console.print("[red]Error:[/red] --query is required")
        sys.exit(1)
