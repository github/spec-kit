"""Core (baseline) asset inventory for the specify-cli package.

Public entry point: :func:`build_core_inventory` returns a fixed-shape dict
enumerating the baseline commands, templates, and scripts that ship inside
the wheel (`specify_cli/core_pack/`) or the source checkout (repo root).

The output is the exact shape validated by
``specs/001-core-inventory/contracts/core-info-schema.json``. See
``specs/001-core-inventory/data-model.md`` for authoritative field types.

Every asset carries a stable identifier per companion issue #4210:
``core:_:{kind}:{name}``. Ordering: alphabetical by ``name`` within each
list. Failure mode: any packaging inconsistency (missing shipped file,
unparseable frontmatter, script with zero runtimes) raises
:class:`CoreInventoryError` — the caller emits a JSON error envelope to
stderr and exits non-zero (FR-012).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .._assets import _locate_core_pack, _repo_root

__all__ = ["build_core_inventory", "CoreInventoryError"]

_TEMPLATE_SUFFIX = "-template.md"
_RUNTIMES: tuple[tuple[str, str, str], ...] = (
    # (runtime name, source-layout subdir, filename suffix)
    ("bash", "bash", ".sh"),
    ("powershell", "powershell", ".ps1"),
    ("python", "python", ".py"),
)


class CoreInventoryError(Exception):
    """Raised when the shipped baseline is inconsistent (FR-012)."""

    def __init__(
        self,
        error: str,
        message: str,
        *,
        kind: str | None = None,
        name: str | None = None,
        source_path: str | None = None,
    ) -> None:
        super().__init__(message)
        self.error = error
        self.message = message
        self.kind = kind
        self.name = name
        self.source_path = source_path

    def to_envelope(self) -> dict[str, Any]:
        if self.kind is None and self.name is None and self.source_path is None:
            artifact: dict[str, Any] | None = None
        else:
            artifact = {
                "kind": self.kind,
                "name": self.name,
                "sourcePath": self.source_path,
            }
        return {"error": self.error, "message": self.message, "artifact": artifact}

    def __str__(self) -> str:  # pragma: no cover
        return self.message


@dataclass(frozen=True)
class _CoreLayout:
    """Filesystem layout for the resolved core-asset base.

    Two shapes are supported. Wheel install: ``core_pack/commands/``,
    ``core_pack/templates/``, ``core_pack/scripts/``. Source checkout:
    ``templates/commands/``, ``templates/``, ``scripts/``. The emitted
    ``sourcePath`` is always the source-layout form so wheel and source
    outputs are byte-identical (FR-010, SC-002).
    """

    commands_dir: Path
    templates_dir: Path
    scripts_dir: Path

    @staticmethod
    def command_source_path(name: str) -> str:
        return f"templates/commands/{name}.md"

    @staticmethod
    def template_source_path(filename: str) -> str:
        return f"templates/{filename}"

    @staticmethod
    def script_source_path(runtime_subdir: str, filename: str) -> str:
        return f"scripts/{runtime_subdir}/{filename}"


def _resolve_core_root() -> _CoreLayout:
    """Return a layout resolved against the wheel core_pack or repo root.

    Prefers the wheel-install location (``_locate_core_pack``); falls back
    to the source checkout (``_repo_root``). Raises :class:`CoreInventoryError`
    if neither location has the expected asset subtrees.
    """
    core_pack = _locate_core_pack()
    candidates: list[_CoreLayout] = []
    if core_pack is not None:
        candidates.append(
            _CoreLayout(
                commands_dir=core_pack / "commands",
                templates_dir=core_pack / "templates",
                scripts_dir=core_pack / "scripts",
            )
        )
    repo = _repo_root()
    candidates.append(
        _CoreLayout(
            commands_dir=repo / "templates" / "commands",
            templates_dir=repo / "templates",
            scripts_dir=repo / "scripts",
        )
    )

    for layout in candidates:
        if (
            layout.commands_dir.is_dir()
            and layout.templates_dir.is_dir()
            and layout.scripts_dir.is_dir()
        ):
            return layout

    raise CoreInventoryError(
        error="core_inventory.assets_missing",
        message=(
            "Could not locate baseline commands/, templates/, and scripts/ "
            "under either the wheel core_pack or the source checkout."
        ),
    )


def _package_relative(path: str) -> str:
    """Normalize to a POSIX package-relative path.

    Enforces the ``packageRelativePath`` grammar from the JSON Schema:
    no leading slash, no backslash. Defensive — callers already build
    forward-slash source-layout strings.
    """
    if "\\" in path or path.startswith("/"):
        raise CoreInventoryError(
            error="core_inventory.invalid_source_path",
            message=f"sourcePath must be package-relative POSIX: {path!r}",
        )
    return path


def _read_leading_frontmatter(md_path: Path, *, kind: str, name: str) -> dict[str, Any]:
    """Parse the ``---``-fenced YAML block at the head of ``md_path``.

    Returns ``{}`` if the file has no frontmatter block. Raises
    :class:`CoreInventoryError` on an unclosed fence or non-mapping payload.
    Imports :mod:`yaml` lazily so module import stays cheap (constitution IV).
    """
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CoreInventoryError(
            error="core_inventory.read_failed",
            message=f"Could not read {kind} file: {exc}",
            kind=kind,
            name=name,
            source_path=str(md_path),
        ) from exc

    if not text.startswith("---"):
        return {}

    lines = text.splitlines()
    close_idx: int | None = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            close_idx = idx
            break
    if close_idx is None:
        raise CoreInventoryError(
            error="core_inventory.frontmatter_parse",
            message=(
                f"Unclosed YAML frontmatter fence in {kind} '{name}' "
                f"({md_path.name})."
            ),
            kind=kind,
            name=name,
            source_path=str(md_path),
        )

    import yaml  # lazy import per constitution IV

    body = "\n".join(lines[1:close_idx])
    try:
        parsed = yaml.safe_load(body) if body.strip() else {}
    except yaml.YAMLError as exc:
        raise CoreInventoryError(
            error="core_inventory.frontmatter_parse",
            message=(
                f"Could not parse YAML frontmatter of {kind} '{name}': {exc}"
            ),
            kind=kind,
            name=name,
            source_path=str(md_path),
        ) from exc

    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise CoreInventoryError(
            error="core_inventory.frontmatter_parse",
            message=(
                f"Frontmatter of {kind} '{name}' must be a mapping, got "
                f"{type(parsed).__name__}."
            ),
            kind=kind,
            name=name,
            source_path=str(md_path),
        )
    return parsed


def _normalize_handoffs(raw: Any, *, name: str, source_path: str) -> list[str]:
    """Coerce ``handoffs`` frontmatter value to ``list[str]``.

    Real-world frontmatter uses list-of-mappings with an ``agent:`` field
    (see ``templates/commands/specify.md``); we surface just the agent
    identifiers, which is what downstream join logic needs. Bare-string
    lists (contract-compliant) pass through unchanged. Absent → ``[]``.
    """
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise CoreInventoryError(
            error="core_inventory.frontmatter_parse",
            message=(
                f"Command '{name}' has a non-list 'handoffs' frontmatter "
                f"field ({type(raw).__name__})."
            ),
            kind="command",
            name=name,
            source_path=source_path,
        )
    result: list[str] = []
    for entry in raw:
        if isinstance(entry, str):
            result.append(entry)
        elif isinstance(entry, dict) and isinstance(entry.get("agent"), str):
            result.append(entry["agent"])
        else:
            raise CoreInventoryError(
                error="core_inventory.frontmatter_parse",
                message=(
                    f"Command '{name}' has an unrecognized 'handoffs' entry "
                    f"({entry!r}); expected string or mapping with 'agent'."
                ),
                kind="command",
                name=name,
                source_path=source_path,
            )
    return result


def _normalize_description(raw: Any, *, kind: str, name: str, source_path: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise CoreInventoryError(
            error="core_inventory.missing_description",
            message=f"{kind.capitalize()} '{name}' is missing a description.",
            kind=kind,
            name=name,
            source_path=source_path,
        )
    return " ".join(raw.split())


def _build_command_entry(name: str, layout: _CoreLayout) -> dict[str, Any]:
    file_path = layout.commands_dir / f"{name}.md"
    source_path = _package_relative(layout.command_source_path(name))
    if not file_path.is_file():
        raise CoreInventoryError(
            error="core_inventory.missing_file",
            message=(
                f"Baseline command file for '{name}' not found "
                f"(expected at {file_path})."
            ),
            kind="command",
            name=name,
            source_path=source_path,
        )
    frontmatter = _read_leading_frontmatter(file_path, kind="command", name=name)
    description = _normalize_description(
        frontmatter.get("description"),
        kind="command",
        name=name,
        source_path=source_path,
    )
    artifact = frontmatter.get("artifact")
    if artifact is not None and not isinstance(artifact, str):
        raise CoreInventoryError(
            error="core_inventory.frontmatter_parse",
            message=(
                f"Command '{name}' has a non-string 'artifact' frontmatter "
                f"field ({type(artifact).__name__})."
            ),
            kind="command",
            name=name,
            source_path=source_path,
        )
    optional_raw = frontmatter.get("optional", False)
    if not isinstance(optional_raw, bool):
        raise CoreInventoryError(
            error="core_inventory.frontmatter_parse",
            message=(
                f"Command '{name}' has a non-boolean 'optional' frontmatter "
                f"field ({type(optional_raw).__name__})."
            ),
            kind="command",
            name=name,
            source_path=source_path,
        )
    handoffs = _normalize_handoffs(
        frontmatter.get("handoffs"), name=name, source_path=source_path
    )
    return {
        "id": f"core:_:command:{name}",
        "name": name,
        "description": description,
        "sourcePath": source_path,
        "artifact": artifact,
        "optional": optional_raw,
        "handoffs": handoffs,
    }


def _extract_template_description(md_path: Path, *, name: str, source_path: str) -> str:
    """Return the template's description.

    Prefers the frontmatter ``description:`` field; falls back to the first
    ``# `` H1 heading. Raises :class:`CoreInventoryError` if neither yields
    a non-empty string.
    """
    frontmatter = _read_leading_frontmatter(md_path, kind="template", name=name)
    fm_desc = frontmatter.get("description")
    if isinstance(fm_desc, str):
        candidate = fm_desc.strip()
        if candidate:
            return " ".join(candidate.split())

    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover
        raise CoreInventoryError(
            error="core_inventory.read_failed",
            message=f"Could not read template file: {exc}",
            kind="template",
            name=name,
            source_path=source_path,
        ) from exc

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            heading = stripped[2:].strip()
            if heading:
                return " ".join(heading.split())

    raise CoreInventoryError(
        error="core_inventory.missing_description",
        message=(
            f"Template '{name}' has no description in frontmatter and no "
            f"H1 heading; cannot derive a description."
        ),
        kind="template",
        name=name,
        source_path=source_path,
    )


def _build_template_entries(layout: _CoreLayout) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for md_path in sorted(layout.templates_dir.glob(f"*{_TEMPLATE_SUFFIX}")):
        if not md_path.is_file():
            continue
        name = md_path.stem
        source_path = _package_relative(layout.template_source_path(md_path.name))
        description = _extract_template_description(
            md_path, name=name, source_path=source_path
        )
        entries.append(
            {
                "id": f"core:_:template:{name}",
                "name": name,
                "description": description,
                "sourcePath": source_path,
            }
        )
    entries.sort(key=lambda entry: entry["name"])
    return entries


def _script_logical_name(runtime_subdir: str, filename: str) -> str:
    """Return the logical script name for a runtime-variant filename.

    Python filenames use underscores (`setup_plan.py`); the logical name is
    always hyphenated (`setup-plan`). Bash/PowerShell already use hyphens.
    """
    stem = Path(filename).stem
    if runtime_subdir == "python":
        stem = stem.replace("_", "-")
    return stem


def _extract_script_description(bash_path: Path, *, name: str, source_path: str) -> str:
    """Return the description parsed from the bash file's leading comments.

    Skips the shebang and blank lines, then joins consecutive ``#``-prefixed
    lines into a single whitespace-normalized string. Falls back to a
    filename-derived description when the source has no header block — most
    of the shipped baseline scripts today have no doc header, so a strict
    error here would break the whole inventory on day-one code. The
    filename-derived form still satisfies the schema's ``minLength: 1``
    invariant and unambiguously identifies the script.
    """
    try:
        text = bash_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CoreInventoryError(
            error="core_inventory.read_failed",
            message=f"Could not read script file: {exc}",
            kind="script",
            name=name,
            source_path=source_path,
        ) from exc

    comment_lines: list[str] = []
    started = False
    for line in text.splitlines():
        stripped = line.strip()
        if not started:
            if stripped.startswith("#!"):
                continue
            if not stripped:
                continue
        if stripped.startswith("#"):
            started = True
            comment_lines.append(stripped.lstrip("#").strip())
            continue
        if started:
            break
        if stripped:
            break

    joined = " ".join(part for part in comment_lines if part).strip()
    if joined:
        return " ".join(joined.split())
    # Fallback: derive a canonical description from the logical name.
    return f"Baseline helper script: {name}."


def _build_script_entries(layout: _CoreLayout) -> list[dict[str, Any]]:
    per_name: dict[str, dict[str, Path]] = {}
    for runtime_name, subdir, suffix in _RUNTIMES:
        runtime_dir = layout.scripts_dir / subdir
        if not runtime_dir.is_dir():
            continue
        for script_path in runtime_dir.iterdir():
            if not script_path.is_file() or script_path.suffix != suffix:
                continue
            logical = _script_logical_name(subdir, script_path.name)
            per_name.setdefault(logical, {})[runtime_name] = script_path

    entries: list[dict[str, Any]] = []
    for name in sorted(per_name):
        variants = per_name[name]
        bash_path = variants.get("bash")
        if bash_path is None:
            raise CoreInventoryError(
                error="core_inventory.missing_canonical",
                message=(
                    f"Script '{name}' has no bash variant; bash is the "
                    f"canonical runtime for the description + sourcePath."
                ),
                kind="script",
                name=name,
            )
        source_path = _package_relative(
            layout.script_source_path("bash", bash_path.name)
        )
        description = _extract_script_description(
            bash_path, name=name, source_path=source_path
        )
        runtimes = sorted(variants.keys())
        entries.append(
            {
                "id": f"core:_:script:{name}",
                "name": name,
                "description": description,
                "sourcePath": source_path,
                "runtimes": runtimes,
            }
        )
    entries.sort(key=lambda entry: entry["name"])
    return entries


def build_core_inventory() -> dict[str, Any]:
    """Return the baseline inventory as a fixed-shape dict.

    Shape (validated by ``contracts/core-info-schema.json``):
    ``{"commands": [...], "templates": [...], "scripts": [...]}``.

    All three top-level lists are sorted alphabetically by ``name``. Two
    consecutive calls MUST return byte-identical JSON when serialized
    with ``json.dumps(..., sort_keys=False)`` (SC-002).

    Raises :class:`CoreInventoryError` on any packaging inconsistency
    (FR-012). No partial inventory is ever returned.
    """
    layout = _resolve_core_root()

    from ..extensions import _load_core_command_names  # lazy: avoid import cycle

    command_names = sorted(_load_core_command_names())
    commands = [_build_command_entry(name, layout) for name in command_names]
    templates = _build_template_entries(layout)
    scripts = _build_script_entries(layout)
    return {"commands": commands, "templates": templates, "scripts": scripts}
