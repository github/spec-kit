"""Shared path constants for specify_cli.

This module is intentionally dependency-free (no typer, no rich, no workflows)
so it can be safely imported from anywhere in the package without side effects.
"""

SPECIFY_DIR = ".specify"
INTEGRATION_JSON = ".specify/integration.json"
INIT_OPTIONS_FILE = ".specify/init-options.json"
