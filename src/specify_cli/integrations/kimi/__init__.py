"""Kimi Code integration — skills-based agent (Moonshot AI).

Kimi uses the ``.kimi-code/skills/speckit-<name>/SKILL.md`` layout with
``/skill:speckit-<name>`` invocation syntax.

Legacy migration covers projects created before Kimi Code CLI moved to
this layout and handles two distinct changes: the directory move from
``.kimi/`` to ``.kimi-code/`` (including the ``KIMI.md`` → ``AGENTS.md``
context file), and the dotted-to-hyphenated skill naming
(``speckit.xxx`` → ``speckit-xxx``).
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
            stem = stem[len("speckit.") :]

        invocation = "/skill:speckit-" + stem.replace(".", "-")
        if args:
            invocation = f"{invocation} {args}"
        return invocation

    def post_process_skill_content(self, content: str) -> str:
        """Ensure in-skill cross-command references use Kimi's `/skill:` syntax."""
        content = super().post_process_skill_content(content)
        return content.replace("/speckit-", "/skill:speckit-")

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
                    ".kimi/skills/ → .kimi-code/skills/, speckit.xxx → speckit-xxx, "
                    "and (when the agent-context extension is enabled) "
                    "KIMI.md user content → AGENTS.md"
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

        # Refuse a symlinked destination before any writes occur. base
        # setup() only rejects a destination that *escapes* project_root
        # after resolve(), so an in-tree symlinked ``.kimi-code`` /
        # ``.kimi-code/skills`` (e.g. ``-> .``) would still pass that check
        # and misdirect the SKILL.md writes into an unintended in-tree
        # location (e.g. ``./skills/``). Reject any symlinked destination
        # component up front so this never happens.
        new_skills_dir = self.skills_dest(project_root)
        if _has_symlinked_component(new_skills_dir, project_root):
            raise ValueError(
                f"Skills destination {new_skills_dir} contains a symlinked "
                f"path component; refusing to install into it."
            )

        # Run base setup first so new-path targets (speckit-*) exist,
        # then migrate/clean legacy dirs without risking user content loss.
        created = super().setup(
            project_root, manifest, parsed_options=parsed_options, **opts
        )

        if parsed_options.get("migrate_legacy", False):
            old_skills_dir = project_root / ".kimi" / "skills"
            # Validate both endpoints. base setup() already rejects a
            # destination that *escapes* the project root, but an in-tree
            # symlinked ``.kimi-code``/``.kimi-code/skills`` (e.g. ``-> .``)
            # would still misdirect the move; ``_is_safe_legacy_dir`` rejects
            # any symlinked component, giving the destination the same
            # protection as the source.
            if _is_safe_legacy_dir(old_skills_dir, project_root) and (
                _is_safe_legacy_dir(new_skills_dir, project_root)
            ):
                _migrate_legacy_kimi_skills_dir(old_skills_dir, new_skills_dir)
            # Mirror upsert/remove_context_section: a disabled agent-context
            # extension is a full opt-out, so skip the KIMI.md → AGENTS.md
            # migration entirely and leave both files untouched.
            if self._agent_context_extension_enabled(project_root):
                marker_start, marker_end = self._resolve_context_markers(project_root)
                _migrate_legacy_kimi_context_file(
                    project_root, marker_start=marker_start, marker_end=marker_end
                )

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


def _has_symlinked_component(path: Path, project_root: Path) -> bool:
    """Return ``True`` when *path* escapes *project_root* or any component is a symlink.

    Walks the components strictly between *project_root* and *path*
    (including the final one) and reports whether any of them is a symlink.
    Components that do not exist yet are not symlinks, so this safely handles
    a not-yet-created destination. *project_root* itself is trusted and never
    checked. A *path* outside *project_root* is treated as unsafe.
    """
    try:
        relative = path.relative_to(project_root)
    except ValueError:
        return True
    current = project_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _is_safe_legacy_dir(path: Path, project_root: Path) -> bool:
    """Return ``True`` when *path* is a real directory safely inside *project_root*.

    Legacy migration and cleanup ``shutil.move()`` and ``shutil.rmtree()``
    directories, so a symlinked ``.kimi``/``.kimi/skills`` (or one reached
    through a symlinked parent) must never be followed: doing so could
    relocate or delete content living outside the project tree — or operate
    on an unrelated in-tree directory (e.g. ``.kimi -> .`` makes
    ``.kimi/skills`` resolve to ``./skills``).

    Checking only the fully-resolved path is insufficient, because a symlink
    pointing elsewhere *inside* the project still resolves to a location under
    *project_root*. We therefore reject the path when it is not a directory,
    when any component between *project_root* and *path* is a symlink
    (including the final component), or when the resolved path escapes the
    resolved *project_root*.
    """
    if not path.is_dir():
        return False

    # Reject if any path component below project_root is a symlink (or the
    # path escapes project_root). We trust project_root itself, so only
    # components strictly under it are checked.
    if _has_symlinked_component(path, project_root):
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
        legacy_skill = legacy_dir / "SKILL.md"
        # Treat a symlinked SKILL.md as invalid: later read_bytes() would
        # otherwise follow it and read content from outside the project.
        if legacy_skill.is_symlink() or not legacy_skill.is_file():
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

        # Target exists — only remove legacy if SKILL.md is identical.
        # Skip when the target dir or its SKILL.md is a symlink (or the dir is
        # not a real directory) so the byte comparison never follows a link
        # outside the project. (legacy_skill is already guaranteed to be a real
        # file by the guard above.)
        if target_dir.is_symlink() or not target_dir.is_dir():
            continue
        target_skill = target_dir / "SKILL.md"
        if target_skill.is_symlink() or not target_skill.is_file():
            continue
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
        suffix = legacy_name[len("speckit.") :]
        if suffix:
            return f"speckit-{suffix.replace('.', '-')}"
    return ""


