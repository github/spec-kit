"""Workflow overlay layer sources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .schema import Overlay, _RESERVED_WORKFLOW_IDS, _SAFE_ID_PATTERN, validate_overlay_yaml


@dataclass
class Layer:
    """A single layer in the workflow overlay stack."""

    content: Overlay
    source: str
    tier: str
    priority: int
    path: Path | None = None


class OverlayLoadError(ValueError):
    """Raised when an overlay file cannot be loaded or validated."""

    def __init__(self, path: Path, errors: list[str]) -> None:
        self.path = path
        self.errors = errors
        super().__init__(f"Invalid overlay {path}:\n  - " + "\n  - ".join(errors))


def _validate_workflow_id(workflow_id: str, context_path: Path) -> None:
    """Raise OverlayLoadError if workflow_id is not a safe path-segment identifier.

    Mirrors the same check performed by WorkflowResolver so layer sources are
    safe to call directly, without going through the resolver.
    """
    if (
        not isinstance(workflow_id, str)
        or not _SAFE_ID_PATTERN.fullmatch(workflow_id)
        or workflow_id in _RESERVED_WORKFLOW_IDS
    ):
        raise OverlayLoadError(
            context_path,
            [f"Invalid workflow ID: {workflow_id!r}"],
        )


def _ensure_contained_dir(path: Path, root: Path) -> None:
    """Raise OverlayLoadError if *path* is a symlink, a non-directory, or escapes *root*.

    Mirrors the logic of ``_ensure_contained_dir`` in ``overlays/_commands.py``
    but raises ``OverlayLoadError`` instead of ``typer.Exit`` so layer sources
    can enforce the same invariants without a CLI dependency.

    The caller is responsible for ensuring *root* itself is already validated
    (e.g. via ``_resolve_project_overlay_root``).
    """
    if path.is_symlink():
        raise OverlayLoadError(path, ["Symlinked overlay directories are not allowed"])
    if path.exists() and not path.is_dir():
        raise OverlayLoadError(path, ["Overlay directory path is not a directory"])
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        raise OverlayLoadError(
            path, ["Path traversal detected: directory escapes allowed root"]
        ) from None


def _resolve_workflows_root(project_root: Path) -> Path:
    """Return the workflow storage root after rejecting unsafe ancestors."""
    project_root_resolved = project_root.resolve()
    workflows_root = project_root / ".specify" / "workflows"

    current = project_root
    for part in (".specify", "workflows"):
        current = current / part
        if current.is_symlink():
            raise OverlayLoadError(
                current,
                [f"Symlinked workflow directories are not allowed ({current})"],
            )
        if current.exists() and not current.is_dir():
            raise OverlayLoadError(
                current,
                [f"Workflow directory path is not a directory ({current})"],
            )

    try:
        workflows_root.resolve().relative_to(project_root_resolved)
    except ValueError:
        raise OverlayLoadError(
            workflows_root,
            ["Workflow directory escapes the project root"],
        ) from None
    return workflows_root


def _resolve_project_overlay_root(project_root: Path) -> Path:
    """Return the unresolved overlay root after rejecting unsafe ancestors."""
    workflows_root = _resolve_workflows_root(project_root)
    overlays_root = workflows_root / "overlays"
    if overlays_root.is_symlink():
        raise OverlayLoadError(
            overlays_root,
            [f"Symlinked overlay directories are not allowed ({overlays_root})"],
        )
    if overlays_root.exists() and not overlays_root.is_dir():
        raise OverlayLoadError(
            overlays_root,
            [f"Overlay directory path is not a directory ({overlays_root})"],
        )
    return overlays_root


class ProjectOverlaySource:
    """Project-local overlays: ``.specify/workflows/overlays/<id>/*.yml``."""

    tier = "project-overlay"

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.overlays_dir = project_root / ".specify" / "workflows" / "overlays"

    def collect(self, workflow_id: str, *, include_disabled: bool = False) -> list[Layer]:
        """Collect project-local overlays for the given workflow id.

        Args:
            workflow_id: Workflow identifier whose overlay directory to scan.
            include_disabled: When True, return disabled overlays for
                management/list views. Resolution paths keep the default False.
        """
        self.overlays_dir = _resolve_project_overlay_root(self.project_root)
        _validate_workflow_id(workflow_id, self.overlays_dir)
        workflow_overlay_dir = self.overlays_dir / workflow_id
        _ensure_contained_dir(workflow_overlay_dir, self.overlays_dir)
        if not workflow_overlay_dir.is_dir():
            return []
        layers: list[Layer] = []
        overlay_paths_by_id: dict[str, Path] = {}
        try:
            entries = sorted(workflow_overlay_dir.iterdir())
        except OSError as exc:
            raise OverlayLoadError(
                workflow_overlay_dir, [f"Cannot enumerate overlays: {exc}"]
            ) from exc
        for path in entries:
            if not path.is_file() or path.suffix not in (".yml", ".yaml"):
                continue
            if path.is_symlink():
                raise OverlayLoadError(path, ["Symlinked overlay files are not allowed"])
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError as exc:
                raise OverlayLoadError(path, [f"Invalid YAML: {exc}"]) from exc
            except (OSError, UnicodeDecodeError) as exc:
                raise OverlayLoadError(path, [f"Cannot load overlay: {exc}"]) from exc
            if (
                not include_disabled
                and isinstance(data, dict)
                and data.get("enabled", True) is False
            ):
                continue
            overlay, errors = validate_overlay_yaml(data)
            if overlay is None or errors:
                raise OverlayLoadError(path, errors)
            if overlay.extends != workflow_id:
                raise OverlayLoadError(
                    path,
                    [
                        f"Overlay extends {overlay.extends!r}, but is stored under "
                        f"workflow {workflow_id!r}."
                    ],
                )
            first_path = overlay_paths_by_id.get(overlay.id)
            if first_path is not None:
                raise OverlayLoadError(
                    path,
                    [
                        f"Duplicate overlay id {overlay.id!r}; also declared in "
                        f"{first_path}."
                    ],
                )
            overlay_paths_by_id[overlay.id] = path
            layers.append(
                Layer(
                    content=overlay,
                    source=f"project:{overlay.id}",
                    tier=self.tier,
                    priority=overlay.priority,
                    path=path,
                )
            )
        return layers


class BaseWorkflowSource:
    """Base workflow layer: ``.specify/workflows/<id>/workflow.yml``."""

    tier = "base"

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.workflows_dir = project_root / ".specify" / "workflows"

    def collect(self, workflow_id: str, *, include_disabled: bool = False) -> list[Layer]:
        """Return the base workflow as a single layer if it exists."""
        self.workflows_dir = _resolve_workflows_root(self.project_root)
        _validate_workflow_id(workflow_id, self.workflows_dir)
        workflow_dir = self.workflows_dir / workflow_id
        _ensure_contained_dir(workflow_dir, self.workflows_dir)
        path = workflow_dir / "workflow.yml"
        if path.is_symlink():
            raise OverlayLoadError(path, ["Symlinked workflow files are not allowed"])
        if not path.is_file():
            return []
        # The base layer is represented by an Overlay with empty edits.
        overlay = Overlay(
            id=workflow_id,
            extends=workflow_id,
            priority=0,
            edits=[],
        )
        return [
            Layer(
                content=overlay,
                source="base",
                tier=self.tier,
                priority=0,
                path=path,
            )
        ]
