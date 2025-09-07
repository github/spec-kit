"""System and utility commands."""

import shutil

import httpx


def check_tool(console, tool: str, install_hint: str) -> bool:
    """Check if a tool is installed."""
    if shutil.which(tool):
        console.print(f"[green]✓[/green] {tool} found")
        return True
    else:
        console.print(f"[yellow]⚠️  {tool} not found[/yellow]")
        console.print(f"   Install with: [cyan]{install_hint}[/cyan]")
        return False


def check_command():
    """Check that all required tools are installed."""
    from specify_cli.core.app import console, show_banner

    show_banner()
    console.print("[bold]Checking Specify requirements...[/bold]\n")

    # Check internet connectivity
    console.print("[cyan]Checking internet connectivity...[/cyan]")
    try:
        httpx.get("https://api.github.com", timeout=5, follow_redirects=True)
        console.print("[green]✓[/green] Internet connection available")
    except httpx.RequestError:
        console.print(
            "[red]✗[/red] No internet connection - required for downloading templates"
        )
        console.print("[yellow]Please check your internet connection[/yellow]")

    console.print("\n[cyan]Optional tools:[/cyan]")
    git_ok = check_tool(console, "git", "https://git-scm.com/downloads")

    console.print("\n[cyan]Optional AI tools:[/cyan]")
    claude_ok = check_tool(
        console,
        "claude",
        "Install from: https://docs.anthropic.com/en/docs/claude-code/setup",
    )
    gemini_ok = check_tool(
        console, "gemini", "Install from: https://github.com/google-gemini/gemini-cli"
    )

    console.print("\n[green]✓ Specify-X CLI is ready to use![/green]")
    if not git_ok:
        console.print(
            "[yellow]Consider installing git for repository management[/yellow]"
        )
    if not (claude_ok or gemini_ok):
        console.print(
            "[yellow]Consider installing an AI assistant for the best experience[/yellow]"
        )
