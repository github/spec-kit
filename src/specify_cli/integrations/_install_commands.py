"""Compatibility imports for the extracted install and uninstall commands."""

from .command_install import integration_install
from .command_uninstall import integration_uninstall

__all__ = ["integration_install", "integration_uninstall"]
