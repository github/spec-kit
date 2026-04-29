"""Shared constants for the workflow engine and CLI layer.

This module is dependency-free (no typer, no rich) so it can be imported
by both the engine and the CLI without circular-import or side-effect concerns.
"""

INTEGRATION_JSON = ".specify/integration.json"
