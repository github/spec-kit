"""Kiro CLI integration."""

from ..base import MarkdownIntegration


# Kiro CLI file-based prompts do NOT support any argument-substitution syntax,
# so a raw "$ARGUMENTS" token would reach the model verbatim and break the
# prompt (issue #1926, kirodotdev/Kiro#4141). Use a prose fallback so the
# rendered prompt instructs the model to take its argument from the user's
# next message.
_KIRO_ARG_FALLBACK = "(the user will provide the argument in this conversation)"


class KiroCliIntegration(MarkdownIntegration):
    key = "kiro-cli"
    multi_install_safe = True
    config = {
        "name": "Kiro CLI",
        "folder": ".kiro/",
        "commands_subdir": "prompts",
        "install_url": "https://kiro.dev/docs/cli/",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".kiro/prompts",
        "format": "markdown",
        "args": _KIRO_ARG_FALLBACK,
        "extension": ".md",
    }

    # Kiro CLI keeps everything under a static, isolated agent root
    # (``.kiro/`` with commands in ``.kiro/prompts``) that no other
    # integration writes to, so it is safe to install alongside others
    # (issue #3471). The registry's multi-install-safe contract tests
    # enforce that isolation for every integration setting this flag.
    multi_install_safe = True
