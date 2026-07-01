"""Developer helpers for scaffolding built-in integrations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IntegrationScaffoldResult:
    """Files and next steps produced by an integration scaffold run."""

    key: str
    package_name: str
    class_name: str
    integration_file: Path
    test_file: Path
    next_steps: tuple[str, ...]


@dataclass(frozen=True)
class _IntegrationTemplate:
    base_class: str
    commands_subdir: str
    registrar_format: str
    args: str
    extension: str


_KEY_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_TEMPLATES = {
    "markdown": _IntegrationTemplate(
        base_class="MarkdownIntegration",
        commands_subdir="commands",
        registrar_format="markdown",
        args="$ARGUMENTS",
        extension=".md",
    ),
    "toml": _IntegrationTemplate(
        base_class="TomlIntegration",
        commands_subdir="commands",
        registrar_format="toml",
        args="{{args}}",
        extension=".toml",
    ),
    "yaml": _IntegrationTemplate(
        base_class="YamlIntegration",
        commands_subdir="recipes",
        registrar_format="yaml",
        args="{{args}}",
        extension=".yaml",
    ),
    "skills": _IntegrationTemplate(
        base_class="SkillsIntegration",
        commands_subdir="skills",
        registrar_format="markdown",
        args="$ARGUMENTS",
        extension="/SKILL.md",
    ),
}


def supported_integration_scaffold_types() -> tuple[str, ...]:
    """Return supported scaffold template names."""
    return tuple(sorted(_TEMPLATES))


def _clean_key(key: str) -> str:
    clean = key.strip()
    if not _KEY_RE.fullmatch(clean):
        raise ValueError(
            "Integration key must be lowercase kebab-case, for example 'my-agent'."
        )
    return clean


def _package_name(key: str) -> str:
    return key.replace("-", "_")


def _class_name(key: str) -> str:
    return "".join(part.capitalize() for part in key.split("-")) + "Integration"


def _display_name(key: str) -> str:
    return " ".join(part.capitalize() for part in key.split("-"))


def _integration_content(
    *,
    key: str,
    class_name: str,
    integration_type: str,
) -> str:
    template = _TEMPLATES[integration_type]
    display_name = _display_name(key)
    folder = f".{key}/"
    commands_dir = f"{folder}{template.commands_subdir}"
    return f'''"""{display_name} integration."""

from ..base import {template.base_class}


class {class_name}({template.base_class}):
    key = "{key}"
    config = {{
        "name": "{display_name}",
        "folder": "{folder}",
        "commands_subdir": "{template.commands_subdir}",
        "install_url": None,
        "requires_cli": False,
    }}
    registrar_config = {{
        "dir": "{commands_dir}",
        "format": "{template.registrar_format}",
        "args": "{template.args}",
        "extension": "{template.extension}",
    }}
    multi_install_safe = False
'''


def _test_content(
    *,
    key: str,
    class_name: str,
    integration_type: str,
) -> str:
    template = _TEMPLATES[integration_type]
    display_name = _display_name(key)
    package_name = _package_name(key)
    commands_dir = f".{key}/{template.commands_subdir}"
    return f'''"""Tests for the {key} integration."""

from specify_cli.integrations.{package_name} import {class_name}
from specify_cli.integrations.base import {template.base_class}


def test_metadata():
    integration = {class_name}()

    assert isinstance(integration, {template.base_class})
    assert integration.key == "{key}"
    assert integration.config["name"] == "{display_name}"
    assert integration.config["folder"] == ".{key}/"
    assert integration.config["commands_subdir"] == "{template.commands_subdir}"
    assert integration.config["requires_cli"] is False
    assert integration.registrar_config["dir"] == "{commands_dir}"
    assert integration.registrar_config["format"] == "{template.registrar_format}"
    assert integration.registrar_config["args"] == "{template.args}"
    assert integration.registrar_config["extension"] == "{template.extension}"
    assert integration.multi_install_safe is False
'''


def _is_spec_kit_repo_root(project_root: Path) -> bool:
    """Return True when `project_root` looks like the Spec Kit repository root."""
    return all(
        (
            (project_root / "pyproject.toml").is_file(),
            (project_root / "src" / "specify_cli" / "__init__.py").is_file(),
            (project_root / "src" / "specify_cli" / "integrations").is_dir(),
            (
                project_root / "src" / "specify_cli" / "integrations" / "__init__.py"
            ).is_file(),
            (project_root / "tests" / "integrations").is_dir(),
        )
    )


def _assert_safe_scaffold_target(project_root: Path, target: Path) -> None:
    """Refuse to scaffold through a symlinked path that could escape the repo.

    Walks each component of *target* under *project_root* and rejects any
    existing symlinked directory (or symlinked target), then confirms the
    write destination still resolves inside the repository root. Mirrors the
    symlink-aware guarding used for integration manifests.
    """
    try:
        rel = target.relative_to(project_root)
    except ValueError:
        raise ValueError(
            f"Refusing to scaffold outside the repository root: {target}"
        ) from None

    current = project_root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            label = current.relative_to(project_root).as_posix()
            raise ValueError(f"Refusing to scaffold through symlinked path: {label}")

    root_resolved = project_root.resolve()
    try:
        target.parent.resolve().relative_to(root_resolved)
    except (OSError, ValueError):
        raise ValueError(
            f"Refusing to scaffold outside the repository root: {target}"
        ) from None


def scaffold_integration(
    project_root: Path,
    key: str,
    integration_type: str,
) -> IntegrationScaffoldResult:
    """Create a minimal built-in integration package and test skeleton."""
    clean_key = _clean_key(key)
    normalized_type = integration_type.strip().lower()
    if normalized_type not in _TEMPLATES:
        supported = ", ".join(supported_integration_scaffold_types())
        raise ValueError(
            f"Unsupported integration type '{normalized_type}'. Use one of: {supported}."
        )

    integrations_root = project_root / "src" / "specify_cli" / "integrations"
    tests_root = project_root / "tests" / "integrations"
    if not _is_spec_kit_repo_root(project_root):
        raise ValueError("Run this command from the Spec Kit repository root.")

    package_name = _package_name(clean_key)
    class_name = _class_name(clean_key)
    integration_dir = integrations_root / package_name
    integration_file = integration_dir / "__init__.py"
    test_file = tests_root / f"test_integration_{package_name}.py"

    for target in (integration_file, test_file):
        _assert_safe_scaffold_target(project_root, target)

    existing = [path for path in (integration_file, test_file) if path.exists()]
    if existing:
        labels = ", ".join(path.relative_to(project_root).as_posix() for path in existing)
        raise FileExistsError(f"Refusing to overwrite existing scaffold file(s): {labels}")

    created_integration_dir = not integration_dir.exists()
    try:
        integration_dir.mkdir(exist_ok=True)
        integration_file.write_text(
            _integration_content(
                key=clean_key,
                class_name=class_name,
                integration_type=normalized_type,
            ),
            encoding="utf-8",
        )
        test_file.write_text(
            _test_content(
                key=clean_key,
                class_name=class_name,
                integration_type=normalized_type,
            ),
            encoding="utf-8",
        )
    except OSError:
        for path in (test_file, integration_file):
            try:
                if path.is_file() or path.is_symlink():
                    path.unlink()
            except OSError:
                pass
        if created_integration_dir:
            try:
                integration_dir.rmdir()
            except OSError:
                pass
        raise

    next_steps = (
        f"Register {class_name} in src/specify_cli/integrations/__init__.py.",
        "Review config metadata, install_url, requires_cli, and multi_install_safe.",
        f"Run pytest tests/integrations/test_integration_{package_name}.py -v.",
    )
    return IntegrationScaffoldResult(
        key=clean_key,
        package_name=package_name,
        class_name=class_name,
        integration_file=integration_file,
        test_file=test_file,
        next_steps=next_steps,
    )
