"""Pin project-local implementations throughout command and skill rendering."""

from __future__ import annotations

import inspect
from functools import wraps
from pathlib import Path


def project_registration(handler):
    signature = inspect.signature(handler)

    @wraps(handler)
    def invoke(*args, **kwargs):
        from .installer import project_integrations

        values = signature.bind(*args, **kwargs).arguments
        root = (
            values["project_root"] if "project_root" in signature.parameters
            else values["self"].project_root
        )
        with project_integrations(root):
            return handler(*args, **kwargs)

    return invoke


def managed_registration(handler):
    """Refresh existing claims only after managed output rendering succeeds."""
    @wraps(handler)
    def invoke(self, *args, **kwargs):
        from ._file_changes import registration_changes
        from ._helpers import _resync_manifest_after_registration, _snapshot_manifest_before_registration
        from .manifest import IntegrationManifest
        from ..file_helper import FileHelper
        from ..shared_infra import _validate_safe_shared_directory

        if registration_changes.get() is not None:
            return handler(self, *args, **kwargs)
        root = self.project_root
        directory = root / ".specify/integrations"
        _validate_safe_shared_directory(root, directory)
        metadata = FileHelper(root)
        snapshots: dict[str, set[str]] = {}
        for path in sorted(directory.glob("*.manifest.json")):
            metadata.read_bytes(path)
            key = path.name.removesuffix(".manifest.json")
            manifest, unmodified = _snapshot_manifest_before_registration(root, key)
            if manifest is not None:
                snapshots[key] = unmodified
        changed: set[Path] = set()
        token = registration_changes.set(changed)
        try:
            result = handler(self, *args, **kwargs)
        finally:
            registration_changes.reset(token)
        for key, unmodified in snapshots.items():
            written = {name for name in unmodified if root / name in changed}
            if not written:
                continue
            metadata.read_bytes(f".specify/integrations/{key}.manifest.json")
            manifest = IntegrationManifest.load(key, root)
            _resync_manifest_after_registration(
                manifest, key, unmodified_files=written,
                continuing="Managed outputs were rendered, but their manifest hashes may be stale.",
            )
        return result

    return invoke
