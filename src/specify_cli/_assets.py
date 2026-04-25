import re
from pathlib import Path


class AssetService:
    """Locates bundled assets (core_pack, extensions, workflows, presets)."""

    def locate_core_pack(self) -> Path | None:
        candidate = Path(__file__).parent / "core_pack"
        if candidate.is_dir():
            return candidate
        return None

    def locate_bundled_extension(self, extension_id: str) -> Path | None:
        if not re.match(r'^[a-z0-9-]+$', extension_id):
            return None
        core = self.locate_core_pack()
        if core is not None:
            candidate = core / "extensions" / extension_id
            if (candidate / "extension.yml").is_file():
                return candidate
        repo_root = Path(__file__).parent.parent.parent
        candidate = repo_root / "extensions" / extension_id
        if (candidate / "extension.yml").is_file():
            return candidate
        return None

    def locate_bundled_workflow(self, workflow_id: str) -> Path | None:
        if not re.match(r'^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$', workflow_id):
            return None
        core = self.locate_core_pack()
        if core is not None:
            candidate = core / "workflows" / workflow_id
            if (candidate / "workflow.yml").is_file():
                return candidate
        repo_root = Path(__file__).parent.parent.parent
        candidate = repo_root / "workflows" / workflow_id
        if (candidate / "workflow.yml").is_file():
            return candidate
        return None

    def locate_bundled_preset(self, preset_id: str) -> Path | None:
        if not re.match(r'^[a-z0-9-]+$', preset_id):
            return None
        core = self.locate_core_pack()
        if core is not None:
            candidate = core / "presets" / preset_id
            if (candidate / "preset.yml").is_file():
                return candidate
        repo_root = Path(__file__).parent.parent.parent
        candidate = repo_root / "presets" / preset_id
        if (candidate / "preset.yml").is_file():
            return candidate
        return None


# Module-level singleton for backward compat
_asset_service = AssetService()
