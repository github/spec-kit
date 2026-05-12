"""ASCII banner displayed at the top of every ``infrakit`` command run.

:class:`BannerGroup` overrides Typer's group class so that ``infrakit --help``
also prints the banner before the help text.
"""

from __future__ import annotations

from rich.align import Align
from rich.text import Text
from typer.core import TyperGroup

from .console import console

BANNER = """
██╗███╗   ██╗███████╗██████╗  █████╗ ██╗  ██╗██╗████████╗
██║████╗  ██║██╔════╝██╔══██╗██╔══██╗██║ ██╔╝██║╚══██╔══╝
██║██╔██╗ ██║█████╗  ██████╔╝███████║█████╔╝ ██║   ██║
██║██║╚██╗██║██╔══╝  ██╔══██╗██╔══██║██╔═██╗ ██║   ██║
██║██║ ╚████║██║     ██║  ██║██║  ██║██║  ██╗██║   ██║
╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝   ╚═╝
"""

TAGLINE = "InfraKit — spec-kit for IaC, with a multi-persona pipeline"


def show_banner():
    """Render the ASCII banner with a gradient and the project tagline beneath."""
    banner_lines = BANNER.strip().split("\n")
    colors = ["bright_blue", "blue", "cyan", "bright_cyan", "white", "bright_white"]

    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)

    console.print(Align.center(styled_banner))
    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()


class BannerGroup(TyperGroup):
    """Typer group that prints the banner ahead of ``--help`` output."""

    def format_help(self, ctx, formatter):
        show_banner()
        super().format_help(ctx, formatter)
