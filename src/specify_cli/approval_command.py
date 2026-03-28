"""Approval gate command

Provides 'specify approval' command using Typer framework.
"""

import typer
from rich.console import Console
from specify_cli.approval_gates import ApprovalGatesConfig

console = Console()


def approval_command(
    action: str = typer.Option("status", "--action", "-a", help="Approval action"),
):
    """Check approval gates status (if configured).

    If no .speckit/approval-gates.yaml exists, returns helpful message.

    Example:
        specify approval
    """

    config = ApprovalGatesConfig.load()

    if config is None:
        console.print("ℹ️  No approval gates configured")
        console.print("   Create .speckit/approval-gates.yaml to enable")
        console.print("")
        console.print("   See: docs/approval-gates-guide.md for setup")
        return

    if action == "status":
        console.print("✅ Approval gates enabled")
        console.print("")
        for phase, gate in config.gates.items():
            if gate.get("enabled"):
                min_approvals = gate.get("min_approvals", 1)
                console.print(f"  {phase}")
                console.print(f"    • Enabled: ✅")
                console.print(f"    • Min approvals: {min_approvals}")
            else:
                console.print(f"  {phase}: disabled")