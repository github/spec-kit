"""Helpers for generating catalog-backed reference docs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
INTEGRATIONS_CATALOG_PATH = ROOT_DIR / "integrations" / "catalog.json"
INTEGRATIONS_REFERENCE_PATH = ROOT_DIR / "docs" / "reference" / "integrations.md"

GENERATED_START_MARKER = "<!-- BEGIN GENERATED INTEGRATIONS TABLE -->"
GENERATED_END_MARKER = "<!-- END GENERATED INTEGRATIONS TABLE -->"


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
    "codex": "Skills-based integration; installs skills into `.agents/skills` and invokes them as `$speckit-<command>`",
    "bob": "IDE-based agent",
    "devin": "Skills-based integration; installs skills into `.devin/skills/` and invokes them as `/speckit-<command>`",
    "goose": "Uses YAML recipe format in `.goose/recipes/`",
    "kimi": "Skills-based integration; supports `--migrate-legacy` for dotted→hyphenated directory migration",
    "kiro-cli": "Kiro CLI does not substitute `$ARGUMENTS` in file-based prompts, so Spec Kit ships a prose fallback at render time (see [Manage prompts](https://kiro.dev/docs/cli/chat/manage-prompts/) and issue [#1926](https://github.com/github/spec-kit/issues/1926)). Alias: `--integration kiro`",
    "lingma": "Skills-based integration; skills are installed automatically",
    "pi": "Pi doesn't have MCP support out of the box, so `taskstoissues` won't work as intended. MCP support can be added via [extensions](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent#extensions)",
    "generic": "Bring your own agent — use `--integration generic --integration-options=\"--commands-dir <path>\"` for AI coding agents not listed above",
    "trae": "Skills-based integration; skills are installed automatically",
}


def load_integrations_catalog(path: Path = INTEGRATIONS_CATALOG_PATH) -> dict[str, Any]:
    """Load and validate the integrations catalog JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected {path} to contain a JSON object")
    integrations = data.get("integrations")
    if not isinstance(integrations, dict):
        raise ValueError(f"Expected {path} to contain an 'integrations' object")
    return data


def _render_cell(value: str) -> str:
    return value.replace("\n", " ")


def _get_integration_registry() -> dict[str, Any]:
    from specify_cli.integrations import INTEGRATION_REGISTRY

    return INTEGRATION_REGISTRY


def _iter_integrations_for_docs() -> list[tuple[str, str, str | None, str]]:
    registry = _get_integration_registry()
    rows: list[tuple[str, str, str | None, str]] = []

    for key, integration in registry.items():
        config = integration.config if isinstance(integration.config, dict) else {}
        label = INTEGRATION_LABEL_OVERRIDES.get(key, str(config.get("name") or key))
        url = INTEGRATION_DOC_URLS.get(key)
        notes = INTEGRATION_NOTES.get(key, "")
        rows.append((key, label, url, notes))

    return rows


def render_integrations_table(catalog: dict[str, Any]) -> str:
    """Render the integrations reference table from the catalog data."""
    integrations = catalog.get("integrations", {})
    rows: list[list[str]] = []

    doc_rows = _iter_integrations_for_docs()
    doc_keys = [key for key, _, _, _ in doc_rows]
    extra_keys = [key for key in integrations if key not in doc_keys]
    if extra_keys:
        raise KeyError(
            "No integrations reference metadata found for catalog entries: "
            + ", ".join(repr(key) for key in extra_keys)
        )

    missing_keys = [key for key in doc_keys if key not in integrations]
    if missing_keys:
        raise KeyError(
            "Catalog is missing integrations needed for the reference table: "
            + ", ".join(repr(key) for key in missing_keys)
        )

    for key, label, url, notes in doc_rows:
        agent = f"[{label}]({url})" if url else label
        rows.append([agent, f"`{key}`", notes])

    widths = [
        max(len(header), *(len(_render_cell(row[index])) for row in rows))
        for index, header in enumerate(("Agent", "Key", "Notes"))
    ]

    def render_row(values: list[str]) -> str:
        return "| " + " | ".join(
            _render_cell(value).ljust(widths[index]) for index, value in enumerate(values)
        ) + " |"

    lines = [
        render_row(["Agent", "Key", "Notes"]),
        "| " + " | ".join("-" * width for width in widths) + " |",
    ]
    lines.extend(render_row(row) for row in rows)
    return "\n".join(lines)


def render_integrations_reference(
    catalog_path: Path = INTEGRATIONS_CATALOG_PATH,
    doc_path: Path = INTEGRATIONS_REFERENCE_PATH,
) -> str:
    """Return the integrations reference markdown with the generated table updated."""
    catalog = load_integrations_catalog(catalog_path)
    table = render_integrations_table(catalog)

    content = doc_path.read_text(encoding="utf-8")
    start = content.find(GENERATED_START_MARKER)
    end = content.find(GENERATED_END_MARKER)
    if start == -1 or end == -1 or end < start:
        raise ValueError(
            f"Could not find generated table markers in {doc_path}"
        )

    start_end = start + len(GENERATED_START_MARKER)
    before = content[:start_end]
    after = content[end:]
    generated_block = f"\n\n{table}\n"
    return before + generated_block + after


def update_integrations_reference(
    catalog_path: Path = INTEGRATIONS_CATALOG_PATH,
    doc_path: Path = INTEGRATIONS_REFERENCE_PATH,
) -> str:
    """Rewrite the integrations reference markdown file and return the new content."""
    updated = render_integrations_reference(catalog_path, doc_path)
    doc_path.write_text(updated, encoding="utf-8")
    return updated
