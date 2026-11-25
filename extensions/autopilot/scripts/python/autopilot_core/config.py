"""Autopilot configuration: defaults, loading and a small YAML-subset reader.

The config lives at ``.specify/extensions/autopilot/autopilot-config.yml``.
PyYAML is used when importable; otherwise a reader for the subset the
shipped template uses (nested mappings, block lists of scalars or mappings,
flow lists of scalars, quoted/unquoted scalars, comments) takes over, the same
approach the git extension's Python helpers take for ``git-config.yml``.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

CONFIG_RELATIVE = Path(".specify") / "extensions" / "autopilot" / "autopilot-config.yml"

DEFAULTS: dict[str, Any] = {
    "gate": {
        # Project commands that must all exit 0. Empty ``run`` entries are skipped;
        # preflight refuses to start when no check has a command.
        "checks": [],
        "check_timeout_seconds": 1800,
        "require_tasks_complete": True,
        "require_review": True,
        "acceptance": {
            "required": True,
            "test_globs": [
                "tests/**",
                "test/**",
                "spec/**",
                "**/__tests__/**",
                "**/*_test.*",
                "**/*.test.*",
                "**/*.spec.*",
                "**/test_*.*",
            ],
            # Optional per-scenario command; ``{tag}`` and ``{tag_underscore}``
            # are replaced with the scenario ID (always [A-Za-z0-9-]).
            "scenario_command": "",
        },
    },
    "pipe": {
        "max_iterations": 5,
        "stuck_after": 2,
        "timeout_minutes": 120,
        "max_attempts": 1,
        # Questions one developer may raise before the epic counts as under-specified.
        "max_questions": 8,
    },
    "run": {
        "max_parallel": 2,
        "timeout_minutes": 480,
        "max_agent_calls": 200,
        "base_branch": "",
        "integration_branch": "autopilot/integration",
        "branch_prefix": "autopilot/",
        "worktree_root": "",
        "specify_command": "specify",
        # Shell command run once in every new worktree (install dependencies).
        "setup": "",
        "integration": "",
        "reviewer_model": "",
        "lead_model": "",
        "sync_paths": [
            ".specify",
            ".claude",
            ".github/agents",
            ".github/prompts",
            ".github/skills",
            ".gemini",
            ".codex",
            ".opencode",
            ".agents",
            ".cursor",
            ".windsurf",
            ".kiro",
        ],
    },
}


class ConfigError(ValueError):
    """Raised when the config file cannot be read or has the wrong shape."""


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def load_config(project_root: Path, path: Path | None = None) -> dict[str, Any]:
    """Return DEFAULTS merged with the project's config file (if present)."""
    config_path = path or (project_root / CONFIG_RELATIVE)
    if not config_path.is_file():
        return copy.deepcopy(DEFAULTS)
    text = config_path.read_text(encoding="utf-8")
    data = parse_yaml(text)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ConfigError(f"{config_path}: top level must be a mapping")
    config = _deep_merge(DEFAULTS, data)
    _validate(config, config_path)
    return config


def _validate(config: dict[str, Any], path: Path) -> None:
    checks = config["gate"]["checks"]
    if not isinstance(checks, list):
        raise ConfigError(f"{path}: gate.checks must be a list")
    for index, check in enumerate(checks):
        if not isinstance(check, dict) or not isinstance(check.get("name"), str):
            raise ConfigError(f"{path}: gate.checks[{index}] needs a string 'name'")
        if not isinstance(check.get("run", ""), str):
            raise ConfigError(f"{path}: gate.checks[{index}].run must be a string")
    for section, key in (
        ("pipe", "max_iterations"),
        ("pipe", "stuck_after"),
        ("pipe", "timeout_minutes"),
        ("pipe", "max_attempts"),
        ("pipe", "max_questions"),
        ("run", "max_parallel"),
        ("run", "timeout_minutes"),
        ("run", "max_agent_calls"),
        ("gate", "check_timeout_seconds"),
    ):
        value = config[section][key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ConfigError(f"{path}: {section}.{key} must be a positive integer")
    if not isinstance(config["run"]["sync_paths"], list):
        raise ConfigError(f"{path}: run.sync_paths must be a list")


def configured_checks(config: dict[str, Any]) -> list[dict[str, str]]:
    """Checks that have a non-empty command."""
    return [
        {"name": c["name"], "run": c.get("run", "")}
        for c in config["gate"]["checks"]
        if str(c.get("run", "")).strip()
    ]


# ── YAML subset ──────────────────────────────────────────────────────────────


def parse_yaml(text: str) -> Any:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return parse_yaml_subset(text)
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:  # pragma: no cover - message passthrough
        raise ConfigError(f"invalid YAML: {exc}") from exc


_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_\-]*)\s*:(?:\s+(.*))?$")


