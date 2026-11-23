"""Agent skill registration and safe reconciliation for installed presets."""

import copy
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, Union

if TYPE_CHECKING:
    from ..agents import CommandRegistrar


from .._init_options import is_ai_skills_enabled
from .._invocation_style import get_invocation_prefix
from .._utils import dump_frontmatter
from ..extensions import ExtensionRegistry
from ..file_helper import FileHelper
from ..integrations.base import IntegrationBase
from ..integrations._registration import project_registration
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

    @project_registration
    def _reconcile_skills(
        self,
        command_names: List[str],
        extra_skills_dirs: Optional[
            Dict[Path, tuple[Optional[str], List[str]]]
        ] = None,
        target_agent: Optional[str] = None,
        new_file_modes: Optional[Dict[Path, int]] = None,
        removed_alias_outputs: Optional[Dict[Path, Set[str]]] = None,
        disabled_composer_deps: Optional[Set[tuple[str, Path, str]]] = None,
        owner_restores: Optional[
            Dict[tuple[Path, Optional[str], str], Dict[str, List[str]]]
        ] = None,
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
            new_file_modes: Permission bits of the ``SKILL.md`` files the
                removed preset had, by path (:meth:`_skill_file_modes`). A
                skill written where one of them was deleted takes its bits.
            removed_alias_outputs: ``{skills_dir: {skill_name, ...}}`` for
                outputs deleted during this removal pass so surviving owners
                can restore only those outputs without recreating unrelated
                user-deleted files.

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
        # Commands won by a composing preset whose stack no longer has any
        # replace base: nothing resolves, so their owned output is removed.
        unresolvable_cmds: Set[str] = set()
        non_preset_skills: List[tuple] = []
        managed_skill_names: set = set()
        reconciled_skill_commands: set[str] = set()
        cmd_layers: Dict[str, List[Dict[str, Any]]] = {}

        for cmd_name in command_names:
            layers = resolver.collect_all_layers(cmd_name, "command")
            if not layers:
                continue
            cmd_layers[cmd_name] = layers

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
                    if (
                        all(layer["strategy"] != "replace" for layer in layers)
                        and resolver.resolve_content(cmd_name, "command") is None
                    ):
                        unresolvable_cmds.add(cmd_name)
                    found_preset = True
                    break
            if not found_preset:
                # Winner is a non-preset source (core/extension/override).
                # Track the winning layer path for skill restoration.
                non_preset_skills.append((skill_name, cmd_name, layers[0]))

        core_ext_skills = [s for s in non_preset_skills if s[2]["source"] != "project override"]
        override_skills = [s for s in non_preset_skills if s[2]["source"] == "project override"]

        # A destination or skill output that cannot be written must not leave
        # the others stale: isolate failures per skill output and continue
        # processing the remaining commands, directories, owners, and aliases,
        # then raise the first failure so the caller still warns about it.
        failures: List[Exception] = []

        def attempt(step: Callable[..., None], *args: Any, **kwargs: Any) -> None:
            try:
                step(*args, **kwargs)
            except Exception as exc:
                failures.append(exc)

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
            # _unregister_skills_in_dir can remove the skill file, so
            # overrides must be handled directly (create dir + write)
            # without that call.
            dir_core_ext_names = [
                candidate
                for _skill_name, cmd_name, _top_layer in core_ext_skills
                for candidate in self._skill_names_for_command(cmd_name)
                if candidate in dir_managed_names
            ]
            for core_skill_name in dict.fromkeys(dir_core_ext_names):
                attempt(
                    self._unregister_skills_in_dir,
                    [core_skill_name],
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
                    from ..shared_infra import _write_shared_text
                    registrar = self._command_registrar()
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
                            preserve_mode=True,
                            new_file_mode=(new_file_modes or {}).get(
                                skill_subdir / "SKILL.md"
                            ),
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
                stale_cmds = [cmd for cmd in dir_cmds if cmd in unresolvable_cmds]
                if stale_cmds:
                    for cmd in stale_cmds:
                        for name in dict.fromkeys(
                            self._skill_names_for_command(cmd)
                        ):
                            if name in dir_managed_names:
                                attempt(
                                    self._remove_owned_skills,
                                    skills_dir,
                                    cmd,
                                    [name],
                                )
                    dir_cmds = [cmd for cmd in dir_cmds if cmd not in unresolvable_cmds]
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

                def reconcile_one_skill(
                    cmd_name: str,
                    skill_name: str,
                    *,
                    _manifest: PresetManifest = manifest,
                    _pack_dir: Path = pack_dir,
                    _pack_id: str = pack_id,
                ) -> None:
                    # Not dead code: _register_skills only *overwrites* skill
                    # subdirectories that already exist (plus brand-new ones
                    # for the active ai_skills agent). For a restore into a
                    # historical directory, _unregister_skills has just deleted
                    # the retiring preset's subdirectory, so pre-create the
                    # tracked (dir_managed_names) subdirectories here — under
                    # the same symlink guard — or the surviving preset's
                    # override would be silently skipped (#2948).
                    if skill_name in dir_managed_names:
                        skill_subdir = skills_dir / skill_name
                        if not self._validate_skill_subdir(
                            skill_subdir,
                            create=True,
                            skills_root=skills_dir,
                        ):
                            return
                    filtered_manifest = self._FilteredManifest(
                        _manifest, {cmd_name}
                    )
                    if is_active:
                        # Preserve exact prior behaviour for the currently
                        # active directory (including the ability to create
                        # brand-new skill subdirectories when ai_skills is on).
                        written = self._register_skills(
                            filtered_manifest,
                            _pack_dir,
                            only_skill_names={skill_name},
                            new_file_modes=new_file_modes,
                        )
                    else:
                        written = self._register_skills(
                            filtered_manifest,
                            _pack_dir,
                            target_dir=skills_dir,
                            target_agent=dir_agent or "",
                            only_skill_names={skill_name},
                            new_file_modes=new_file_modes,
                        )
                    if target_agent is None:
                        written_names = {
                            name
                            for names in written.values()
                            for name in names
                        }
                    else:
                        written_names = set(written.get(target_agent, []))
                    if skill_name in written_names:
                        reconciled_skill_commands.add(cmd_name)
                    # The winning preset may not have previously written to
                    # this directory's agent (most notably a historical agent
                    # reconciliation just restored content into via
                    # extra_skills_dirs). If that write isn't merged back into
                    # the preset's own registered_skills, its registry entry
                    # silently lies about which directories it owns and a
                    # later removal of this same preset orphans the directory
                    # reconciliation just wrote to on its behalf (#2948).
                    self._merge_pack_registered_skills(_pack_id, written)

                for cmd_name in dir_cmds:
                    for skill_name in dict.fromkeys(
                        self._skill_names_for_command(cmd_name)
                    ):
                        if (
                            managed_names is not None
                            and skill_name not in managed_names
                        ):
                            continue
                        attempt(reconcile_one_skill, cmd_name, skill_name)

        extra_dirs = dict(extra_skills_dirs or {})
        # {(skills_dir, agent, owner_id): {cmd_name: [skill_name, ...]}}
        owner_refreshes: Dict[tuple, Dict[str, List[str]]] = {}
        if extra_skills_dirs is not None:
            # _unregister_skills only restored what the removed preset owned.
            # Skills a surviving preset composed on top of it are its own, so
            # refresh those recorded destinations from that owner's layer and
            # the layers below it. A replace owner never depended on lower
            # layers, and a higher preset that never registered there must
            # not be rendered into it (#2948), so the global winner is used
            # only when it is the owner.
            for skills_dir, agent, owner_id, cmd_name, name in self._surviving_owned_skills(
                command_names, presets_by_priority, active_ai, active_skills_dir
            ):
                layers = cmd_layers.get(cmd_name, [])
                owner_dir = self.presets_dir / owner_id
                owner_idx = next(
                    (
                        idx
                        for idx, layer in enumerate(layers)
                        if layer["path"].is_relative_to(owner_dir)
                    ),
                    None,
                )
                if owner_idx is None or layers[owner_idx]["strategy"] == "replace":
                    continue
                # A layer under the owner that was never registered in this
                # destination (a preset installed while another agent was
                # active) must not be composed into it either. The global
                # winner's own composition is only right when nothing is
                # filtered out; otherwise compose from the owner's layers
                # that belong here.
                registered_here = self._layers_registered_in(
                    layers[owner_idx:], skills_dir, active_ai, active_skills_dir,
                    cmd_name,
                )
                # A project override wins the command for every agent, so the
                # owner's composition is not what belongs there: let the
                # winner pass below render the override, as a rescaffold does.
                # When multiple affected commands share this skill directory
                # name (e.g. ``speckit.custom-short`` and ``speckit.custom.short``),
                # route through ``owner_refreshes`` so ``apply_to_dir`` cannot
                # overwrite the file with a colliding command's winner.
                overridden = layers[0]["source"] == "project override"
                collides_with_other_cmd = (
                    sum(
                        1
                        for other_cmd in command_names
                        if name in self._skill_names_for_command(other_cmd)
                    )
                    > 1
                )
                if overridden or (
                    owner_idx == 0
                    and len(registered_here) == len(layers)
                    and not collides_with_other_cmd
                ):
                    prior_agent, prior_names = extra_dirs.get(skills_dir, (agent, []))
                    chosen_agent = agent if agent == active_ai else prior_agent
                    extra_dirs[skills_dir] = (
                        chosen_agent, list(dict.fromkeys([*prior_names, name]))
                    )
                    continue
                owner_refreshes.setdefault(
                    (skills_dir, agent, owner_id), {}
                ).setdefault(cmd_name, []).append(name)

        if active_skills_dir:
            active_provenance = extra_dirs.get(active_skills_dir)
            if extra_skills_dirs is None or active_provenance:
                attempt(
                    apply_to_dir,
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
            attempt(
                apply_to_dir,
                extra_dir,
                extra_agent,
                is_active=False,
                managed_names=set(extra_names),
            )

        def refresh_owner(
            skills_dir: Path,
            agent: Optional[str],
            owner_id: str,
            owned: Dict[str, List[str]],
            *,
            create_missing_dirs: bool = False,
        ) -> None:
            owner_dir = self.presets_dir / owner_id
            try:
                manifest = PresetManifest(owner_dir / "preset.yml")
            except PresetValidationError:
                return

            def write_owner_skill(
                cmd_name: str, skill_name: str, composed_content: str
            ) -> None:
                if create_missing_dirs:
                    if not self._validate_skill_subdir(
                        skills_dir / skill_name,
                        create=True,
                        skills_root=skills_dir,
                    ):
                        return
                written = self._register_skills(
                    self._FilteredManifest(manifest, {cmd_name}),
                    owner_dir,
                    target_dir=skills_dir,
                    target_agent=agent or "",
                    only_skill_names={skill_name},
                    content_overrides={cmd_name: composed_content},
                    new_file_modes=new_file_modes,
                )
                if target_agent is None or agent == target_agent:
                    written_names = {
                        n for names in written.values() for n in names
                    }
                    if skill_name in written_names:
                        reconciled_skill_commands.add(cmd_name)

            for cmd_name, names in owned.items():
                layers = cmd_layers.get(cmd_name)
                if layers is None:
                    layers = resolver.collect_all_layers(cmd_name, "command")
                owner_idx = next(
                    (
                        idx
                        for idx, layer in enumerate(layers)
                        if layer["path"].is_relative_to(owner_dir)
                    ),
                    None,
                )
                if owner_idx is None:
                    continue
                owner_layers = self._layers_registered_in(
                    layers[owner_idx:], skills_dir, active_ai, active_skills_dir,
                    cmd_name,
                )
                composed = resolver.resolve_content(
                    cmd_name, "command", layers=owner_layers
                )
                if composed is not None:
                    for skill_name in dict.fromkeys(names):
                        attempt(write_owner_skill, cmd_name, skill_name, composed)
                elif all(layer["strategy"] != "replace" for layer in owner_layers):
                    # Nothing left under the owner to compose onto.
                    for skill_name in dict.fromkeys(names):
                        attempt(
                            self._remove_owned_skills,
                            skills_dir,
                            cmd_name,
                            [skill_name],
                        )
                # Otherwise a surviving layer is unreadable: keep the
                # existing output rather than deleting it.

        for (skills_dir, agent, owner_id), owned in owner_refreshes.items():
            attempt(refresh_owner, skills_dir, agent, owner_id, owned)

        for (skills_dir, agent, owner_id), owned in (owner_restores or {}).items():
            attempt(
                refresh_owner,
                skills_dir,
                agent,
                owner_id,
                owned,
                create_missing_dirs=True,
            )

        combined_removed_outputs: Dict[Path, Set[str]] = {
            skills_dir: set(names)
            for skills_dir, names in (removed_alias_outputs or {}).items()
            if names
        }
        if extra_skills_dirs:
            for skills_dir, (_agent, names) in extra_skills_dirs.items():
                if names:
                    combined_removed_outputs.setdefault(skills_dir, set()).update(names)

        attempt(
            self._reconcile_preset_aliases,
            command_names,
            presets_by_priority,
            active_ai,
            active_skills_dir,
            create_missing=extra_skills_dirs is None,
            removal_pass=extra_skills_dirs is not None,
            removed_alias_outputs=combined_removed_outputs or None,
            new_file_modes=new_file_modes,
            disabled_composer_deps=disabled_composer_deps,
        )

        if failures:
            raise failures[0]
        return reconciled_skill_commands

    def _render_alias_skill_text(
        self,
        registrar: "CommandRegistrar",
        agent: str,
        agent_config: Dict[str, Any],
        alias: str,
        skill_name: str,
        raw_content: str,
        pack_id: str,
        source_rel: str,
        version: Optional[str],
        *,
        primary_command: Optional[str] = None,
    ) -> str:
        """Render a native-skill alias ``SKILL.md`` for an explicit output dir."""
        from ..integrations import get_integration

        frontmatter, body = registrar.parse_frontmatter(raw_content)
        if frontmatter.get("strategy") == "wrap":
            body, core_frontmatter = _substitute_core_template(
                body, primary_command or alias, self.project_root, registrar
            )
            frontmatter = dict(frontmatter)
            for key in ("scripts", "agent_scripts"):
                if key not in frontmatter and key in core_frontmatter:
                    frontmatter[key] = core_frontmatter[key]
            frontmatter.pop("strategy", None)
        frontmatter = registrar._adjust_script_paths(frontmatter)
        for key in agent_config.get("strip_frontmatter_keys", []):
            frontmatter.pop(key, None)
        if agent_config.get("inject_name") and not frontmatter.get("name"):
            format_name = agent_config.get("format_name")
            frontmatter["name"] = format_name(alias) if format_name else alias
        sep = agent_config.get("invoke_separator", ".")
        try:
            integration = get_integration(agent)
            if integration is not None:
                sep = integration.invoke_separator_for_mode(True)
                frontmatter, body = integration.process_registered_command(
                    frontmatter, body, source_id=pack_id
                )
        except (ImportError, ValueError, KeyError):
            pass
        prefix = get_invocation_prefix(agent, True)
        body = registrar._convert_argument_placeholder(
            body, "$ARGUMENTS", agent_config["args"]
        )
        body = IntegrationBase.resolve_command_refs(body, sep, prefix)
        return registrar.render_skill_command(
            agent,
            skill_name,
            frontmatter,
            body,
            pack_id,
            source_rel,
            self.project_root,
            version=version,
        )

    def _reconcile_preset_aliases(
        self,
        command_names: List[str],
        presets_by_priority: List[Any],
        active_ai: Optional[str],
        active_skills_dir: Optional[Path],
        *,
        create_missing: bool = False,
        removal_pass: bool = False,
        removed_alias_outputs: Optional[Dict[Path, Set[str]]] = None,
        new_file_modes: Optional[Dict[Path, int]] = None,
        disabled_composer_deps: Optional[Set[tuple[str, Path, str]]] = None,
    ) -> None:
        """Re-render, retire or restore native-skill aliases of composed commands.

        For native skill agents, a preset's command aliases are written by
        command registration (``<id>:<file>`` source marker) and recorded in
        its ``registered_commands``, not in ``registered_skills``, so the
        skill pass above never sees them. When a layer under a composing
        preset is added or removed, its aliases would otherwise keep the old
        composition. Rewrite each from the current stack, or remove it when
        nothing is left to compose onto, the same as its primary skill. Only
        outputs still carrying the preset's marker for that command are
        touched.

        Args:
            create_missing: Also render a recorded alias that is missing from
                the active agent's directory (e.g. one retired when its base
                was removed, once a new base makes it composable again). Like
                the primary skill, this only happens for the active agent.
            removal_pass: True when called after a preset was removed, where
                the primary-skill pass also repairs historical agents'
                directories. On install/activation passes, rendering stays
                active-only (the single-active rule of #2948); an alias that
                is no longer composable is still retired wherever it is
                recorded, mirroring stale-output retirement.
            removed_alias_outputs: ``{skills_dir: {skill_name, ...}}`` for
                outputs deleted during this removal so a registered surviving
                owner can restore them without recreating unrelated
                user-deleted files.
            new_file_modes: Pre-deletion permission bits by path for restored
                outputs.
        """
        from ..integrations._file_changes import unlink_in_directory
        from ..shared_infra import _write_shared_text

        try:
            registrar = self._command_registrar()
        except ImportError:
            return
        registrar._ensure_configs()
        resolver = PresetResolver(self.project_root)
        wanted = set(command_names)
        # An alias that cannot be written or removed must not keep the
        # others stale: go on, and raise the first failure at the end.
        failures: List[Exception] = []

        def probe_alias_file(
            skills_dir: Path, skill_name: str
        ) -> tuple[bool, Optional[str], bool]:
            """Return ``(missing, content, skip)`` without following symlinks."""
            skill_dir = skills_dir / skill_name
            try:
                with FileHelper(skills_dir) as files:
                    mode = files.file_mode(Path(skill_name) / "SKILL.md")
                    if mode is None:
                        return True, None, False
                    if not self._validate_skill_subdir(
                        skill_dir, create=False, skills_root=skills_dir
                    ):
                        return False, None, True
                    content = files.read_text(Path(skill_name) / "SKILL.md")
                    return False, content, False
            except FileNotFoundError:
                return True, None, False
            except (OSError, ValueError):
                return False, None, True

        def check_alias_ownership(
            pack_id: str,
            tmpl: Dict[str, Any],
            templates: List[Dict[str, Any]],
            agent: str,
            agent_config: Dict[str, Any],
            alias: str,
            skill_name: str,
            content: str,
        ) -> tuple[bool, bool]:
            """Return ``(owned, standalone_twin)`` for an alias output file."""
            metadata = registrar.parse_frontmatter(content)[0].get("metadata")
            source = (
                metadata.get("source") if isinstance(metadata, dict) else None
            )
            if source == f"{pack_id}:.composed/{tmpl['name']}.md":
                return True, False
            if source != f"{pack_id}:{tmpl.get('file')}":
                return False, False
            position = templates.index(tmpl)
            twins = [
                (idx, other)
                for idx, other in enumerate(templates)
                if other is not tmpl
                and other.get("type") == "command"
                and other.get("file") == tmpl.get("file")
                and any(
                    isinstance(candidate, str)
                    and (
                        candidate == alias
                        or candidate == skill_name
                        or registrar._compute_output_name(
                            agent, candidate, agent_config
                        )
                        == skill_name
                    )
                    for candidate in (
                        other.get("name"),
                        *(other.get("aliases") or []),
                    )
                )
            ]
            if any(idx > position for idx, _ in twins):
                return False, False
            standalone_twin = any(
                other.get("strategy", "replace") == "replace"
                for _, other in twins
            )
            return True, standalone_twin

        def group_recorded_agents(
            recorded: Dict[str, Any],
        ) -> Dict[Path, Dict[str, Any]]:
            groups: Dict[Path, Dict[str, Any]] = {}
            for agent, names in recorded.items():
                agent_config = registrar.AGENT_CONFIGS.get(agent)
                if (
                    not isinstance(names, list)
                    or not agent_config
                    or agent_config.get("extension") != "/SKILL.md"
                ):
                    continue
                skills_dir = (
                    active_skills_dir
                    if agent == active_ai and active_skills_dir is not None
                    else self._safe_skills_dir_for_agent(agent)
                )
                if skills_dir is None:
                    continue
                group = groups.setdefault(skills_dir, {"agents": [], "aliases": []})
                group["agents"].append(agent)
                for name in names:
                    if isinstance(name, str) and name not in group["aliases"]:
                        group["aliases"].append(name)
            return groups

        active_native_dir = self._active_native_skills_dir(
            active_ai, active_skills_dir, registrar.AGENT_CONFIGS
        )

        def pick_renderer_agent(skills_dir: Path, agents: List[str]) -> str:
            return (
                active_ai
                if active_ai
                and (
                    active_ai in agents
                    or (
                        active_native_dir is not None
                        and skills_dir == active_native_dir
                    )
                )
                else sorted(agents)[0]
            )

        for pack_id, meta in presets_by_priority:
            if not isinstance(meta, dict):
                continue
            recorded = meta.get("registered_commands")
            if not isinstance(recorded, dict):
                continue
            pack_dir = self.presets_dir / pack_id
            manifest = self._safe_get_manifest(resolver, pack_dir)
            if not manifest:
                continue
            alias_to_tmpl: Dict[str, tuple[Dict[str, Any], bool]] = {}
            templates = list(manifest.templates)
            for tmpl in templates:
                if tmpl.get("type") != "command":
                    continue
                tmpl_aliases = [
                    a for a in (tmpl.get("aliases") or []) if isinstance(a, str)
                ]
                primary_wanted = tmpl.get("name") in wanted
                alias_wanted = bool(removed_alias_outputs) and any(
                    a in wanted for a in tmpl_aliases
                )
                if not primary_wanted and not alias_wanted:
                    continue
                if tmpl.get("strategy", "replace") == "replace" and not removed_alias_outputs:
                    # A replace layer's own file did not change unless a
                    # retiring higher layer just deleted its shared output.
                    continue
                for alias in tmpl_aliases:
                    if primary_wanted or alias in wanted:
                        alias_to_tmpl[alias] = (tmpl, primary_wanted)
            if not alias_to_tmpl:
                continue

            # Several native skill agents can resolve to one physical
            # directory (agy/codex/zed all use ``.agents/skills``). Rendering
            # it once per recorded agent would let whichever agent is iterated
            # last win, writing another agent's command-reference syntax over
            # the active one's. Group by resolved directory and render with
            # the active agent when it shares that directory, exactly as
            # ``_unregister_skills`` does.
            groups = group_recorded_agents(recorded)

            for skills_dir, group in groups.items():
                agent = pick_renderer_agent(skills_dir, group["agents"])
                agent_config = registrar.AGENT_CONFIGS[agent]
                # Rendering follows the single-active rule outside a removal
                # pass; retiring an uncomposable alias is allowed anywhere.
                may_render = removal_pass or skills_dir == active_skills_dir
                removed_in_dir = (removed_alias_outputs or {}).get(skills_dir, set())
                for alias in group["aliases"]:
                    entry = alias_to_tmpl.get(alias) if isinstance(alias, str) else None
                    if entry is None:
                        continue
                    tmpl, primary_wanted = entry
                    modern_skill_name = registrar._compute_output_name(
                        agent, alias, agent_config
                    )
                    candidate_skill_names = [modern_skill_name]
                    if (
                        modern_skill_name != alias
                        and registrar._is_safe_command_name(alias)
                    ):
                        candidate_skill_names.append(alias)

                    probed = []
                    for skill_name in candidate_skill_names:
                        missing, content, skip = probe_alias_file(
                            skills_dir, skill_name
                        )
                        owned = False
                        standalone_twin = False
                        if not missing and not skip and content is not None:
                            owned, standalone_twin = check_alias_ownership(
                                pack_id,
                                tmpl,
                                templates,
                                agent,
                                agent_config,
                                alias,
                                skill_name,
                                content,
                            )
                        probed.append(
                            (skill_name, missing, skip, owned, standalone_twin)
                        )
                    has_existing_owned = any(
                        not missing and owned
                        for _, missing, _, owned, _ in probed
                    )
                    is_replace = tmpl.get("strategy", "replace") == "replace"

                    for (
                        skill_name,
                        missing,
                        skip,
                        owned,
                        standalone_twin,
                    ) in probed:
                        if skip:
                            continue
                        is_legacy = skill_name != modern_skill_name
                        was_removed = skill_name in removed_in_dir
                        can_restore_removed = (
                            was_removed and not has_existing_owned
                        )
                        if missing:
                            can_create_active = (
                                create_missing
                                and skills_dir == active_skills_dir
                                and not is_legacy
                            )
                            if not (can_restore_removed or can_create_active):
                                continue
                            if (is_replace or not primary_wanted) and not can_restore_removed:
                                continue
                        else:
                            if is_replace or not primary_wanted or not owned:
                                continue

                        skill_dir = skills_dir / skill_name
                        skill_file = skill_dir / "SKILL.md"
                        primary = tmpl["name"]
                        layers = resolver.collect_all_layers(primary, "command")
                        owner_idx = next(
                            (
                                idx
                                for idx, layer in enumerate(layers)
                                if layer["path"].is_relative_to(pack_dir)
                            ),
                            None,
                        )
                        if owner_idx is None:
                            continue
                        # The alias belongs to the highest layer registered in
                        # this directory that declares it, not to whichever
                        # layer wins the primary command.
                        higher_layers = self._layers_registered_in(
                            layers[:owner_idx],
                            skills_dir,
                            active_ai,
                            active_skills_dir,
                            primary,
                        )
                        alias_shadowed = any(
                            self._layer_declares_alias(
                                resolver, layer, primary, alias
                            )
                            for layer in higher_layers
                        )
                        if alias_shadowed and missing:
                            continue

                        if is_replace:
                            if not may_render:
                                continue
                            if not self._validate_skill_subdir(
                                skill_dir, create=True, skills_root=skills_dir
                            ):
                                continue
                            raw_rel = tmpl.get("file")
                            if not isinstance(raw_rel, str):
                                continue
                            try:
                                with FileHelper(pack_dir) as files:
                                    raw_content = files.read_text(Path(raw_rel))
                                rendered = self._render_alias_skill_text(
                                    registrar,
                                    agent,
                                    agent_config,
                                    alias,
                                    skill_name,
                                    raw_content,
                                    pack_id,
                                    raw_rel,
                                    manifest.version,
                                    primary_command=primary,
                                )
                                _write_shared_text(
                                    skills_dir,
                                    skill_file,
                                    rendered,
                                    preserve_mode=True,
                                    new_file_mode=(new_file_modes or {}).get(
                                        skill_file
                                    ),
                                )
                            except (ValueError, OSError) as exc:
                                failures.append(exc)
                            continue

                        # A shadowed alias is not ours to render outside a
                        # removal pass. It still goes through the retirement
                        # check below: a rescaffold re-registers it from the raw
                        # fragment, which must not stay executable once nothing
                        # is left to compose onto. On a removal pass an existing
                        # shadowed alias is refreshed from its own layer down, as
                        # its primary skill is.
                        shadowed = alias_shadowed and not removal_pass
                        owner_layers = self._layers_registered_in(
                            layers[owner_idx:],
                            skills_dir,
                            active_ai,
                            active_skills_dir,
                            primary,
                        )
                        composed = resolver.resolve_content(
                            primary, "command", layers=owner_layers
                        )
                        if composed is None:
                            if (
                                missing
                                or standalone_twin
                                or any(
                                    layer["strategy"] == "replace"
                                    for layer in owner_layers
                                )
                            ):
                                # A replace base is still there, so this is a
                                # resolution failure (e.g. an unreadable layer),
                                # not a missing base: keep the alias, as the
                                # primary-skill path keeps its output. So is an
                                # alias another command of the preset renders
                                # from this file without needing a base.
                                continue
                            alias_file = skill_dir / "SKILL.md"
                            try:
                                unlink_in_directory(
                                    alias_file,
                                    root=(
                                        self.project_root
                                        if alias_file.is_relative_to(
                                            self.project_root
                                        )
                                        else skills_dir
                                    ),
                                )
                            except (ValueError, OSError) as exc:
                                failures.append(exc)
                            continue
                        if shadowed or not may_render:
                            continue
                        hard_linked = False
                        if not missing:
                            try:
                                hard_linked = skill_file.stat().st_nlink > 1
                            except OSError:
                                continue
                        if hard_linked:
                            # Command registration writes the alias in place,
                            # which would reach every other link of the file.
                            # As elsewhere for generated artifacts with extra
                            # links, it is not ours to rewrite: leave it, and
                            # say that it no longer matches the preset stack.
                            import warnings

                            warnings.warn(
                                f"Alias skill {skill_file} has other hard links "
                                f"and was not refreshed. It may still contain "
                                f"content from a preset that is no longer "
                                f"installed; delete it and reinstall the preset "
                                f"to regenerate it.",
                                stacklevel=2,
                            )
                            continue
                        if missing and not self._validate_skill_subdir(
                            skill_dir, create=True, skills_root=skills_dir
                        ):
                            continue
                        composed_file = pack_dir / ".composed" / f"{primary}.md"
                        try:
                            self._write_alias_composed_cache(
                                composed_file, composed
                            )
                        except (ValueError, OSError) as exc:
                            failures.append(exc)
                            continue
                        saved_mode = (
                            (new_file_modes or {}).get(skill_file)
                            if missing
                            else None
                        )
                        try:
                            if not is_legacy and saved_mode is None:
                                registrar.register_commands(
                                    agent,
                                    [
                                        {
                                            "name": alias,
                                            "file": f".composed/{primary}.md",
                                        }
                                    ],
                                    pack_id,
                                    pack_dir,
                                    self.project_root,
                                    _resolved_dir=skills_dir,
                                    version=manifest.version,
                                )
                            else:
                                rendered = self._render_alias_skill_text(
                                    registrar,
                                    agent,
                                    agent_config,
                                    alias,
                                    skill_name,
                                    composed,
                                    pack_id,
                                    f".composed/{primary}.md",
                                    manifest.version,
                                    primary_command=primary,
                                )
                                _write_shared_text(
                                    skills_dir,
                                    skill_file,
                                    rendered,
                                    preserve_mode=True,
                                    new_file_mode=saved_mode,
                                )
                        except (ValueError, OSError) as exc:
                            failures.append(exc)

        if removal_pass:
            # Disabled composing presets are excluded from presets_by_priority,
            # so any alias they previously composed onto the removed layer
            # would otherwise stay executable with the removed layer's text.
            # Retire only outputs still carrying the disabled composer's own
            # marker for a command affected by this removal.
            disabled_presets = [
                (pack_id, meta)
                for pack_id, meta in self.registry.list_by_priority(
                    include_disabled=True
                )
                if isinstance(meta, dict) and not meta.get("enabled", True)
            ]
            for pack_id, meta in disabled_presets:
                recorded = meta.get("registered_commands")
                if not isinstance(recorded, dict):
                    continue
                pack_dir = self.presets_dir / pack_id
                manifest = self._safe_get_manifest(resolver, pack_dir)
                if not manifest:
                    continue
                alias_to_tmpl = {}
                templates = list(manifest.templates)
                for tmpl in templates:
                    if (
                        tmpl.get("type") != "command"
                        or tmpl.get("name") not in wanted
                        or tmpl.get("strategy", "replace") == "replace"
                    ):
                        continue
                    for alias in tmpl.get("aliases") or []:
                        if isinstance(alias, str):
                            alias_to_tmpl[alias] = tmpl
                if not alias_to_tmpl:
                    continue
                groups = group_recorded_agents(recorded)
                for skills_dir, group in groups.items():
                    agent = pick_renderer_agent(skills_dir, group["agents"])
                    agent_config = registrar.AGENT_CONFIGS[agent]
                    for alias in group["aliases"]:
                        tmpl = alias_to_tmpl.get(alias)
                        if tmpl is None:
                            continue
                        if (
                            disabled_composer_deps is not None
                            and (pack_id, skills_dir, tmpl["name"])
                            not in disabled_composer_deps
                        ):
                            continue
                        modern_skill_name = registrar._compute_output_name(
                            agent, alias, agent_config
                        )
                        candidate_skill_names = [modern_skill_name]
                        if (
                            modern_skill_name != alias
                            and registrar._is_safe_command_name(alias)
                        ):
                            candidate_skill_names.append(alias)
                        for skill_name in candidate_skill_names:
                            missing, content, skip = probe_alias_file(
                                skills_dir, skill_name
                            )
                            if missing or skip or content is None:
                                continue
                            owned, standalone_twin = check_alias_ownership(
                                pack_id,
                                tmpl,
                                templates,
                                agent,
                                agent_config,
                                alias,
                                skill_name,
                                content,
                            )
                            if not owned or standalone_twin:
                                continue
                            alias_file = skills_dir / skill_name / "SKILL.md"
                            try:
                                unlink_in_directory(
                                    alias_file,
                                    root=(
                                        self.project_root
                                        if alias_file.is_relative_to(
                                            self.project_root
                                        )
                                        else skills_dir
                                    ),
                                )
                            except (ValueError, OSError) as exc:
                                failures.append(exc)

        if failures:
            raise failures[0]

    def _write_alias_composed_cache(self, composed_file: Path, composed: str) -> None:
        """Write a preset's ``.composed`` cache entry for an alias refresh.

        Every ancestor and the cache file itself must stay inside the project
        and off symlinks, so a planted ``.composed`` link cannot redirect the
        write. The shared writer replaces the entry atomically, so a hard
        link to an outside file is broken, not written through, and nothing
        planted at the path in the meantime is opened or followed. An
        existing entry keeps its permission bits; a missing one is created
        under the process umask, as the other ``.composed`` writes are.

        Raises:
            ValueError, OSError: The path is unsafe or the write failed.
        """
        from ..shared_infra import _ensure_safe_shared_directory, _write_shared_text

        _ensure_safe_shared_directory(
            self.project_root,
            composed_file.parent,
            create=True,
            context="preset composed cache directory",
        )
        _write_shared_text(
            self.project_root, composed_file, composed, preserve_mode=True
        )

    def _layers_registered_in(
        self,
        layers: List[Dict[str, Any]],
        skills_dir: Path,
        active_ai: Optional[str],
        active_skills_dir: Optional[Path],
        cmd_name: str,
    ) -> List[Dict[str, Any]]:
        """Drop pack layers of ``cmd_name`` never registered in ``skills_dir``.

        Presets are registered for the active agent only (#2948), so a preset
        installed while another agent was active has no output in a
        historical agent's directory and must not be composed into one. A
        preset counts as registered here when its ``registered_skills`` lists
        this command's skill for an agent that resolves to this directory, or
        its ``registered_commands`` lists the command for a native skill
        agent that does: only for those is a registered command a file in
        the skills directory. Another command of the same pack recorded
        there says nothing about this one (a registration can be partial). A
        command-backed agent's entry records command files elsewhere, and
        its skills directory can be another agent's (Amp's resolves to
        Codex's ``.agents/skills``). The active directory is never filtered,
        core and project overrides always stay, and so do packs whose
        provenance is unknown. Extensions record native skill commands per
        agent, but their optional skill registrations are still a flat list.
        """
        if active_skills_dir is not None and skills_dir == active_skills_dir:
            return layers
        registered: Dict[str, bool] = {}
        extensions_dir = self.project_root / ".specify" / "extensions"
        extension_registry = None
        try:
            registrar = self._command_registrar()
            registrar._ensure_configs()
            agent_configs = registrar.AGENT_CONFIGS
        except ImportError:
            agent_configs = {}

        wanted = {
            "registered_skills": set(self._skill_names_for_command(cmd_name)),
            "registered_commands": {cmd_name},
        }

        def lists_command(key: str, names: Any) -> bool:
            return isinstance(names, list) and any(
                isinstance(name, str) and name in wanted[key] for name in names
            )

        def writes_skills(agent: Any) -> bool:
            config = agent_configs.get(agent) if isinstance(agent, str) else None
            return bool(config) and config.get("extension") == "/SKILL.md"

        def resolves_here(agent: Any) -> bool:
            if not isinstance(agent, str):
                return False
            if agent == active_ai:
                agent_dir = (
                    active_skills_dir
                    if active_skills_dir is not None or not writes_skills(agent)
                    else self._safe_skills_dir_for_agent(agent)
                )
            else:
                agent_dir = self._safe_skills_dir_for_agent(agent)
            return agent_dir is not None and agent_dir == skills_dir

        def is_registered(pack_id: str) -> bool:
            meta = self.registry.get(pack_id)
            if not isinstance(meta, dict):
                return True
            if isinstance(meta.get("registered_skills"), list):
                if not active_ai:
                    return True
                meta = {
                    **meta,
                    "registered_skills": self._infer_legacy_skill_provenance(
                        [n for n in meta["registered_skills"] if isinstance(n, str)],
                        pack_id,
                        active_ai,
                    ),
                }
            for key in ("registered_skills", "registered_commands"):
                recorded = meta.get(key)
                if isinstance(recorded, dict) and any(
                    lists_command(key, names)
                    and (key == "registered_skills" or writes_skills(agent))
                    and resolves_here(agent)
                    for agent, names in recorded.items()
                ):
                    return True
            return False

        kept: List[Dict[str, Any]] = []
        for layer in layers:
            try:
                ext_rel = layer["path"].relative_to(extensions_dir)
            except (KeyError, TypeError, ValueError):
                ext_rel = None
            if ext_rel is not None and ext_rel.parts:
                if extension_registry is None:
                    extension_registry = ExtensionRegistry(extensions_dir)
                meta = extension_registry.get(ext_rel.parts[0])
                # A nonempty flat skill list cannot establish which agent
                # owns those files. Preserve that legacy fallback, as well
                # as extensions without registration metadata.
                if isinstance(meta, dict) and not meta.get("registered_skills"):
                    commands = meta.get("registered_commands")
                    if isinstance(commands, dict) and not any(
                        lists_command("registered_commands", names)
                        and writes_skills(agent)
                        and resolves_here(agent)
                        for agent, names in commands.items()
                    ):
                        continue
                kept.append(layer)
                continue
            try:
                rel = layer["path"].relative_to(self.presets_dir)
            except (KeyError, TypeError, ValueError):
                kept.append(layer)
                continue
            if not rel.parts:
                kept.append(layer)
                continue
            pack_id = rel.parts[0]
            if pack_id not in registered:
                registered[pack_id] = is_registered(pack_id)
            if registered[pack_id]:
                kept.append(layer)
        return kept

    @staticmethod
    def _safe_get_manifest(
        resolver: PresetResolver, pack_dir: Path
    ) -> Optional["PresetManifest"]:
        """Load a preset manifest, treating validation errors as unavailable."""
        try:
            return resolver._get_manifest(pack_dir)
        except PresetValidationError:
            return None

    def _layer_declares_alias(
        self, resolver: Any, layer: Dict[str, Any], primary: str, alias: str
    ) -> bool:
        """Whether ``layer`` comes from a preset declaring ``alias`` for ``primary``."""
        try:
            rel = layer["path"].relative_to(self.presets_dir)
        except (KeyError, TypeError, ValueError):
            return False
        if not rel.parts:
            return False
        manifest = self._safe_get_manifest(resolver, self.presets_dir / rel.parts[0])
        if not manifest:
            return False
        return any(
            tmpl.get("type") == "command"
            and tmpl.get("name") == primary
            and alias in (tmpl.get("aliases") or [])
            for tmpl in manifest.templates
        )

    def _active_native_skills_dir(
        self,
        active_ai: Optional[str],
        active_skills_dir: Optional[Path],
        agent_configs: Dict[str, Any],
    ) -> Optional[Path]:
        """Return the active agent's skills directory when it is a native skill agent.

        Native skill agents (``extension == "/SKILL.md"``) always render into
        their skills directory even when ``ai_skills`` is false or absent, so
        renderer tie-breaks must resolve their directory independently of the
        optional ``ai_skills`` flag.
        """
        if not isinstance(active_ai, str) or not active_ai:
            return None
        config = agent_configs.get(active_ai)
        if not config or config.get("extension") != "/SKILL.md":
            return None
        if active_skills_dir is not None:
            return active_skills_dir
        return self._safe_skills_dir_for_agent(active_ai)

    def _collect_disabled_composer_dependencies(
        self,
        pack_id: str,
        removed_cmd_names: Optional[Set[str]] = None,
    ) -> Set[tuple[str, Path, str]]:
        """Capture ``(disabled_pack_id, skills_dir, cmd_name)`` pairs that depend on ``pack_id``.

        Must run while ``pack_id`` is still in the registry and on disk. A
        disabled composing preset depends on ``pack_id`` for ``cmd_name`` in
        ``skills_dir`` only when:
        - ``pack_id`` has lower priority (sits below the composer),
        - ``pack_id`` actually supplies a command layer for ``cmd_name`` in
          ``skills_dir``, and
        - no enabled ``replace`` layer registered in ``skills_dir`` sits
          strictly between the disabled composer and ``pack_id``.
        """
        from .. import load_init_options

        all_presets = list(self.registry.list_by_priority(include_disabled=True))
        priority_rank = {pid: idx for idx, (pid, _meta) in enumerate(all_presets)}
        pack_rank = priority_rank.get(pack_id)
        if pack_rank is None:
            return set()
        disabled_presets = [
            (pid, meta)
            for pid, meta in all_presets
            if pid != pack_id
            and isinstance(meta, dict)
            and not meta.get("enabled", True)
        ]
        if not disabled_presets:
            return set()

        try:
            registrar = self._command_registrar()
        except ImportError:
            return set()
        registrar._ensure_configs()

        resolver = PresetResolver(self.project_root)
        pack_dir = self.presets_dir / pack_id
        pack_manifest = self._safe_get_manifest(resolver, pack_dir)
        pack_meta = self.registry.get(pack_id)
        pack_enabled = (
            bool(pack_meta.get("enabled", True))
            if isinstance(pack_meta, dict)
            else False
        )
        if pack_manifest is not None:
            pack_primary_cmds = {
                tmpl["name"]
                for tmpl in pack_manifest.templates
                if tmpl.get("type") == "command"
                and isinstance(tmpl.get("name"), str)
            }
        elif removed_cmd_names is not None:
            pack_primary_cmds = set(removed_cmd_names)
        else:
            pack_primary_cmds = set()
            if isinstance(pack_meta, dict):
                reg_cmds = pack_meta.get("registered_commands")
                if isinstance(reg_cmds, dict):
                    for names in reg_cmds.values():
                        if isinstance(names, list):
                            pack_primary_cmds.update(
                                n for n in names if isinstance(n, str)
                            )
        if removed_cmd_names is not None:
            pack_primary_cmds &= removed_cmd_names
        if not pack_primary_cmds:
            return set()

        init_opts = load_init_options(self.project_root)
        active_ai = init_opts.get("ai") if isinstance(init_opts, dict) else None
        if not isinstance(active_ai, str) or not active_ai:
            active_ai = None
        active_skills_dir = self._get_skills_dir()

        def resolve_dir(agent_name: str, native_skill_agent: bool) -> Optional[Path]:
            if agent_name == active_ai:
                return (
                    active_skills_dir
                    if active_skills_dir is not None or not native_skill_agent
                    else self._safe_skills_dir_for_agent(agent_name)
                )
            return self._safe_skills_dir_for_agent(agent_name)

        enabled_layers_cache: Dict[str, Optional[List[Dict[str, Any]]]] = {}

        def get_enabled_layers(cmd_name: str) -> Optional[List[Dict[str, Any]]]:
            if cmd_name not in enabled_layers_cache:
                try:
                    enabled_layers_cache[cmd_name] = resolver.collect_all_layers(
                        cmd_name, "command"
                    )
                except PresetValidationError:
                    enabled_layers_cache[cmd_name] = None
            return enabled_layers_cache[cmd_name]

        def pack_contributes_to(
            other_id: str, cmd_name: str, skills_dir: Path
        ) -> bool:
            if cmd_name not in pack_primary_cmds:
                return False
            other_rank = priority_rank.get(other_id)
            if other_rank is None or pack_rank <= other_rank:
                return False
            enabled_layers = get_enabled_layers(cmd_name)
            if enabled_layers is None:
                return True
            dir_layers = self._layers_registered_in(
                enabled_layers, skills_dir, active_ai, active_skills_dir, cmd_name
            )
            if pack_enabled:
                if not any(
                    layer["path"].is_relative_to(pack_dir)
                    for layer in dir_layers
                ):
                    return False
            else:
                synthetic_layer = [
                    {
                        "path": pack_dir / "commands" / f"{cmd_name}.md",
                        "source": pack_id,
                        "strategy": "replace",
                    }
                ]
                if not self._layers_registered_in(
                    synthetic_layer,
                    skills_dir,
                    active_ai,
                    active_skills_dir,
                    cmd_name,
                ):
                    return False
            for layer in dir_layers:
                if layer["strategy"] != "replace":
                    continue
                try:
                    rel = layer["path"].relative_to(self.presets_dir)
                except (KeyError, TypeError, ValueError):
                    continue
                if not rel.parts:
                    continue
                mid_rank = priority_rank.get(rel.parts[0])
                if mid_rank is not None and other_rank < mid_rank < pack_rank:
                    return False
            return True

        deps: Set[tuple[str, Path, str]] = set()
        for other_id, meta in disabled_presets:
            other_manifest = self._safe_get_manifest(
                resolver, self.presets_dir / other_id
            )
            if other_manifest is None:
                continue
            composing_templates = [
                tmpl
                for tmpl in other_manifest.templates
                if tmpl.get("type") == "command"
                and isinstance(tmpl.get("name"), str)
                and tmpl.get("strategy", "replace") != "replace"
            ]
            if not composing_templates:
                continue
            candidates: Set[tuple[Path, str]] = set()
            reg_skills = meta.get("registered_skills")
            if isinstance(reg_skills, list):
                reg_skills = self._infer_legacy_skill_provenance(
                    [n for n in reg_skills if isinstance(n, str)],
                    other_id,
                    active_ai or "",
                )
            if isinstance(reg_skills, dict):
                for other_agent, other_skills in reg_skills.items():
                    if not isinstance(other_agent, str) or not isinstance(
                        other_skills, list
                    ):
                        continue
                    other_cfg = registrar.AGENT_CONFIGS.get(other_agent)
                    other_native = bool(
                        other_cfg and other_cfg.get("extension") == "/SKILL.md"
                    )
                    other_dir = resolve_dir(other_agent, other_native)
                    if other_dir is None:
                        continue
                    for skill_name in other_skills:
                        if not isinstance(skill_name, str):
                            continue
                        for tmpl in composing_templates:
                            if skill_name in self._skill_names_for_command(
                                tmpl["name"]
                            ):
                                candidates.add((other_dir, tmpl["name"]))
            reg_cmds = meta.get("registered_commands")
            if isinstance(reg_cmds, dict):
                for other_agent, other_cmds in reg_cmds.items():
                    if not isinstance(other_agent, str) or not isinstance(
                        other_cmds, list
                    ):
                        continue
                    other_cfg = registrar.AGENT_CONFIGS.get(other_agent)
                    if not other_cfg or other_cfg.get("extension") != "/SKILL.md":
                        continue
                    other_dir = resolve_dir(other_agent, True)
                    if other_dir is None:
                        continue
                    for other_cmd in other_cmds:
                        if not isinstance(other_cmd, str):
                            continue
                        for tmpl in composing_templates:
                            if (
                                tmpl["name"] == other_cmd
                                or other_cmd in (tmpl.get("aliases") or [])
                            ):
                                candidates.add((other_dir, tmpl["name"]))
            for other_dir, cmd_name in candidates:
                if pack_contributes_to(other_id, cmd_name, other_dir):
                    deps.add((other_id, other_dir, cmd_name))
        return deps

    def _drop_survivor_owned_aliases(
        self,
        pack_id: str,
        registered_commands: Dict[str, List[str]],
        *,
        deleted_outputs: Optional[Dict[Path, Set[str]]] = None,
        retired_modes: Optional[Dict[Path, int]] = None,
        removed_cmd_names: Optional[Set[str]] = None,
        disabled_composer_deps: Optional[Set[tuple[str, Path, str]]] = None,
        restored_primary_owners: Optional[
            Dict[tuple[Path, Optional[str], str], Dict[str, List[str]]]
        ] = None,
    ) -> Dict[str, List[str]]:
        """Clean retiring native-skill outputs per spelling without harming survivors.

        Two presets can declare the same command or alias. For native skill
        agents both record it in ``registered_commands``, but only one file
        exists, carrying the ``<id>:<file>`` marker of whichever registered
        it last, or a ``preset:<id>`` marker after skill registration.
        A partial skill registration can leave a primary command in this
        cleanup list too.

        Ownership is decided per spelling (modern output name and legacy
        dotted name) against the retiring preset's exact sources and each
        survivor's actual registrations in that directory:

        - Outputs owned by an enabled survivor (or a disabled preset whose
          command does not compose onto the retiring layer) are kept for
          reconciliation or left untouched.
        - Dependent outputs owned by a disabled composing preset are retired
          here because post-removal reconciliation excludes disabled presets.
        - Outputs carrying an exact retiring marker are unlinked here and
          recorded in ``deleted_outputs`` (with their pre-deletion bits in
          ``retired_modes``) so reconciliation can restore them for a
          registered surviving owner without recreating unrelated
          user-deleted files.
        - Unowned, user-edited, unreadable, or symlinked files for a shared
          output are preserved rather than forwarded to unconditional cleanup.
        """
        from .. import load_init_options
        from ..integrations._file_changes import unlink_in_directory

        try:
            registrar = self._command_registrar()
        except ImportError:
            return registered_commands
        registrar._ensure_configs()
        all_others = [
            pid
            for pid, _meta in self.registry.list_by_priority(include_disabled=True)
            if pid != pack_id
        ]
        if not all_others:
            return registered_commands

        if disabled_composer_deps is None:
            disabled_composer_deps = self._collect_disabled_composer_dependencies(
                pack_id, removed_cmd_names
            )

        resolver = PresetResolver(self.project_root)
        retiring_manifest = self._safe_get_manifest(
            resolver, self.presets_dir / pack_id
        )
        init_opts = load_init_options(self.project_root)
        active_ai = init_opts.get("ai") if isinstance(init_opts, dict) else None
        if not isinstance(active_ai, str) or not active_ai:
            active_ai = None
        active_skills_dir = self._get_skills_dir()
        active_native_dir = self._active_native_skills_dir(
            active_ai, active_skills_dir, registrar.AGENT_CONFIGS
        )
        effective_active_dir = (
            active_skills_dir
            if active_skills_dir is not None
            else active_native_dir
        )

        def resolve_dir(agent_name: str, native_skill_agent: bool) -> Optional[Path]:
            if agent_name == active_ai:
                return (
                    active_skills_dir
                    if active_skills_dir is not None or not native_skill_agent
                    else self._safe_skills_dir_for_agent(agent_name)
                )
            return self._safe_skills_dir_for_agent(agent_name)

        # {(skills_dir, candidate_name): [(other_id, enabled, dependent_composer, markers_or_none, other_agent, primary_cmd_or_none)]}
        survivor_entries: Dict[
            tuple[Path, str],
            List[
                tuple[
                    str,
                    bool,
                    bool,
                    Optional[Set[str]],
                    str,
                    Optional[str],
                ]
            ],
        ] = {}
        # {(other_id, skills_dir): [agent_name, ...]} for renderer tie-breaking
        survivor_dir_agents: Dict[tuple[str, Path], List[str]] = {}
        for other in all_others:
            meta = self.registry.get(other)
            if not isinstance(meta, dict):
                continue
            enabled = bool(meta.get("enabled", True))
            other_manifest = self._safe_get_manifest(
                resolver, self.presets_dir / other
            )
            other_cmd_templates = (
                [
                    tmpl
                    for tmpl in other_manifest.templates
                    if tmpl.get("type") == "command"
                    and isinstance(tmpl.get("name"), str)
                ]
                if other_manifest is not None
                else []
            )
            reg_skills = meta.get("registered_skills")
            if isinstance(reg_skills, list):
                reg_skills = self._infer_legacy_skill_provenance(
                    [n for n in reg_skills if isinstance(n, str)],
                    other,
                    active_ai or "",
                )
            if isinstance(reg_skills, dict):
                for other_agent, other_skills in reg_skills.items():
                    if not isinstance(other_agent, str) or not isinstance(
                        other_skills, list
                    ):
                        continue
                    other_cfg = registrar.AGENT_CONFIGS.get(other_agent)
                    other_native = bool(
                        other_cfg and other_cfg.get("extension") == "/SKILL.md"
                    )
                    other_dir = resolve_dir(other_agent, other_native)
                    if other_dir is None:
                        continue
                    agents_in_dir = survivor_dir_agents.setdefault(
                        (other, other_dir), []
                    )
                    if other_agent not in agents_in_dir:
                        agents_in_dir.append(other_agent)
                    for skill_name in other_skills:
                        if not isinstance(skill_name, str):
                            continue
                        matching = [
                            tmpl
                            for tmpl in other_cmd_templates
                            if skill_name
                            in self._skill_names_for_command(tmpl["name"])
                        ]
                        dependent = (
                            not enabled
                            and bool(matching)
                            and all(
                                tmpl.get("strategy", "replace") != "replace"
                                and (other, other_dir, tmpl["name"])
                                in disabled_composer_deps
                                for tmpl in matching
                            )
                        )
                        primary_cmd = (
                            matching[0]["name"] if len(matching) == 1 else None
                        )
                        survivor_entries.setdefault(
                            (other_dir, skill_name), []
                        ).append(
                            (
                                other,
                                enabled,
                                dependent,
                                {f"preset:{other}"},
                                other_agent,
                                primary_cmd,
                            )
                        )
            reg_cmds = meta.get("registered_commands")
            if isinstance(reg_cmds, dict):
                for other_agent, other_cmds in reg_cmds.items():
                    if not isinstance(other_agent, str) or not isinstance(
                        other_cmds, list
                    ):
                        continue
                    other_cfg = registrar.AGENT_CONFIGS.get(other_agent)
                    if not other_cfg or other_cfg.get("extension") != "/SKILL.md":
                        continue
                    other_dir = resolve_dir(other_agent, True)
                    if other_dir is None:
                        continue
                    agents_in_dir = survivor_dir_agents.setdefault(
                        (other, other_dir), []
                    )
                    if other_agent not in agents_in_dir:
                        agents_in_dir.append(other_agent)
                    for other_cmd in other_cmds:
                        if not isinstance(other_cmd, str):
                            continue
                        other_out = registrar._compute_output_name(
                            other_agent, other_cmd, other_cfg
                        )
                        other_outs = [other_out]
                        if other_out != other_cmd and registrar._is_safe_command_name(
                            other_cmd
                        ):
                            other_outs.append(other_cmd)
                        if other_manifest is None:
                            for cand in other_outs:
                                survivor_entries.setdefault(
                                    (other_dir, cand), []
                                ).append(
                                    (other, enabled, False, None, other_agent, None)
                                )
                            continue
                        matching = [
                            tmpl
                            for tmpl in other_cmd_templates
                            if tmpl["name"] == other_cmd
                            or other_cmd in (tmpl.get("aliases") or [])
                        ]
                        if not matching:
                            for cand in other_outs:
                                survivor_entries.setdefault(
                                    (other_dir, cand), []
                                ).append(
                                    (
                                        other,
                                        enabled,
                                        False,
                                        {f"{other}:.composed/{other_cmd}.md"},
                                        other_agent,
                                        None,
                                    )
                                )
                            continue
                        for tmpl in matching:
                            markers = {f"{other}:.composed/{tmpl['name']}.md"}
                            if isinstance(tmpl.get("file"), str):
                                markers.add(f"{other}:{tmpl['file']}")
                            dependent = (
                                not enabled
                                and tmpl.get("strategy", "replace") != "replace"
                                and (other, other_dir, tmpl["name"])
                                in disabled_composer_deps
                            )
                            primary_cmd = (
                                tmpl["name"] if other_cmd == tmpl["name"] else None
                            )
                            for cand in other_outs:
                                survivor_entries.setdefault(
                                    (other_dir, cand), []
                                ).append(
                                    (
                                        other,
                                        enabled,
                                        dependent,
                                        markers,
                                        other_agent,
                                        primary_cmd,
                                    )
                                )

        retiring_skill_marker = f"preset:{pack_id}"

        def retiring_sources_for(cmd_name: str) -> Set[str]:
            sources = {retiring_skill_marker}
            if retiring_manifest is None:
                sources.add(f"{pack_id}:.composed/{cmd_name}.md")
                return sources
            for tmpl in retiring_manifest.templates:
                if tmpl.get("type") != "command":
                    continue
                primary = tmpl.get("name")
                aliases = tmpl.get("aliases") or []
                if primary != cmd_name and cmd_name not in aliases:
                    continue
                if isinstance(primary, str):
                    sources.add(f"{pack_id}:.composed/{primary}.md")
                if isinstance(tmpl.get("file"), str):
                    sources.add(f"{pack_id}:{tmpl['file']}")
            return sources

        def read_source_and_mode(
            skills_dir: Path, skill_dir: Path
        ) -> tuple[Optional[str], Optional[int]]:
            if not self._validate_skill_subdir(
                skill_dir, create=False, skills_root=skills_dir
            ):
                return None, None
            try:
                # FileHelper reads a relative path against its root, so
                # name the file from the skills directory, not from a
                # project root that may itself be relative.
                with FileHelper(skills_dir) as files:
                    rel = Path(skill_dir.name) / "SKILL.md"
                    mode = files.file_mode(rel)
                    if mode is None:
                        return None, None
                    content = files.read_text(rel)
            except (OSError, ValueError):
                # Missing, unreadable, symlinked, not a regular file or not UTF-8.
                return None, None
            metadata = registrar.parse_frontmatter(content)[0].get("metadata")
            source = metadata.get("source") if isinstance(metadata, dict) else None
            return (source if isinstance(source, str) else None), mode

        def classify_survivor(
            skills_dir: Path, candidate: str, source: Optional[str]
        ) -> tuple[bool, bool, bool, List[tuple[str, str]]]:
            """Return ``(enabled_owner, disabled_independent, disabled_dependent, colliding_primaries)``."""
            if not isinstance(source, str):
                return False, False, False, []
            entries = survivor_entries.get((skills_dir, candidate), ())
            enabled_owner = False
            disabled_independent = False
            disabled_dependent = False
            colliding_primaries: List[tuple[str, str]] = []
            for (
                other,
                enabled,
                dependent,
                markers,
                _other_agent,
                primary_cmd,
            ) in entries:
                if markers is None:
                    # Exclude the retiring pack's explicit skill marker so a
                    # survivor named ``preset`` with a missing/invalid manifest
                    # cannot claim ``preset:<retiring-id>`` via prefix match.
                    matched = (
                        source.startswith(f"{other}:")
                        and source != retiring_skill_marker
                    )
                else:
                    matched = source in markers
                if not matched:
                    continue
                if enabled:
                    enabled_owner = True
                    if (
                        primary_cmd is not None
                        and (other, primary_cmd) not in colliding_primaries
                    ):
                        colliding_primaries.append((other, primary_cmd))
                elif dependent:
                    disabled_dependent = True
                else:
                    disabled_independent = True
            return (
                enabled_owner,
                disabled_independent,
                disabled_dependent,
                colliding_primaries,
            )

        def pick_survivor_renderer(other_id: str, skills_dir: Path) -> Optional[str]:
            agents = survivor_dir_agents.get((other_id, skills_dir), [])
            if active_ai and (
                active_ai in agents
                or (
                    effective_active_dir is not None
                    and skills_dir == effective_active_dir
                )
            ):
                return active_ai
            return sorted(agents)[0] if agents else None

        result: Dict[str, List[str]] = {}
        for agent, names in registered_commands.items():
            agent_config = registrar.AGENT_CONFIGS.get(agent)
            if (
                not isinstance(names, list)
                or not agent_config
                or agent_config.get("extension") != "/SKILL.md"
            ):
                result[agent] = names
                continue
            skills_dir = resolve_dir(agent, True)
            kept: List[str] = []
            for name in names:
                if skills_dir is None or not isinstance(name, str):
                    kept.append(name)
                    continue
                output = registrar._compute_output_name(agent, name, agent_config)
                outputs = [output]
                if output != name and registrar._is_safe_command_name(name):
                    outputs.append(name)
                any_survivor_registered = any(
                    survivor_entries.get((skills_dir, cand)) for cand in outputs
                )
                retiring_sources = retiring_sources_for(name)
                inspected = []
                any_handled = False
                for candidate in outputs:
                    src, mode = read_source_and_mode(
                        skills_dir, skills_dir / candidate
                    )
                    (
                        enabled_own,
                        disabled_indep,
                        disabled_dep,
                        colliding_primaries,
                    ) = classify_survivor(skills_dir, candidate, src)
                    retiring_own = (
                        isinstance(src, str) and src in retiring_sources
                    )
                    if (
                        enabled_own
                        or disabled_indep
                        or disabled_dep
                        or retiring_own
                    ):
                        any_handled = True
                    inspected.append(
                        (
                            candidate,
                            mode,
                            enabled_own,
                            disabled_indep,
                            disabled_dep,
                            retiring_own,
                            colliding_primaries,
                        )
                    )
                if not any_survivor_registered and not any_handled:
                    kept.append(name)
                    continue
                for (
                    candidate,
                    mode,
                    enabled_own,
                    disabled_indep,
                    disabled_dep,
                    retiring_own,
                    colliding_primaries,
                ) in inspected:
                    # An exact marker collision (e.g. a survivor named ``preset``
                    # whose source file is literally ``<retiring-id>`` matching
                    # ``preset:<retiring-id>``) is ambiguous: unlink the file
                    # and let reconciliation restore the registered survivor
                    # from its own command instead of keeping possibly removed
                    # instructions on disk.
                    if (enabled_own or disabled_indep) and not retiring_own:
                        continue
                    if not (disabled_dep or retiring_own):
                        continue
                    skill_file = skills_dir / candidate / "SKILL.md"
                    if retired_modes is not None and mode is not None:
                        retired_modes.setdefault(skill_file, mode)
                    unlink_in_directory(
                        skill_file,
                        root=(
                            self.project_root
                            if skill_file.is_relative_to(self.project_root)
                            else skills_dir
                        ),
                    )
                    if deleted_outputs is not None:
                        deleted_outputs.setdefault(skills_dir, set()).add(
                            candidate
                        )
                    if (
                        enabled_own
                        and retiring_own
                        and colliding_primaries
                        and restored_primary_owners is not None
                    ):
                        other_id, primary_cmd = colliding_primaries[0]
                        renderer = pick_survivor_renderer(other_id, skills_dir)
                        restored_names = restored_primary_owners.setdefault(
                            (skills_dir, renderer, other_id), {}
                        ).setdefault(primary_cmd, [])
                        if candidate not in restored_names:
                            restored_names.append(candidate)
            if kept:
                result[agent] = kept
        return result

    def _unambiguous_command_sources(
        self,
        pack_id: str,
        manifest: Optional["PresetManifest"],
        cmd_name: str,
        target_names: List[str],
    ) -> Dict[str, Set[str]]:
        """Return unambiguous ``metadata.source`` markers for ``cmd_name`` per skill dir.

        A marker proves ``pack_id`` rendered ``cmd_name`` into ``name`` only when:
        - ``<id>:.composed/<cmd_name>.md`` (names the command explicitly),
        - ``preset:<id>`` (when no other command of ``pack_id`` maps to ``name``), or
        - ``<id>:<file>`` (when no other command's primary name or alias in
          ``pack_id`` shares that file and maps to ``name``).
        """
        owned_sources_by_name: Dict[str, Set[str]] = {
            name: set() for name in target_names
        }
        if manifest is None:
            return owned_sources_by_name
        cmd_templates = [
            tmpl
            for tmpl in manifest.templates
            if tmpl.get("type") == "command"
            and isinstance(tmpl.get("name"), str)
        ]
        matching = [tmpl for tmpl in cmd_templates if tmpl["name"] == cmd_name]
        if not matching:
            return owned_sources_by_name
        other_templates = [
            tmpl for tmpl in cmd_templates if tmpl["name"] != cmd_name
        ]
        cmd_skill_names = set(self._skill_names_for_command(cmd_name))
        for name in target_names:
            if name not in cmd_skill_names:
                continue
            sources = owned_sources_by_name[name]
            sources.add(f"{pack_id}:.composed/{cmd_name}.md")
            if not any(
                name in self._skill_names_for_command(other["name"])
                for other in other_templates
            ):
                sources.add(f"preset:{pack_id}")
            for tmpl in matching:
                file_rel = tmpl.get("file")
                if not isinstance(file_rel, str):
                    continue
                if not any(
                    other.get("file") == file_rel
                    and any(
                        isinstance(candidate, str)
                        and name in self._skill_names_for_command(candidate)
                        for candidate in (
                            other["name"],
                            *(other.get("aliases") or []),
                        )
                    )
                    for other in other_templates
                ):
                    sources.add(f"{pack_id}:{file_rel}")
        return owned_sources_by_name

    def _surviving_owned_skills(
        self,
        command_names: List[str],
        presets_by_priority: List[Any],
        active_ai: Optional[str],
        active_skills_dir: Optional[Path],
    ) -> List[tuple[Path, Optional[str], str, str, str]]:
        """Recorded skill destinations of ``command_names`` still owned by a survivor.

        Reads each remaining preset's ``registered_skills`` (inferring per-agent
        provenance for legacy flat lists) and keeps the names whose ``SKILL.md``
        unambiguously carries that preset's marker for an affected command, as
        ``(skills_dir, agent, owner_id, command_name, skill_name)`` tuples.

        For native skill agents command registration writes the same file
        first, marked ``<id>:<file>``, and records it in
        ``registered_commands``. When the skills phase then fails, that is
        all there is, so those records and that marker (when unambiguous for
        the command's own file, raw or composed) count as well.

        Several agents can record one physical directory (agy/codex/zed all
        use ``.agents/skills``), so each file is returned once, with the
        agent to render it: the active agent when it uses that directory,
        otherwise the first recorded agent in sorted order, as
        ``_unregister_skills`` and the alias pass choose.
        """
        registrar = self._command_registrar()
        registrar._ensure_configs()
        active_native_dir = self._active_native_skills_dir(
            active_ai, active_skills_dir, registrar.AGENT_CONFIGS
        )
        effective_active_dir = (
            active_skills_dir
            if active_skills_dir is not None
            else active_native_dir
        )
        resolver = PresetResolver(self.project_root)
        affected: Dict[str, List[str]] = {}
        for cmd_name in command_names:
            for name in self._skill_names_for_command(cmd_name):
                cmds = affected.setdefault(name, [])
                if cmd_name not in cmds:
                    cmds.append(cmd_name)
        found: List[tuple[Path, Optional[str], str, str, str]] = []
        for pack_id, meta in presets_by_priority:
            if not isinstance(meta, dict):
                continue
            recorded = meta.get("registered_skills")
            if isinstance(recorded, list):
                recorded = self._infer_legacy_skill_provenance(
                    [n for n in recorded if isinstance(n, str)],
                    pack_id,
                    active_ai or "",
                )
            recorded_commands = meta.get("registered_commands")
            groups: Dict[Path, Dict[str, List[str]]] = {}
            for from_commands, records in (
                (False, recorded if isinstance(recorded, dict) else {}),
                (True, recorded_commands if isinstance(recorded_commands, dict) else {}),
            ):
                for agent, names in records.items():
                    if not isinstance(agent, str) or not isinstance(names, list):
                        continue
                    agent_config = registrar.AGENT_CONFIGS.get(agent)
                    native_skill_agent = bool(
                        agent_config and agent_config.get("extension") == "/SKILL.md"
                    )
                    if from_commands and not native_skill_agent:
                        continue
                    if agent == active_ai:
                        skills_dir = (
                            active_skills_dir
                            if active_skills_dir is not None or not native_skill_agent
                            else self._safe_skills_dir_for_agent(agent)
                        )
                    else:
                        skills_dir = self._safe_skills_dir_for_agent(agent)
                    if skills_dir is None:
                        continue
                    group = groups.setdefault(skills_dir, {"agents": [], "names": []})
                    if agent not in group["agents"]:
                        group["agents"].append(agent)
                    for name in names:
                        if not isinstance(name, str):
                            continue
                        if from_commands:
                            # Only a primary command: aliases are reconciled
                            # by ``_reconcile_preset_aliases``. Probe both the
                            # modern output name and the supported legacy dotted
                            # spelling so a legacy primary skill left behind
                            # after a failed skills phase is still reconciled.
                            output = registrar._compute_output_name(
                                agent, name, agent_config
                            )
                            if name not in affected.get(output, ()):
                                continue
                            candidates = [output]
                            if (
                                output != name
                                and registrar._is_safe_command_name(name)
                            ):
                                candidates.append(name)
                        else:
                            candidates = [name]
                        for candidate in candidates:
                            if (
                                candidate in affected
                                and candidate not in group["names"]
                            ):
                                group["names"].append(candidate)
            manifest = self._safe_get_manifest(resolver, self.presets_dir / pack_id)
            if manifest is None:
                continue
            for skills_dir, group in groups.items():
                agents = group["agents"]
                agent = (
                    active_ai
                    if active_ai
                    and (
                        active_ai in agents
                        or (
                            effective_active_dir is not None
                            and skills_dir == effective_active_dir
                        )
                    )
                    else sorted(agents)[0]
                )
                for name in group["names"]:
                    skill_dir = skills_dir / name
                    if not self._validate_skill_subdir(
                        skill_dir, create=False, skills_root=skills_dir
                    ):
                        continue
                    try:
                        with FileHelper(skills_dir) as files:
                            content = files.read_text(Path(name) / "SKILL.md")
                    except (OSError, ValueError):
                        continue
                    metadata = registrar.parse_frontmatter(content)[0].get("metadata")
                    source = metadata.get("source") if isinstance(metadata, dict) else None
                    if not isinstance(source, str):
                        continue
                    matched_cmds = [
                        cmd_name
                        for cmd_name in affected[name]
                        if source
                        in self._unambiguous_command_sources(
                            pack_id, manifest, cmd_name, [name]
                        ).get(name, ())
                    ]
                    if len(matched_cmds) == 1:
                        found.append(
                            (skills_dir, agent, pack_id, matched_cmds[0], name)
                        )
        return found

    def _remove_owned_skills(
        self, skills_dir: Path, cmd_name: str, skill_names: List[str]
    ) -> None:
        """Delete ``cmd_name``'s preset-rendered skills among ``skill_names`` (journaled).

        A skill is removed only when its ``SKILL.md`` source marker
        unambiguously proves an installed preset rendered ``cmd_name`` into
        that output directory: ``<id>:.composed/<cmd_name>.md`` (which names
        the command explicitly), ``preset:<id>`` (when the preset supplies
        ``cmd_name`` and no other command of the preset maps to the same skill
        directory), or ``<id>:<file>`` (when no other command's primary name
        or alias in the preset shares that file and output directory).
        Anything else or any ambiguous ownership is preserved.
        """
        from ..integrations._file_changes import unlink_in_directory

        registrar = self._command_registrar()
        resolver = PresetResolver(self.project_root)
        target_names = list(dict.fromkeys(skill_names))
        owned_sources_by_name: Dict[str, Set[str]] = {
            name: set() for name in target_names
        }
        for pack_id in self.registry.list():
            manifest = self._safe_get_manifest(resolver, self.presets_dir / pack_id)
            if not manifest:
                continue
            pack_sources = self._unambiguous_command_sources(
                pack_id, manifest, cmd_name, target_names
            )
            for name, sources in pack_sources.items():
                owned_sources_by_name[name].update(sources)
        for name in target_names:
            owned_sources = owned_sources_by_name[name]
            if not owned_sources:
                continue
            skill_dir = skills_dir / name
            skill_file = skill_dir / "SKILL.md"
            if not self._validate_skill_subdir(
                skill_dir, create=False, skills_root=skills_dir
            ):
                continue
            try:
                # Named from the helper's root: see _drop_survivor_owned_aliases.
                with FileHelper(skills_dir) as files:
                    content = files.read_text(Path(name) / "SKILL.md")
            except (OSError, ValueError):
                # Missing, unreadable, not a regular file or not UTF-8.
                continue
            metadata = registrar.parse_frontmatter(content)[0].get("metadata")
            source = metadata.get("source") if isinstance(metadata, dict) else None
            if isinstance(source, str) and source in owned_sources:
                unlink_in_directory(
                    skill_file,
                    root=self.project_root if skill_file.is_relative_to(self.project_root) else skills_dir,
                )

    def _resolve_agent_skills_dir(self, agent_name: str) -> Path:
        """Resolve the real skill output directory for an integration."""
        from .. import _get_skills_dir as _project_skills_dir

        registrar = self._command_registrar()
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

    @project_registration
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
        opts = load_init_options(self.project_root)
        if isinstance(opts, dict) and opts.get("ai") == "generic":
            return None
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
                    "version": manifest.version,
                    "extension_id": manifest.id,
                    "extension_dir": ext_root,
                    "resources": cmd_info.get("resources", []),
                }
                modern_skill_name, legacy_skill_name = self._skill_names_for_command(cmd_name)
                restore_index.setdefault(modern_skill_name, restore_info)
                if legacy_skill_name != modern_skill_name:
                    restore_index.setdefault(legacy_skill_name, restore_info)

        return restore_index

    @project_registration
    def _register_skills(
        self,
        manifest: "PresetManifest",
        preset_dir: Path,
        *,
        target_dir: Optional[Path] = None,
        target_agent: Optional[str] = None,
        only_skill_names: Optional[Set[str]] = None,
        content_overrides: Optional[Dict[str, str]] = None,
        new_file_modes: Optional[Dict[Path, int]] = None,
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
            only_skill_names: When given, write only these skill
                directory names; any other existing modern or legacy
                skill for the same command is left untouched.
            content_overrides: ``{command_name: content}`` to render instead
                of the preset's command file or ``.composed`` cache, for a
                composition that has already been resolved by the caller.
            new_file_modes: ``{skill_file: permission bits}`` for skills that
                stand in for a file deleted earlier in the same removal.

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
        registrar = self._command_registrar()
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
            override = (content_overrides or {}).get(cmd_name)
            source_rel = Path(cmd_file_rel)
            if override is None:
                with FileHelper(preset_dir) as files:
                    if files.file_mode(source_rel) is None:
                        continue
                    # Use composed content if available (written by
                    # _register_commands for commands with non-replace
                    # strategies), otherwise the original.
                    composed_rel = Path(".composed") / f"{cmd_name}.md"
                    try:
                        if files.file_mode(composed_rel) is not None:
                            source_rel = composed_rel
                    except (FileNotFoundError, NotADirectoryError):
                        pass

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
            if only_skill_names is not None:
                target_skill_names = [
                    name for name in target_skill_names if name in only_skill_names
                ]
            if not target_skill_names:
                continue

            # Parse the command file (skip obsolete .composed cache when
            # caller already supplied the resolved composition).
            if override is not None:
                content = override
            else:
                with FileHelper(preset_dir) as files:
                    content = files.read_text(source_rel)
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
            # A cached composition can outlive its base (e.g. one removed
            # while its composer was disabled), so the resolver decides even
            # when the cache exists.
            if (
                override is None
                and effective_strategy != "replace"
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
                    version=manifest.version,
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
                    skills_dir,
                    skill_file,
                    skill_content,
                    preserve_mode=True,
                    new_file_mode=(new_file_modes or {}).get(skill_file),
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

        registrar = self._command_registrar()
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
                try:
                    with FileHelper(resolved_dir) as files:
                        content = files.read_text(Path(name) / "SKILL.md")
                except (OSError, ValueError):
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

    def _skill_file_modes(
        self, registered_skills: Union[Dict[str, List[str]], List[str]]
    ) -> Dict[Path, int]:
        """Permission bits of the ``SKILL.md`` files a preset has registered.

        Removal deletes a preset's skill when no core or extension command
        backs it, and reconciliation then writes the next winner's skill as
        a new file. Taken before the deletion, these bits let that file
        stay as private as the one it stands in for.
        """
        if isinstance(registered_skills, dict):
            entries = [
                (self._safe_skills_dir_for_agent(agent), names)
                for agent, names in registered_skills.items()
                if isinstance(agent, str)
            ]
        else:
            entries = [(self._get_skills_dir(), registered_skills)]
        modes: Dict[Path, int] = {}
        for skills_dir, names in entries:
            if skills_dir is None or not isinstance(names, list):
                continue
            for name in names:
                if not self._is_safe_registry_skill_name(name):
                    continue
                skill_file = skills_dir / name / "SKILL.md"
                try:
                    with FileHelper(skills_dir) as files:
                        mode = files.file_mode(Path(name) / "SKILL.md")
                except (OSError, ValueError):
                    # Unreadable, or not a regular file reached without links.
                    continue
                if mode is not None:
                    modes[skill_file] = mode
        return modes

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
        from ..shared_infra import _ensure_safe_shared_directory

        if agent_name not in self._command_registrar().AGENT_CONFIGS:
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

            active_skills_dir = self._get_skills_dir()
            try:
                registrar = self._command_registrar()
                registrar._ensure_configs()
                agent_configs = registrar.AGENT_CONFIGS
            except ImportError:
                agent_configs = {}
            active_native_dir = self._active_native_skills_dir(
                active_agent, active_skills_dir, agent_configs
            )
            effective_active_dir = (
                active_skills_dir
                if active_skills_dir is not None
                else active_native_dir
            )

            restored: Dict[Path, tuple[Optional[str], List[str]]] = {}
            for skills_dir, group in groups.items():
                agents = group["agents"]
                renderer_agent = (
                    active_agent
                    if active_agent
                    and (
                        active_agent in agents
                        or (
                            effective_active_dir is not None
                            and skills_dir == effective_active_dir
                        )
                    )
                    else sorted(agents)[0]
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


        registrar = self._command_registrar()
        marker = f"preset:{pack_id}"
        override_sources: Dict[str, str] = {}
        manifest = self._safe_get_manifest(
            PresetResolver(self.project_root),
            self.presets_dir / pack_id,
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
                from ..integrations._file_changes import unlink_in_directory

                unlink_in_directory(
                    skill_file,
                    root=self.project_root if skill_file.is_relative_to(self.project_root) else skills_dir,
                )

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

    @staticmethod
    def _warn_unrestored_skill_resources(
        skill_name: str, extension_dir: Path, exc: BaseException
    ) -> None:
        """Warn that a skill kept preset content because its resources are unresolved.

        The command file itself was read; the extension's declared ``resources``
        no longer resolve. As for an unreadable source, leaving the skill in
        place is the safe recovery, so say what is wrong and where to fix it.
        """
        import warnings

        warnings.warn(
            f"Skill '{skill_name}' still contains the removed preset's content: "
            f"the resources declared by its extension command could not be "
            f"resolved in '{extension_dir}' ({exc.__class__.__name__}: {exc}). "
            f"The skill was left in place rather than deleted. Restore the "
            f"missing resource in that extension or fix its 'resources' in "
            f"extension.yml, then re-run 'specify preset add'/'specify preset "
            f"remove' to refresh it.",
            stacklevel=2,
        )

    @project_registration
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
        from .. import SKILL_DESCRIPTIONS, get_speckit_version
        from ..integrations import get_integration
        from ..shared_infra import _write_shared_text

        # Locate core command templates from the project's installed templates
        core_templates_dir = self.project_root / ".specify" / "templates" / "commands"
        registrar = self._command_registrar()
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
            # writes/removals operate through it (#2948).
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
                # rather than falling through to the removal below, which
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
                    version=get_speckit_version(),
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
                _write_shared_text(
                    skills_dir, skill_file, skill_content, preserve_mode=True
                )
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
                resources = extension_restore.get("resources", [])
                resolved_resources = []
                if resources:
                    from ..extensions import ValidationError
                    from ..extensions._skill_resources import resolve_skill_resources

                    try:
                        resolved_resources = resolve_skill_resources(
                            extension_restore["extension_dir"], resources
                        )
                    except ValidationError as exc:
                        self._warn_unrestored_skill_resources(
                            skill_name, extension_restore["extension_dir"], exc
                        )
                        continue
                else:
                    body = registrar.rewrite_extension_paths(
                        body, extension_restore["extension_id"],
                        extension_restore["extension_dir"],
                    )
                if isinstance(selected_ai, str):
                    body = registrar.resolve_skill_placeholders(
                        selected_ai, frontmatter, body, self.project_root,
                        rewrite_paths=not bool(resources),
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
                    version=extension_restore.get("version"),
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
                _write_shared_text(
                    skills_dir, skill_file, skill_content, preserve_mode=True
                )
                if resources:
                    import copy
                    from ..extensions import ExtensionRegistry
                    from ..extensions._skill_resources import (
                        deliver_skill_resources, recorded_resource_hashes,
                    )

                    registry = ExtensionRegistry(self.project_root / ".specify" / "extensions")
                    ext_id = extension_restore["extension_id"]
                    metadata = registry.get(ext_id)
                    previous = recorded_resource_hashes(metadata)
                    hashes = copy.deepcopy(previous)
                    deliver_skill_resources(
                        self.project_root, ext_id, skills_dir, skill_name,
                        extension_restore["extension_dir"], resolved_resources, previous, hashes,
                    )
                    if metadata is not None and hashes != previous:
                        registry.update(ext_id, {"skill_resource_hashes": hashes})
                mutated_names.append(skill_name)
            else:
                # No core or extension template — remove only the generated file
                from ..integrations._file_changes import unlink_in_directory

                unlink_in_directory(
                    skill_file,
                    root=self.project_root if skill_file.is_relative_to(self.project_root) else skills_dir,
                )
                mutated_names.append(skill_name)

        return mutated_names
