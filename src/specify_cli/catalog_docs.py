"""Helpers for rendering the built-in integrations reference table."""

from __future__ import annotations

from typing import Any

from ._assets import ROOT_DIR

INTEGRATIONS_REFERENCE_PATH = ROOT_DIR / "docs" / "reference" / "integrations.md"


INTEGRATION_DOC_URLS: dict[str, str | None] = {
    "amp": "https://ampcode.com/",
    "agy": "https://antigravity.google/",
    "auggie": "https://docs.augmentcode.com/cli/overview",
    "bob": "https://www.ibm.com/products/bob",
    "claude": "https://www.anthropic.com/claude-code",
    "codebuddy": "https://www.codebuddy.ai/cli",
    "codex": "https://github.com/openai/codex",
    "copilot": "https://code.visualstudio.com/",
    "cursor-agent": "https://cursor.sh/",
    "devin": "https://cli.devin.ai/docs",
    "forge": "https://forgecode.dev/",
    "gemini": "https://github.com/google-gemini/gemini-cli",
    "generic": None,
    "goose": "https://block.github.io/goose/",
    "iflow": "https://docs.iflow.cn/en/cli/quickstart",
    "junie": "https://junie.jetbrains.com/",
    "kilocode": "https://github.com/Kilo-Org/kilocode",
    "kimi": "https://code.kimi.com/",
    "kiro-cli": "https://kiro.dev/docs/cli/",
    "lingma": "https://lingma.aliyun.com/",
    "opencode": "https://opencode.ai/",
    "pi": "https://pi.dev",
    "qodercli": "https://qoder.com/cli",
    "qwen": "https://github.com/QwenLM/qwen-code",
    "roo": "https://roocode.com/",
    "shai": "https://github.com/ovh/shai",
    "tabnine": "https://docs.tabnine.com/main/getting-started/tabnine-cli",
    "trae": "https://www.trae.ai/",
    "vibe": "https://github.com/mistralai/mistral-vibe",
    "windsurf": "https://windsurf.com/",
    "zed": "https://zed.dev/",
}

INTEGRATION_LABEL_OVERRIDES: dict[str, str] = {
    "agy": "Antigravity (agy)",
    "codebuddy": "CodeBuddy CLI",
    "generic": "Generic",
    "shai": "SHAI (OVHcloud)",
}

INTEGRATION_NOTES: dict[str, str] = {
    "agy": "Skills-based integration; skills are installed automatically",
    "claude": "Skills-based integration; installs skills in `.claude/skills`",
    "codex": (
        "Skills-based integration; installs skills into `.agents/skills` "
        "and invokes them as `$speckit-<command>`"
    ),
    "bob": "IDE-based agent",
    "devin": (
        "Skills-based integration; installs skills into `.devin/skills/` "
        "and invokes them as `/speckit-<command>`"
    ),
    "goose": "Uses YAML recipe format in `.goose/recipes/`",
    "kimi": (
        "Skills-based integration; supports `--migrate-legacy` "
        "for dotted→hyphenated directory migration"
    ),
    "kiro-cli": (
        "Kiro CLI does not substitute `$ARGUMENTS` in file-based prompts, "
        "so Spec Kit ships a prose fallback at render time "
        "(see [Manage prompts](https://kiro.dev/docs/cli/chat/manage-prompts/) "
        "and issue [#1926](https://github.com/github/spec-kit/issues/1926)). "
        "Alias: `--integration kiro`"
    ),
    "lingma": "Skills-based integration; skills are installed automatically",
    "pi": (
        "Pi doesn't have MCP support out of the box, so `taskstoissues` "
        "won't work as intended. MCP support can be added via "
        "[extensions](https://github.com/badlogic/pi-mono/tree/main/"
        "packages/coding-agent#extensions)"
    ),
    "generic": (
        "Bring your own agent — use `--integration generic "
        "--integration-options=\"--commands-dir <path>\"` "
        "for AI coding agents not listed above"
    ),
    "trae": "Skills-based integration; skills are installed automatically",
}


def render_cell(value: str) -> str:
    r"""Escape markdown special characters (pipes) and normalize newlines to spaces.

    This ensures table cells remain valid markdown even if they contain
    pipes (escaped as \|) or carriage returns (normalized to spaces).
    """
    value = value.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    return value.replace("|", "\\|")