def _is_speckit_generated_skill(skill_dir: Path) -> bool:
    """Return True when *skill_dir* contains a Speckit-generated SKILL.md.

    Uses the ``metadata.author`` and ``metadata.source`` fields written by
    ``SkillsIntegration.setup()`` to avoid deleting user-authored skills.
    """
    skill_file = skill_dir / "SKILL.md"
    # A symlinked SKILL.md is never treated as Speckit-generated, so teardown
    # cleanup never follows it to read frontmatter from outside the project.
    if skill_file.is_symlink() or not skill_file.is_file():
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
    return (
        author == "github-spec-kit"
        and isinstance(source, str)
        and source.startswith("templates/commands/")
    )


def _migrate_legacy_kimi_context_file(
    project_root: Path,
    *,
    marker_start: str = IntegrationBase.CONTEXT_MARKER_START,
    marker_end: str = IntegrationBase.CONTEXT_MARKER_END,
) -> bool:
    """Migrate user content from legacy ``KIMI.md`` to ``AGENTS.md``.

    The Speckit managed section is stripped from ``KIMI.md`` before the
    remaining content is appended to ``AGENTS.md``. The legacy file is
    deleted if it becomes empty. Returns ``True`` if ``KIMI.md`` was
    migrated, ``False`` when the migration is skipped.

    The migration is skipped (leaving ``KIMI.md`` untouched) in any of these
    cases, so a best-effort legacy cleanup never aborts ``setup()`` or
    corrupts ``AGENTS.md``:

    - ``KIMI.md`` is a symlink, missing, or unreadable (its target could be
      read from outside the project, or it may not be valid UTF-8).
    - ``AGENTS.md`` is a symlink (it could redirect the write to a file
      outside the project root), exists as a non-file (e.g. a directory),
      or is unreadable/unwritable.
    - ``KIMI.md`` has a corrupted managed section — only one marker is
      present, or the end marker precedes the start. Stripping is only done
      when both markers are present and well-ordered, so a partial managed
      block is never copied into ``AGENTS.md``; the user repairs it manually.
    """
    legacy_path = project_root / "KIMI.md"
    if legacy_path.is_symlink() or not legacy_path.is_file():
        return False

    target_path = project_root / "AGENTS.md"
    # Never follow a symlinked target, and never treat an existing non-file
    # (e.g. a directory) as a writable context file.
    if target_path.is_symlink() or (target_path.exists() and not target_path.is_file()):
        return False

    try:
        content = legacy_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return False

    marker_pairs = [(marker_start, marker_end)]
    default_pair = (
        IntegrationBase.CONTEXT_MARKER_START,
        IntegrationBase.CONTEXT_MARKER_END,
    )
    if default_pair not in marker_pairs:
        marker_pairs.append(default_pair)

    start_idx = -1
    end_idx = -1
    has_start = False
    has_end = False
    for s, e in marker_pairs:
        s_idx = content.find(s)
        e_idx = content.find(e, s_idx if s_idx != -1 else 0)
        has_s = s_idx != -1
        has_e = e_idx != -1
        if not has_s and not has_e:
            continue
        # Refuse to migrate a corrupted managed section: exactly one marker, or
        # an end marker that does not follow the start.
        if has_s != has_e or e_idx <= s_idx:
            return False
        marker_start, marker_end = s, e
        start_idx, end_idx = s_idx, e_idx
        has_start = True
        has_end = True
        break
    if has_start and has_end:
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

    try:
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
    except (OSError, UnicodeDecodeError):
        return False

    legacy_path.unlink()
    return True


def _migrate_legacy_kimi_dotted_skills(skills_dir: Path) -> tuple[int, int]:
    """Compatibility shim — migrate legacy dotted skill dirs in place.

    .. deprecated::
        Kept for direct callers/tests. New code should call
        ``_migrate_legacy_kimi_skills_dir`` directly.

    Delegates to ``_migrate_legacy_kimi_skills_dir`` with *skills_dir* as both
    source and destination, so it processes every ``speckit-*`` and
    ``speckit.*`` entry under *skills_dir*. Because the two paths are
    identical, the same-path short-circuit there skips any directory whose
    target resolves to itself; in practice this renames dotted
    ``speckit.xxx`` dirs to hyphenated ``speckit-xxx`` in place and never
    moves content outside *skills_dir*.

    Returns ``(migrated_count, removed_count)``.
    """
    return _migrate_legacy_kimi_skills_dir(skills_dir, skills_dir)
