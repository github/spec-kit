"""Shared helpers for extension command tests."""
from __future__ import annotations

import os
from pathlib import Path

import yaml


MINIMAL_ZIP_BYTES = b"PK\x05\x06" + b"\x00" * 18


def open_test_download_zip(project_root, download_dir, zip_filename):
    """Create a transient download file using platform-appropriate semantics."""
    target = download_dir / zip_filename
    o_temporary = getattr(os, "O_TEMPORARY", 0)
    if o_temporary:
        return os.open(
            target,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | o_temporary,
            0o600,
        )
    fd = os.open(target, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.unlink(target)
    except OSError:
        os.close(fd)
        raise
    return fd


def validate_safe_cache_dir(project_root):
    """Create the expected extension download cache for command tests."""
    download_dir = project_root / ".specify" / "extensions" / ".cache" / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


def can_create_symlink(tmp_path: Path) -> bool:
    """Return whether the current platform can create file symlinks."""
    target = tmp_path / "symlink-target.txt"
    link = tmp_path / "symlink-link.txt"
    target.write_text("ok", encoding="utf-8")
    try:
        os.symlink(target, link)
    except OSError:
        return False
    return link.is_symlink()


def installed_generic_hook_extension(tmp_path: Path, extension_dir: Path):
    """Install a hook-bearing extension with a real generic invocation artifact."""
    from specify_cli import save_init_options
    from specify_cli.extensions import ExtensionManager
    from specify_cli.integration_state import write_integration_json
    from specify_cli.integrations import get_integration
    from specify_cli.integrations.manifest import IntegrationManifest

    manifest_path = extension_dir / "extension.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["hooks"] = {"before_plan": {"command": "speckit.test-ext.hello"}}
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    project = tmp_path / "generic-project"
    project.mkdir()
    options = {"commands_dir": ".custom/commands", "skills": False}
    installation = IntegrationManifest("generic", project)
    get_integration("generic").setup(project, installation, parsed_options=options)
    installation.save()
    write_integration_json(
        project, version="1.0.0", integration_key="generic",
        settings={"generic": {"parsed_options": options}},
    )
    save_init_options(project, {"ai": "generic", "ai_skills": False, "script": "sh"})
    manager = ExtensionManager(project)
    manager.install_from_directory(extension_dir, "1.0.0")
    artifact = project / ".custom/commands/speckit.test-ext.hello.md"
    assert artifact.is_file()
    return project, manager, artifact
