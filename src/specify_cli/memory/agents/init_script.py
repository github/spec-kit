"""
Agent Init Script - CLI command for creating agents.

Provides `/agent init` command for interactive agent creation.
"""

import sys
from pathlib import Path
from typing import Optional

try:
    import typer
    from rich import print as rprint
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False
    print("Warning: typer/rich not available, using basic CLI")

from .skill_workflow import SkillCreationWorkflow
from .agent_templates import get_template, list_templates, get_all_templates
from ..logging import get_logger


app = typer.Typer(help="Agent Creation System - Create and manage AI agents")


def init_agent(
    agent_name: Optional[str] = typer.Argument(None, help="Name for the agent"),
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Use predefined template"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", "-i/-n", help="Interactive mode"),
    search: bool = typer.Option(True, "--search/--no-search", "-s/-ns", help="Search SkillsMP for existing agents")
) -> None:
    """Initialize a new AI agent with 4-level memory system.

    Usage:
        agent init my-agent                    # Interactive with search
        agent init my-agent -t frontend       # Use template, skip search
        agent init my-agent --no-search        # Skip SkillsMP search
    """
    logger = get_logger()

    if not TYPER_AVAILABLE:
        print("Error: typer and rich packages required for CLI")
        print("Install with: pip install typer rich")
        sys.exit(1)

    rprint("\n[bold cyan]🤖 Agent Creation System[/bold cyan]")
    rprint("[dim]4-Level Memory: File + Vector + Context + Identity[/dim]\n")

    # Get agent name if not provided
    if not agent_name:
        agent_name = Prompt.ask("[yellow]Agent name[/yellow]", default="my-agent")
        if not agent_name:
            rprint("[red]Error: Agent name required[/red]")
            sys.exit(1)

    # Sanitize agent name
    agent_name = agent_name.strip().lower().replace(" ", "-")

    # Step 1: Search for existing agents (if enabled)
    if interactive and search:
        rprint(f"\n[bold]Step 1: Searching for existing agents...[/bold]")

        workflow = SkillCreationWorkflow()
        search_query = Prompt.ask(
            "[yellow]Search query[/yellow]",
            default=agent_name.replace("-", " ")
        )

        search_results = workflow.search_agents(search_query, limit=5)

        if search_results["found"]:
            rprint(f"\n{workflow.present_options(search_results)}")

            use_existing = Confirm.ask(
                "[yellow]Use existing agent instead of creating new?[/yellow]",
                default=False
            )

            if use_existing:
                rprint("[green]✓ Selected existing agent[/green]")
                rprint("\n[dim]Tip: Clone/configure the existing agent for your needs[/dim]")
                return

    # Step 2: Choose template or custom
    rprint(f"\n[bold]Step 2: Choose agent configuration[/bold]")

    use_template = None
    if interactive and not template:
        show_templates = Confirm.ask(
            "[yellow]Show available templates?[/yellow]",
            default=True
        )

        if show_templates:
            _show_available_templates()

        use_template = Confirm.ask(
            "[yellow]Use predefined template?[/yellow]",
            default=True
        )

    if template or use_template:
        # Get template name
        if not template:
            template = Prompt.ask(
                "[yellow]Template name[/yellow]",
                choices=list_templates(),
                default="fullstack-dev"
            )

        try:
            template_data = get_template(template)
            rprint(f"[green]✓ Using template: {template}[/green]")
            requirements = template_data.copy()

            # Allow customization
            if interactive:
                customize = Confirm.ask(
                    "[yellow]Customize template?[/yellow]",
                    default=False
                )

                if customize:
                    _customize_requirements(requirements)

        except KeyError as e:
            rprint(f"[red]Error: {e}[/red]")
            sys.exit(1)
    else:
        # Custom agent
        rprint("[dim]Creating custom agent...[/dim]\n")
        requirements = _collect_custom_requirements(agent_name, interactive)

    # Step 3: Create agent
    rprint(f"\n[bold]Step 3: Creating agent '{agent_name}'...[/bold]")

    workflow = SkillCreationWorkflow()
    created_files = workflow.create_agent_from_requirements(
        agent_name=agent_name,
        requirements=requirements
    )

    # Show results
    rprint("\n[bold green]✓ Agent created successfully![/bold green]\n")
    _show_created_files(created_files, agent_name)

    # Next steps
    _show_next_steps(agent_name)


def _show_available_templates() -> None:
    """Display available agent templates."""
    templates = get_all_templates()

    table = Table(title="\n📋 Available Agent Templates")
    table.add_column("Template", style="cyan")
    table.add_column("Role", style="yellow")
    table.add_column("Skills", style="dim")

    for name, data in templates.items():
        skills_count = len(data.get("skills", []))
        table.add_row(
            name,
            data.get("role", "Unknown"),
            f"{skills_count} skills"
        )

    rprint(table)


