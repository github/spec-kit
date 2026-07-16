"""Workflow overlay resolver — composes installed workflows from layers."""

from __future__ import annotations

from pathlib import Path

from ..engine import WorkflowDefinition
from .composer import StepListComposer
from .layer_sources import (
    BaseWorkflowSource,
    Layer,
    ProjectOverlaySource,
)
from .merge import ComposedStep


class WorkflowResolver:
    """Resolves a workflow ID to its composed ``WorkflowDefinition``.

    Collects layers from two tiers:
    - project-local overlays (``.specify/workflows/overlays/<id>/*.yml``)
    - the base workflow itself (``.specify/workflows/<id>/workflow.yml``)

    Resolution is higher-wins: overlays with higher priority are applied
    later and override earlier edits on the same anchors.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self._sources = [
            ProjectOverlaySource(project_root),
            BaseWorkflowSource(project_root),
        ]
        self._composer = StepListComposer()

    def collect_all_layers(self, workflow_id: str) -> list[Layer]:
        """Collect all layers sorted by resolver precedence.

        Higher priority wins. Ties are broken alphabetically by source.
        """
        all_layers: list[Layer] = []
        for source in self._sources:
            all_layers.extend(source.collect(workflow_id))

        return sorted(
            all_layers,
            key=lambda layer: (-layer.priority, layer.source),
        )

    def resolve(self, workflow_id: str) -> WorkflowDefinition:
        """Resolve a workflow ID to its composed definition.

        Raises:
            FileNotFoundError: if the workflow cannot be found.
            ValueError: if the composed workflow is invalid.
        """
        layers = self.collect_all_layers(workflow_id)
        definition, _ = self._composer.compose(layers)
        if definition is None:
            raise FileNotFoundError(f"Workflow not found: {workflow_id}")
        return definition

    def resolve_with_layers(
        self, workflow_id: str
    ) -> tuple[WorkflowDefinition, list[Layer], list[ComposedStep]]:
        """Resolve a workflow and return its definition plus layer attribution."""
        layers = self.collect_all_layers(workflow_id)
        definition, attribution = self._composer.compose(layers)
        if definition is None:
            raise FileNotFoundError(f"Workflow not found: {workflow_id}")
        return definition, layers, attribution

