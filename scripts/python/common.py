"""Shared helpers for Spec Kit Python scripts."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path


def _trim_trailing_separators(value: Path) -> str:
    text = str(value)
    while len(text) > 1 and text.endswith((os.sep, "/")):
        text = text[:-1]
    return text


def find_specify_root(start_dir: Path | None = None) -> Path | None:
    current = (start_dir or Path.cwd()).resolve()
    while True:
        if (current / ".specify").is_dir():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def resolve_specify_init_dir() -> Path:
    raw = os.environ.get("SPECIFY_INIT_DIR", "")
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    try:
        init_root = candidate.resolve(strict=True)
    except OSError:
        print(
            f"ERROR: SPECIFY_INIT_DIR does not point to an existing directory: {raw}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if not init_root.is_dir():
        print(
            f"ERROR: SPECIFY_INIT_DIR does not point to an existing directory: {raw}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if not (init_root / ".specify").is_dir():
        print(
            "ERROR: SPECIFY_INIT_DIR is not a Spec Kit project "
            f"(no .specify/ directory): {init_root}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return init_root


def get_repo_root(script_file: Path | None = None) -> Path:
    if os.environ.get("SPECIFY_INIT_DIR"):
        return resolve_specify_init_dir()

    specify_root = find_specify_root()
    if specify_root is not None:
        return specify_root

    if script_file is not None:
        script_root = find_specify_root(script_file.resolve().parent)
        if script_root is not None:
            return script_root

        # Installed scripts live at .specify/scripts/python/<script>.py.
        return script_file.resolve().parents[3]
    return Path.cwd().resolve()


def get_current_branch() -> str:
    return os.environ.get("SPECIFY_FEATURE", "")


def read_feature_json_feature_directory(repo_root: Path) -> str:
    feature_json = repo_root / ".specify" / "feature.json"
    if not feature_json.is_file():
        return ""
    try:
        data = json.loads(feature_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ""
    value = data.get("feature_directory") if isinstance(data, dict) else None
    return value if isinstance(value, str) else ""


def _json_dump(data: dict[str, str]) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"


def persist_feature_json(repo_root: Path, feature_dir_value: str) -> None:
    # Strip the repo root prefix lexically (no resolve()) to mirror the
    # Bash/PowerShell helpers: with a symlinked <repo>/specs, resolve() would
    # escape the repo and persist a machine-specific absolute path instead of
    # the relative "specs/NNN-name" the other variants store.
    value = feature_dir_value
    relative = Path(value)
    if relative.is_absolute():
        try:
            value = relative.relative_to(repo_root).as_posix()
        except ValueError:
            value = str(relative)

    current = read_feature_json_feature_directory(repo_root)
    if current == value:
        return

    specify_dir = repo_root / ".specify"
    specify_dir.mkdir(parents=True, exist_ok=True)
    (specify_dir / "feature.json").write_bytes(
        _json_dump({"feature_directory": value}).encode("utf-8")
    )


@dataclass(frozen=True)
class FeaturePaths:
    repo_root: Path
    current_branch: str
    feature_dir: Path
    feature_spec: Path
    impl_plan: Path
    tasks: Path
    research: Path
    data_model: Path
    quickstart: Path
    contracts_dir: Path


def get_feature_paths(
    *, no_persist: bool = False, script_file: Path | None = None
) -> FeaturePaths:
    repo_root = get_repo_root(script_file)
    current_branch = get_current_branch()

    feature_dir_raw = os.environ.get("SPECIFY_FEATURE_DIRECTORY", "")
    if feature_dir_raw:
        feature_dir = Path(feature_dir_raw)
        if not feature_dir.is_absolute():
            feature_dir = repo_root / feature_dir
        if not no_persist:
            persist_feature_json(repo_root, feature_dir_raw)
    elif (repo_root / ".specify" / "feature.json").is_file():
        stored = read_feature_json_feature_directory(repo_root)
        if not stored:
            print(
                "ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY "
                "or ensure .specify/feature.json contains feature_directory.",
                file=sys.stderr,
            )
            raise SystemExit(1)
        feature_dir = Path(stored)
        if not feature_dir.is_absolute():
            feature_dir = repo_root / feature_dir
    else:
        print(
            "ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY "
            "or run the specify command to create .specify/feature.json.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if not current_branch:
        current_branch = Path(_trim_trailing_separators(feature_dir)).name

    return FeaturePaths(
        repo_root=repo_root,
        current_branch=current_branch,
        feature_dir=feature_dir,
        feature_spec=feature_dir / "spec.md",
        impl_plan=feature_dir / "plan.md",
        tasks=feature_dir / "tasks.md",
        research=feature_dir / "research.md",
        data_model=feature_dir / "data-model.md",
        quickstart=feature_dir / "quickstart.md",
        contracts_dir=feature_dir / "contracts",
    )


def _sorted_preset_ids(presets_dir: Path) -> list[str]:
    registry = presets_dir / ".registry"
    if registry.is_file():
        # Mirrors bash: any failure while reading or sorting the registry
        # (invalid JSON, non-dict shapes, unorderable priority values) falls
        # back to the directory scan below.
        try:
            data = json.loads(registry.read_text(encoding="utf-8"))
            presets = data.get("presets", {})
            return [
                pid
                for pid, meta in sorted(
                    presets.items(),
                    key=lambda kv: kv[1].get("priority", 10)
                    if isinstance(kv[1], dict)
                    else 10,
                )
                if isinstance(meta, dict) and meta.get("enabled", True) is not False
            ]
        except Exception:
            pass
    try:
        return sorted(
            p.name
            for p in presets_dir.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        )
    except OSError:
        return []


def resolve_template(template_name: str, repo_root: Path) -> Path | None:
    """Resolve a template name to a file path using the priority stack.

    Order (mirrors resolve_template in scripts/bash/common.sh):
      1. .specify/templates/overrides/
      2. .specify/presets/<preset-id>/templates/ (sorted by .registry priority)
      3. .specify/extensions/<ext-id>/templates/ (hidden directories skipped)
      4. .specify/templates/ (core)
    """
    base = repo_root / ".specify" / "templates"

    override = base / "overrides" / f"{template_name}.md"
    if override.is_file():
        return override

    presets_dir = repo_root / ".specify" / "presets"
    if presets_dir.is_dir():
        for preset_id in _sorted_preset_ids(presets_dir):
            candidate = presets_dir / preset_id / "templates" / f"{template_name}.md"
            if candidate.is_file():
                return candidate

    ext_dir = repo_root / ".specify" / "extensions"
    if ext_dir.is_dir():
        try:
            extensions = sorted(p for p in ext_dir.iterdir() if p.is_dir())
        except OSError:
            extensions = []
        for ext in extensions:
            if ext.name.startswith("."):
                continue
            candidate = ext / "templates" / f"{template_name}.md"
            if candidate.is_file():
                return candidate

    core = base / f"{template_name}.md"
    if core.is_file():
        return core
    return None


def get_invoke_separator(repo_root: Path) -> str:
    integration_json = repo_root / ".specify" / "integration.json"
    if not integration_json.is_file():
        return "."
    try:
        state = json.loads(integration_json.read_text(encoding="utf-8"))
        key = state.get("default_integration") or state.get("integration") or ""
        settings = state.get("integration_settings")
        if isinstance(key, str) and isinstance(settings, dict):
            entry = settings.get(key)
            if isinstance(entry, dict) and entry.get("invoke_separator") in {".", "-"}:
                return entry["invoke_separator"]
    except (OSError, json.JSONDecodeError):
        pass
    return "."


def format_speckit_command(command_name: str, repo_root: Path) -> str:
    separator = get_invoke_separator(repo_root)
    name = command_name.lstrip("/")
    if name.startswith("speckit."):
        name = name[len("speckit.") :]
    elif name.startswith("speckit-"):
        name = name[len("speckit-") :]
    name = name.replace(".", separator)
    return f"/speckit{separator}{name}"