def _customize_requirements(requirements: dict) -> None:
    """Interactive customization of requirements."""
    rprint("\n[dim]Customize agent (press Enter to keep default)[/dim]\n")

    # Role
    default_role = requirements.get("role", "")
    new_role = Prompt.ask("[yellow]Role[/yellow]", default=default_role)
    if new_role != default_role:
        requirements["role"] = new_role

    # Skills
    customize_skills = Confirm.ask(
        "[yellow]Customize skills?[/yellow]",
        default=False
    )

    if customize_skills:
        rprint("\n[dim]Current skills:[/dim]")
        for skill in requirements.get("skills", [])[:5]:
            rprint(f"  • {skill}")

        add_skills = Confirm.ask(
            "[yellow]Add more skills?[/yellow]",
            default=False
        )

        if add_skills:
            while True:
                new_skill = Prompt.ask("[yellow]New skill (or empty to finish)[/yellow]", default="")
                if not new_skill:
                    break
                requirements.setdefault("skills", []).append(new_skill)


def _collect_custom_requirements(agent_name: str, interactive: bool) -> dict:
    """Collect custom agent requirements interactively."""
    requirements = {}

    # Role
    rprint("\n[bold]Agent Configuration[/bold]\n")
    role = Prompt.ask(
        "[yellow]Primary role[/yellow]",
        default=f"AI Agent for {agent_name}"
    )
    requirements["role"] = role

    # Personality
    personality = Prompt.ask(
        "[yellow]Personality traits[/yellow]",
        default="Professional and constructive"
    )
    requirements["personality"] = personality

    # Skills
    rprint("\n[dim]Enter skills (one per line, empty line to finish):[/dim]")
    skills = []
    while True:
        skill = Prompt.ask("[yellow]Skill[/yellow]", default="")
        if not skill:
            break
        skills.append(skill)

    requirements["skills"] = skills

    # Team
    add_team = Confirm.ask(
        "[yellow]Add team members?[/yellow]",
        default=False
    )

    if add_team:
        team = []
        while True:
            member = Prompt.ask(
                "[yellow]Team member (or empty to finish)[/yellow]",
                default=""
            )
            if not member:
                break
            team.append(member)
        requirements["team"] = team

    return requirements


def _show_created_files(created_files: dict, agent_name: str) -> None:
    """Display created files summary."""
    from rich.tree import Tree
    from rich.filesize import dec

    tree = Tree(f"📁 {agent_name}/")
    tree.add("📄 AGENTS.md - Role and skills")
    tree.add("📄 SOUL.md - Personality and principles")
    tree.add("📄 USER.md - User profile")
    tree.add("📄 MEMORY.md - Knowledge summary")

    memory_dir = tree.add("📁 memory/")
    memory_dir.add("📄 lessons.md - Accumulated rules")
    memory_dir.add("📄 patterns.md - Error patterns")
    memory_dir.add("📄 projects-log.md - Task history")
    memory_dir.add("📄 architecture.md - Design decisions")
    memory_dir.add("📄 handoff.md - Session context")

    rprint(tree)


def _show_next_steps(agent_name: str) -> None:
    """Display next steps for the user."""
    rprint("\n[bold]Next Steps:[/bold]\n")
    rprint("1. [cyan]Review agent files[/cyan]")
    rprint(f"   Edit: ~/.claude/agents/{agent_name}/AGENTS.md\n")

    rprint("2. [cyan]Test agent memory[/cyan]")
    rprint("   Before task: Read headers from memory/")
    rprint("   When stuck: Search vector memory")
    rprint("   After task: Auto-document to memory/\n")

    rprint("3. [cyan]Enable auto-improvement[/cyan]")
    rprint("   Errors automatically recorded to patterns.md")
    rprint("   After 3 repeats → promoted to lessons.md\n")

    rprint("4. [cyan]Weekly handoff[/cyan]")
    rprint("   Run: agent handoff")
    rprint("   Creates: memory/handoff.md with context\n")

    rprint("[dim]For more info, see: ~/.claude/agents/{agent_name}/MEMORY.md[/dim]\n")


def list_agents_command() -> None:
    """List all created agents."""
    agents_dir = Path.home() / ".claude" / "agents"

    if not agents_dir.exists():
        rprint("[yellow]No agents found[/yellow]")
        rprint(f"[dim]Agents directory: {agents_dir}[/dim]")
        return

    agents = [d for d in agents_dir.iterdir() if d.is_dir()]

    if not agents:
        rprint("[yellow]No agents found[/yellow]")
        return

    table = Table(title="\n🤖 Your Agents")
    table.add_column("Agent", style="cyan")
    table.add_column("Files", style="dim")
    table.add_column("Memory Files", style="dim")

    for agent_dir in sorted(agents):
        agent_name = agent_dir.name

        # Count files
        agent_files = list(agent_dir.glob("*.md"))
        memory_dir = agent_dir / "memory"
        memory_files = list(memory_dir.glob("*.md")) if memory_dir.exists() else []

        table.add_row(
            agent_name,
            str(len(agent_files)),
            str(len(memory_files))
        )

    rprint(table)


# Main entry point
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_agents_command()
    else:
        # Parse args manually for simpler interface
        import shlex

        args = sys.argv[1:]
        agent_name = None
        template = None
        interactive = True
        search = True

        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith("-t"):
                template = args[i + 1] if i + 1 < len(args) else "fullstack-dev"
                i += 2
            elif arg == "--no-interactive" or arg == "-n":
                interactive = False
                i += 1
            elif arg == "--no-search" or arg == "-ns":
                search = False
                i += 1
            elif not arg.startswith("-"):
                agent_name = arg
                i += 1
            else:
                i += 1

        init_agent(
            agent_name=agent_name,
            template=template,
            interactive=interactive,
            search=search
        )
