"""Agent command registration and reconciliation for installed presets."""

import copy
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

if TYPE_CHECKING:
    from ..agents import CommandRegistrar


from .._init_options import (
    MISSING_INIT_OPTIONS_FILE,
    is_ai_skills_enabled,
    load_init_options,
    resolve_active_agent_for_registration,
)
from ..extensions import ExtensionRegistry
from ._manifest import PresetManifest
from ._resolver import PresetResolver


def _substitute_core_template(
    body: str,
    cmd_name: str,
    project_root: "Path",
    registrar: "CommandRegistrar",
) -> "tuple[str, dict]":
    """Substitute {CORE_TEMPLATE} with the body of the installed core command template.

    Args:
        body: Preset command body (may contain {CORE_TEMPLATE} placeholder).
        cmd_name: Full command name (e.g. "speckit.git.feature" or "speckit.specify").
        project_root: Project root path.
        registrar: CommandRegistrar instance for parse_frontmatter.

    Returns:
        A tuple of (body, core_frontmatter) where body has {CORE_TEMPLATE} replaced
        by the core template body and core_frontmatter holds the core template's parsed
        frontmatter (so callers can inherit scripts/agent_scripts from it).  Both are
        unchanged / empty when the placeholder is absent or the core template file does
        not exist or cannot be read.
    """
    if "{CORE_TEMPLATE}" not in body:
        return body, {}

    # Derive the short name (strip "speckit." prefix) used by core command templates.
    short_name = cmd_name
    if short_name.startswith("speckit."):
        short_name = short_name[len("speckit."):]

    resolver = PresetResolver(project_root)
    # Resolution order for the core template:
    # 1. resolve_core(cmd_name) — covers tier-1 project overrides and tier-3/4
    #    name-based lookup (file named <cmd_name>.md).  Checked first so that a
    #    local override always wins, even for extension commands.
    # 2. resolve_extension_command_via_manifest(cmd_name) — manifest-based tier-3
    #    fallback for extension commands whose file is named differently from the
    #    command name (e.g. speckit.selftest.extension → commands/selftest.md).
    # 3. resolve_core(short_name) — core template fallback using the unprefixed
    #    name (e.g. specify → templates/commands/specify.md).
    # resolve_core() skips installed presets (tier 2) to prevent accidental nesting
    # where another preset's wrap output is mistaken for the real core.
    core_file = (
        resolver.resolve_core(cmd_name, "command")
        or resolver.resolve_extension_command_via_manifest(cmd_name)
        or resolver.resolve_core(short_name, "command")
    )
    if core_file is None:
        return body, {}

    # Treat an unreadable/undecodable core template like a missing one so a
    # single corrupted project override cannot crash command registration —
    # the wrap-strategy callers already skip an unreadable preset source with
    # a warning (CommandRegistrar.register_pack).
    try:
        core_content = core_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        import warnings

        warnings.warn(
            f"Ignoring core template for command '{cmd_name}': could not read "
            f"'{core_file.name}' ({exc.__class__.__name__}: {exc}).",
            stacklevel=2,
        )
        return body, {}

    core_frontmatter, core_body = registrar.parse_frontmatter(core_content)
    return body.replace("{CORE_TEMPLATE}", core_body), core_frontmatter


