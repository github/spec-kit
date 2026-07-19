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
from .schema import _RESERVED_WORKFLOW_IDS, _SAFE_ID_PATTERN


def _validate_workflow_id(workflow_id: str) -> None:
    """Reject workflow IDs that are unsafe as installed-storage path segments."""
    if (
        not isinstance(workflow_id, str)
        or not _SAFE_ID_PATTERN.fullmatch(workflow_id)
        or workflow_id in _RESERVED_WORKFLOW_IDS
    ):
        raise ValueError(f"Invalid workflow ID: {workflow_id!r}")


class WorkflowResolver:
    """Resolves a workflow ID to its composed ``WorkflowDefinition``.

    Collects layers from two tiers:
    - project-local overlays (``.specify/workflows/overlays/<id>/*.yml``)
    - the base workflow itself (``.specify/workflows/<id>/workflow.yml``)

    Resolution is lower-wins: overlays with lower priority numbers are applied
    later and override earlier edits on the same anchors.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self._sources = [
            ProjectOverlaySource(project_root),
            BaseWorkflowSource(project_root),
        ]
        self._composer = StepListComposer()

    def collect_all_layers(
        self, workflow_id: str, *, include_disabled: bool = False
    ) -> list[Layer]:
        """Collect overlays sorted by precedence, followed by the base layer.

        Lower priority numbers win. Ties are sorted alphabetically by source,
        matching ``PresetRegistry.list_by_priority()``. The base workflow is a
        foundation rather than a precedence candidate, so it is kept separate.
        """
        _validate_workflow_id(workflow_id)

        all_layers: list[Layer] = []
        for source in self._sources:
            all_layers.extend(
                source.collect(workflow_id, include_disabled=include_disabled)
            )

        overlays = [layer for layer in all_layers if layer.tier != "base"]
        base_layers = [layer for layer in all_layers if layer.tier == "base"]
        return (
            sorted(overlays, key=lambda layer: (layer.priority, layer.source))
            + base_layers
        )

    def resolve(self, workflow_id: str) -> WorkflowDefinition:
        """Resolve a workflow ID to its composed definition.

        This method composes layers but does not validate workflow semantics;
        callers should validate the returned definition when needed.

        Raises:
            FileNotFoundError: if the workflow cannot be found.
            ValueError: if layer collection/composition fails.
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
