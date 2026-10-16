"""Implementation of the ``specify preset resolve`` command."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from ._commands import preset_app


@preset_app.command("resolve")
def preset_resolve(
    template_name: str = typer.Argument(
        ..., help="Template name to resolve (e.g., spec-template)"
    ),
    kind: Literal["command", "script", "template"] | None = typer.Option(
        None,
        "--kind",
        help="Artifact kind (defaults to command for dotted names, template otherwise)",
    ),
    output: Path | None = typer.Option(  # noqa: B008
        None,
        "--output",
        help=(
            "Write the effective script to this path "
            "(required to materialize composition)"
        ),
    ),
):
    """Show which artifact wins, or materialize an effective script."""
    from .. import _require_specify_project
    from . import PresetResolver

    template_type = kind or ("command" if "." in template_name else "template")
    is_command = template_type == "command"
    valid_name = (
        re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+", template_name)
        if is_command
        else re.fullmatch(r"[a-z0-9-]+", template_name)
    )
    if valid_name is None:
        typer.echo(
            f"Error: invalid template name '{template_name}'; "
            "use lowercase letters, digits, and hyphens, with non-empty "
            "dot-separated segments for commands",
            err=True,
        )
        raise typer.Exit(1)

    if output is not None and template_type != "script":
        console.print("[red]Error:[/red] --output can only be used with --kind script")
        raise typer.Exit(1)

    project_root = _require_specify_project()
    resolver = PresetResolver(project_root)

    if output is not None:
        try:
            content = resolver.resolve_content(template_name, "script")
        except Exception as exc:
            console.print(
                f"[red]Error:[/red] Could not resolve script: "
                f"{_escape_markup(str(exc))}"
            )
            raise typer.Exit(1) from exc
        if content is None:
            console.print(
                f"[yellow]{_escape_markup(str(template_name))}[/yellow]: "
                "not found or cannot be composed"
            )
            raise typer.Exit(1)

        output_path = output.expanduser()
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        output_path = output_path.resolve()
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
        except OSError as exc:
            console.print(
                f"[red]Error:[/red] Could not write script to "
                f"{_escape_markup(str(output_path))}: {_escape_markup(str(exc))}"
            )
            raise typer.Exit(1) from exc

        console.print(
            f"  [bold]{_escape_markup(str(template_name))}[/bold]: "
            f"{_escape_markup(str(output_path))}"
        )
        console.print("    [dim](effective script written to --output path)[/dim]")
        return

    layers = resolver.collect_all_layers(template_name, template_type)
    safe_template_name = _escape_markup(str(template_name))

    if layers:
        # Use the highest-priority layer for display because the final output
        # may be composed and may not map to resolve_with_source()'s single path.
        display_layer = layers[0]
        console.print(
            f"  [bold]{safe_template_name}[/bold]: "
            f"{_escape_markup(str(display_layer['path']))}"
        )
        console.print(
            f"    [dim](top layer from: "
            f"{_escape_markup(str(display_layer['source']))})[/dim]"
        )

        has_composition = any(layer["strategy"] != "replace" for layer in layers)
        if has_composition:
            # Verify composition is actually possible
            try:
                composed = resolver.resolve_content(template_name, template_type)
            except Exception as exc:  # noqa: BLE001 - render composition failures
                composed = None
                console.print(
                    f"    [yellow]Warning: composition error: "
                    f"{_escape_markup(str(exc))}[/yellow]"
                )
            if composed is None:
                console.print(
                    "    [yellow]Warning: composition cannot produce output (no base layer with 'replace' strategy)[/yellow]"
                )
            else:
                console.print(
                    "    [dim]Final output is composed from multiple preset layers; the path above is the highest-priority contributing layer.[/dim]"
                )
                if template_type == "script":
                    console.print(
                        "    [dim]Use --output PATH to write the effective composed "
                        "script. Relative imports in the output resolve from that "
                        "file's directory.[/dim]"
                    )
            console.print("\n  [bold]Composition chain:[/bold]")
            # Compute the effective base: first replace layer scanning from
            # highest priority (matching resolve_content top-down logic).
            # Only show layers from the base upward (lower layers are ignored).
            effective_base_idx = None
            for idx, lyr in enumerate(layers):
                if lyr["strategy"] == "replace":
                    effective_base_idx = idx
                    break
            # Show only contributing layers (base and above)
            if effective_base_idx is not None:
                contributing = layers[: effective_base_idx + 1]
            else:
                contributing = layers
            for i, layer in enumerate(reversed(contributing)):
                strategy_label = layer["strategy"]
                if strategy_label == "replace" and i == 0:
                    strategy_label = "base"
                # Escape the literal bracket (\[) so Rich renders `[<strategy>]`
                # instead of parsing it as a style tag and swallowing the label,
                # mirroring `workflow info`'s step-graph line.
                console.print(
                    f"    {i + 1}. \\[{_escape_markup(str(strategy_label))}] "
                    f"{_escape_markup(str(layer['source']))} → "
                    f"{_escape_markup(str(layer['path']))}"
                )
    else:
        # No layers found — fall back to resolve_with_source for non-composition cases
        result = resolver.resolve_with_source(template_name, template_type)
        if result:
            console.print(
                f"  [bold]{safe_template_name}[/bold]: "
                f"{_escape_markup(str(result['path']))}"
            )
            console.print(
                f"    [dim](from: {_escape_markup(str(result['source']))})[/dim]"
            )
        else:
            console.print(f"  [yellow]{safe_template_name}[/yellow]: not found")
            console.print(
                "    [dim]No template with this name exists in the resolution stack[/dim]"
            )
