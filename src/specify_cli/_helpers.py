import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from ._console import console
from ._ui import StepTracker

CLAUDE_LOCAL_PATH = Path.home() / ".claude" / "local" / "claude"
CLAUDE_NPM_LOCAL_PATH = Path.home() / ".claude" / "local" / "node_modules" / ".bin" / "claude"


def run_command(cmd: list[str], check_return: bool = True, capture: bool = False, shell: bool = False) -> Optional[str]:
    """Run a shell command and optionally capture output."""
    try:
        if capture:
            result = subprocess.run(cmd, check=check_return, capture_output=True, text=True, shell=shell)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=check_return, shell=shell)
            return None
    except subprocess.CalledProcessError as e:
        if check_return:
            console.print(f"[red]Error running command:[/red] {' '.join(cmd)}")
            console.print(f"[red]Exit code:[/red] {e.returncode}")
            if hasattr(e, 'stderr') and e.stderr:
                console.print(f"[red]Error output:[/red] {e.stderr}")
            raise
        return None


def check_tool(tool: str, tracker: StepTracker = None) -> bool:
    """Check if a tool is installed. Optionally update tracker.

    Args:
        tool: Name of the tool to check
        tracker: Optional StepTracker to update with results

    Returns:
        True if tool is found, False otherwise
    """
    # Special handling for Claude CLI local installs
    # See: https://github.com/github/spec-kit/issues/123
    # See: https://github.com/github/spec-kit/issues/550
    # Claude Code can be installed in two local paths:
    #   1. ~/.claude/local/claude          (after `claude migrate-installer`)
    #   2. ~/.claude/local/node_modules/.bin/claude  (npm-local install, e.g. via nvm)
    # Neither path may be on the system PATH, so we check them explicitly.
    if tool == "claude":
        if CLAUDE_LOCAL_PATH.is_file() or CLAUDE_NPM_LOCAL_PATH.is_file():
            if tracker:
                tracker.complete(tool, "available")
            return True

    if tool == "kiro-cli":
        # Kiro currently supports both executable names. Prefer kiro-cli and
        # accept kiro as a compatibility fallback.
        found = shutil.which("kiro-cli") is not None or shutil.which("kiro") is not None
    else:
        found = shutil.which(tool) is not None

    if tracker:
        if found:
            tracker.complete(tool, "available")
        else:
            tracker.error(tool, "not found")

    return found


def _install_shared_infra(
    project_path: Path,
    script_type: str,
    tracker: StepTracker | None = None,
    force: bool = False,
    invoke_separator: str = ".",
) -> bool:
    """Install shared infrastructure files into *project_path*.

    Copies ``.specify/scripts/`` and ``.specify/templates/`` from the
    bundled core_pack or source checkout.  Tracks all installed files
    in ``speckit.manifest.json``.

    Page templates are processed to resolve ``__SPECKIT_COMMAND_<NAME>__``
    placeholders using *invoke_separator* (``"."`` for markdown agents,
    ``"-"`` for skills agents).

    When *force* is ``True``, existing files are overwritten with the
    latest bundled versions.  When ``False`` (default), only missing
    files are added and existing ones are skipped.

    Returns ``True`` on success.
    """
    import importlib.metadata

    def _get_version() -> str:
        try:
            return importlib.metadata.version("specify-cli")
        except Exception:
            return "unknown"

    from .integrations.base import IntegrationBase
    from .integrations.manifest import IntegrationManifest
    from ._assets import _asset_service as _svc

    core = _svc.locate_core_pack()
    manifest = IntegrationManifest("speckit", project_path, version=_get_version())

    # Scripts
    if core and (core / "scripts").is_dir():
        scripts_src = core / "scripts"
    else:
        repo_root = Path(__file__).parent.parent.parent
        scripts_src = repo_root / "scripts"

    skipped_files: list[str] = []

    if scripts_src.is_dir():
        dest_scripts = project_path / ".specify" / "scripts"
        dest_scripts.mkdir(parents=True, exist_ok=True)
        variant_dir = "bash" if script_type == "sh" else "powershell"
        variant_src = scripts_src / variant_dir
        if variant_src.is_dir():
            dest_variant = dest_scripts / variant_dir
            dest_variant.mkdir(parents=True, exist_ok=True)
            for src_path in variant_src.rglob("*"):
                if src_path.is_file():
                    rel_path = src_path.relative_to(variant_src)
                    dst_path = dest_variant / rel_path
                    if dst_path.exists() and not force:
                        skipped_files.append(str(dst_path.relative_to(project_path)))
                    else:
                        dst_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_path, dst_path)
                        rel = dst_path.relative_to(project_path).as_posix()
                        manifest.record_existing(rel)

    # Page templates (not command templates, not vscode-settings.json)
    if core and (core / "templates").is_dir():
        templates_src = core / "templates"
    else:
        repo_root = Path(__file__).parent.parent.parent
        templates_src = repo_root / "templates"

    if templates_src.is_dir():
        dest_templates = project_path / ".specify" / "templates"
        dest_templates.mkdir(parents=True, exist_ok=True)
        for f in templates_src.iterdir():
            if f.is_file() and f.name != "vscode-settings.json" and not f.name.startswith("."):
                dst = dest_templates / f.name
                if dst.exists() and not force:
                    skipped_files.append(str(dst.relative_to(project_path)))
                else:
                    content = f.read_text(encoding="utf-8")
                    content = IntegrationBase.resolve_command_refs(
                        content, invoke_separator
                    )
                    dst.write_text(content, encoding="utf-8")
                    rel = dst.relative_to(project_path).as_posix()
                    manifest.record_existing(rel)

    if skipped_files:
        console.print(
            f"[yellow]⚠[/yellow]  {len(skipped_files)} shared infrastructure file(s) already exist and were not updated:"
        )
        for f in skipped_files:
            console.print(f"    {f}")
        console.print(
            "To refresh shared infrastructure, run "
            "[cyan]specify init --here --force[/cyan] or "
            "[cyan]specify integration upgrade --force[/cyan]."
        )

    manifest.save()
    return True


