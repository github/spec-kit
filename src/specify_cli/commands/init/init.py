"""Project management commands using services."""

from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel

# Import services
from specify_cli.services import (
    CommandLineGitService,
    HttpxDownloadService,
    JinjaTemplateService,
    SpecifyProjectManager,
    TomlConfigService,
)


# Initialize services
def get_project_manager():
    """Factory function to create ProjectManager with all dependencies."""
    template_service = JinjaTemplateService()
    config_service = TomlConfigService()
    git_service = CommandLineGitService()
    download_service = HttpxDownloadService()

    return SpecifyProjectManager(
        template_service=template_service,
        config_service=config_service,
        git_service=git_service,
        download_service=download_service,
    )


def init_command(
    project_name: Optional[str] = typer.Argument(
        None, help="Name for your new project directory (optional if using --here)"
    ),
    ai_assistant: str = typer.Option(
        "claude", "--ai", help="AI assistant to use: claude, gemini, or copilot"
    ),
    # no_git: bool = typer.Option(
    #     False, "--no-git", help="Skip git repository initialization"
    # ),
    here: bool = typer.Option(
        False,
        "--here",
        help="Initialize project in the current directory instead of creating a new one",
    ),
):
    """
    Initialize a new Specify-X project using the modular service architecture.

    This command uses the ProjectManager service to orchestrate:
    - Project structure creation
    - Template rendering with Jinja2
    - Git repository initialization
    - Configuration management with TOML
    """
    from specify_cli.core.app import console, show_banner

    # Show banner
    show_banner()

    # Validate arguments
    if here and project_name:
        console.print(
            "[red]Error:[/red] Cannot specify both project name and --here flag"
        )
        raise typer.Exit(1)

    if not here and not project_name:
        console.print(
            "[red]Error:[/red] Must specify either a project name or use --here flag"
        )
        raise typer.Exit(1)

    # Determine project path
    if here:
        project_name = Path.cwd().name
        project_path = Path.cwd()
    else:
        project_path = Path(project_name).resolve()

    # Check if project already exists
    if not here and project_path.exists():
        console.print(f"[red]Error:[/red] Directory '{project_name}' already exists")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            "[bold cyan]Specify-X Project Setup (Modular Architecture)[/bold cyan]\n"
            f"{'Initializing in current directory:' if here else 'Creating new project:'} [green]{project_path.name}[/green]"
            + (f"\n[dim]Path: {project_path}[/dim]" if here else ""),
            border_style="cyan",
        )
    )

    # Get project manager
    project_manager = get_project_manager()

    try:
        # Use ProjectManager service to initialize project
        console.print("[cyan]Initializing project using service architecture...[/cyan]")

        result = project_manager.initialize_project(
            project_name=project_name,
            project_path=project_path,
            ai_assistant=ai_assistant,
        )

        if result:
            console.print(
                "[bold green]✓ Project initialized successfully![/bold green]"
            )

            # Show next steps
            steps_lines = []
            if not here:
                steps_lines.append(f"1. [bold green]cd {project_name}[/bold green]")
                step_num = 2
            else:
                steps_lines.append("1. You're already in the project directory!")
                step_num = 2

            steps_lines.append(
                f"{step_num}. Update [bold magenta]CONSTITUTION.md[/bold magenta] with your project's principles"
            )
            steps_lines.append(
                f"{step_num + 1}. Use your AI assistant to start developing!"
            )

            steps_panel = Panel(
                "\n".join(steps_lines),
                title="Next steps",
                border_style="cyan",
                padding=(1, 2),
            )
            console.print()
            console.print(steps_panel)
        else:
            console.print("[red]✗ Project initialization failed[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error during project initialization:[/red] {e}")
        raise typer.Exit(1) from e
