"""An artifact-free integration for teams using shared scaffolding only."""

from pathlib import Path

from ..base import IntegrationBase
from ..manifest import IntegrationManifest


class NoneIntegration(IntegrationBase):
    key = "none"
    multi_install_safe = True
    config = {
        "name": "None (shared scaffolding only)",
        "folder": None,
        "install_url": None,
        "requires_cli": False,
    }

    def list_command_templates(self) -> list[Path]:
        return []

    def teardown(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        *,
        force: bool = False,
    ) -> tuple[list[Path], list[Path]]:
        return manifest.uninstall(project_root, force=force)
