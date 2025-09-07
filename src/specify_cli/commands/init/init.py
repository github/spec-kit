"""Project management commands using services and enhanced UI."""

from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel

from specify_cli.models.project import ProjectInitOptions

# Import services
from specify_cli.services import (
    CommandLineGitService,
    HttpxDownloadService,
    JinjaTemplateService,
    SpecifyProjectManager,
    TomlConfigService,
)
from specify_cli.utils.ui import InteractiveUI, StepTracker


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
    ai_assistant: Optional[str] = typer.Option(
        None,
        "--ai",
        help="AI assistant to use: claude, gemini, or copilot (interactive if not specified)",
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

    # Determine project path (for display only; manager derives it from options)
    if here:
        display_project_name = Path.cwd().name
        project_path = Path.cwd()
    else:
        # project_name is asserted below
        display_project_name = project_name or ""
        project_path = (
            Path.cwd() / display_project_name if display_project_name else Path.cwd()
        )

    # Check if project already exists
    if not here and project_path.exists():
        console.print(f"[red]Error:[/red] Directory '{project_name}' already exists")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            "[bold cyan]Specify-X Project Setup[/bold cyan]\n"
            f"{'Initializing in current directory:' if here else 'Creating new project:'} [green]{project_path.name}[/green]"
            + (f"\n[dim]Path: {project_path}[/dim]" if here else ""),
            border_style="cyan",
        )
    )

    # Interactive AI assistant selection if not specified
    if ai_assistant is None:
        ui = InteractiveUI()
        ai_choices = {
            "claude": "Claude Code (Terminal-based AI assistant with / commands)",
            "gemini": "Gemini CLI (Terminal-based AI assistant)",
            "copilot": "GitHub Copilot (VS Code/IDE integration)",
        }

        try:
            # Create choices as dict format for proper key:value display
            choice_dict = ai_choices
            choice_keys = list(ai_choices.keys())

            selected_choice = ui.select(
                "Choose your AI assistant:",
                choices=choice_dict,
                default=choice_keys[0],  # First choice key (claude)
            )

            # The selected_choice should be the key directly
            ai_assistant = selected_choice
        except KeyboardInterrupt:
            console.print("[yellow]Setup cancelled[/yellow]")
            raise typer.Exit(0) from None

    # Validate AI assistant choice
    valid_assistants = ["claude", "gemini", "copilot"]
    if ai_assistant not in valid_assistants:
        console.print(
            f"[red]Error:[/red] Invalid AI assistant '{ai_assistant}'. Choose from: {', '.join(valid_assistants)}"
        )
        raise typer.Exit(1)

    # Get project manager
    project_manager = get_project_manager()

    # Use StepTracker for enhanced progress display
    with StepTracker.create_default("Specify-X Project Setup") as tracker:
        try:
            tracker.add_step("validate", "Validate project settings")
            tracker.start_step("validate")

            # Build options for project initialization
            options = ProjectInitOptions(
                project_name=project_name if not here else None,
                ai_assistant=ai_assistant,
                use_current_dir=here,
                skip_git=False,
            )
            tracker.complete_step("validate", f"AI: {ai_assistant}")

            tracker.add_step("initialize", "Initialize project structure")
            tracker.start_step("initialize")

            result = project_manager.initialize_project(options)

            if result:
                tracker.complete_step("initialize", "Project created successfully")

                tracker.add_step("finalize", "Finalize setup")
                tracker.start_step("finalize")
                tracker.complete_step("finalize", "Ready to use!")
            else:
                tracker.error_step("initialize", "Project initialization failed")
                raise typer.Exit(1)

        except Exception as e:
            if "tracker" in locals():
                tracker.error_step("initialize", f"Error: {e}")
            console.print(f"[red]Error during project initialization:[/red] {e}")
            raise typer.Exit(1) from e

    # Show next steps (outside the context manager so tracker is displayed)
    if result:
        console.print("\n[bold green]✓ Project initialized successfully![/bold green]")

        # Show next steps with enhanced formatting
        steps_lines = []
        if not here:
            steps_lines.append(f"1. [bold green]cd {project_name}[/bold green]")
            step_num = 2
        else:
            steps_lines.append("1. You're already in the project directory!")
            step_num = 2

        # Add AI-specific guidance
        if ai_assistant == "claude":
            steps_lines.append(
                f"{step_num}. Open in VS Code and use / commands with Claude Code"
            )
            steps_lines.append("   • Type / in any file to see available commands")
            steps_lines.append("   • Use /specify to create specifications")
        elif ai_assistant == "gemini":
            steps_lines.append(f"{step_num}. Use Gemini CLI for development")
            steps_lines.append("   • Run gemini /specify for specifications")
        elif ai_assistant == "copilot":
            steps_lines.append(f"{step_num}. Use GitHub Copilot in your IDE")
            steps_lines.append("   • Use /specify, /plan, /tasks commands")

        steps_lines.append(
            f"{step_num + 1}. Update [bold magenta]CONSTITUTION.md[/bold magenta] with your project's principles"
        )

        steps_panel = Panel(
            "\n".join(steps_lines),
            title="Next steps",
            border_style="cyan",
            padding=(1, 2),
        )
        console.print(steps_panel)
