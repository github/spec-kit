#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#    "typer",
#    "rich",
#    "httpx",
#    "platformdirs",
#    "readchar",
#    "jinja2",
#    "dynaconf",
#    "tomli-w"
# ]
# ///

"""
Specify-X CLI - Setup tool for Specify-X projects

Usage:
    uvx specify-cli.py init <project-name>
    uvx specify-cli.py init --here

Or install globally:
    uv tool install --from specify-cli.py specify-cli
    specifyx init <project-name>
    specifyx init --here
"""

from .core.app import main

if __name__ == "__main__":
    main()
