"""Top-level constants shared by the CLI and the workflow engine.

This module is dependency-free (no typer, no rich, no workflow imports), so it
can be imported from anywhere inside the package without triggering side effects.
"""

INTEGRATION_JSON = ".specify/integration.json"
