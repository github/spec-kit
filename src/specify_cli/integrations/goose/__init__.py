"""Goose integration — open source AI agent (Agentic AI Foundation)."""

from __future__ import annotations

from ..base import YamlIntegration


class GooseIntegration(YamlIntegration):
    key = "goose"
    config = {
        "name": "Goose",
        "folder": ".goose/",
        "commands_subdir": "recipes",
        "install_url": "https://goose-docs.ai/docs/getting-started/installation",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".goose/recipes",
        "format": "yaml",
        "args": "{{args}}",
        "extension": ".yaml",
    }

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        """Build CLI arguments for non-interactive ``goose`` execution.

        ``YamlIntegration`` never overrode ``build_exec_args()``, so Goose
        inherited the ``IntegrationBase`` no-op returning ``None``. Callers read
        ``None`` as "this CLI is unavailable", so a workflow command/prompt step
        targeting Goose reported ``CLI not found or not installed`` even with
        ``goose`` on ``PATH`` (the Goose item in issue #2416).

        ``goose`` has no ``-p`` flag; its non-interactive entry point is
        ``goose run``, which takes ``-t/--text`` for free-form text,
        ``--recipe`` for a stored recipe, ``--params KEY=VALUE`` for recipe
        parameters, plus ``--model`` and ``--output-format``.

        Spec Kit installs its commands as Goose *recipes* under
        ``.goose/recipes/``, each declaring an optional ``args`` string
        parameter, so a ``/speckit.<name> <rest>`` invocation maps onto
        ``--recipe <path> --params args=<rest>``. Only that namespace is
        mapped: ``--recipe`` is a *path* Spec Kit synthesizes, unlike
        opencode's ``--command`` or hermes' ``-s``, which hand a bare name to
        the agent's own resolver. Any other prompt -- including Goose's own
        session commands such as ``/help`` or ``/plan`` -- goes to ``-t``.
        """
        args = [self._resolve_executable(), "run"]
        # Extra args are applied first, matching the opencode / codex /
        # cursor-agent ordering. Positional parity only, NOT precedence:
        # ``goose run`` is clap-derive based, and --recipe / --model /
        # --output-format are single-value args with no ``args_override_self``,
        # so re-passing any of them through
        # SPECKIT_INTEGRATION_GOOSE_EXTRA_ARGS makes goose exit with
        # "cannot be used multiple times" whichever side comes first. The same
        # is true of goose's boolean flags. Only its ``Vec``-typed args (which
        # clap infers as ArgAction::Append) may legitimately repeat.
        self._apply_extra_args_env_var(args)

        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "json"])

        # Only the ``speckit.`` namespace maps to a recipe: this branch
        # synthesizes a *path*, and ``command_filename()`` can only ever spell
        # ``speckit.<name>.yaml``. ``PromptStep`` passes arbitrary ``prompt:``
        # strings here, so other slash text -- including Goose's own session
        # commands ``/help`` and ``/plan`` -- must reach ``-t`` unchanged.
        if prompt.startswith("/speckit."):
            command, _, remainder = prompt[1:].partition(" ")
            # ``command_filename`` re-adds the ``speckit.`` prefix and the
            # ``.yaml`` extension, so strip it here; a dotted extension command
            # (``speckit.git.commit``) round-trips too. A bare ``/speckit.``
            # leaves no stem and falls through to ``-t``.
            stem = command[len("speckit."):]
            if stem:
                # Derive the recipe path from the same two sources ``setup()``
                # uses -- ``config["folder"]`` + ``config["commands_subdir"]``
                # (exactly what ``commands_dest()`` does) and
                # ``command_filename()`` -- so the dispatch target cannot drift
                # from the file that was actually installed.
                folder = (self.config.get("folder") or "").strip("/")
                subdir = (self.config.get("commands_subdir") or "").strip("/")
                # Relative, forward-slash path: dispatch runs with
                # ``cwd=project_root``, and goose accepts a POSIX separator on
                # every platform (``commands_dest()`` yields backslashes on
                # win32).
                parts = [
                    p for p in (folder, subdir, self.command_filename(stem)) if p
                ]
                args.extend(["--recipe", "/".join(parts)])
                if remainder.strip():
                    args.extend(["--params", f"args={remainder}"])
                return args

        args.extend(["-t", prompt])
        return args