def ensure_executable_scripts(project_path: Path, tracker: StepTracker | None = None) -> None:
    """Ensure POSIX .sh scripts under .specify/scripts and .specify/extensions (recursively) have execute bits (no-op on Windows)."""
    if os.name == "nt":
        return  # Windows: skip silently
    scan_roots = [
        project_path / ".specify" / "scripts",
        project_path / ".specify" / "extensions",
    ]
    failures: list[str] = []
    updated = 0
    for scripts_root in scan_roots:
        if not scripts_root.is_dir():
            continue
        for script in scripts_root.rglob("*.sh"):
            try:
                if script.is_symlink() or not script.is_file():
                    continue
                try:
                    with script.open("rb") as f:
                        if f.read(2) != b"#!":
                            continue
                except Exception:
                    continue
                st = script.stat()
                mode = st.st_mode
                if mode & 0o111:
                    continue
                new_mode = mode
                if mode & 0o400:
                    new_mode |= 0o100
                if mode & 0o040:
                    new_mode |= 0o010
                if mode & 0o004:
                    new_mode |= 0o001
                if not (new_mode & 0o100):
                    new_mode |= 0o100
                os.chmod(script, new_mode)
                updated += 1
            except Exception as e:
                failures.append(f"{script.relative_to(project_path)}: {e}")
    if tracker:
        detail = f"{updated} updated" + (f", {len(failures)} failed" if failures else "")
        tracker.add("chmod", "Set script permissions recursively")
        (tracker.error if failures else tracker.complete)("chmod", detail)
    else:
        if updated:
            console.print(f"[cyan]Updated execute permissions on {updated} script(s) recursively[/cyan]")
        if failures:
            console.print("[yellow]Some scripts could not be updated:[/yellow]")
            for f in failures:
                console.print(f"  - {f}")


def ensure_constitution_from_template(project_path: Path, tracker: StepTracker | None = None) -> None:
    """Copy constitution template to memory if it doesn't exist (preserves existing constitution on reinitialization)."""
    memory_constitution = project_path / ".specify" / "memory" / "constitution.md"
    template_constitution = project_path / ".specify" / "templates" / "constitution-template.md"

    # If constitution already exists in memory, preserve it
    if memory_constitution.exists():
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.skip("constitution", "existing file preserved")
        return

    # If template doesn't exist, something went wrong with extraction
    if not template_constitution.exists():
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.error("constitution", "template not found")
        return

    # Copy template to memory directory
    try:
        memory_constitution.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_constitution, memory_constitution)
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.complete("constitution", "copied from template")
        else:
            console.print("[cyan]Initialized constitution from template[/cyan]")
    except Exception as e:
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.error("constitution", str(e))
        else:
            console.print(f"[yellow]Warning: Could not initialize constitution: {e}[/yellow]")


def _get_skills_dir(project_path: Path, selected_ai: str) -> Path:
    """Resolve the agent-specific skills directory.

    Returns ``project_path / <agent_folder> / "skills"``, falling back
    to ``project_path / ".agents/skills"`` for unknown agents.
    """
    from specify_cli import AGENT_CONFIG
    agent_config = AGENT_CONFIG.get(selected_ai, {})
    agent_folder = agent_config.get("folder", "")
    if agent_folder:
        return project_path / agent_folder.rstrip("/") / "skills"
    return project_path / ".agents" / "skills"
