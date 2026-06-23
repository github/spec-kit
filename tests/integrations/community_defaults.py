"""Expected file inventory for bigsmartben bundled init defaults."""

from pathlib import Path

import yaml

from specify_cli.agents import CommandRegistrar
from specify_cli.extensions import ExtensionManager
from specify_cli.integrations import get_integration

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXTENSION_IDS = ("arch", "preview", "repository-governance")
DEFAULT_EXTENSION_COMMANDS = (
    "speckit.arch.generate",
    "speckit.arch.reverse",
    "speckit.preview.low-md",
    "speckit.preview.low-html",
    "speckit.preview.mid-md",
    "speckit.preview.mid-html",
    "speckit.preview.high-md",
    "speckit.preview.high-html",
    "speckit.repository-governance.refresh",
)
DEFAULT_PRESET_ID = "workflow-preset"
DEFAULT_PRESET_COMMANDS = (
    "speckit.specify",
    "speckit.clarify",
    "speckit.checklist",
    "speckit.constitution",
    "speckit.analyze",
    "speckit.plan",
    "speckit.tasks",
    "speckit.implement",
)


def _copied_extension_files(extension_id: str) -> list[str]:
    source_dir = REPO_ROOT / "extensions" / extension_id
    ignore_fn = ExtensionManager._load_extensionignore(source_dir)
    files: list[str] = []

    for source_file in source_dir.rglob("*"):
        if not source_file.is_file():
            continue
        rel = source_file.relative_to(source_dir)
        if ignore_fn is not None:
            ignored = ignore_fn(str(source_file.parent), [source_file.name])
            if source_file.name in ignored:
                continue
        files.append(f".specify/extensions/{extension_id}/{rel.as_posix()}")

    return files


def _copied_workflow_preset_files() -> list[str]:
    source_dir = REPO_ROOT / "presets" / DEFAULT_PRESET_ID
    files = [
        f".specify/presets/{DEFAULT_PRESET_ID}/{source_file.relative_to(source_dir).as_posix()}"
        for source_file in source_dir.rglob("*")
        if source_file.is_file()
    ]

    preset_data = yaml.safe_load((source_dir / "preset.yml").read_text(encoding="utf-8"))
    for entry in preset_data.get("provides", {}).get("templates", []):
        if (
            isinstance(entry, dict)
            and entry.get("type") == "command"
            and entry.get("strategy") == "wrap"
            and isinstance(entry.get("file"), str)
        ):
            files.append(
                f".specify/presets/{DEFAULT_PRESET_ID}/.composed/{Path(entry['file']).name}"
            )
    return files


def _registered_extension_command_files(
    integration_key: str,
    *,
    skills_mode: bool = False,
    commands_dir: str | None = None,
) -> list[str]:
    integration = get_integration(integration_key)
    config = dict(integration.registrar_config)
    if skills_mode:
        config["dir"] = f"{integration.config['folder']}skills"
        config["extension"] = "/SKILL.md"
    if commands_dir is not None:
        config["dir"] = commands_dir
    command_dir = Path(config["dir"])
    extension = config["extension"]

    files: list[str] = []
    for command_name in DEFAULT_EXTENSION_COMMANDS:
        output_name = CommandRegistrar._compute_output_name(
            integration_key, command_name, config
        )
        if extension == "/SKILL.md":
            files.append((command_dir / output_name / "SKILL.md").as_posix())
        else:
            files.append((command_dir / f"{output_name}{extension}").as_posix())

        if integration_key == "copilot" and not skills_mode:
            files.append(f".github/prompts/{command_name}.prompt.md")

    return files


def _registered_workflow_preset_command_files(
    integration_key: str,
    *,
    skills_mode: bool = False,
    commands_dir: str | None = None,
) -> list[str]:
    integration = get_integration(integration_key)
    config = dict(integration.registrar_config)
    if skills_mode:
        config["dir"] = f"{integration.config['folder']}skills"
        config["extension"] = "/SKILL.md"
    if commands_dir is not None:
        config["dir"] = commands_dir
    command_dir = Path(config["dir"])
    extension = config["extension"]

    files: list[str] = []
    for command_name in DEFAULT_PRESET_COMMANDS:
        output_name = CommandRegistrar._compute_output_name(
            integration_key, command_name, config
        )
        if extension == "/SKILL.md":
            files.append((command_dir / output_name / "SKILL.md").as_posix())
        else:
            files.append((command_dir / f"{output_name}{extension}").as_posix())

        if integration_key == "copilot" and not skills_mode:
            files.append(f".github/prompts/{command_name}.prompt.md")

    return files


def bundled_community_default_files(
    integration_key: str,
    *,
    skills_mode: bool = False,
    commands_dir: str | None = None,
    include_registered_commands: bool = True,
) -> list[str]:
    """Return files added by bigsmartben's default bundled extensions/preset."""
    files = [
        ".specify/extensions.yml",
        ".specify/extensions/.registry",
        ".specify/presets/.registry",
    ]
    for extension_id in DEFAULT_EXTENSION_IDS:
        files.extend(_copied_extension_files(extension_id))
    files.extend(_copied_workflow_preset_files())
    if include_registered_commands:
        files.extend(
            _registered_extension_command_files(
                integration_key,
                skills_mode=skills_mode,
                commands_dir=commands_dir,
            )
        )
        # workflow-preset wraps/replaces core commands whose output paths are already
        # accounted for by each integration's base command inventory.
    return sorted(set(files))
