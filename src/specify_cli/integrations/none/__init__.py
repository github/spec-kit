"""An artifact-free integration for teams using shared scaffolding only."""

from pathlib import Path
from typing import Any

from ..base import IntegrationBase
from ..manifest import IntegrationManifest


class NoneIntegration(IntegrationBase):
    key = "none"
    config = {
        "name": "None (shared scaffolding only)",
        "folder": None,
        "install_url": None,
        "requires_cli": False,
    }

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        return []
