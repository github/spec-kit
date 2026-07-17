"""Workflow overlay layer sources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .schema import Overlay, validate_overlay_yaml


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


def _resolve_project_overlay_root(project_root: Path) -> Path:
    """Return the unresolved overlay root after rejecting symlinked ancestors.

    This mirrors the older workflow step-directory hardening pattern locally.
    The path-walk / containment logic should be centralized in a shared helper
    in a follow-up DRY pass, but this stays inline here to keep the Cluster 1
    security fix small and low-risk.
    """
    project_root_resolved = project_root.resolve()
    overlays_root = project_root / ".specify" / "workflows" / "overlays"

    current = project_root
    for part in (".specify", "workflows", "overlays"):
        current = current / part
        if current.is_symlink():
            raise OverlayLoadError(
                current,
                [f"Symlinked overlay directories are not allowed ({current})"],
            )
        if current.exists() and not current.is_dir():
            raise OverlayLoadError(
                current,
                [f"Overlay directory path is not a directory ({current})"],
            )

    try:
        overlays_root.resolve().relative_to(project_root_resolved)
    except ValueError:
        raise OverlayLoadError(
            overlays_root,
            ["Overlay directory escapes the project root"],
        ) from None
    return overlays_root


class ProjectOverlaySource:
    """Project-local overlays: ``.specify/workflows/overlays/<id>/*.yml``."""

    tier = "project-overlay"

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.overlays_dir = project_root / ".specify" / "workflows" / "overlays"

    def collect(self, workflow_id: str) -> list[Layer]:
        """Collect all project-local overlays for the given workflow id."""
        self.overlays_dir = _resolve_project_overlay_root(self.project_root)
        workflow_overlay_dir = self.overlays_dir / workflow_id
        if workflow_overlay_dir.is_symlink():
            raise OverlayLoadError(
                workflow_overlay_dir,
                ["Symlinked overlay directories are not allowed"],
            )
        if workflow_overlay_dir.exists() and not workflow_overlay_dir.is_dir():
            raise OverlayLoadError(
                workflow_overlay_dir,
                ["Overlay directory path is not a directory"],
            )
        if not workflow_overlay_dir.is_dir():
            return []
        layers: list[Layer] = []
        for path in sorted(workflow_overlay_dir.iterdir()):
            if not path.is_file() or path.suffix not in (".yml", ".yaml"):
                continue
            if path.is_symlink():
                raise OverlayLoadError(path, ["Symlinked overlay files are not allowed"])
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError as exc:
                raise OverlayLoadError(path, [f"Invalid YAML: {exc}"]) from exc
            overlay, errors = validate_overlay_yaml(data)
            if overlay is None or errors:
                raise OverlayLoadError(path, errors)
            if not overlay.enabled:
                continue
            if overlay.extends != workflow_id:
                continue
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

    def collect(self, workflow_id: str) -> list[Layer]:
        """Return the base workflow as a single layer if it exists."""
        path = self.workflows_dir / workflow_id / "workflow.yml"
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
