"""Tests for KiroCliIntegration."""

import os
import re

from specify_cli.integrations import get_integration
from specify_cli.integrations.kiro_cli import _KIRO_ARG_FALLBACK
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_markdown import MarkdownIntegrationTests


# Regex shapes that indicate a value is a placeholder token, not prose.
# Covers Bash ($VAR, ${VAR}, ${VAR:-default}), Mustache/Handlebars/Jinja
# ({{var}}, {{{var}}}), Liquid/Jinja control ({% ... %}), Python str.format /
# .NET ({var}, {0}), angle-bracket (<var>), and Windows-style (%VAR%).
# Anchored to the FULL STRING so legitimate prose mentioning a placeholder
# (e.g. "the {{magic}} of placeholders") is not flagged. The Liquid pattern
# is anchored to the START so multi-tag templates fire while mid-sentence
# {%-quotation does not.
_PLACEHOLDER_TOKEN_PATTERNS = (
    re.compile(r"^\$\w+$"),                                  # $ARGUMENTS, $args
    re.compile(r"^\$\{\w+(?:[:\-+?][^}]*)?\}$"),             # ${ARGS}, ${ARGS:-default}
    re.compile(r"^\{\{\{?\s*\w+(\s*[|.][^}]*)?\s*\}?\}\}$"), # {{var}} {{{var}}} {{x|y}}
    re.compile(r"^\{%"),                                     # {% if x %}{{ x }}{% endif %}
    re.compile(r"^<\w+>$"),                                  # <args>
    re.compile(r"^%\w+%$"),                                  # %USERNAME%
    re.compile(r"^\{(?:\d+|[a-zA-Z_]\w*)(?:[.\[][^}]*)?(?:![rsa])?(?::[^}]*)?\}$"),  # {0}, {var}, {0:>5}
)


def _looks_like_placeholder_token(value: str) -> bool:
    """Return True if *value* matches a known placeholder-token shape."""
    if not value:
        return False
    return any(p.search(value) for p in _PLACEHOLDER_TOKEN_PATTERNS)


class TestKiroCliIntegration(MarkdownIntegrationTests):
    KEY = "kiro-cli"
    FOLDER = ".kiro/"
    COMMANDS_SUBDIR = "prompts"
    REGISTRAR_DIR = ".kiro/prompts"
    CONTEXT_FILE = "AGENTS.md"

    def test_registrar_config(self):
        """Override base assertion: kiro-cli uses a prose fallback for args
        because Kiro CLI file-based prompts do not natively substitute
        ``$ARGUMENTS`` (see issue #1926 / kirodotdev/Kiro#4141). The
        regression-guard load is carried by the two layer tests below
        (exact-fallback + placeholder-shape rejection)."""
        i = get_integration(self.KEY)
        assert i.registrar_config["dir"] == self.REGISTRAR_DIR
        assert i.registrar_config["format"] == "markdown"
        assert i.registrar_config["extension"] == ".md"

    def test_registrar_config_args_is_exact_prose_fallback(self):
        """Layer 1 — pin the exact fallback so wording drift requires a
        deliberate paired commit (production constant + test update)."""
        i = get_integration(self.KEY)
        assert i.registrar_config["args"] == _KIRO_ARG_FALLBACK, (
            f"args drifted from the pinned fallback constant. "
            f"Got: {i.registrar_config['args']!r}; expected: {_KIRO_ARG_FALLBACK!r}. "
            f"If the wording change is intentional, update _KIRO_ARG_FALLBACK and "
            f"this test together."
        )

    def test_registrar_config_args_does_not_look_like_a_placeholder_token(self):
        """Layer 2 — independent regression guard: even if someone bypasses
        layer-1 by changing both constant and test, the value still must not
        look like ANY placeholder token shape ($X, ${X}, {{X}}, <X>, %X%, {0},
        {% %}). Catches the class of regression Copilot called out: a swap
        from $ARGUMENTS to $INPUT or {{userMessage}} would fail this test
        even if it accidentally passed layer 1."""
        i = get_integration(self.KEY)
        args = i.registrar_config["args"]
        assert not _looks_like_placeholder_token(args), (
            f"registrar_config['args'] = {args!r} matches a known placeholder-"
            f"token shape — Kiro CLI does not substitute placeholders so this "
            f"would reach the model verbatim and break the prompt (issue #1926). "
            f"Use a prose fallback instead."
        )

    def test_rendered_prompts_do_not_contain_raw_arguments(self, tmp_path):
        """Rendered Kiro prompt files must NOT contain the raw ``$ARGUMENTS``
        token — Kiro CLI does not substitute it, so the literal would reach
        the model and break the prompt (issue #1926)."""
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")

        prompts_dir = tmp_path / self.REGISTRAR_DIR
        rendered = list(prompts_dir.glob("*.md"))
        assert rendered, "expected at least one rendered prompt file"

        offenders = [
            p.name for p in rendered if "$ARGUMENTS" in p.read_text(encoding="utf-8")
        ]
        assert offenders == [], (
            f"these rendered prompts still contain the raw $ARGUMENTS token: {offenders}"
        )

    def test_rendered_prompts_contain_kiro_arg_placeholder(self, tmp_path):
        """The chosen kiro-cli args fallback string must end up in at least
        one rendered prompt (proves substitution actually fired, not just
        that $ARGUMENTS was removed). Imports the fallback constant directly
        instead of reading the field back so the test stays independent of
        the integration's own config — even if the registrar_config['args']
        regresses, this test still verifies the FALLBACK STRING is in the
        rendered output."""
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")

        expected = _KIRO_ARG_FALLBACK
        prompts_dir = tmp_path / self.REGISTRAR_DIR
        contents = "\n".join(
            p.read_text(encoding="utf-8") for p in prompts_dir.glob("*.md")
        )
        assert expected in contents, (
            f"none of the rendered prompts contain the configured args fallback "
            f"({expected!r})"
        )


class TestKiroAlias:
    """--ai kiro alias normalizes to kiro-cli and auto-promotes."""

    def test_kiro_alias_normalized_to_kiro_cli(self, tmp_path):
        """--ai kiro should normalize to canonical kiro-cli and auto-promote."""
        from typer.testing import CliRunner
        from specify_cli import app

        target = tmp_path / "kiro-alias-proj"
        target.mkdir()

        old_cwd = os.getcwd()
        try:
            os.chdir(target)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--ai", "kiro",
                "--ignore-agent-tools", "--script", "sh", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert (target / ".kiro" / "prompts" / "speckit.plan.md").exists()
