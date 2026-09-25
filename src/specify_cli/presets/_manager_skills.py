"""Agent skill registration and safe reconciliation for installed presets."""

import copy
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Union

if TYPE_CHECKING:
    from ..agents import CommandRegistrar


from .._init_options import is_ai_skills_enabled
from .._invocation_style import get_invocation_prefix
from .._utils import dump_frontmatter
from ..integrations.base import IntegrationBase
from ._manager_commands import _substitute_core_template
from ._manifest import PresetManifest, PresetValidationError
from ._resolver import PresetResolver


class _PresetSkillMethods:
    """Skill artifact methods shared through PresetManager's lifecycle state."""

    class _FilteredManifest:
        """Wrapper that exposes only selected command templates from a manifest.

        Used by _reconcile_skills to avoid overwriting skills for commands
        that aren't being reconciled.
        """

        def __init__(self, manifest: "PresetManifest", cmd_names: set):
            self._manifest = manifest
            self._cmd_names = cmd_names

        def __getattr__(self, name: str):
            return getattr(self._manifest, name)

        @property
        def templates(self) -> List[Dict[str, Any]]:
            return [
                t for t in self._manifest.templates
                if t.get("name") in self._cmd_names
            ]

    def _merge_pack_registered_skills(
        self, pack_id: str, written: Optional[Dict[str, List[str]]]
    ) -> None:
        """Merge actually-written agent skill registrations into a preset's metadata.

        Mirrors :meth:`_merge_pack_registered_commands` for the skills
        side: ``_reconcile_skills`` can render a preset's SKILL.md content
        into an agent directory the preset never wrote to before — most
        notably a historical (currently inactive) agent restored via
        ``extra_skills_dirs`` when a higher-priority preset is removed. If
        that write isn't reflected back into the winning preset's own
        ``registered_skills``, a later removal of this same preset only
        cleans up the agents it already knew about, orphaning the skill
        directory reconciliation just wrote to on its behalf (#2948).

        Args:
            pack_id: The preset whose metadata should be updated.
            written: ``{agent_name: [skill_name, ...]}`` actually written
                by the ``_register_skills`` call just made. A falsy value
                is a no-op.
        """
        if not written:
            return
        metadata = self.registry.get(pack_id)
        if metadata is None:
            return  # pack_id no longer installed (e.g. removed mid-loop)
        raw_existing_skills = metadata.get("registered_skills")
        if isinstance(raw_existing_skills, list) and raw_existing_skills:
            # Legacy flat-list value: infer real per-agent ownership from
            # on-disk provenance rather than guessing (#2948).
            fallback_agent = next(iter(written)) if written else None
            existing_skills = self._infer_legacy_skill_provenance(
                [n for n in raw_existing_skills if isinstance(n, str)],
                pack_id,
                fallback_agent=fallback_agent,
            )
        else:
            existing_skills = self._normalize_registered_skills(raw_existing_skills)
        merged_skills = copy.deepcopy(existing_skills)
        changed = (
            isinstance(raw_existing_skills, list) and bool(raw_existing_skills)
        )
        for agent_name, skill_names in written.items():
            if not skill_names:
                continue
            existing_names = merged_skills.get(agent_name, [])
            new_names = [n for n in skill_names if n not in existing_names]
            if new_names:
                merged_skills[agent_name] = existing_names + new_names
                changed = True
        if changed:
            self.registry.update(pack_id, {"registered_skills": merged_skills})

    def _reconcile_skills(
        self,
        command_names: List[str],
        extra_skills_dirs: Optional[
            Dict[Path, tuple[Optional[str], List[str]]]
        ] = None,
        target_agent: Optional[str] = None,
    ) -> Set[str]:
        """Re-register skills for commands whose winning layer changed.

        After a preset is removed, finds the next preset in the priority
        stack that provides each command and re-runs skill registration
        for that preset so SKILL.md files reflect the current winner.

        Args:
            command_names: List of command names to reconcile skills for
            extra_skills_dirs: Additional
                ``{skills_dir: (renderer_agent, managed_skill_names)}``
                entries restored by ``_unregister_skills``. Reconciliation
                is limited to the names actually managed in each directory.
            target_agent: If set, report only command names written for this
                agent. Other callers receive the union of all written names.

        Returns:
            Command names whose skill output was successfully written.
        """
        if not command_names:
            return set()

        # Preset-owned command names are not filtered by the
        # ``speckit.<ns>.<cmd>`` shape here either: a self-contained preset
        # command renders its skill whether or not a like-named extension is
        # installed. The per-name loop below skips anything that doesn't
        # resolve to a managed skill directory.
        resolver = PresetResolver(self.project_root)
        active_skills_dir = self._get_skills_dir()

        from .. import load_init_options

        init_opts = load_init_options(self.project_root)
        active_ai = init_opts.get("ai") if isinstance(init_opts, dict) else None
        if not isinstance(active_ai, str) or not active_ai:
            active_ai = None

        # Cache registry once to avoid repeated filesystem reads
        presets_by_priority = list(self.registry.list_by_priority())

        # Group command names by winning preset to batch _register_skills calls
        # while only registering skills for the specific commands being
        # reconciled. This resolution (which preset/content wins) is
        # directory-independent, so it's computed once and then applied to
        # every affected directory below.
        preset_cmds: Dict[str, List[str]] = {}
        non_preset_skills: List[tuple] = []
        managed_skill_names: set = set()
        reconciled_skill_commands: set[str] = set()

        for cmd_name in command_names:
            layers = resolver.collect_all_layers(cmd_name, "command")
            if not layers:
                continue

            skill_name, legacy_skill_name = self._skill_names_for_command(
                cmd_name
            )
            candidate_skill_names = {skill_name, legacy_skill_name}
            # Track whether any preset previously registered this skill
            # (i.e., it was actively managed), so a not-yet-existing skill
            # dir can be re-created per affected directory below.
            for _pid, meta in presets_by_priority:
                if not isinstance(meta, dict):
                    continue
                recorded = meta.get("registered_skills", [])
                if isinstance(recorded, dict):
                    recorded_names = {
                        name
                        for names in recorded.values()
                        if isinstance(names, list)
                        for name in names
                    }
                elif isinstance(recorded, list):
                    recorded_names = set(recorded)
                else:
                    recorded_names = set()
                recorded_candidates = (
                    candidate_skill_names & recorded_names
                )
                if recorded_candidates:
                    managed_skill_names.update(recorded_candidates)

            top_path = layers[0]["path"]
            # Find the preset that owns the winning layer
            found_preset = False
            for pack_id, _meta in presets_by_priority:
                pack_dir = self.presets_dir / pack_id
                if top_path.is_relative_to(pack_dir):
                    preset_cmds.setdefault(pack_id, []).append(cmd_name)
                    found_preset = True
                    break
            if not found_preset:
                # Winner is a non-preset source (core/extension/override).
                # Track the winning layer path for skill restoration.
                non_preset_skills.append((skill_name, cmd_name, layers[0]))

        core_ext_skills = [s for s in non_preset_skills if s[2]["source"] != "project override"]
        override_skills = [s for s in non_preset_skills if s[2]["source"] == "project override"]

        def apply_to_dir(
            skills_dir: Path,
            dir_agent: Optional[str],
            *,
            is_active: bool,
            managed_names: Optional[Set[str]] = None,
        ) -> None:
            dir_managed_names = (
                managed_skill_names if managed_names is None else managed_names
            )
            # Restore skills for commands whose winner is non-preset.
            # _unregister_skills_in_dir can rmtree the skill dir, so
            # overrides must be handled directly (create dir + write)
            # without that call.
            dir_core_ext_names = [
                candidate
                for _skill_name, cmd_name, _top_layer in core_ext_skills
                for candidate in self._skill_names_for_command(cmd_name)
                if candidate in dir_managed_names
            ]
            if dir_core_ext_names:
                self._unregister_skills_in_dir(
                    dir_core_ext_names,
                    skills_dir,
                    dir_agent,
                    restore_from_bundled_core=True,
                )

            for _skill_name, cmd_name, top_layer in override_skills:
                target_skill_names = [
                    name
                    for name in self._skill_names_for_command(cmd_name)
                    if name in dir_managed_names
                ]
                if not target_skill_names:
                    continue
                try:
                    from .. import SKILL_DESCRIPTIONS
                    from ..agents import CommandRegistrar
                    from ..shared_infra import _write_shared_text
                    registrar = CommandRegistrar()
                    content = top_layer["path"].read_text(encoding="utf-8")
                    fm, body = registrar.parse_frontmatter(content)
                    short_name = cmd_name
                    if short_name.startswith("speckit."):
                        short_name = short_name[len("speckit."):]
                    desc = fm.get("description", "") or SKILL_DESCRIPTIONS.get(
                        short_name.replace(".", "-"),
                        f"Command: {short_name}",
                    )
                    selected_ai = dir_agent if isinstance(dir_agent, str) else ""
                    if selected_ai:
                        body = registrar.resolve_skill_placeholders(
                            selected_ai, fm, body, self.project_root
                        )
                        body = self._resolve_skill_command_refs(
                            body, registrar, selected_ai, self.project_root
                        )
                    from ..integrations import get_integration
                    integration = get_integration(selected_ai) if selected_ai else None
                    skill_title = self._skill_title_from_command(cmd_name)
                    wrote_override = False
                    for target_skill_name in target_skill_names:
                        skill_subdir = skills_dir / target_skill_name
                        # Same symlink guard as _register_skills's
                        # registration path (#2948).
                        if not self._validate_skill_subdir(
                            skill_subdir,
                            create=True,
                            skills_root=skills_dir,
                        ):
                            continue
                        fm_data = registrar.build_skill_frontmatter(
                            selected_ai,
                            target_skill_name,
                            desc,
                            f"override:{cmd_name}",
                        )
                        registrar.apply_argument_hint(
                            fm, fm_data, integration
                        )
                        fm_text = dump_frontmatter(fm_data)
                        skill_content = (
                            f"---\n{fm_text}\n---\n\n"
                            f"# Speckit {skill_title} Skill\n\n{body}\n"
                        )
                        if integration is not None and hasattr(
                            integration, "post_process_skill_content"
                        ):
                            skill_content = (
                                integration.post_process_skill_content(
                                    skill_content
                                )
                            )
                        _write_shared_text(
                            skills_dir,
                            skill_subdir / "SKILL.md",
                            skill_content,
                        )
                        wrote_override = True
                    if (
                        wrote_override
                        and (
                            target_agent is None
                            or dir_agent == target_agent
                        )
                    ):
                        reconciled_skill_commands.add(cmd_name)
                except Exception:
                    pass  # best-effort override skill restoration

            # Register skills only for the specific commands being
            # reconciled, not all commands in each winning preset's
            # manifest.
            for pack_id, cmds in preset_cmds.items():
                dir_cmds = [
                    cmd
                    for cmd in cmds
                    if any(
                        name in dir_managed_names
                        for name in self._skill_names_for_command(cmd)
                    )
                ]
                if not dir_cmds:
                    continue
                pack_dir = self.presets_dir / pack_id
                manifest_path = pack_dir / "preset.yml"
                if not manifest_path.exists():
                    continue
                try:
                    manifest = PresetManifest(manifest_path)
                except PresetValidationError:
                    continue
                cmds_set = set(dir_cmds)
                filtered_manifest = self._FilteredManifest(manifest, cmds_set)
                # Not dead code: _register_skills only *overwrites* skill
                # subdirectories that already exist (plus brand-new ones for
                # the active ai_skills agent). For a restore into a
                # historical directory, _unregister_skills has just deleted
                # the retiring preset's subdirectory, so pre-create the
                # tracked (dir_managed_names) subdirectories here — under
                # the same symlink guard — or the surviving preset's
                # override would be silently skipped (#2948).
                for cmd_name in dir_cmds:
                    for skill_name in self._skill_names_for_command(cmd_name):
                        if skill_name not in dir_managed_names:
                            continue
                        skill_subdir = skills_dir / skill_name
                        if not self._validate_skill_subdir(
                            skill_subdir,
                            create=True,
                            skills_root=skills_dir,
                        ):
                            continue
                if is_active:
                    # Preserve exact prior behaviour for the currently
                    # active directory (including the ability to create
                    # brand-new skill subdirectories when ai_skills is on).
                    written = self._register_skills(filtered_manifest, pack_dir)
                else:
                    written = self._register_skills(
                        filtered_manifest, pack_dir,
                        target_dir=skills_dir, target_agent=dir_agent or "",
                    )
                if target_agent is None:
                    written_names = {
                        name
                        for names in written.values()
                        for name in names
                    }
                else:
                    written_names = set(written.get(target_agent, []))
                for cmd_name in dir_cmds:
                    if written_names.intersection(
                        self._skill_names_for_command(cmd_name)
                    ):
                        reconciled_skill_commands.add(cmd_name)
                # The winning preset may not have previously written to
                # this directory's agent (most notably a historical agent
                # reconciliation just restored content into via
                # extra_skills_dirs). If that write isn't merged back into
                # the preset's own registered_skills, its registry entry
                # silently lies about which directories it owns and a
                # later removal of this same preset orphans the directory
                # reconciliation just wrote to on its behalf (#2948).
                self._merge_pack_registered_skills(pack_id, written)

        extra_dirs = extra_skills_dirs or {}
        if active_skills_dir:
            active_provenance = extra_dirs.get(active_skills_dir)
            if extra_skills_dirs is None or active_provenance:
                apply_to_dir(
                    active_skills_dir,
                    active_ai,
                    is_active=True,
                    managed_names=(
                        set(active_provenance[1])
                        if active_provenance
                        else None
                    ),
                )

        for extra_dir, (extra_agent, extra_names) in extra_dirs.items():
            if extra_dir == active_skills_dir:
                continue  # already reconciled above as the active directory
            apply_to_dir(
                extra_dir,
                extra_agent,
                is_active=False,
                managed_names=set(extra_names),
            )

        return reconciled_skill_commands

    def _resolve_agent_skills_dir(self, agent_name: str) -> Path:
        """Resolve the real skill output directory for an integration."""
        from .. import _get_skills_dir as _project_skills_dir
        from ..agents import CommandRegistrar

        registrar = CommandRegistrar()
        agent_config = registrar.AGENT_CONFIGS.get(agent_name)
        if agent_config and agent_config.get("extension") == "/SKILL.md":
            return registrar._resolve_agent_dir(
                agent_name, agent_config, self.project_root
            )
        return _project_skills_dir(self.project_root, agent_name)

    def _skills_validation_root(self, skills_dir: Path) -> Optional[Path]:
        """Return the trusted root containing a project or user skill dir."""
        for root in (self.project_root, Path.home()):
            if skills_dir.is_relative_to(root):
                return root
        return None

    def _get_skills_dir(self) -> Optional[Path]:
        """Return the active skills directory for preset skill overrides.

        Uses :func:`resolve_active_skills_dir` for activation/detection,
        then resolves native skill agents through the registrar's output
        directory so integrations such as Hermes write to their global
        skills path rather than their project-local detection marker.

        Returns ``None`` (instead of raising) when the directory cannot
        be created due to symlink, containment, or permission issues so
        that callers can fall back gracefully.
        """
        from .. import (
            _print_cli_warning,
            load_init_options,
            resolve_active_skills_dir,
        )
        from ..shared_infra import _ensure_safe_shared_directory
        try:
            skills_dir = resolve_active_skills_dir(self.project_root)
        except (ValueError, OSError) as exc:
            _print_cli_warning(
                "resolve", "skills directory", None, exc,
                continuing="Continuing without skill registration.",
            )
            return None
        if skills_dir is None:
            return None

        opts = load_init_options(self.project_root)
        selected_ai = opts.get("ai") if isinstance(opts, dict) else None
        if not isinstance(selected_ai, str) or not selected_ai:
            return skills_dir

        agent_skills_dir = self._resolve_agent_skills_dir(selected_ai)
        if agent_skills_dir == skills_dir:
            return skills_dir

        validation_root = self._skills_validation_root(agent_skills_dir)
        if validation_root is None:
            _print_cli_warning(
                "resolve",
                "skills directory",
                str(agent_skills_dir),
                ValueError("skills directory is outside trusted roots"),
                continuing="Continuing without skill registration.",
            )
            return None
        try:
            _ensure_safe_shared_directory(
                validation_root,
                agent_skills_dir,
                context="preset skills directory",
            )
        except (ValueError, OSError) as exc:
            _print_cli_warning(
                "resolve", "skills directory", str(agent_skills_dir), exc,
                continuing="Continuing without skill registration.",
            )
            return None
        return agent_skills_dir

    @staticmethod
    def _skill_names_for_command(cmd_name: str) -> tuple[str, str]:
        """Return the modern and legacy skill directory names for a command."""
        raw_short_name = cmd_name
        if raw_short_name.startswith("speckit."):
            raw_short_name = raw_short_name[len("speckit."):]

        modern_skill_name = f"speckit-{raw_short_name.replace('.', '-')}"
        legacy_skill_name = f"speckit.{raw_short_name}"
        return modern_skill_name, legacy_skill_name

    @staticmethod
    def _skill_title_from_command(cmd_name: str) -> str:
        """Return a human-friendly title for a skill command name."""
        title_name = cmd_name
        if title_name.startswith("speckit."):
            title_name = title_name[len("speckit."):]
        return title_name.replace(".", " ").replace("-", " ").title()

    @staticmethod
    def _resolve_skill_command_refs(
        body: str,
        registrar: "CommandRegistrar",
        selected_ai: str,
        project_root: "Path | None" = None,
    ) -> str:
        """Render ``__SPECKIT_COMMAND_*__`` tokens in a skill body as invocations.

        Looks up the agent's invoke separator and rewrites each
        ``__SPECKIT_COMMAND_<NAME>__`` placeholder into the matching
        agent-native invocation -- ``/speckit-<cmd>`` or ``$speckit-<cmd>`` for
        a ``-`` separator, ``/speckit.<cmd>`` for ``.``, or
        ``/skill:speckit-<cmd>`` for skill-colon agents (e.g. Kimi) -- the
        same rendering the command layer applies via
        ``CommandRegistrar.register_commands()``.

        For dual-layout agents (e.g. Bob) the separator depends on the
        project's persisted skills state, so -- when *project_root* is provided
        -- the separator is resolved from the integration via
        ``invoke_separator_for_mode`` rather than the single static
        ``AGENT_CONFIGS`` value.
        """
        separator = None
        if project_root is not None and isinstance(selected_ai, str):
            try:
                from .. import load_init_options
                from ..integrations import get_integration

                integration = get_integration(selected_ai)
                if integration is not None:
                    separator = integration.invoke_separator_for_mode(
                        is_ai_skills_enabled(load_init_options(project_root))
                    )
            except Exception:
                separator = None
        if separator is None:
            separator = registrar.AGENT_CONFIGS.get(selected_ai, {}).get(
                "invoke_separator", "."
            )
        prefix = get_invocation_prefix(selected_ai, separator == "-")
        return IntegrationBase.resolve_command_refs(body, separator, prefix)

    def _build_extension_skill_restore_index(self) -> Dict[str, Dict[str, Any]]:
        """Index extension-backed skill restore data by skill directory name."""
        from ..extensions import ExtensionManifest, ValidationError

        resolver = PresetResolver(self.project_root)
        extensions_dir = self.project_root / ".specify" / "extensions"
        restore_index: Dict[str, Dict[str, Any]] = {}

        for _priority, ext_id, _metadata in resolver._get_all_extensions_by_priority():
            ext_dir = extensions_dir / ext_id
            manifest_path = ext_dir / "extension.yml"
            if not manifest_path.is_file():
                continue

            try:
                manifest = ExtensionManifest(manifest_path)
            except (ValidationError, TypeError, AttributeError):
                continue

            ext_root = ext_dir.resolve()
            for cmd_info in manifest.commands:
                cmd_name = cmd_info.get("name")
                cmd_file_rel = cmd_info.get("file")
                if not isinstance(cmd_name, str) or not isinstance(cmd_file_rel, str):
                    continue

                cmd_path = Path(cmd_file_rel)
                if cmd_path.is_absolute():
                    continue

                try:
                    source_file = (ext_root / cmd_path).resolve()
                    source_file.relative_to(ext_root)
                except (OSError, ValueError):
                    continue

                if not source_file.is_file():
                    continue

                restore_info = {
                    "command_name": cmd_name,
                    "source_file": source_file,
                    "source": f"extension:{manifest.id}",
                    "author": manifest.data["extension"].get("author"),
                    "extension_id": manifest.id,
                    "extension_dir": ext_root,
                }
                modern_skill_name, legacy_skill_name = self._skill_names_for_command(cmd_name)
                restore_index.setdefault(modern_skill_name, restore_info)
                if legacy_skill_name != modern_skill_name:
                    restore_index.setdefault(legacy_skill_name, restore_info)

        return restore_index

    def _register_skills(
        self,
        manifest: "PresetManifest",
        preset_dir: Path,
        *,
        target_dir: Optional[Path] = None,
        target_agent: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        """Generate SKILL.md files for preset command overrides.

        For every command template in the preset, checks whether a
        corresponding skill already exists in any detected skills
        directory.  If so, the skill is overwritten with content derived
        from the preset's command file.  This ensures that presets that
        override commands also propagate to the agentskills.io skill
        layer when skills mode was used during project initialisation.

        Args:
            manifest: Preset manifest.
            preset_dir: Installed preset directory.
            target_dir: Explicit skills directory to render into, instead
                of resolving the currently active one. Used by
                ``_reconcile_skills`` to restore a surviving preset's
                override into a historical (currently inactive) agent's
                directory that removal of a higher-priority preset just
                reverted (#2948).
            target_agent: Explicit agent name to render for, paired with
                ``target_dir``. When set, skills are only ever restored
                into already-tracked directories/names — brand-new skill
                subdirectories are never created for a non-active,
                explicitly targeted directory (that creation path is only
                meaningful for the currently active agent).

        Returns:
            ``{agent_name: [skill_name, ...]}`` for the single active
            agent skills were written for (empty if none were written),
            matching the shape ``registered_commands`` already uses so the
            two can be tracked/restored consistently (#2948).
        """
        command_templates = [
            t for t in manifest.templates if t.get("type") == "command"
        ]
        if not command_templates:
            return {}

        # Preset command templates are self-contained and render as skills
        # regardless of whether a like-named extension is installed — the same
        # rule _register_commands() uses. No ``speckit.<ns>.<cmd>`` name-shape
        # filtering; the per-command loop below skips anything without a target
        # skill directory.
        skills_dir = target_dir if target_dir is not None else self._get_skills_dir()
        if not skills_dir:
            return {}

        resolver = PresetResolver(self.project_root)

        from .. import SKILL_DESCRIPTIONS, load_init_options
        from ..agents import CommandRegistrar
        from ..integrations import get_integration
        from ..shared_infra import _write_shared_text

        init_opts = load_init_options(self.project_root)
        if not isinstance(init_opts, dict):
            init_opts = {}
        selected_ai = target_agent if target_agent is not None else init_opts.get("ai")
        if not isinstance(selected_ai, str) or not selected_ai:
            return {}
        # A target_dir/target_agent call reconciles an explicitly-known,
        # already-tracked directory (see _reconcile_skills) rather than the
        # currently active agent, so ai_skills_enabled must not be derived
        # from the *current* project-wide toggle for that other agent — it
        # only controls whether brand-new skill subdirectories may be
        # created below, which is only meaningful for the active agent.
        ai_skills_enabled = target_agent is None and is_ai_skills_enabled(init_opts)
        registrar = CommandRegistrar()
        integration = get_integration(selected_ai)
        agent_config = registrar.AGENT_CONFIGS.get(selected_ai, {})
        # Native skill agents (e.g. codex/kimi/agy/trae) materialize brand-new
        # preset skills in _register_commands() because their detected agent
        # directory is already the skills directory. This flag is only for
        # command-backed agents that also mirror commands into skills.
        create_missing_skills = ai_skills_enabled and agent_config.get("extension") != "/SKILL.md"

        written: List[str] = []

        for cmd_tmpl in command_templates:
            cmd_name = cmd_tmpl["name"]
            cmd_file_rel = cmd_tmpl["file"]
            source_file = preset_dir / cmd_file_rel
            if not source_file.exists():
                continue

            # Use composed content if available (written by _register_commands
            # for commands with non-replace strategies), otherwise the original.
            composed_file = preset_dir / ".composed" / f"{cmd_name}.md"
            if composed_file.exists():
                source_file = composed_file

            # Derive the short command name (e.g. "specify" from "speckit.specify")
            raw_short_name = cmd_name
            if raw_short_name.startswith("speckit."):
                raw_short_name = raw_short_name[len("speckit."):]
            short_name = raw_short_name.replace(".", "-")
            skill_name, legacy_skill_name = self._skill_names_for_command(cmd_name)
            skill_title = self._skill_title_from_command(cmd_name)

            # Only overwrite skills that already exist under skills_dir,
            # including Kimi native skills when ai_skills is false.
            # If both modern and legacy directories exist, update both.
            target_skill_names: List[str] = []
            if (skills_dir / skill_name).is_dir():
                target_skill_names.append(skill_name)
            if legacy_skill_name != skill_name and (skills_dir / legacy_skill_name).is_dir():
                target_skill_names.append(legacy_skill_name)
            if not target_skill_names and create_missing_skills:
                missing_skill_dir = skills_dir / skill_name
                if not missing_skill_dir.exists():
                    target_skill_names.append(skill_name)
            if not target_skill_names:
                continue

            # Parse the command file
            content = source_file.read_text(encoding="utf-8")
            frontmatter, body = registrar.parse_frontmatter(content)

            # A composition-strategy command (wrap/prepend/append) needs a
            # base layer to compose onto. When _register_commands produced no
            # composed file for it and the stack still has no base
            # (resolve_content is None) — e.g. the command it wraps comes from
            # an extension that isn't installed — rendering the raw preset
            # fragment as a skill would emit broken output: a literal
            # {CORE_TEMPLATE} for wrap, or only the preset's own fragment for
            # prepend/append. Skip it here too so command mode and skills mode
            # agree (mirrors _register_commands, which skips the same command).
            # _register_commands already warned for this command in the same
            # pass, so the skip is silent here to avoid a duplicate warning.
            effective_strategy = (
                cmd_tmpl.get("strategy")
                or frontmatter.get("strategy")
                or "replace"
            )
            if (
                effective_strategy != "replace"
                and not composed_file.exists()
                and resolver.resolve_content(cmd_name, "command") is None
            ):
                continue

            if frontmatter.get("strategy") == "wrap":
                body, core_frontmatter = _substitute_core_template(body, cmd_name, self.project_root, registrar)
                frontmatter = dict(frontmatter)
                for key in ("scripts", "agent_scripts", "argument-hint"):
                    if key not in frontmatter and key in core_frontmatter:
                        frontmatter[key] = core_frontmatter[key]

            original_desc = frontmatter.get("description", "")
            enhanced_desc = original_desc or SKILL_DESCRIPTIONS.get(
                short_name,
                f"Spec-kit workflow command: {short_name}",
            )
            frontmatter = dict(frontmatter)
            frontmatter["description"] = enhanced_desc
            body = registrar.resolve_skill_placeholders(
                selected_ai, frontmatter, body, self.project_root
            )
            body = self._resolve_skill_command_refs(body, registrar, selected_ai, self.project_root)

            for target_skill_name in target_skill_names:
                skill_subdir = skills_dir / target_skill_name
                if skill_subdir.exists() and not skill_subdir.is_dir():
                    continue
                # Validate (and create, if missing) the skill's own
                # subdirectory under the same symlink guard as its parent —
                # is_dir() above follows symlinks, so a symlinked subdir
                # with a real parent would otherwise slip through and have
                # SKILL.md written through it to an arbitrary location (#2948).
                if not self._validate_skill_subdir(
                    skill_subdir, create=True, skills_root=skills_dir
                ):
                    continue
                frontmatter_data = registrar.build_skill_frontmatter(
                    selected_ai,
                    target_skill_name,
                    enhanced_desc,
                    f"preset:{manifest.id}",
                )
                registrar.apply_argument_hint(frontmatter, frontmatter_data, integration)
                frontmatter_text = dump_frontmatter(frontmatter_data)
                skill_content = (
                    f"---\n"
                    f"{frontmatter_text}\n"
                    f"---\n\n"
                    f"# Speckit {skill_title} Skill\n\n"
                    f"{body}\n"
                )
                if integration is not None and hasattr(integration, "post_process_skill_content"):
                    skill_content = integration.post_process_skill_content(
                        skill_content
                    )

                skill_file = skill_subdir / "SKILL.md"
                _write_shared_text(
                    skills_dir, skill_file, skill_content
                )
                written.append(target_skill_name)
                self._merge_pack_registered_skills(
                    manifest.id, {selected_ai: [target_skill_name]}
                )

        return {selected_ai: written} if written else {}

    def _infer_legacy_skill_provenance(
        self, skill_names: List[str], pack_id: str, fallback_agent: str
    ) -> Dict[str, List[str]]:
        """Infer per-agent ownership of a legacy flat-list ``registered_skills`` value.

        Pre-#2948 registries recorded ``registered_skills`` as a flat list
        with no record of which agent directory each name was actually
        written under. Blindly attributing every name to ``fallback_agent``
        (the agent currently being processed) loses the real writer whenever
        the *first* operation after upgrading is a direct switch to a
        *different* agent — e.g. a legacy Copilot override (written while
        Copilot was active with ``ai_skills`` enabled) followed directly by
        ``integration use claude``, with no intervening rescaffold for
        Copilot — permanently orphaning Copilot's override on later
        removal.

        Every project-local configured integration's skills directory is probed (via
        the same safe, symlink-validated helpers used for
        restore/removal), not only agents whose registrar config is
        statically ``/SKILL.md``-only: a command-backed agent (e.g.
        Copilot, whose command extension is ``.agent.md``) renders its
        preset overrides as ``SKILL.md`` files exactly like a native
        skill-only agent whenever it was the active agent with
        ``ai_skills`` enabled, so excluding it would miss real,
        preset-owned provenance and misattribute it to whichever agent
        happens to be processed first. Each directory is probed for a
        ``SKILL.md`` whose frontmatter records this exact preset as the
        owner (``metadata.source == "preset:<pack_id>"``, the same marker
        :meth:`_register_skills` writes) — this marker check is what keeps
        the broadened probe from falsely attributing ownership to an
        agent's directory that never actually held this preset's override
        (e.g. a command-mode agent that never rendered skills, or an
        unrelated skill of the same name). A name can legitimately be
        found under more than one agent's directory — the preset may have
        been active while the user switched between several agents before
        provenance tracking existed — so every matching agent is recorded,
        not just the first. Names that can't be matched to any directory
        (e.g. the file was deleted out of band) fall back to
        ``fallback_agent``, preserving the previous best-effort behaviour
        for the unrecoverable case.
        """
        from ..agents import CommandRegistrar

        registrar = CommandRegistrar()
        candidate_agents = sorted(registrar.AGENT_CONFIGS)

        # Multiple agent names can resolve to the same physical directory
        # (e.g. agy/amp/codex/zed all use .agents/skills); group by
        # directory so each is probed once and attributed to a single
        # deterministic canonical agent name, matching the tie-break
        # already used by _unregister_skills's directory grouping. Deliberately
        # keep the unresolved path (matching what _safe_skills_dir_for_agent
        # already validated) rather than calling .resolve() here: on macOS
        # /var is itself a symlink to /private/var, so resolving would make
        # this path diverge from self.project_root's own resolution state
        # and make every subsequent containment check in
        # _validate_skill_subdir() spuriously fail.
        dir_to_agents: Dict[Path, List[str]] = {}
        for agent_name in candidate_agents:
            skills_dir = self._safe_skills_dir_for_agent(agent_name)
            if skills_dir is None:
                continue
            # Only project-local skills directories are eligible: the
            # legacy provenance markers don't record which project owns a
            # skill under a home directory, so deletion stays restricted
            # to the project root. Revisit if provenance ever records the
            # owning project.
            if not Path(os.path.abspath(skills_dir)).is_relative_to(
                Path(os.path.abspath(self.project_root))
            ):
                continue
            dir_to_agents.setdefault(skills_dir, []).append(agent_name)

        marker = f"preset:{pack_id}"
        # Filter unsafe names once, up front, rather than only inside the
        # matching loop: any name skipped there would otherwise still
        # land in "unmatched" below and get blindly attributed to
        # fallback_agent anyway, defeating the guard entirely (#2948).
        safe_skill_names = [
            name for name in skill_names if self._is_safe_registry_skill_name(name)
        ]
        inferred: Dict[str, List[str]] = {}
        matched_names: set = set()
        for resolved_dir, agents in dir_to_agents.items():
            canonical_agent = fallback_agent if fallback_agent in agents else sorted(agents)[0]
            for name in safe_skill_names:
                skill_subdir = resolved_dir / name
                if not self._validate_skill_subdir(
                    skill_subdir, create=False, skills_root=resolved_dir
                ):
                    continue
                skill_file = skill_subdir / "SKILL.md"
                if not skill_file.is_file():
                    continue
                try:
                    content = skill_file.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                frontmatter, _ = registrar.parse_frontmatter(content)
                skill_metadata = frontmatter.get("metadata")
                source = (
                    skill_metadata.get("source")
                    if isinstance(skill_metadata, dict)
                    else None
                )
                if source == marker:
                    inferred.setdefault(canonical_agent, []).append(name)
                    matched_names.add(name)

        unmatched = [name for name in safe_skill_names if name not in matched_names]
        if unmatched and fallback_agent:
            fallback_names = inferred.setdefault(fallback_agent, [])
            for name in unmatched:
                if name not in fallback_names:
                    fallback_names.append(name)

        return inferred

    @staticmethod
    def _normalize_registered_skills(
        value: Any, fallback_agent: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """Normalize a ``registered_skills`` registry value to per-agent form.

        The registry stores ``registered_skills`` as ``Dict[str, List[str]]``
        (agent name -> skill names actually written for that agent),
        mirroring ``registered_commands``. Older registries predate that
        provenance and stored a flat ``List[str]`` with no record of which
        agent directory the names were written under; since that can't be
        recovered, ``fallback_agent`` (when given) attributes the legacy
        list to the agent currently being processed so the format
        self-migrates on the next write. Without a fallback agent, legacy
        lists are dropped rather than guessed at.

        Callers that can identify the owning preset (i.e. have a
        ``pack_id``) should prefer :meth:`_infer_legacy_skill_provenance`
        for a legacy flat-list value instead, which probes on-disk
        provenance rather than assuming ``fallback_agent`` wrote every name.
        """
        if isinstance(value, dict):
            return {
                agent: list(names)
                for agent, names in value.items()
                if isinstance(agent, str) and isinstance(names, list)
            }
        if isinstance(value, list) and value and fallback_agent:
            return {fallback_agent: [n for n in value if isinstance(n, str)]}
        return {}

    def _safe_skills_dir_for_agent(self, agent_name: str) -> Optional[Path]:
        """Resolve ``agent_name``'s skills directory, validated for safety.

        Unlike :meth:`_get_skills_dir` (which resolves only the *currently
        active* integration via init-options), this resolves an arbitrary
        agent's directory from persisted provenance so a preset's skill
        registrations can be restored/cleaned up under an agent that isn't
        currently active. The candidate directory is validated through the
        project's shared symlink/containment guard before any file in it is
        touched; directories that don't exist or fail validation are
        skipped rather than raising.
        """
        from ..agents import CommandRegistrar
        from ..shared_infra import _ensure_safe_shared_directory

        if agent_name not in CommandRegistrar.AGENT_CONFIGS:
            return None
        skills_dir = self._resolve_agent_skills_dir(agent_name)
        validation_root = self._skills_validation_root(skills_dir)
        if validation_root is None:
            return None
        try:
            _ensure_safe_shared_directory(
                validation_root, skills_dir,
                create=False, context="preset skills directory",
            )
        except (ValueError, OSError):
            return None
        return skills_dir

    @staticmethod
    def _is_safe_registry_skill_name(name: Any) -> bool:
        """Validate a registry-provided skill name is a single safe path component.

        ``registered_skills`` entries are persisted registry data, not
        derived from the current preset manifest, so a corrupted or
        maliciously edited registry could contain an absolute path, a
        multi-segment path (containing ``/`` or ``\\``), or a traversal
        component (``"."``/``".."``) instead of a plain skill directory
        name. Any of these — if joined directly onto a skills directory —
        can escape the intended skill subtree while still resolving to a
        location inside the project root, which is enough to pass the
        parent-directory containment/symlink check alone (#2948). This
        centralizes the single boundary check every preset cleanup and
        provenance loop that consumes registry-provided skill names must
        apply before ever constructing a path from one.
        """
        if not isinstance(name, str) or not name:
            return False
        if name in (".", ".."):
            return False
        candidate = Path(name)
        if candidate.is_absolute():
            return False
        if len(candidate.parts) != 1:
            return False
        if candidate.name != name:
            return False
        return True

    def _validate_skill_subdir(
        self,
        skill_subdir: Path,
        *,
        create: bool,
        skills_root: Optional[Path] = None,
    ) -> bool:
        """Validate a single skill's subdirectory is symlink-free.

        Unlike :meth:`_safe_skills_dir_for_agent` (which only validates the
        *parent* skills directory), this validates the skill's own
        subdirectory — e.g. ``.claude/skills/speckit-specify`` — so a
        symlink planted at that level (with a safe parent) can't be used to
        write or delete through to a location outside the project. Shared by
        both the registration path (``create=True``, so a missing directory
        is created component-by-component under the same guard) and the
        restore/removal path (``create=False``, so a missing directory is
        left for the caller's own existence check to skip). Returns
        ``False`` rather than raising when the path escapes the project
        root or crosses a symlink. ``skills_root`` supplies the trusted
        agent output boundary for native global skill integrations such as
        Hermes; project-local callers default to ``self.project_root``.
        """
        from ..shared_infra import (
            _ensure_safe_shared_directory,
            _validate_safe_shared_directory,
        )

        validation_root = skills_root or self.project_root
        if validation_root.is_symlink():
            return False
        try:
            if create:
                _ensure_safe_shared_directory(
                    validation_root, skill_subdir,
                    create=True, context="preset skill directory",
                )
            else:
                _validate_safe_shared_directory(
                    validation_root, skill_subdir
                )
        except (ValueError, OSError):
            return False
        return True

    def _unregister_skills(
        self,
        registered_skills: Union[Dict[str, List[str]], List[str]],
        preset_dir: Union[Path, str],
        *,
        additional_owned_sources: Optional[Dict[str, str]] = None,
        restore_from_bundled_core: bool = False,
    ) -> Dict[Path, tuple[Optional[str], List[str]]]:
        """Restore original SKILL.md files after a preset is removed.

        For each skill that was overridden by the preset, attempts to
        regenerate the skill from the core command template.  If no core
        template exists, the skill directory is removed.

        Args:
            restore_from_bundled_core: When True, a missing project-local
                core template (the common case — ``specify init`` never
                populates ``.specify/templates/commands``) falls back to
                the bundled core_pack/repo-root templates so the skill is
                restored instead of deleted (#3928). Callers that are
                retiring a skill because its command now renders elsewhere
                (a command file superseding it) must leave this False so
                the skill is removed rather than resurrected with core
                content that would duplicate the winning command.

        ``registered_skills`` records exactly which agent directories this
        preset actually wrote to (see :meth:`_register_skills`), so removal
        restores precisely those directories rather than guessing at every
        skill-mode agent that happens to exist on disk. Each directory is
        re-resolved and safety-validated at removal time (see
        :meth:`_safe_skills_dir_for_agent`) since it may belong to an agent
        that isn't currently active.

        Args:
            registered_skills: Per-agent skill names written by the preset
                (``{agent_name: [skill_name, ...]}``), or a legacy flat
                ``List[str]`` from a registry written before this
                provenance tracking existed.
            preset_dir: The preset's installed directory (may already be deleted).
            additional_owned_sources: Generated non-preset source markers
                that this cleanup may also replace for specific skill names.

        Returns:
            ``{skills_dir: (renderer_agent, managed_skill_names)}`` for
            every directory and skill name actually restored or removed.
        """
        if not registered_skills:
            return {}

        pack_id = preset_dir if isinstance(preset_dir, str) else preset_dir.name

        if isinstance(registered_skills, dict):
            from .. import load_init_options

            init_opts = load_init_options(self.project_root)
            active_agent = init_opts.get("ai") if isinstance(init_opts, dict) else None
            if not isinstance(active_agent, str) or not active_agent:
                active_agent = None

            # Multiple integration keys can share the same physical
            # directory (e.g. agy/codex/zed all resolve to
            # ``.agents/skills``). Restoring that directory once per
            # recorded agent would have each pass's agent-specific
            # rendering (frontmatter, post-processing) overwrite the
            # previous one, with whichever agent is iterated *last* silently
            # winning regardless of which agent is actually active. Group
            # provenance by resolved directory so each physical directory is
            # restored exactly once, using the active agent's renderer when
            # it shares that directory (otherwise any recorded owner,
            # chosen deterministically).
            groups: Dict[Path, Dict[str, Any]] = {}
            for agent_name, skill_names in registered_skills.items():
                if not skill_names:
                    continue
                skills_dir = self._safe_skills_dir_for_agent(agent_name)
                if skills_dir is None:
                    continue
                group = groups.setdefault(skills_dir, {"agents": [], "names": []})
                group["agents"].append(agent_name)
                for name in skill_names:
                    if (
                        self._is_safe_registry_skill_name(name)
                        and name not in group["names"]
                    ):
                        group["names"].append(name)

            restored: Dict[Path, tuple[Optional[str], List[str]]] = {}
            for skills_dir, group in groups.items():
                agents = group["agents"]
                renderer_agent = (
                    active_agent if active_agent in agents else sorted(agents)[0]
                )
                mutated_names = self._unregister_skills_in_dir(
                    group["names"],
                    skills_dir,
                    renderer_agent,
                    pack_id=pack_id,
                    additional_owned_sources=additional_owned_sources,
                    restore_from_bundled_core=restore_from_bundled_core,
                )
                if mutated_names:
                    restored[skills_dir] = (
                        renderer_agent,
                        mutated_names,
                    )
            return restored

        # Legacy flat-list format: no record of which agent directory these
        # names were written under, so best-effort restore is limited to the
        # currently active agent's directory (the pre-provenance behaviour).
        skills_dir = self._get_skills_dir()
        if not skills_dir:
            return {}
        from .. import load_init_options

        init_opts = load_init_options(self.project_root)
        if not isinstance(init_opts, dict):
            init_opts = {}
        selected_ai = init_opts.get("ai")
        selected_ai = selected_ai if isinstance(selected_ai, str) else None
        safe_names = [
            name
            for name in registered_skills
            if self._is_safe_registry_skill_name(name)
        ]
        mutated_names = self._unregister_skills_in_dir(
            safe_names,
            skills_dir,
            selected_ai,
            pack_id=pack_id,
            additional_owned_sources=additional_owned_sources,
            restore_from_bundled_core=restore_from_bundled_core,
        )
        return (
            {skills_dir: (selected_ai, mutated_names)}
            if mutated_names
            else {}
        )

    def _delete_agent_preset_skills(
        self, agent_name: str, skill_names: List[str], pack_id: str
    ) -> None:
        """Delete still-preset-owned skills when an agent is deactivated."""
        skills_dir = self._safe_skills_dir_for_agent(agent_name)
        if skills_dir is None:
            return

        from ..agents import CommandRegistrar

        registrar = CommandRegistrar()
        marker = f"preset:{pack_id}"
        override_sources: Dict[str, str] = {}
        manifest = PresetResolver(self.project_root)._get_manifest(
            self.presets_dir / pack_id
        )
        if manifest is not None:
            for template in manifest.templates:
                command_name = template.get("name")
                if (
                    template.get("type") == "command"
                    and isinstance(command_name, str)
                ):
                    for skill_name in self._skill_names_for_command(
                        command_name
                    ):
                        override_sources[skill_name] = (
                            f"override:{command_name}"
                        )
        for skill_name in skill_names:
            if not self._is_safe_registry_skill_name(skill_name):
                continue
            skill_subdir = skills_dir / skill_name
            if not self._validate_skill_subdir(
                skill_subdir, create=False, skills_root=skills_dir
            ):
                continue
            skill_file = skill_subdir / "SKILL.md"
            if not skill_file.is_file():
                continue
            try:
                content = skill_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            frontmatter, _ = registrar.parse_frontmatter(content)
            metadata = frontmatter.get("metadata")
            source = (
                metadata.get("source")
                if isinstance(metadata, dict)
                else None
            )
            owned_sources = {marker}
            override_source = override_sources.get(skill_name)
            if override_source:
                owned_sources.add(override_source)
            if source in owned_sources:
                shutil.rmtree(skill_subdir)

    @staticmethod
    def _warn_unrestored_skill(
        skill_name: str, source_file: Path, exc: BaseException
    ) -> None:
        """Warn that a skill kept preset content because its restore source is unreadable.

        Skipping the restore is the safe recovery — the alternative branch
        deletes the skill outright — but it is still a partial removal: the
        preset directory and registry entry go away while this ``SKILL.md``
        keeps the removed preset's content, and reconciliation never revisits
        it because the name is left out of ``mutated_names``. Name the skill
        and the source so the condition is actionable instead of silent.
        """
        import warnings

        warnings.warn(
            f"Skill '{skill_name}' still contains the removed preset's content: "
            f"its restore source '{source_file}' could not be read "
            f"({exc.__class__.__name__}: {exc}). The skill was left in place "
            f"rather than deleted. Fix or remove that file and re-run "
            f"'specify preset add'/'specify preset remove' to refresh it.",
            stacklevel=2,
        )

    def _unregister_skills_in_dir(
        self,
        skill_names: List[str],
        skills_dir: Path,
        selected_ai: Optional[str],
        *,
        pack_id: Optional[str] = None,
        additional_owned_sources: Optional[Dict[str, str]] = None,
        restore_from_bundled_core: bool = False,
    ) -> List[str]:
        """Restore original SKILL.md files within a single skills directory.

        Args:
            skill_names: List of skill names written by the preset.
            skills_dir: The skills directory to restore within.
            selected_ai: The agent name that owns ``skills_dir``, used for
                placeholder resolution and argument-hint formatting.
            additional_owned_sources: Generated non-preset source markers
                accepted as owned for specific skill names.
            restore_from_bundled_core: See ``_unregister_skills``.

        Returns:
            Skill names whose files were restored or removed.
        """
        from .. import SKILL_DESCRIPTIONS
        from ..agents import CommandRegistrar
        from ..integrations import get_integration
        from ..shared_infra import _write_shared_text

        # Locate core command templates from the project's installed templates
        core_templates_dir = self.project_root / ".specify" / "templates" / "commands"
        registrar = CommandRegistrar()
        integration = get_integration(selected_ai) if isinstance(selected_ai, str) else None
        extension_restore_index = self._build_extension_skill_restore_index()
        mutated_names: List[str] = []

        for skill_name in skill_names:
            # Guard against a corrupted/malicious registry entry: a
            # registered_skills name is persisted data, not derived from
            # the current manifest, so it must be validated as a single,
            # relative, non-"."/".." path component before ever being
            # joined onto skills_dir. Without this, an absolute name
            # discards skills_dir entirely (Path's "/" operator drops the
            # left side for an absolute right side) or a multi-component
            # name containing ".." can resolve to a different, unrelated
            # directory that still happens to be inside the project root
            # — passing the containment-only symlink guard below and
            # letting removal overwrite/delete it (#2948).
            if not self._is_safe_registry_skill_name(skill_name):
                continue

            # Derive command name from skill name (speckit-specify -> specify)
            short_name = skill_name
            if short_name.startswith("speckit-"):
                short_name = short_name[len("speckit-"):]
            elif short_name.startswith("speckit."):
                short_name = short_name[len("speckit."):]

            skill_subdir = skills_dir / skill_name
            skill_file = skill_subdir / "SKILL.md"
            if not skill_subdir.is_dir():
                continue
            # is_dir() follows symlinks, so a symlinked skill subdirectory
            # (with a safe, non-symlinked parent) would otherwise slip past
            # _safe_skills_dir_for_agent's parent-only check and have
            # write_text/rmtree operate through it (#2948).
            if not self._validate_skill_subdir(
                skill_subdir, create=False, skills_root=skills_dir
            ):
                continue
            if not skill_file.is_file():
                # Only manage directories that contain the expected skill entrypoint.
                continue
            if pack_id is not None:
                try:
                    current_content = skill_file.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                current_frontmatter, _ = registrar.parse_frontmatter(current_content)
                current_metadata = current_frontmatter.get("metadata")
                current_source = (
                    current_metadata.get("source")
                    if isinstance(current_metadata, dict)
                    else None
                )
                owned_sources = {f"preset:{pack_id}"}
                if additional_owned_sources:
                    additional_source = additional_owned_sources.get(
                        skill_name
                    )
                    if additional_source:
                        owned_sources.add(additional_source)
                if current_source not in owned_sources:
                    continue

            extension_restore = extension_restore_index.get(skill_name)

            # Try to find the core command template. Project-local overrides
            # in core_templates_dir take precedence, but that directory is
            # rarely populated — the real core commands ship in the bundled
            # core_pack (wheel install) or the repo-root templates/ tree
            # (source checkout). Callers that want a genuine restore (a
            # preset was removed outright, not superseded by another
            # renderer) opt into that fallback via restore_from_bundled_core
            # so the skill is restored instead of deleted (#3928). An
            # installed extension providing a core-named command resolves
            # ahead of bundled core elsewhere, so skip the bundled fallback
            # when an extension restore exists — otherwise it would win
            # over the higher-priority extension layer below.
            core_file = core_templates_dir / f"{short_name}.md"
            if (
                not core_file.exists()
                and restore_from_bundled_core
                and extension_restore is None
            ):
                from .. import _locate_core_pack, _repo_root

                _core_pack = _locate_core_pack()
                if _core_pack is not None:
                    core_file = _core_pack / "commands" / f"{short_name}.md"
                else:
                    core_file = _repo_root() / "templates" / "commands" / f"{short_name}.md"
            if not core_file.exists():
                core_file = None

            if core_file:
                # Restore from core template. An unreadable/undecodable
                # source cannot produce restored content, so leave the
                # existing skill untouched rather than leaking a raw
                # OSError/UnicodeDecodeError out of `preset remove` — and
                # rather than falling through to the rmtree below, which
                # would delete a skill precisely when its replacement
                # cannot be generated. Matches the `continue` guards above
                # (unsafe name, missing subdir, foreign owner), which also
                # skip without recording the name as mutated.
                try:
                    content = core_file.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError) as exc:
                    self._warn_unrestored_skill(skill_name, core_file, exc)
                    continue
                frontmatter, body = registrar.parse_frontmatter(content)
                if isinstance(selected_ai, str):
                    body = registrar.resolve_skill_placeholders(
                        selected_ai, frontmatter, body, self.project_root
                    )
                    body = self._resolve_skill_command_refs(
                        body, registrar, selected_ai, self.project_root
                    )

                original_desc = frontmatter.get("description", "")
                enhanced_desc = original_desc or SKILL_DESCRIPTIONS.get(
                    short_name,
                    f"Spec-kit workflow command: {short_name}",
                )

                frontmatter_data = registrar.build_skill_frontmatter(
                    selected_ai if isinstance(selected_ai, str) else "",
                    skill_name,
                    enhanced_desc,
                    f"templates/commands/{short_name}.md",
                )
                registrar.apply_argument_hint(frontmatter, frontmatter_data, integration)
                frontmatter_text = dump_frontmatter(frontmatter_data)
                skill_title = self._skill_title_from_command(short_name)
                skill_content = (
                    f"---\n"
                    f"{frontmatter_text}\n"
                    f"---\n\n"
                    f"# Speckit {skill_title} Skill\n\n"
                    f"{body}\n"
                )
                if integration is not None and hasattr(integration, "post_process_skill_content"):
                    skill_content = integration.post_process_skill_content(
                        skill_content
                    )
                _write_shared_text(skills_dir, skill_file, skill_content)
                mutated_names.append(skill_name)
                continue

            if extension_restore:
                # Same boundary as the core-template branch above: an
                # unreadable extension source leaves the skill in place
                # instead of crashing or being deleted.
                try:
                    content = extension_restore["source_file"].read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError) as exc:
                    self._warn_unrestored_skill(
                        skill_name, extension_restore["source_file"], exc
                    )
                    continue
                frontmatter, body = registrar.parse_frontmatter(content)
                # Mirror the register-time rewrite (#2101): resolve
                # extension-relative subdir references (agents/,
                # knowledge-base/, etc.) to their installed location before
                # the generic placeholder resolution below, otherwise
                # restoring after a preset override removal would leave
                # bare, unresolvable paths in the skill body.
                body = registrar.rewrite_extension_paths(
                    body,
                    extension_restore["extension_id"],
                    extension_restore["extension_dir"],
                )
                if isinstance(selected_ai, str):
                    body = registrar.resolve_skill_placeholders(
                        selected_ai, frontmatter, body, self.project_root
                    )
                    body = self._resolve_skill_command_refs(
                        body, registrar, selected_ai, self.project_root
                    )

                command_name = extension_restore["command_name"]
                title_name = self._skill_title_from_command(command_name)

                frontmatter_data = registrar.build_skill_frontmatter(
                    selected_ai if isinstance(selected_ai, str) else "",
                    skill_name,
                    frontmatter.get("description", f"Extension command: {command_name}"),
                    extension_restore["source"],
                    author=extension_restore.get("author", "github-spec-kit"),
                )
                registrar.apply_argument_hint(frontmatter, frontmatter_data, integration)
                frontmatter_text = dump_frontmatter(frontmatter_data)
                skill_content = (
                    f"---\n"
                    f"{frontmatter_text}\n"
                    f"---\n\n"
                    f"# {title_name} Skill\n\n"
                    f"{body}\n"
                )
                if integration is not None and hasattr(integration, "post_process_skill_content"):
                    skill_content = integration.post_process_skill_content(
                        skill_content
                    )
                _write_shared_text(skills_dir, skill_file, skill_content)
                mutated_names.append(skill_name)
            else:
                # No core or extension template — remove the skill entirely
                shutil.rmtree(skill_subdir)
                mutated_names.append(skill_name)

        return mutated_names
