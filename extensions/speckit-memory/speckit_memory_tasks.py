"""
speckit.memory.tasks - Enhanced task generation with pattern memory.

Uses accumulated patterns for better task decomposition.
"""

from pathlib import Path
from typing import Optional, Dict, List

try:
    from rich.console import Console
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def get_pattern_memory(project_id: str) -> List[Dict]:
    """Get accumulated patterns for task generation.

    Args:
        project_id: Project identifier

    Returns:
        List of pattern dicts
    """
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        from specify_cli.memory.headers_reader import HeadersFirstReader

        reader = HeadersFirstReader()

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

        return patterns

    except Exception as e:
        if RICH_AVAILABLE:
            console = Console()
            console.print(f"[yellow]Warning:[/yellow] Could not read patterns: {e}")
        return []


def speckit_memory_tasks(
    project_id: Optional[str] = None,
    tasks_file: Optional[Path] = None
) -> int:
    """Enhanced task generation with pattern memory.

    Usage:
        python -m speckit_memory_tasks --project-id my-feature

    Args:
        project_id: Project identifier
        tasks_file: Path to tasks file

    Returns:
        Exit code (0 = success)
    """
    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel.fit(
            "[bold cyan]speckit.memory.tasks[/bold cyan]",
            "Enhanced task generation with pattern memory"
        ))

    # Get patterns
    if project_id:
        patterns = get_pattern_memory(project_id)

        if patterns:
            if RICH_AVAILABLE:
                console.print(f"[green]✓[/green] Loaded {len(patterns)} patterns for: {project_id}")
                for pattern in patterns[:3]:
                    console.print(f"  - {pattern['title']}")
        else:
            if RICH_AVAILABLE:
                console.print("[dim]No patterns found (new project)[/dim]")

    return 0


if __name__ == "__main__":
    import sys

    project_id = None
    tasks_file = None

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--project-id" and i + 1 < len(sys.argv):
            project_id = sys.argv[i + 1]
            i += 2
        elif arg == "--tasks-file":
            tasks_file = Path(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    sys.exit(speckit_memory_tasks(project_id, tasks_file))