def _strip_comment(line: str) -> str:
    """Drop a trailing ``# comment`` that is not inside quotes."""
    quote = ""
    for index, char in enumerate(line):
        if quote:
            if char == quote:
                quote = ""
        elif char in "'\"":
            quote = char
        elif char == "#" and (index == 0 or line[index - 1] in " \t"):
            return line[:index].rstrip()
    return line.rstrip()


def _scalar(raw: str) -> Any:
    value = raw.strip()
    if value == "":
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_scalar(part) for part in _split_flow(inner)]
    if value.startswith("{") and value == "{}":
        return {}
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        body = value[1:-1]
        if value[0] == '"':
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return body
        return body.replace("''", "'")
    lowered = value.lower()
    if lowered in ("true", "yes", "on"):
        return True
    if lowered in ("false", "no", "off"):
        return False
    if lowered in ("null", "~", "none"):
        return None
    if re.fullmatch(r"[-+]?\d+", value):
        return int(value)
    if re.fullmatch(r"[-+]?\d*\.\d+", value):
        return float(value)
    return value


def _split_flow(inner: str) -> list[str]:
    parts: list[str] = []
    current = ""
    quote = ""
    for char in inner:
        if quote:
            current += char
            if char == quote:
                quote = ""
        elif char in "'\"":
            quote = char
            current += char
        elif char == ",":
            parts.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current)
    return parts


def parse_yaml_subset(text: str) -> Any:
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise ConfigError("tabs are not allowed for indentation")
        stripped = _strip_comment(raw)
        if not stripped.strip():
            continue
        lines.append((len(stripped) - len(stripped.lstrip(" ")), stripped.strip()))
    if not lines:
        return None
    value, index = _parse_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise ConfigError(f"unexpected content: {lines[index][1]!r}")
    return value


def _parse_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if lines[index][1].startswith("- ") or lines[index][1] == "-":
        return _parse_list(lines, index, indent)
    return _parse_map(lines, index, indent)


def _parse_map(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[dict, int]:
    result: dict[str, Any] = {}
    while index < len(lines):
        line_indent, content = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise ConfigError(f"unexpected indentation: {content!r}")
        match = _KEY_RE.match(content)
        if not match:
            raise ConfigError(f"expected 'key: value', got {content!r}")
        key, rest = match.group(1), match.group(2)
        index += 1
        if rest is None or rest == "":
            if index < len(lines) and (
                lines[index][0] > indent
                or (lines[index][0] == indent and lines[index][1].startswith("-"))
            ):
                child_indent = lines[index][0]
                result[key], index = _parse_block(lines, index, child_indent)
            else:
                result[key] = None
        else:
            result[key] = _scalar(rest)
    return result, index


def _parse_list(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[list, int]:
    result: list[Any] = []
    while index < len(lines):
        line_indent, content = lines[index]
        if line_indent < indent or not (content.startswith("- ") or content == "-"):
            break
        if line_indent > indent:
            raise ConfigError(f"unexpected indentation: {content!r}")
        item = content[1:].strip()
        index += 1
        if not item:
            if index < len(lines) and lines[index][0] > indent:
                value, index = _parse_block(lines, index, lines[index][0])
                result.append(value)
            else:
                result.append(None)
            continue
        if _KEY_RE.match(item):
            # "- key: value" starts an inline mapping; continuation keys are
            # indented to the column after "- ".
            item_indent = indent + 2
            sub_lines = [(item_indent, item)]
            while index < len(lines) and lines[index][0] >= item_indent:
                sub_lines.append(lines[index])
                index += 1
            value, consumed = _parse_map(sub_lines, 0, item_indent)
            if consumed != len(sub_lines):
                raise ConfigError(f"unexpected content in list item: {sub_lines[consumed][1]!r}")
            result.append(value)
        else:
            result.append(_scalar(item))
    return result, index
