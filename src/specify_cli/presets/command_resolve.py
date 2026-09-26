"""Implementation of the ``specify preset resolve`` command."""

from __future__ import annotations

import re

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from ._commands import preset_app


@preset_app.command("script-chain", hidden=True)
def preset_script_chain(
    script_name: str = typer.Argument(
        ..., help="Script name to resolve (e.g., setup-plan)"
    ),
):
    """Print the resolved script continuation chain, one path per line.

    Internal command consumed by the generated script continuation
    dispatcher and runner (see ``PresetResolver.resolve_script_chain``);
    not intended for interactive use. Output is the ordered chain of
    file paths from highest priority to the terminating "replace" layer,
    one absolute path per line, with no other output.
    """
    from .. import _require_specify_project
    from . import PresetResolver, PresetValidationError

    if re.fullmatch(r"[a-z0-9-]+", script_name) is None:
        typer.echo(
            f"Error: invalid script name '{script_name}'; "
            "use lowercase letters, digits, and hyphens",
            err=True,
        )
        raise typer.Exit(1)

    project_root = _require_specify_project()
    resolver = PresetResolver(project_root)
    try:
        chain = resolver.resolve_script_chain(script_name)
    except PresetValidationError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    if not chain:
        typer.echo(
            f"Error: could not resolve a script chain for '{script_name}'",
            err=True,
        )
        raise typer.Exit(1)

    for path in chain:
        typer.echo(str(path))


@preset_app.command("resolve")
def preset_resolve(
    template_name: str = typer.Argument(
        ..., help="Template name to resolve (e.g., spec-template)"
    ),
):
    """Show which template will be resolved for a given name."""
    from .. import _require_specify_project
    from . import PresetResolver

    is_command = "." in template_name
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

    project_root = _require_specify_project()
    resolver = PresetResolver(project_root)
    template_type = "command" if is_command else "template"

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

        has_composition = layers[0]["strategy"] != "replace" and any(
            layer["strategy"] != "replace" for layer in layers
        )
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
