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
        ``--recipe <path> --params args=<rest>``. This mirrors
        ``OpencodeIntegration``, which maps the same leading slash-command onto
        opencode's native ``--command``.
        """
        args = [self._resolve_executable(), "run"]
        # Operator-injected extra args land before Spec Kit's canonical flags so
        # --model/--output-format stay authoritative under repeated-flag CLI
        # semantics (mirrors OpencodeIntegration).
        self._apply_extra_args_env_var(args)

        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "json"])

        if prompt.startswith("/"):
            command, _, remainder = prompt[1:].partition(" ")
            if command:
                # Derive the recipe path from the same two sources ``setup()``
                # uses -- ``config["folder"]`` + ``config["commands_subdir"]``
                # (exactly what ``commands_dest()`` does) and
                # ``command_filename()`` -- so the dispatch target cannot drift
                # from the file that was actually installed.
                # ``command_filename`` re-adds the ``speckit.`` prefix and the
                # ``.yaml`` extension, so strip the prefix first; a dotted
                # extension command (``speckit.git.commit``) round-trips too.
                stem = (
                    command[len("speckit."):]
                    if command.startswith("speckit.")
                    else command
                )
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
