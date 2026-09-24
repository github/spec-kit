from __future__ import annotations

import re
from pathlib import Path

import yaml

from specify_cli.extensions import ExtensionRegistry

ERROR_REGEX = re.compile(
    r"^(unknown artifact |unknown contribution |ambiguous artifact |"
    r"artifact resolution failed|not a Spec Kit project)"
)


def install_extension_with_hooks(
    project_root: Path,
    extension_id: str,
    hooks: dict,
    *,
    manifest_id: str | None = None,
    priority: int = 10,
    enabled: bool = True,
) -> Path:
    """Create a registered extension whose manifest declares hook contributions."""
    ext_dir = project_root / ".specify" / "extensions" / extension_id
    ext_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "1.0",
        "extension": {
            "id": manifest_id or extension_id,
            "name": manifest_id or extension_id,
            "version": "1.0.0",
            "description": "Test extension",
            "author": "test",
            "repository": "https://example.com",
            "license": "MIT",
        },
        "requires": {"speckit_version": ">=0.2.0"},
        "provides": {},
        "hooks": hooks,
    }
    (ext_dir / "extension.yml").write_text(
        yaml.safe_dump(manifest), encoding="utf-8"
    )
    ExtensionRegistry(project_root / ".specify" / "extensions").add(
        extension_id,
        {"version": "1.0.0", "enabled": enabled, "priority": priority},
    )
    return ext_dir


def write_hook_binding(
    project_root: Path,
    event_name: str,
    entries: list[dict],
) -> None:
    """Write concrete hook bindings in the runtime extension configuration."""
    config_path = project_root / ".specify" / "extensions.yml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "installed": [],
                "settings": {"auto_execute_hooks": True},
                "hooks": {event_name: entries},
            }
        ),
        encoding="utf-8",
    )
