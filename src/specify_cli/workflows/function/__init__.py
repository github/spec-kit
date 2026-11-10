"""Workflow function domain and ``specify workflow function`` commands."""

from __future__ import annotations

import typer

function_app = typer.Typer(
    name="function", help="Manage workflow expression functions", add_completion=False
)


def register(app: typer.Typer) -> None:
    from . import command_add  # noqa: F401
    from . import command_list  # noqa: F401
    from . import command_remove  # noqa: F401

    app.add_typer(function_app, name="function")


from ._domain import (  # noqa: E402
    FunctionExport,
    FunctionManifest,
    FunctionRegistry,
    WorkflowFunctionError,
    parse_function_manifest,
)
from .loader import load_workflow_functions  # noqa: E402

__all__ = [
    "FunctionExport",
    "FunctionManifest",
    "FunctionRegistry",
    "WorkflowFunctionError",
    "function_app",
    "load_workflow_functions",
    "parse_function_manifest",
    "register",
]
