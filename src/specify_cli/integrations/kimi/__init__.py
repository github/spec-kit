"""Kimi Code integration — skills-based agent (Moonshot AI).

Kimi uses the ``.kimi-code/skills/speckit-<name>/SKILL.md`` layout with
``/skill:speckit-<name>`` invocation syntax.

Includes legacy migration logic for projects initialised before Kimi
Code CLI adopted the ``.kimi-code/`` directory, as well as for the
older dotted skill directory naming (``speckit.xxx`` → ``speckit-xxx``).
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from ..base import IntegrationBase, IntegrationOption, SkillsIntegration
from ..manifest import IntegrationManifest


class KimiIntegration(SkillsIntegration):
    """Integration for Kimi Code CLI (Moonshot AI)."""

    key = "kimi"
    config = {
        "name": "Kimi Code",
        "folder": ".kimi-code/",
        "commands_subdir": "skills",
        "install_url": "https://code.kimi.com/",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".kimi-code/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    context_file = "AGENTS.md"
    multi_install_safe = False

    def build_command_invocation(self, command_name: str, args: str = "") -> str:
        """Build Kimi's native skill invocation: ``/skill:speckit-<stem>``.

        Kimi Code CLI invokes installed skills with a ``/skill:<name>``
        slash command (e.g. ``/skill:speckit-plan``), not the bare
        ``/speckit-<name>`` form produced by the generic skills base
        class. Overriding here keeps ``dispatch_command()`` and workflow
        command steps aligned with the ``/skill:`` guidance shown at init
        time and in rendered hook invocations.
        """
        stem = command_name
        if stem.startswith("speckit."):
            stem = stem[len("speckit."):]

        invocation = "/skill:speckit-" + stem.replace(".", "-")
        if args:
            invocation = f"{invocation} {args}"
        return invocation

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Kimi)",
            ),
            IntegrationOption(
                "--migrate-legacy",
                is_flag=True,
                default=False,
                help=(
                    "Migrate legacy Kimi installations: "
                    ".kimi/skills/ → .kimi-code/skills/ and speckit.xxx → speckit-xxx"
                ),
            ),
        ]

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install skills with optional legacy migration."""
        parsed_options = parsed_options or {}

        # Run base setup first so new-path targets (speckit-*) exist,
        # then migrate/clean legacy dirs without risking user content loss.
        created = super().setup(
            project_root, manifest, parsed_options=parsed_options, **opts
        )

        if parsed_options.get("migrate_legacy", False):
            new_skills_dir = self.skills_dest(project_root)
            old_skills_dir = project_root / ".kimi" / "skills"
            if _is_safe_legacy_dir(old_skills_dir, project_root):
                _migrate_legacy_kimi_skills_dir(old_skills_dir, new_skills_dir)
            _migrate_legacy_kimi_context_file(project_root)

        return created

    def teardown(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        *,
        force: bool = False,
    ) -> tuple[list[Path], list[Path]]:
        """Uninstall Kimi skills and remove leftover legacy directories."""
        removed, skipped = super().teardown(project_root, manifest, force=force)

        old_skills_dir = project_root / ".kimi" / "skills"
        if _is_safe_legacy_dir(old_skills_dir, project_root):
            legacy_dirs = sorted(
                [*old_skills_dir.glob("speckit-*"), *old_skills_dir.glob("speckit.*")]
            )
            for legacy_dir in legacy_dirs:
                if legacy_dir.is_symlink() or not legacy_dir.is_dir():
                    continue
                if _is_speckit_generated_skill(legacy_dir):
                    try:
                        shutil.rmtree(legacy_dir)
                        removed.append(legacy_dir)
                    except OSError:
                        skipped.append(legacy_dir)

            try:
                old_skills_dir.rmdir()
            except OSError:
                pass

        return removed, skipped


def _is_safe_legacy_dir(path: Path, project_root: Path) -> bool:
    """Return ``True`` when *path* is a real directory safely inside *project_root*.

    Legacy migration and cleanup ``shutil.move()`` and ``shutil.rmtree()``
    directories, so a symlinked ``.kimi``/``.kimi/skills`` (or one reached
    through a symlinked parent) must never be followed: doing so could
    relocate or delete content living outside the project tree. We reject
    the path when it is itself a symlink, when it is not a directory, or
    when resolving every symlink lands outside *project_root*.
    """
    if path.is_symlink() or not path.is_dir():
        return False
    try:
        resolved = path.resolve()
        root = project_root.resolve()
    except OSError:
        return False
    return resolved == root or root in resolved.parents


