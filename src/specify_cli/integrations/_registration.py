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
        from .manifest import IntegrationManifest
        from ..file_helper import FileHelper
        from ..shared_infra import _validate_safe_shared_directory

        if registration_changes.get() is not None:
            return handler(self, *args, **kwargs)
        changed: set[Path] = set()
        token = registration_changes.set(changed)
        try:
            result = handler(self, *args, **kwargs)
        finally:
            registration_changes.reset(token)
        if changed:
            root = self.project_root
            directory = root / ".specify/integrations"
            _validate_safe_shared_directory(root, directory)
            metadata = FileHelper(root)
            for path in sorted(directory.glob("*.manifest.json")):
                metadata.read_bytes(path)
                manifest = IntegrationManifest.load(path.name.removesuffix(".manifest.json"), root)
                refreshed = False
                for name in manifest.files:
                    output = root / name
                    if output in changed and output.is_file() and not output.is_symlink():
                        manifest.record_existing(name)
                        refreshed = True
                if refreshed:
                    manifest.save()
        return result

    return invoke