class _PresetCommandMethods:
    """Command artifact methods shared through PresetManager's lifecycle state."""

    def _register_commands(
        self,
        manifest: PresetManifest,
        preset_dir: Path
    ) -> Dict[str, List[str]]:
        """Register preset command overrides with all detected AI agents.

        Scans the preset's templates for type "command", reads each command
        file, and writes it to every detected agent directory using the
        CommandRegistrar from the agents module.

        When a command uses a composition strategy (prepend, append, wrap),
        the content is composed with the lower-priority command before
        registration.

        Args:
            manifest: Preset manifest
            preset_dir: Installed preset directory

        Returns:
            Dictionary mapping agent names to lists of registered command names
        """
        command_templates = [
            t for t in manifest.templates if t.get("type") == "command"
        ]
        if not command_templates:
            return {}

        # A preset command template always ships its own body, so it is
        # self-contained and scaffolds regardless of whether any similarly
        # named extension is installed. Namespaced names (speckit.<ns>.<cmd>)
        # are treated exactly like short names (speckit.<cmd>) — they are NOT
        # filtered out just because ``.specify/extensions/<ns>/`` is absent.
        # The only command that cannot be materialized is a composition
        # (prepend/append/wrap) with no base layer to compose onto; that case
        # is handled per-command below (warn + skip), not by dropping names up
        # front.
        # Handle composition strategies: resolve composed content for non-replace commands
        resolver = PresetResolver(self.project_root)
        composed_dir = None
        commands_to_register = []
        for cmd in command_templates:
            strategy = cmd.get("strategy", "replace")
            if strategy != "replace":
                # Only pre-compose if this preset is the top composing layer.
                # If a higher-priority replace already wins, skip composition
                # here — reconciliation will write the correct content.
                layers = resolver.collect_all_layers(cmd["name"], "command")
                top_layer_is_ours = (
                    layers and layers[0]["path"].is_relative_to(preset_dir)
                )
                if top_layer_is_ours:
                    composed = resolver.resolve_content(cmd["name"], "command")
                    if composed is not None:
                        if composed_dir is None:
                            composed_dir = preset_dir / ".composed"
                            composed_dir.mkdir(parents=True, exist_ok=True)
                        composed_file = composed_dir / f"{cmd['name']}.md"
                        composed_file.write_text(composed, encoding="utf-8")
                        commands_to_register.append({
                            **cmd,
                            "file": f".composed/{cmd['name']}.md",
                        })
                    else:
                        # No base layer to compose onto (e.g. the command it
                        # would wrap comes from an extension that isn't
                        # installed). Warn and skip this single command rather
                        # than aborting the whole install — mirrors the
                        # "composed is None" branch in
                        # _reconcile_composed_commands so command-mode and
                        # reconciliation behave identically.
                        import warnings
                        warnings.warn(
                            f"Command '{cmd['name']}' uses '{strategy}' "
                            f"strategy but no base command layer exists to "
                            f"compose onto; skipping. Provide a lower-priority "
                            f"preset, extension, or core command for it before "
                            f"using composition strategies.",
                            stacklevel=2,
                        )
                        continue
                else:
                    # Not the top layer — register raw file; reconciliation
                    # will overwrite with the correct composed/winning content.
                    # Note: CommandRegistrar may process frontmatter strategy: wrap
                    # from the raw file (legacy compat), but reconciliation runs
                    # immediately after install and corrects the final output.
                    commands_to_register.append(cmd)
            else:
                commands_to_register.append(cmd)

        try:
            from ..agents import CommandRegistrar
        except ImportError:
            return {}

        registrar = CommandRegistrar()

        # Single-active rule (#2948): preset command overrides register for
        # the active integration only. A project without a recorded active
        # integration (init-options.json does not exist at all — a legacy
        # pre-init-options layout or direct library use) falls back to
        # detection-based registration for all agents. A recorded key with
        # no registrar config (e.g. "generic") naturally yields no matches
        # via only_agent instead of falling back.
        #
        # An init-options.json that exists but is corrupted, unreadable, or
        # has a malformed/empty "ai" value must not be treated the same as
        # "no file" — that would silently reintroduce all-agent
        # registration. Fail closed (register nothing) instead.
        resolved_agent = resolve_active_agent_for_registration(self.project_root)
        if resolved_agent is MISSING_INIT_OPTIONS_FILE:
            active_agent = None
        elif resolved_agent is None:
            return {}
        else:
            active_agent = resolved_agent
            # Mirror the extension path's ai_skills guard: when the active
            # agent is a command-backed integration (extension != "/SKILL.md")
            # running in skills mode, its preset command overrides render as
            # skills via _register_skills, not as command files. Command-mode
            # and skills-mode artifacts are mutually exclusive — writing both
            # (e.g. `integration use copilot` with `--skills`) leaves a stale
            # command file alongside the SKILL.md that is actually active.
            init_options = load_init_options(self.project_root)
            agent_config = registrar.AGENT_CONFIGS.get(active_agent)
            if (
                agent_config
                and is_ai_skills_enabled(init_options)
                and agent_config.get("extension") != "/SKILL.md"
            ):
                return {}

        return registrar.register_commands_for_all_agents(
            commands_to_register,
            manifest.id,
            preset_dir,
            self.project_root,
            create_missing_active_skills_dir=True,
            only_agent=active_agent,
        )

    def register_enabled_presets_for_agent(self, agent_name: str) -> None:
        """Re-register enabled presets' command overrides and skills for ``agent_name``.

        Mirrors ``ExtensionManager.register_enabled_extensions_for_agent`` for
        presets (#2948): ``integration use`` / ``switch`` call this for the
        newly active agent so a preset installed while a different
        integration was active gets rescaffolded on activation, instead of
        writing artifacts for inactive integrations at install time.
        ``_register_commands`` / ``_register_skills`` already resolve the
        active integration from init-options themselves, so this re-runs them
        for every enabled preset and merges the fresh result for
        ``agent_name`` into its stored registry metadata.

        Presets are processed in *reverse* priority order (lowest-precedence
        first). Each pass overwrites the same target command/skill files, so
        writing the highest-precedence preset last is what makes it win when
        two enabled presets override the same command — matching the
        priority stack documented for ``list_by_priority()``.
        """
        if not agent_name:
            return

        # Resolve once: whether agent_name is a command-backed integration
        # (extension != "/SKILL.md") currently running in skills mode, or
        # vice versa. Native skill-only agents (extension == "/SKILL.md",
        # e.g. claude/codex) have no command/skill toggle at all — both
        # registered_commands and registered_skills legitimately co-exist
        # for them by design, so this restriction only applies to
        # command-backed integrations.
        try:
            from ..agents import CommandRegistrar

            agent_config = CommandRegistrar().AGENT_CONFIGS.get(agent_name)
        except ImportError:
            agent_config = None
        is_command_backed = bool(agent_config) and agent_config.get("extension") != "/SKILL.md"
        ai_skills_now = is_command_backed and is_ai_skills_enabled(
            load_init_options(self.project_root)
        )

        resolver = PresetResolver(self.project_root)
        affected_cmd_names: set = set()
        presets_by_priority = list(self.registry.list_by_priority())
        winning_pack_by_command: Dict[str, str] = {}
        winning_source_by_command: Dict[str, Path] = {}
        project_override_commands: set[str] = set()
        for candidate_pack_id, _candidate_metadata in presets_by_priority:
            candidate_manifest = resolver._get_manifest(
                self.presets_dir / candidate_pack_id
            )
            if candidate_manifest is None:
                continue
            for template in candidate_manifest.templates:
                command_name = template.get("name")
                if (
                    template.get("type") == "command"
                    and isinstance(command_name, str)
                ):
                    if (
                        resolver.overrides_dir / f"{command_name}.md"
                    ).is_file():
                        project_override_commands.add(command_name)
                    winning_pack_by_command.setdefault(
                        command_name, candidate_pack_id
                    )
                    source_file = template.get("file")
                    if isinstance(source_file, str):
                        winning_source_by_command.setdefault(
                            command_name,
                            self.presets_dir
                            / candidate_pack_id
                            / source_file,
                        )

        pending_command_cleanups: List[
            tuple[
                str,
                Dict[str, List[str]],
                List[str],
                Dict[str, str],
            ]
        ] = []
        successful_skill_replacements: set[tuple[str, str]] = set()
        pending_skill_cleanups: List[
            tuple[
                str,
                Path,
                Dict[str, List[str]],
                List[str],
                Dict[str, str],
            ]
        ] = []
        successful_command_replacements: set[tuple[str, str]] = set()
        for pack_id, metadata in reversed(presets_by_priority):
            pack_dir = self.presets_dir / pack_id
            manifest = resolver._get_manifest(pack_dir)
            if manifest is None:
                continue

            # Registration can write one command and then fail on a later
            # template. Record names first so final reconciliation can repair
            # any partial writes even when _register_commands never returns.
            for tmpl in manifest.templates:
                name = tmpl.get("name")
                if tmpl.get("type") == "command" and isinstance(name, str):
                    affected_cmd_names.add(name)

            # Isolate per-preset failures: one preset that fails to register
            # must not abort registration of the remaining enabled presets.
            try:
                registered_commands = self._register_commands(manifest, pack_dir)
                registered_command_names = set(
                    registered_commands.get(agent_name) or []
                )
                for tmpl in manifest.templates:
                    if tmpl.get("type") != "command":
                        continue
                    primary_name = tmpl.get("name")
                    if (
                        isinstance(primary_name, str)
                        and primary_name in registered_command_names
                    ):
                        successful_command_replacements.add(
                            (pack_id, primary_name)
                        )
                existing_commands = metadata.get("registered_commands", {})
                if not isinstance(existing_commands, dict):
                    existing_commands = {}
                merged_commands = copy.deepcopy(existing_commands)
                # Toggled command -> skills for this same agent:
                # _register_commands's ai_skills guard just made this a
                # no-op, but the command file this preset wrote while
                # command mode was active is still on disk and still
                # tracked. Do NOT unregister it yet — _register_skills()
                # below is an independently fallible replacement step, and
                # deleting the old artifact before it succeeds would leave
                # neither the old command file nor a new skill file if
                # skills registration raises. The old artifact is only
                # removed after the skills phase below completes without
                # raising, preserving command/skill mutual exclusion while
                # never leaving a transient failure with nothing in place
                # (#2948).
                stale_command_names: Optional[List[str]] = None
                if registered_commands.get(agent_name):
                    existing_names = merged_commands.get(agent_name, [])
                    merged_commands[agent_name] = existing_names + [
                        name
                        for name in registered_commands[agent_name]
                        if name not in existing_names
                    ]
                elif ai_skills_now and merged_commands.get(agent_name):
                    stale_command_names = merged_commands[agent_name]
                # Persist the commands phase immediately, mirroring
                # install_from_directory(): _register_skills is an
                # independently fallible phase, and if it raises, the files
                # the commands phase already wrote to disk must still be
                # tracked so preset removal can clean them up (#2948).
                if merged_commands != existing_commands:
                    self.registry.update(pack_id, {"registered_commands": merged_commands})

                registered_skills = self._register_skills(manifest, pack_dir)
                replaced_skill_names = set(registered_skills.get(agent_name) or [])
                for tmpl in manifest.templates:
                    if tmpl.get("type") != "command":
                        continue
                    primary_name = tmpl.get("name")
                    if not isinstance(primary_name, str):
                        continue
                    modern_name, legacy_name = self._skill_names_for_command(
                        primary_name
                    )
                    if (
                        modern_name in replaced_skill_names
                        or legacy_name in replaced_skill_names
                    ):
                        successful_skill_replacements.add(
                            (pack_id, primary_name)
                        )
                raw_existing_skills = metadata.get("registered_skills")
                if isinstance(raw_existing_skills, list) and raw_existing_skills:
                    # Legacy flat-list value: don't assume agent_name wrote
                    # every name (the first post-upgrade operation may be a
                    # direct switch to a different skill-mode agent) —
                    # infer real ownership from on-disk provenance instead
                    # (#2948).
                    existing_skills = self._infer_legacy_skill_provenance(
                        [n for n in raw_existing_skills if isinstance(n, str)],
                        pack_id,
                        fallback_agent=agent_name,
                    )
                else:
                    existing_skills = self._normalize_registered_skills(
                        raw_existing_skills, fallback_agent=agent_name
                    )
                merged_skills = copy.deepcopy(existing_skills)
                if registered_skills.get(agent_name):
                    existing_names = merged_skills.get(agent_name, [])
                    merged_skills[agent_name] = existing_names + [
                        name
                        for name in registered_skills[agent_name]
                        if name not in existing_names
                    ]
                elif is_command_backed and not ai_skills_now and merged_skills.get(agent_name):
                    # Mirror image: toggled skills -> command for this same
                    # agent. _get_skills_dir() no longer resolves a skills
                    # directory once ai_skills is off, so _register_skills
                    # is a no-op — but the SKILL.md this preset wrote while
                    # skills mode was active is still tracked and still on
                    # disk. Restore/remove it narrowly for this agent. This
                    # direction is already register-new-then-remove-old:
                    # _register_commands (the replacement) ran unconditionally
                    # above and only reaches here once it has already
                    # succeeded — but that call can still have returned
                    # empty or partial results (missing source template,
                    # safety-validation skip, corrupted manifest), so only
                    # retire the subset of stale skills whose corresponding
                    # command name was actually returned for this agent;
                    # anything unreplaced stays tracked and on disk (#2948).
                    stale_skill_names = merged_skills[agent_name]
                    skill_to_primary: Dict[str, str] = {}
                    for tmpl in manifest.templates:
                        if tmpl.get("type") != "command":
                            continue
                        primary_name = tmpl.get("name")
                        if not isinstance(primary_name, str):
                            continue
                        modern_name, legacy_name = self._skill_names_for_command(
                            primary_name
                        )
                        skill_to_primary[modern_name] = primary_name
                        skill_to_primary[legacy_name] = primary_name
                    pending_skill_cleanups.append(
                        (
                            pack_id,
                            pack_dir,
                            merged_skills,
                            stale_skill_names,
                            skill_to_primary,
                        )
                    )
                # A legacy flat-list registered_skills value (predating
                # per-agent provenance) must migrate to the dict format on
                # disk even when the rescaffolded names are unchanged from
                # what the list already held — comparing only the
                # *normalized* forms would otherwise treat that as a no-op
                # and leave the raw un-migrated list in the registry, which
                # later removal/switch handling treats as legacy
                # best-effort (restoring only the currently active agent's
                # directory) instead of per-agent provenance (#2948).
                needs_migration = (
                    isinstance(raw_existing_skills, list) and raw_existing_skills
                )
                if merged_skills != existing_skills or needs_migration:
                    self.registry.update(pack_id, {"registered_skills": merged_skills})

                # The skills phase above completed without raising, but a
                # non-raising result can still be empty or partial (missing
                # source template, safety-validation skip, corrupted
                # manifest) — retiring every stale command purely on "did
                # not raise" would delete a command whose replacement skill
                # never actually landed, leaving neither artifact. Only
                # retire the subset of stale commands whose corresponding
                # skill name was actually returned for this agent; anything
                # unreplaced stays tracked and on disk (#2948).
                if stale_command_names:
                    # Commands may carry aliases (CommandRegistrar.register_
                    # commands() tracks and returns primary + alias names
                    # flattened together into one list), but _register_
                    # skills() only ever renders/returns the *primary*
                    # command name's skill — running an alias's own name
                    # through _skill_names_for_command() never matches
                    # anything real, so an alias would stay tracked/on-disk
                    # forever even after its primary's skill replacement
                    # landed. Map each stale name back to its template's
                    # primary via the manifest so the whole primary+alias
                    # group is retired or kept together, based solely on
                    # whether the *primary*'s skill replacement actually
                    # landed (#2948).
                    alias_to_primary: Dict[str, str] = {}
                    for tmpl in manifest.templates:
                        if tmpl.get("type") != "command":
                            continue
                        primary_name = tmpl.get("name")
                        if not isinstance(primary_name, str):
                            continue
                        for alias in tmpl.get("aliases", []):
                            if isinstance(alias, str):
                                alias_to_primary[alias] = primary_name

                    pending_command_cleanups.append(
                        (
                            pack_id,
                            merged_commands,
                            stale_command_names,
                            alias_to_primary,
                        )
                    )
            except Exception as pack_err:
                from .. import _print_cli_warning

                _print_cli_warning(
                    "register preset artifacts for",
                    "preset",
                    pack_id,
                    pack_err,
                    continuing="Continuing with the remaining presets.",
                )
                continue

        # Registration writes each preset's raw layer. Reconcile before
        # retiring opposite-mode artifacts so project overrides and composed
        # winners are materialized first, and so cleanup runs last instead of
        # being undone by skill reconciliation.
        reconciled_commands: set[str] = set()
        reconciled_skills: set[str] = set()
        if affected_cmd_names:
            try:
                reconciled_commands = self._reconcile_composed_commands(
                    list(affected_cmd_names), target_agent=agent_name
                )
                reconciled_skills = self._reconcile_skills(
                    list(affected_cmd_names), target_agent=agent_name
                )
            except Exception as exc:
                import warnings

                warnings.warn(
                    f"Post-rescaffold reconciliation failed for '{agent_name}': "
                    f"{exc}. Agent command files may be stale; re-run "
                    f"'specify integration use {agent_name}' or reinstall "
                    f"affected presets to refresh.",
                    stacklevel=2,
                )

        successfully_replaced_winners = {
            command_name
            for command_name, winning_pack_id in winning_pack_by_command.items()
            if command_name not in project_override_commands
            and (
                (winning_pack_id, command_name)
                in successful_skill_replacements
                or (
                    command_name in reconciled_skills
                    and command_name in winning_source_by_command
                    and winning_source_by_command[command_name].is_file()
                )
            )
        }
        successfully_replaced_winners.update(
            project_override_commands & reconciled_skills
        )

        for (
            pack_id,
            merged_commands,
            stale_command_names,
            alias_to_primary,
        ) in pending_command_cleanups:
            fully_replaced = [
                command_name
                for command_name in stale_command_names
                if alias_to_primary.get(command_name, command_name)
                in successfully_replaced_winners
            ]
            if not fully_replaced:
                continue
            remaining_stale = [
                command_name
                for command_name in stale_command_names
                if command_name not in fully_replaced
            ]
            self._unregister_commands({agent_name: fully_replaced})
            if remaining_stale:
                merged_commands[agent_name] = remaining_stale
            else:
                merged_commands.pop(agent_name, None)
            self.registry.update(
                pack_id, {"registered_commands": merged_commands}
            )

        successfully_replaced_command_winners = {
            command_name
            for command_name, winning_pack_id in winning_pack_by_command.items()
            if command_name not in project_override_commands
            and (
                (winning_pack_id, command_name)
                in successful_command_replacements
                or (
                    command_name in reconciled_commands
                    and command_name in winning_source_by_command
                    and winning_source_by_command[command_name].is_file()
                )
            )
        }
        successfully_replaced_command_winners.update(
            project_override_commands & reconciled_commands
        )

        # Skill restoration walks the priority stack, so retire stale layers
        # from highest to lowest. The last cleanup then restores the true
        # non-preset fallback (or removes the skill) rather than cycling back
        # to a lower-priority preset.
        for (
            pack_id,
            pack_dir,
            merged_skills,
            stale_skill_names,
            skill_to_primary,
        ) in reversed(pending_skill_cleanups):
            fully_replaced = [
                skill_name
                for skill_name in stale_skill_names
                if skill_to_primary.get(skill_name)
                in successfully_replaced_command_winners
            ]
            if not fully_replaced:
                continue
            remaining_stale = [
                skill_name
                for skill_name in stale_skill_names
                if skill_name not in fully_replaced
            ]
            override_sources = {
                skill_name: f"override:{skill_to_primary[skill_name]}"
                for skill_name in fully_replaced
                if skill_name in skill_to_primary
            }
            self._unregister_skills(
                {agent_name: fully_replaced},
                pack_dir,
                additional_owned_sources=override_sources,
            )
            if remaining_stale:
                merged_skills[agent_name] = remaining_stale
            else:
                merged_skills.pop(agent_name, None)
            self.registry.update(
                pack_id, {"registered_skills": merged_skills}
            )

    def unregister_agent_artifacts(self, agent_name: str) -> None:
        """Remove ``agent_name``'s tracked preset command/skill artifacts.

        Mirrors ``ExtensionManager.unregister_agent_artifacts()`` (#2948):
        used by ``integration switch`` when deactivating the previous
        integration, so a preset's command overrides and skill mirrors
        written for that agent don't linger as orphans in its directory
        once a different (possibly not-yet-installed) integration becomes
        active — including custom preset commands and files the registrar
        would otherwise skip as user-modified.

        Scoped strictly to ``agent_name``: only that agent's own tracked
        artifacts and registry entries are touched. Other agents' files,
        tracking, and preset packs themselves are left untouched, and no
        priority-stack reconciliation runs — this is agent-scoped cleanup
        only, not preset removal.
        """
        if not agent_name:
            return

        try:
            from ..agents import CommandRegistrar

            registrar = CommandRegistrar()
            agent_config = registrar.AGENT_CONFIGS.get(agent_name)
        except ImportError:
            registrar = None
            agent_config = None
        if agent_config is None or registrar is None:
            return

        for pack_id, metadata in list(self.registry.list().items()):
            updates: Dict[str, Any] = {}

            raw_skills = metadata.get("registered_skills", [])
            if isinstance(raw_skills, list) and raw_skills:
                # Legacy flat-list value predating per-agent provenance:
                # infer real ownership from on-disk markers before removing
                # anything, so only agent_name's actual share is unregistered
                # and the rest migrates to per-agent form instead of either
                # guessing every name belongs to agent_name or blindly
                # leaving other agents' shares unrecoverable (#2948).
                registered_skills_all = self._infer_legacy_skill_provenance(
                    [n for n in raw_skills if isinstance(n, str)],
                    pack_id,
                    fallback_agent=agent_name,
                )
                skills_migrated = True
            elif isinstance(raw_skills, dict):
                registered_skills_all = copy.deepcopy(raw_skills)
                skills_migrated = False
            else:
                registered_skills_all = {}
                skills_migrated = False

            registered_commands = metadata.get("registered_commands", {})
            if not isinstance(registered_commands, dict):
                registered_commands = {}

            agent_command_names = [
                n for n in registered_commands.get(agent_name, []) if isinstance(n, str)
            ]

            # Native SKILL.md agents (claude/codex/agy/…) materialize their
            # preset override in _register_commands(), tracked under
            # registered_commands, not registered_skills — see
            # _register_skills()'s own docstring ("Native skill agents …
            # materialize brand-new preset skills in _register_commands()").
            # A legacy flat-list registered_skills value predating that
            # split can still attribute the very same on-disk file to this
            # agent via provenance inference; unregistering through both
            # paths would double-process the identical directory (delete
            # via the commands path, then no-op "restore" via the skills
            # path since the directory is already gone). Mirror remove()'s
            # own coordination: whenever this agent's artifact is already
            # handled via registered_commands, never additionally treat it
            # as a registered_skills entry for the same agent.
            native_skills_entry_removed = False
            if agent_command_names and agent_config.get("extension") == "/SKILL.md":
                native_skills_entry_removed = agent_name in registered_skills_all
                registered_skills_all.pop(agent_name, None)

            if agent_command_names:
                command_names_to_unregister = agent_command_names
                if agent_config.get("extension") == "/SKILL.md":
                    agent_output = registrar._resolve_agent_dir(
                        agent_name, agent_config, self.project_root
                    )
                    shared_names: set[str] = set()
                    for other_agent, other_names in registered_commands.items():
                        if (
                            other_agent == agent_name
                            or not isinstance(other_names, list)
                        ):
                            continue
                        other_config = registrar.AGENT_CONFIGS.get(other_agent)
                        if (
                            not other_config
                            or other_config.get("extension") != "/SKILL.md"
                        ):
                            continue
                        other_output = registrar._resolve_agent_dir(
                            other_agent, other_config, self.project_root
                        )
                        if other_output == agent_output:
                            shared_names.update(
                                name
                                for name in other_names
                                if isinstance(name, str)
                            )
                    command_names_to_unregister = [
                        name
                        for name in agent_command_names
                        if name not in shared_names
                    ]
                if command_names_to_unregister:
                    self._unregister_commands(
                        {agent_name: command_names_to_unregister}
                    )
                new_registered_commands = copy.deepcopy(registered_commands)
                new_registered_commands.pop(agent_name, None)
                updates["registered_commands"] = new_registered_commands

            agent_skill_names = registered_skills_all.get(agent_name) or []
            if (
                agent_skill_names
                or skills_migrated
                or native_skills_entry_removed
            ):
                if agent_skill_names:
                    self._delete_agent_preset_skills(
                        agent_name, agent_skill_names, pack_id
                    )
                remaining = {
                    other_agent: names
                    for other_agent, names in registered_skills_all.items()
                    if other_agent != agent_name
                }
                updates["registered_skills"] = remaining

            if updates:
                self.registry.update(pack_id, updates)

    def _unregister_commands(self, registered_commands: Dict[str, List[str]]) -> None:
        """Remove previously registered command files from agent directories.

        Args:
            registered_commands: Dict mapping agent names to command name lists
        """
        try:
            from ..agents import CommandRegistrar
        except ImportError:
            return

        registrar = CommandRegistrar()
        registrar.unregister_commands(registered_commands, self.project_root)

    def _merge_pack_registered_commands(
        self, pack_id: str, written: Optional[Dict[str, List[str]]]
    ) -> None:
        """Merge actually-written agent command registrations into a preset's metadata.

        Reconciliation (``_reconcile_composed_commands``) can write a
        preset's content into an agent directory the preset never wrote to
        before — most notably a historical (currently inactive) agent
        supplied via ``extra_agents`` when a higher-priority preset is
        removed. If that write isn't reflected back into the winning
        preset's own ``registered_commands``, the registry silently lies
        about which directories the preset owns: a later removal of this
        same preset only cleans up the agents it already knew about,
        orphaning the directory reconciliation just wrote to on its behalf
        (#2948).

        Args:
            pack_id: The preset whose metadata should be updated.
            written: ``{agent_name: [cmd_name, ...]}`` actually written by
                the reconciliation call just made, exactly mirroring
                ``CommandRegistrar.register_commands_for_non_skill_agents``'s
                return value. A falsy value is a no-op.
        """
        if not written:
            return
        metadata = self.registry.get(pack_id)
        if metadata is None:
            return  # pack_id no longer installed (e.g. removed mid-loop)
        existing_commands = metadata.get("registered_commands", {})
        if not isinstance(existing_commands, dict):
            existing_commands = {}
        merged_commands = copy.deepcopy(existing_commands)
        changed = False
        for agent_name, cmd_names in written.items():
            if not cmd_names:
                continue
            existing_names = merged_commands.get(agent_name, [])
            new_names = [n for n in cmd_names if n not in existing_names]
            if new_names:
                merged_commands[agent_name] = existing_names + new_names
                changed = True
        if changed:
            self.registry.update(pack_id, {"registered_commands": merged_commands})

    def _merge_extension_registered_commands(
        self, extension_id: str, written: Optional[Dict[str, List[str]]]
    ) -> None:
        """Merge reconciliation writes into an extension's registry entry."""
        if not written:
            return
        registry = ExtensionRegistry(self.project_root / ".specify" / "extensions")
        metadata = registry.get(extension_id)
        if metadata is None:
            return
        existing_commands = metadata.get("registered_commands", {})
        if not isinstance(existing_commands, dict):
            existing_commands = {}
        merged_commands = copy.deepcopy(existing_commands)
        changed = False
        for agent_name, cmd_names in written.items():
            existing_names = merged_commands.get(agent_name, [])
            new_names = [name for name in cmd_names if name not in existing_names]
            if new_names:
                merged_commands[agent_name] = existing_names + new_names
                changed = True
        if changed:
            registry.update(extension_id, {"registered_commands": merged_commands})

    def _reconcile_composed_commands(
        self,
        command_names: List[str],
        extra_agents: Optional[Set[str]] = None,
        target_agent: Optional[str] = None,
    ) -> Set[str]:
        """Re-resolve and re-register composed commands from the full stack.

        After install or remove, recompute the effective content for each
        command name that participates in composition, and write the winning
        content to the agent directories. This ensures command files always
        reflect the current priority stack rather than depending on
        install/remove order.

        Single-active rule (#2948): non-skill command-file registration
        performed by this pass is restricted to the active integration, the
        same as ``_register_commands``. Without this, reconciliation after
        install/remove would write command files for every detected
        non-skill agent even though registration itself is active-only,
        leaving inactive integrations with artifacts that are never
        recorded in ``registered_commands`` (and therefore never cleaned up
        on removal).

        Args:
            command_names: List of command names to reconcile
            extra_agents: Additional agent names to also reconcile besides
                the currently active one. Populated by ``remove()`` with the
                historical agents a just-removed preset's
                ``registered_commands`` actually targeted, so a surviving
                lower-priority preset's content is restored there too — not
                only for the currently active agent (#2948). Install/use
                callers omit this, preserving pure active-only behavior.
            target_agent: If set, report only command names written for this
                agent. Other callers receive the union of all written names.

        Returns:
            Command names successfully written by this reconciliation pass.
        """
        if not command_names:
            return set()

        # Every preset-owned command name flows through unchanged. Names are
        # NOT filtered by the ``speckit.<ns>.<cmd>`` shape: a self-contained
        # preset command scaffolds whether or not a like-named extension is
        # installed (parity with _register_commands), and a name whose base
        # layer has disappeared must still reach the loop below so its now
        # uncomposable stale file gets unregistered. The loop already skips
        # names that resolve to no layers at all (``if not layers: continue``).
        try:
            from ..agents import CommandRegistrar
        except ImportError:
            return set()

        resolver = PresetResolver(self.project_root)
        registrar = CommandRegistrar()
        reconciled_commands: set[str] = set()

        def record_written(written: Dict[str, List[str]]) -> None:
            if target_agent is not None:
                reconciled_commands.update(written.get(target_agent, []))
            else:
                for names in written.values():
                    reconciled_commands.update(names)

        # Resolve the active-only restriction once. MISSING_INIT_OPTIONS_FILE
        # (legacy pre-init-options project) keeps the pre-#2948 fallback of
        # registering every detected non-skill agent; a corrupted/malformed
        # init-options.json fails closed via a sentinel that matches no real
        # agent name instead of silently falling back to "no restriction".
        resolved_agent = resolve_active_agent_for_registration(self.project_root)
        if resolved_agent is MISSING_INIT_OPTIONS_FILE:
            only_agent: Optional[str] = None
        elif resolved_agent is None:
            only_agent = ""
        else:
            only_agent = resolved_agent
            # Mirror _register_commands's ai_skills guard: a command-backed
            # active agent running in skills mode renders preset/extension
            # overrides as skills, not command files, so this non-skill
            # command reconciliation pass must not target it either.
            agent_config = registrar.AGENT_CONFIGS.get(only_agent)
            if (
                agent_config
                and is_ai_skills_enabled(load_init_options(self.project_root))
                and agent_config.get("extension") != "/SKILL.md"
            ):
                only_agent = ""

        # The active agent's participation is decided exclusively by the
        # only_agent guard above (which encodes the ai_skills mode). A
        # partially failed command→skills toggle can leave the active agent
        # behind in extra_agents via its stale registered_commands entry,
        # and register_commands_for_non_skill_agents admits every
        # extra_agents member even when only_agent excludes the agent —
        # recreating a command file for an agent now running in skills
        # mode. Never re-admit the active agent through the
        # historical-agents side channel (#2948).
        if extra_agents and isinstance(resolved_agent, str):
            extra_agents = set(extra_agents) - {resolved_agent}

        # Cache registry and manifests outside the loop to avoid
        # repeated filesystem reads for each command name.
        presets_by_priority = list(self.registry.list_by_priority())

        for cmd_name in command_names:
            layers = resolver.collect_all_layers(cmd_name, "command")
            if not layers:
                continue

            # If the top layer is replace, it wins entirely — lower layers
            # are irrelevant regardless of their strategies.
            top_is_replace = layers[0]["strategy"] == "replace"
            has_composition = not top_is_replace and any(
                layer["strategy"] != "replace" for layer in layers
            )
            if not has_composition:
                # Pure replace — the top layer wins.
                top_layer = layers[0]
                top_path = top_layer["path"]
                # Try to find which preset owns this layer
                registered = False
                for pack_id, _meta in presets_by_priority:
                    pack_dir = self.presets_dir / pack_id
                    if top_path.is_relative_to(pack_dir):
                        manifest = resolver._get_manifest(pack_dir)
                        if manifest:
                            for tmpl in manifest.templates:
                                if tmpl.get("name") == cmd_name and tmpl.get("type") == "command":
                                    written = self._register_for_non_skill_agents(
                                        registrar, [tmpl], manifest.id, pack_dir,
                                        only_agent=only_agent, extra_agents=extra_agents,
                                    )
                                    record_written(written)
                                    self._merge_pack_registered_commands(manifest.id, written)
                                    registered = True
                                    break
                        break
                if not registered:
                    # Top layer is a non-preset source (extension, core, or
                    # project override). Register directly from the layer path.
                    source = layers[0]["source"]
                    extension_id = None
                    written: Dict[str, List[str]] = {}
                    if source.startswith("extension:"):
                        # Use extension's own registration to preserve context formatting
                        extension_id = source.split(":", 1)[1].split(" ", 1)[0]
                        ext_dir = (
                            self.project_root / ".specify" / "extensions" / extension_id
                        )
                        ext_manifest_path = ext_dir / "extension.yml"
                        if ext_manifest_path.exists():
                            try:
                                from ..extensions import ExtensionManifest
                                ext_manifest = ExtensionManifest(ext_manifest_path)
                                # Filter to only the command being reconciled
                                matching_cmds = [
                                    c for c in ext_manifest.commands
                                    if c.get("name") == cmd_name
                                ]
                                if matching_cmds:
                                    written = registrar.register_commands_for_non_skill_agents(
                                        matching_cmds, extension_id, ext_dir,
                                        self.project_root,
                                        context_note=f"\n<!-- Extension: {extension_id} -->\n<!-- Config: .specify/extensions/{extension_id}/ -->\n",
                                        extension_id=extension_id,
                                        only_agent=only_agent,
                                        extra_agents=extra_agents,
                                    )
                                    record_written(written)
                                    registered = True
                            except (ImportError, FileNotFoundError, OSError):
                                # Extension registration failed; fall back to
                                # generic path-based registration below.
                                pass
                    if not registered:
                        source_id = extension_id or source
                        written = self._register_command_from_path(
                            registrar, cmd_name, top_path,
                            source_id=source_id,
                            only_agent=only_agent, extra_agents=extra_agents,
                        )
                        record_written(written)
                    if extension_id:
                        self._merge_extension_registered_commands(
                            extension_id, written
                        )
            else:
                # Composed command — resolve from full stack
                composed = resolver.resolve_content(cmd_name, "command")
                if composed is None:
                    # Composition no longer possible (e.g. base layer removed).
                    # Unregister any stale command file from non-skill agents.
                    import warnings
                    warnings.warn(
                        f"Cannot compose command '{cmd_name}': no base layer. "
                        f"Stale command files may remain.",
                        stacklevel=2,
                    )
                    registrar._ensure_configs()
                    # Include aliases from the top layer's manifest
                    cmd_names_to_unregister = [cmd_name]
                    for _pid, _meta in presets_by_priority:
                        _pd = self.presets_dir / _pid
                        _m = resolver._get_manifest(_pd)
                        if _m:
                            for _t in _m.templates:
                                if _t.get("name") == cmd_name and _t.get("type") == "command":
                                    for alias in _t.get("aliases", []):
                                        if isinstance(alias, str):
                                            cmd_names_to_unregister.append(alias)
                                    break
                    # Mirror the active-only restriction used elsewhere in
                    # this pass: without it, unregistering a stale composed
                    # command would touch every non-skill agent's directory,
                    # deleting historical artifacts from integrations that
                    # were never active when this preset registered (#2948).
                    registrar.unregister_commands(
                        {
                            agent: cmd_names_to_unregister
                            for agent in registrar.AGENT_CONFIGS
                            if registrar.AGENT_CONFIGS[agent].get("extension") != "/SKILL.md"
                            and (
                                only_agent is None
                                or agent == only_agent
                                or agent in (extra_agents or ())
                            )
                        },
                        self.project_root,
                    )
                    continue

                # Write to the highest-priority preset's .composed dir
                registered = False
                for pack_id, _meta in presets_by_priority:
                    pack_dir = self.presets_dir / pack_id
                    manifest = resolver._get_manifest(pack_dir)
                    if not manifest:
                        continue
                    for tmpl in manifest.templates:
                        if tmpl.get("name") == cmd_name and tmpl.get("type") == "command":
                            composed_dir = pack_dir / ".composed"
                            composed_dir.mkdir(parents=True, exist_ok=True)
                            composed_file = composed_dir / f"{cmd_name}.md"
                            composed_file.write_text(composed, encoding="utf-8")
                            written = self._register_for_non_skill_agents(
                                registrar,
                                [{**tmpl, "file": f".composed/{cmd_name}.md"}],
                                manifest.id, pack_dir,
                                only_agent=only_agent, extra_agents=extra_agents,
                            )
                            record_written(written)
                            self._merge_pack_registered_commands(manifest.id, written)
                            registered = True
                            break
                    else:
                        continue
                    break
                if not registered:
                    # No preset owns this composed command — write to a
                    # shared .composed dir and register from the top layer.
                    shared_composed = self.presets_dir / ".composed"
                    shared_composed.mkdir(parents=True, exist_ok=True)
                    composed_file = shared_composed / f"{cmd_name}.md"
                    composed_file.write_text(composed, encoding="utf-8")
                    source = layers[0]["source"]
                    if source.startswith("extension:"):
                        source_id = source.split(":", 1)[1].split(" ", 1)[0]
                    else:
                        source_id = source
                    written = self._register_command_from_path(
                        registrar, cmd_name, composed_file,
                        source_id=source_id,
                        only_agent=only_agent, extra_agents=extra_agents,
                    )
                    record_written(written)
                    if source.startswith("extension:"):
                        self._merge_extension_registered_commands(
                            source_id, written
                        )

        return reconciled_commands

    def _register_command_from_path(
        self,
        registrar: Any,
        cmd_name: str,
        cmd_path: Path,
        source_id: str = "reconciled",
        only_agent: Optional[str] = None,
        extra_agents: Optional[Set[str]] = None,
    ) -> Dict[str, List[str]]:
        """Register a single command from a file path (non-preset source).

        Used by reconciliation when the winning layer is an extension,
        core template, or project override rather than a preset.

        Args:
            registrar: CommandRegistrar instance
            cmd_name: Command name
            cmd_path: Path to the command file
            source_id: Source attribution for rendered output
            only_agent: If set, restrict registration to this single agent (#2948).
            extra_agents: Additional agent names to register for besides
                ``only_agent`` (post-removal reconciliation only, #2948).

        Returns:
            ``{agent_name: [cmd_name, ...]}`` for every agent this call
            actually registered the command for (empty if the source path
            doesn't exist or nothing was written).
        """
        if not cmd_path.exists():
            return {}
        cmd_tmpl: Dict[str, Any] = {
            "name": cmd_name,
            "type": "command",
            "file": cmd_path.name,
        }
        # Load aliases from extension manifest when the winning layer is an extension
        if source_id and not source_id.startswith("preset:"):
            try:
                from ..extensions import ExtensionManifest
                for ext_dir in (self.project_root / ".specify" / "extensions").iterdir():
                    if not ext_dir.is_dir():
                        continue
                    if cmd_path.is_relative_to(ext_dir):
                        manifest_path = ext_dir / "extension.yml"
                        if manifest_path.exists():
                            ext_manifest = ExtensionManifest(manifest_path)
                            for cmd in ext_manifest.commands:
                                if cmd.get("name") == cmd_name:
                                    aliases = cmd.get("aliases", [])
                                    if isinstance(aliases, list) and aliases:
                                        cmd_tmpl["aliases"] = aliases
                                    break
                        break
            except Exception:
                pass  # best-effort alias loading
        return self._register_for_non_skill_agents(
            registrar, [cmd_tmpl], source_id, cmd_path.parent,
            only_agent=only_agent, extra_agents=extra_agents,
        )

    def _register_for_non_skill_agents(
        self,
        registrar: Any,
        commands: List[Dict[str, Any]],
        source_id: str,
        source_dir: Path,
        only_agent: Optional[str] = None,
        extra_agents: Optional[Set[str]] = None,
    ) -> Dict[str, List[str]]:
        """Register commands for non-skill agents during reconciliation.

        Skill-based agents (``/SKILL.md`` layout) are handled separately:
        - On removal: ``_unregister_skills()`` restores from core/extension,
          then ``_reconcile_skills()`` re-runs ``_register_skills()`` for the
          next winning preset so SKILL.md files get proper frontmatter and
          descriptions.
        - On install: ``_register_skills()`` writes formatted SKILL.md, then
          ``_reconcile_skills()`` ensures the actual priority winner is used.

        Writing raw command content to skill agents would produce invalid
        SKILL.md files (missing skill frontmatter, descriptions, etc.).

        Args:
            only_agent: If set, restrict registration to this single agent,
                matching the active-only rule applied by ``_register_commands``
                (#2948).
            extra_agents: Additional agent names to register for besides
                ``only_agent``. Used by post-removal reconciliation to also
                restore surviving content into historical agent directories
                a just-removed preset actually wrote to (#2948).

        Returns:
            ``{agent_name: [cmd_name, ...]}`` for every agent this call
            actually registered a command for, mirroring
            ``CommandRegistrar.register_commands_for_non_skill_agents``'s
            return value so callers can merge it into a preset's own
            ``registered_commands`` tracking (#2948).
        """
        return registrar.register_commands_for_non_skill_agents(
            commands, source_id, source_dir, self.project_root,
            only_agent=only_agent, extra_agents=extra_agents,
        )