def escape_url_for_markdown_link(url: str) -> str:
    """Escape characters that can break Markdown link syntax.

    Escapes `)` and `|` which can terminate or corrupt the link destination.
    """
    return url.replace(")", "\\)").replace("|", "\\|")


def escape_markdown_link_text(text: str) -> str:
    """Escape characters that can break Markdown link text."""
    return text.replace("[", "\\[").replace("]", "\\]")


def render_code_span(value: str) -> str:
    """Safely render a value as an inline markdown code span.

    Replaces internal backticks with single quotes to prevent breaking the code span.
    """
    safe_value = value.replace("`", "'")
    return f"`{safe_value}`"


def _get_integration_registry() -> dict[str, Any]:
    from specify_cli.integrations import INTEGRATION_REGISTRY

    return INTEGRATION_REGISTRY


def list_integrations_for_docs(
    warn_on_missing: bool = False,
    warn_on_extra: bool = False,
) -> list[tuple[str, str, str | None, str]]:
    """List all integrations with their documentation URLs and notes.

    Returns all integrations in the registry. Missing entries in INTEGRATION_DOC_URLS
    default to None; if `warn_on_missing` is True, emits a warning for these.
    If `warn_on_extra` is True, emits a warning for stale keys in the doc maps that
    are no longer in the registry. Missing notes entries default to empty string.
    """
    registry = _get_integration_registry()
    registry_keys = set(registry)

    # Warn if there are integrations missing from INTEGRATION_DOC_URLS (when enabled)
    missing = sorted(registry_keys - set(INTEGRATION_DOC_URLS))
    if missing and warn_on_missing:
        import warnings
        warnings.warn(
            f"Integration(s) missing from INTEGRATION_DOC_URLS: "
            f"{', '.join(missing)}. They will be included in the docs table "
            "without documentation links. Add them to INTEGRATION_DOC_URLS in "
            "catalog_docs.py if a link should be available.",
            stacklevel=2
        )

    # Warn if there are stale keys in doc maps not in the registry (when enabled)
    if warn_on_extra:
        extra_in_urls = sorted(set(INTEGRATION_DOC_URLS) - registry_keys)
        extra_in_labels = sorted(
            set(INTEGRATION_LABEL_OVERRIDES) - registry_keys
        )
        extra_in_notes = sorted(set(INTEGRATION_NOTES) - registry_keys)
        extra_keys = extra_in_urls or extra_in_labels or extra_in_notes
        if extra_keys:
            import warnings
            stale_keys = sorted(
                set(extra_in_urls + extra_in_labels + extra_in_notes)
            )
            warnings.warn(
                f"Stale key(s) found in doc maps (no longer in registry): "
                f"{', '.join(stale_keys)}. Consider removing them from "
                "INTEGRATION_DOC_URLS, INTEGRATION_LABEL_OVERRIDES, and "
                "INTEGRATION_NOTES.",
                stacklevel=2
            )

    rows: list[tuple[str, str, str | None, str]] = []

    for key, integration in registry.items():
        config = getattr(integration, "config", {})
        if not isinstance(config, dict):
            config = {}
        label = INTEGRATION_LABEL_OVERRIDES.get(key, str(config.get("name") or key))
        if key in INTEGRATION_DOC_URLS:
            url = INTEGRATION_DOC_URLS[key]
        else:
            url = config.get("install_url")
        notes = INTEGRATION_NOTES.get(key, "")
        rows.append((key, label, url, notes))

    return sorted(rows, key=lambda r: r[0])


def render_integrations_table() -> str:
    """Render the built-in integrations reference table as markdown."""
    table_rows: list[list[str]] = []

    for key, label, url, notes in list_integrations_for_docs():
        # Escape raw field values *before* composing Markdown syntax so that
        # a pipe inside a label or notes doesn't break a link target.
        safe_label = escape_markdown_link_text(render_cell(label))
        safe_notes = render_cell(notes)
        safe_url = escape_url_for_markdown_link(url) if url else None
        agent = (
            f"[{safe_label}]({safe_url})"
            if safe_url
            else safe_label
        )
        table_rows.append([agent, render_code_span(key), safe_notes])

    headers = ("Agent", "Key", "Notes")

    def render_row(values: list[str]) -> str:
        # Values are already escaped; do not re-apply render_cell here.
        return "| " + " | ".join(values) + " |"

    separator = "| " + " | ".join("---" for _ in headers) + " |"
    lines = [render_row(list(headers)), separator]
    lines.extend(render_row(row) for row in table_rows)
    return "\n".join(lines) + "\n"
