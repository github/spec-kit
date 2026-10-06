"""Workflow overlay composer — builds a WorkflowDefinition from layers."""

from __future__ import annotations

from typing import Any

from ..engine import WorkflowDefinition
from .layer_sources import Layer
from .merge import OverlayLayer, merge_steps, validate_edits


class StepListComposer:
    """Compose a workflow from a base layer and overlay layers.

    - The base layer (tier="base") provides the full step list.
    - Overlay layers provide edit operations.
    - Overlays are applied in merge order: highest priority number first,
      lowest last, so lower priority numbers win. Ties are applied by overlay
      ID, with the alphabetically last ID winning.
    - Returns a parsed WorkflowDefinition; callers must validate separately.
    """

    def compose(
        self, layers: list[Layer]
    ) -> tuple[WorkflowDefinition | None, list]:
        """Compose a ``WorkflowDefinition`` from the given layers.

        Returns ``(None, [])`` when no base layer is present.
        """
        base_layer: Layer | None = None
        overlay_layers: list[Layer] = []
        for layer in layers:
            if layer.tier == "base":
                base_layer = layer
            else:
                overlay_layers.append(layer)

        if base_layer is None or base_layer.path is None:
            return None, []

        # Read the base workflow definition from disk.
        base_definition = WorkflowDefinition.from_yaml(base_layer.path)
        base_steps = base_definition.data.get("steps", [])
        if not isinstance(base_steps, list):
            # Preserve the invalid definition intact so validate_workflow can
            # report "'steps' must be a list." to the caller; coercing to []
            # here would mask that error.
            return base_definition, []

        # Last applied wins, so apply lower priority numbers last.
        merge_order = sorted(
            overlay_layers,
            key=lambda layer: (-layer.priority, layer.content.id),
        )

        # Validate edits against base anchors before mutation.
        base_step_ids = self._collect_base_step_ids(base_steps)
        for layer in merge_order:
            edit_errors = validate_edits(layer.content.edits, base_step_ids)
            if edit_errors:
                raise ValueError(
                    f"Overlay '{layer.content.id}' has invalid edits:\n  - "
                    + "\n  - ".join(edit_errors)
                )

        composed_steps, attribution = merge_steps(
            base_steps,
            [OverlayLayer(layer.content, layer.source) for layer in merge_order],
        )

        # Build composed data while preserving all non-step fields from base.
        composed_data: dict[str, Any] = dict(base_definition.data)
        composed_data["steps"] = composed_steps

        composed_definition = WorkflowDefinition(composed_data, source_path=base_layer.path)

        return composed_definition, attribution

    def _collect_base_step_ids(self, steps: list[dict[str, Any]]) -> set[str]:
        """Collect all base step IDs reachable in the step tree."""
        ids: set[str] = set()
        for step in steps:
            if not isinstance(step, dict):
                continue
            step_id = step.get("id")
            if isinstance(step_id, str):
                ids.add(step_id)
            for key in ("then", "else", "steps", "default"):
                nested = step.get(key)
                if isinstance(nested, list):
                    ids.update(self._collect_base_step_ids(nested))
            cases = step.get("cases")
            if isinstance(cases, dict):
                for case_steps in cases.values():
                    if isinstance(case_steps, list):
                        ids.update(self._collect_base_step_ids(case_steps))
        return ids
