"""Core CLI application setup and configuration.

This module contains the Typer app setup, Rich console configuration,
and main entry point for the Specify-X CLI tool.
"""

import sys
from importlib.metadata import version
from typing import Dict

import typer
from rich.align import Align
from rich.console import Console
from rich.text import Text
from typer.core import TyperGroup

# AI assistant choices for validation
AI_CHOICES: Dict[str, str] = {
    "copilot": "GitHub Copilot",
    "claude": "Claude Code",
    "gemini": "Gemini CLI",
}

# ASCII Art Banner
BANNER = """
███████╗██████╗ ███████╗ ██████╗██╗███████╗██╗   ██╗    ██╗  ██╗
██╔════╝██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝    ╚██╗██╔╝
███████╗██████╔╝█████╗  ██║     ██║█████╗   ╚████╔╝█████╗╚███╔╝ 
╚════██║██╔═══╝ ██╔══╝  ██║     ██║██╔══╝    ╚██╔╝ ╚════╝██╔██╗ 
███████║██║     ███████╗╚██████╗██║██║        ██║       ██╔╝ ██╗
╚══════╝╚═╝     ╚══════╝ ╚═════╝╚═╝╚═╝        ╚═╝       ╚═╝  ╚═╝
"""

TAGLINE = "Spec-Driven Development Toolkit"

# Rich console instance
console = Console()


class BannerGroup(TyperGroup):
    """Custom group that shows banner before help."""

    def format_help(self, ctx, formatter):
        # Show banner before help
        show_banner()
        super().format_help(ctx, formatter)


def show_banner():
    """Display the ASCII art banner with enhanced colorization for front and back characters."""
    banner_lines = BANNER.strip().split("\n")

    # Professional color palette: green to teal gradient for front characters
    front_colors = [
        "bright_green",
        "green",
        "bright_cyan",
        "cyan",
        "bright_blue",
        "blue",
    ]
    # Subtle background color for decorative elements
    back_color = "dim white"

    num_colors = len(front_colors)

    # Print each line with different colors for front and back characters
    for i, line in enumerate(banner_lines):
        # Get front color for this line using gradient
        front_color_index = int((i / len(banner_lines)) * num_colors) % num_colors
        front_color = front_colors[front_color_index]

        # Split the line into front characters (█) and back characters (box drawing)
        # Only the solid block characters █ are front characters
        # All other characters (╗╔╝║═╚ and spaces) are back characters
        colored_line = ""
        for char in line:
            if char == "█":
                # Only the solid block character is the front character
                colored_line += f"[bold {front_color}]{char}[/]"
            else:
                # All other characters are back characters
                colored_line += f"[{back_color}]{char}[/]"

        console.print(Align.center(colored_line))

    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()


# Main Typer app instance
app = typer.Typer(
    name="specify",
    help="Setup tool for Specify-X spec-driven development projects",
    add_completion=True,
    invoke_without_command=True,
    cls=BannerGroup,
)


@app.callback()
def callback(
    ctx: typer.Context,
    show_version: bool = typer.Option(
        False, "--version", "-V", help="Show version and exit"
    ),
):
    """Show banner when no subcommand is provided."""
    # Handle version flag
    if show_version:
        try:
            pkg_version = version("specify-cli")
        except Exception:
            pkg_version = "unknown"
        console.print(f"Specify-X CLI [bold cyan]v{pkg_version}[/bold cyan]")
        raise typer.Exit()

    # Show banner only when no subcommand and no help flag
    # (help is handled by BannerGroup)
    if (
        ctx.invoked_subcommand is None
        and "--help" not in sys.argv
        and "-h" not in sys.argv
    ):
        show_banner()
        console.print(
            Align.center("[dim]Run 'specifyx --help' for usage information[/dim]")
        )
        console.print()


def register_commands():
    """Register commands with the main app."""
    from specify_cli.commands import check_command, init_command

    # Register commands directly on main app
    app.command("init")(init_command)
    app.command("check")(check_command)


def main():
    """Main entry point for the Specify-X CLI."""
    register_commands()
    app()
