"""The ``specify integration status`` command."""
from __future__ import annotations

import json
from typing import Any

import typer
from rich.markup import escape as _rich_escape

from .._console import console
from ._commands import integration_app


def _print_integration_status_report(report: dict[str, Any]) -> None:
    status = report["status"]
    status_label = {
        "ok": "[green]OK[/green]",
        "warning": "[yellow]WARNING[/yellow]",
        "error": "[red]ERROR[/red]",
    }.get(str(status), str(status).upper())
    installed = report.get("installed_integrations") or []
    installed_display = ", ".join(_rich_escape(str(item)) for item in installed)

    console.print(f"Integration status: {status_label}")
    console.print(
        f"Default integration: {_rich_escape(str(report.get('default_integration') or 'none'))}"
    )
    console.print(f"Installed integrations: {installed_display if installed else 'none'}")
    multi_install_safe = report.get("multi_install_safe")
    if multi_install_safe is None:
        multi_install_safe_display = "unknown"
    else:
        multi_install_safe_display = "yes" if multi_install_safe else "no"
    console.print(f"Multi-install safe: {multi_install_safe_display}")
    console.print(
        f"Shared templates target alignment: "
        f"{_rich_escape(str(report.get('shared_templates_target_alignment') or 'none'))}"
    )
    console.print(f"Modified managed files: {report.get('modified_managed_files', 0)}")
    console.print(f"Missing managed files: {report.get('missing_managed_files', 0)}")
    console.print(f"Invalid manifest paths: {report.get('invalid_manifest_paths', 0)}")
    console.print(f"Unchecked manifests: {report.get('unchecked_manifests', 0)}")

    findings = report.get("findings") or []
    if not findings:
        return

    console.print()
    console.print("[bold]Findings:[/bold]")
    for item in findings:
        severity = item.get("severity", "")
        severity_label = {
            "error": "[red]error[/red]",
            "warning": "[yellow]warning[/yellow]",
        }.get(severity, severity)
        prefix = f"- {severity_label} {_rich_escape(str(item.get('code', '')))}"
        if item.get("integration"):
            prefix += f" ({_rich_escape(str(item['integration']))})"
        console.print(
            f"{prefix}: {_rich_escape(str(item.get('message', '')))}",
            soft_wrap=True,
        )
        if item.get("suggestion"):
            console.print(
                f"  Suggestion: {_rich_escape(str(item['suggestion']))}",
                soft_wrap=True,
            )


@integration_app.command("status")
def integration_status(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable integration status.",
    ),
):
    """Report the current project's integration status without changing files."""
    from .. import _require_specify_project
    from ..integration_status import build_integration_status_report

    project_root = _require_specify_project()
    report = build_integration_status_report(project_root)

    if json_output:
        typer.echo(json.dumps(report, indent=2))
    else:
        _print_integration_status_report(report)

    if report["status"] == "error":
        raise typer.Exit(1)
