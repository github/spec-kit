"""Tests for the workflow overlay merge engine."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from specify_cli.workflows.overlays.merge import (
    ComposedStep,
    OverlayLayer,
    apply_edit,
    find_step,
    merge_steps,
    validate_edits,
)
from specify_cli.workflows.overlays.schema import Overlay, OverlayEdit


def _step(id: str, **kwargs: Any) -> dict[str, Any]:  # noqa: A002
    """Build a minimal step dict with the given id."""
    return {"id": id, "type": "command", "command": "speckit.specify", **kwargs}


def _layer(overlay: Overlay, source: str) -> OverlayLayer:
    """Build an OverlayLayer for merge_steps."""
    return OverlayLayer(overlay, source)


class TestFindStep:
    """Recursive anchor lookup across nested step lists."""

    def test_find_step_flat(self):
        steps = [_step("a"), _step("b"), _step("c")]
        result = find_step(steps, "b")
        assert result is not None
        assert result[0] is steps
        assert result[1] == 1

    def test_find_step_missing(self):
        steps = [_step("a"), _step("b")]
        assert find_step(steps, "missing") is None

    def test_find_step_in_then(self):
        steps = [
            {
                "id": "if-1",
                "type": "if",
                "condition": "true",
                "then": [_step("then-a")],
                "else": [_step("else-b")],
            },
        ]
        result = find_step(steps, "then-a")
        assert result is not None
        assert result[0] is steps[0]["then"]
        assert result[1] == 0

    def test_find_step_in_else(self):
        steps = [
            {
                "id": "if-1",
                "type": "if",
                "condition": "true",
                "then": [_step("then-a")],
                "else": [_step("else-b")],
            },
        ]
        result = find_step(steps, "else-b")
        assert result is not None
        assert result[0] is steps[0]["else"]
        assert result[1] == 0

    def test_find_step_in_nested_steps(self):
        steps = [
            {
                "id": "while-1",
                "type": "while",
                "condition": "true",
                "steps": [_step("inner-a"), _step("inner-b")],
            },
        ]
        result = find_step(steps, "inner-b")
        assert result is not None
        assert result[0] is steps[0]["steps"]
        assert result[1] == 1

    def test_find_step_in_switch_cases(self):
        steps = [
            {
                "id": "switch-1",
                "type": "switch",
                "expression": "{{ inputs.x }}",
                "cases": {
                    "one": [_step("case-a")],
                    "two": [_step("case-b")],
                },
                "default": [_step("default-c")],
            },
        ]
        assert find_step(steps, "case-b")[1] == 0
        assert find_step(steps, "default-c")[1] == 0

    def test_find_step_not_in_fan_out_template(self):
        steps = [
            {
                "id": "fan-1",
                "type": "fan-out",
                "items": "{{ inputs.items }}",
                "step": {"id": "template-x", "type": "command", "command": "echo"},
            },
        ]
        assert find_step(steps, "template-x") is None


class TestApplyEdit:
    """Single edit operations against a step list."""

    def test_insert_after(self):
        steps = [_step("a"), _step("b")]
        new_step = _step("new")
        result, composed, replaced = apply_edit(steps, OverlayEdit("insert_after", "a", new_step), "project")
        assert [s["id"] for s in result] == ["a", "new", "b"]
        assert composed == ComposedStep("new", "project")
        assert replaced is None

    def test_insert_before(self):
        steps = [_step("a"), _step("b")]
        new_step = _step("new")
        result, composed, replaced = apply_edit(steps, OverlayEdit("insert_before", "b", new_step), "project")
        assert [s["id"] for s in result] == ["a", "new", "b"]
        assert replaced is None

    def test_replace(self):
        steps = [_step("a"), _step("b")]
        new_step = _step("replaced")
        result, composed, replaced = apply_edit(steps, OverlayEdit("replace", "b", new_step), "installed:x")
        assert [s["id"] for s in result] == ["a", "replaced"]
        assert composed == ComposedStep("replaced", "installed:x")
        assert replaced == "b"

    def test_remove(self):
        steps = [_step("a"), _step("b"), _step("c")]
        result, composed, replaced = apply_edit(steps, OverlayEdit("remove", "b"), "project")
        assert [s["id"] for s in result] == ["a", "c"]
        assert composed is None
        assert replaced == "b"

    def test_apply_edit_anchors_nested(self):
        steps = [
            {
                "id": "if-1",
                "type": "if",
                "condition": "true",
                "then": [_step("then-a")],
            },
        ]
        new_step = _step("new")
        result, _, _ = apply_edit(steps, OverlayEdit("insert_after", "then-a", new_step), "project")
        assert [s["id"] for s in result[0]["then"]] == ["then-a", "new"]

    def test_apply_edit_missing_anchor(self):
        steps = [_step("a")]
        new_step = _step("new")
        with pytest.raises(ValueError, match="Anchor 'missing' not found"):
            apply_edit(steps, OverlayEdit("insert_after", "missing", new_step), "project")


class TestMergeSteps:
    """Composition of multiple overlays in merge order."""

    def test_merge_steps_no_overlays(self):
        base = [_step("a"), _step("b")]
        steps, attribution = merge_steps(base, [])
        assert [s["id"] for s in steps] == ["a", "b"]
        assert attribution == [ComposedStep("a", "base"), ComposedStep("b", "base")]

    def test_merge_steps_single_overlay(self):
        base = [_step("a"), _step("b")]
        overlay = Overlay(
            id="ov1",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("insert_after", "a", _step("new"))],
        )
        steps, attribution = merge_steps(base, [_layer(overlay, "project:ov1")])
        assert [s["id"] for s in steps] == ["a", "new", "b"]
        assert attribution == [
            ComposedStep("a", "base"),
            ComposedStep("new", "project:ov1"),
            ComposedStep("b", "base"),
        ]

    def test_merge_steps_higher_priority_wins(self):
        base = [_step("a")]
        low = Overlay(
            id="low",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("insert_after", "a", _step("low-step"))],
        )
        high = Overlay(
            id="high",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("insert_after", "a", _step("high-step"))],
        )
        steps, attribution = merge_steps(base, [_layer(low, "project:low"), _layer(high, "project:high")])
        # low applied first, then high; both insert after 'a', so high-step ends
        # closer to the anchor (higher priority wins the conflict).
        assert [s["id"] for s in steps] == ["a", "high-step", "low-step"]
        assert attribution == [
            ComposedStep("a", "base"),
            ComposedStep("high-step", "project:high"),
            ComposedStep("low-step", "project:low"),
        ]

    def test_merge_steps_replace_wins_over_insert(self):
        base = [_step("a")]
        insert = Overlay(
            id="insert",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("insert_after", "a", _step("inserted"))],
        )
        replace = Overlay(
            id="replace",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "inserted", _step("replaced"))],
        )
        steps, _ = merge_steps(base, [_layer(insert, "project:insert"), _layer(replace, "project:replace")])
        assert [s["id"] for s in steps] == ["a", "replaced"]

    def test_merge_steps_does_not_mutate_base(self):
        base = [_step("a")]
        overlay = Overlay(
            id="ov1",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("insert_after", "a", _step("new"))],
        )
        original = copy.deepcopy(base)
        merge_steps(base, [_layer(overlay, "project:ov1")])
        assert base == original

    def test_merge_steps_attribution_uses_source_not_overlay_id(self):
        base = [_step("a")]
        overlay = Overlay(
            id="same-id",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("insert_after", "a", _step("new"))],
        )
        steps, attribution = merge_steps(base, [_layer(overlay, "installed:same-id")])
        assert [s["id"] for s in steps] == ["a", "new"]
        assert attribution == [
            ComposedStep("a", "base"),
            ComposedStep("new", "installed:same-id"),
        ]

    def test_merge_steps_nested_base_attribution(self):
        base = [
            {
                "id": "if-1",
                "type": "if",
                "condition": "true",
                "then": [_step("then-a")],
                "else": [_step("else-b")],
            },
        ]
        steps, attribution = merge_steps(base, [])
        assert attribution == [
            ComposedStep("if-1", "base"),
            ComposedStep("then-a", "base"),
            ComposedStep("else-b", "base"),
        ]

    def test_merge_steps_higher_replace_wins_lower_replace_same_anchor(self):
        base = [_step("implement")]
        low = Overlay(
            id="low",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("replace", "implement", _step("low-implement"))],
        )
        high = Overlay(
            id="high",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "implement", _step("high-implement"))],
        )
        steps, attribution = merge_steps(base, [_layer(low, "project:low"), _layer(high, "project:high")])
        assert [s["id"] for s in steps] == ["high-implement"]
        assert any(
            composed.step_id == "high-implement" and composed.source == "project:high"
            for composed in attribution
        )

    def test_merge_steps_higher_replace_wins_after_lower_remove_same_anchor(self):
        base = [_step("implement")]
        low = Overlay(
            id="low",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("remove", "implement")],
        )
        high = Overlay(
            id="high",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "implement", _step("high-implement"))],
        )
        steps, attribution = merge_steps(base, [_layer(low, "project:low"), _layer(high, "project:high")])
        assert [s["id"] for s in steps] == ["high-implement"]

    def test_merge_steps_higher_insert_wins_after_lower_remove_same_anchor(self):
        base = [_step("implement")]
        low = Overlay(
            id="low",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("remove", "implement")],
        )
        high = Overlay(
            id="high",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("insert_after", "implement", _step("high-after"))],
        )
        steps, attribution = merge_steps(base, [_layer(low, "project:low"), _layer(high, "project:high")])
        assert [s["id"] for s in steps] == ["implement", "high-after"]
        assert attribution == [
            ComposedStep("implement", "base"),
            ComposedStep("high-after", "project:high"),
        ]

    def test_merge_steps_later_overlay_wins_tie_same_anchor(self):
        """When two overlays have the same priority, the one applied later wins."""
        base = [_step("a")]
        first = Overlay(
            id="first",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "a", _step("first-replace"))],
        )
        second = Overlay(
            id="second",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "a", _step("second-replace"))],
        )
        # Merge order: first applied, then second wins tie.
        steps, attribution = merge_steps(
            base,
            [
                _layer(first, "overlay:first"),
                _layer(second, "overlay:second"),
            ],
        )
        assert [s["id"] for s in steps] == ["second-replace"]
        assert any(
            composed.step_id == "second-replace" and composed.source == "overlay:second"
            for composed in attribution
        )

    def test_merge_steps_insert_after_then_replace_same_anchor_id_change(self):
        """Inserts must be applied before the winning replace so the anchor still exists.

        Regression: when a replace changes the step ID, applying it before inserts
        causes ``find_step`` to fail on the now-gone original anchor.
        """
        base = [_step("build")]
        low = Overlay(
            id="low",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("insert_after", "build", _step("test"))],
        )
        high = Overlay(
            id="high",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "build", _step("compile"))],
        )
        steps, attribution = merge_steps(
            base, [_layer(low, "project:low"), _layer(high, "project:high")]
        )
        # The insert should land after the original anchor position, then the
        # anchor is replaced.  Final order: ["compile", "test"].
        assert [s["id"] for s in steps] == ["compile", "test"]
        assert attribution == [
            ComposedStep("compile", "project:high"),
            ComposedStep("test", "project:low"),
        ]

    def test_merge_steps_insert_before_then_replace_same_anchor_id_change(self):
        """Same as above but with insert_before — anchor must still be findable."""
        base = [_step("build")]
        low = Overlay(
            id="low",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("insert_before", "build", _step("lint"))],
        )
        high = Overlay(
            id="high",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "build", _step("compile"))],
        )
        steps, attribution = merge_steps(
            base, [_layer(low, "project:low"), _layer(high, "project:high")]
        )
        assert [s["id"] for s in steps] == ["lint", "compile"]
        assert attribution == [
            ComposedStep("lint", "project:low"),
            ComposedStep("compile", "project:high"),
        ]

    def test_merge_steps_unknown_anchor_still_raises(self):
        base = [_step("a")]
        overlay = Overlay(
            id="ov",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "missing", _step("new"))],
        )
        with pytest.raises(ValueError, match="Anchor 'missing' not found"):
            merge_steps(base, [_layer(overlay, "project:ov")])

    # ── composite step attribution ───────────────────────────────────────

    def test_merge_insert_composite_if_attribution(self):
        """Nested then/else children of an inserted 'if' step get the overlay source."""
        base = [_step("a")]
        composite = {
            "id": "if-1",
            "type": "if",
            "condition": "true",
            "then": [_step("then-a")],
            "else": [_step("else-b")],
        }
        overlay = Overlay(
            id="ov", extends="wf", priority=10,
            edits=[OverlayEdit("insert_after", "a", composite)],
        )
        _steps, attribution = merge_steps(
            base, [_layer(overlay, "project:ov")]
        )
        assert attribution == [
            ComposedStep("a", "base"),
            ComposedStep("if-1", "project:ov"),
            ComposedStep("then-a", "project:ov"),
            ComposedStep("else-b", "project:ov"),
        ]

    def test_merge_insert_composite_switch_attribution(self):
        """Nested cases/default children of an inserted 'switch' step get the overlay source."""
        base = [_step("a")]
        composite = {
            "id": "switch-1",
            "type": "switch",
            "expression": "{{inputs.x}}",
            "cases": {"one": [_step("case-one")], "two": [_step("case-two")]},
            "default": [_step("default-z")],
        }
        overlay = Overlay(
            id="ov", extends="wf", priority=10,
            edits=[OverlayEdit("insert_before", "a", composite)],
        )
        _steps, attribution = merge_steps(
            base, [_layer(overlay, "project:ov")]
        )
        assert attribution == [
            ComposedStep("switch-1", "project:ov"),
            ComposedStep("default-z", "project:ov"),
            ComposedStep("case-one", "project:ov"),
            ComposedStep("case-two", "project:ov"),
            ComposedStep("a", "base"),
        ]

    def test_merge_replace_flat_with_composite_attribution(self):
        """Replacing a flat step with a composite step attributes all nested children."""
        base = [_step("a")]
        composite = {
            "id": "if-1",
            "type": "if",
            "condition": "true",
            "then": [_step("inner-x"), _step("inner-y")],
        }
        overlay = Overlay(
            id="ov", extends="wf", priority=10,
            edits=[OverlayEdit("replace", "a", composite)],
        )
        _steps, attribution = merge_steps(
            base, [_layer(overlay, "project:ov")]
        )
        assert attribution == [
            ComposedStep("if-1", "project:ov"),
            ComposedStep("inner-x", "project:ov"),
            ComposedStep("inner-y", "project:ov"),
        ]

    def test_merge_remove_composite_step_cleans_nested_sources(self):
        """Removing a composite step also cleans its nested children from sources."""
        base = [
            {
                "id": "if-1",
                "type": "if",
                "condition": "true",
                "then": [_step("then-a")],
                "else": [_step("else-b")],
            },
            _step("a"),
        ]
        overlay = Overlay(
            id="ov", extends="wf", priority=10,
            edits=[OverlayEdit("remove", "if-1")],
        )
        steps, attribution = merge_steps(
            base, [_layer(overlay, "project:ov")]
        )
        assert [s["id"] for s in steps] == ["a"]
        assert attribution == [ComposedStep("a", "base")]

    def test_merge_insert_deeply_nested_composite_attribution(self):
        """Deep nesting (if inside while) gets the overlay source at every level."""
        base = [_step("a")]
        inner_if = {
            "id": "inner-if",
            "type": "if",
            "condition": "true",
            "then": [_step("deep-x")],
        }
        composite = {
            "id": "while-1",
            "type": "while",
            "condition": "true",
            "steps": [inner_if],
        }
        overlay = Overlay(
            id="ov", extends="wf", priority=10,
            edits=[OverlayEdit("insert_after", "a", composite)],
        )
        _steps, attribution = merge_steps(
            base, [_layer(overlay, "project:ov")]
        )
        assert attribution == [
            ComposedStep("a", "base"),
            ComposedStep("while-1", "project:ov"),
            ComposedStep("inner-if", "project:ov"),
            ComposedStep("deep-x", "project:ov"),
        ]


class TestValidateEdits:
    """Edit validation against known base step IDs."""

    def test_valid_edits(self):
        edits = [
            OverlayEdit("insert_after", "a", _step("new")),
            OverlayEdit("remove", "b"),
        ]
        assert validate_edits(edits, {"a", "b"}) == []

    def test_invalid_anchor(self):
        edits = [OverlayEdit("insert_after", "missing", _step("new"))]
        errors = validate_edits(edits, {"a"})
        assert any("missing" in e for e in errors)

    def test_step_id_contains_colon(self):
        edits = [OverlayEdit("insert_after", "a", _step("bad:id"))]
        errors = validate_edits(edits, {"a"})
        assert any("':'" in e for e in errors)

    def test_remove_requires_no_step(self):
        edits = [OverlayEdit("remove", "a", _step("extra"))]
        errors = validate_edits(edits, {"a"})
        assert len(errors) > 0
