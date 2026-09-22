"""CLI adapter for ``specify version``."""

from __future__ import annotations

import json
import platform

import typer
from rich.panel import Panel
from rich.table import Table

from ._console import console, show_banner


def _feature_capabilities() -> dict[str, bool]:
    """Return stable local CLI capability flags for humans and agents."""
    return {
        "controlled_multi_install_integrations": True,
        "integration_use_command": True,
        "multi_install_safe_registry_metadata": True,
        "integration_upgrade_command": True,
        "self_check_command": True,
        "workflow_catalog": True,
        "bundled_templates": True,
    }


def version(
    features: bool = typer.Option(
        False,
        "--features",
        help="Show local CLI feature capabilities.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit feature capabilities as JSON. Requires --features.",
    ),
) -> None:
    """Display version and system information."""
    from . import get_speckit_version

    cli_version = get_speckit_version()

    if json_output and not features:
        console.print("[red]Error:[/red] --json requires --features.")
        raise typer.Exit(1)

    if features:
        capabilities = _feature_capabilities()
        if json_output:
            payload = {"version": cli_version, "features": capabilities}
            console.print(json.dumps(payload, indent=2))
            return

        console.print(f"Spec Kit CLI: {cli_version}")
        console.print()
        console.print("Features:")
        for key, enabled in capabilities.items():
            label = key.replace("_", " ")
            console.print(f"- {label}: {'yes' if enabled else 'no'}")
        return

    show_banner()

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Key", style="cyan", justify="right")
    info_table.add_column("Value", style="white")

    info_table.add_row("CLI Version", cli_version)
    info_table.add_row("", "")
    info_table.add_row("Python", platform.python_version())
    info_table.add_row("Platform", platform.system())
    info_table.add_row("Architecture", platform.machine())
    info_table.add_row("OS Version", platform.version())
    # The OpenSSL runtime the interpreter actually loaded. HTTPS failure
    # reports (#4433) hinge on which OpenSSL is in play, and on Windows it is
    # not obvious from the outside, so surface it here. An interpreter built
    # without the ssl extension skips the row rather than failing the command.
    try:
        import ssl

        openssl_version = getattr(ssl, "OPENSSL_VERSION", "")
    except ImportError:
        openssl_version = ""
    if openssl_version:
        info_table.add_row("OpenSSL", openssl_version)

    panel = Panel(
        info_table,
        title="[bold cyan]Specify CLI Information[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )

    console.print(panel)
    console.print()


def register(app: typer.Typer) -> None:
    """Register ``specify version`` on the root application."""
    app.command()(version)
