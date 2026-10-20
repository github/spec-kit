"""An artifact-free integration for teams using shared scaffolding only."""

from pathlib import Path

from ..base import IntegrationBase


class NoneIntegration(IntegrationBase):
    key = "none"
    config = {
        "name": "None (shared scaffolding only)",
        "folder": None,
        "install_url": None,
        "requires_cli": False,
    }

    def list_command_templates(self) -> list[Path]:
        return []
