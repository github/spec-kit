"""Factory Droid CLI integration — skills-based agent.

Droid discovers project skills from
``.factory/skills/speckit-<name>/SKILL.md``. Spec Kit installs into that
native tree so the generated skills are visible to Droid without extra
configuration.

See: https://docs.factory.ai/cli/configuration/skills
"""

from __future__ import annotations

from ..base import SkillsIntegration


class DroidIntegration(SkillsIntegration):
    """Integration for Factory Droid CLI."""

    key = "droid"
    config = {
        "name": "Factory Droid",
        "folder": ".factory/",
        "commands_subdir": "skills",
        "install_url": "https://docs.factory.ai/cli/getting-started/overview",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".factory/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    multi_install_safe = True

    @staticmethod
    def _inject_frontmatter_flag(content: str, key: str, value: str = "true") -> str:
        """Insert ``key: value`` before the closing ``---`` if not already present.

        Mirrors the helper used by ``ClaudeIntegration`` / ``VibeIntegration``
        so per-agent frontmatter injection stays consistent across skills-based
        integrations. Pre-scans for the key to keep injection idempotent.
        """
        lines = content.splitlines(keepends=True)

        # Pre-scan: bail out if already present in frontmatter
        dash_count = 0
        for line in lines:
            stripped = line.rstrip("\n\r")
            if stripped == "---":
                dash_count += 1
                if dash_count == 2:
                    break
                continue
            if dash_count == 1 and stripped.startswith(f"{key}:"):
                return content

        # Inject before the closing --- of frontmatter. Always emit a
        # newline after the injected key so the key and the closing ---
        # stay on separate lines even when the closing delimiter is the
        # last line of the file with no trailing newline.
        out: list[str] = []
        dash_count = 0
        injected = False
        for line in lines:
            stripped = line.rstrip("\n\r")
            if stripped == "---":
                dash_count += 1
                if dash_count == 2 and not injected:
                    out.append(f"{key}: {value}\n")
                    injected = True
            out.append(line)
        return "".join(out)

    def post_process_skill_content(self, content: str) -> str:
        """Inject Droid-specific skill frontmatter flags.

        Applies the shared hook-command normalization note (skills agents use
        hyphenated ``/speckit-<name>`` invocations, not dotted ``/speckit.<name>``)
        and the Droid-specific ``user-invocable`` / ``disable-model-invocation``
        frontmatter flags so skills are both user- and Droid-invocable.
        """
        updated = super().post_process_skill_content(content)
        updated = self._inject_frontmatter_flag(updated, "user-invocable")
        updated = self._inject_frontmatter_flag(updated, "disable-model-invocation", "false")
        return updated

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        """Build CLI arguments for non-interactive ``droid`` execution.

        Uses ``droid exec "<prompt>"`` for headless dispatch. Spec Kit does
        not auto-apply any permission-bypass flag: operators who want to
        skip interactive confirmation can pass it through
        ``SPECKIT_INTEGRATION_DROID_EXTRA_ARGS`` (e.g.
        ``SPECKIT_INTEGRATION_DROID_EXTRA_ARGS="--skip-permissions-unsafe"``).

        Output format and model selection mirror the documented CLI flags:
        ``--output-format json`` (when ``output_json`` is set) and
        ``--model <id>``. Operator-supplied extra args via
        ``SPECKIT_INTEGRATION_DROID_EXTRA_ARGS`` are appended after the
        canonical Spec Kit flags so the canonical flags are guaranteed to
        be present in argv. Note that with duplicate-flag CLI parsing the
        later (operator-supplied) value may take precedence over the
        canonical one, so operators can still override ``--model`` or
        ``--output-format``.
        """
        if not self.config or not self.config.get("requires_cli"):
            return None
        args = [
            self._resolve_executable(),
            "exec",
            prompt,
        ]
        # Operator-injected extra args are appended after Spec Kit's
        # canonical --model / --output-format flags so the canonical
        # flags are guaranteed to be present in argv regardless of
        # whatever the operator passes via SPECKIT_INTEGRATION_DROID_EXTRA_ARGS.
        # This is a deliberate inversion of the cursor-agent / opencode /
        # codex ordering (which all apply extra args first, then append
        # canonical flags so the canonical values win under duplicate-flag
        # parsing). For Droid the canonical flag values are written into
        # argv first, then the operator-supplied values follow; with
        # duplicate-flag parsing the later (operator) value may therefore
        # take precedence.
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "json"])
        self._apply_extra_args_env_var(args)
        return args
