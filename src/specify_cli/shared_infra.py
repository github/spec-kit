"""Shared Spec Kit infrastructure installation helpers."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from .integrations.base import IntegrationBase
from .integrations.manifest import IntegrationManifest


def load_speckit_manifest(
    project_path: Path,
    *,
    version: str,
    console: Any | None = None,
) -> IntegrationManifest:
    """Load the shared infrastructure manifest, preserving existing entries."""
    manifest_path = project_path / ".specify" / "integrations" / "speckit.manifest.json"
    if manifest_path.exists():
        try:
            manifest = IntegrationManifest.load("speckit", project_path)
            manifest.version = version
            return manifest
        except (ValueError, FileNotFoundError, OSError, UnicodeDecodeError) as exc:
            if console is not None:
                console.print(
                    f"[yellow]Warning:[/yellow] Could not read shared infrastructure "
                    f"manifest at {manifest_path}: {exc}"
                )
                console.print(
                    "A new shared manifest will be created; previously tracked "
                    "shared files may be treated as untracked."
                )
    return IntegrationManifest("speckit", project_path, version=version)


def shared_templates_source(
    *,
    core_pack: Path | None,
    repo_root: Path,
) -> Path:
    """Return the bundled/source shared templates directory."""
    if core_pack and (core_pack / "templates").is_dir():
        return core_pack / "templates"
    return repo_root / "templates"


def shared_scripts_source(
    *,
    core_pack: Path | None,
    repo_root: Path,
) -> Path:
    """Return the bundled/source shared scripts directory."""
    if core_pack and (core_pack / "scripts").is_dir():
        return core_pack / "scripts"
    return repo_root / "scripts"


def _shared_destination_label(project_path: Path, dest: Path) -> str:
    try:
        return dest.relative_to(project_path).as_posix()
    except ValueError:
        return str(dest)


def _ensure_safe_shared_destination(project_path: Path, dest: Path) -> None:
    """Refuse shared infra writes that would escape or follow symlinks."""
    root = project_path.resolve()
    try:
        dest.parent.resolve().relative_to(root)
    except (OSError, ValueError):
        label = _shared_destination_label(project_path, dest)
        raise ValueError(f"Shared infrastructure destination escapes project root: {label}") from None

    label = _shared_destination_label(project_path, dest)
    if dest.is_symlink():
        raise ValueError(f"Refusing to overwrite symlinked shared infrastructure path: {label}")

    if dest.exists():
        try:
            dest.resolve().relative_to(root)
        except (OSError, ValueError):
            raise ValueError(f"Shared infrastructure destination escapes project root: {label}") from None


def _write_shared_text(project_path: Path, dest: Path, content: str) -> None:
    _write_shared_bytes(project_path, dest, content.encode("utf-8"))


def _copy_shared_file(project_path: Path, src: Path, dest: Path) -> None:
    _write_shared_bytes(project_path, dest, src.read_bytes(), mode=src.stat().st_mode & 0o777)


def _write_shared_bytes(
    project_path: Path,
    dest: Path,
    content: bytes,
    *,
    mode: int = 0o666,
) -> None:
    _ensure_safe_shared_destination(project_path, dest)
    fd, temp_name = tempfile.mkstemp(prefix=f".{dest.name}.", dir=dest.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(content)
        temp_path.chmod(mode)
        _ensure_safe_shared_destination(project_path, dest)
        os.replace(temp_path, dest)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def refresh_shared_templates(
    project_path: Path,
    *,
    version: str,
    core_pack: Path | None,
    repo_root: Path,
    console: Any,
    invoke_separator: str,
    force: bool = False,
) -> None:
    """Refresh default-sensitive shared templates without touching scripts."""
    templates_src = shared_templates_source(core_pack=core_pack, repo_root=repo_root)
    if not templates_src.is_dir():
        return

    manifest = load_speckit_manifest(project_path, version=version, console=console)
    tracked_files = manifest.files
    modified = set(manifest.check_modified())
    skipped_files: list[str] = []

    dest_templates = project_path / ".specify" / "templates"
    dest_templates.mkdir(parents=True, exist_ok=True)
    for src in templates_src.iterdir():
        if not src.is_file() or src.name == "vscode-settings.json" or src.name.startswith("."):
            continue

        dst = dest_templates / src.name
        _ensure_safe_shared_destination(project_path, dst)
        rel = dst.relative_to(project_path).as_posix()
        if dst.exists() and not force:
            if rel not in tracked_files or rel in modified:
                skipped_files.append(rel)
                continue

        content = src.read_text(encoding="utf-8")
        content = IntegrationBase.resolve_command_refs(content, invoke_separator)
        _write_shared_text(project_path, dst, content)
        manifest.record_existing(rel)

    manifest.save()

    if skipped_files:
        console.print(
            f"[yellow]⚠[/yellow]  {len(skipped_files)} modified or untracked shared template file(s) were not updated:"
        )
        for rel in skipped_files:
            console.print(f"    {rel}")


def install_shared_infra(
    project_path: Path,
    script_type: str,
    *,
    version: str,
    core_pack: Path | None,
    repo_root: Path,
    console: Any,
    force: bool = False,
    invoke_separator: str = ".",
) -> bool:
    """Install shared scripts and templates into *project_path*."""
    manifest = load_speckit_manifest(project_path, version=version, console=console)
    skipped_files: list[str] = []

    scripts_src = shared_scripts_source(core_pack=core_pack, repo_root=repo_root)
    if scripts_src.is_dir():
        dest_scripts = project_path / ".specify" / "scripts"
        dest_scripts.mkdir(parents=True, exist_ok=True)
        variant_dir = "bash" if script_type == "sh" else "powershell"
        variant_src = scripts_src / variant_dir
        if variant_src.is_dir():
            dest_variant = dest_scripts / variant_dir
            dest_variant.mkdir(parents=True, exist_ok=True)
            for src_path in variant_src.rglob("*"):
                if not src_path.is_file():
                    continue

                rel_path = src_path.relative_to(variant_src)
                dst_path = dest_variant / rel_path
                _ensure_safe_shared_destination(project_path, dst_path)
                if dst_path.exists() and not force:
                    skipped_files.append(str(dst_path.relative_to(project_path)))
                    continue

                dst_path.parent.mkdir(parents=True, exist_ok=True)
                _copy_shared_file(project_path, src_path, dst_path)
                rel = dst_path.relative_to(project_path).as_posix()
                manifest.record_existing(rel)

    templates_src = shared_templates_source(core_pack=core_pack, repo_root=repo_root)
    if templates_src.is_dir():
        dest_templates = project_path / ".specify" / "templates"
        dest_templates.mkdir(parents=True, exist_ok=True)
        for src in templates_src.iterdir():
            if not src.is_file() or src.name == "vscode-settings.json" or src.name.startswith("."):
                continue

            dst = dest_templates / src.name
            _ensure_safe_shared_destination(project_path, dst)
            if dst.exists() and not force:
                skipped_files.append(str(dst.relative_to(project_path)))
                continue

            content = src.read_text(encoding="utf-8")
            content = IntegrationBase.resolve_command_refs(content, invoke_separator)
            _write_shared_text(project_path, dst, content)
            rel = dst.relative_to(project_path).as_posix()
            manifest.record_existing(rel)

    if skipped_files:
        console.print(
            f"[yellow]⚠[/yellow]  {len(skipped_files)} shared infrastructure file(s) already exist and were not updated:"
        )
        for path in skipped_files:
            console.print(f"    {path}")
        console.print(
            "To refresh shared infrastructure, run "
            "[cyan]specify init --here --force[/cyan] or "
            "[cyan]specify integration upgrade --force[/cyan]."
        )

    manifest.save()
    return True