def _migrate_legacy_kimi_skills_dir(
    old_skills_dir: Path, new_skills_dir: Path
) -> tuple[int, int]:
    """Migrate skills from the legacy ``.kimi/skills/`` directory to ``.kimi-code/skills/``.

    Handles both hyphenated (``speckit-xxx``) and dotted (``speckit.xxx``)
    legacy directory names. If a target already exists, the legacy dir is
    only removed when its ``SKILL.md`` is byte-identical and no extra user
    files are present.

    Returns ``(migrated_count, removed_count)``.
    """
    if not old_skills_dir.is_dir():
        return (0, 0)

    migrated_count = 0
    removed_count = 0

    # Process hyphenated dirs first, then dotted dirs.
    legacy_dirs = sorted(old_skills_dir.glob("speckit-*")) + sorted(
        old_skills_dir.glob("speckit.*")
    )

    for legacy_dir in legacy_dirs:
        if legacy_dir.is_symlink() or not legacy_dir.is_dir():
            continue
        if not (legacy_dir / "SKILL.md").exists():
            continue

        target_name = _legacy_to_target_name(legacy_dir.name)
        if not target_name:
            continue

        target_dir = new_skills_dir / target_name

        # Skip if the legacy dir is already the target dir (same-directory call).
        if legacy_dir.resolve() == target_dir.resolve():
            continue

        if not target_dir.exists():
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(legacy_dir), str(target_dir))
            migrated_count += 1
            continue

        # Target exists — only remove legacy if SKILL.md is identical
        target_skill = target_dir / "SKILL.md"
        legacy_skill = legacy_dir / "SKILL.md"
        if target_skill.is_file():
            try:
                if target_skill.read_bytes() == legacy_skill.read_bytes():
                    has_extra = any(
                        child.name != "SKILL.md" for child in legacy_dir.iterdir()
                    )
                    if not has_extra:
                        shutil.rmtree(legacy_dir)
                        removed_count += 1
            except OSError:
                pass

    # Remove the legacy skills directory if it is now empty.
    try:
        old_skills_dir.rmdir()
    except OSError:
        pass

    return (migrated_count, removed_count)


def _legacy_to_target_name(legacy_name: str) -> str:
    """Convert a legacy skill directory name to the modern hyphenated form."""
    if legacy_name.startswith("speckit-"):
        return legacy_name
    if legacy_name.startswith("speckit."):
        suffix = legacy_name[len("speckit."):]
        if suffix:
            return f"speckit-{suffix.replace('.', '-')}"
    return ""


def _is_speckit_generated_skill(skill_dir: Path) -> bool:
    """Return True when *skill_dir* contains a Speckit-generated SKILL.md.

    Uses the ``metadata.author`` and ``metadata.source`` fields written by
    ``SkillsIntegration.setup()`` to avoid deleting user-authored skills.
    """
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return False

    try:
        content = skill_file.read_text(encoding="utf-8")
    except OSError:
        return False

    if not content.startswith("---"):
        return False

    parts = content.split("---", 2)
    if len(parts) < 3:
        return False

    try:
        import yaml

        frontmatter = yaml.safe_load(parts[1])
    except Exception:
        return False

    if not isinstance(frontmatter, dict):
        return False

    metadata = frontmatter.get("metadata", {})
    if not isinstance(metadata, dict):
        return False

    author = metadata.get("author", "")
    source = metadata.get("source", "")
    return author == "github-spec-kit" or (
        isinstance(source, str) and source.startswith("templates/commands/")
    )


def _migrate_legacy_kimi_context_file(project_root: Path) -> bool:
    """Migrate user content from legacy ``KIMI.md`` to ``AGENTS.md``.

    The Speckit managed section is stripped from ``KIMI.md`` before the
    remaining content is appended to ``AGENTS.md``. The legacy file is
    deleted if it becomes empty. Returns ``True`` if ``KIMI.md`` existed
    and was processed.
    """
    legacy_path = project_root / "KIMI.md"
    if not legacy_path.is_file():
        return False

    marker_start = IntegrationBase.CONTEXT_MARKER_START
    marker_end = IntegrationBase.CONTEXT_MARKER_END

    content = legacy_path.read_text(encoding="utf-8-sig")
    start_idx = content.find(marker_start)
    end_idx = content.find(marker_end, start_idx if start_idx != -1 else 0)

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        removal_start = start_idx
        removal_end = end_idx + len(marker_end)
        if removal_end < len(content) and content[removal_end] == "\r":
            removal_end += 1
        if removal_end < len(content) and content[removal_end] == "\n":
            removal_end += 1
        if removal_start > 0 and content[removal_start - 1] == "\n":
            if removal_start > 1 and content[removal_start - 2] == "\n":
                removal_start -= 1
        content = content[:removal_start] + content[removal_end:]

    user_content = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not user_content:
        legacy_path.unlink()
        return True

    target_path = project_root / "AGENTS.md"
    if target_path.is_file():
        existing = target_path.read_text(encoding="utf-8-sig")
        existing = existing.replace("\r\n", "\n").replace("\r", "\n")
        if not existing.endswith("\n"):
            existing += "\n"
        new_content = existing + "\n" + user_content + "\n"
    else:
        new_content = user_content + "\n"

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(new_content.encode("utf-8"))
    legacy_path.unlink()
    return True


def _migrate_legacy_kimi_dotted_skills(skills_dir: Path) -> tuple[int, int]:
    """Migrate legacy Kimi dotted skill dirs (speckit.xxx) to hyphenated format.

    .. deprecated::
        Kept for direct callers/tests; new code should use
        ``_migrate_legacy_kimi_skills_dir``.

    Returns ``(migrated_count, removed_count)``.
    """
    return _migrate_legacy_kimi_skills_dir(skills_dir, skills_dir)
